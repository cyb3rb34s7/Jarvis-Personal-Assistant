"""JARVIS API - Status endpoints."""

from fastapi import APIRouter

from ...utils import check_ollama_running, check_dependencies
from ...database import list_conversations
from ..auth import is_auth_enabled

router = APIRouter()


@router.get("/status")
async def get_status():
    """Get system status and health check.

    This endpoint does not require authentication.

    Returns:
        System status including:
        - API version
        - Ollama status
        - Dependencies status
        - Auth status
        - Database stats
    """
    deps = check_dependencies()
    conversations = list_conversations(limit=1000)

    return {
        "status": "ok",
        "version": "0.2.0",
        "auth_enabled": is_auth_enabled(),
        "ollama": {
            "running": deps.get("ollama", False),
        },
        "dependencies": {
            "ollama": deps.get("ollama", False),
            "faster_whisper": deps.get("faster_whisper", False),
            "kokoro_onnx": deps.get("kokoro_onnx", False),
            "sounddevice": deps.get("sounddevice", False),
        },
        "database": {
            "conversations": len(conversations),
        },
    }


@router.get("/health")
async def health_check():
    """Simple health check endpoint.

    Returns:
        {"status": "ok"} if the API is running
    """
    return {"status": "ok"}
