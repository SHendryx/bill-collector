"""Unit and integration tests for the Xfinity statement parser."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from parsers import AVAILABLE_PARSERS, parse_bill_pdf, xfinity
from tests.conftest import get_sample_pdfs

XFINITY_PDFS = get_sample_pdfs("xfinity")

SAMPLE_XFINITY_TEXT = """
Account Number
8555 66 033 1111111
Billing Date
Dec 05, 2024
Services From
Dec 10, 2024 to Jan 09, 2025
Thank you for choosing Xfinity.
Amount due
$75.00
Visit xfinity.com/customersupport
Automatic payment
Jan 01, 2025
Please pay
$75.00
"""


def test_xfinity_in_available_parsers() -> None:
    """Verify the Xfinity parser is registered in AVAILABLE_PARSERS."""
    assert xfinity in AVAILABLE_PARSERS


def test_xfinity_can_parse_detection() -> None:
    """Verify can_parse identifies Xfinity text and rejects unrelated text."""
    assert xfinity.can_parse(SAMPLE_XFINITY_TEXT) is True
    assert xfinity.can_parse("Make check payable to SMUD") is False


def test_xfinity_parse_extracts_bill() -> None:
    """Verify parse() extracts account number, dates, and amount due accurately."""
    dummy_path = Path("xfinity_dec_2024.pdf")
    parsed = xfinity.parse(SAMPLE_XFINITY_TEXT, dummy_path)

    assert parsed.source_file == dummy_path
    assert parsed.biller_name == "Xfinity"
    assert parsed.account_number == "8555 66 033 1111111"
    assert parsed.amount_due == Decimal("75.00")
    assert parsed.due_date == date(2025, 1, 1)
    assert parsed.start_date == date(2024, 12, 10)
    assert parsed.end_date == date(2025, 1, 9)
    assert parsed.readings == []


@pytest.mark.skipif(
    not XFINITY_PDFS,
    reason="No real Xfinity PDF files found in /bills/test/xfinity/.",
)
@pytest.mark.parametrize("pdf_path", XFINITY_PDFS, ids=lambda p: p.name)
def test_parse_real_xfinity_bills(pdf_path: Path) -> None:
    """Verify every real Xfinity PDF in /bills/test/xfinity/ parses cleanly."""
    parsed = parse_bill_pdf(pdf_path)

    assert parsed.source_file == pdf_path
    assert parsed.biller_name == "Xfinity"
    assert parsed.account_number
    assert parsed.amount_due > Decimal("0.00")
    assert parsed.end_date >= parsed.start_date
    assert parsed.readings == []
