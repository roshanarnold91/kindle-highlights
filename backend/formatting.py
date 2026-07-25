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


def _note_callout_html(text, *, standalone):
    label_size = "11px" if standalone else "10px"
    return (
        '<div style="margin-top:{top}px;padding:8px 12px;background:#fef3c7;'
        'border:1px solid #f3d896;border-left:3px solid #d97706;border-radius:4px;">'
        '<div style="font-size:{size};font-weight:700;'
        'color:#92400e;margin-bottom:3px;">📝 NOTE</div>'
        '<div style="color:#78350f;white-space:pre-wrap;">{text}</div>'
        "</div>"
    ).format(top=0 if standalone else 10, size=label_size, text=_esc(text).replace("\n", "<br>"))


def format_highlight_block_html(highlight, pref):
    """Render one highlight/note/bookmark as a self-contained HTML block with
    inline styles, so the formatting survives paste into rich-text targets
    (Notion, Google Docs, email clients) — Notes get a distinct amber callout
    so they stand out from plain Highlights, matching the app's own UI.
    Each block gets a full border plus generous bottom margin (not just a
    left accent) so consecutive entries read as clearly separate cards.

    Browser/email-only — real rendering engines handle nested bordered divs
    fine. The PDF path uses format_highlight_block_pdf instead (see there
    for why)."""
    if highlight.type == "note":
        inner = (
            '<div style="font-size:11px;font-weight:700;'
            'color:#6b7280;margin-bottom:4px;">📝 NOTE</div>'
            '<div style="color:#78350f;white-space:pre-wrap;">'
            + _esc(highlight.text or "").replace("\n", "<br>")
            + "</div>"
        )
        block = (
            '<div style="margin:0 0 24px 0;padding:12px 16px;background:#fef3c7;'
            "border:1px solid #f3d896;border-left:5px solid #d97706;border-radius:6px;"
            'box-shadow:0 1px 2px rgba(0,0,0,0.06);">' + inner
        )
        block += _meta_html(highlight, pref)
        block += "</div>"
        return block

    if highlight.type == "bookmark":
        block = (
            '<div style="margin:0 0 24px 0;padding:10px 16px;color:#6b7280;'
            "background:#fbfbfb;border:1px solid #e5e7eb;border-left:4px solid #d1d5db;"
            'border-radius:6px;font-style:italic;">🔖 Bookmark'
        )
        block += _meta_html(highlight, pref)
        block += "</div>"
        return block

    # highlight, optionally with a merged note
    block = (
        '<div style="margin:0 0 24px 0;padding:12px 16px;background:#f8fafc;'
        "border:1px solid #e2e8f0;border-left:5px solid #94a3b8;border-radius:6px;"
        'box-shadow:0 1px 2px rgba(0,0,0,0.06);">'
        '<div style="font-size:11px;font-weight:700;'
        'color:#64748b;margin-bottom:4px;">🖍️ HIGHLIGHT</div>'
        '<div style="color:#111827;white-space:pre-wrap;">'
        + _esc(highlight.text or "").replace("\n", "<br>")
        + "</div>"
    )
    if highlight.note:
        block += _note_callout_html(highlight.note, standalone=False)
    block += _meta_html(highlight, pref)
    block += "</div>"
    return block


def format_book_highlights_html(book, highlights, user):
    pref = effective_pref(user, book)
    title = _esc(book.title)
    if book.author:
        title += " — " + _esc(book.author)

    total = len(highlights)
    meta_line = f"{total} highlight{'s' if total != 1 else ''}"

    body = "".join(format_highlight_block_html(h, pref) for h in highlights)
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


def _meta_pdf(highlight, pref):
    meta_bits = []
    loc_str = _loc_page_str(highlight, pref)
    if loc_str:
        meta_bits.append(loc_str)
    if highlight.date_added:
        meta_bits.append(f"Added on {highlight.date_added.strftime('%d %B %Y %H:%M')}")
    if not meta_bits:
        return ""
    return (
        '<div style="margin-top:8px;font-size:11px;color:#6b7280;">'
        + _esc(" · ".join(meta_bits))
        + "</div>"
    )


