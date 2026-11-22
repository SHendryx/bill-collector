"""Parser implementation for Guild Mortgage PDF loan activity statements."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re

from parsers.base import ParsedBill


def can_parse(text: str) -> bool:
    """Check whether raw PDF text belongs to a Guild Mortgage statement.

    Args:
        text: Full text extracted from a PDF document.

    Returns:
        True if Guild Mortgage identifiers are found in the text, False otherwise.
    """
    lowered = text.lower()
    identifiers = (
        "guildmortgage.com",
        "guild mortgage company",
        "1-800-365-4441",
    )
    return any(identifier in lowered for identifier in identifiers)


def parse(text: str, pdf_path: Path) -> ParsedBill:
    """Parse raw Guild Mortgage PDF text into a structured ParsedBill object.

    Uses Statement Date as start_date and Payment Due Date as both due_date
    and end_date, leaving meter readings empty.

    Args:
        text: Full text extracted from the Guild Mortgage PDF document.
        pdf_path: Filesystem path to the source PDF file.

    Returns:
        A populated ParsedBill instance ready for database persistence.

    Raises:
        ValueError: If any required billing field cannot be extracted or parsed.
    """
    loan_match = re.search(r"Loan\s+Number\s*:?\s*([\d-]+)", text, re.IGNORECASE)
    if not loan_match:
        raise ValueError("Could not find 'account_number' (Loan Number) in Guild PDF text.")

    stmt_match = re.search(
        r"Statement\s+Date\s*:?\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE
    )
    if not stmt_match:
        raise ValueError("Could not find 'start_date' (Statement Date) in Guild PDF text.")

    due_match = re.search(
        r"Payment\s+Due\s+Date\s*:?\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE
    )
    if not due_match:
        raise ValueError("Could not find 'due_date' (Payment Due Date) in Guild PDF text.")

    amount_match = re.search(
        r"Total\s+Amount\s+Due\s*:?\s*\$([\d,]+\.\d{2})", text, re.IGNORECASE
    )
    if not amount_match:
        raise ValueError("Could not find 'amount_due' in Guild PDF text.")

    start_dt = datetime.strptime(stmt_match.group(1), "%m/%d/%Y").date()
    due_dt = datetime.strptime(due_match.group(1), "%m/%d/%Y").date()

    return ParsedBill(
        source_file=pdf_path,
        biller_name="Guild Mortgage",
        account_number=loan_match.group(1).strip(),
        amount_due=Decimal(amount_match.group(1).replace(",", "")),
        due_date=due_dt,
        start_date=start_dt,
        end_date=due_dt,
        readings=[],
    )
