"""JARVIS API - Chat endpoints and WebSocket."""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from ...agent import run_agent, run_agent_async
from ...database import get_conversation
from ...memory import SessionMemory
from ..auth import verify_token
from ..deps import get_agent, get_session

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_mcp: bool = False


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    _: None = Depends(verify_token),
):
    """Send a message and get a response.

    Args:
        data: Chat request with message and optional conversation ID

    Returns:
        Assistant response with conversation ID
    """
    # Get or create session
    session = get_session(data.conversation_id)

    # Get agent
    agent = await get_agent(use_mcp=data.use_mcp)

    # Run agent with session
    if data.use_mcp:
        response = await run_agent_async(data.message, agent, session=session)
    else:
        response = run_agent(data.message, agent, session=session)

    return ChatResponse(
        response=response,
        conversation_id=session.conversation_id,
    )


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat.

    Protocol:
        Client → Server:
            { "action": "send_message", "text": "...", "conversation_id": "...", "use_mcp": false }
            { "action": "interrupt" }
            { "action": "ping" }

        Server → Client:
            { "type": "connected", "session_id": "..." }
            { "type": "response_start", "message_id": "..." }
            { "type": "response_delta", "message_id": "...", "delta": "..." }
            { "type": "response_end", "message_id": "...", "content": "..." }
            { "type": "error", "message": "...", "code": "..." }
            { "type": "pong" }
    """
    await websocket.accept()

    # Generate session ID
    import uuid
    session_id = str(uuid.uuid4())[:8]

    # Send connected event
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
    })

    # Current session (lazy initialized)
    current_session: Optional[SessionMemory] = None
    current_agent = None

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if action == "send_message":
                text = data.get("text", "").strip()
                conversation_id = data.get("conversation_id")
                use_mcp = data.get("use_mcp", False)

                if not text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty message",
                        "code": "EMPTY_MESSAGE",
                    })
                    continue

                # Get or create session
                if conversation_id:
                    if current_session is None or current_session.conversation_id != conversation_id:
                        current_session = SessionMemory(conversation_id=conversation_id)
                else:
                    if current_session is None:
                        current_session = SessionMemory()

                # Get agent (lazy load)
                if current_agent is None:
                    current_agent = await get_agent(use_mcp=use_mcp)

                # Generate message ID
                message_id = str(uuid.uuid4())[:8]

                # Send start event
                await websocket.send_json({
                    "type": "response_start",
                    "message_id": message_id,
                    "conversation_id": current_session.conversation_id,
                })

                try:
                    # Run agent
                    # Note: For streaming, we'd need to modify the agent to yield chunks
                    # For now, we send the full response at once
                    if use_mcp:
                        response = await run_agent_async(text, current_agent, session=current_session)
                    else:
                        # Run sync agent in thread pool to not block
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(
                            None,
                            lambda: run_agent(text, current_agent, session=current_session)
                        )

                    # Send response (as single delta for now)
                    await websocket.send_json({
                        "type": "response_delta",
                        "message_id": message_id,
                        "delta": response,
                    })

                    # Send end event
                    await websocket.send_json({
                        "type": "response_end",
                        "message_id": message_id,
                        "content": response,
                        "conversation_id": current_session.conversation_id,
                    })

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "code": "AGENT_ERROR",
                    })

            elif action == "interrupt":
                # TODO: Implement interrupt for TTS/long responses
                await websocket.send_json({
                    "type": "interrupted",
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}",
                    "code": "UNKNOWN_ACTION",
                })

    except WebSocketDisconnect:
        print(f"[WebSocket] Client {session_id} disconnected")
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "code": "WEBSOCKET_ERROR",
            })
        except:
            pass
