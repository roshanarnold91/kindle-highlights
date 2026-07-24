import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser import content_hash, merge_notes_into_highlights, parse_clippings

SAMPLE = (
    "Atomic Habits (James Clear)\n"
    "- Your Highlight on page 34 | Location 512-514 | Added on Monday, 3 January 2022 21:15:03\n"
    "\n"
    "You do not rise to the level of your goals. You fall to the level of your systems.\n"
    "==========\n"
    "Atomic Habits (James Clear)\n"
    "- Your Note on page 34 | Location 512 | Added on Monday, 3 January 2022 21:16:10\n"
    "\n"
    "Key idea for habit design\n"
    "==========\n"
    "Atomic Habits (James Clear)\n"
    "- Your Bookmark on page 40 | Location 601 | Added on Tuesday, 4 January 2022 08:00:00\n"
    "\n"
    "==========\n"
    "Deep Work (Cal Newport)\n"
    "- Your Highlight on Location 88-90 | Added on Wednesday, 5 January 2022 10:00:00\n"
    "\n"
    "The ability to perform deep work is becoming increasingly rare.\n"
    "==========\n"
)


def test_parse_clippings_extracts_all_entry_types():
    entries = parse_clippings(SAMPLE)
    assert len(entries) == 4

    highlight = entries[0]
    assert highlight["title"] == "Atomic Habits"
    assert highlight["author"] == "James Clear"
    assert highlight["type"] == "highlight"
    assert highlight["page"] == "34"
    assert highlight["location"] == "512-514"
    assert highlight["date_added"] is not None
    assert "systems" in highlight["text"]

    note = entries[1]
    assert note["type"] == "note"
    assert note["text"] == "Key idea for habit design"

    bookmark = entries[2]
    assert bookmark["type"] == "bookmark"
    assert bookmark["page"] == "40"

    location_only = entries[3]
    assert location_only["title"] == "Deep Work"
    assert location_only["page"] is None
    assert location_only["location"] == "88-90"


def test_merge_notes_into_highlights_attaches_matching_note():
    entries = parse_clippings(SAMPLE)
    merged = merge_notes_into_highlights(entries)

    highlight_entries = [e for e in merged if e["type"] == "highlight" and e["title"] == "Atomic Habits"]
    assert len(highlight_entries) == 1
    assert highlight_entries[0]["note"] == "Key idea for habit design"

    note_entries = [e for e in merged if e["type"] == "note"]
    assert note_entries == []

    bookmark_entries = [e for e in merged if e["type"] == "bookmark"]
    assert len(bookmark_entries) == 1


def test_content_hash_is_stable_and_distinguishes_entries():
    h1 = content_hash("Atomic Habits", "James Clear", "highlight", "512-514", "34", "text")
    h2 = content_hash("Atomic Habits", "James Clear", "highlight", "512-514", "34", "text")
    h3 = content_hash("Atomic Habits", "James Clear", "highlight", "515-516", "35", "other text")

    assert h1 == h2
    assert h1 != h3
