"""Unit tests for extractor fallback, untrusted input sanitization, and heuristics."""

import pytest
from PIL import Image, ImageFilter
import numpy as np

from src.models import ExpenseCategory
from src.extractor import (
    sanitize_text,
    sanitize_float,
    suggest_category,
    assess_image_quality,
    RuleBasedFallbackExtractor,
    STUDENT_RECEIPT_TEMPLATES,
    create_from_template,
)


def test_sanitize_text_strips_html_and_limits():
    """Verify HTML tags and excessive chars are sanitized from untrusted OCR text."""
    dirty_text = "<script>alert('hack')</script><b>Trader Joe's</b>   #123 \x00 "
    clean = sanitize_text(dirty_text, max_len=30)
    assert "<script>" not in clean
    assert "<b>" not in clean
    assert "Trader Joe's #123" in clean
    assert len(clean) <= 30


def test_sanitize_float_handles_currency_symbols():
    """Verify dirty currency strings coerce safely to valid floats."""
    assert sanitize_float("$1,234.56") == 1234.56
    assert sanitize_float("Total: $45.99 USD") == 45.99
    assert sanitize_float("€ 19.50") == 19.50
    assert sanitize_float(None, default=0.0) == 0.0
    assert sanitize_float("Invalid text", default=5.0) == 5.0


def test_category_suggestion_keywords():
    """Verify heuristic classification of student merchants."""
    assert suggest_category("Trader Joe's Supermarket") == ExpenseCategory.FOOD.value
    assert suggest_category("Campus Bookstore") == ExpenseCategory.LEARNING.value
    assert suggest_category("City Metro Pass") == ExpenseCategory.TRAVEL.value
    assert suggest_category("CVS Pharmacy") == ExpenseCategory.HEALTH.value
    assert suggest_category("Spotify Premium") == ExpenseCategory.ENTERTAINMENT.value
    assert suggest_category("Pacific Gas & Electric") == ExpenseCategory.UTILITIES.value
    assert suggest_category("Random Mystery Store") == ExpenseCategory.OTHER.value


def test_rule_based_fallback_extractor_without_key():
    """Verify offline extractor returns a structured receipt ready for user review."""
    extractor = RuleBasedFallbackExtractor()
    receipt = extractor.extract(image=None)

    assert receipt.merchant != ""
    assert receipt.total > 0.0
    assert len(receipt.line_items) > 0
    assert receipt.extraction_method == "Rule-based Fallback"
    assert receipt.has_discrepancy is False


def test_student_templates_validity():
    """Ensure all pre-built student templates have balanced totals."""
    for name in STUDENT_RECEIPT_TEMPLATES.keys():
        receipt = create_from_template(name)
        assert receipt.total > 0.0
        assert len(receipt.line_items) > 0
        assert receipt.category in [c.value for c in ExpenseCategory]
        # Tolerance check for student template calculations
        items_sum = sum(i.total_price for i in receipt.line_items)
        calc_total = round(items_sum + receipt.tax - receipt.discount, 2)
        assert abs(calc_total - receipt.total) <= 0.05


def test_image_quality_assessment():
    """Test image sharpness and size detection."""
    # Sharp small image with lines
    img = Image.new("RGB", (300, 300), "white")
    res = assess_image_quality(img)
    assert res["width"] == 300
    assert res["height"] == 300
    assert "sharpness_score" in res
