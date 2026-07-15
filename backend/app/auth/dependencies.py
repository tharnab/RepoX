"""FastAPI dependencies for authentication."""

from fastapi import Request, HTTPException, Depends
from typing import Optional
from app.auth.session import verify_session_cookie
from app.auth.models import validate_session, get_user_by_id, get_token_for_user


class User:
    """
    Represents the currently authenticated user.
    A simple class to hold user data.
    """

    def __init__(self, id: int, login: str, avatar_url: str):
        self.id = id
        self.login = login
        self.avatar_url = avatar_url

    def to_dict(self) -> dict:
        """Convert to dictionary (for JSON responses)."""
        return {
            "id": self.id,
            "login": self.login,
            "avatar_url": self.avatar_url,
        }


async def get_current_user(request: Request) -> Optional[User]:
    """
    Extract the current user from the session cookie.

    This is the MAIN dependency. Use it on every endpoint.
    Returns:
        User object if logged in, None if anonymous.
    
    Usage:
        @app.get("/something")
        async def something(user: User | None = Depends(get_current_user)):
            if user:
                return f"Hello {user.login}!"
            return "Hello anonymous!"
    """
    # Step 1: Get the signed cookie from the request
    signed_cookie = request.cookies.get("repox_session")
    if not signed_cookie:
        return None

    # Step 2: Verify the signature and extract session token
    session_token = verify_session_cookie(signed_cookie)
    if not session_token:
        return None

    # Step 3: Check the session exists and hasn't expired
    user_id = await validate_session(session_token)
    if not user_id:
        return None

    # Step 4: Get the user from the database
    user_data = await get_user_by_id(user_id)
    if not user_data:
        return None

    # Step 5: Return the user
    return User(
        id=user_data["id"],
        login=user_data["login"],
        avatar_url=user_data["avatar_url"],
    )


async def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    """
    Like get_current_user, but raises a 401 error if not logged in.
    
    Use this on endpoints that REQUIRE authentication.
    
    Usage:
        @app.get("/private-data")
        async def private_data(user: User = Depends(require_user)):
            return f"Secret data for {user.login}"
    """
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in with GitHub.",
        )
    return user


async def get_github_token(user: Optional[User] = Depends(get_current_user)) -> Optional[str]:
    """
    Get the decrypted GitHub access token for the current user.
    
    Returns None if not logged in or token not found.
    
    Usage:
        @app.get("/repos/private")
        async def private_repos(token: str = Depends(get_github_token)):
            # Use this token to call GitHub API
            ...
    """
    if user is None:
        return None

    return await get_token_for_user(user.id)