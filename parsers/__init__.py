"""PDF text extraction and dispatcher for routing utility bills to provider parsers."""

from pathlib import Path
from pypdf import PdfReader

from parsers import pge
from parsers.base import ParsedBill, ParsedReading


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract and concatenate text from all pages of a PDF file.

    Args:
        pdf_path: Filesystem path to the PDF file.

    Returns:
        Combined text content from every page separated by newlines.
    """
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_bill_pdf(pdf_path: Path) -> ParsedBill:
    """Extract text from a PDF bill and dispatch it to a matching utility parser.

    Args:
        pdf_path: Filesystem path to the PDF bill.

    Returns:
        A ParsedBill containing the scraped billing and meter usage details.

    Raises:
        ValueError: If the PDF contains no selectable text or matches no known parser.
    """
    text = extract_pdf_text(pdf_path)
    if not text.strip():
        raise ValueError(
            f"'{pdf_path.name}' contains no selectable text (may be a scanned image)."
        )

    if pge.can_parse(text):
        return pge.parse_pge_pdf(text, pdf_path)

    raise ValueError(f"No parser matched the utility provider in '{pdf_path.name}'.")


__all__ = ["ParsedBill", "ParsedReading", "extract_pdf_text", "parse_bill_pdf"]
