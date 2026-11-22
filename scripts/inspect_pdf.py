"""CLI utility to extract and display raw text from PDF utility bills for parser development."""

import argparse
from pathlib import Path
import pymupdf

from parsers import _is_garbled_text


def dump_pdf_pages(pdf_path: Path, force_ocr: bool = False) -> str:
    """Read a PDF file and format its extracted text with page markers.

    Automatically falls back to Tesseract OCR if native text is garbled or empty.

    Args:
        pdf_path: Filesystem path to the target PDF file.
        force_ocr: When True, forces Tesseract OCR even if native text looks valid.

    Returns:
        Formatted string containing page headers and extracted text for each page.

    Raises:
        FileNotFoundError: If the provided PDF path does not exist.
    """
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    sections: list[str] = []
    with pymupdf.open(pdf_path) as doc:
        total_pages = len(doc)
        native_all = "\n".join(page.get_text("text") or "" for page in doc)
        use_ocr = force_ocr or _is_garbled_text(native_all)

        for page_num, page in enumerate(doc, start=1):
            if use_ocr:
                tp = page.get_textpage_ocr(language="eng", dpi=200, full=True)
                page_text = page.get_text("text", textpage=tp) or "[NO TEXT FOUND]"
                mode_tag = " [OCR]"
            else:
                page_text = page.get_text("text") or "[NO SELECTABLE TEXT ON THIS PAGE]"
                mode_tag = ""

            header = f"{'=' * 18} PAGE {page_num} of {total_pages}{mode_tag} {'=' * 18}"
            sections.append(f"{header}\n{page_text.strip()}")

    return "\n\n".join(sections)


def main() -> None:
    """Parse CLI arguments and print or save the extracted PDF text."""
    parser = argparse.ArgumentParser(
        description="Inspect raw text extracted from a PDF bill to help write regex parsers."
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the PDF bill file to inspect.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Optional path to save the extracted text to a .txt file.",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Force Tesseract OCR extraction even if native text is present.",
    )
    args = parser.parse_args()

    extracted = dump_pdf_pages(args.pdf_path, force_ocr=args.ocr)

    if args.output:
        args.output.write_text(extracted, encoding="utf-8")
        print(f"Saved extracted text ({len(extracted)} chars) to {args.output}")
    else:
        print(extracted)


if __name__ == "__main__":
    main()
