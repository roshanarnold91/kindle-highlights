import io

from xhtml2pdf import pisa


def html_to_pdf_bytes(html):
    """Render a full HTML document (see formatting.wrap_html_document) to PDF bytes."""
    buf = io.BytesIO()
    result = pisa.CreatePDF(io.StringIO(html), dest=buf)
    if result.err:
        raise RuntimeError("Failed to render PDF")
    return buf.getvalue()
