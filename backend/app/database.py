"""Async SQLite database connection and initialization."""

import aiosqlite  # type: ignore[reportMissingImports]
from pathlib import Path
from app.config import DATABASE_URL


# Global database connection (SQLite works best with a single connection)
_db = None


async def get_db() -> aiosqlite.Connection:
    """
    Get or create the database connection.
    Returns the same connection every time (singleton pattern).
    """
    global _db

    if _db is None:
        # Extract file path from the URL
        # "sqlite+aiosqlite:///./data/repox.db" → "./data/repox.db"
        db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")

        # Make sure the data folder exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create connection
        _db = await aiosqlite.connect(db_path)
        
        # Return rows as dictionaries (easier to work with)
        _db.row_factory = aiosqlite.Row
        
        # Enable WAL mode for better performance
        await _db.execute("PRAGMA journal_mode=WAL")
        
        # Enable foreign keys
        await _db.execute("PRAGMA foreign_keys=ON")

    return _db


async def init_db():
    """
    Create all database tables from schema.sql.
    Runs once when the server starts.
    """
    db = await get_db()

    # Read the SQL schema file
    schema_path = Path(__file__).parent / "auth" / "schema.sql"
    
    with open(schema_path) as f:
        schema_sql = f.read()

    # Execute all CREATE TABLE statements
    await db.executescript(schema_sql)
    await db.commit()


async def close_db():
    """Close the database connection. Called on server shutdown."""
    global _db
    if _db:
        await _db.close()
        _db = None