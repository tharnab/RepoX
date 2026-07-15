"""Database operations for users, tokens, and sessions."""

import hashlib
import secrets
from datetime import datetime, timedelta
from app.database import get_db
from app.config import SESSION_MAX_AGE_DAYS
from app.auth.encryption import encrypt_token, decrypt_token


async def upsert_user(github_id: int, login: str, avatar_url: str) -> dict:
    """
    Insert a new user or update if they already exist.
    Called every time someone logs in.
    """
    db = await get_db()

    await db.execute(
        """
        INSERT INTO users (id, login, avatar_url, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            login = excluded.login,
            avatar_url = excluded.avatar_url,
            updated_at = CURRENT_TIMESTAMP
        """,
        (github_id, login, avatar_url)
    )
    await db.commit()

    # Return the user we just created/updated
    cursor = await db.execute(
        "SELECT id, login, avatar_url, created_at FROM users WHERE id = ?",
        (github_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def store_token(user_id: int, access_token: str, scopes: str = ""):
    """
    Encrypt and store a GitHub access token.
    Replaces old token if user logs in again.
    """
    encrypted = encrypt_token(access_token)
    db = await get_db()

    await db.execute(
        """
        INSERT INTO tokens (user_id, encrypted_token, scopes, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            encrypted_token = excluded.encrypted_token,
            scopes = excluded.scopes,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, encrypted, scopes)
    )
    await db.commit()


async def get_token_for_user(user_id: int) -> str | None:
    """
    Retrieve and decrypt the GitHub token for a user.
    Returns None if user has no token or decryption fails.
    """
    db = await get_db()

    cursor = await db.execute(
        "SELECT encrypted_token FROM tokens WHERE user_id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()

    if row:
        try:
            return decrypt_token(row["encrypted_token"])
        except Exception:
            # Decryption failed (wrong key? corrupted data?)
            return None

    return None


async def get_user_by_id(user_id: int) -> dict | None:
    """Get a user by their GitHub ID."""
    db = await get_db()

    cursor = await db.execute(
        "SELECT id, login, avatar_url, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def create_session(user_id: int) -> str:
    """
    Create a login session for a user.
    Returns the raw session token (goes in the cookie).
    """
    # Generate a random session token
    session_token = secrets.token_urlsafe(32)

    # Hash it before storing (so even if DB leaks, sessions are safe)
    session_hash = hashlib.sha256(session_token.encode()).hexdigest()

    # Calculate when this session expires
    expires_at = datetime.utcnow() + timedelta(days=SESSION_MAX_AGE_DAYS)

    db = await get_db()
    await db.execute(
        "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)",
        (session_hash, user_id, expires_at.isoformat())
    )
    await db.commit()

    # Return the UNHASHED token (only this once, for the cookie)
    return session_token


async def validate_session(session_token: str) -> int | None:
    """
    Check if a session token is valid.
    Returns the user_id if valid, None if expired or invalid.
    """
    # Hash the token to look it up in the database
    session_hash = hashlib.sha256(session_token.encode()).hexdigest()

    db = await get_db()
    cursor = await db.execute(
        """
        SELECT user_id, expires_at FROM sessions
        WHERE session_id = ? AND expires_at > ?
        """,
        (session_hash, datetime.utcnow().isoformat())
    )
    row = await cursor.fetchone()

    if row:
        return row["user_id"]

    return None


async def delete_session(session_token: str):
    """Delete a session (user logs out)."""
    session_hash = hashlib.sha256(session_token.encode()).hexdigest()

    db = await get_db()
    await db.execute(
        "DELETE FROM sessions WHERE session_id = ?",
        (session_hash,)
    )
    await db.commit()


async def cleanup_expired_sessions():
    """Remove all expired sessions. Call periodically."""
    db = await get_db()
    await db.execute(
        "DELETE FROM sessions WHERE expires_at < ?",
        (datetime.utcnow().isoformat(),)
    )
    await db.commit()