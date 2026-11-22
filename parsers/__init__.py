"""PDF text extraction, hashing, and registry dispatcher for utility bill parsers."""

import hashlib
from pathlib import Path

import pymupdf

from parsers import chwd, guild, pge, smud, xfinity
from parsers.base import BillParser, ParsedBill, ParsedReading

# Add new utility parser modules to this list as you create them
AVAILABLE_PARSERS: list[BillParser] = [
    smud,
    pge,
    chwd,
    guild,
    xfinity,
]


def compute_file_hash(file_path: Path) -> str:
    """Compute the SHA-256 hexadecimal digest of a file.

    Args:
        file_path: Filesystem path to the file to hash.

    Returns:
        64-character lowercase SHA-256 hex digest string.
    """
    with file_path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def _is_garbled_text(text: str) -> bool:
    """Detect whether extracted PDF text is empty or has corrupted font encoding.

    Args:
        text: Raw text extracted natively by PyMuPDF.

    Returns:
        True if the text is empty or lacks recognizable billing keywords/letters.
    """
    stripped = text.strip()
    if not stripped:
        return True

    non_space = [ch for ch in stripped if not ch.isspace()]
    alpha_count = sum(ch.isalpha() for ch in non_space)
    if alpha_count / len(non_space) < 0.35:
        return True

    keywords = (
        "account",
        "bill",
        "due",
        "total",
        "statement",
        "energy",
        "smud",
        "pg&e",
        "water",
    )
    lowered = stripped.lower()
    return not any(word in lowered for word in keywords)


def _extract_with_ocr(doc: pymupdf.Document) -> str:
    """Extract text from all PDF pages using PyMuPDF's built-in Tesseract OCR hook.

    Args:
        doc: An open PyMuPDF Document instance.

    Returns:
        OCR-extracted text from every page separated by newlines.
    """
    ocr_pages: list[str] = []
    for page in doc:
        textpage = page.get_textpage_ocr(language="eng", dpi=200, full=True)
        ocr_pages.append(page.get_text("text", textpage=textpage) or "")
    return "\n".join(ocr_pages)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF file, falling back to Tesseract OCR if garbled.

    Args:
        pdf_path: Filesystem path to the PDF file.

    Returns:
        Combined text content from every page separated by newlines.
    """
    with pymupdf.open(pdf_path) as doc:
        native_text = "\n".join(page.get_text("text") or "" for page in doc)
        if not _is_garbled_text(native_text):
            return native_text
        return _extract_with_ocr(doc)


def parse_bill_pdf(pdf_path: Path) -> ParsedBill:
    """Extract text from a PDF bill, compute its file hash, and dispatch to a parser.

    Args:
        pdf_path: Filesystem path to the PDF bill.

    Returns:
        A ParsedBill containing scraped details and its SHA-256 file_hash.

    Raises:
        ValueError: If the PDF contains no selectable text or matches no known parser.
    """
    text = extract_pdf_text(pdf_path)
    if not text.strip():
        raise ValueError(
            f"'{pdf_path.name}' contains no selectable text even after OCR."
        )

    for parser in AVAILABLE_PARSERS:
        if parser.can_parse(text):
            parsed = parser.parse(text, pdf_path)
            parsed.file_hash = compute_file_hash(pdf_path)
            return parsed

    raise ValueError(f"No parser matched the utility provider in '{pdf_path.name}'.")


__all__ = [
    "AVAILABLE_PARSERS",
    "BillParser",
    "ParsedBill",
    "ParsedReading",
    "compute_file_hash",
    "extract_pdf_text",
    "parse_bill_pdf",
]
