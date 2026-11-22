"""Tests for the central parser registry, file hashing, and PDF routing dispatcher."""

from pathlib import Path

import pytest

from parsers import AVAILABLE_PARSERS, compute_file_hash, parse_bill_pdf


def test_available_parsers_is_not_empty() -> None:
    """Verify at least one parser is registered in AVAILABLE_PARSERS."""
    assert len(AVAILABLE_PARSERS) > 0


def test_compute_file_hash_is_deterministic_sha256(tmp_path: Path) -> None:
    """Verify compute_file_hash returns a consistent 64-char SHA-256 hex digest."""
    sample_file = tmp_path / "sample.pdf"
    sample_file.write_bytes(b"%PDF-1.4 fake binary content")

    digest_1 = compute_file_hash(sample_file)
    digest_2 = compute_file_hash(sample_file)

    assert len(digest_1) == 64
    assert digest_1 == digest_2


def test_parse_bill_pdf_attaches_file_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify parse_bill_pdf populates ParsedBill.file_hash from the source file."""
    fake_pdf = tmp_path / "smud_bill.pdf"
    fake_pdf.write_bytes(b"dummy pdf bytes")

    sample_text = """
    Account Number: 7777777
    Bill Period: 09/22/26 - 10/20/26 (29 Days)
    Current Charges, Due 11/18/26 $139.56
    Total Amount Due: $139.56
    Make check payable to SMUD
    """
    monkeypatch.setattr("parsers.extract_pdf_text", lambda _: sample_text)

    parsed = parse_bill_pdf(fake_pdf)
    assert parsed.file_hash == compute_file_hash(fake_pdf)


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
