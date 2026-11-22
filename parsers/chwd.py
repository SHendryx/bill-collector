"""Parser implementation for Citrus Heights Water District (CHWD) PDF statements."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re

from models import UnitOfMeasure
from parsers.base import ParsedBill, ParsedReading


def can_parse(text: str) -> bool:
    """Check whether raw PDF text belongs to a Citrus Heights Water District statement.

    Args:
        text: Full text extracted from a PDF document.

    Returns:
        True if CHWD identifiers are found in the text, False otherwise.
    """
    lowered = text.lower()
    identifiers = (
        "citrus heights water district",
        "chwd.org",
        "916.725.6873",
        "916-725-6873",
    )
    return any(identifier in lowered for identifier in identifiers)


def _is_new_xpress_format(text: str) -> bool:
    """Determine whether the CHWD text uses the post-August 2026 Xpress Bill Pay layout.

    Args:
        text: Full text extracted from a CHWD PDF document.

    Returns:
        True if the new Xpress Bill Pay format markers are present, False otherwise.
    """
    return "TOTAL AMOUNT DUE BY" in text.upper() or "METER READING" in text.upper()


def _extract_readings(text: str) -> list[ParsedReading]:
    """Extract water meter serial numbers and CCF consumption from a CHWD statement.

    Supports both the new Xpress Bill Pay layout and the legacy Invoice Cloud layout.

    Args:
        text: Full text extracted from a CHWD PDF document.

    Returns:
        A list of ParsedReading instances found on the statement.
    """
    readings: list[ParsedReading] = []

    if _is_new_xpress_format(text):
        # Matches: Serial No -> <serial> -> <prev_date> -> <prev_read> -> <curr_date> -> <curr_read> -> <cons>
        pattern = re.compile(
            r"Serial\s+No\s+(\w+)\s+\d{1,2}/\d{1,2}/\d{4}\s+[\d,]+\s+\d{1,2}/\d{1,2}/\d{4}\s+[\d,]+\s+([\d,.]+)",
            re.IGNORECASE,
        )
    else:
        # Legacy format: Domestic -> 1" -> <meter_no> -> <prev> -> <curr> -> <units>
        pattern = re.compile(
            r"Domestic\s+[\d/\"']+\s+(\w+)\s+[\d,]+\s+[\d,]+\s+([\d,.]+)",
            re.IGNORECASE,
        )

    for match in pattern.finditer(text):
        meter_number = match.group(1).strip()
        usage_str = match.group(2).replace(",", "")
        readings.append(
            ParsedReading(
                meter_number=meter_number,
                usage=Decimal(usage_str),
                unit_of_measure=UnitOfMeasure.CCF,
            )
        )

    return readings


def _parse_new_format(text: str, pdf_path: Path) -> ParsedBill:
    """Parse a post-August 2026 CHWD Xpress Bill Pay statement.

    Args:
        text: Full text extracted from the CHWD PDF document.
        pdf_path: Filesystem path to the source PDF file.

    Returns:
        A populated ParsedBill instance.

    Raises:
        ValueError: If any required billing field cannot be extracted or parsed.
    """
    acct_match = re.search(r"ACCOUNT:\s*([\d-]+)", text, re.IGNORECASE)
    if not acct_match:
        raise ValueError("Could not find 'account_number' in new CHWD PDF text.")

    amount_match = re.search(
        r"TOTAL\s+AMOUNT\s+DUE\s+\$?([\d,]+\.\d{2})", text, re.IGNORECASE
    )
    if not amount_match:
        raise ValueError("Could not find 'amount_due' in new CHWD PDF text.")

    due_match = re.search(
        r"TOTAL\s+AMOUNT\s+DUE\s+BY\s+(\d{1,2}/\d{1,2}/\d{4})",
        text,
        re.IGNORECASE,
    )
    if not due_match:
        raise ValueError("Could not find 'due_date' in new CHWD PDF text.")

    period_match = re.search(
        r"(\d{1,2}/\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{1,2}/\d{4})\s*\(\d+\s+days\)",
        text,
        re.IGNORECASE,
    )
    if not period_match:
        raise ValueError("Could not find 'billing_period' in new CHWD PDF text.")

    return ParsedBill(
        source_file=pdf_path,
        biller_name="Citrus Heights Water District",
        account_number=acct_match.group(1).strip(),
        amount_due=Decimal(amount_match.group(1).replace(",", "")),
        due_date=datetime.strptime(due_match.group(1), "%m/%d/%Y").date(),
        start_date=datetime.strptime(period_match.group(1), "%m/%d/%Y").date(),
        end_date=datetime.strptime(period_match.group(2), "%m/%d/%Y").date(),
        readings=_extract_readings(text),
    )


def _parse_legacy_format(text: str, pdf_path: Path) -> ParsedBill:
    """Parse a legacy pre-August 2026 CHWD Invoice Cloud statement.

    Args:
        text: Full text extracted from the CHWD PDF document.
        pdf_path: Filesystem path to the source PDF file.

    Returns:
        A populated ParsedBill instance.

    Raises:
        ValueError: If any required billing field cannot be extracted or parsed.
    """
    acct_match = re.search(r"\b(\d{4,6}\s*-\s*\d{5,9})\b", text)
    if not acct_match:
        raise ValueError("Could not find 'account_number' in legacy CHWD PDF text.")

    due_match = re.search(
        r"Total\s+Due\s+by\s+(\d{1,2}/\d{1,2}/\d{4})\s*\$?([\d,]+\.\d{2})",
        text,
        re.IGNORECASE,
    )
    if not due_match:
        raise ValueError("Could not find 'due_date' or 'amount_due' in legacy CHWD PDF text.")

    period_match = re.search(
        r"Billing\s+Cycle:\s*(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})",
        text,
        re.IGNORECASE,
    )
    if not period_match:
        raise ValueError("Could not find 'billing_period' in legacy CHWD PDF text.")

    return ParsedBill(
        source_file=pdf_path,
        biller_name="Citrus Heights Water District",
        account_number=acct_match.group(1).strip(),
        amount_due=Decimal(due_match.group(2).replace(",", "")),
        due_date=datetime.strptime(due_match.group(1), "%m/%d/%Y").date(),
        start_date=datetime.strptime(period_match.group(1), "%m/%d/%Y").date(),
        end_date=datetime.strptime(period_match.group(2), "%m/%d/%Y").date(),
        readings=_extract_readings(text),
    )


def parse(text: str, pdf_path: Path) -> ParsedBill:
    """Parse raw CHWD PDF text into a structured ParsedBill object.

    Automatically detects whether the statement uses the post-August 2026 Xpress
    Bill Pay layout or the legacy Invoice Cloud format.

    Args:
        text: Full text extracted from the CHWD PDF document.
        pdf_path: Filesystem path to the source PDF file.

    Returns:
        A populated ParsedBill instance ready for database persistence.

    Raises:
        ValueError: If any required billing field cannot be extracted or parsed.
    """
    if _is_new_xpress_format(text):
        return _parse_new_format(text, pdf_path)
    return _parse_legacy_format(text, pdf_path)
