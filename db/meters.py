"""CRUD Database operations for Meter objects."""
import sqlite3
from dataclasses import replace
from db.mappers import row_to_meter
from models import Meter


def create_meter(conn: sqlite3.Connection, meter: Meter) -> Meter:
    """Insert a new meter into the database and return the created Meter with its ID."""
    cursor = conn.execute(
        "INSERT INTO meters (number, account_id, unit_of_measure) VALUES (?, ?, ?)",
        (meter.number, meter.account_id, meter.unit_of_measure),
    )
    return replace(meter, id=cursor.lastrowid)


def get_meter(conn: sqlite3.Connection, meter_id: int) -> Meter | None:
    """Return the meter with the given ID, or None if it does not exist."""
    row = conn.execute("SELECT * FROM meters WHERE id = ?", (meter_id,)).fetchone()
    return row_to_meter(row) if row else None


def list_meters(conn: sqlite3.Connection, account_id: int | None = None) -> list[Meter]:
    """Return a list of all meters, optionally filtered by account_id."""
    if account_id is not None:
        rows = conn.execute(
            "SELECT * FROM meters WHERE account_id = ? ORDER BY number",
            (account_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM meters ORDER BY number").fetchall()
    return [row_to_meter(row) for row in rows]


def update_meter(conn: sqlite3.Connection, meter: Meter) -> bool:
    """Update an existing meter in the database. Returns True if successful, False otherwise."""
    if meter.id is None:
        raise ValueError("Cannot update Meter without an id.")
    cursor = conn.execute(
        """
        UPDATE meters
        SET number = ?, account_id = ?, unit_of_measure = ?
        WHERE id = ?
        """,
        (meter.number, meter.account_id, meter.unit_of_measure, meter.id),
    )
    return cursor.rowcount > 0


def delete_meter(conn: sqlite3.Connection, meter_id: int) -> bool:
    """Delete a meter from the database by its ID. Returns True if successful, False otherwise."""
    cursor = conn.execute("DELETE FROM meters WHERE id = ?", (meter_id,))
    return cursor.rowcount > 0
