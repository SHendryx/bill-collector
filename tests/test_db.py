"""Integration tests for SQLite schemas, type converters, mappers, and CRUD modules."""

from datetime import date
from decimal import Decimal
import sqlite3
import pytest

from db.accounts import (
    create_account,
    delete_account,
    get_account,
    list_accounts,
    update_account,
)
from db.billers import (
    create_biller,
    delete_biller,
    get_biller_by_id,
    list_billers,
    update_biller,
)
from db.bills import (
    create_bill,
    delete_bill,
    get_bill,
    get_bill_by_hash,
    list_bills,
    update_bill,
)
from db.meter_readings import (
    create_reading,
    delete_reading,
    get_reading,
    list_readings_for_bill,
    list_readings_for_meter,
    update_reading,
)
from db.meters import (
    create_meter,
    delete_meter,
    get_meter,
    list_meters,
    update_meter,
)
from models import Account, Bill, Biller, Meter, MeterReading, UnitOfMeasure


def test_biller_crud(db_conn: sqlite3.Connection) -> None:
    """Verify create, read, list, update, and delete operations for Billers."""
    created = create_biller(
        db_conn, Biller(name="Pacific Gas & Electric", website="https://pge.com")
    )
    assert created.id == 1

    fetched = get_biller_by_id(db_conn, created.id)
    assert fetched == created
    assert list_billers(db_conn) == [created]

    updated = Biller(id=created.id, name="PG&E", website="https://pge.com")
    assert update_biller(db_conn, updated) is True
    assert get_biller_by_id(db_conn, created.id) == updated

    assert delete_biller(db_conn, created.id) is True
    assert get_biller_by_id(db_conn, created.id) is None


def test_account_and_meter_crud_with_enum_conversion(
    db_conn: sqlite3.Connection,
) -> None:
    """Verify Account and Meter CRUD operations and UnitOfMeasure StrEnum round-trip."""
    biller = create_biller(db_conn, Biller(name="City Water"))
    account = create_account(
        db_conn, Account(number="ACC-9001", biller_id=biller.id)
    )
    meter = create_meter(
        db_conn,
        Meter(
            number="WTR-442",
            account_id=account.id,
            unit_of_measure=UnitOfMeasure.CCF,
        ),
    )

    assert get_account(db_conn, account.id) == account
    assert list_accounts(db_conn, biller_id=biller.id) == [account]

    updated_account = Account(id=account.id, number="ACC-9002", biller_id=biller.id)
    assert update_account(db_conn, updated_account) is True
    assert get_account(db_conn, account.id) == updated_account

    fetched_meter = get_meter(db_conn, meter.id)
    assert fetched_meter == meter
    assert isinstance(fetched_meter.unit_of_measure, UnitOfMeasure)
    assert fetched_meter.unit_of_measure == UnitOfMeasure.CCF
    assert list_meters(db_conn, account_id=account.id) == [meter]

    updated_meter = Meter(
        id=meter.id,
        number="WTR-443",
        account_id=account.id,
        unit_of_measure=UnitOfMeasure.THERMS,
    )
    assert update_meter(db_conn, updated_meter) is True
    assert get_meter(db_conn, meter.id) == updated_meter

    assert delete_meter(db_conn, meter.id) is True
    assert delete_account(db_conn, account.id) is True


def test_bill_and_reading_crud_decimal_truncation_and_dates(
    db_conn: sqlite3.Connection,
) -> None:
    """Verify Bill and MeterReading CRUD, two-decimal truncation, and date parsing."""
    biller = create_biller(db_conn, Biller(name="Metro Electric"))
    account = create_account(
        db_conn, Account(number="EL-100", biller_id=biller.id)
    )
    meter = create_meter(
        db_conn,
        Meter(
            number="MTR-01",
            account_id=account.id,
            unit_of_measure=UnitOfMeasure.KWH,
        ),
    )

    bill = create_bill(
        db_conn,
        Bill(
            account_id=account.id,
            amount_due=Decimal("142.859"),
            due_date=date(2026, 12, 15),
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 30),
        ),
    )

    fetched_bill = get_bill(db_conn, bill.id)
    assert fetched_bill is not None
    assert isinstance(fetched_bill.amount_due, Decimal)
    assert fetched_bill.amount_due == Decimal("142.85")
    assert isinstance(fetched_bill.due_date, date)
    assert fetched_bill.due_date == date(2026, 12, 15)
    assert list_bills(db_conn, account_id=account.id) == [fetched_bill]

    updated_bill = Bill(
        id=bill.id,
        account_id=account.id,
        amount_due=Decimal("150.00"),
        due_date=date(2026, 12, 20),
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 30),
    )
    assert update_bill(db_conn, updated_bill) is True
    assert get_bill(db_conn, bill.id) == updated_bill

    # Verify MeterReading usage truncation (150.879 -> 150.87)
    reading = create_reading(
        db_conn,
        MeterReading(
            meter_id=meter.id,
            bill_id=bill.id,
            usage=Decimal("150.879"),
        ),
    )

    fetched_reading = get_reading(db_conn, reading.id)
    assert fetched_reading is not None
    assert fetched_reading.usage == Decimal("150.87")

    assert list_readings_for_bill(db_conn, bill.id) == [fetched_reading]
    assert list_readings_for_meter(db_conn, meter.id) == [fetched_reading]

    updated_reading = MeterReading(
        id=reading.id,
        meter_id=meter.id,
        bill_id=bill.id,
        usage=Decimal("160.50"),
    )
    assert update_reading(db_conn, updated_reading) is True
    assert get_reading(db_conn, reading.id) == updated_reading

    assert delete_reading(db_conn, reading.id) is True
    assert delete_bill(db_conn, bill.id) is True


