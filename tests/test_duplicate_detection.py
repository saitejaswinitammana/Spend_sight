"""Unit tests for duplicate receipt detection in SQLite database."""

import os
import pytest
from src.models import ReceiptData, LineItem, ExpenseCategory
from src.database import DatabaseManager


@pytest.fixture
def temp_db(tmp_path):
    """Provide a temporary clean SQLite database instance."""
    db_file = str(tmp_path / "test_spendsight.db")
    manager = DatabaseManager(db_path=db_file)
    return manager


def test_exact_duplicate_detection(temp_db):
    """Detect duplicate receipt when merchant, date, and total match exactly."""
    receipt = ReceiptData(
        merchant="Trader Joe's",
        date="2026-09-02",
        total=38.40,
        category=ExpenseCategory.FOOD.value,
    )
    inserted_id = temp_db.insert_transaction(receipt)
    assert inserted_id > 0

    # Search for duplicate with same details
    duplicate = temp_db.find_potential_duplicate(
        merchant="Trader Joe's",
        date_str="2026-09-02",
        total=38.40,
        day_window=1,
    )
    assert duplicate is not None
    assert duplicate["id"] == inserted_id
    assert duplicate["merchant"] == "Trader Joe's"
    assert duplicate["total"] == 38.40


def test_case_insensitive_merchant_duplicate(temp_db):
    """Detect duplicate even if merchant casing differs (e.g. 'TRADER JOE'S' vs 'trader joe's')."""
    receipt = ReceiptData(
        merchant="Campus Bookstore",
        date="2026-09-01",
        total=86.66,
        category=ExpenseCategory.LEARNING.value,
    )
    temp_db.insert_transaction(receipt)

    duplicate = temp_db.find_potential_duplicate(
        merchant="campus bookstore",
        date_str="2026-09-01",
        total=86.66,
        day_window=0,
    )
    assert duplicate is not None
    assert duplicate["merchant"] == "Campus Bookstore"


def test_day_window_duplicate_detection(temp_db):
    """Detect potential duplicate if transaction date is within day_window."""
    receipt = ReceiptData(
        merchant="City Metro",
        date="2026-09-02",
        total=30.00,
        category=ExpenseCategory.TRAVEL.value,
    )
    temp_db.insert_transaction(receipt)

    # Date 1 day earlier
    dup_earlier = temp_db.find_potential_duplicate(
        merchant="City Metro",
        date_str="2026-09-01",
        total=30.00,
        day_window=2,
    )
    assert dup_earlier is not None

    # Date 5 days later (outside 2-day window)
    no_dup = temp_db.find_potential_duplicate(
        merchant="City Metro",
        date_str="2026-09-08",
        total=30.00,
        day_window=2,
    )
    assert no_dup is None


def test_different_amount_not_duplicate(temp_db):
    """Different amounts from same merchant should not be flagged as duplicates."""
    receipt = ReceiptData(
        merchant="Aldi",
        date="2026-09-05",
        total=25.00,
        category=ExpenseCategory.FOOD.value,
    )
    temp_db.insert_transaction(receipt)

    dup = temp_db.find_potential_duplicate(
        merchant="Aldi",
        date_str="2026-09-05",
        total=45.00,
        day_window=2,
    )
    assert dup is None


def test_exclude_self_during_update(temp_db):
    """When editing an existing transaction, exclude its own ID from duplicate warning."""
    receipt = ReceiptData(
        merchant="Library Cafe",
        date="2026-09-03",
        total=5.75,
        category=ExpenseCategory.FOOD.value,
    )
    tx_id = temp_db.insert_transaction(receipt)

    # Checking duplicate excluding self
    dup = temp_db.find_potential_duplicate(
        merchant="Library Cafe",
        date_str="2026-09-03",
        total=5.75,
        exclude_id=tx_id,
    )
    assert dup is None
