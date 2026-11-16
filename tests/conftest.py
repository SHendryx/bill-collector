from collections.abc import Iterator
import sqlite3
import pytest

from db import SCHEMAS_DIR, get_connection


@pytest.fixture
def db_conn() -> Iterator[sqlite3.Connection]:
    """Provide a fresh, schema-initialized in-memory SQLite connection per test."""
    conn = get_connection(":memory:")
    sql_files = sorted(SCHEMAS_DIR.glob("*.sql"))
    assert sql_files, f"No .sql schema files found in {SCHEMAS_DIR}"

    for sql_file in sql_files:
        try:
            conn.executescript(sql_file.read_text(encoding="utf-8"))
        except sqlite3.OperationalError as exc:
            raise sqlite3.OperationalError(
                f"SQL syntax error in {sql_file.name}: {exc}"
            ) from exc

    # Re-enable foreign keys since executescript resets transaction state
    conn.execute("PRAGMA foreign_keys = ON;")

    yield conn
    conn.close()
