"""GitHub OAuth flow - login URL, token exchange, user info."""

import asyncio
import json
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_REDIRECT_URI


def get_authorization_url() -> tuple[str, str]:
    """
    Build the GitHub OAuth login URL.
    
    Returns:
        (url, state) 
        - url: The GitHub page to redirect the user to
        - state: A random string to prevent CSRF attacks
    """
    # Generate random state to prevent CSRF
    state = secrets.token_urlsafe(32)

    # Build the GitHub authorization URL
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "repo read:org",       # Permissions we need
        "state": state,                 # CSRF protection
        "allow_signup": "false",        # Don't show signup page
        "prompt": "consent",
    }

    url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return url, state


def _fetch_json(method: str, url: str, headers: dict[str, str], payload: bytes | None = None) -> dict | None:
    request = Request(url, data=payload, headers=headers, method=method)

    try:
        with urlopen(request) as response:
            body = response.read()
            if not body:
                return None
            return json.loads(body.decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError):
        return None


async def _fetch_json_async(method: str, url: str, headers: dict[str, str], payload: bytes | None = None) -> dict | None:
    return await asyncio.to_thread(_fetch_json, method, url, headers, payload)


async def exchange_code_for_token(code: str) -> dict | None:
    """
    After user approves on GitHub, exchange the code for an access token.
    
    Args:
        code: The authorization code from GitHub's callback
        
    Returns:
        dict with 'access_token' and 'scopes', or None if failed
    """
    payload = json.dumps(
        {
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI,
        }
    ).encode("utf-8")

    data = await _fetch_json_async(
        "POST",
        "https://github.com/login/oauth/access_token",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        payload=payload,
    )

    if data and "access_token" in data:
        return {
            "access_token": data["access_token"],
            "scopes": data.get("scope", ""),
        }

    return None


async def get_github_user(access_token: str) -> dict | None:
    """
    Use the access token to fetch the user's GitHub profile.
    
    Args:
        access_token: The token from exchange_code_for_token()
        
    Returns:
        dict with 'id', 'login', 'avatar_url', or None if failed
    """
    data = await _fetch_json_async(
        "GET",
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "User-Agent": "RepoX GitHub OAuth",
        },
    )

    if data and "id" in data:
        return {
            "id": data["id"],
            "login": data["login"],
            "avatar_url": data["avatar_url"],
        }

    return None