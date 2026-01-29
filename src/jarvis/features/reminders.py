"""JARVIS - Reminder system."""

import json
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..utils.notifications import show_notification

# Default data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
REMINDERS_FILE = DATA_DIR / "reminders.json"


def _parse_time_delta(time_str: str) -> Optional[timedelta]:
    """Parse a time string like '30m', '1h', '2h30m' into a timedelta."""
    time_str = time_str.lower().strip()

    # Pattern for time like "30m", "1h", "2h30m", "1h 30m"
    pattern = r'(?:(\d+)\s*h(?:ours?)?)?[\s]*(?:(\d+)\s*m(?:in(?:utes?)?)?)?'
    match = re.match(pattern, time_str)

    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        if hours or minutes:
            return timedelta(hours=hours, minutes=minutes)

    # Try seconds for testing
    sec_match = re.match(r'(\d+)\s*s(?:ec(?:onds?)?)?', time_str)
    if sec_match:
        return timedelta(seconds=int(sec_match.group(1)))

    return None


def _load_reminders() -> list:
    """Load reminders from file."""
    if REMINDERS_FILE.exists():
        try:
            return json.loads(REMINDERS_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []


def _save_reminders(reminders: list) -> None:
    """Save reminders to file."""
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REMINDERS_FILE.write_text(json.dumps(reminders, indent=2))


def _fire_reminder(reminder: dict) -> None:
    """Fire a reminder notification."""
    show_notification("JARVIS Reminder", reminder["message"])


def _check_reminders() -> None:
    """Check and fire due reminders (runs in background)."""
    while True:
        try:
            reminders = _load_reminders()
            now = datetime.now().timestamp()
            remaining = []

            for r in reminders:
                if r["due_at"] <= now:
                    _fire_reminder(r)
                else:
                    remaining.append(r)

            if len(remaining) != len(reminders):
                _save_reminders(remaining)

        except Exception:
            pass

        time.sleep(10)  # Check every 10 seconds


# Start background checker
_checker_thread = None


def start_reminder_checker():
    """Start the background reminder checker."""
    global _checker_thread
    if _checker_thread is None or not _checker_thread.is_alive():
        _checker_thread = threading.Thread(target=_check_reminders, daemon=True)
        _checker_thread.start()


def set_reminder(message: str, time_from_now: str) -> str:
    """Set a reminder.

    Args:
        message: The reminder message
        time_from_now: When to remind, e.g. "30m", "1h", "2h30m"

    Returns:
        Confirmation message
    """
    delta = _parse_time_delta(time_from_now)
    if delta is None:
        return f"Could not parse time: {time_from_now}. Use format like '30m', '1h', '2h30m'"

    due_at = datetime.now() + delta

    reminder = {
        "message": message,
        "due_at": due_at.timestamp(),
        "created_at": datetime.now().isoformat(),
        "due_at_human": due_at.strftime("%H:%M:%S")
    }

    reminders = _load_reminders()
    reminders.append(reminder)
    _save_reminders(reminders)

    # Ensure checker is running
    start_reminder_checker()

    return f"Reminder set for {due_at.strftime('%H:%M:%S')}: {message}"


def list_reminders() -> str:
    """List all pending reminders.

    Returns:
        Formatted list of reminders or "No pending reminders"
    """
    reminders = _load_reminders()

    if not reminders:
        return "No pending reminders."

    lines = ["Pending reminders:"]
    for i, r in enumerate(reminders, 1):
        due = datetime.fromtimestamp(r["due_at"]).strftime("%H:%M:%S")
        lines.append(f"{i}. [{due}] {r['message']}")

    return "\n".join(lines)
