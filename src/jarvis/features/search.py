"""JARVIS - Web search via DuckDuckGo."""

import re
from typing import Optional


def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo.

    Args:
        query: Search query
        max_results: Maximum number of results to return

    Returns:
        Formatted search results
    """
    try:
        import httpx

        # Use DuckDuckGo HTML search (no API key needed)
        url = "https://html.duckduckgo.com/html/"

        response = httpx.post(
            url,
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            timeout=10.0,
            follow_redirects=True
        )
        response.raise_for_status()

        # Parse results (simple regex extraction)
        html = response.text

        # Extract result snippets
        results = []

        # Pattern for result links and snippets
        link_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
        snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>([^<]*(?:<[^>]*>[^<]*)*)</a>'

        links = re.findall(link_pattern, html)
        snippets = re.findall(snippet_pattern, html)

        for i, (url, title) in enumerate(links[:max_results]):
            snippet = snippets[i] if i < len(snippets) else ""
            # Clean HTML from snippet
            snippet = re.sub(r'<[^>]+>', '', snippet).strip()
            if title.strip():
                results.append({
                    "title": title.strip(),
                    "url": url,
                    "snippet": snippet[:200]
                })

        if not results:
            return f"No results found for '{query}'."

        # Format results
        lines = [f"Search results for '{query}':"]
        for r in results:
            lines.append(f"\n🔗 {r['title']}")
            if r['snippet']:
                lines.append(f"   {r['snippet']}")

        return "\n".join(lines)

    except ImportError:
        return "Error: httpx not installed. Run: pip install httpx"
    except Exception as e:
        return f"Search error: {str(e)}"
