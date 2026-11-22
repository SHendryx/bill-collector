"""Analytical SQL queries and summary dataclasses for utility billing and usage data."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import sqlite3

from models import UnitOfMeasure


@dataclass(frozen=True)
class BillerYearSummary:
    """Represents annual spending totals and bill counts for a single biller."""

    year: str
    biller_name: str
    bill_count: int
    total_spent: Decimal
    avg_bill: Decimal


@dataclass(frozen=True)
class MonthlySpendSummary:
    """Represents total household spending across all billers for a given YYYY-MM month."""

    year_month: str
    bill_count: int
    total_spent: Decimal


@dataclass(frozen=True)
class PeriodUsageSummary:
    """Represents meter usage, billing days, and effective unit cost for a single bill."""

    biller_name: str
    meter_number: str
    unit_of_measure: UnitOfMeasure
    start_date: date
    end_date: date
    billing_days: int
    usage: Decimal
    bill_amount: Decimal
    daily_avg_usage: Decimal
    cost_per_unit: Decimal


@dataclass(frozen=True)
class AnnualMeterUsage:
    """Represents total annual consumption for a specific meter and unit of measure."""

    year: str
    biller_name: str
    meter_number: str
    unit_of_measure: UnitOfMeasure
    reading_count: int
    total_usage: Decimal


def get_annual_spending_by_biller(
    conn: sqlite3.Connection,
) -> list[BillerYearSummary]:
    """Calculate total bills, total spend, and average bill per year and biller.

    Args:
        conn: Active SQLite database connection.

    Returns:
        List of BillerYearSummary records ordered by year descending, then total spent.
    """
    rows = conn.execute(
        """
        SELECT
            strftime('%Y', b.end_date) AS year,
            bl.name AS biller_name,
            COUNT(b.id) AS bill_count,
            SUM(b.amount_due) AS "total_spent [DECIMAL]",
            CAST(ROUND(AVG(b.amount_due)) AS INTEGER) AS "avg_bill [DECIMAL]"
        FROM bills b
        JOIN accounts a ON b.account_id = a.id
        JOIN billers bl ON a.biller_id = bl.id
        GROUP BY year, bl.name
        ORDER BY year DESC, SUM(b.amount_due) DESC
        """
    ).fetchall()

    return [
        BillerYearSummary(
            year=row["year"],
            biller_name=row["biller_name"],
            bill_count=row["bill_count"],
            total_spent=row["total_spent"],
            avg_bill=row["avg_bill"],
        )
        for row in rows
    ]


def get_monthly_spending_summary(
    conn: sqlite3.Connection,
) -> list[MonthlySpendSummary]:
    """Calculate total combined spending across all billers grouped by YYYY-MM.

    Args:
        conn: Active SQLite database connection.

    Returns:
        List of MonthlySpendSummary records ordered chronologically newest first.
    """
    rows = conn.execute(
        """
        SELECT
            strftime('%Y-%m', end_date) AS year_month,
            COUNT(id) AS bill_count,
            SUM(amount_due) AS "total_spent [DECIMAL]"
        FROM bills
        GROUP BY year_month
        ORDER BY year_month DESC
        """
    ).fetchall()

    return [
        MonthlySpendSummary(
            year_month=row["year_month"],
            bill_count=row["bill_count"],
            total_spent=row["total_spent"],
        )
        for row in rows
    ]


def get_meter_usage_and_unit_cost(
    conn: sqlite3.Connection,
    biller_name: str | None = None,
) -> list[PeriodUsageSummary]:
    """Calculate usage, daily averages, and effective cost per unit for metered bills.

    Args:
        conn: Active SQLite database connection.
        biller_name: Optional case-insensitive biller name filter (e.g., 'SMUD').

    Returns:
        List of PeriodUsageSummary records ordered by billing end_date descending.
    """
    base_sql = """
        SELECT
            bl.name AS biller_name,
            m.number AS meter_number,
            m.unit_of_measure AS "unit_of_measure [UNIT_OF_MEASURE]",
            b.start_date AS "start_date [DATE]",
            b.end_date AS "end_date [DATE]",
            CAST(julianday(b.end_date) - julianday(b.start_date) + 1 AS INTEGER) AS billing_days,
            mr.usage AS "usage [DECIMAL]",
            b.amount_due AS "bill_amount [DECIMAL]"
        FROM meter_readings mr
        JOIN bills b ON mr.bill_id = b.id
        JOIN meters m ON mr.meter_id = m.id
        JOIN accounts a ON b.account_id = a.id
        JOIN billers bl ON a.biller_id = bl.id
    """
    params: tuple[str, ...] = ()
    if biller_name is not None:
        base_sql += " WHERE LOWER(bl.name) = LOWER(?)"
        params = (biller_name,)

    base_sql += " ORDER BY b.end_date DESC, m.number"
    rows = conn.execute(base_sql, params).fetchall()

    results: list[PeriodUsageSummary] = []
    for row in rows:
        days = max(row["billing_days"], 1)
        usage: Decimal = row["usage"]
        amount: Decimal = row["bill_amount"]

        daily_avg = (usage / Decimal(days)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        unit_cost = (
            (amount / usage).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            if usage > Decimal("0.00")
            else Decimal("0.0000")
        )

        results.append(
            PeriodUsageSummary(
                biller_name=row["biller_name"],
                meter_number=row["meter_number"],
                unit_of_measure=row["unit_of_measure"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                billing_days=days,
                usage=usage,
                bill_amount=amount,
                daily_avg_usage=daily_avg,
                cost_per_unit=unit_cost,
            )
        )

    return results


def get_annual_usage_by_meter(
    conn: sqlite3.Connection,
) -> list[AnnualMeterUsage]:
    """Aggregate total annual consumption per meter and unit of measure.

    Args:
        conn: Active SQLite database connection.

    Returns:
        List of AnnualMeterUsage records ordered by year descending, then biller.
    """
    rows = conn.execute(
        """
        SELECT
            strftime('%Y', b.end_date) AS year,
            bl.name AS biller_name,
            m.number AS meter_number,
            m.unit_of_measure AS "unit_of_measure [UNIT_OF_MEASURE]",
            COUNT(mr.id) AS reading_count,
            SUM(mr.usage) AS "total_usage [DECIMAL]"
        FROM meter_readings mr
        JOIN bills b ON mr.bill_id = b.id
        JOIN meters m ON mr.meter_id = m.id
        JOIN accounts a ON b.account_id = a.id
        JOIN billers bl ON a.biller_id = bl.id
        GROUP BY year, bl.name, m.number, m.unit_of_measure
        ORDER BY year DESC, bl.name, m.number
        """
    ).fetchall()

    return [
        AnnualMeterUsage(
            year=row["year"],
            biller_name=row["biller_name"],
            meter_number=row["meter_number"],
            unit_of_measure=row["unit_of_measure"],
            reading_count=row["reading_count"],
            total_usage=row["total_usage"],
        )
        for row in rows
    ]
