"""JARVIS API - Shared dependencies."""

from typing import Optional

from fastapi import Depends

from .auth import verify_token

# Global agent instance (lazy loaded)
_agent = None
_agent_with_mcp = None


async def get_agent(use_mcp: bool = False):
    """Get or create the JARVIS agent.

    Uses lazy loading to avoid loading heavy models until first request.

    Args:
        use_mcp: Whether to load MCP tools

    Returns:
        LangGraph agent instance
    """
    global _agent, _agent_with_mcp

    if use_mcp:
        if _agent_with_mcp is None:
            from ..agent import create_agent_async
            print("[API] Loading agent with MCP tools...")
            _agent_with_mcp = await create_agent_async()
        return _agent_with_mcp
    else:
        if _agent is None:
            from ..agent import create_agent
            print("[API] Loading agent...")
            _agent = create_agent()
        return _agent


def get_session(conversation_id: Optional[str] = None):
    """Get or create a session memory instance.

    Args:
        conversation_id: Optional conversation ID to resume

    Returns:
        SessionMemory instance
    """
    from ..memory import SessionMemory
    return SessionMemory(conversation_id=conversation_id)


# Dependency for protected routes
RequireAuth = Depends(verify_token)
