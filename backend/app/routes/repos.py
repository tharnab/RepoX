"""Example repository endpoints showing public + private access."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import httpx
from app.auth.dependencies import get_current_user, get_github_token, require_user, User

router = APIRouter(prefix="/api/repos", tags=["repositories"])


@router.get("/public/{owner}/{repo}")
async def get_public_repo(owner: str, repo: str):
    """
    Get a public repository - NO authentication required.
    
    Example: GET /api/repos/public/facebook/react
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={"Accept": "application/json"},
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")

        return response.json()


@router.get("/{owner}/{repo}")
async def get_repo(
    owner: str,
    repo: str,
    user: Optional[User] = Depends(get_current_user),
    token: Optional[str] = Depends(get_github_token),
):
    """
    Get a repository - works for everyone, better with auth.
    
    - Anonymous users: Can only see public repos, 60 requests/hour limit
    - Logged in users: Can see private repos too, 5000 requests/hour limit
    
    Example: GET /api/repos/facebook/react
    """
    headers = {"Accept": "application/json"}

    # If user is logged in, use their GitHub token
    # This gives access to private repos + higher rate limit
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers,
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Repository not accessible. Sign in to access private repos.",
            )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")

        return response.json()


@router.get("/private/{owner}/{repo}")
async def get_private_repo(
    owner: str,
    repo: str,
    user: User = Depends(require_user),           # MUST be logged in
    token: str = Depends(get_github_token),       # MUST have a token
):
    """
    Get a repository - REQUIRES authentication.
    
    Use this when you know the repo might be private.
    
    Example: GET /api/repos/private/mycompany/secret-repo
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")

        return response.json()