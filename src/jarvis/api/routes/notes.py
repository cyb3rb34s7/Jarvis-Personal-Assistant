"""JARVIS API - Notes endpoints."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import verify_token

router = APIRouter()

# Notes directory
NOTES_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "notes"


def _ensure_notes_dir():
    """Ensure notes directory exists."""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)


def _get_note_files() -> list[Path]:
    """Get all note files sorted by modification time."""
    _ensure_notes_dir()
    files = list(NOTES_DIR.glob("*.md"))
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files


def _generate_filename(title: str) -> str:
    """Generate a filename from title."""
    # Clean title for filename
    clean_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    clean_title = clean_title[:40].strip().replace(" ", "_")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{clean_title}.md"


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class NoteResponse(BaseModel):
    id: str  # filename without extension
    title: str
    content: str
    created_at: str
    updated_at: str


class NoteListItem(BaseModel):
    id: str
    title: str
    preview: str  # First 100 chars
    updated_at: str


@router.get("/notes", response_model=list[NoteListItem])
async def list_notes(
    _: None = Depends(verify_token),
):
    """List all notes.

    Returns:
        List of notes with preview
    """
    files = _get_note_files()

    notes = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        lines = content.split("\n")

        # Extract title (first line or filename)
        title = lines[0].lstrip("# ").strip() if lines else f.stem

        # Preview (first 100 chars of content)
        preview_content = "\n".join(lines[1:]).strip()[:100]

        notes.append(NoteListItem(
            id=f.stem,
            title=title,
            preview=preview_content,
            updated_at=datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        ))

    return notes


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    data: NoteCreate,
    _: None = Depends(verify_token),
):
    """Create a new note.

    Args:
        data: Note title and content

    Returns:
        Created note
    """
    _ensure_notes_dir()

    filename = _generate_filename(data.title)
    filepath = NOTES_DIR / filename

    # Format content with title
    full_content = f"# {data.title}\n\n{data.content}"
    filepath.write_text(full_content, encoding="utf-8")

    stat = filepath.stat()

    return NoteResponse(
        id=filepath.stem,
        title=data.title,
        content=data.content,
        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
        updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
    )


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    _: None = Depends(verify_token),
):
    """Get a specific note.

    Args:
        note_id: Note ID (filename without extension)

    Returns:
        Note content
    """
    _ensure_notes_dir()

    filepath = NOTES_DIR / f"{note_id}.md"
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )

    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Extract title
    title = lines[0].lstrip("# ").strip() if lines else note_id

    # Content without title
    body = "\n".join(lines[1:]).strip()

    stat = filepath.stat()

    return NoteResponse(
        id=note_id,
        title=title,
        content=body,
        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
        updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
    )


@router.patch("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    data: NoteUpdate,
    _: None = Depends(verify_token),
):
    """Update a note.

    Args:
        note_id: Note ID
        data: Fields to update

    Returns:
        Updated note
    """
    _ensure_notes_dir()

    filepath = NOTES_DIR / f"{note_id}.md"
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )

    # Read existing content
    existing_content = filepath.read_text(encoding="utf-8")
    lines = existing_content.split("\n")
    existing_title = lines[0].lstrip("# ").strip() if lines else note_id
    existing_body = "\n".join(lines[1:]).strip()

    # Update fields
    new_title = data.title if data.title is not None else existing_title
    new_body = data.content if data.content is not None else existing_body

    # Write updated content
    full_content = f"# {new_title}\n\n{new_body}"
    filepath.write_text(full_content, encoding="utf-8")

    stat = filepath.stat()

    return NoteResponse(
        id=note_id,
        title=new_title,
        content=new_body,
        created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
        updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
    )


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    _: None = Depends(verify_token),
):
    """Delete a note.

    Args:
        note_id: Note ID
    """
    _ensure_notes_dir()

    filepath = NOTES_DIR / f"{note_id}.md"
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )

    filepath.unlink()


@router.get("/notes/search")
async def search_notes(
    q: str,
    _: None = Depends(verify_token),
):
    """Search notes by content.

    Args:
        q: Search query

    Returns:
        List of matching notes
    """
    files = _get_note_files()
    query_lower = q.lower()

    results = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        if query_lower in content.lower():
            lines = content.split("\n")
            title = lines[0].lstrip("# ").strip() if lines else f.stem

            # Find matching snippet
            content_lower = content.lower()
            idx = content_lower.find(query_lower)
            start = max(0, idx - 50)
            end = min(len(content), idx + len(q) + 50)
            snippet = content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."

            results.append({
                "id": f.stem,
                "title": title,
                "snippet": snippet,
                "updated_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })

    return results
