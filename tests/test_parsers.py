"""Unit tests for utility bill PDF parsers and parser registry routing."""

from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest

from models import UnitOfMeasure
from parsers import AVAILABLE_PARSERS, parse_bill_pdf
from parsers.base import ParsedReading
from parsers import smud


SAMPLE_SMUD_TEXT = """
Your Electric Bill
Phone Inquiries: 1 (888) 742-7683
Account Number: 7777777
Bill Issue Date: 10/22/26
Bill Period: 09/22/26 - 10/20/26 (29 Days)
Current Charges, Due 11/18/26 $139.56
Total Amount Due: $139.56
Meter Summary
Meter Usage Type Monitor your account
on smud.org/myaccount4444444 739 Total kWh from SMUD
4444444 141 Total kWh to SMUD
2222222 355 Total kWh Generation
Make check payable to SMUD
"""


def test_smud_in_available_parsers() -> None:
    """Verify the SMUD parser is registered in AVAILABLE_PARSERS."""
    assert smud in AVAILABLE_PARSERS


def test_smud_can_parse_detection() -> None:
    """Verify can_parse identifies SMUD text and rejects unrelated text."""
    assert smud.can_parse(SAMPLE_SMUD_TEXT) is True
    assert smud.can_parse("Pacific Gas and Electric Statement") is False


def test_smud_parse_extracts_bill_and_readings() -> None:
    """Verify parse() extracts account, dates, amount, and meter readings accurately."""
    dummy_path = Path("smud_oct_2026.pdf")
    parsed = smud.parse(SAMPLE_SMUD_TEXT, dummy_path)

    assert parsed.source_file == dummy_path
    assert parsed.biller_name == "SMUD"
    assert parsed.account_number == "7777777"
    assert parsed.amount_due == Decimal("139.56")
    assert parsed.due_date == date(2026, 11, 18)
    assert parsed.start_date == date(2026, 9, 22)
    assert parsed.end_date == date(2026, 10, 20)

    assert parsed.readings == [
        ParsedReading(
            meter_number="4444444",
            usage=Decimal("739"),
            unit_of_measure=UnitOfMeasure.KWH,
        ),
        ParsedReading(
            meter_number="2222222",
            usage=Decimal("355"),
            unit_of_measure=UnitOfMeasure.KWH,
        ),
    ]


def test_parse_bill_pdf_dispatches_via_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify parse_bill_pdf routes extracted text through AVAILABLE_PARSERS."""
    monkeypatch.setattr("parsers.extract_pdf_text", lambda _: SAMPLE_SMUD_TEXT)

    parsed = parse_bill_pdf(Path("fake_smud.pdf"))
    assert parsed.biller_name == "SMUD"
    assert parsed.amount_due == Decimal("139.56")
