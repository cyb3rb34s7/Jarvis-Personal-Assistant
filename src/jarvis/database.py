"""JARVIS - SQLite database setup and management."""

import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Database file location
DB_PATH = Path(__file__).parent.parent.parent / "data" / "jarvis.db"


def get_db_path() -> Path:
    """Get database file path, ensure parent directory exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_connection():
    """Get a database connection with proper cleanup."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database with schema."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                archived BOOLEAN DEFAULT FALSE
            )
        """)

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'tool', 'system')),
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'text',
                tool_name TEXT,
                tool_args TEXT,
                tool_call_id TEXT,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)

        # Reminders table (migrated from JSON)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id TEXT PRIMARY KEY,
                message TEXT NOT NULL,
                due_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                notified BOOLEAN DEFAULT FALSE
            )
        """)

        # Notes metadata (content stays in markdown files)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT,
                file_path TEXT NOT NULL UNIQUE,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        """)

        # Tool usage stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                query TEXT,
                success BOOLEAN,
                used_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User preferences / facts (long-term memory)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id TEXT PRIMARY KEY,
                fact_type TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                UNIQUE(fact_type, key)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(due_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_facts_type ON user_facts(fact_type)")

        conn.commit()


# Data classes for typed access
@dataclass
class Conversation:
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    archived: bool = False


@dataclass
class Message:
    id: str
    conversation_id: str
    role: str
    content: str
    message_type: str = "text"
    tool_name: Optional[str] = None
    tool_args: Optional[str] = None
    tool_call_id: Optional[str] = None  # Links tool response to tool call
    metadata: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class UserFact:
    id: str
    fact_type: str
    key: str
    value: str
    confidence: float = 1.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())[:8]


# Conversation CRUD
def create_conversation(title: Optional[str] = None) -> str:
    """Create a new conversation, return its ID."""
    conv_id = generate_id()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (id, title) VALUES (?, ?)",
            (conv_id, title)
        )
        conn.commit()
    return conv_id


def get_conversation(conv_id: str) -> Optional[Conversation]:
    """Get a conversation by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conv_id,)
        ).fetchone()
        if row:
            return Conversation(
                id=row["id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                archived=bool(row["archived"])
            )
    return None


def list_conversations(limit: int = 50, include_archived: bool = False) -> list[Conversation]:
    """List recent conversations."""
    with get_connection() as conn:
        query = "SELECT * FROM conversations"
        if not include_archived:
            query += " WHERE archived = FALSE"
        query += " ORDER BY updated_at DESC LIMIT ?"

        rows = conn.execute(query, (limit,)).fetchall()
        return [
            Conversation(
                id=row["id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                archived=bool(row["archived"])
            )
            for row in rows
        ]


def update_conversation_title(conv_id: str, title: str):
    """Update conversation title."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, conv_id)
        )
        conn.commit()


# Message CRUD
def add_message(
    conversation_id: str,
    role: str,
    content: str,
    message_type: str = "text",
    tool_name: Optional[str] = None,
    tool_args: Optional[str] = None,
    tool_call_id: Optional[str] = None,
    metadata: Optional[str] = None
) -> str:
    """Add a message to a conversation."""
    msg_id = generate_id()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO messages
               (id, conversation_id, role, content, message_type, tool_name, tool_args, tool_call_id, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (msg_id, conversation_id, role, content, message_type, tool_name, tool_args, tool_call_id, metadata)
        )
        # Update conversation timestamp
        conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
    return msg_id


def get_messages(conversation_id: str, limit: int = 100) -> list[Message]:
    """Get messages for a conversation, ordered by creation time."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM messages
               WHERE conversation_id = ?
               ORDER BY created_at ASC
               LIMIT ?""",
            (conversation_id, limit)
        ).fetchall()

        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                message_type=row["message_type"],
                tool_name=row["tool_name"],
                tool_args=row["tool_args"],
                tool_call_id=row["tool_call_id"],
                metadata=row["metadata"],
                created_at=row["created_at"]
            )
            for row in rows
        ]


def get_recent_messages(conversation_id: str, limit: int = 10) -> list[Message]:
    """Get the N most recent messages (for context window).

    Note: This fetches slightly more than limit to ensure we don't
    cut off tool call/response pairs. The session memory handles
    the sliding window logic properly.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM (
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ) ORDER BY created_at ASC""",
            (conversation_id, limit)
        ).fetchall()

        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                message_type=row["message_type"],
                tool_name=row["tool_name"],
                tool_args=row["tool_args"],
                tool_call_id=row["tool_call_id"],
                metadata=row["metadata"],
                created_at=row["created_at"]
            )
            for row in rows
        ]


# User facts (long-term memory)
def set_user_fact(fact_type: str, key: str, value: str, confidence: float = 1.0):
    """Set or update a user fact."""
    fact_id = generate_id()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO user_facts (id, fact_type, key, value, confidence)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(fact_type, key) DO UPDATE SET
               value = excluded.value,
               confidence = excluded.confidence,
               updated_at = CURRENT_TIMESTAMP""",
            (fact_id, fact_type, key, value, confidence)
        )
        conn.commit()


def get_user_facts(fact_type: Optional[str] = None) -> list[UserFact]:
    """Get user facts, optionally filtered by type."""
    with get_connection() as conn:
        if fact_type:
            rows = conn.execute(
                "SELECT * FROM user_facts WHERE fact_type = ? ORDER BY updated_at DESC",
                (fact_type,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM user_facts ORDER BY fact_type, key"
            ).fetchall()

        return [
            UserFact(
                id=row["id"],
                fact_type=row["fact_type"],
                key=row["key"],
                value=row["value"],
                confidence=row["confidence"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]


# Tool usage tracking
def log_tool_usage(tool_name: str, query: Optional[str] = None, success: bool = True):
    """Log tool usage for analytics."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tool_usage (tool_name, query, success) VALUES (?, ?, ?)",
            (tool_name, query, success)
        )
        conn.commit()


# Initialize on import
init_db()
