"""Unit tests for financial math, line-item reconciliation, and budget metrics."""

import pytest
from src.models import ReceiptData, LineItem, FieldConfidence, ExpenseCategory, TransactionRecord
from src.analytics import (
    calculate_month_metrics,
    get_category_breakdown,
    get_daily_spending_trend,
)


def test_line_item_total_match():
    """Verify that balanced line items mark has_discrepancy as False."""
    receipt = ReceiptData(
        merchant="Campus Cafe",
        date="2026-09-01",
        total=15.00,
        tax=1.00,
        discount=1.00,
        line_items=[
            LineItem(item_name="Coffee", quantity=2.0, unit_price=4.00, total_price=8.00),
            LineItem(item_name="Sandwich", quantity=1.0, unit_price=7.00, total_price=7.00),
        ],
    )
    # items sum = 15.00; + tax 1.00 - discount 1.00 = 15.00; total = 15.00
    receipt.validate_totals()
    assert receipt.has_discrepancy is False
    assert receipt.discrepancy_amount == 0.0


def test_line_item_discrepancy_detection():
    """Verify that an arithmetic discrepancy is correctly flagged."""
    receipt = ReceiptData(
        merchant="Bookstore",
        date="2026-09-02",
        total=45.00,  # Stated receipt total
        tax=3.00,
        discount=0.00,
        line_items=[
            LineItem(item_name="Notebook", quantity=1.0, unit_price=10.00, total_price=10.00),
            LineItem(item_name="Pen", quantity=1.0, unit_price=5.00, total_price=5.00),
        ],
    )
    # items sum = 15.00 + tax 3.00 = 18.00; stated total = 45.00
    receipt.validate_totals()
    assert receipt.has_discrepancy is True
    assert receipt.discrepancy_amount == -27.00  # 18.00 - 45.00 = -27.00


def test_calculate_month_metrics_under_budget():
    """Test monthly spend calculations when under budget."""
    txs = [
        TransactionRecord(
            id=1, merchant="Groceries", date="2026-09-02", category="Food", total=50.00
        ),
        TransactionRecord(
            id=2, merchant="Metro", date="2026-09-05", category="Travel", total=30.00
        ),
        TransactionRecord(
            id=3, merchant="Textbook", date="2026-09-10", category="Learning", total=70.00
        ),
    ]
    budget = 500.00
    metrics = calculate_month_metrics(
        transactions=txs,
        monthly_budget=budget,
        current_month_year="2026-09",
    )

    assert metrics["total_spend"] == 150.00
    assert metrics["remaining_budget"] == 350.00
    assert metrics["spend_percentage"] == 30.0
    assert metrics["transaction_count"] == 3
    assert metrics["largest_purchase"]["merchant"] == "Textbook"
    assert metrics["largest_purchase"]["amount"] == 70.00


def test_calculate_month_metrics_over_budget():
    """Test monthly spend calculation when over budget."""
    txs = [
        TransactionRecord(
            id=1, merchant="Big Tech", date="2026-09-01", category="Learning", total=600.00
        ),
    ]
    metrics = calculate_month_metrics(
        transactions=txs,
        monthly_budget=400.00,
        current_month_year="2026-09",
    )
    assert metrics["total_spend"] == 600.00
    assert metrics["remaining_budget"] == -200.00
    assert metrics["spend_percentage"] == 150.0


def test_period_over_period_comparison():
    """Test spending change vs previous month."""
    prev_txs = [
        TransactionRecord(id=10, merchant="August Cafe", date="2026-08-10", category="Food", total=100.00),
    ]
    curr_txs = [
        TransactionRecord(id=11, merchant="Sept Cafe", date="2026-09-05", category="Food", total=125.00),
    ]
    metrics = calculate_month_metrics(
        transactions=curr_txs,
        monthly_budget=500.00,
        current_month_year="2026-09",
        previous_transactions=prev_txs,
    )
    assert metrics["previous_spend"] == 100.00
    assert metrics["spend_diff"] == 25.00
    assert metrics["pct_change"] == 25.0


def test_category_breakdown_percentages():
    """Test category breakdown aggregations."""
    txs = [
        TransactionRecord(id=1, merchant="Aldi", date="2026-09-01", category=ExpenseCategory.FOOD.value, total=60.00),
        TransactionRecord(id=2, merchant="Subway", date="2026-09-02", category=ExpenseCategory.TRAVEL.value, total=40.00),
    ]
    df = get_category_breakdown(txs)
    food_row = df[df["category"] == ExpenseCategory.FOOD.value].iloc[0]
    travel_row = df[df["category"] == ExpenseCategory.TRAVEL.value].iloc[0]

    assert food_row["total"] == 60.00
    assert food_row["percentage"] == 60.0
    assert travel_row["total"] == 40.00
    assert travel_row["percentage"] == 40.0


def test_daily_spending_trend_cumulative():
    """Test that cumulative spending strictly increases or stays equal."""
    txs = [
        TransactionRecord(id=1, merchant="Cafe 1", date="2026-09-01", category="Food", total=10.00),
        TransactionRecord(id=2, merchant="Cafe 2", date="2026-09-01", category="Food", total=15.00),
        TransactionRecord(id=3, merchant="Transit", date="2026-09-03", category="Travel", total=20.00),
    ]
    df = get_daily_spending_trend(txs, "2026-09")

    # Day 1 should have 25.00
    day1_row = df[df["date"] == "2026-09-01"].iloc[0]
    assert day1_row["daily_spend"] == 25.00
    assert day1_row["cumulative_spend"] == 25.00

    # Day 2 should have 0.00 daily, 25.00 cumulative
    day2_row = df[df["date"] == "2026-09-02"].iloc[0]
    assert day2_row["daily_spend"] == 0.00
    assert day2_row["cumulative_spend"] == 25.00

    # Day 3 should have 20.00 daily, 45.00 cumulative
    day3_row = df[df["date"] == "2026-09-03"].iloc[0]
    assert day3_row["daily_spend"] == 20.00
    assert day3_row["cumulative_spend"] == 45.00
