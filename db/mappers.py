"""Helpers that convert SQLite rows into domain model objects."""

import sqlite3
from models import Account, Bill, Biller, Meter, MeterReading


def row_to_biller(row: sqlite3.Row) -> Biller:
    """Create a Biller object from a database row."""
    return Biller(
        id=row["id"],
        name=row["name"],
        website=row["website"],
    )


def row_to_account(row: sqlite3.Row) -> Account:
    """Create an Account object from a database row."""
    return Account(
        id=row["id"],
        number=row["number"],
        biller_id=row["biller_id"],
    )


def row_to_meter(row: sqlite3.Row) -> Meter:
    """Create a Meter object from a database row."""
    return Meter(
        id=row["id"],
        number=row["number"],
        account_id=row["account_id"],
        unit_of_measure=row["unit_of_measure"],
    )


def row_to_bill(row: sqlite3.Row) -> Bill:
    """Convert a SQLite row from the bills table into a Bill dataclass.

    Args:
        row: A sqlite3.Row retrieved from the bills table.

    Returns:
        A populated Bill instance.
    """
    return Bill(
        id=row["id"],
        account_id=row["account_id"],
        amount_due=row["amount_due"],
        due_date=row["due_date"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        file_hash=row["file_hash"],
    )


def row_to_meter_reading(row: sqlite3.Row) -> MeterReading:
    """Create a MeterReading object from a database row."""
    return MeterReading(
        id=row["id"],
        meter_id=row["meter_id"],
        bill_id=row["bill_id"],
        usage=row["usage"],
    )
