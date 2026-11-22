"""Batch PDF bill import pipeline, database persistence helpers, and error reporting."""

import sqlite3
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from db import get_connection, init_db
from db.accounts import create_account, list_accounts
from db.billers import create_biller, list_billers
from db.bills import create_bill, get_bill_by_hash
from db.meter_readings import create_reading
from db.meters import create_meter, list_meters
from models import Account, Bill, Biller, Meter, MeterReading, UnitOfMeasure
from parsers import compute_file_hash, parse_bill_pdf
from parsers.base import ParsedBill


@dataclass
class ImportFailure:
    """Represents a single failed PDF import attempt with its categorized error."""

    file_path: Path
    error_type: str
    detail: str


@dataclass
class ImportReport:
    """Aggregates import counts and categorized failures across a batch run."""

    imported: int = 0
    skipped: int = 0
    failures: list[ImportFailure] = field(default_factory=list)

    @property
    def failed_count(self) -> int:
        """Return the total number of failed PDF imports."""
        return len(self.failures)

    def add_failure(self, file_path: Path, exc: Exception) -> None:
        """Classify an exception into a readable error category and record it.

        Args:
            file_path: Path to the PDF file that failed to import.
            exc: The exception raised during hashing, parsing, or database saving.
        """
        message = str(exc)
        if isinstance(exc, sqlite3.IntegrityError):
            category = "Database Constraint Error"
        elif isinstance(exc, sqlite3.Error):
            category = "Database Operational Error"
        elif "no selectable text" in message.lower():
            category = "Unreadable / Empty PDF"
        elif "no parser matched" in message.lower():
            category = "Unrecognized Utility Provider"
        elif "could not find" in message.lower():
            category = "Missing Required Field"
        else:
            category = type(exc).__name__

        self.failures.append(
            ImportFailure(file_path=file_path, error_type=category, detail=message)
        )

    def format_detailed_report(self) -> str:
        """Render a formatted summary grouping import errors by category and count.

        Returns:
            A multi-line human-readable diagnostic report string.
        """
        lines = [
            "",
            "=" * 60,
            "IMPORT RESULT REPORT",
            "=" * 60,
            f"Imported : {self.imported}",
            f"Skipped  : {self.skipped} (already in database)",
            f"Failed   : {self.failed_count}",
        ]

        if not self.failures:
            lines.append("\nNo import errors occurred.")
            lines.append("=" * 60)
            return "\n".join(lines)

        grouped: dict[str, list[ImportFailure]] = defaultdict(list)
        for failure in self.failures:
            grouped[failure.error_type].append(failure)

        sorted_groups = sorted(
            grouped.items(), key=lambda item: len(item[1]), reverse=True
        )

        lines.append("\nErrors by Category:")
        for error_type, items in sorted_groups:
            lines.append(f"  - {error_type}: {len(items)}")

        lines.append("\nDetailed Failure Breakdown:")
        for error_type, items in sorted_groups:
            lines.append(f"\n[{error_type}] ({len(items)})")
            for item in items:
                lines.append(f"  * {item.file_path}: {item.detail}")

        lines.append("=" * 60)
        return "\n".join(lines)

def get_or_create_biller(conn: sqlite3.Connection, name: str) -> Biller:
    """Fetch an existing Biller by case-insensitive name or insert a new one.

    Args:
        conn: Active SQLite database connection.
        name: Utility provider name (e.g., 'SMUD', 'PG&E').

    Returns:
        The existing or newly created Biller instance with a valid id.
    """
    for biller in list_billers(conn):
        if biller.name.lower() == name.lower():
            return biller
    return create_biller(conn, Biller(name=name))


def get_or_create_account(
    conn: sqlite3.Connection, account_number: str, biller_id: int
) -> Account:
    """Fetch an existing Account by number and biller_id or insert a new one.

    Args:
        conn: Active SQLite database connection.
        account_number: Utility account number string.
        biller_id: Foreign key id of the parent Biller.

    Returns:
        The existing or newly created Account instance with a valid id.
    """
    for account in list_accounts(conn, biller_id=biller_id):
        if account.number == account_number:
            return account
    return create_account(conn, Account(number=account_number, biller_id=biller_id))


