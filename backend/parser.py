import hashlib
import re
from datetime import datetime, timezone

SEPARATOR = "=========="

# "- Your Highlight on page 12 | Location 123-125 | Added on Sunday, 1 January 2023 09:15:32"
# "- Your Note on page 12 | Location 123 | Added on ..."
# "- Your Bookmark on page 12 | Location 123 | Added on ..."
META_RE = re.compile(
    r"-\s*Your\s+(?P<type>Highlight|Note|Bookmark)\b"
    r"(?:.*?\bpage\s+(?P<page>[\w-]+))?"
    r"(?:.*?\b[Ll]ocation\s+(?P<location>[\d-]+))?"
    r"(?:.*?\bAdded on\s+(?P<date>.+))?$",
    re.IGNORECASE,
)

DATE_FORMATS = [
    "%A, %d %B %Y %H:%M:%S",
    "%A, %B %d, %Y %I:%M:%S %p",
    "%a %b %d %H:%M:%S %Y",
    "%d %B %Y %H:%M:%S",
    "%A, %d %b %Y %H:%M:%S",
]


def _parse_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_title_author(header_line):
    header_line = header_line.strip().lstrip("﻿")
    match = re.match(r"^(.*)\(([^()]+)\)\s*$", header_line)
    if match:
        title = match.group(1).strip()
        author = match.group(2).strip()
        return title, author
    return header_line, ""


def content_hash(title, author, entry_type, location, page, text):
    key = "|".join([
        (title or "").strip().lower(),
        (author or "").strip().lower(),
        (entry_type or "").strip().lower(),
        (location or "").strip(),
        (page or "").strip(),
        (text or "").strip(),
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def parse_clippings(raw_text):
    """Parse My Clippings.txt content into a list of entry dicts."""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [b.strip("\n") for b in text.split(SEPARATOR)]
    entries = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [l for l in block.split("\n")]
        lines = [l for l in lines if l.strip() != ""] if len(lines) < 2 else lines
        if len(lines) < 2:
            continue

        header_line = lines[0]
        meta_line = lines[1]
        body_lines = lines[2:]
        body_text = "\n".join(body_lines).strip()

        title, author = _parse_title_author(header_line)
        if not title:
            continue

        m = META_RE.search(meta_line)
        if not m:
            continue

        entry_type = (m.group("type") or "Highlight").lower()
        page = (m.group("page") or "").strip() or None
        location = (m.group("location") or "").strip() or None
        date_added = _parse_date(m.group("date"))

        entries.append({
            "title": title,
            "author": author,
            "type": entry_type,
            "text": body_text,
            "location": location,
            "page": page,
            "date_added": date_added,
        })

    return entries


def _parse_loc_range(location):
    if not location:
        return None
    parts = location.split("-")
    try:
        start = int(parts[0])
        end = int(parts[-1])
    except ValueError:
        return None
    return start, end


def _find_note_target(note, highlights):
    """Kindle notes are usually pinned to a single position that falls
    within the location range of the highlight they annotate, rather than
    matching it exactly (e.g. highlight 512-514, note at 512)."""
    same_book = [
        h for h in highlights if h["title"] == note["title"] and h["author"] == note["author"]
    ]

    note_range = _parse_loc_range(note["location"])
    if note_range:
        for h in same_book:
            h_range = _parse_loc_range(h["location"])
            if h_range and h_range[0] <= note_range[0] <= h_range[1]:
                return h

    if note["page"]:
        page_matches = [h for h in same_book if h["page"] == note["page"]]
        if len(page_matches) == 1:
            return page_matches[0]

    return None


def merge_notes_into_highlights(entries):
    """Attach Note entries to the Highlight entry they annotate.
    Bookmarks and unattached notes remain standalone entries."""
    highlights = [e for e in entries if e["type"] == "highlight"]
    for h in highlights:
        h["note"] = None

    result = list(highlights)

    for e in entries:
        if e["type"] != "note":
            continue
        target = _find_note_target(e, highlights)
        if target is not None:
            target["note"] = e["text"]
        else:
            e["note"] = None
            result.append(e)

    for e in entries:
        if e["type"] == "bookmark":
            e["note"] = None
            result.append(e)

    return result
