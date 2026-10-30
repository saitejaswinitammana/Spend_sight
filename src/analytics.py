"""Financial analytics, budget tracking, pattern detection, and student insights."""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from src.models import TransactionRecord, ExpenseCategory, CATEGORY_ICONS


def calculate_month_metrics(
    transactions: List[TransactionRecord],
    monthly_budget: float,
    current_month_year: str,  # e.g. "2026-09"
    previous_transactions: Optional[List[TransactionRecord]] = None,
) -> Dict[str, Any]:
    """
    Calculate high-level financial KPIs for the specified month:
    - Total spend
    - Remaining budget
    - Budget consumption %
    - Largest purchase
    - Previous period comparison
    - Discrepancy counts
    """
    current_txs = [t for t in transactions if t.date.startswith(current_month_year)]
    total_spend = sum(t.total for t in current_txs)
    remaining_budget = monthly_budget - total_spend
    spend_pct = (total_spend / monthly_budget * 100.0) if monthly_budget > 0 else 0.0

    # Largest purchase
    if current_txs:
        largest_tx = max(current_txs, key=lambda t: t.total)
        largest_purchase = {
            "merchant": largest_tx.merchant,
            "amount": largest_tx.total,
            "date": largest_tx.date,
            "category": largest_tx.category,
        }
    else:
        largest_purchase = None

    # Previous period comparison
    prev_spend = 0.0
    if previous_transactions is not None:
        prev_spend = sum(t.total for t in previous_transactions)

    spend_diff = total_spend - prev_spend
    if prev_spend > 0:
        pct_change = ((total_spend - prev_spend) / prev_spend) * 100.0
    else:
        pct_change = 0.0 if total_spend == 0 else 100.0

    # Discrepancies
    discrepancy_count = sum(1 for t in current_txs if t.has_discrepancy)

    return {
        "current_month_year": current_month_year,
        "total_spend": round(total_spend, 2),
        "monthly_budget": round(monthly_budget, 2),
        "remaining_budget": round(remaining_budget, 2),
        "spend_percentage": round(spend_pct, 1),
        "largest_purchase": largest_purchase,
        "previous_spend": round(prev_spend, 2),
        "spend_diff": round(spend_diff, 2),
        "pct_change": round(pct_change, 1),
        "transaction_count": len(current_txs),
        "discrepancy_count": discrepancy_count,
    }


def get_category_breakdown(transactions: List[TransactionRecord]) -> pd.DataFrame:
    """Calculate aggregate spending and count per expense category."""
    data: Dict[str, Dict[str, Any]] = {
        cat.value: {"category": cat.value, "icon": cat.icon, "color": cat.color, "total": 0.0, "count": 0}
        for cat in ExpenseCategory
    }

    total_all = sum(t.total for t in transactions)

    for t in transactions:
        cat = t.category if t.category in data else ExpenseCategory.OTHER.value
        data[cat]["total"] += t.total
        data[cat]["count"] += 1

    df = pd.DataFrame(list(data.values()))
    df["percentage"] = df["total"].apply(lambda val: round((val / total_all * 100.0), 1) if total_all > 0 else 0.0)
    df["total"] = df["total"].apply(lambda v: round(v, 2))
    df = df.sort_values(by="total", ascending=False).reset_index(drop=True)
    return df


def get_daily_spending_trend(
    transactions: List[TransactionRecord],
    month_year: str,  # e.g. "2026-09"
) -> pd.DataFrame:
    """Compute daily spending totals and cumulative progress for a given month."""
    try:
        year, month = map(int, month_year.split("-"))
    except ValueError:
        year, month = date.today().year, date.today().month

    # Generate complete date range for the month
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    days_in_month = (next_month - date(year, month, 1)).days

    all_dates = [f"{year:04d}-{month:02d}-{d:02d}" for d in range(1, days_in_month + 1)]
    daily_map = {d: 0.0 for d in all_dates}

    for t in transactions:
        if t.date in daily_map:
            daily_map[t.date] += t.total

    df = pd.DataFrame(list(daily_map.items()), columns=["date", "daily_spend"])
    df["daily_spend"] = df["daily_spend"].round(2)
    df["cumulative_spend"] = df["daily_spend"].cumsum().round(2)
    df["day"] = [int(d.split("-")[2]) for d in df["date"]]
    return df


