"""Shared pytest fixtures and helpers for database and parser test suites."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from db import SCHEMAS_DIR, get_connection

BILLS_DIR = Path(__file__).resolve().parent.parent / "bills"


def get_sample_pdfs(biller_folder: str) -> list[Path]:
    """Return sorted PDF paths directly inside bills/test/<biller_folder>/.

    Args:
        biller_folder: Subdirectory name under /bills/test/ (e.g., 'smud', 'pge').

    Returns:
        A sorted list of Path objects for all .pdf files found, or an empty list.
    """
    folder = BILLS_DIR / "test" / biller_folder
    if not folder.is_dir():
        return []
    return sorted(folder.glob("*.pdf"))



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

    conn.execute("PRAGMA foreign_keys = ON;")

    yield conn
    conn.close()
