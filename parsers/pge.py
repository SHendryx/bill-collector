"""Parser implementation for Pacific Gas and Electric (PG&E) PDF statements."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from models import UnitOfMeasure
from parsers.base import ParsedBill, ParsedReading, extract_regex


def can_parse(text: str) -> bool:
    """Check whether raw PDF text belongs to a PG&E statement.

    Args:
        text: Full text extracted from a PDF document.

    Returns:
        True if PG&E identifiers are found in the text, False otherwise.
    """
    return "Pacific Gas and Electric" in text or "PG&E" in text


def _extract_readings(text: str) -> list[ParsedReading]:
    """Extract meter usage readings from PG&E statement text if present.

    Supports statements showing direct total usage or start/end meter reads.

    Args:
        text: Full text extracted from a PDF document.

    Returns:
        A list of ParsedReading instances found on the bill (empty if none exist).
    """
    readings: list[ParsedReading] = []
    try:
        meter_num = extract_regex(r"Meter Number:\s*(\w+)", text, "meter_number")
    except ValueError:
        return readings

    # Try direct total usage first; fall back to calculating (end - start)
    try:
        usage_str = extract_regex(r"Total Usage:\s*([\d,.]+)\s*kWh", text, "usage")
        usage = Decimal(usage_str.replace(",", ""))
    except ValueError:
        try:
            start_str = extract_regex(r"Prior Read:\s*([\d,.]+)", text, "start_value")
            end_str = extract_regex(r"Current Read:\s*([\d,.]+)", text, "end_value")
            usage = Decimal(end_str.replace(",", "")) - Decimal(
                start_str.replace(",", "")
            )
        except ValueError:
            return readings

    readings.append(
        ParsedReading(
            meter_number=meter_num,
            usage=usage,
            unit_of_measure=UnitOfMeasure.KWH,
        )
    )
    return readings


def parse_pge_pdf(text: str, pdf_path: Path) -> ParsedBill:
    """Parse raw PG&E PDF text into a structured ParsedBill object.

    Args:
        text: Full text extracted from the PDF document.
        pdf_path: Filesystem path to the source PDF file.

    Returns:
        A populated ParsedBill instance ready for database persistence.

    Raises:
        ValueError: If any required billing field cannot be extracted or parsed.
    """
    account_num = extract_regex(r"Account No:\s*([\d-]+)", text, "account_number")
    amount_str = extract_regex(
        r"Total Amount Due\s*\$([\d,]+\.\d{2})", text, "amount_due"
    )
    due_str = extract_regex(r"Due Date:\s*(\d{2}/\d{2}/\d{4})", text, "due_date")
    period_str = extract_regex(
        r"Billing Period:\s*(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})",
        text,
        "billing_period",
    )

    start_raw, end_raw = [part.strip() for part in period_str.split("-")]
    start_dt = datetime.strptime(start_raw, "%m/%d/%Y").date()
    end_dt = datetime.strptime(end_raw, "%m/%d/%Y").date()

    return ParsedBill(
        source_file=pdf_path,
        biller_name="PG&E",
        account_number=account_num,
        amount_due=Decimal(amount_str.replace(",", "")),
        due_date=datetime.strptime(due_str, "%m/%d/%Y").date(),
        start_date=start_dt,
        end_date=end_dt,
        readings=_extract_readings(text),
    )
