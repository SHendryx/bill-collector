"""This module contains the CRUD functions for the meter_readings table."""
from dataclasses import replace
import sqlite3
from db.mappers import row_to_meter_reading
from models import MeterReading


def create_reading(conn: sqlite3.Connection, reading: MeterReading) -> MeterReading:
    """Insert a new meter reading into the database and return the created 
    MeterReading with its ID."""
    cursor = conn.execute(
        """
        INSERT INTO meter_readings (meter_id, bill_id, usage)
        VALUES (?, ?, ?)
        """,
        (reading.meter_id, reading.bill_id, reading.usage),
    )
    return replace(reading, id=cursor.lastrowid)


def get_reading(conn: sqlite3.Connection, reading_id: int) -> MeterReading | None:
    """Return the meter reading with the given ID, or None if it does not exist."""
    row = conn.execute(
        "SELECT * FROM meter_readings WHERE id = ?", (reading_id,)
    ).fetchone()
    return row_to_meter_reading(row) if row else None


def list_readings_for_meter(conn: sqlite3.Connection, meter_id: int) -> list[MeterReading]:
    """Return a list of all meter readings for a specific meter, ordered by the related 
    bill's end_date descending."""
    rows = conn.execute(
        """
        SELECT mr.*
        FROM meter_readings mr
        JOIN bills b ON mr.bill_id = b.id
        WHERE mr.meter_id = ?
        ORDER BY b.end_date DESC
        """,
        (meter_id,),
    ).fetchall()
    return [row_to_meter_reading(row) for row in rows]


def list_readings_for_bill(conn: sqlite3.Connection, bill_id: int) -> list[MeterReading]:
    """Return a list of all meter readings for a specific bill, ordered by the  
    meter in ascending order."""
    rows = conn.execute(
        """
        SELECT * FROM meter_readings
        WHERE bill_id = ?
        ORDER BY meter_id
        """,
        (bill_id,),
    ).fetchall()
    return [row_to_meter_reading(row) for row in rows]


def update_reading(conn: sqlite3.Connection, reading: MeterReading) -> bool:
    """Update an existing meter reading in the database. Returns True if successful, 
    False otherwise."""
    if reading.id is None:
        raise ValueError("Cannot update MeterReading without an id.")
    cursor = conn.execute(
        """
        UPDATE meter_readings
        SET meter_id = ?, bill_id = ?, usage = ?
        WHERE id = ?
        """,
        (
            reading.meter_id,
            reading.bill_id,
            reading.usage,
            reading.id,
        ),
    )
    return cursor.rowcount > 0


def delete_reading(conn: sqlite3.Connection, reading_id: int) -> bool:
    """Delete a meter reading from the database by its ID. Returns True if successful, 
    False otherwise."""
    cursor = conn.execute("DELETE FROM meter_readings WHERE id = ?", (reading_id,))
    return cursor.rowcount > 0