def detect_recurring_patterns(transactions: List[TransactionRecord]) -> List[Dict[str, Any]]:
    """
    Detect recurring patterns, including:
    - Fixed monthly subscriptions (e.g. Spotify, iCloud, Netflix)
    - Frequent merchant visits (e.g. 4+ visits to campus cafe or dining hall)
    """
    if not transactions:
        return []

    patterns = []
    # Group by normalized merchant
    merchant_map: Dict[str, List[TransactionRecord]] = {}
    for t in transactions:
        key = t.merchant.strip().title()
        merchant_map.setdefault(key, []).append(t)

    for merchant, tx_list in merchant_map.items():
        count = len(tx_list)
        total_spent = sum(t.total for t in tx_list)
        amounts = [t.total for t in tx_list]

        # Subscription check: 2 or more occurrences with near-identical amounts
        if count >= 2:
            unique_amounts = set(round(a, 2) for a in amounts)
            if len(unique_amounts) == 1 or (max(amounts) - min(amounts) < 0.50):
                patterns.append({
                    "type": "Subscription / Fixed Cost",
                    "icon": "🔄",
                    "title": f"Recurring Subscription: {merchant}",
                    "detail": f"{count} bills at ~${amounts[0]:.2f} each (${total_spent:.2f} total).",
                    "severity": "info",
                })
            elif count >= 4:
                patterns.append({
                    "type": "Frequent Habit",
                    "icon": "☕",
                    "title": f"Frequent Visits: {merchant}",
                    "detail": f"Visited {count} times this period, totaling ${total_spent:.2f} (avg ${total_spent/count:.2f}/visit).",
                    "severity": "tip",
                })

    return patterns


def detect_unusual_spending(
    current_txs: List[TransactionRecord],
    all_historical_txs: Optional[List[TransactionRecord]] = None,
) -> List[Dict[str, Any]]:
    """
    Detect unusual spending spikes or outlier purchases in a supportive manner.
    """
    if not current_txs:
        return []

    insights = []
    all_txs = all_historical_txs if all_historical_txs else current_txs
    totals = [t.total for t in all_txs]

    if len(totals) >= 4:
        median_spend = float(np.median(totals))
        q75 = float(np.percentile(totals, 75))
        threshold = max(q75 * 2.0, median_spend * 3.0, 50.0)

        outliers = [t for t in current_txs if t.total > threshold]
        for out in outliers[:2]:  # Report top 2
            insights.append({
                "type": "Notable Purchase",
                "icon": "💎",
                "title": f"High-Value Expense: {out.merchant}",
                "detail": f"${out.total:.2f} on {out.date} in {out.category}. Noticeably higher than your usual ${median_spend:.2f} median purchase.",
                "severity": "warning",
            })

    return insights


def generate_student_savings_tips(
    current_txs: List[TransactionRecord],
    monthly_budget: float,
    current_month_year: str,
) -> List[Dict[str, Any]]:
    """
    Generate non-judgmental, practical, student-tailored savings suggestions.
    Zero shaming; empathetic and supportive phrasing.
    """
    tips = []
    month_txs = [t for t in current_txs if t.date.startswith(current_month_year)]
    total_spend = sum(t.total for t in month_txs)

    # Category totals
    cat_spend: Dict[str, float] = {}
    for t in month_txs:
        cat_spend[t.category] = cat_spend.get(t.category, 0.0) + t.total

    food_spend = cat_spend.get(ExpenseCategory.FOOD.value, 0.0)
    ent_spend = cat_spend.get(ExpenseCategory.ENTERTAINMENT.value, 0.0)
    travel_spend = cat_spend.get(ExpenseCategory.TRAVEL.value, 0.0)
    learn_spend = cat_spend.get(ExpenseCategory.LEARNING.value, 0.0)

    # Food tip
    if food_spend > 150.0:
        tips.append({
            "category": "Food & Dining",
            "icon": "🥗",
            "title": "Smart Meal Prepping & Campus Dining",
            "tip": f"You've invested ${food_spend:.2f} in food this month. Pairing campus meal plan perks or prepping 2 bulk lunches a week can comfortably save ~$25–$40/month without feeling restricted.",
        })

    # Transit tip
    if travel_spend > 40.0:
        tips.append({
            "category": "Transit & Commute",
            "icon": "🚆",
            "title": "Campus Transit Discount Verification",
            "tip": "Check if your university student ID offers semester-subsidized metro cards or campus shuttle routes—many campuses offer up to 50% off regular transit passes.",
        })

    # Learning / Textbook tip
    if learn_spend > 35.0:
        tips.append({
            "category": "Course Materials",
            "icon": "📚",
            "title": "Library Course Reserves & Rental Programs",
            "tip": f"You spent ${learn_spend:.2f} on course materials. Check your university library’s 2-hour textbook loan reserves or digital rental options next semester to minimize upfront costs.",
        })

    # Entertainment / Streaming tip
    if ent_spend > 25.0:
        tips.append({
            "category": "Streaming & Entertainment",
            "icon": "🎧",
            "title": "Student Tier Subscriptions",
            "tip": "Make sure all your digital services (Spotify, Prime, YouTube) are enrolled under student plans (.edu discount), which often slash monthly subscription fees by half.",
        })

    # Budget Health Affirmation
    if total_spend <= monthly_budget:
        remaining = monthly_budget - total_spend
        tips.append({
            "category": "Budget Health",
            "icon": "🌟",
            "title": "Pacing Comfortably on Budget",
            "tip": f"Great pacing! You have ${remaining:.2f} cushion left this month. Keep up the steady mindful tracking.",
        })
    else:
        over = total_spend - monthly_budget
        tips.append({
            "category": "Budget Reflection",
            "icon": "🌱",
            "title": "Budget Calibration",
            "tip": f"You're currently ${over:.2f} above your target. Life and unexpected student costs happen! Review if your monthly goal needs adjusting or if one-off textbook fees skewed the total.",
        })

    return tips
