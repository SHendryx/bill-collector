"""CLI entry point for scanning directories of PDF utility bills and importing them into SQLite."""

import argparse
from pathlib import Path

from db import DEFAULT_DB_PATH
from importer import process_directories


def main() -> None:
    """Parse command-line arguments and run the PDF bill import pipeline."""
    parser = argparse.ArgumentParser(
        description="Scrape utility bills from PDF directories into SQLite."
    )
    parser.add_argument(
        "directories",
        nargs="+",
        type=Path,
        help="One or more directories containing PDF bills.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively scan subdirectories (e.g., year folders like 2025/, 2026/).",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database file (default: {DEFAULT_DB_PATH}).",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print a detailed import report grouping errors by type and count.",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        default=None,
        help="Optional file path to save the detailed import report.",
    )
    args = parser.parse_args()
    process_directories(
        args.directories,
        args.db,
        recursive=args.recursive,
        show_report=args.report,
        report_file=args.report_file,
    )


if __name__ == "__main__":
    main()
