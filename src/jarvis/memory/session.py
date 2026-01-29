"""JARVIS - Session memory management.

Handles conversation context with proper sliding window logic
to ensure tool call/response pairs are never split.
"""

import json
from typing import Optional

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from ..database import (
    Message,
    UserFact,
    add_message,
    create_conversation,
    get_conversation,
    get_recent_messages,
    get_user_facts,
    list_conversations,
    update_conversation_title,
)


class SessionMemory:
    """Manages conversation context for a single session.

    Handles:
    - Creating/resuming conversations
    - Building message history for LLM context
    - Safe sliding window (never splits tool call/response pairs)
    - Auto-generating conversation titles
    """

    def __init__(
        self,
        conversation_id: Optional[str] = None,
        context_window: int = 20,
    ):
        """Initialize session memory.

        Args:
            conversation_id: Resume existing conversation, or None for new
            context_window: Max messages to include in LLM context
        """
        self.context_window = context_window

        if conversation_id:
            # Resume existing conversation
            conv = get_conversation(conversation_id)
            if conv:
                self.conversation_id = conversation_id
            else:
                # Conversation not found, create new
                self.conversation_id = create_conversation()
        else:
            # Create new conversation
            self.conversation_id = create_conversation()

        self._title_generated = False

    def add_user_message(self, content: str) -> str:
        """Add a user message and return its ID."""
        msg_id = add_message(
            conversation_id=self.conversation_id,
            role="user",
            content=content,
        )

        # Auto-generate title from first message
        if not self._title_generated:
            self._generate_title(content)

        return msg_id

    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[list] = None,
    ) -> str:
        """Add an assistant message.

        Args:
            content: The text response
            tool_calls: List of tool calls made (if any)
        """
        metadata = None
        if tool_calls:
            # Store tool calls in metadata for reconstruction
            metadata = json.dumps({
                "tool_calls": [
                    {
                        "id": tc.get("id"),
                        "name": tc.get("name"),
                        "args": tc.get("args"),
                    }
                    for tc in tool_calls
                ]
            })

        return add_message(
            conversation_id=self.conversation_id,
            role="assistant",
            content=content,
            metadata=metadata,
        )

    def add_tool_message(
        self,
        tool_name: str,
        content: str,
        tool_call_id: str,
        tool_args: Optional[str] = None,
    ) -> str:
        """Add a tool response message."""
        return add_message(
            conversation_id=self.conversation_id,
            role="tool",
            content=content,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_call_id=tool_call_id,
        )

    def get_context_messages(self) -> list:
        """Get messages for LLM context with safe sliding window.

        Returns LangChain message objects ready for the agent.
        Ensures tool call/response pairs are never split.
        """
        # Fetch more than needed to handle edge cases
        raw_messages = get_recent_messages(
            self.conversation_id,
            limit=self.context_window + 10  # Buffer for tool pairs
        )

        if not raw_messages:
            return []

        # Apply safe sliding window
        messages = self._safe_sliding_window(raw_messages, self.context_window)

        # Convert to LangChain message format
        return self._to_langchain_messages(messages)

    def _safe_sliding_window(
        self,
        messages: list[Message],
        limit: int,
    ) -> list[Message]:
        """Apply sliding window without splitting tool call/response pairs.

        The key insight: if we're about to cut off a tool message,
        we need to also include its parent assistant message (with tool_calls).
        """
        if len(messages) <= limit:
            return messages

        # Start from the end and work backwards
        result = []
        tool_call_ids_needed = set()

        # First pass: collect recent messages and track required tool calls
        for msg in reversed(messages):
            if len(result) >= limit and not tool_call_ids_needed:
                break

            # If this is a tool response, we need its parent tool call
            if msg.role == "tool" and msg.tool_call_id:
                tool_call_ids_needed.add(msg.tool_call_id)

            # If this is an assistant message with tool calls, check if needed
            if msg.role == "assistant" and msg.metadata:
                try:
                    meta = json.loads(msg.metadata)
                    if "tool_calls" in meta:
                        for tc in meta["tool_calls"]:
                            tc_id = tc.get("id")
                            if tc_id in tool_call_ids_needed:
                                tool_call_ids_needed.discard(tc_id)
                except (json.JSONDecodeError, KeyError):
                    pass

            result.append(msg)

        # If we still have unresolved tool call IDs, we need to search further back
        if tool_call_ids_needed:
            remaining_messages = messages[:-len(result)] if result else messages
            for msg in reversed(remaining_messages):
                if not tool_call_ids_needed:
                    break
                if msg.role == "assistant" and msg.metadata:
                    try:
                        meta = json.loads(msg.metadata)
                        if "tool_calls" in meta:
                            for tc in meta["tool_calls"]:
                                if tc.get("id") in tool_call_ids_needed:
                                    result.append(msg)
                                    tool_call_ids_needed.discard(tc.get("id"))
                                    break
                    except (json.JSONDecodeError, KeyError):
                        pass

        # Reverse to get chronological order
        result.reverse()
        return result

    def _to_langchain_messages(self, messages: list[Message]) -> list:
        """Convert database messages to LangChain message objects."""
        lc_messages = []

        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))

            elif msg.role == "assistant":
                # Check for tool calls
                tool_calls = []
                if msg.metadata:
                    try:
                        meta = json.loads(msg.metadata)
                        if "tool_calls" in meta:
                            tool_calls = [
                                {
                                    "id": tc["id"],
                                    "name": tc["name"],
                                    "args": tc["args"],
                                }
                                for tc in meta["tool_calls"]
                            ]
                    except (json.JSONDecodeError, KeyError):
                        pass

                if tool_calls:
                    lc_messages.append(AIMessage(
                        content=msg.content,
                        tool_calls=tool_calls,
                    ))
                else:
                    lc_messages.append(AIMessage(content=msg.content))

            elif msg.role == "tool":
                lc_messages.append(ToolMessage(
                    content=msg.content,
                    tool_call_id=msg.tool_call_id or "",
                    name=msg.tool_name or "unknown",
                ))

            elif msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))

        return lc_messages

    def _generate_title(self, first_message: str):
        """Generate a title from the first message."""
        # Truncate to first 50 chars
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."

        update_conversation_title(self.conversation_id, title)
        self._title_generated = True

    def get_user_facts_formatted(self) -> str:
        """Get user facts formatted for system prompt injection."""
        facts = get_user_facts()
        if not facts:
            return ""

        # Group by type
        grouped: dict[str, list[UserFact]] = {}
        for fact in facts:
            if fact.fact_type not in grouped:
                grouped[fact.fact_type] = []
            grouped[fact.fact_type].append(fact)

        # Format
        lines = []
        for fact_type, type_facts in grouped.items():
            lines.append(f"{fact_type.upper()}:")
            for f in type_facts:
                lines.append(f"  - {f.key}: {f.value}")

        return "\n".join(lines)

    @property
    def is_new_conversation(self) -> bool:
        """Check if this is a new (empty) conversation."""
        messages = get_recent_messages(self.conversation_id, limit=1)
        return len(messages) == 0


def get_session_memory(
    conversation_id: Optional[str] = None,
    context_window: int = 20,
) -> SessionMemory:
    """Factory function to get a session memory instance."""
    return SessionMemory(
        conversation_id=conversation_id,
        context_window=context_window,
    )


def get_or_create_session(resume_latest: bool = False) -> SessionMemory:
    """Get a session, optionally resuming the most recent one."""
    if resume_latest:
        conversations = list_conversations(limit=1)
        if conversations:
            return SessionMemory(conversation_id=conversations[0].id)

    return SessionMemory()
