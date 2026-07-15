"""Application configuration from environment variables."""

import os
from pathlib import Path

def load_dotenv(dotenv_path=None) -> None:
    """Load environment variables from a .env file if present."""
    dotenv_path = Path(dotenv_path or ".env")
    if not dotenv_path.exists():
        return

    with dotenv_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

# Load .env file
load_dotenv()


def get_env(key: str, default: str = None, required: bool = True) -> str:
    """
    Get an environment variable.
    If required=True and not set, raises an error with a clear message.
    """
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(
            f"Missing required environment variable: {key}\n"
            f"Check your .env file (copy from .env.example and fill in values)"
        )
    return value


# GitHub OAuth
GITHUB_CLIENT_ID = get_env("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = get_env("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = get_env(
    "GITHUB_REDIRECT_URI",
    default="http://localhost:8000/auth/github/callback"
)

# Security keys
ENCRYPTION_KEY = get_env("ENCRYPTION_KEY")
SESSION_SECRET_KEY = get_env("SESSION_SECRET_KEY")

# Database
DATABASE_URL = get_env(
    "DATABASE_URL",
    default="sqlite+aiosqlite:///./data/repox.db"
)

# Frontend
FRONTEND_URL = get_env("FRONTEND_URL", default="http://localhost:3000")

# App settings
APP_ENV = get_env("APP_ENV", default="development")
SESSION_MAX_AGE_DAYS = int(get_env("SESSION_MAX_AGE_DAYS", default="30"))


def ensure_data_dir():
    """Create the data directory for SQLite if it doesn't exist."""
    if "sqlite" in DATABASE_URL:
        # Extract path from: sqlite+aiosqlite:///./data/repox.db
        db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)