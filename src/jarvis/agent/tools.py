"""JARVIS - Tool definitions."""

from langchain_core.tools import tool

from ..features.reminders import set_reminder, list_reminders, start_reminder_checker
from ..features.notes import save_note, search_notes
from ..features.search import web_search as do_web_search


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A math expression like "2 + 2" or "15 * 7"

    Returns:
        The result as a string
    """
    # Safe evaluation - only allow math operations
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        return "Error: Invalid characters in expression"

    try:
        result = eval(expression)
        # Return clean integer if possible
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool
def reminder_set(message: str, time_from_now: str) -> str:
    """Set a reminder for later.

    Args:
        message: What to remind about
        time_from_now: When to remind, e.g. "30m", "1h", "2h30m", "30s"

    Returns:
        Confirmation message
    """
    return set_reminder(message, time_from_now)


@tool
def reminder_list() -> str:
    """List all pending reminders.

    Returns:
        List of reminders or "No pending reminders"
    """
    return list_reminders()


@tool
def note_save(content: str, title: str = "") -> str:
    """Save a note.

    Args:
        content: The note content to save
        title: Optional title for the note

    Returns:
        Confirmation message
    """
    return save_note(content, title if title else None)


@tool
def note_search(query: str) -> str:
    """Search saved notes.

    Args:
        query: Keywords to search for

    Returns:
        Matching notes or "No notes found"
    """
    return search_notes(query)


@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo. FREE and FAST.

    ALWAYS use this FIRST for any web search. It's free and handles most queries well.
    Only use Exa MCP tools if this returns insufficient results.

    Good for: weather, quick facts, general questions, news headlines.

    Args:
        query: What to search for

    Returns:
        Search results
    """
    return do_web_search(query)


# All tools for the agent (Exa tools come from MCP)
ALL_TOOLS = [
    calculator,
    reminder_set,
    reminder_list,
    note_save,
    note_search,
    web_search,
]


def init_tools():
    """Initialize tools that need background processes."""
    start_reminder_checker()
