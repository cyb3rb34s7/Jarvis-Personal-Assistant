"""JARVIS - LangGraph agent definition (async with MCP support)."""

import asyncio
import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from .tools import ALL_TOOLS, init_tools
from .mcp_loader import load_mcp_tools

# Base system prompt (user facts injected at runtime)
BASE_SYSTEM_PROMPT = """You are JARVIS, a voice assistant. Rules:
- ALWAYS respond in English only (even if user speaks Hindi/Hinglish)
- Answer in 1-2 sentences max
- No preamble ("Sure!", "Of course!")
- Use tools when needed, report results directly

TOOL USAGE:
- Calculator: math expressions
- Reminders: reminder_set, reminder_list
- Notes: note_save, note_search

SEARCH RULES (STRICT):
1. ALWAYS use web_search (DuckDuckGo) FIRST - it's FREE
2. Use Exa MCP tools ONLY when:
   - User explicitly says "deep search", "research", or "detailed info"
   - User asks about CODE/programming → web_search_exa or get_code_context_exa
   - User asks about a COMPANY/business → company_research_exa
   - DuckDuckGo results are clearly insufficient for the query
3. NEVER use Exa for simple queries (weather, basic facts, quick lookups)

If unsure, ask one clarifying question."""

# Legacy prompt for backwards compatibility
SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


async def create_agent_async(model: str = "qwen2.5:7b-instruct"):
    """Create and return the JARVIS agent with MCP tools (async version)."""
    # Initialize background processes
    init_tools()

    # Load MCP tools from config
    mcp_tools = await load_mcp_tools()

    # Combine built-in + MCP tools
    all_tools = list(ALL_TOOLS) + list(mcp_tools)

    print(f"[Agent] Loaded {len(ALL_TOOLS)} built-in + {len(mcp_tools)} MCP tools")

    llm = ChatOllama(model=model)

    agent = create_react_agent(
        llm,
        all_tools,
        prompt=SYSTEM_PROMPT,
    )
    return agent


def create_agent(model: str = "qwen2.5:7b-instruct"):
    """Create and return the JARVIS agent (sync version, no MCP tools)."""
    # Initialize background processes
    init_tools()

    llm = ChatOllama(model=model)

    agent = create_react_agent(
        llm,
        ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )
    return agent


def _build_system_prompt(user_facts: str = "") -> str:
    """Build system prompt with user facts if available."""
    if user_facts:
        return f"{BASE_SYSTEM_PROMPT}\n\nUSER CONTEXT:\n{user_facts}"
    return BASE_SYSTEM_PROMPT


def _extract_response_and_tool_calls(result: dict) -> tuple[str, list]:
    """Extract final response and tool calls from agent result."""
    messages = result.get("messages", [])
    response = "No response generated"
    tool_calls = []

    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.type == "ai":
            response = msg.content
            # Capture tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls = [
                    {
                        "id": tc.get("id", ""),
                        "name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                    }
                    for tc in msg.tool_calls
                ]
            break

    return response, tool_calls


async def run_agent_async(
    query: str,
    agent=None,
    session=None,
) -> str:
    """Run a query through the agent with optional session memory (async version).

    Args:
        query: User's question/command
        agent: Pre-created agent (optional)
        session: SessionMemory instance for conversation context (optional)
    """
    if agent is None:
        agent = await create_agent_async()

    # Build input messages
    if session:
        # Get user facts for context
        user_facts = session.get_user_facts_formatted()
        system_prompt = _build_system_prompt(user_facts)

        # Get conversation history
        history_messages = session.get_context_messages()

        # Build full message list: system + history + new query
        input_messages = [SystemMessage(content=system_prompt)]
        input_messages.extend(history_messages)
        input_messages.append(HumanMessage(content=query))

        # Save user message to DB
        session.add_user_message(query)
    else:
        # No session - simple single-turn
        input_messages = [("user", query)]

    result = await agent.ainvoke({"messages": input_messages})

    # Extract response
    response, tool_calls = _extract_response_and_tool_calls(result)

    # Save assistant response if session provided
    if session:
        session.add_assistant_message(response, tool_calls if tool_calls else None)

        # Save tool messages if any
        for msg in result.get("messages", []):
            if msg.type == "tool":
                session.add_tool_message(
                    tool_name=getattr(msg, "name", "unknown"),
                    content=msg.content,
                    tool_call_id=getattr(msg, "tool_call_id", ""),
                )

    return response


def run_agent(
    query: str,
    agent=None,
    session=None,
) -> str:
    """Run a query through the agent with optional session memory (sync version).

    Args:
        query: User's question/command
        agent: Pre-created agent (optional)
        session: SessionMemory instance for conversation context (optional)
    """
    if agent is None:
        agent = create_agent()

    # Build input messages
    if session:
        # Get user facts for context
        user_facts = session.get_user_facts_formatted()
        system_prompt = _build_system_prompt(user_facts)

        # Get conversation history
        history_messages = session.get_context_messages()

        # Build full message list: system + history + new query
        input_messages = [SystemMessage(content=system_prompt)]
        input_messages.extend(history_messages)
        input_messages.append(HumanMessage(content=query))

        # Save user message to DB
        session.add_user_message(query)
    else:
        # No session - simple single-turn
        input_messages = [("user", query)]

    result = agent.invoke({"messages": input_messages})

    # Extract response
    response, tool_calls = _extract_response_and_tool_calls(result)

    # Save assistant response if session provided
    if session:
        session.add_assistant_message(response, tool_calls if tool_calls else None)

        # Save tool messages if any
        for msg in result.get("messages", []):
            if msg.type == "tool":
                session.add_tool_message(
                    tool_name=getattr(msg, "name", "unknown"),
                    content=msg.content,
                    tool_call_id=getattr(msg, "tool_call_id", ""),
                )

    return response


def run_agent_with_mcp(query: str, session=None) -> str:
    """Run a query with MCP tools (convenience sync wrapper)."""
    return asyncio.run(run_agent_async(query, session=session))
