"""Parser implementation for Pacific Gas and Electric (PG&E) PDF statements."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re

from models import UnitOfMeasure
from parsers.base import ParsedBill, ParsedReading, extract_regex


def can_parse(text: str) -> bool:
    """Check whether raw PDF text belongs to a PG&E energy statement.

    Args:
        text: Full text extracted from a PDF document.

    Returns:
        True if PG&E identifiers are found in the text, False otherwise.
    """
    lowered = text.lower()
    identifiers = (
        "pge.com",
        "pacific gas and electric",
        "pg&e",
        "95899-7300",
    )
    return any(identifier in lowered for identifier in identifiers)


def _extract_readings(text: str) -> list[ParsedReading]:
    """Extract gas and/or electric meter usage readings from PG&E Service Information blocks.

    Matches blocks containing a 'Meter #' followed by 'Total Usage <value> <Therms|kWh>'.

    Args:
        text: Full text extracted from a PG&E PDF document.

    Returns:
        A list of ParsedReading instances found on the statement.
    """
    readings: list[ParsedReading] = []

    pattern = re.compile(
        r"Meter\s*#\s*(\w+).*?Total\s+Usage\s+([\d,.]+)\s*(Therms|kWh)",
        re.IGNORECASE | re.DOTALL,
    )

    for match in pattern.finditer(text):
        meter_number = match.group(1).strip()
        usage_str = match.group(2).replace(",", "")
        unit_raw = match.group(3).strip().lower()

        unit = (
            UnitOfMeasure.THERMS
            if unit_raw == "therms"
            else UnitOfMeasure.KWH
        )

        readings.append(
            ParsedReading(
                meter_number=meter_number,
                usage=Decimal(usage_str),
                unit_of_measure=unit,
            )
        )

    return readings


def parse(text: str, pdf_path: Path) -> ParsedBill:
    """Parse raw PG&E PDF text into a structured ParsedBill object.

    Supports both native PDF text extraction and Tesseract OCR output across
    multiple statement layout revisions.

    Args:
        text: Full text extracted from the PG&E PDF document.
        pdf_path: Filesystem path to the source PDF file.

    Returns:
        A populated ParsedBill instance ready for database persistence.

    Raises:
        ValueError: If any required billing field cannot be extracted or parsed.
    """
    account_num = extract_regex(
        r"Account\s+(?:No|Number):?\s*([\d-]+)", text, "account_number"
    )
    amount_str = extract_regex(
        r"Total\s+Amount\s+Due(?:\s+by\s+\d{2}/\d{2}/\d{4})?:?\s*\$?([\d,]+\.\d{2})",
        text,
        "amount_due",
    )
    due_str = extract_regex(
        r"Due\s+Date:?\s*(\d{2}/\d{2}/\d{4})", text, "due_date"
    )
    period_match = re.search(
        r"(\d{2}/\d{2}/\d{4})\s*(?:to|-|–)\s*(\d{2}/\d{2}/\d{4})\s*\(\d+\s+billing\s+days\)",
        text,
        re.IGNORECASE,
    )
    if not period_match:
        raise ValueError("Could not find 'billing_period' in PG&E PDF text.")

    start_dt = datetime.strptime(period_match.group(1), "%m/%d/%Y").date()
    end_dt = datetime.strptime(period_match.group(2), "%m/%d/%Y").date()
    due_dt = datetime.strptime(due_str, "%m/%d/%Y").date()

    return ParsedBill(
        source_file=pdf_path,
        biller_name="PG&E",
        account_number=account_num,
        amount_due=Decimal(amount_str.replace(",", "")),
        due_date=due_dt,
        start_date=start_dt,
        end_date=end_dt,
        readings=_extract_readings(text),
    )
