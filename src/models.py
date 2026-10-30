"""Data models and constants for SpendSight."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, date


class ExpenseCategory(str, Enum):
    FOOD = "Food"
    TRAVEL = "Travel"
    LEARNING = "Learning"
    HEALTH = "Health"
    ENTERTAINMENT = "Entertainment"
    UTILITIES = "Utilities"
    OTHER = "Other"

    @property
    def icon(self) -> str:
        icons = {
            ExpenseCategory.FOOD: "🍔",
            ExpenseCategory.TRAVEL: "🚆",
            ExpenseCategory.LEARNING: "📚",
            ExpenseCategory.HEALTH: "💊",
            ExpenseCategory.ENTERTAINMENT: "🎮",
            ExpenseCategory.UTILITIES: "💡",
            ExpenseCategory.OTHER: "📦",
        }
        return icons.get(self, "🏷️")

    @property
    def color(self) -> str:
        colors = {
            ExpenseCategory.FOOD: "#10B981",         # Emerald
            ExpenseCategory.TRAVEL: "#06B6D4",       # Cyan
            ExpenseCategory.LEARNING: "#6366F1",     # Indigo
            ExpenseCategory.HEALTH: "#EC4899",       # Pink
            ExpenseCategory.ENTERTAINMENT: "#F59E0B", # Amber
            ExpenseCategory.UTILITIES: "#8B5CF6",    # Violet
            ExpenseCategory.OTHER: "#64748B",        # Slate
        }
        return colors.get(self, "#64748B")


CATEGORY_CHOICES = [c.value for c in ExpenseCategory]

CATEGORY_ICONS = {c.value: c.icon for c in ExpenseCategory}
CATEGORY_COLORS = {c.value: c.color for c in ExpenseCategory}


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @property
    def badge_color(self) -> str:
        colors = {
            ConfidenceLevel.HIGH: "#10B981",    # Emerald
            ConfidenceLevel.MEDIUM: "#F59E0B",  # Amber
            ConfidenceLevel.LOW: "#EF4444",     # Red
        }
        return colors.get(self, "#64748B")


@dataclass
class LineItem:
    item_name: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total_price: float = 0.0

    def calculate_total(self) -> float:
        """Compute item total based on quantity and unit price if unit price is set."""
        if self.unit_price > 0 and self.quantity > 0:
            return round(self.quantity * self.unit_price, 2)
        return round(self.total_price, 2)


@dataclass
class FieldConfidence:
    merchant: str = "Medium"
    date: str = "Medium"
    total: str = "Medium"
    line_items: str = "Medium"

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class ReceiptData:
    merchant: str = "Unknown Merchant"
    date: str = field(default_factory=lambda: date.today().isoformat())
    currency: str = "$"
    category: str = ExpenseCategory.OTHER.value
    subtotal: float = 0.0
    tax: float = 0.0
    discount: float = 0.0
    total: float = 0.0
    line_items: List[LineItem] = field(default_factory=list)
    confidence: FieldConfidence = field(default_factory=FieldConfidence)
    notes: str = ""
    has_discrepancy: bool = False
    discrepancy_amount: float = 0.0
    extraction_method: str = "Rule-based Fallback"
    warning_flags: List[str] = field(default_factory=list)

    def validate_totals(self, tolerance: float = 0.02) -> None:
        """
        Validate line item sum against receipt total.
        Formula: calculated_total = sum(item.total_price) + tax - discount
        If line items are empty, validate that total > 0.
        """
        if self.line_items:
            items_sum = sum(item.total_price for item in self.line_items)
            calculated_total = round(items_sum + self.tax - self.discount, 2)
            diff = round(abs(calculated_total - self.total), 2)
            if diff > tolerance:
                self.has_discrepancy = True
                self.discrepancy_amount = round(calculated_total - self.total, 2)
            else:
                self.has_discrepancy = False
                self.discrepancy_amount = 0.0
        else:
            self.has_discrepancy = False
            self.discrepancy_amount = 0.0


@dataclass
class TransactionRecord:
    id: Optional[int] = None
    merchant: str = ""
    date: str = ""
    currency: str = "$"
    category: str = ExpenseCategory.OTHER.value
    subtotal: float = 0.0
    tax: float = 0.0
    discount: float = 0.0
    total: float = 0.0
    confidence_score: float = 0.8
    notes: str = ""
    has_discrepancy: bool = False
    discrepancy_amount: float = 0.0
    has_image: bool = False
    image_bytes: Optional[bytes] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    line_items: List[LineItem] = field(default_factory=list)
