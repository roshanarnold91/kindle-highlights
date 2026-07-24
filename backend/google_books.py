import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.googleapis.com/books/v1/volumes"


def _volume_to_metadata(item):
    info = item.get("volumeInfo", {})
    image_links = info.get("imageLinks", {})
    cover_url = image_links.get("thumbnail") or image_links.get("smallThumbnail")
    if cover_url:
        cover_url = cover_url.replace("http://", "https://")
    publishers = info.get("publisher")
    return {
        "source": "google",
        "source_id": item.get("id"),
        "title": info.get("title"),
        "author": ", ".join(info.get("authors", [])) or None,
        "cover_url": cover_url,
        "description": info.get("description"),
        "publisher": publishers,
        "published_date": info.get("publishedDate"),
    }


def search_metadata(query, max_results=5):
    """Search Google Books and return a list of metadata dicts."""
    params = {"q": query, "maxResults": max_results}
    api_key = current_app.config.get("GOOGLE_BOOKS_API_KEY")
    if api_key:
        params["key"] = api_key

    try:
        resp = requests.get(SEARCH_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Google Books search failed for %r: %s", query, exc)
        return []

    return [_volume_to_metadata(item) for item in (data.get("items") or [])]


def fetch_metadata(title, author):
    """Look up a single best-match book on Google Books.

    Returns a metadata dict (see _volume_to_metadata) or None if no match/error.
    """
    query = f'intitle:"{title}"'
    if author:
        query += f' inauthor:"{author}"'

    results = search_metadata(query, max_results=1)
    return results[0] if results else None