def test_bill_file_hash_lookup_and_uniqueness(db_conn: sqlite3.Connection) -> None:
    """Verify get_bill_by_hash finds imported bills and UNIQUE blocks duplicate hashes."""
    biller = create_biller(db_conn, Biller(name="SMUD"))
    account = create_account(
        db_conn, Account(number="7777777", biller_id=biller.id)
    )

    sample_hash = "a" * 64
    created = create_bill(
        db_conn,
        Bill(
            account_id=account.id,
            amount_due=Decimal("139.56"),
            due_date=date(2026, 11, 18),
            start_date=date(2026, 9, 22),
            end_date=date(2026, 10, 20),
            file_hash=sample_hash,
        ),
    )

    fetched = get_bill_by_hash(db_conn, sample_hash)
    assert fetched == created
    assert get_bill_by_hash(db_conn, "b" * 64) is None

    with pytest.raises(sqlite3.IntegrityError):
        create_bill(
            db_conn,
            Bill(
                account_id=account.id,
                amount_due=Decimal("139.56"),
                due_date=date(2026, 11, 18),
                start_date=date(2026, 9, 22),
                end_date=date(2026, 10, 20),
                file_hash=sample_hash,
            ),
        )


def test_foreign_key_constraints(db_conn: sqlite3.Connection) -> None:
    """Verify SQLite foreign keys block orphan rows and restrict parent deletion."""
    with pytest.raises(sqlite3.IntegrityError):
        create_account(db_conn, Account(number="BAD-ACC", biller_id=9999))

    biller = create_biller(db_conn, Biller(name="Restricted Utility"))
    create_account(db_conn, Account(number="ACC-1", biller_id=biller.id))

    with pytest.raises(sqlite3.IntegrityError):
        delete_biller(db_conn, biller.id)


def test_sql_aggregate_sums_with_decimal_colname(
    db_conn: sqlite3.Connection,
) -> None:
    """Verify SQL SUM() queries return exact Python Decimal values via [DECIMAL]."""
    biller = create_biller(db_conn, Biller(name="Solar Co"))
    account = create_account(
        db_conn, Account(number="SOL-1", biller_id=biller.id)
    )
    meter = create_meter(
        db_conn,
        Meter(
            number="SOL-MTR",
            account_id=account.id,
            unit_of_measure=UnitOfMeasure.KWH,
        ),
    )

    b1 = create_bill(
        db_conn,
        Bill(
            account_id=account.id,
            amount_due=Decimal("50.25"),
            due_date=date(2026, 10, 15),
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
        ),
    )
    b2 = create_bill(
        db_conn,
        Bill(
            account_id=account.id,
            amount_due=Decimal("75.50"),
            due_date=date(2026, 11, 15),
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
        ),
    )

    create_reading(
        db_conn, MeterReading(meter_id=meter.id, bill_id=b1.id, usage=Decimal("310.40"))
    )
    create_reading(
        db_conn, MeterReading(meter_id=meter.id, bill_id=b2.id, usage=Decimal("425.10"))
    )

    bill_row = db_conn.execute(
        'SELECT SUM(amount_due) AS "total [DECIMAL]" FROM bills WHERE account_id = ?',
        (account.id,),
    ).fetchone()
    assert bill_row["total"] == Decimal("125.75")

    usage_row = db_conn.execute(
        'SELECT SUM(usage) AS "total_usage [DECIMAL]" FROM meter_readings WHERE meter_id = ?',
        (meter.id,),
    ).fetchone()
    assert usage_row["total_usage"] == Decimal("735.50")
