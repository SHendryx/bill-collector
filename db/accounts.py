"""This module contains the CRUD functions for the accounts table."""
from dataclasses import replace
import sqlite3
from db.mappers import row_to_account
from models import Account


def create_account(conn: sqlite3.Connection, account: Account) -> Account:
    """Create an account in the database and return it with its assigned ID."""
    cursor = conn.execute(
        "INSERT INTO accounts (number, biller_id) VALUES (?, ?)",
        (account.number, account.biller_id),
    )
    return replace(account, id=cursor.lastrowid)


def get_account(conn: sqlite3.Connection, account_id: int) -> Account | None:
    """Return the account with the given ID, or None if it does not exist."""
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return row_to_account(row) if row else None


def list_accounts(conn: sqlite3.Connection, biller_id: int | None = None) -> list[Account]:
    """Return a list of all accounts, optionally filtered by biller_id."""
    if biller_id is not None:
        rows = conn.execute(
            "SELECT * FROM accounts WHERE biller_id = ? ORDER BY number",
            (biller_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM accounts ORDER BY number").fetchall()
    return [row_to_account(row) for row in rows]


def update_account(conn: sqlite3.Connection, account: Account) -> bool:
    """Update an existing account in the database. Returns True if successful, False otherwise."""
    if account.id is None:
        raise ValueError("Cannot update Account without an id.")
    cursor = conn.execute(
        "UPDATE accounts SET number = ?, biller_id = ? WHERE id = ?",
        (account.number, account.biller_id, account.id),
    )
    return cursor.rowcount > 0


def delete_account(conn: sqlite3.Connection, account_id: int) -> bool:
    """Delete an account from the database by its ID. 
    Returns True if successful, False otherwise."""
    cursor = conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    return cursor.rowcount > 0
