from html import escape as _esc


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


def _meta_html(highlight, pref):
    meta_bits = []
    loc_str = _loc_page_str(highlight, pref)
    if loc_str:
        meta_bits.append(loc_str)
    if highlight.date_added:
        meta_bits.append(f"Added on {highlight.date_added.strftime('%d %B %Y %H:%M')}")
    if not meta_bits:
        return ""
    return (
        '<div style="margin-top:6px;font-size:12px;color:#6b7280;">'
        + _esc(" · ".join(meta_bits))
        + "</div>"
    )


def _note_callout_html(text, *, standalone, emoji=True):
    label_size = "11px" if standalone else "10px"
    label = "📝 NOTE" if emoji else "NOTE"
    return (
        '<div style="margin-top:{top}px;padding:8px 12px;background:#fef3c7;'
        'border-left:3px solid #d97706;border-radius:4px;">'
        '<div style="font-size:{size};font-weight:700;'
        'color:#92400e;margin-bottom:3px;">{label}</div>'
        '<div style="color:#78350f;white-space:pre-wrap;">{text}</div>'
        "</div>"
    ).format(top=0 if standalone else 8, size=label_size, label=label, text=_esc(text).replace("\n", "<br>"))


def format_highlight_block_html(highlight, pref, emoji=True):
    """Render one highlight/note/bookmark as a self-contained HTML block with
    inline styles, so the formatting survives paste into rich-text targets
    (Notion, Google Docs, email clients) — Notes get a distinct amber callout
    so they stand out from plain Highlights, matching the app's own UI.

    `emoji=False` omits the decorative emoji from labels — the PDF renderer
    (reportlab, via xhtml2pdf) has no emoji glyphs and would otherwise show
    tofu/missing-glyph boxes instead."""
    if highlight.type == "note":
        label = "📝 NOTE" if emoji else "NOTE"
        inner = (
            '<div style="font-size:11px;font-weight:700;'
            f'color:#6b7280;margin-bottom:4px;">{label}</div>'
            '<div style="color:#78350f;white-space:pre-wrap;">'
            + _esc(highlight.text or "").replace("\n", "<br>")
            + "</div>"
        )
        block = (
            '<div style="margin:0 0 16px 0;padding:10px 14px;background:#fef3c7;'
            'border-left:4px solid #d97706;border-radius:6px;">' + inner
        )
        block += _meta_html(highlight, pref)
        block += "</div>"
        return block

    if highlight.type == "bookmark":
        label = "🔖 Bookmark" if emoji else "Bookmark"
        block = (
            '<div style="margin:0 0 16px 0;padding:8px 14px;color:#6b7280;'
            f'font-style:italic;border-left:3px solid #d1d5db;">{label}'
        )
        block += _meta_html(highlight, pref)
        block += "</div>"
        return block

    # highlight, optionally with a merged note
    label = "🖍️ HIGHLIGHT" if emoji else "HIGHLIGHT"
    block = (
        '<div style="margin:0 0 16px 0;padding:10px 14px;background:#f8fafc;'
        'border-left:4px solid #94a3b8;border-radius:6px;">'
        '<div style="font-size:11px;font-weight:700;'
        f'color:#64748b;margin-bottom:4px;">{label}</div>'
        '<div style="color:#111827;white-space:pre-wrap;">'
        + _esc(highlight.text or "").replace("\n", "<br>")
        + "</div>"
    )
    if highlight.note:
        block += _note_callout_html(highlight.note, standalone=False, emoji=emoji)
    block += _meta_html(highlight, pref)
    block += "</div>"
    return block


def format_book_highlights_html(book, highlights, user, emoji=True):
    pref = effective_pref(user, book)
    title = _esc(book.title)
    if book.author:
        title += " — " + _esc(book.author)

    total = len(highlights)
    meta_line = f"{total} highlight{'s' if total != 1 else ''}"

    body = "".join(format_highlight_block_html(h, pref, emoji=emoji) for h in highlights)
    if not body:
        body = '<p style="color:#9ca3af;">(no highlights)</p>'

    return (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">'
        f'<h2 style="margin:0 0 4px 0;font-size:18px;">{title}</h2>'
        f'<p style="margin:0 0 16px 0;color:#6b7280;font-size:13px;">{_esc(meta_line)}</p>'
        f"{body}"
        "</div>"
    )


def wrap_html_document(title, body_html):
    """Wrap a body fragment as a standalone, self-contained HTML document
    suitable for saving/opening directly (double-clicked, imported into
    Word, opened in a browser) rather than just pasted from the clipboard."""
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f"<title>{_esc(title)}</title>\n"
        "<style>@page { size: A4; margin: 2cm; }</style>\n</head>\n"
        f'<body style="margin:0;padding:24px;background:#ffffff;">\n{body_html}\n</body>\n</html>\n'
    )
