"""JARVIS Utilities module."""

from .errors import (
    JarvisError,
    ConfigError,
    ModelError,
    STTError,
    TTSError,
    ToolError,
    MCPError,
    NetworkError,
    handle_errors,
    handle_errors_async,
    format_error_for_user,
    check_ollama_running,
    check_dependencies,
)

__all__ = [
    "JarvisError",
    "ConfigError",
    "ModelError",
    "STTError",
    "TTSError",
    "ToolError",
    "MCPError",
    "NetworkError",
    "handle_errors",
    "handle_errors_async",
    "format_error_for_user",
    "check_ollama_running",
    "check_dependencies",
]
