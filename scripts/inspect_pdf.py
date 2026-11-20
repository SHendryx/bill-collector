"""CLI utility to extract and display raw text from PDF utility bills for parser development."""

import argparse
from pathlib import Path
from pypdf import PdfReader


def dump_pdf_pages(pdf_path: Path) -> str:
    """Read a PDF file and format its extracted text with clear page markers.

    Args:
        pdf_path: Filesystem path to the target PDF file.

    Returns:
        Formatted string containing page headers and extracted text for each page.

    Raises:
        FileNotFoundError: If the provided PDF path does not exist.
    """
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    sections: list[str] = []

    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text(extraction_mode='plain') or "[NO SELECTABLE TEXT ON THIS PAGE]"
        header = f"{'=' * 20} PAGE {page_num} of {len(reader.pages)} {'=' * 20}"
        sections.append(f"{header}\n{page_text}")

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
    args = parser.parse_args()

    extracted = dump_pdf_pages(args.pdf_path)

    if args.output:
        args.output.write_text(extracted, encoding="utf-8")
        print(f"Saved extracted text ({len(extracted)} chars) to {args.output}")
    else:
        print(extracted)


if __name__ == "__main__":
    main()
