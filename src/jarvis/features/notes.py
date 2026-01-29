"""JARVIS - Note management with BM25 search."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# Default data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
NOTES_DIR = DATA_DIR / "notes"


def _ensure_notes_dir():
    """Ensure notes directory exists."""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_filename(text: str) -> str:
    """Create a safe filename from text."""
    # Take first 30 chars, remove special chars
    safe = re.sub(r'[^\w\s-]', '', text[:30]).strip()
    safe = re.sub(r'[-\s]+', '_', safe)
    return safe or "note"


def save_note(content: str, title: Optional[str] = None) -> str:
    """Save a note to a markdown file.

    Args:
        content: The note content
        title: Optional title (auto-generated from content if not provided)

    Returns:
        Confirmation message with filename
    """
    _ensure_notes_dir()

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title_part = _sanitize_filename(title or content)
    filename = f"{timestamp}_{title_part}.md"
    filepath = NOTES_DIR / filename

    # Write note with metadata
    note_content = f"""# {title or content[:50]}

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{content}
"""

    filepath.write_text(note_content, encoding="utf-8")
    return f"Note saved: {filename}"


def search_notes(query: str, max_results: int = 5) -> str:
    """Search notes using keyword matching (BM25 for larger collections).

    Args:
        query: Search query
        max_results: Maximum number of results to return

    Returns:
        Formatted search results
    """
    _ensure_notes_dir()

    notes = list(NOTES_DIR.glob("*.md"))
    if not notes:
        return "No notes found."

    # Load all notes
    documents = []
    filenames = []
    for note_path in notes:
        try:
            content = note_path.read_text(encoding="utf-8")
            documents.append(content)
            filenames.append(note_path.name)
        except Exception:
            continue

    if not documents:
        return "No notes found."

    # For small collections (<10 notes), use simple keyword search
    # BM25's IDF doesn't work well with very few documents
    query_lower = query.lower()
    query_words = query_lower.split()

    results = []
    for fname, doc in zip(filenames, documents):
        doc_lower = doc.lower()
        # Score based on how many query words appear
        score = sum(1 for word in query_words if word in doc_lower)
        if score > 0:
            results.append((score, fname, doc))

    # Sort by score descending
    results.sort(reverse=True)
    results = results[:max_results]

    if not results:
        return f"No notes found matching '{query}'."

    # Format results
    lines = [f"Found {len(results)} note(s) matching '{query}':"]
    for score, fname, doc in results:
        # Extract first meaningful line as preview (skip markdown headers and metadata)
        preview_lines = [
            l.strip() for l in doc.split('\n')
            if l.strip()
            and not l.startswith('#')
            and not l.startswith('**')
            and not l.startswith('---')
        ]
        preview = preview_lines[0][:80] if preview_lines else "(no preview)"
        lines.append(f"\n  {fname}")
        lines.append(f"   {preview}")

    return "\n".join(lines)
