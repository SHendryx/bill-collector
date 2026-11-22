"""Unit and integration tests for the Guild Mortgage statement parser."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from parsers import AVAILABLE_PARSERS, guild, parse_bill_pdf
from tests.conftest import get_sample_pdfs

GUILD_PDFS = get_sample_pdfs("guild")

SAMPLE_GUILD_TEXT = """
P O Box 88888
Some City, CA 92222-5555
Customer Service: 1-888-555-4444
www.guildmortgage.com
Statement Date
12/01/2023
LOAN ACTIVITY STATEMENT
Loan Number
111-3333333
Payment Due Date
01/01/2024
Amount Due
$3,606.71
Total Amount Due
$3,606.71
Made Payable to: GUILD MORTGAGE COMPANY
"""


def test_guild_in_available_parsers() -> None:
    """Verify the Guild Mortgage parser is registered in AVAILABLE_PARSERS."""
    assert guild in AVAILABLE_PARSERS


def test_guild_can_parse_detection() -> None:
    """Verify can_parse identifies Guild Mortgage text and rejects unrelated text."""
    assert guild.can_parse(SAMPLE_GUILD_TEXT) is True
    assert guild.can_parse("Make check payable to SMUD") is False


def test_guild_parse_extracts_bill() -> None:
    """Verify parse() extracts loan number, dates, and amount due accurately."""
    dummy_path = Path("guild_jan_2024.pdf")
    parsed = guild.parse(SAMPLE_GUILD_TEXT, dummy_path)

    assert parsed.source_file == dummy_path
    assert parsed.biller_name == "Guild Mortgage"
    assert parsed.account_number == "111-3333333"
    assert parsed.amount_due == Decimal("3606.71")
    assert parsed.due_date == date(2024, 1, 1)
    assert parsed.start_date == date(2023, 12, 1)
    assert parsed.end_date == date(2024, 1, 1)
    assert parsed.readings == []


@pytest.mark.skipif(
    not GUILD_PDFS,
    reason="No real Guild Mortgage PDF files found in /bills/test/guild/.",
)
@pytest.mark.parametrize("pdf_path", GUILD_PDFS, ids=lambda p: p.name)
def test_parse_real_guild_bills(pdf_path: Path) -> None:
    """Verify every real Guild Mortgage PDF in /bills/test/guild/ parses cleanly."""
    parsed = parse_bill_pdf(pdf_path)

    assert parsed.source_file == pdf_path
    assert parsed.biller_name == "Guild Mortgage"
    assert parsed.account_number
    assert parsed.amount_due > Decimal("0.00")
    assert parsed.end_date >= parsed.start_date
    assert parsed.readings == []
