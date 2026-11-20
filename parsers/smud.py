"""Parser implementation for Sacramento Municipal Utility District (SMUD) PDF bills."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re

from models import UnitOfMeasure
from parsers.base import ParsedBill, ParsedReading, extract_regex


def can_parse(text: str) -> bool:
    """Check whether raw PDF text belongs to a SMUD electricity statement.

    Args:
        text: Full text extracted from a PDF document.

    Returns:
        True if SMUD identifiers are found in the text, False otherwise.
    """
    return "smud.org" in text.lower() or "payable to smud" in text.lower()


def _extract_readings(text: str) -> list[ParsedReading]:
    """Extract meter usage readings from the SMUD Meter Summary section.

    Args:
        text: Full text extracted from a SMUD PDF document.

    Returns:
        A list of ParsedReading instances found on the statement.
    """
    readings: list[ParsedReading] = []
    pattern = re.compile(
        r"(?:myaccount)?(\d{5,12})\s+([\d,.]+)\s+Total\s+kWh\s+(from\s+SMUD|Generation)",
        re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        meter_number = match.group(1).strip()
        usage_str = match.group(2).replace(",", "")
        readings.append(
            ParsedReading(
                meter_number=meter_number,
                usage=Decimal(usage_str),
                unit_of_measure=UnitOfMeasure.KWH,
            )
        )

    return readings


def parse(text: str, pdf_path: Path) -> ParsedBill:
    """Parse raw SMUD PDF text into a structured ParsedBill object.

    Args:
        text: Full text extracted from the SMUD PDF document.
        pdf_path: Filesystem path to the source PDF file.

    Returns:
        A populated ParsedBill instance ready for database persistence.

    Raises:
        ValueError: If any required billing field cannot be extracted or parsed.
    """
    account_num = extract_regex(r"Account Number:\s*(\d+)", text, "account_number")
    amount_str = extract_regex(
        r"Total Amount Due:\s*\$([\d,]+\.\d{2})", text, "amount_due"
    )
    due_str = extract_regex(
        r"Current Charges,\s*Due\s*(\d{2}/\d{2}/\d{2})", text, "due_date"
    )
    period_str = extract_regex(
        r"Bill Period:\s*(\d{2}/\d{2}/\d{2}\s*-\s*\d{2}/\d{2}/\d{2})",
        text,
        "billing_period",
    )

    start_raw, end_raw = [part.strip() for part in period_str.split("-")]
    start_dt = datetime.strptime(start_raw, "%m/%d/%y").date()
    end_dt = datetime.strptime(end_raw, "%m/%d/%y").date()
    due_dt = datetime.strptime(due_str, "%m/%d/%y").date()

    return ParsedBill(
        source_file=pdf_path,
        biller_name="SMUD",
        account_number=account_num,
        amount_due=Decimal(amount_str.replace(",", "")),
        due_date=due_dt,
        start_date=start_dt,
        end_date=end_dt,
        readings=_extract_readings(text),
    )
