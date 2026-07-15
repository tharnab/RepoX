"""Session cookie management - signing and verification."""

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.config import SESSION_SECRET_KEY, SESSION_MAX_AGE_DAYS


def get_serializer() -> URLSafeTimedSerializer:
    """
    Create a serializer that signs data with our secret key.
    """
    return URLSafeTimedSerializer(
        SESSION_SECRET_KEY,
        salt="repox-session",
    )


def create_session_cookie_value(session_token: str) -> str:
    """Sign a session token for cookie storage."""
    serializer = get_serializer()
    signed = serializer.dumps(session_token)
    return signed


def verify_session_cookie(signed_value: str) -> str | None:
    """Verify a signed cookie and extract the session token."""
    serializer = get_serializer()

    try:
        max_age_seconds = SESSION_MAX_AGE_DAYS * 86400
        session_token = serializer.loads(signed_value, max_age=max_age_seconds)
        return session_token
    except SignatureExpired:
        return None
    except BadSignature:
        return None


def get_session_cookie_config() -> dict:
    """Get secure cookie configuration."""
    from app.config import APP_ENV

    return {
        "key": "repox_session",
        "httponly": True,
        "secure": APP_ENV == "production",
        "samesite": "lax",
        "path": "/",
        "max_age": SESSION_MAX_AGE_DAYS * 86400,
    }