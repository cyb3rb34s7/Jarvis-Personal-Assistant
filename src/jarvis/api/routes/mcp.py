"""JARVIS API - MCP (Model Context Protocol) endpoints."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import verify_token

router = APIRouter()

# MCP config file path
MCP_CONFIG_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "mcp_servers.json"


def _load_mcp_config() -> dict:
    """Load MCP configuration from file."""
    if not MCP_CONFIG_PATH.exists():
        return {"mcpServers": {}}
    try:
        with open(MCP_CONFIG_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"mcpServers": {}}


def _save_mcp_config(config: dict):
    """Save MCP configuration to file."""
    MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MCP_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


@router.get("/mcp/servers")
async def list_mcp_servers(
    _: None = Depends(verify_token),
):
    """List configured MCP servers.

    Returns:
        List of MCP server configurations
    """
    config = _load_mcp_config()
    servers = config.get("mcpServers", {})

    result = []
    for name, server_config in servers.items():
        transport = server_config.get("transport", "unknown")

        server_info = {
            "name": name,
            "transport": transport,
        }

        if transport == "http":
            server_info["url"] = server_config.get("url", "N/A")
        elif transport == "stdio":
            server_info["command"] = server_config.get("command", "N/A")
            server_info["args"] = server_config.get("args", [])

        result.append(server_info)

    return {"servers": result}


@router.get("/mcp/tools")
async def list_mcp_tools(
    _: None = Depends(verify_token),
):
    """List available MCP tools.

    This attempts to load MCP tools from configured servers.

    Returns:
        List of available tools
    """
    try:
        from ...agent.mcp_loader import load_mcp_tools

        tools = await load_mcp_tools()

        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description[:200] if tool.description else "",
                }
                for tool in tools
            ],
            "count": len(tools),
        }
    except Exception as e:
        return {
            "tools": [],
            "count": 0,
            "error": str(e),
        }


@router.post("/mcp/reload")
async def reload_mcp(
    _: None = Depends(verify_token),
):
    """Reload MCP connections.

    This clears cached MCP tools and reloads from config.

    Returns:
        Reload status
    """
    from ..deps import _agent_with_mcp

    # Clear cached agent with MCP
    import jarvis.api.deps as deps
    deps._agent_with_mcp = None

    # Try to reload
    try:
        from ...agent.mcp_loader import load_mcp_tools
        tools = await load_mcp_tools()

        return {
            "status": "ok",
            "message": f"Reloaded {len(tools)} MCP tools",
            "tools_count": len(tools),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload MCP: {str(e)}",
        )


@router.get("/mcp/config")
async def get_mcp_config(
    _: None = Depends(verify_token),
):
    """Get raw MCP configuration.

    Returns:
        MCP configuration JSON
    """
    config = _load_mcp_config()

    # Mask sensitive values
    masked_config = {"mcpServers": {}}
    for name, server_config in config.get("mcpServers", {}).items():
        masked_server = dict(server_config)

        # Mask headers with API keys
        if "headers" in masked_server:
            masked_server["headers"] = {
                k: "***" if "key" in k.lower() or "token" in k.lower() else v
                for k, v in masked_server["headers"].items()
            }

        # Mask env vars with tokens
        if "env" in masked_server:
            masked_server["env"] = {
                k: "***" if "key" in k.lower() or "token" in k.lower() else v
                for k, v in masked_server["env"].items()
            }

        masked_config["mcpServers"][name] = masked_server

    return masked_config
