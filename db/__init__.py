"""Initialize database and setup adapters/converters."""
from datetime import date
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
import sqlite3
from models import UnitOfMeasure

SQL_DIR = Path(__file__).parent / "schemas"
DEFAULT_DB_PATH = Path("billing.db")

SCALE = Decimal("100")

def adapt_decimal_to_int(val: Decimal) -> int:
    """Truncate a Python Decimal to 2 decimal places and convert to a scaled integer."""
    return int((val * SCALE).to_integral_value(rounding=ROUND_DOWN))

def convert_int_to_decimal(raw: bytes) -> Decimal:
    """Convert a scaled SQLite integer back into a 2-decimal-place Python Decimal."""
    return (Decimal(int(raw)) / SCALE).quantize(Decimal("0.01"))

def _register_sqlite_types() -> None:
    """Register custom adapters and converters for Python domain types."""
    # Python -> SQLite
    sqlite3.register_adapter(date, date.isoformat)
    sqlite3.register_adapter(Decimal, adapt_decimal_to_int)

    # SQLite -> Python (keys must be UPPERCASE)
    sqlite3.register_converter("DATE", lambda b: date.fromisoformat(b.decode("utf-8")))
    sqlite3.register_converter("DECIMAL", convert_int_to_decimal)
    sqlite3.register_converter(
        "UNIT_OF_MEASURE", lambda b: UnitOfMeasure(b.decode("utf-8"))
    )


_register_sqlite_types()


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with type parsing, Row factory, and foreign keys."""
    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
