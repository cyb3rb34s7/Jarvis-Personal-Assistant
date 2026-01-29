"""JARVIS - Load MCP tools from JSON configuration."""

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env for API keys
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "data" / "mcp_servers.json"


def substitute_env_vars(obj: Any) -> Any:
    """Replace ${VAR} with environment variable values.

    Supports:
    - ${VAR} - full string replacement
    - Nested in strings like "Bearer ${TOKEN}"
    """
    if isinstance(obj, str):
        # Pattern to match ${VAR_NAME}
        pattern = r'\$\{([^}]+)\}'

        def replace_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, "")

        return re.sub(pattern, replace_var, obj)
    elif isinstance(obj, dict):
        return {k: substitute_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [substitute_env_vars(item) for item in obj]
    return obj


async def load_mcp_tools() -> list:
    """Load all MCP tools from config file.

    Returns:
        List of LangChain-compatible tools from MCP servers
    """
    if not CONFIG_PATH.exists():
        print(f"[MCP] No config found at {CONFIG_PATH}, skipping MCP tools")
        return []

    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[MCP] Error parsing config: {e}")
        return []

    servers = config.get("mcpServers", {})
    if not servers:
        print("[MCP] No servers configured")
        return []

    # Substitute environment variables
    servers = substitute_env_vars(servers)

    # Filter out servers with missing required env vars (empty strings)
    valid_servers = {}
    for name, server_config in servers.items():
        # Check if any required values are empty after substitution
        if server_config.get("transport") == "http":
            api_key = server_config.get("headers", {}).get("x-api-key", "")
            if not api_key and "x-api-key" in server_config.get("headers", {}):
                print(f"[MCP] Skipping {name}: missing API key")
                continue
        valid_servers[name] = server_config

    if not valid_servers:
        print("[MCP] No valid servers after env var substitution")
        return []

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        print(f"[MCP] Connecting to {len(valid_servers)} server(s): {list(valid_servers.keys())}")

        # New API: don't use context manager
        client = MultiServerMCPClient(valid_servers)
        tools = await client.get_tools()
        print(f"[MCP] Loaded {len(tools)} tools")
        return tools

    except ImportError as e:
        print(f"[MCP] langchain-mcp-adapters not installed: {e}")
        return []
    except Exception as e:
        print(f"[MCP] Error loading tools: {e}")
        return []


def get_mcp_config_path() -> Path:
    """Return the path to the MCP config file."""
    return CONFIG_PATH
