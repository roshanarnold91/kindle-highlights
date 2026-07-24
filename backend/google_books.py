import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.googleapis.com/books/v1/volumes"


def fetch_cover(title, author):
    """Look up a book on Google Books and return (cover_url, google_books_id) or (None, None)."""
    query = f'intitle:"{title}"'
    if author:
        query += f' inauthor:"{author}"'

    params = {"q": query, "maxResults": 1}
    api_key = current_app.config.get("GOOGLE_BOOKS_API_KEY")
    if api_key:
        params["key"] = api_key

    try:
        resp = requests.get(SEARCH_URL, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Google Books lookup failed for %r: %s", title, exc)
        return None, None

    items = data.get("items") or []
    if not items:
        return None, None

    item = items[0]
    volume_id = item.get("id")
    image_links = item.get("volumeInfo", {}).get("imageLinks", {})
    cover_url = image_links.get("thumbnail") or image_links.get("smallThumbnail")
    if cover_url:
        cover_url = cover_url.replace("http://", "https://")
    return cover_url, volume_id
