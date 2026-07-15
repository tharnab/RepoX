"""Authentication routes - login, callback, logout, me."""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from app.config import FRONTEND_URL
from app.auth.github_oauth import (
    get_authorization_url,
    exchange_code_for_token,
    get_github_user,
)
from app.auth.models import (
    upsert_user,
    store_token,
    create_session,
    delete_session,
)
from app.auth.session import (
    create_session_cookie_value,
    get_session_cookie_config,
    verify_session_cookie,
)
from app.auth.dependencies import get_current_user, User

router = APIRouter(prefix="/auth", tags=["auth"])

# Temporary storage for OAuth state values
# In production, use Redis or a database table
_oauth_states = {}


@router.get("/github/login")
async def github_login():
    """
    Start the GitHub OAuth flow.
    Redirects the user to GitHub to approve the app.
    
    Visit this in your browser to test:
    http://localhost:8000/auth/github/login
    """
    url, state = get_authorization_url()

    # Store the state so we can verify it in the callback
    _oauth_states[state] = True

    # Send the user to GitHub
    return RedirectResponse(url=url)


@router.get("/github/callback")
async def github_callback(code: str, state: str):
    """
    GitHub redirects back here after the user approves.
    
    This endpoint:
    1. Verifies the state (CSRF protection)
    2. Exchanges the code for an access token
    3. Fetches the user's GitHub profile
    4. Saves everything in the database
    5. Creates a session and sets a cookie
    6. Redirects to the frontend
    """
    # Step 1: Verify state to prevent CSRF attacks
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Remove used state (each state can only be used once)
    _oauth_states.pop(state, None)

    # Step 2: Exchange the code for an access token
    token_data = await exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(
            status_code=400,
            detail="Failed to exchange code for token"
        )

    # Step 3: Get the user's GitHub profile
    github_user = await get_github_user(token_data["access_token"])
    if not github_user:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch GitHub user info"
        )

    # Step 4: Save user to database
    await upsert_user(
        github_user["id"],
        github_user["login"],
        github_user["avatar_url"],
    )

    # Step 5: Encrypt and store the access token
    await store_token(
        github_user["id"],
        token_data["access_token"],
        token_data["scopes"],
    )

    # Step 6: Create a session
    session_token = await create_session(github_user["id"])

    # Step 7: Set the session cookie and redirect to frontend
    signed_cookie = create_session_cookie_value(session_token)
    cookie_config = get_session_cookie_config()

    response = RedirectResponse(url="http://localhost:3000")
    response.set_cookie(
        key=cookie_config["key"],
        value=signed_cookie,
        httponly=cookie_config["httponly"],
        secure=cookie_config["secure"],
        samesite=cookie_config["samesite"],
        path=cookie_config["path"],
        max_age=cookie_config["max_age"],
    )

    return response

@router.get("/logout")
async def logout_get(request: Request, user: User | None = Depends(get_current_user)):
    """
    Log out via GET request (browser-friendly).
    """
    if user:
        signed_cookie = request.cookies.get("repox_session")
        if signed_cookie:
            session_token = verify_session_cookie(signed_cookie)
            if session_token:
                await delete_session(session_token)

    cookie_config = get_session_cookie_config()
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie(
        key=cookie_config["key"],
        path=cookie_config["path"],
    )
    return response

@router.post("/logout")
async def logout(request: Request, user: User | None = Depends(get_current_user)):
    """
    Log out the current user.
    Deletes the session from the database and clears the cookie.
    """
    # If user is logged in, delete their session
    if user:
        signed_cookie = request.cookies.get("repox_session")
        if signed_cookie:
            session_token = verify_session_cookie(signed_cookie)
            if session_token:
                await delete_session(session_token)

    # Clear the cookie whether they were logged in or not
    cookie_config = get_session_cookie_config()
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie(
        key=cookie_config["key"],
        path=cookie_config["path"],
    )

    return response


@router.get("/me")
async def me(user: User | None = Depends(get_current_user)):
    """
    Return the current user or null.
    The frontend calls this on page load to check if someone is logged in.
    
    Response when logged in:
        {"authenticated": true, "user": {"id": 123, "login": "john", ...}}
    
    Response when anonymous:
        {"authenticated": false, "user": null}
    """
    if user:
        return {
            "authenticated": True,
            "user": user.to_dict(),
        }

    return {
        "authenticated": False,
        "user": None,
    }