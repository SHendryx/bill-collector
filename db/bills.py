"""This module contains the CRUD functions for the bills table."""
from dataclasses import replace
import sqlite3
from db.mappers import row_to_bill
from models import Bill


def create_bill(conn: sqlite3.Connection, bill: Bill) -> Bill:
    """Insert a new bill into the database and return the created Bill with its ID."""
    cursor = conn.execute(
        """
        INSERT INTO bills (account_id, amount_due, due_date, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            bill.account_id,
            bill.amount_due,
            bill.due_date,
            bill.start_date,
            bill.end_date,
        ),
    )
    return replace(bill, id=cursor.lastrowid)


def get_bill(conn: sqlite3.Connection, bill_id: int) -> Bill | None:
    """Return the bill with the given ID, or None if it does not exist."""
    row = conn.execute("SELECT * FROM bills WHERE id = ?", (bill_id,)).fetchone()
    return row_to_bill(row) if row else None


def list_bills(conn: sqlite3.Connection, account_id: int | None = None) -> list[Bill]:
    """Return a list of all bills, optionally filtered by account_id."""
    if account_id is not None:
        rows = conn.execute(
            "SELECT * FROM bills WHERE account_id = ? ORDER BY due_date DESC",
            (account_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM bills ORDER BY due_date DESC").fetchall()
    return [row_to_bill(row) for row in rows]


def update_bill(conn: sqlite3.Connection, bill: Bill) -> bool:
    """Update an existing bill in the database. Returns True if successful, False otherwise."""
    if bill.id is None:
        raise ValueError("Cannot update Bill without an id.")
    cursor = conn.execute(
        """
        UPDATE bills
        SET account_id = ?, amount_due = ?, due_date = ?, start_date = ?, end_date = ?
        WHERE id = ?
        """,
        (
            bill.account_id,
            bill.amount_due,
            bill.due_date,
            bill.start_date,
            bill.end_date,
            bill.id,
        ),
    )
    return cursor.rowcount > 0


def delete_bill(conn: sqlite3.Connection, bill_id: int) -> bool:
    """Delete a bill from the database by its ID. Returns True if successful, False otherwise."""
    cursor = conn.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    return cursor.rowcount > 0
