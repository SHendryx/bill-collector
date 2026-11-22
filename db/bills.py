"""CRUD repository functions for managing Bill records in SQLite."""

from dataclasses import replace
import sqlite3

from db.mappers import row_to_bill
from models import Bill


def create_bill(conn: sqlite3.Connection, bill: Bill) -> Bill:
    """Insert a new bill record into the database.

    Args:
        conn: Active SQLite database connection.
        bill: Bill instance to persist.

    Returns:
        A copy of the Bill with its newly assigned database id.
    """
    cursor = conn.execute(
        """
        INSERT INTO bills (
            account_id, amount_due, due_date, start_date, end_date, file_hash
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            bill.account_id,
            bill.amount_due,
            bill.due_date,
            bill.start_date,
            bill.end_date,
            bill.file_hash,
        ),
    )
    return replace(bill, id=cursor.lastrowid)


def get_bill(conn: sqlite3.Connection, bill_id: int) -> Bill | None:
    """Retrieve a single bill by its primary key id.

    Args:
        conn: Active SQLite database connection.
        bill_id: Primary key id of the bill.

    Returns:
        The matching Bill instance if found, otherwise None.
    """
    row = conn.execute("SELECT * FROM bills WHERE id = ?", (bill_id,)).fetchone()
    return row_to_bill(row) if row else None


def get_bill_by_hash(conn: sqlite3.Connection, file_hash: str) -> Bill | None:
    """Retrieve a bill matching the given SHA-256 PDF file hash.

    Args:
        conn: Active SQLite database connection.
        file_hash: Hexadecimal SHA-256 digest of the source PDF file.

    Returns:
        The matching Bill instance if already imported, otherwise None.
    """
    row = conn.execute(
        "SELECT * FROM bills WHERE file_hash = ?", (file_hash,)
    ).fetchone()
    return row_to_bill(row) if row else None


def list_bills(
    conn: sqlite3.Connection, account_id: int | None = None
) -> list[Bill]:
    """Retrieve all bills, optionally filtered by account_id, ordered newest first.

    Args:
        conn: Active SQLite database connection.
        account_id: Optional account primary key to filter results.

    Returns:
        A list of matching Bill instances sorted by due_date descending.
    """
    if account_id is not None:
        rows = conn.execute(
            "SELECT * FROM bills WHERE account_id = ? ORDER BY due_date DESC",
            (account_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM bills ORDER BY due_date DESC").fetchall()
    return [row_to_bill(row) for row in rows]


def update_bill(conn: sqlite3.Connection, bill: Bill) -> bool:
    """Update an existing bill record in the database.

    Args:
        conn: Active SQLite database connection.
        bill: Bill instance containing updated fields and a valid id.

    Returns:
        True if a matching row was updated, False otherwise.

    Raises:
        ValueError: If bill.id is None.
    """
    if bill.id is None:
        raise ValueError("Cannot update Bill without an id.")
    cursor = conn.execute(
        """
        UPDATE bills
        SET account_id = ?, amount_due = ?, due_date = ?,
            start_date = ?, end_date = ?, file_hash = ?
        WHERE id = ?
        """,
        (
            bill.account_id,
            bill.amount_due,
            bill.due_date,
            bill.start_date,
            bill.end_date,
            bill.file_hash,
            bill.id,
        ),
    )
    return cursor.rowcount > 0


def delete_bill(conn: sqlite3.Connection, bill_id: int) -> bool:
    """Delete a bill record by its primary key id.

    Args:
        conn: Active SQLite database connection.
        bill_id: Primary key id of the bill to delete.

    Returns:
        True if a row was deleted, False otherwise.
    """
    cursor = conn.execute("DELETE FROM bills WHERE id = ?", (bill_id,))
    return cursor.rowcount > 0
