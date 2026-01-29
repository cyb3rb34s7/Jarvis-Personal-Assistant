"""JARVIS - Configuration management."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import yaml
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ENV_PATH)

# Default paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
CONFIG_PATH = DATA_DIR / "config.yaml"


@dataclass
class ModelConfig:
    """LLM model configuration."""
    name: str = "qwen2.5:7b-instruct"
    temperature: float = 0.7


@dataclass
class VoiceConfig:
    """Voice input/output configuration."""
    # STT settings
    stt_model: str = "large-v3-turbo"
    stt_language: str = "hi"  # For Hinglish support
    stt_device: str = "cuda"

    # TTS settings
    tts_voice: str = "af_heart"
    tts_speed: float = 1.0

    # Hotkey
    hotkey: str = "ctrl+space"


@dataclass
class MCPConfig:
    """MCP integration configuration."""
    enabled: bool = False  # Whether to load MCP tools by default
    config_path: str = "data/mcp_servers.json"


@dataclass
class Config:
    """Main configuration."""
    model: ModelConfig = field(default_factory=ModelConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)

    # Data paths
    notes_dir: str = "data/notes"
    reminders_file: str = "data/reminders.json"

    # Logging
    verbose: bool = False
    log_file: Optional[str] = None


def load_config() -> Config:
    """Load configuration from YAML file.

    Returns:
        Config object with settings from file or defaults
    """
    config = Config()

    if not CONFIG_PATH.exists():
        # Create default config file
        save_config(config)
        return config

    try:
        with open(CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f) or {}

        # Model settings
        if "model" in data:
            model_data = data["model"]
            config.model = ModelConfig(
                name=model_data.get("name", config.model.name),
                temperature=model_data.get("temperature", config.model.temperature),
            )

        # Voice settings
        if "voice" in data:
            voice_data = data["voice"]
            config.voice = VoiceConfig(
                stt_model=voice_data.get("stt_model", config.voice.stt_model),
                stt_language=voice_data.get("stt_language", config.voice.stt_language),
                stt_device=voice_data.get("stt_device", config.voice.stt_device),
                tts_voice=voice_data.get("tts_voice", config.voice.tts_voice),
                tts_speed=voice_data.get("tts_speed", config.voice.tts_speed),
                hotkey=voice_data.get("hotkey", config.voice.hotkey),
            )

        # MCP settings
        if "mcp" in data:
            mcp_data = data["mcp"]
            config.mcp = MCPConfig(
                enabled=mcp_data.get("enabled", config.mcp.enabled),
                config_path=mcp_data.get("config_path", config.mcp.config_path),
            )

        # Other settings
        config.notes_dir = data.get("notes_dir", config.notes_dir)
        config.reminders_file = data.get("reminders_file", config.reminders_file)
        config.verbose = data.get("verbose", config.verbose)
        config.log_file = data.get("log_file", config.log_file)

    except yaml.YAMLError as e:
        print(f"[Config] Error parsing config file: {e}")
    except Exception as e:
        print(f"[Config] Error loading config: {e}")

    return config


def save_config(config: Config) -> None:
    """Save configuration to YAML file.

    Args:
        config: Config object to save
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "model": {
            "name": config.model.name,
            "temperature": config.model.temperature,
        },
        "voice": {
            "stt_model": config.voice.stt_model,
            "stt_language": config.voice.stt_language,
            "stt_device": config.voice.stt_device,
            "tts_voice": config.voice.tts_voice,
            "tts_speed": config.voice.tts_speed,
            "hotkey": config.voice.hotkey,
        },
        "mcp": {
            "enabled": config.mcp.enabled,
            "config_path": config.mcp.config_path,
        },
        "notes_dir": config.notes_dir,
        "reminders_file": config.reminders_file,
        "verbose": config.verbose,
        "log_file": config.log_file,
    }

    try:
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"[Config] Error saving config: {e}")


def get_env(key: str, default: str = "") -> str:
    """Get environment variable with fallback.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


# Global config instance (lazy loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Config object (creates default if not exists)
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Config:
    """Reload configuration from file.

    Returns:
        Fresh Config object
    """
    global _config
    _config = load_config()
    return _config
