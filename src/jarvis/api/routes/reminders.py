"""JARVIS API - Reminders endpoints."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import verify_token

router = APIRouter()

# Reminders file path
REMINDERS_FILE = Path(__file__).parent.parent.parent.parent.parent / "data" / "reminders.json"


def _load_reminders() -> list[dict]:
    """Load reminders from JSON file."""
    if not REMINDERS_FILE.exists():
        return []
    try:
        with open(REMINDERS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_reminders(reminders: list[dict]):
    """Save reminders to JSON file."""
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2, default=str)


class ReminderCreate(BaseModel):
    message: str
    due_at: datetime


class ReminderUpdate(BaseModel):
    message: Optional[str] = None
    due_at: Optional[datetime] = None
    completed: Optional[bool] = None


class ReminderResponse(BaseModel):
    id: str
    message: str
    due_at: str
    created_at: str
    completed: bool = False
    notified: bool = False


@router.get("/reminders", response_model=list[ReminderResponse])
async def list_reminders(
    filter: str = "pending",  # pending, completed, all
    _: None = Depends(verify_token),
):
    """List reminders.

    Args:
        filter: Filter by status (pending, completed, all)

    Returns:
        List of reminders
    """
    reminders = _load_reminders()

    if filter == "pending":
        reminders = [r for r in reminders if not r.get("completed", False)]
    elif filter == "completed":
        reminders = [r for r in reminders if r.get("completed", False)]

    return [
        ReminderResponse(
            id=r.get("id", ""),
            message=r.get("message", ""),
            due_at=str(r.get("due_at", "")),
            created_at=str(r.get("created_at", "")),
            completed=r.get("completed", False),
            notified=r.get("notified", False),
        )
        for r in reminders
    ]


@router.post("/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    data: ReminderCreate,
    _: None = Depends(verify_token),
):
    """Create a new reminder.

    Args:
        data: Reminder data

    Returns:
        Created reminder
    """
    import uuid

    reminders = _load_reminders()

    new_reminder = {
        "id": str(uuid.uuid4())[:8],
        "message": data.message,
        "due_at": data.due_at.isoformat(),
        "created_at": datetime.now().isoformat(),
        "completed": False,
        "notified": False,
    }

    reminders.append(new_reminder)
    _save_reminders(reminders)

    return ReminderResponse(
        id=new_reminder["id"],
        message=new_reminder["message"],
        due_at=new_reminder["due_at"],
        created_at=new_reminder["created_at"],
        completed=False,
        notified=False,
    )


@router.get("/reminders/{reminder_id}", response_model=ReminderResponse)
async def get_reminder(
    reminder_id: str,
    _: None = Depends(verify_token),
):
    """Get a specific reminder.

    Args:
        reminder_id: Reminder ID

    Returns:
        Reminder details
    """
    reminders = _load_reminders()

    for r in reminders:
        if r.get("id") == reminder_id:
            return ReminderResponse(
                id=r.get("id", ""),
                message=r.get("message", ""),
                due_at=str(r.get("due_at", "")),
                created_at=str(r.get("created_at", "")),
                completed=r.get("completed", False),
                notified=r.get("notified", False),
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Reminder {reminder_id} not found",
    )


@router.patch("/reminders/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: str,
    data: ReminderUpdate,
    _: None = Depends(verify_token),
):
    """Update a reminder.

    Args:
        reminder_id: Reminder ID
        data: Fields to update

    Returns:
        Updated reminder
    """
    reminders = _load_reminders()

    for r in reminders:
        if r.get("id") == reminder_id:
            if data.message is not None:
                r["message"] = data.message
            if data.due_at is not None:
                r["due_at"] = data.due_at.isoformat()
            if data.completed is not None:
                r["completed"] = data.completed

            _save_reminders(reminders)

            return ReminderResponse(
                id=r.get("id", ""),
                message=r.get("message", ""),
                due_at=str(r.get("due_at", "")),
                created_at=str(r.get("created_at", "")),
                completed=r.get("completed", False),
                notified=r.get("notified", False),
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Reminder {reminder_id} not found",
    )


@router.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: str,
    _: None = Depends(verify_token),
):
    """Delete a reminder.

    Args:
        reminder_id: Reminder ID
    """
    reminders = _load_reminders()
    original_len = len(reminders)

    reminders = [r for r in reminders if r.get("id") != reminder_id]

    if len(reminders) == original_len:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {reminder_id} not found",
        )

    _save_reminders(reminders)
