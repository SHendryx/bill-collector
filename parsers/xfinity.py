"""Parser implementation for Xfinity (Comcast) PDF billing statements."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re

from parsers.base import ParsedBill


def can_parse(text: str) -> bool:
    """Check whether raw PDF text belongs to an Xfinity statement.

    Args:
        text: Full text extracted from a PDF document.

    Returns:
        True if Xfinity identifiers are found in the text, False otherwise.
    """
    lowered = text.lower()
    identifiers = (
        "xfinity.com",
        "choosing xfinity",
        "comcast",
    )
    return any(identifier in lowered for identifier in identifiers)


def parse(text: str, pdf_path: Path) -> ParsedBill:
    """Parse raw Xfinity PDF text into a structured ParsedBill object.

    Extracts account number, service period dates, due/autopay date, and
    amount due with an empty readings list.

    Args:
        text: Full text extracted from the Xfinity PDF document.
        pdf_path: Filesystem path to the source PDF file.

    Returns:
        A populated ParsedBill instance ready for database persistence.

    Raises:
        ValueError: If any required billing field cannot be extracted or parsed.
    """
    acct_match = re.search(
        r"Account\s+Number\s+([\d\s]{10,25})", text, re.IGNORECASE
    )
    if not acct_match:
        raise ValueError("Could not find 'account_number' in Xfinity PDF text.")

    amount_match = re.search(
        r"Amount\s+due\s+\$([\d,]+\.\d{2})", text, re.IGNORECASE
    )
    if not amount_match:
        raise ValueError("Could not find 'amount_due' in Xfinity PDF text.")

    period_match = re.search(
        r"Services\s+From\s+([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+to\s+([A-Za-z]{3}\s+\d{1,2},\s+\d{4})",
        text,
        re.IGNORECASE,
    )
    if not period_match:
        raise ValueError("Could not find 'billing_period' in Xfinity PDF text.")

    # Supports both AutoPay ("Automatic payment\nJan 01, 2025") and standard ("Due Date\nJan 01, 2025")
    due_match = re.search(
        r"(?:Automatic\s+payment|Due\s+Date)\s+([A-Za-z]{3}\s+\d{1,2},\s+\d{4})",
        text,
        re.IGNORECASE,
    )
    if not due_match:
        raise ValueError("Could not find 'due_date' in Xfinity PDF text.")

    account_number = " ".join(acct_match.group(1).split())
    start_dt = datetime.strptime(period_match.group(1), "%b %d, %Y").date()
    end_dt = datetime.strptime(period_match.group(2), "%b %d, %Y").date()
    due_dt = datetime.strptime(due_match.group(1), "%b %d, %Y").date()

    return ParsedBill(
        source_file=pdf_path,
        biller_name="Xfinity",
        account_number=account_number,
        amount_due=Decimal(amount_match.group(1).replace(",", "")),
        due_date=due_dt,
        start_date=start_dt,
        end_date=end_dt,
        readings=[],
    )
