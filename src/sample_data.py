"""Realistic student sample dataset generator for SpendSight."""

from typing import List
from src.models import ReceiptData, LineItem, FieldConfidence, ExpenseCategory
from src.database import DatabaseManager


def generate_sample_transactions() -> List[ReceiptData]:
    """Generate realistic fictional student expenses across August and September 2026."""
    samples: List[ReceiptData] = [
        # --- August 2026 Transactions (Previous Period) ---
        ReceiptData(
            merchant="Trader Joe's",
            date="2026-08-04",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=24.50,
            tax=0.00,
            discount=0.00,
            total=24.50,
            line_items=[
                LineItem("Oat Milk & Sourdough", 1.0, 5.49, 5.49),
                LineItem("Organic Bananas", 1.0, 1.49, 1.49),
                LineItem("Frozen Dumplings & Rice", 2.0, 4.99, 9.98),
                LineItem("Greek Yogurt (Pack)", 1.0, 7.54, 7.54),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Weekly grocery run",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Campus Library Cafe",
            date="2026-08-07",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=6.50,
            tax=0.55,
            discount=0.00,
            total=7.05,
            line_items=[
                LineItem("Iced Caramel Macchiato", 1.0, 5.25, 5.25),
                LineItem("Chocolate Chip Cookie", 1.0, 1.25, 1.25),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Study fuel during finals prep",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="City Metro Transit",
            date="2026-08-09",
            currency="$",
            category=ExpenseCategory.TRAVEL.value,
            subtotal=30.00,
            tax=0.00,
            discount=0.00,
            total=30.00,
            line_items=[
                LineItem("August Student Monthly Pass", 1.0, 30.00, 30.00),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Discounted campus metro card",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Spotify",
            date="2026-08-11",
            currency="$",
            category=ExpenseCategory.ENTERTAINMENT.value,
            subtotal=5.99,
            tax=0.00,
            discount=0.00,
            total=5.99,
            line_items=[
                LineItem("Spotify Student Monthly Premium", 1.0, 5.99, 5.99),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Student discount plan",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="University Bookstore",
            date="2026-08-18",
            currency="$",
            category=ExpenseCategory.LEARNING.value,
            subtotal=48.20,
            tax=3.86,
            discount=5.00,
            total=47.06,
            line_items=[
                LineItem("Graphing Notebooks (3)", 1.0, 12.00, 12.00),
                LineItem("Pilot G2 Pens (Set of 8)", 1.0, 11.20, 11.20),
                LineItem("USB-C Flash Drive 64GB", 1.0, 25.00, 25.00),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Semester stationery and supplies",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Aldi Supermarket",
            date="2026-08-21",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=31.20,
            tax=0.00,
            discount=0.00,
            total=31.20,
            line_items=[
                LineItem("Pasta, Marinara, Lentils", 1.0, 12.40, 12.40),
                LineItem("Apples & Oranges", 1.0, 6.80, 6.80),
                LineItem("Eggs & Cheese Slices", 1.0, 12.00, 12.00),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Budget grocery restock",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Campus Library Cafe",
            date="2026-08-24",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=4.75,
            tax=0.40,
            discount=0.00,
            total=5.15,
            line_items=[
                LineItem("Drip Coffee with Oat Milk", 1.0, 4.75, 4.75),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Morning lecture coffee",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="CVS Pharmacy",
            date="2026-08-27",
            currency="$",
            category=ExpenseCategory.HEALTH.value,
            subtotal=14.30,
            tax=1.14,
            discount=2.00,
            total=13.44,
            line_items=[
                LineItem("Allergy Relief Medicine", 1.0, 10.30, 10.30),
                LineItem("Lip Balm & Sanitizer", 1.0, 4.00, 4.00),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Health essentials",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Xfinity Internet",
            date="2026-08-28",
            currency="$",
            category=ExpenseCategory.UTILITIES.value,
            subtotal=23.33,
            tax=0.00,
            discount=0.00,
            total=23.33,
            line_items=[
                LineItem("Shared Apartment Wi-Fi (1/3 share)", 1.0, 23.33, 23.33),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="August Wi-Fi split",
            extraction_method="Sample Data",
        ),

        # --- September 2026 Transactions (Current Period) ---
        ReceiptData(
            merchant="University Bookstore",
            date="2026-09-01",
            currency="$",
            category=ExpenseCategory.LEARNING.value,
            subtotal=89.50,
            tax=7.16,
            discount=10.00,
            total=86.66,
            line_items=[
                LineItem("Data Structures & Algorithms Course Reader", 1.0, 55.00, 55.00),
                LineItem("Engineering Notebook", 2.0, 12.25, 24.50),
                LineItem("Stapler & Staples", 1.0, 10.00, 10.00),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Fall Semester course materials (largest purchase)",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="City Metro Transit",
            date="2026-09-01",
            currency="$",
            category=ExpenseCategory.TRAVEL.value,
            subtotal=30.00,
            tax=0.00,
            discount=0.00,
            total=30.00,
            line_items=[
                LineItem("September Student Transit Card", 1.0, 30.00, 30.00),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Monthly commuter pass",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Trader Joe's",
            date="2026-09-02",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=38.40,
            tax=0.00,
            discount=0.00,
            total=38.40,
            line_items=[
                LineItem("Chicken Breasts & Tofu", 1.0, 14.20, 14.20),
                LineItem("Brown Rice & Quinoa", 1.0, 6.40, 6.40),
                LineItem("Spinach & Bell Peppers", 1.0, 8.80, 8.80),
                LineItem("Almond Butter & Apples", 1.0, 9.00, 9.00),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Meal prep supplies for first week of classes",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Campus Library Cafe",
            date="2026-09-02",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=5.50,
            tax=0.45,
            discount=0.00,
            total=5.95,
            line_items=[
                LineItem("Cold Brew Coffee", 1.0, 4.50, 4.50),
                LineItem("Extra Espresso Shot", 1.0, 1.00, 1.00),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="First day of semester coffee",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Campus Library Cafe",
            date="2026-09-03",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=4.75,
            tax=0.40,
            discount=0.00,
            total=5.15,
            line_items=[
                LineItem("Iced Tea Latte", 1.0, 4.75, 4.75),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Afternoon study break",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Campus Library Cafe",
            date="2026-09-04",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=5.25,
            tax=0.45,
            discount=0.00,
            total=5.70,
            line_items=[
                LineItem("Matcha Green Tea Latte", 1.0, 5.25, 5.25),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Friday morning boost",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Spotify",
            date="2026-09-11",
            currency="$",
            category=ExpenseCategory.ENTERTAINMENT.value,
            subtotal=5.99,
            tax=0.00,
            discount=0.00,
            total=5.99,
            line_items=[
                LineItem("Spotify Student Premium", 1.0, 5.99, 5.99),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Monthly subscription",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="AMC Theatres",
            date="2026-09-12",
            currency="$",
            category=ExpenseCategory.ENTERTAINMENT.value,
            subtotal=18.50,
            tax=1.50,
            discount=4.00,
            total=16.00,
            line_items=[
                LineItem("Student Matinee Movie Ticket", 1.0, 11.00, 11.00),
                LineItem("Small Popcorn Combo", 1.0, 7.50, 7.50),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Weekend cinema with dorm friends",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Aldi Supermarket",
            date="2026-09-15",
            currency="$",
            category=ExpenseCategory.FOOD.value,
            subtotal=29.10,
            tax=0.00,
            discount=0.00,
            total=29.10,
            line_items=[
                LineItem("Oatmeal, Chia Seeds & Milk", 1.0, 11.20, 11.20),
                LineItem("Frozen Veggies & Pasta", 1.0, 9.50, 9.50),
                LineItem("Canned Beans & Salsa", 1.0, 8.40, 8.40),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Mid-month groceries",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Walgreens",
            date="2026-09-18",
            currency="$",
            category=ExpenseCategory.HEALTH.value,
            subtotal=15.80,
            tax=1.26,
            discount=0.00,
            total=17.06,
            line_items=[
                LineItem("Vitamin C & Zinc Gummies", 1.0, 10.99, 10.99),
                LineItem("Electrolyte Drink Mix", 1.0, 4.81, 4.81),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="Flu season vitamins",
            extraction_method="Sample Data",
        ),
        ReceiptData(
            merchant="Xfinity Internet",
            date="2026-09-28",
            currency="$",
            category=ExpenseCategory.UTILITIES.value,
            subtotal=23.33,
            tax=0.00,
            discount=0.00,
            total=23.33,
            line_items=[
                LineItem("Shared Apartment Wi-Fi (1/3 share)", 1.0, 23.33, 23.33),
            ],
            confidence=FieldConfidence("High", "High", "High", "High"),
            notes="September Wi-Fi bill split",
            extraction_method="Sample Data",
        ),
    ]

    for s in samples:
        s.validate_totals()
    return samples


def populate_sample_data(db: DatabaseManager, budget: float = 650.0) -> int:
    """Populate database with sample student transactions and set budget benchmarks."""
    samples = generate_sample_transactions()
    db.set_budget_for_month("2026-08", budget)
    db.set_budget_for_month("2026-09", budget)

    inserted = 0
    for s in samples:
        # Check if already exists to avoid duplicates when clicking multiple times
        existing = db.find_potential_duplicate(s.merchant, s.date, s.total, day_window=0)
        if not existing:
            db.insert_transaction(s)
            inserted += 1
    return inserted
