def _loc_page_str(highlight, pref):
    page = highlight.page
    location = highlight.location
    parts = []
    if pref in ("page", "both") and page:
        parts.append(f"Page {page}")
    if pref in ("location", "both") and location:
        parts.append(f"Location {location}")
    return " | ".join(parts)


def effective_pref(user, book):
    if book and book.display_pref_override:
        return book.display_pref_override
    return user.display_pref


def format_highlight_block(highlight, pref):
    type_label = {"highlight": "Highlight", "note": "Note", "bookmark": "Bookmark"}.get(
        highlight.type, highlight.type.title()
    )
    lines = [f"[{type_label}]"]
    if highlight.text:
        lines.append(highlight.text)
    if highlight.note:
        lines.append(f"Note: {highlight.note}")

    meta_bits = []
    loc_str = _loc_page_str(highlight, pref)
    if loc_str:
        meta_bits.append(loc_str)
    if highlight.date_added:
        meta_bits.append(f"Added on {highlight.date_added.strftime('%d %B %Y %H:%M')}")
    if meta_bits:
        lines.append(" | ".join(meta_bits))

    return "\n".join(lines)


def format_book_highlights(book, highlights, user):
    pref = effective_pref(user, book)
    header = f"{book.title}"
    if book.author:
        header += f" — {book.author}"

    total = len(highlights)
    meta_line = f"{total} highlight{'s' if total != 1 else ''}"

    blocks = [format_highlight_block(h, pref) for h in highlights]
    separator = "\n\n" + ("-" * 40) + "\n\n"

    body = separator.join(blocks) if blocks else "(no highlights)"

    return f"{header}\n{meta_line}\n{'=' * 40}\n\n{body}\n"
