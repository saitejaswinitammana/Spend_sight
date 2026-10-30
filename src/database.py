"""SQLite Database Layer for SpendSight.

Handles schema initialization, CRUD operations, duplicate receipt detection,
budget settings, and CSV export.
"""

import sqlite3
import os
import io
import csv
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd

from src.models import (
    ReceiptData,
    LineItem,
    TransactionRecord,
    ExpenseCategory,
    FieldConfidence,
)

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendsight.db")


class DatabaseManager:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema if tables do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant TEXT NOT NULL,
                    date TEXT NOT NULL,
                    currency TEXT NOT NULL DEFAULT '$',
                    category TEXT NOT NULL,
                    subtotal REAL DEFAULT 0.0,
                    tax REAL DEFAULT 0.0,
                    discount REAL DEFAULT 0.0,
                    total REAL NOT NULL,
                    confidence_score REAL DEFAULT 0.85,
                    notes TEXT DEFAULT '',
                    has_discrepancy INTEGER DEFAULT 0,
                    discrepancy_amount REAL DEFAULT 0.0,
                    has_image INTEGER DEFAULT 0,
                    image_blob BLOB,
                    extraction_method TEXT DEFAULT 'Rule-based Fallback',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Line items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS line_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    total_price REAL NOT NULL,
                    FOREIGN KEY (transaction_id) REFERENCES transactions (id) ON DELETE CASCADE
                )
            """)

            # Budgets table (keyed by month_year e.g. '2026-09')
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_budgets (
                    month_year TEXT PRIMARY KEY,
                    budget_amount REAL NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # App settings table (key-value store for preferences like retain_images)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Create indices for quick lookups and duplicate detection
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON transactions(merchant)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_line_items_txid ON line_items(transaction_id)")

            conn.commit()

    # -------------------------------------------------------------------------
    # Duplicate Detection
    # -------------------------------------------------------------------------
    def find_potential_duplicate(
        self,
        merchant: str,
        date_str: str,
        total: float,
        day_window: int = 3,
        exclude_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Detect duplicate receipts based on normalized merchant name,
        exact total, and transaction date within +/- day_window days.
        """
        clean_merchant = merchant.strip().lower()
        clean_total = round(float(total), 2)

        try:
            target_dt = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_date = (target_dt - timedelta(days=day_window)).isoformat()
            end_date = (target_dt + timedelta(days=day_window)).isoformat()
        except ValueError:
            # Fallback to exact date matching if date parsing fails
            start_date = date_str
            end_date = date_str

        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT id, merchant, date, total, category
                FROM transactions
                WHERE LOWER(TRIM(merchant)) = ?
                  AND ABS(total - ?) < 0.01
                  AND date BETWEEN ? AND ?
            """
            params: List[Any] = [clean_merchant, clean_total, start_date, end_date]

            if exclude_id is not None:
                query += " AND id != ?"
                params.append(exclude_id)

            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "merchant": row["merchant"],
                    "date": row["date"],
                    "total": row["total"],
                    "category": row["category"],
                }
        return None

    # -------------------------------------------------------------------------
    # Transaction CRUD
    # -------------------------------------------------------------------------
    def insert_transaction(
        self,
        receipt: ReceiptData,
        image_bytes: Optional[bytes] = None,
        retain_images_override: Optional[bool] = None,
    ) -> int:
        """
        Insert a structured receipt into the database.
        Images are discarded by default unless explicitly retained.
        """
        # Determine image retention: override param, or app setting, or env var
        if retain_images_override is not None:
            should_retain = retain_images_override
        else:
            should_retain = self.get_setting("retain_images", "false").lower() == "true"

        store_blob = image_bytes if (should_retain and image_bytes) else None
        has_img = 1 if store_blob is not None else 0

        # Run total discrepancy check
        receipt.validate_totals()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transactions (
                    merchant, date, currency, category, subtotal, tax, discount, total,
                    confidence_score, notes, has_discrepancy, discrepancy_amount,
                    has_image, image_blob, extraction_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.merchant.strip() or "Unknown Merchant",
                    receipt.date,
                    receipt.currency or "$",
                    receipt.category or ExpenseCategory.OTHER.value,
                    float(receipt.subtotal),
                    float(receipt.tax),
                    float(receipt.discount),
                    float(receipt.total),
                    0.9 if receipt.confidence.merchant == "High" else 0.75,
                    receipt.notes,
                    1 if receipt.has_discrepancy else 0,
                    float(receipt.discrepancy_amount),
                    has_img,
                    store_blob,
                    receipt.extraction_method,
                ),
            )
            transaction_id = cursor.lastrowid

            # Insert line items
            for item in receipt.line_items:
                cursor.execute(
                    """
                    INSERT INTO line_items (
                        transaction_id, item_name, quantity, unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        transaction_id,
                        item.item_name.strip() or "Item",
                        float(item.quantity),
                        float(item.unit_price),
                        float(item.total_price),
                    ),
                )
            conn.commit()
            return transaction_id

    def update_transaction(
        self,
        tx_id: int,
        merchant: str,
        date_str: str,
        category: str,
        total: float,
        tax: float = 0.0,
        discount: float = 0.0,
        notes: str = "",
        line_items: Optional[List[LineItem]] = None,
    ) -> bool:
        """Update an existing transaction and recalculate discrepancies."""
        has_disc = 0
        disc_amt = 0.0

        if line_items:
            items_sum = sum(it.total_price for it in line_items)
            calc_total = round(items_sum + tax - discount, 2)
            if abs(calc_total - total) > 0.02:
                has_disc = 1
                disc_amt = round(calc_total - total, 2)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transactions
                SET merchant = ?, date = ?, category = ?, total = ?, tax = ?,
                    discount = ?, notes = ?, has_discrepancy = ?, discrepancy_amount = ?
                WHERE id = ?
                """,
                (
                    merchant.strip(),
                    date_str,
                    category,
                    float(total),
                    float(tax),
                    float(discount),
                    notes,
                    has_disc,
                    disc_amt,
                    tx_id,
                ),
            )

            if line_items is not None:
                # Replace line items
                cursor.execute("DELETE FROM line_items WHERE transaction_id = ?", (tx_id,))
                for item in line_items:
                    cursor.execute(
                        """
                        INSERT INTO line_items (
                            transaction_id, item_name, quantity, unit_price, total_price
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            tx_id,
                            item.item_name.strip(),
                            float(item.quantity),
                            float(item.unit_price),
                            float(item.total_price),
                        ),
                    )
            conn.commit()
            return cursor.rowcount > 0

    def delete_transaction(self, tx_id: int) -> bool:
        """Delete a transaction and cascade-delete its line items."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_transaction(self, tx_id: int) -> Optional[TransactionRecord]:
        """Fetch single transaction along with its line items."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                "SELECT * FROM line_items WHERE transaction_id = ? ORDER BY id ASC",
                (tx_id,),
            )
            items = [
                LineItem(
                    item_name=item_row["item_name"],
                    quantity=float(item_row["quantity"]),
                    unit_price=float(item_row["unit_price"]),
                    total_price=float(item_row["total_price"]),
                )
                for item_row in cursor.fetchall()
            ]

            return TransactionRecord(
                id=row["id"],
                merchant=row["merchant"],
                date=row["date"],
                currency=row["currency"],
                category=row["category"],
                subtotal=float(row["subtotal"]),
                tax=float(row["tax"]),
                discount=float(row["discount"]),
                total=float(row["total"]),
                confidence_score=float(row["confidence_score"]),
                notes=row["notes"] or "",
                has_discrepancy=bool(row["has_discrepancy"]),
                discrepancy_amount=float(row["discrepancy_amount"]),
                has_image=bool(row["has_image"]),
                image_bytes=row["image_blob"],
                created_at=row["created_at"],
                line_items=items,
            )

    def get_all_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        only_discrepancies: bool = False,
    ) -> List[TransactionRecord]:
        """Fetch transactions filtered by date range, category, search term, or discrepancy."""
        query = "SELECT * FROM transactions WHERE 1=1"
        params: List[Any] = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        if search_query:
            query += " AND (LOWER(merchant) LIKE ? OR LOWER(notes) LIKE ?)"
            term = f"%{search_query.strip().lower()}%"
            params.extend([term, term])
        if only_discrepancies:
            query += " AND has_discrepancy = 1"

        query += " ORDER BY date DESC, id DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results: List[TransactionRecord] = []
            for row in rows:
                # Load line items for each transaction
                cursor.execute(
                    "SELECT * FROM line_items WHERE transaction_id = ? ORDER BY id ASC",
                    (row["id"],),
                )
                items = [
                    LineItem(
                        item_name=item_row["item_name"],
                        quantity=float(item_row["quantity"]),
                        unit_price=float(item_row["unit_price"]),
                        total_price=float(item_row["total_price"]),
                    )
                    for item_row in cursor.fetchall()
                ]
                results.append(
                    TransactionRecord(
                        id=row["id"],
                        merchant=row["merchant"],
                        date=row["date"],
                        currency=row["currency"],
                        category=row["category"],
                        subtotal=float(row["subtotal"]),
                        tax=float(row["tax"]),
                        discount=float(row["discount"]),
                        total=float(row["total"]),
                        confidence_score=float(row["confidence_score"]),
                        notes=row["notes"] or "",
                        has_discrepancy=bool(row["has_discrepancy"]),
                        discrepancy_amount=float(row["discrepancy_amount"]),
                        has_image=bool(row["has_image"]),
                        image_bytes=row["image_blob"],
                        created_at=row["created_at"],
                        line_items=items,
                    )
                )
            return results

    def get_transactions_dataframe(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return transactions as a clean Pandas DataFrame for Plotly and data grids."""
        txs = self.get_all_transactions(start_date, end_date, category, search_query)
        if not txs:
            return pd.DataFrame(
                columns=[
                    "id",
                    "date",
                    "merchant",
                    "category",
                    "total",
                    "tax",
                    "discount",
                    "notes",
                    "has_discrepancy",
                    "discrepancy_amount",
                    "items_count",
                ]
            )

        data = []
        for t in txs:
            data.append(
                {
                    "id": t.id,
                    "date": t.date,
                    "merchant": t.merchant,
                    "category": t.category,
                    "total": t.total,
                    "tax": t.tax,
                    "discount": t.discount,
                    "notes": t.notes,
                    "has_discrepancy": "⚠️ Discrepancy" if t.has_discrepancy else "✅ Valid",
                    "discrepancy_amount": t.discrepancy_amount,
                    "items_count": len(t.line_items),
                }
            )
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        return df

    # -------------------------------------------------------------------------
    # Budget Settings
    # -------------------------------------------------------------------------
    def get_budget_for_month(self, month_year: str, default_amount: float = 650.0) -> float:
        """Fetch student budget for given 'YYYY-MM', or insert default if absent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT budget_amount FROM monthly_budgets WHERE month_year = ?",
                (month_year,),
            )
            row = cursor.fetchone()
            if row:
                return float(row["budget_amount"])

            # Default budget fallback
            cursor.execute(
                "INSERT OR REPLACE INTO monthly_budgets (month_year, budget_amount) VALUES (?, ?)",
                (month_year, default_amount),
            )
            conn.commit()
            return default_amount

    def set_budget_for_month(self, month_year: str, budget_amount: float) -> None:
        """Update or insert budget for month_year."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO monthly_budgets (month_year, budget_amount, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(month_year) DO UPDATE SET
                    budget_amount = excluded.budget_amount,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (month_year, float(budget_amount)),
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # General Settings (Key-Value)
    # -------------------------------------------------------------------------
    def get_setting(self, key: str, default: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO app_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, str(value)),
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # CSV Export
    # -------------------------------------------------------------------------
    def export_csv(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_line_items: bool = True,
    ) -> str:
        """Export transactions and line items to CSV format as a string."""
        txs = self.get_all_transactions(start_date=start_date, end_date=end_date)
        output = io.StringIO()

        if include_line_items:
            writer = csv.writer(output)
            writer.writerow([
                "Transaction ID",
                "Date",
                "Merchant",
                "Category",
                "Total",
                "Tax",
                "Discount",
                "Item Name",
                "Item Quantity",
                "Item Unit Price",
                "Item Total Price",
                "Has Discrepancy",
                "Discrepancy Amount",
                "Notes",
            ])
            for t in txs:
                if t.line_items:
                    for item in t.line_items:
                        writer.writerow([
                            t.id,
                            t.date,
                            t.merchant,
                            t.category,
                            f"{t.total:.2f}",
                            f"{t.tax:.2f}",
                            f"{t.discount:.2f}",
                            item.item_name,
                            f"{item.quantity:.2f}",
                            f"{item.unit_price:.2f}",
                            f"{item.total_price:.2f}",
                            t.has_discrepancy,
                            f"{t.discrepancy_amount:.2f}",
                            t.notes,
                        ])
                else:
                    writer.writerow([
                        t.id,
                        t.date,
                        t.merchant,
                        t.category,
                        f"{t.total:.2f}",
                        f"{t.tax:.2f}",
                        f"{t.discount:.2f}",
                        "N/A",
                        0,
                        0.0,
                        0.0,
                        t.has_discrepancy,
                        f"{t.discrepancy_amount:.2f}",
                        t.notes,
                    ])
        else:
            writer = csv.writer(output)
            writer.writerow([
                "Transaction ID",
                "Date",
                "Merchant",
                "Category",
                "Total",
                "Tax",
                "Discount",
                "Line Items Count",
                "Has Discrepancy",
                "Discrepancy Amount",
                "Notes",
            ])
            for t in txs:
                writer.writerow([
                    t.id,
                    t.date,
                    t.merchant,
                    t.category,
                    f"{t.total:.2f}",
                    f"{t.tax:.2f}",
                    f"{t.discount:.2f}",
                    len(t.line_items),
                    t.has_discrepancy,
                    f"{t.discrepancy_amount:.2f}",
                    t.notes,
                ])

        return output.getvalue()

    def clear_all_transactions(self) -> None:
        """Clear all transactions and line items (for resetting or demo data reload)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM line_items")
            cursor.execute("DELETE FROM transactions")
            cursor.execute("DELETE FROM monthly_budgets")
            conn.commit()
