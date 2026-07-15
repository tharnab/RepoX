"""RepoX - Main application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import FRONTEND_URL, ensure_data_dir
from app.database import init_db, close_db
from app.auth.router import router as auth_router
from app.routes.repos import router as repos_router
from app.routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    
    Startup: Create data directory, initialize database tables
    Shutdown: Close database connection
    """
    # Startup
    ensure_data_dir()
    await init_db()
    print("✅ Database initialized")
    
    yield  # The app runs here
    
    # Shutdown
    await close_db()
    print("✅ Database connection closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="RepoX",
        description="AI-powered code repository analysis",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS - Allow the frontend to make requests
    # In development, this allows localhost:3000 to call localhost:8000
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,        # Allows cookies to be sent
        allow_methods=["*"],            # Allows all HTTP methods
        allow_headers=["*"],            # Allows all headers
    )

    # Mount routers
    app.include_router(auth_router)
    app.include_router(repos_router)
    app.include_router(chat_router)

    # Health check endpoint
    @app.get("/health")
    async def health():
        return {"status": "ok", "app": "RepoX"}

    return app


# Create the app instance
app = create_app()