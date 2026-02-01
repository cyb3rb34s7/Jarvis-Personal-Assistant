"""JARVIS API - Conversations endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...database import (
    create_conversation,
    get_conversation,
    get_messages,
    list_conversations,
    update_conversation_title,
)
from ..auth import verify_token

router = APIRouter()


# Pydantic models for request/response
class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tool_name: Optional[str] = None
    tool_args: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str
    archived: bool = False

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    messages: list[MessageResponse]


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_all_conversations(
    limit: int = 50,
    include_archived: bool = False,
    _: None = Depends(verify_token),
):
    """List all conversations.

    Args:
        limit: Maximum number of conversations to return
        include_archived: Include archived conversations

    Returns:
        List of conversations ordered by last update
    """
    conversations = list_conversations(limit=limit, include_archived=include_archived)
    return [
        ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=str(c.created_at),
            updated_at=str(c.updated_at),
            archived=c.archived,
        )
        for c in conversations
    ]


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    data: ConversationCreate,
    _: None = Depends(verify_token),
):
    """Create a new conversation.

    Args:
        data: Optional title for the conversation

    Returns:
        Created conversation
    """
    conv_id = create_conversation(title=data.title)
    conv = get_conversation(conv_id)

    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=str(conv.created_at),
        updated_at=str(conv.updated_at),
        archived=conv.archived,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation_with_messages(
    conversation_id: str,
    _: None = Depends(verify_token),
):
    """Get a conversation with all its messages.

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation with messages
    """
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    messages = get_messages(conversation_id)

    return ConversationWithMessages(
        id=conv.id,
        title=conv.title,
        created_at=str(conv.created_at),
        updated_at=str(conv.updated_at),
        archived=conv.archived,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                tool_name=m.tool_name,
                tool_args=m.tool_args,
                created_at=str(m.created_at) if m.created_at else None,
            )
            for m in messages
        ],
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    _: None = Depends(verify_token),
):
    """Update a conversation's title.

    Args:
        conversation_id: Conversation ID
        data: New title

    Returns:
        Updated conversation
    """
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    update_conversation_title(conversation_id, data.title)
    conv = get_conversation(conversation_id)

    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=str(conv.created_at),
        updated_at=str(conv.updated_at),
        archived=conv.archived,
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    _: None = Depends(verify_token),
):
    """Delete a conversation.

    Note: This archives the conversation rather than hard deleting it.

    Args:
        conversation_id: Conversation ID
    """
    from ...database import get_connection

    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    # Soft delete (archive)
    with get_connection() as conn:
        conn.execute(
            "UPDATE conversations SET archived = TRUE WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
