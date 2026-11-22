"""CLI terminal dashboard for viewing formatted utility spending and usage tables."""

import argparse
from contextlib import closing
from pathlib import Path

from db import DEFAULT_DB_PATH, get_connection
from db.analytics import (
    get_annual_spending_by_biller,
    get_annual_usage_by_meter,
    get_meter_usage_and_unit_cost,
    get_monthly_spending_summary,
)


def _print_table(title: str, headers: list[str], rows: list[list[str]], right_align: set[int]) -> None:
    """Render an aligned ASCII table with column headers and clean borders.

    Args:
        title: Section banner displayed above the table.
        headers: Column header labels.
        rows: Matrix of formatted cell strings.
        right_align: Set of zero-based column indices to right-align (numbers/currency).
    """
    print(f"\n{title}")
    if not rows:
        print("  (No data available)")
        return

    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def format_row(cells: list[str]) -> str:
        parts = [
            cell.rjust(widths[i]) if i in right_align else cell.ljust(widths[i])
            for i, cell in enumerate(cells)
        ]
        return "  " + " | ".join(parts)

    separator = "  " + "-+-".join("-" * w for w in widths)
    print(format_row(headers))
    print(separator)
    for row in rows:
        print(format_row(row))


def render_dashboard(
    db_path: Path,
    year_filter: str | None = None,
    biller_filter: str | None = None,
    recent_limit: int = 12,
) -> None:
    """Query SQLite analytics and print formatted tables to the terminal.

    Args:
        db_path: Path to the SQLite database file.
        year_filter: Optional 4-digit year string (e.g., '2026') to filter rows.
        biller_filter: Optional case-insensitive biller name filter (e.g., 'SMUD').
        recent_limit: Maximum number of rows shown in monthly and per-bill tables.
    """
    with closing(get_connection(db_path)) as conn:
        annual_spend = get_annual_spending_by_biller(conn)
        monthly_spend = get_monthly_spending_summary(conn)
        annual_usage = get_annual_usage_by_meter(conn)
        period_usage = get_meter_usage_and_unit_cost(conn, biller_name=biller_filter)

    if year_filter:
        annual_spend = [r for r in annual_spend if r.year == year_filter]
        monthly_spend = [r for r in monthly_spend if r.year_month.startswith(year_filter)]
        annual_usage = [r for r in annual_usage if r.year == year_filter]
        period_usage = [r for r in period_usage if str(r.end_date.year) == year_filter]

    if biller_filter:
        target = biller_filter.lower()
        annual_spend = [r for r in annual_spend if r.biller_name.lower() == target]
        annual_usage = [r for r in annual_usage if r.biller_name.lower() == target]

    _print_table(
        "=== ANNUAL SPENDING BY BILLER ===",
        ["Year", "Biller", "Bills", "Total Spent", "Avg Bill"],
        [
            [
                r.year,
                r.biller_name,
                str(r.bill_count),
                f"${r.total_spent:,.2f}",
                f"${r.avg_bill:,.2f}",
            ]
            for r in annual_spend
        ],
        right_align={2, 3, 4},
    )

    _print_table(
        f"=== MONTHLY HOUSEHOLD SPEND (LAST {recent_limit} MONTHS) ===",
        ["Month", "Bills", "Total Spent"],
        [
            [r.year_month, str(r.bill_count), f"${r.total_spent:,.2f}"]
            for r in monthly_spend[:recent_limit]
        ],
        right_align={1, 2},
    )

    _print_table(
        "=== ANNUAL USAGE BY METER ===",
        ["Year", "Biller", "Meter #", "Bills", "Total Usage"],
        [
            [
                r.year,
                r.biller_name,
                r.meter_number,
                str(r.reading_count),
                f"{r.total_usage:,.2f} {r.unit_of_measure.value}",
            ]
            for r in annual_usage
        ],
        right_align={3, 4},
    )

    _print_table(
        f"=== RECENT METERED BILLS & UNIT COSTS (LAST {recent_limit}) ===",
        ["Period End", "Biller", "Meter #", "Days", "Usage", "Daily Avg", "Bill", "Cost/Unit"],
        [
            [
                str(r.end_date),
                r.biller_name,
                r.meter_number,
                str(r.billing_days),
                f"{r.usage:,.2f} {r.unit_of_measure.value}",
                f"{r.daily_avg_usage:,.2f}/day",
                f"${r.bill_amount:,.2f}",
                f"${r.cost_per_unit:.4f}/{r.unit_of_measure.value}",
            ]
            for r in period_usage[:recent_limit]
        ],
        right_align={3, 4, 5, 6, 7},
    )
    print()


def main() -> None:
    """Parse CLI arguments and display the utility billing dashboard."""
    parser = argparse.ArgumentParser(
        description="Display formatted utility spending and usage analytics."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database file (default: {DEFAULT_DB_PATH}).",
    )
    parser.add_argument(
        "--year",
        type=str,
        default=None,
        help="Filter results to a specific 4-digit year (e.g., 2026).",
    )
    parser.add_argument(
        "--biller",
        type=str,
        default=None,
        help="Filter results to a single biller (e.g., SMUD, PG&E).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Number of recent rows to show in monthly/bill tables (default: 12).",
    )
    args = parser.parse_args()
    render_dashboard(
        args.db,
        year_filter=args.year,
        biller_filter=args.biller,
        recent_limit=args.limit,
    )


if __name__ == "__main__":
    main()