def get_or_create_meter(
    conn: sqlite3.Connection,
    meter_number: str,
    account_id: int,
    unit_of_measure: UnitOfMeasure,
) -> Meter:
    """Fetch an existing Meter by its unique number or insert a new one.

    Searches across all accounts because meters.number is globally unique and
    physical meters persist even when a utility issues a new account number.

    Args:
        conn: Active SQLite database connection.
        meter_number: Utility meter serial or identifier number.
        account_id: Foreign key id of the parent Account if creating a new meter.
        unit_of_measure: UnitOfMeasure enum for the meter's readings.

    Returns:
        The existing or newly created Meter instance with a valid id.
    """
    for meter in list_meters(conn):
        if meter.number == meter_number:
            return meter
    return create_meter(
        conn,
        Meter(
            number=meter_number,
            account_id=account_id,
            unit_of_measure=unit_of_measure,
        ),
    )


def save_parsed_bill(conn: sqlite3.Connection, parsed: ParsedBill) -> Bill:
    """Persist a ParsedBill and its associated MeterReadings into SQLite.

    Args:
        conn: Active SQLite database connection.
        parsed: Structured billing and usage data extracted from a PDF.

    Returns:
        The newly inserted Bill record with its assigned database id.
    """
    biller = get_or_create_biller(conn, parsed.biller_name)
    assert biller.id is not None

    account = get_or_create_account(conn, parsed.account_number, biller.id)
    assert account.id is not None

    saved_bill = create_bill(
        conn,
        Bill(
            account_id=account.id,
            amount_due=parsed.amount_due,
            due_date=parsed.due_date,
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            file_hash=parsed.file_hash or None,
        ),
    )
    assert saved_bill.id is not None

    for reading in parsed.readings:
        meter = get_or_create_meter(
            conn,
            reading.meter_number,
            account.id,
            reading.unit_of_measure,
        )
        assert meter.id is not None
        create_reading(
            conn,
            MeterReading(
                meter_id=meter.id,
                bill_id=saved_bill.id,
                usage=reading.usage,
            ),
        )

    return saved_bill


def collect_pdf_files(directories: list[Path], recursive: bool = False) -> list[Path]:
    """Gather sorted PDF file paths from one or more directories.

    Args:
        directories: List of directory paths to scan for .pdf files.
        recursive: When True, searches subdirectories using rglob.

    Returns:
        Sorted list of discovered PDF Path objects.
    """
    pdf_files: list[Path] = []
    for directory in directories:
        if not directory.is_dir():
            print(f"[WARN] Skipping invalid directory: {directory}")
            continue
        matcher = directory.rglob("*.pdf") if recursive else directory.glob("*.pdf")
        pdf_files.extend(sorted(matcher))
    return pdf_files

def process_directories(
    directories: list[Path],
    db_path: Path,
    recursive: bool = False,
    show_report: bool = False,
    report_file: Path | None = None,
) -> ImportReport:
    """Scan directories for PDFs, skip duplicates, parse new bills, and save to SQLite.

    Args:
        directories: List of directories containing PDF bills.
        db_path: Path to the target SQLite database file.
        recursive: Whether to scan subdirectories recursively.
        show_report: When True, prints a categorized error report after processing.
        report_file: Optional path to write the detailed import report to disk.

    Returns:
        An ImportReport summarizing imported, skipped, and failed PDF files.
    """
    init_db(db_path)
    report = ImportReport()
    pdf_files = collect_pdf_files(directories, recursive=recursive)

    if not pdf_files:
        print("No PDF files found.")
        return report

    with closing(get_connection(db_path)) as conn:
        for pdf_path in pdf_files:
            try:
                file_hash = compute_file_hash(pdf_path)
                if get_bill_by_hash(conn, file_hash) is not None:
                    print(f"[SKIP] Already imported: {pdf_path.name}")
                    report.skipped += 1
                    continue

                parsed = parse_bill_pdf(pdf_path)
                parsed.file_hash = file_hash

                with conn:
                    save_parsed_bill(conn, parsed)

                print(
                    f"[OK]   {parsed.biller_name} | {pdf_path.name} | "
                    f"${parsed.amount_due} ({parsed.start_date} to {parsed.end_date})"
                )
                report.imported += 1
            except (ValueError, OSError, sqlite3.Error, pymupdf.FileDataError) as exc:
                print(f"[FAIL] {pdf_path.name}: {exc}")
                report.add_failure(pdf_path, exc)

    if show_report or report_file is not None:
        formatted = report.format_detailed_report()
        if show_report:
            print(formatted)
        if report_file is not None:
            report_file.write_text(formatted.lstrip("\n") + "\n", encoding="utf-8")
            print(f"Saved import report to {report_file}")
    else:
        print(
            f"\nSummary: {report.imported} imported, "
            f"{report.skipped} skipped (duplicate), {report.failed_count} failed."
        )

    return report