def _card_table_pdf(inner_html, *, background, border_color, accent_color, top_margin=0):
    """xhtml2pdf (via reportlab) redraws the border of a bordered <div> around
    EVERY nested block-level child instead of once around the whole box, so a
    label/text/meta stack inside one bordered div renders as several stacked
    boxes instead of a single card. Putting the border/background on a single
    <table><td> instead avoids this — xhtml2pdf treats a table cell as one
    atomic frame."""
    return (
        f'<table style="width:100%;border-collapse:collapse;margin:{top_margin}px 0 20px 0;">'
        f'<tr><td style="padding:12px 16px;background:{background};'
        f'border:1px solid {border_color};border-left:5px solid {accent_color};">'
        f"{inner_html}</td></tr></table>"
    )


def _note_card_pdf(text, *, standalone):
    label_size = "11px" if standalone else "10px"
    inner = (
        f'<div style="font-size:{label_size};font-weight:700;color:#92400e;margin-bottom:3px;">NOTE</div>'
        f'<div style="color:#78350f;">{_esc(text).replace(chr(10), "<br/>")}</div>'
    )
    return (
        '<table style="width:100%;border-collapse:collapse;margin-top:{top}px;">'
        '<tr><td style="padding:8px 12px;background:#fef3c7;'
        'border:1px solid #f3d896;border-left:3px solid #d97706;">'
        f"{inner}</td></tr></table>"
    ).format(top=0 if standalone else 10)


def format_highlight_block_pdf(highlight, pref):
    """PDF-only equivalent of format_highlight_block_html — table-based to
    avoid xhtml2pdf's repeated-border-per-child-div bug (see _card_table_pdf)
    and without emoji (reportlab has no emoji glyphs, would show tofu)."""
    if highlight.type == "note":
        inner = (
            '<div style="font-size:11px;font-weight:700;color:#6b7280;margin-bottom:4px;">NOTE</div>'
            f'<div style="color:#78350f;">{_esc(highlight.text or "").replace(chr(10), "<br/>")}</div>'
        )
        inner += _meta_pdf(highlight, pref)
        return _card_table_pdf(inner, background="#fef3c7", border_color="#f3d896", accent_color="#d97706")

    if highlight.type == "bookmark":
        inner = '<div style="font-style:italic;color:#6b7280;">Bookmark</div>'
        inner += _meta_pdf(highlight, pref)
        return _card_table_pdf(inner, background="#fbfbfb", border_color="#e5e7eb", accent_color="#d1d5db")

    inner = (
        '<div style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:4px;">HIGHLIGHT</div>'
        f'<div style="color:#111827;">{_esc(highlight.text or "").replace(chr(10), "<br/>")}</div>'
    )
    if highlight.note:
        inner += _note_card_pdf(highlight.note, standalone=False)
    inner += _meta_pdf(highlight, pref)
    return _card_table_pdf(inner, background="#f8fafc", border_color="#e2e8f0", accent_color="#94a3b8")


def format_book_highlights_pdf(book, highlights, user):
    pref = effective_pref(user, book)
    title = _esc(book.title)
    if book.author:
        title += " — " + _esc(book.author)

    total = len(highlights)
    meta_line = f"{total} highlight{'s' if total != 1 else ''}"

    body = "".join(format_highlight_block_pdf(h, pref) for h in highlights)
    if not body:
        body = '<p style="color:#9ca3af;">(no highlights)</p>'

    return (
        '<div style="font-family:Helvetica,Arial,sans-serif;">'
        f'<h2 style="margin:0 0 4px 0;font-size:18px;">{title}</h2>'
        f'<p style="margin:0 0 16px 0;color:#6b7280;font-size:13px;">{_esc(meta_line)}</p>'
        f"{body}"
        "</div>"
    )
