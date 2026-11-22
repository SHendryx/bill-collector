"""Unit and integration tests for the PG&E utility bill parser."""

from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest

from models import UnitOfMeasure
from parsers import AVAILABLE_PARSERS, parse_bill_pdf, pge
from parsers.base import ParsedReading
from tests.conftest import get_sample_pdfs

PGE_PDFS = get_sample_pdfs("pge")

SAMPLE_PGE_TEXT = """
Account No: 5555555555-9
Statement Date:
10/07/2026
Due Date:
10/28/2026
ENERGY STATEMENT
www.pge.com/MyEnergy
Total Amount Due:
$91.33
Details of Gas Charges
09/05/2026 to 10/06/2026 (32 billing days)
Total Gas Charges
$91.33
Service Information
Meter #
55555555
Current Meter Reading
5,453
Prior Meter Reading
5,423
Difference
30
Multiplier
1.062124
Total Usage
32.000000 Therms
"""


def test_pge_in_available_parsers() -> None:
    """Verify the PG&E parser is registered in AVAILABLE_PARSERS."""
    assert pge in AVAILABLE_PARSERS


def test_pge_can_parse_detection() -> None:
    """Verify can_parse identifies PG&E text and rejects unrelated text."""
    assert pge.can_parse(SAMPLE_PGE_TEXT) is True
    assert pge.can_parse("Make check payable to SMUD") is False


def test_pge_parse_extracts_bill_and_readings() -> None:
    """Verify parse() extracts account, dates, amount, and gas therms accurately."""
    dummy_path = Path("10 Oct - PGE - 09-05-26 to 10-06-26.pdf")
    parsed = pge.parse(SAMPLE_PGE_TEXT, dummy_path)

    assert parsed.source_file == dummy_path
    assert parsed.biller_name == "PG&E"
    assert parsed.account_number == "5555555555-9"
    assert parsed.amount_due == Decimal("91.33")
    assert parsed.due_date == date(2026, 10, 28)
    assert parsed.start_date == date(2026, 9, 5)
    assert parsed.end_date == date(2026, 10, 6)

    assert parsed.readings == [
        ParsedReading(
            meter_number="55555555",
            usage=Decimal("32.000000"),
            unit_of_measure=UnitOfMeasure.THERMS,
        )
    ]


@pytest.mark.skipif(
    not PGE_PDFS,
    reason="No real PG&E PDF files found in /bills/pge/.",
)
@pytest.mark.parametrize("pdf_path", PGE_PDFS, ids=lambda p: p.name)
def test_parse_real_pge_bills(pdf_path: Path) -> None:
    """Verify every real PG&E PDF in /bills/pge/ routes and parses cleanly."""
    parsed = parse_bill_pdf(pdf_path)

    assert parsed.source_file == pdf_path
    assert parsed.biller_name == "PG&E"
    assert parsed.account_number
    assert parsed.amount_due > Decimal("0.00")
    assert parsed.end_date >= parsed.start_date
    assert len(parsed.readings) >= 1
