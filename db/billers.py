"""This module provides CRUD functions to interact with the 'billers' table in the SQLite database."""
from dataclasses import replace
import sqlite3
from db.mappers import row_to_biller
from models import Biller

def create_biller(conn: sqlite3.Connection, biller: Biller) -> Biller:
    """Insert a new biller into the database and return the created Biller with its ID."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO billers (name, website) VALUES (?, ?)",
        (biller.name, biller.website),
    )
    return replace(biller, id=cursor.lastrowid)


def get_biller_by_id(conn: sqlite3.Connection, biller_id: int) -> Biller | None:
    """Retrieve a biller by its ID from the database."""
    row = conn.execute("SELECT * FROM billers WHERE id = ?", (biller_id,)).fetchone()
    return row_to_biller(row) if row else None


def list_billers(conn: sqlite3.Connection) -> list[Biller]:
    """Retrieve all billers from the database."""
    rows = conn.execute("SELECT * FROM billers").fetchall()
    return [row_to_biller(row) for row in rows]


def update_biller(conn: sqlite3.Connection, biller: Biller) -> bool:
    """Update an existing biller in the database. Returns True if successful, False otherwise."""
    if biller.id is None:
        raise ValueError("Cannot update Biller without an ID.")
    cursor = conn.execute(
        "UPDATE billers SET name = ?, website = ? WHERE id = ?",
        (biller.name, biller.website, biller.id),
    )
    return cursor.rowcount > 0


def delete_biller(conn: sqlite3.Connection, biller_id: int) -> bool:
    """Delete a biller from the database by its ID. Returns True if successful, False otherwise."""
    cursor = conn.execute("DELETE FROM billers WHERE id = ?", (biller_id,))
    return cursor.rowcount > 0
