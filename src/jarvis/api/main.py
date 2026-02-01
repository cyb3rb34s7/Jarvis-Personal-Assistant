"""JARVIS API - Main FastAPI application."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import chat, conversations, status, reminders, notes, mcp, voice


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler - startup and shutdown."""
    # Startup
    print("[API] Starting JARVIS API server...")

    # Initialize agent (lazy load on first request instead)
    # This avoids loading heavy models if not needed immediately

    yield

    # Shutdown
    print("[API] Shutting down JARVIS API server...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="JARVIS API",
        description="Local AI Voice Assistant API",
        version="0.2.0",
        lifespan=lifespan,
    )

    # CORS configuration
    cors_origins = [
        "http://localhost:3000",      # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:5173",      # Vite dev server
        "http://127.0.0.1:5173",
    ]

    # Add production origins from environment
    if os.getenv("JARVIS_CORS_ORIGINS"):
        cors_origins.extend(os.getenv("JARVIS_CORS_ORIGINS").split(","))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(status.router, prefix="/api/v1", tags=["status"])
    app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(reminders.router, prefix="/api/v1", tags=["reminders"])
    app.include_router(notes.router, prefix="/api/v1", tags=["notes"])
    app.include_router(mcp.router, prefix="/api/v1", tags=["mcp"])
    app.include_router(voice.router, prefix="/api/v1", tags=["voice"])

    return app


# Create default app instance
app = create_app()


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """Run the API server with uvicorn."""
    import uvicorn

    uvicorn.run(
        "jarvis.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
