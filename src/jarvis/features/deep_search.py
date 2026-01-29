"""JARVIS - Deep Search using Exa API."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

EXA_API_KEY = os.getenv("EXA_API_KEY")


def deep_search(query: str, max_results: int = 5, include_content: bool = True) -> str:
    """Perform deep semantic search using Exa API.

    Use this for complex queries where DuckDuckGo results are insufficient.
    Rate limit: 5 QPS.

    Args:
        query: Search query (can be natural language)
        max_results: Number of results (1-10)
        include_content: Whether to include page content/summary

    Returns:
        Formatted search results with content
    """
    if not EXA_API_KEY:
        return "Error: EXA_API_KEY not found in environment variables."

    try:
        from exa_py import Exa

        exa = Exa(api_key=EXA_API_KEY)

        # Perform semantic search with content extraction
        if include_content:
            result = exa.search_and_contents(
                query,
                type="auto",  # Auto-select best search type
                num_results=min(max_results, 10),
                text={"max_characters": 500},  # Get text summary
                highlights=True,  # Get relevant highlights
            )
        else:
            result = exa.search(
                query,
                type="auto",
                num_results=min(max_results, 10),
            )

        if not result.results:
            return f"No results found for deep search: '{query}'"

        # Format results
        lines = [f"Deep Search Results for '{query}':\n"]

        for i, r in enumerate(result.results, 1):
            lines.append(f"{i}. **{r.title}**")
            lines.append(f"   URL: {r.url}")

            # Add highlights if available
            if hasattr(r, 'highlights') and r.highlights:
                highlight = r.highlights[0] if r.highlights else ""
                if highlight:
                    lines.append(f"   Key info: {highlight[:300]}...")

            # Add text summary if available
            elif hasattr(r, 'text') and r.text:
                lines.append(f"   Summary: {r.text[:300]}...")

            lines.append("")

        return "\n".join(lines)

    except ImportError:
        return "Error: exa-py not installed. Run: pip install exa-py"
    except Exception as e:
        return f"Deep search error: {str(e)}"


def research_topic(query: str) -> str:
    """Perform thorough research on a topic using Exa.

    Returns comprehensive results with full content extraction.
    Use for complex research queries.

    Args:
        query: Research topic or question

    Returns:
        Detailed research results
    """
    return deep_search(query, max_results=7, include_content=True)
