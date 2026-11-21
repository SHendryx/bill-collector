"""Tests for the central parser registry and PDF routing dispatcher."""

from pathlib import Path
import pytest

from parsers import AVAILABLE_PARSERS, parse_bill_pdf


def test_available_parsers_is_not_empty() -> None:
    """Verify at least one parser is registered in AVAILABLE_PARSERS."""
    assert len(AVAILABLE_PARSERS) > 0


def test_parse_bill_pdf_raises_on_unrecognized_biller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify parse_bill_pdf raises ValueError when no parser matches the PDF text."""
    monkeypatch.setattr(
        "parsers.extract_pdf_text",
        lambda _: "Unknown Utility Company Invoice #12345",
    )

    with pytest.raises(ValueError, match="No parser matched"):
        parse_bill_pdf(Path("unknown_bill.pdf"))


def test_parse_bill_pdf_raises_on_empty_pdf_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify parse_bill_pdf raises ValueError when a PDF has no selectable text."""
    monkeypatch.setattr("parsers.extract_pdf_text", lambda _: "   \n  ")

    with pytest.raises(ValueError, match="no selectable text"):
        parse_bill_pdf(Path("scanned_bill.pdf"))
