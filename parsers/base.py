"""Defines intermediate data structures and regex helpers for parsing PDF utility bills."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
import re

from models import UnitOfMeasure


@dataclass
class ParsedReading:
    """Holds extracted meter usage details before saving to the database."""

    meter_number: str
    usage: Decimal
    unit_of_measure: UnitOfMeasure = UnitOfMeasure.KWH


@dataclass
class ParsedBill:
    """Holds extracted billing details and associated readings from a single PDF."""

    source_file: Path
    biller_name: str
    account_number: str
    amount_due: Decimal
    due_date: date
    start_date: date
    end_date: date
    readings: list[ParsedReading] = field(default_factory=list)


def extract_regex(pattern: str, text: str, field_name: str) -> str:
    """Extract the first capture group matching pattern from text.

    Args:
        pattern: Regular expression containing at least one capture group.
        text: Raw text extracted from a PDF document.
        field_name: Descriptive field name used in error messages if no match is found.

    Returns:
        The stripped string matched by the first capture group.

    Raises:
        ValueError: If the pattern does not match anywhere in the text.
    """
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find '{field_name}' in PDF text.")
    return match.group(1).strip()
