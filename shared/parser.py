"""
File text extraction. Pure Python, no LLM.
Uses pdfplumber for PDFs — extracts text by spatial position so captions,
footnotes, and report text near images (X-rays, ECGs, lab graphs) are captured.
"""
import io
from typing import Optional


def extract_text(filename: str, content: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

    if ext == "pdf":
        return _extract_pdf(content, filename)
    elif ext in ("docx", "doc"):
        return _extract_docx(content)
    elif ext in ("md", "txt"):
        return content.decode("utf-8", errors="replace")
    else:
        return content.decode("utf-8", errors="replace")


def _extract_pdf(content: bytes, filename: str) -> str:
    """
    Uses pdfplumber for spatial-aware extraction — captures text that sits
    beside or below embedded images (radiology reports, ECG interpretations,
    lab result annotations, chart footnotes).
    Falls back to pypdf if pdfplumber is unavailable.
    """
    try:
        import pdfplumber
    except ImportError:
        return _extract_pdf_fallback(content)

    pages_text = []
    low_text_pages = 0

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            text = text.strip()

            # Capture table data (lab result grids, medication tables)
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row_text = "  |  ".join(
                        cell.strip() if cell else "" for cell in row
                    )
                    if row_text.strip():
                        text += "\n" + row_text

            if len(text) < 80:
                low_text_pages += 1
            if text:
                pages_text.append(text)

    combined = "\n\n".join(pages_text)

    # Warn if the PDF is mostly images with minimal text
    total_pages = low_text_pages + len(pages_text) - low_text_pages
    if total_pages > 0 and low_text_pages / max(total_pages, 1) > 0.6:
        combined = (
            "[NOTE: This PDF appears to contain mostly images (scanned document or image-heavy report). "
            "Only the text annotations, captions, and footnotes below images were extracted. "
            "If results are poor, request a text-based PDF or typed report from your source.]\n\n"
            + combined
        )

    if not combined.strip():
        raise RuntimeError(
            "No text could be extracted from this PDF. "
            "It may be a fully scanned document. "
            "Please provide the typed radiology/lab report as a separate text file."
        )

    return combined


def _extract_pdf_fallback(content: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        combined = "\n\n".join(p for p in pages if p.strip())
        if not combined.strip():
            raise RuntimeError("No text extracted.")
        return combined
    except ImportError:
        raise RuntimeError(
            "Neither pdfplumber nor pypdf is installed. "
            "Run: pip install pdfplumber"
        )


def _extract_docx(content: bytes) -> str:
    """
    Extracts paragraphs and table cells. Captions on images in DOCX files
    are stored as normal paragraphs and will be included.
    """
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
    except ImportError:
        raise RuntimeError(
            "python-docx not installed. Run: pip install python-docx"
        )

    parts = []

    for block in doc.element.body:
        tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

        if tag == "p":
            from docx.oxml.ns import qn
            text = "".join(
                node.text or ""
                for node in block.iter()
                if node.tag == qn("w:t")
            )
            if text.strip():
                parts.append(text.strip())

        elif tag == "tbl":
            # Tables contain lab values, medication grids, etc.
            from docx.oxml.ns import qn
            rows = block.findall(".//" + qn("w:tr"))
            for row in rows:
                cells = row.findall(".//" + qn("w:tc"))
                row_text = "  |  ".join(
                    "".join(n.text or "" for n in cell.iter() if n.tag == qn("w:t")).strip()
                    for cell in cells
                )
                if row_text.strip():
                    parts.append(row_text)

    if not parts:
        raise RuntimeError(
            "No text could be extracted from this DOCX file. "
            "It may contain only images without captions."
        )

    return "\n\n".join(parts)
