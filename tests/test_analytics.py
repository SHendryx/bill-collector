"""Unit tests for SQL analytics queries and summary calculations."""

import sqlite3
from datetime import date
from decimal import Decimal

from db.accounts import create_account
from db.analytics import (
    get_annual_spending_by_biller,
    get_annual_usage_by_meter,
    get_meter_usage_and_unit_cost,
    get_monthly_spending_summary,
)
from db.billers import create_biller
from db.bills import create_bill
from db.meter_readings import create_reading
from db.meters import create_meter
from models import Account, Bill, Biller, Meter, MeterReading, UnitOfMeasure


def _seed_sample_data(conn: sqlite3.Connection) -> None:
    """Populate an in-memory database with sample bills and meter readings."""
    smud = create_biller(conn, Biller(name="SMUD"))
    chwd = create_biller(conn, Biller(name="CHWD"))

    smud_acct = create_account(conn, Account(number="7777777", biller_id=smud.id))
    chwd_acct = create_account(conn, Account(number="088888-000", biller_id=chwd.id))

    smud_mtr = create_meter(
        conn,
        Meter(
            number="4444444",
            account_id=smud_acct.id,
            unit_of_measure=UnitOfMeasure.KWH,
        ),
    )
    chwd_mtr = create_meter(
        conn,
        Meter(
            number="44444444",
            account_id=chwd_acct.id,
            unit_of_measure=UnitOfMeasure.CCF,
        ),
    )

    b1 = create_bill(
        conn,
        Bill(
            account_id=smud_acct.id,
            amount_due=Decimal("100.00"),
            due_date=date(2026, 10, 15),
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 20),  # 20 billing days inclusive
        ),
    )
    b2 = create_bill(
        conn,
        Bill(
            account_id=smud_acct.id,
            amount_due=Decimal("150.00"),
            due_date=date(2026, 11, 15),
            start_date=date(2026, 9, 21),
            end_date=date(2026, 10, 20),  # 30 billing days inclusive
        ),
    )
    b3 = create_bill(
        conn,
        Bill(
            account_id=chwd_acct.id,
            amount_due=Decimal("200.00"),
            due_date=date(2025, 11, 12),
            start_date=date(2025, 8, 15),
            end_date=date(2025, 10, 13),  # 60 billing days inclusive
        ),
    )

    create_reading(conn, MeterReading(meter_id=smud_mtr.id, bill_id=b1.id, usage=Decimal("500.00")))
    create_reading(conn, MeterReading(meter_id=smud_mtr.id, bill_id=b2.id, usage=Decimal("750.00")))
    create_reading(conn, MeterReading(meter_id=chwd_mtr.id, bill_id=b3.id, usage=Decimal("50.00")))


def test_annual_spending_by_biller(db_conn: sqlite3.Connection) -> None:
    """Verify annual spending totals, counts, and averages per biller."""
    _seed_sample_data(db_conn)
    results = get_annual_spending_by_biller(db_conn)

    assert len(results) == 2
    assert results[0].year == "2026"
    assert results[0].biller_name == "SMUD"
    assert results[0].bill_count == 2
    assert results[0].total_spent == Decimal("250.00")
    assert results[0].avg_bill == Decimal("125.00")

    assert results[1].year == "2025"
    assert results[1].biller_name == "CHWD"
    assert results[1].total_spent == Decimal("200.00")


def test_monthly_spending_summary(db_conn: sqlite3.Connection) -> None:
    """Verify monthly totals group cleanly by YYYY-MM newest first."""
    _seed_sample_data(db_conn)
    results = get_monthly_spending_summary(db_conn)

    assert [r.year_month for r in results] == ["2026-10", "2026-09", "2025-10"]
    assert results[0].total_spent == Decimal("150.00")
    assert results[1].total_spent == Decimal("100.00")


def test_meter_usage_and_unit_cost(db_conn: sqlite3.Connection) -> None:
    """Verify billing days, daily averages, and cost-per-unit calculations."""
    _seed_sample_data(db_conn)
    smud_periods = get_meter_usage_and_unit_cost(db_conn, biller_name="smud")

    assert len(smud_periods) == 2
    latest = smud_periods[0]  # 2026-10-20 period ($150 / 750 kWh / 30 days)
    assert latest.billing_days == 30
    assert latest.usage == Decimal("750.00")
    assert latest.daily_avg_usage == Decimal("25.00")
    assert latest.cost_per_unit == Decimal("0.2000")


def test_annual_usage_by_meter(db_conn: sqlite3.Connection) -> None:
    """Verify annual consumption sums per meter and unit of measure."""
    _seed_sample_data(db_conn)
    annual_usage = get_annual_usage_by_meter(db_conn)

    assert len(annual_usage) == 2
    assert annual_usage[0].year == "2026"
    assert annual_usage[0].total_usage == Decimal("1250.00")
    assert annual_usage[0].unit_of_measure == UnitOfMeasure.KWH
