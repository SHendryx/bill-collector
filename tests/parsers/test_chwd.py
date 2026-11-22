"""Unit and integration tests for the Citrus Heights Water District (CHWD) parser."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from models import UnitOfMeasure
from parsers import AVAILABLE_PARSERS, chwd, parse_bill_pdf
from parsers.base import ParsedReading
from tests.conftest import get_sample_pdfs

CHWD_PDFS = get_sample_pdfs("chwd")

SAMPLE_LEGACY_CHWD_TEXT = """
666 Some Rd Some City CA 99999
11111 - 0044444
Citrus Heights Water District
Visit our web site at www.chwd.org to pay bill on-line.
Billing Cycle:
02/22/2024 - 04/24/2024
Service Type Size Meter No. Service Date
Readings
Previous Current
Water Charge
Units
Domestic
1"
44444444
6525
6578
53
02/08/2024 - 04/12/2024
$196.58
Total Due by 05/16/2024
$196.58
"""

SAMPLE_NEW_CHWD_TEXT = """
ACCOUNT:
088888-000
ACCOUNT INFORMATION
SERVICE PERIOD:
BILLING DATE:
DUE DATE:
11/12/2026
10/21/2026
8/14/2026 to 10/7/2026 (55 days)
METER READING
Current Reading
Previous Reading
Cons
Reading
Reading
Date
Date
Serial No
44444444
8/14/2026
7726 10/7/2026
7817
91
Please visit www.chwd.org/billing for information on our New
Billing Portal!
BILL SUMMARY
TOTAL AMOUNT DUE
270.83
TOTAL AMOUNT DUE BY 11/12/2026
Citrus Heights Water District
"""


def test_chwd_in_available_parsers() -> None:
    """Verify the CHWD parser is registered in AVAILABLE_PARSERS."""
    assert chwd in AVAILABLE_PARSERS


def test_chwd_can_parse_detection() -> None:
    """Verify can_parse identifies both CHWD formats and rejects unrelated text."""
    assert chwd.can_parse(SAMPLE_LEGACY_CHWD_TEXT) is True
    assert chwd.can_parse(SAMPLE_NEW_CHWD_TEXT) is True
    assert chwd.can_parse("Make check payable to SMUD") is False


def test_chwd_parse_legacy_format() -> None:
    """Verify parse() extracts fields accurately from pre-August 2026 CHWD bills."""
    dummy_path = Path("chwd_apr_2024.pdf")
    parsed = chwd.parse(SAMPLE_LEGACY_CHWD_TEXT, dummy_path)

    assert parsed.source_file == dummy_path
    assert parsed.biller_name == "Citrus Heights Water District"
    assert parsed.account_number == "11111 - 0044444"
    assert parsed.amount_due == Decimal("196.58")
    assert parsed.due_date == date(2024, 5, 16)
    assert parsed.start_date == date(2024, 2, 22)
    assert parsed.end_date == date(2024, 4, 24)

    assert parsed.readings == [
        ParsedReading(
            meter_number="44444444",
            usage=Decimal("53"),
            unit_of_measure=UnitOfMeasure.CCF,
        )
    ]


def test_chwd_parse_new_xpress_format() -> None:
    """Verify parse() extracts fields accurately from post-August 2026 CHWD bills."""
    dummy_path = Path("chwd_oct_2026.pdf")
    parsed = chwd.parse(SAMPLE_NEW_CHWD_TEXT, dummy_path)

    assert parsed.source_file == dummy_path
    assert parsed.biller_name == "Citrus Heights Water District"
    assert parsed.account_number == "088888-000"
    assert parsed.amount_due == Decimal("270.83")
    assert parsed.due_date == date(2026, 11, 12)
    assert parsed.start_date == date(2026, 8, 14)
    assert parsed.end_date == date(2026, 10, 7)

    assert parsed.readings == [
        ParsedReading(
            meter_number="44444444",
            usage=Decimal("91"),
            unit_of_measure=UnitOfMeasure.CCF,
        )
    ]


@pytest.mark.skipif(
    not CHWD_PDFS,
    reason="No real CHWD PDF files found in /bills/test/chwd/.",
)
@pytest.mark.parametrize("pdf_path", CHWD_PDFS, ids=lambda p: p.name)
def test_parse_real_chwd_bills(pdf_path: Path) -> None:
    """Verify every real CHWD PDF in /bills/test/chwd/ routes and parses cleanly."""
    parsed = parse_bill_pdf(pdf_path)

    assert parsed.source_file == pdf_path
    assert parsed.biller_name == "Citrus Heights Water District"
    assert parsed.account_number
    assert parsed.amount_due > Decimal("0.00")
    assert parsed.end_date >= parsed.start_date
    assert len(parsed.readings) >= 1
