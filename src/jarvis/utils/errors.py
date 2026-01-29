"""JARVIS - Error handling utilities."""

import functools
import traceback
from typing import Callable, TypeVar, Any

T = TypeVar("T")


class JarvisError(Exception):
    """Base exception for JARVIS errors."""

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def user_message(self) -> str:
        """Return a user-friendly error message."""
        return self.message


class ConfigError(JarvisError):
    """Configuration-related errors."""
    pass


class ModelError(JarvisError):
    """LLM model errors."""

    def user_message(self) -> str:
        return f"Model error: {self.message}. Is Ollama running?"


class STTError(JarvisError):
    """Speech-to-text errors."""

    def user_message(self) -> str:
        return f"Speech recognition error: {self.message}"


class TTSError(JarvisError):
    """Text-to-speech errors."""

    def user_message(self) -> str:
        return f"Speech synthesis error: {self.message}"


class ToolError(JarvisError):
    """Tool execution errors."""

    def user_message(self) -> str:
        return f"Tool error: {self.message}"


class MCPError(JarvisError):
    """MCP-related errors."""

    def user_message(self) -> str:
        return f"MCP error: {self.message}"


class NetworkError(JarvisError):
    """Network-related errors."""

    def user_message(self) -> str:
        return f"Network error: {self.message}. Check your internet connection."


def handle_errors(
    default_return: Any = None,
    error_prefix: str = "Error",
    reraise: bool = False,
    verbose: bool = False
) -> Callable:
    """Decorator for graceful error handling.

    Args:
        default_return: Value to return on error (or callable for dynamic default)
        error_prefix: Prefix for error messages
        reraise: Whether to re-raise the exception after handling
        verbose: Whether to print full traceback

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except JarvisError as e:
                print(f"[{error_prefix}] {e.user_message()}")
                if verbose and e.details:
                    print(f"  Details: {e.details}")
                if reraise:
                    raise
                return default_return() if callable(default_return) else default_return
            except Exception as e:
                print(f"[{error_prefix}] {str(e)}")
                if verbose:
                    traceback.print_exc()
                if reraise:
                    raise
                return default_return() if callable(default_return) else default_return
        return wrapper
    return decorator


def handle_errors_async(
    default_return: Any = None,
    error_prefix: str = "Error",
    reraise: bool = False,
    verbose: bool = False
) -> Callable:
    """Async version of handle_errors decorator."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except JarvisError as e:
                print(f"[{error_prefix}] {e.user_message()}")
                if verbose and e.details:
                    print(f"  Details: {e.details}")
                if reraise:
                    raise
                return default_return() if callable(default_return) else default_return
            except Exception as e:
                print(f"[{error_prefix}] {str(e)}")
                if verbose:
                    traceback.print_exc()
                if reraise:
                    raise
                return default_return() if callable(default_return) else default_return
        return wrapper
    return decorator


def safe_import(module_name: str, package_name: str = None) -> Any:
    """Safely import a module with helpful error message.

    Args:
        module_name: Name of module to import
        package_name: pip package name if different from module_name

    Returns:
        Imported module or None

    Raises:
        ImportError: With helpful installation instructions
    """
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError:
        pkg = package_name or module_name
        raise ImportError(
            f"Module '{module_name}' not found. "
            f"Install with: pip install {pkg}"
        )


def format_error_for_user(error: Exception) -> str:
    """Format an exception for user display.

    Args:
        error: The exception to format

    Returns:
        User-friendly error message
    """
    if isinstance(error, JarvisError):
        return error.user_message()

    # Map common exceptions to friendly messages
    error_messages = {
        ConnectionError: "Connection failed. Check your internet or Ollama service.",
        TimeoutError: "Request timed out. Try again.",
        FileNotFoundError: f"File not found: {error}",
        PermissionError: f"Permission denied: {error}",
        ValueError: f"Invalid value: {error}",
        KeyError: f"Missing configuration: {error}",
    }

    for error_type, message in error_messages.items():
        if isinstance(error, error_type):
            return message

    # Generic fallback
    return f"An error occurred: {str(error)}"


def check_ollama_running() -> bool:
    """Check if Ollama service is running.

    Returns:
        True if Ollama is accessible
    """
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def check_dependencies() -> dict:
    """Check if all required dependencies are available.

    Returns:
        Dict with dependency status
    """
    deps = {
        "ollama": check_ollama_running(),
        "faster_whisper": False,
        "kokoro_onnx": False,
        "sounddevice": False,
    }

    try:
        import faster_whisper
        deps["faster_whisper"] = True
    except ImportError:
        pass

    try:
        import kokoro_onnx
        deps["kokoro_onnx"] = True
    except ImportError:
        pass

    try:
        import sounddevice
        deps["sounddevice"] = True
    except ImportError:
        pass

    return deps
