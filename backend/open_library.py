import logging

import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://openlibrary.org/search.json"
COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"


def _doc_to_metadata(doc):
    cover_id = doc.get("cover_i")
    publishers = doc.get("publisher") or []
    return {
        "source": "openlibrary",
        "source_id": doc.get("key"),
        "title": doc.get("title"),
        "author": ", ".join(doc.get("author_name", [])) or None,
        "cover_url": COVER_URL.format(cover_id=cover_id) if cover_id else None,
        "description": None,
        "publisher": publishers[0] if publishers else None,
        "published_date": str(doc.get("first_publish_year")) if doc.get("first_publish_year") else None,
    }


def search_metadata(query, max_results=5):
    """Search Open Library and return a list of metadata dicts. No API key required."""
    params = {
        "q": query,
        "fields": "key,title,author_name,cover_i,first_publish_year,publisher",
        "limit": max_results,
    }
    try:
        resp = requests.get(SEARCH_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Open Library search failed for %r: %s", query, exc)
        return []

    return [_doc_to_metadata(doc) for doc in (data.get("docs") or [])]


def fetch_metadata(title, author):
    """Look up a single best-match book on Open Library, or None."""
    query = f"{title} {author}".strip() if author else title
    results = search_metadata(query, max_results=1)
    return results[0] if results else None
