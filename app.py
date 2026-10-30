"""SpendSight — Smart Receipt & Budget Analyzer for Students.

A modern, privacy-first Streamlit application featuring Google Gemini Vision extraction,
100% offline fallback, SQLite storage, total discrepancy checking, duplicate detection,
and supportive student financial insights.
"""

import os
import io
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from PIL import Image
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

from src.models import (
    ReceiptData,
    LineItem,
    FieldConfidence,
    ExpenseCategory,
    CATEGORY_CHOICES,
    CATEGORY_ICONS,
)
from src.database import DatabaseManager
from src.extractor import (
    GeminiVisionExtractor,
    RuleBasedFallbackExtractor,
    STUDENT_RECEIPT_TEMPLATES,
    create_from_template,
    assess_image_quality,
    sanitize_text,
    sanitize_float,
    suggest_category,
)
from src.analytics import (
    calculate_month_metrics,
    get_category_breakdown,
    get_daily_spending_trend,
    detect_recurring_patterns,
    detect_unusual_spending,
    generate_student_savings_tips,
)
from src.ui_components import (
    inject_custom_theme,
    render_metric_card,
    render_budget_progress,
    create_category_donut_chart,
    create_daily_trend_chart,
    create_category_bar_chart,
    get_confidence_badge_html,
    COLOR_EMERALD,
    COLOR_AMBER,
    COLOR_ROSE,
)
from src.sample_data import populate_sample_data

# Set Streamlit Page Config
st.set_page_config(
    page_title="SpendSight — Student Receipt & Budget Analyzer",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject styling
inject_custom_theme()

# Initialize Database
@st.cache_resource
def get_database() -> DatabaseManager:
    return DatabaseManager()

db = get_database()

# Session State Initialization
if "current_month" not in st.session_state:
    # Default to current month, or 2026-09 if within sample data range
    st.session_state["current_month"] = "2026-09"
if "scanned_receipt" not in st.session_state:
    st.session_state["scanned_receipt"] = None
if "scanned_image_bytes" not in st.session_state:
    st.session_state["scanned_image_bytes"] = None
if "delete_tx_id" not in st.session_state:
    st.session_state["delete_tx_id"] = None
if "edit_tx_id" not in st.session_state:
    st.session_state["edit_tx_id"] = None


# -----------------------------------------------------------------------------
# Sidebar Navigation & Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-size: 1.45rem; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 0.5rem;">
                <span>🧾</span> SpendSight
            </div>
            <div style="font-size: 0.8rem; color: #059669; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">
                Student Budget & Receipt AI
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "📊 Budget Dashboard",
            "📸 Receipt Scanner & Entry",
            "📋 Transactions & Export",
            "⚙️ Settings & Sample Data",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Month Selector
    selected_month = st.selectbox(
        "🗓️ Target Budget Month",
        options=["2026-09", "2026-08", "2026-07", "2026-10"],
        index=0,
        help="Select the month you want to review or budget for.",
    )
    st.session_state["current_month"] = selected_month

    # Quick Monthly Budget Configuration
    current_budget = db.get_budget_for_month(selected_month, default_amount=650.0)
    new_budget = st.number_input(
        f"🎯 Monthly Budget Target ($)",
        min_value=50.0,
        max_value=10000.0,
        value=float(current_budget),
        step=25.0,
        help="Target spending limit for students in the selected month.",
    )
    if new_budget != current_budget:
        db.set_budget_for_month(selected_month, new_budget)
        st.success(f"Budget updated to ${new_budget:.2f}")

    st.markdown("---")

    # API Key & Mode Status
    env_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    user_api_key = st.session_state.get("custom_gemini_key", "").strip()
    active_api_key = user_api_key or env_api_key

    if active_api_key:
        st.markdown(
            """
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.6rem;">
                <div style="color: #065F46; font-size: 0.78rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem;">
                    <span>⚡</span> Gemini Vision Active
                </div>
                <div style="color: #047857; font-size: 0.72rem;">AI receipt extraction ready</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.6rem;">
                <div style="color: #334155; font-size: 0.78rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem;">
                    <span>🛡️</span> Offline Mode Active
                </div>
                <div style="color: #64748B; font-size: 0.72rem;">Rule-based fallback & templates</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Privacy Indicator
    retain_img = db.get_setting("retain_images", "false").lower() == "true"
    retention_status = "Retained" if retain_img else "Discarded (Privacy Default)"
    st.caption(f"🔒 **Receipt Images**: {retention_status}")


# -----------------------------------------------------------------------------
# Top Banner
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="spendsight-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h1><span>🧾</span> SpendSight <span class="spendsight-badge">Student Edition</span></h1>
                <p>Smart, privacy-first receipt scanning and supportive monthly budget tracking.</p>
            </div>
            <div style="text-align: right; background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 10px;">
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #6EE7B7;">Active Month</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">{selected_month}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# PAGE 1: BUDGET DASHBOARD
# =============================================================================
if page == "📊 Budget Dashboard":
    all_txs = db.get_all_transactions()

    # Determine previous month for comparison
    try:
        cur_year, cur_m = map(int, selected_month.split("-"))
        if cur_m == 1:
            prev_month = f"{cur_year - 1:04d}-12"
        else:
            prev_month = f"{cur_year:04d}-{cur_m - 1:02d}"
    except Exception:
        prev_month = "2026-08"

    prev_txs = [t for t in all_txs if t.date.startswith(prev_month)]
    metrics = calculate_month_metrics(
        transactions=all_txs,
        monthly_budget=current_budget,
        current_month_year=selected_month,
        previous_transactions=prev_txs,
    )

    # Empty State Check
    if metrics["transaction_count"] == 0:
        st.info(
            f"No transactions found for **{selected_month}** yet! "
            "Scan a receipt in **Receipt Scanner & Entry** or load fictional demo data below to see the dashboard in action."
        )
        if st.button("✨ Load Realistic Student Sample Data", type="primary"):
            added = populate_sample_data(db, budget=current_budget)
            st.success(f"Loaded {added} realistic student transactions across August & September 2026!")
            st.rerun()

    # 4 Metric Cards Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        # Comparison delta vs previous period
        spend_diff = metrics["spend_diff"]
        pct_chg = metrics["pct_change"]
        if metrics["previous_spend"] > 0:
            if spend_diff > 0:
                delta_str = f"+${spend_diff:.2f} (+{pct_chg:.1f}% vs {prev_month})"
                delta_type = "neg"  # Spending more is higher spend
            else:
                delta_str = f"-${abs(spend_diff):.2f} ({pct_chg:.1f}% vs {prev_month})"
                delta_type = "pos"
        else:
            delta_str = "First period tracked"
            delta_type = "neutral"

        render_metric_card(
            title="Total Spend",
            value=f"${metrics['total_spend']:,.2f}",
            subtext=f"{metrics['transaction_count']} receipts recorded",
            delta=delta_str,
            delta_type=delta_type,
            icon="💳",
        )

    with m_col2:
        rem = metrics["remaining_budget"]
        if rem >= 0:
            rem_title = "Remaining Budget"
            rem_val = f"${rem:,.2f}"
            subtext = f"{100 - metrics['spend_percentage']:.1f}% cushion left"
            delta_type = "pos"
            delta_str = "Under Budget"
        else:
            rem_title = "Over Budget"
            rem_val = f"-${abs(rem):,.2f}"
            subtext = f"Exceeded by ${abs(rem):,.2f}"
            delta_type = "neg"
            delta_str = "Over Target"

        render_metric_card(
            title=rem_title,
            value=rem_val,
            subtext=subtext,
            delta=delta_str,
            delta_type=delta_type,
            icon="🎯",
        )

    with m_col3:
        largest = metrics["largest_purchase"]
        if largest:
            val = f"${largest['amount']:,.2f}"
            sub = f"{largest['merchant']} ({largest['category']})"
            date_info = f"On {largest['date']}"
        else:
            val = "$0.00"
            sub = "No purchases"
            date_info = ""

        render_metric_card(
            title="Largest Purchase",
            value=val,
            subtext=sub,
            delta=date_info,
            delta_type="neutral",
            icon="🏷️",
        )

    with m_col4:
        disc_count = metrics["discrepancy_count"]
        if disc_count > 0:
            render_metric_card(
                title="Line-Item Checks",
                value=f"{disc_count} Flagged",
                subtext="Line-item sums differ from total",
                delta="Review Recommended",
                delta_type="neg",
                icon="⚠️",
            )
        else:
            render_metric_card(
                title="Line-Item Checks",
                value="100% Balanced",
                subtext="All line items match receipt totals",
                delta="Verified Clean",
                delta_type="pos",
                icon="✅",
            )

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Budget Progress Bar
    render_budget_progress(metrics["total_spend"], current_budget)

    # Charts Row
    current_month_txs = [t for t in all_txs if t.date.startswith(selected_month)]
    chart_col1, chart_col2 = st.columns([1, 1])

    with chart_col1:
        st.markdown(
            """
            <div class="ss-card">
                <div style="font-weight: 700; color: #0F172A; font-size: 1rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem;">
                    <span>🍩</span> Spending by Category
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cat_df = get_category_breakdown(current_month_txs)
        donut_fig = create_category_donut_chart(cat_df, metrics["total_spend"])
        st.plotly_chart(donut_fig, use_container_width=True)

    with chart_col2:
        st.markdown(
            """
            <div class="ss-card">
                <div style="font-weight: 700; color: #0F172A; font-size: 1rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem;">
                    <span>📈</span> Daily Spending Trend & Cumulative Pace
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        trend_df = get_daily_spending_trend(current_month_txs, selected_month)
        trend_fig = create_daily_trend_chart(trend_df, current_budget)
        st.plotly_chart(trend_fig, use_container_width=True)

    # Category Bar Chart & Detailed Breakdown
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    with st.expander("📊 Detailed Category Breakdown & Item Counts", expanded=False):
        col_bar, col_table = st.columns([1.2, 1])
        with col_bar:
            bar_fig = create_category_bar_chart(cat_df)
            st.plotly_chart(bar_fig, use_container_width=True)
        with col_table:
            st.dataframe(
                cat_df[["category", "total", "percentage", "count"]].rename(
                    columns={
                        "category": "Category",
                        "total": "Total Spent ($)",
                        "percentage": "Share (%)",
                        "count": "Receipts",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Insight Cards Section
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 1.2rem 0 0.8rem 0; display: flex; align-items: center; gap: 0.5rem;">
            <span>💡</span> Student Financial Insights & Mindful Hacks
        </div>
        """,
        unsafe_allow_html=True,
    )

    recurring_patterns = detect_recurring_patterns(current_month_txs)
    unusual_spends = detect_unusual_spending(current_month_txs, all_txs)
    saving_tips = generate_student_savings_tips(current_month_txs, current_budget, selected_month)

    i_col1, i_col2 = st.columns(2)

    with i_col1:
        st.markdown(
            "<div style='font-weight: 700; color: #334155; font-size: 0.92rem; margin-bottom: 0.5rem;'>🔄 Recurring Patterns & Subscriptions</div>",
            unsafe_allow_html=True,
        )
        if recurring_patterns:
            for p in recurring_patterns:
                st.markdown(
                    f"""
                    <div class="ss-insight-card" style="border-left-color: #06B6D4; background: #F0FDFA; border-color: #CCFBF1;">
                        <div class="ss-insight-title" style="color: #0F766E;">{p['icon']} {p['title']}</div>
                        <div class="ss-insight-body">{p['detail']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No recurring subscriptions or multi-visit habits detected in this month yet.")

        if unusual_spends:
            st.markdown(
                "<div style='font-weight: 700; color: #334155; font-size: 0.92rem; margin: 0.8rem 0 0.5rem 0;'>💎 Notable / Spike Expenses</div>",
                unsafe_allow_html=True,
            )
            for u in unusual_spends:
                st.markdown(
                    f"""
                    <div class="ss-insight-card" style="border-left-color: #F59E0B; background: #FFFBEB; border-color: #FEF3C7;">
                        <div class="ss-insight-title" style="color: #B45309;">{u['icon']} {u['title']}</div>
                        <div class="ss-insight-body">{u['detail']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with i_col2:
        st.markdown(
            "<div style='font-weight: 700; color: #334155; font-size: 0.92rem; margin-bottom: 0.5rem;'>🌱 Practical Savings Actions (Zero Shame)</div>",
            unsafe_allow_html=True,
        )
        if saving_tips:
            for tip in saving_tips:
                st.markdown(
                    f"""
                    <div class="ss-insight-card">
                        <div class="ss-insight-title">{tip['icon']} {tip['title']}</div>
                        <div class="ss-insight-body">{tip['tip']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Add more transactions to unlock tailored student budget recommendations.")


# =============================================================================
# PAGE 2: RECEIPT SCANNER & ENTRY
# =============================================================================
elif page == "📸 Receipt Scanner & Entry":
    st.markdown(
        """
        <div style="font-size: 1.3rem; font-weight: 800; color: #0F172A; margin-bottom: 0.5rem;">
            Scan & Review Receipt
        </div>
        <p style="color: #64748B; font-size: 0.9rem;">
            Upload a receipt image (JPG, JPEG, PNG), take a photo, or select a student archetype.
            Review extracted details, verify line items, and confirm before saving.
        </p>
        """,
        unsafe_allow_html=True,
    )

    tab_upload, tab_camera, tab_template = st.tabs([
        "📁 Upload Receipt File",
        "📷 Camera Capture",
        "⚡ Quick Student Template",
    ])

    uploaded_image: Optional[Image.Image] = None
    uploaded_bytes: Optional[bytes] = None

    with tab_upload:
        file_buffer = st.file_uploader(
            "Select receipt image (JPG, JPEG, PNG)",
            type=["jpg", "jpeg", "png"],
            help="Images are processed locally and discarded unless you enable image retention.",
        )
        if file_buffer is not None:
            try:
                uploaded_bytes = file_buffer.getvalue()
                uploaded_image = Image.open(io.BytesIO(uploaded_bytes))
            except Exception as e:
                st.error(f"Could not read image file: {e}. Please ensure it is a valid JPG/PNG.")

    with tab_camera:
        camera_buffer = st.camera_input("Take a photo of your receipt")
        if camera_buffer is not None:
            try:
                uploaded_bytes = camera_buffer.getvalue()
                uploaded_image = Image.open(io.BytesIO(uploaded_bytes))
            except Exception as e:
                st.error(f"Error capturing camera image: {e}")

    with tab_template:
        st.write("No receipt handy right now? Pick a standard student expense template to test:")
        selected_template = st.selectbox("Template Type", list(STUDENT_RECEIPT_TEMPLATES.keys()))
        if st.button("Apply Template", key="apply_template_btn"):
            st.session_state["scanned_receipt"] = create_from_template(selected_template)
            st.session_state["scanned_image_bytes"] = None
            st.success(f"Applied template: {selected_template}")

    # Process Uploaded Image
    if uploaded_image is not None:
        col_img, col_proc = st.columns([1, 1.4])

        with col_img:
            st.markdown(
                """
                <div style="font-weight: 700; color: #334155; font-size: 0.9rem; margin-bottom: 0.4rem;">
                    Receipt Preview
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Modern Streamlit image API
            st.image(uploaded_image, use_container_width=True)

            # Quality and Blur Analysis
            quality = assess_image_quality(uploaded_image)
            if quality["warnings"]:
                for w in quality["warnings"]:
                    st.warning(f"⚠️ {w}")
            else:
                st.success("✅ Image sharpness looks crisp and readable.")

        with col_proc:
            st.markdown(
                """
                <div style="font-weight: 700; color: #334155; font-size: 0.9rem; margin-bottom: 0.4rem;">
                    Extraction Engine
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Choose extraction mode
            has_gemini = bool(active_api_key)
            extractor_choice = st.radio(
                "Extraction Method:",
                options=[
                    "Google Gemini Vision (AI)" if has_gemini else "Google Gemini Vision (Requires API Key)",
                    "Offline Rule-Based / Manual Entry",
                ],
                index=0 if has_gemini else 1,
            )

            if st.button("🚀 Extract Receipt Data", type="primary", use_container_width=True):
                with st.spinner("Extracting structured receipt data..."):
                    if "Gemini Vision" in extractor_choice and has_gemini:
                        try:
                            extractor = GeminiVisionExtractor(api_key=active_api_key)
                            parsed_receipt = extractor.extract(uploaded_image)
                        except Exception as e:
                            st.warning(f"Gemini extraction error: {e}. Using offline fallback.")
                            parsed_receipt = RuleBasedFallbackExtractor().extract(uploaded_image)
                    else:
                        parsed_receipt = RuleBasedFallbackExtractor().extract(uploaded_image)

                    st.session_state["scanned_receipt"] = parsed_receipt
                    st.session_state["scanned_image_bytes"] = uploaded_bytes
                    st.success("Extraction complete! Please review and confirm the details below.")

    # -------------------------------------------------------------------------
    # Structured Review and Confirmation Form
    # -------------------------------------------------------------------------
    receipt_to_review: Optional[ReceiptData] = st.session_state.get("scanned_receipt")

    if receipt_to_review:
        st.markdown("---")
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div style="font-size: 1.2rem; font-weight: 800; color: #0F172A;">
                    📝 Verify & Confirm Receipt Details
                </div>
                <div style="font-size: 0.8rem; background: #F1F5F9; padding: 0.3rem 0.7rem; border-radius: 6px; font-weight: 600; color: #475569;">
                    Method: {receipt_to_review.extraction_method}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Confidence Badges Row
        conf = receipt_to_review.confidence
        st.markdown(
            f"""
            <div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.2rem; background: #F8FAFC; padding: 0.8rem 1rem; border-radius: 10px; border: 1px solid #E2E8F0;">
                <div><span style="font-size: 0.78rem; color: #64748B;">Merchant:</span> {get_confidence_badge_html(conf.merchant)}</div>
                <div><span style="font-size: 0.78rem; color: #64748B;">Date:</span> {get_confidence_badge_html(conf.date)}</div>
                <div><span style="font-size: 0.78rem; color: #64748B;">Total:</span> {get_confidence_badge_html(conf.total)}</div>
                <div><span style="font-size: 0.78rem; color: #64748B;">Line Items:</span> {get_confidence_badge_html(conf.line_items)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Main Editable Form
        with st.form("confirm_receipt_form"):
            r_col1, r_col2, r_col3 = st.columns(3)

            with r_col1:
                edit_merchant = st.text_input("Merchant / Store Name", value=receipt_to_review.merchant)
                try:
                    default_date = datetime.strptime(receipt_to_review.date, "%Y-%m-%d").date()
                except Exception:
                    default_date = date.today()
                edit_date = st.date_input("Transaction Date", value=default_date)

            with r_col2:
                cur_cat = receipt_to_review.category
                cat_idx = CATEGORY_CHOICES.index(cur_cat) if cur_cat in CATEGORY_CHOICES else 0
                edit_category = st.selectbox(
                    "Expense Category",
                    options=CATEGORY_CHOICES,
                    index=cat_idx,
                    format_func=lambda c: f"{CATEGORY_ICONS.get(c, '🏷️')} {c}",
                )
                edit_currency = st.text_input("Currency Symbol", value=receipt_to_review.currency or "$")

            with r_col3:
                edit_tax = st.number_input("Tax ($)", min_value=0.0, value=float(receipt_to_review.tax), step=0.25)
                edit_discount = st.number_input("Discount / Savings ($)", min_value=0.0, value=float(receipt_to_review.discount), step=0.50)

            st.markdown("#### Line Items")
            st.caption("Adjust items, quantities, or unit prices. The total is calculated automatically.")

            # Prepare initial line items data for editor
            initial_items_data = [
                {
                    "item_name": item.item_name,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "total_price": float(item.total_price),
                }
                for item in receipt_to_review.line_items
            ]
            if not initial_items_data:
                initial_items_data = [{"item_name": "Item 1", "quantity": 1.0, "unit_price": float(receipt_to_review.total), "total_price": float(receipt_to_review.total)}]

            items_df = pd.DataFrame(initial_items_data)
            edited_items_df = st.data_editor(
                items_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "item_name": st.column_config.TextColumn("Item Description", required=True),
                    "quantity": st.column_config.NumberColumn("Qty", min_value=0.1, step=1.0, default=1.0),
                    "unit_price": st.column_config.NumberColumn("Unit Price ($)", min_value=0.0, format="$%.2f", step=0.5),
                    "total_price": st.column_config.NumberColumn("Total Price ($)", min_value=0.0, format="$%.2f", step=0.5),
                },
            )

            # Final Total Input
            t_col1, t_col2 = st.columns([1, 1.5])
            with t_col1:
                edit_total = st.number_input(
                    "Receipt Total Amount ($)",
                    min_value=0.0,
                    value=float(receipt_to_review.total),
                    step=0.50,
                    help="Final amount charged to your card or paid in cash.",
                )
            with t_col2:
                edit_notes = st.text_input("Notes / Purpose", value=receipt_to_review.notes or "")

            # Submit button
            submitted = st.form_submit_button("💾 Confirm & Save Transaction", type="primary", use_container_width=True)

        # Reconciliation / Discrepancy Check on Current Values
        current_items_sum = 0.0
        parsed_items: List[LineItem] = []
        for _, row in edited_items_df.iterrows():
            name = str(row.get("item_name", "Item")).strip()
            qty = float(row.get("quantity", 1.0) or 1.0)
            u_p = float(row.get("unit_price", 0.0) or 0.0)
            t_p = float(row.get("total_price", 0.0) or 0.0)
            if t_p == 0.0 and u_p > 0:
                t_p = round(qty * u_p, 2)
            parsed_items.append(LineItem(item_name=name, quantity=qty, unit_price=u_p, total_price=t_p))
            current_items_sum += t_p

        calc_expected_total = round(current_items_sum + edit_tax - edit_discount, 2)
        discrepancy = round(abs(calc_expected_total - edit_total), 2)

        if discrepancy > 0.02:
            st.markdown(
                f"""
                <div class="ss-discrepancy-box">
                    <div class="ss-discrepancy-title">⚠️ Total Discrepancy Flagged</div>
                    <div style="color: #78350F; font-size: 0.85rem; margin-top: 0.2rem;">
                        Line items sum (${current_items_sum:.2f}) + Tax (${edit_tax:.2f}) - Discount (${edit_discount:.2f}) = <b>${calc_expected_total:.2f}</b>,
                        which differs from receipt total <b>${edit_total:.2f}</b> by <b>${discrepancy:.2f}</b>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Duplicate Receipt Warning Check
        formatted_date_str = edit_date.strftime("%Y-%m-%d")
        dup_match = db.find_potential_duplicate(
            merchant=edit_merchant,
            date_str=formatted_date_str,
            total=edit_total,
            day_window=2,
        )
        if dup_match:
            st.markdown(
                f"""
                <div style="background: #FFF7ED; border-left: 4px solid #EA580C; padding: 0.8rem 1rem; border-radius: 8px; margin: 0.8rem 0; border: 1px solid #FFEDD5;">
                    <div style="font-weight: 700; color: #C2410C; font-size: 0.9rem;">
                        ⚠️ Potential Duplicate Receipt Detected!
                    </div>
                    <div style="color: #9A3412; font-size: 0.84rem; margin-top: 0.2rem;">
                        An existing transaction matching <b>"{dup_match['merchant']}"</b> on <b>{dup_match['date']}</b> for <b>${dup_match['total']:.2f}</b> was found (ID #{dup_match['id']}).
                        If this is an intentional repeat purchase, you may still proceed.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Handle Form Submission
        if submitted:
            # Build finalized ReceiptData
            final_receipt = ReceiptData(
                merchant=sanitize_text(edit_merchant),
                date=formatted_date_str,
                currency=edit_currency,
                category=edit_category,
                subtotal=current_items_sum,
                tax=edit_tax,
                discount=edit_discount,
                total=edit_total,
                line_items=parsed_items,
                confidence=receipt_to_review.confidence,
                notes=sanitize_text(edit_notes),
                extraction_method=receipt_to_review.extraction_method,
            )
            final_receipt.validate_totals()

            img_bytes = st.session_state.get("scanned_image_bytes")
            new_id = db.insert_transaction(final_receipt, image_bytes=img_bytes)

            st.toast(f"✅ Transaction #{new_id} successfully saved to budget!", icon="🎉")
            st.success(f"Receipt saved as Transaction #{new_id} ({final_receipt.merchant} — ${final_receipt.total:.2f})")

            # Reset review state
            st.session_state["scanned_receipt"] = None
            st.session_state["scanned_image_bytes"] = None


# =============================================================================
# PAGE 3: TRANSACTIONS & CSV EXPORT
# =============================================================================
elif page == "📋 Transactions & Export":
    st.markdown(
        """
        <div style="font-size: 1.3rem; font-weight: 800; color: #0F172A; margin-bottom: 0.4rem;">
            Transaction Records & Export
        </div>
        <p style="color: #64748B; font-size: 0.9rem;">
            Search, filter, view itemized lines, edit, delete with confirmation, and export to CSV.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Filter Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1, 1, 1])

    with f_col1:
        search_kw = st.text_input("🔍 Search Merchant or Notes", placeholder="e.g. Bookstore, Coffee...")
    with f_col2:
        filter_cat = st.selectbox("Category Filter", ["All"] + CATEGORY_CHOICES)
    with f_col3:
        filter_disc = st.checkbox("Only Discrepancies", value=False)
    with f_col4:
        # CSV Export Options
        csv_full = db.export_csv(include_line_items=True)
        st.download_button(
            label="📥 Export CSV",
            data=csv_full,
            file_name=f"spendsight_transactions_{date.today().isoformat()}.csv",
            mime="text/csv",
            help="Download transactions with full line items in CSV format",
            use_container_width=True,
        )

    # Fetch Filtered Transactions
    transactions = db.get_all_transactions(
        category=filter_cat,
        search_query=search_kw,
        only_discrepancies=filter_disc,
    )

    st.markdown(f"**Found {len(transactions)} transactions**")

    if not transactions:
        st.info("No matching transactions found. Try adjusting your filters or adding new receipts.")
    else:
        # Display Transaction List with Expandable Line Items & Actions
        for t in transactions:
            disc_badge = "⚠️ Discrepancy" if t.has_discrepancy else "✅ Balanced"
            cat_icon = CATEGORY_ICONS.get(t.category, "🏷️")

            with st.expander(f"{cat_icon} {t.merchant} — ${t.total:.2f} | {t.date} ({t.category})"):
                t_info_col1, t_info_col2 = st.columns([2, 1])

                with t_info_col1:
                    st.markdown(
                        f"""
                        **Date**: {t.date} &nbsp;|&nbsp; **Category**: {cat_icon} {t.category} &nbsp;|&nbsp; **Status**: {disc_badge}  
                        **Tax**: ${t.tax:.2f} &nbsp;|&nbsp; **Discount**: ${t.discount:.2f} &nbsp;|&nbsp; **Confidence**: {t.confidence_score*100:.0f}%  
                        **Notes**: {t.notes if t.notes else 'None'}
                        """
                    )

                    # Show line items table if present
                    if t.line_items:
                        items_summary = [
                            {
                                "Item": item.item_name,
                                "Qty": item.quantity,
                                "Unit Price ($)": f"${item.unit_price:.2f}",
                                "Total ($)": f"${item.total_price:.2f}",
                            }
                            for item in t.line_items
                        ]
                        st.table(pd.DataFrame(items_summary))
                    else:
                        st.caption("No individual line items stored.")

                with t_info_col2:
                    st.markdown("##### Manage")

                    # Edit Transaction
                    if st.button("✏️ Edit", key=f"edit_btn_{t.id}"):
                        st.session_state["edit_tx_id"] = t.id

                    # Delete Transaction with Confirmation
                    if st.button("🗑️ Delete", key=f"del_btn_{t.id}"):
                        st.session_state["delete_tx_id"] = t.id

                    # Show confirmation UI if this ID was clicked
                    if st.session_state.get("delete_tx_id") == t.id:
                        st.error(f"Are you sure you want to permanently delete #{t.id} ({t.merchant})?")
                        c_yes, c_no = st.columns(2)
                        with c_yes:
                            if st.button("Confirm Delete", key=f"confirm_del_{t.id}", type="primary"):
                                db.delete_transaction(t.id)
                                st.session_state["delete_tx_id"] = None
                                st.success(f"Transaction #{t.id} deleted.")
                                st.rerun()
                        with c_no:
                            if st.button("Cancel", key=f"cancel_del_{t.id}"):
                                st.session_state["delete_tx_id"] = None
                                st.rerun()

            # Inline Edit Form if this transaction is being edited
            if st.session_state.get("edit_tx_id") == t.id:
                with st.form(f"inline_edit_form_{t.id}"):
                    st.markdown(f"#### Edit Transaction #{t.id}")
                    e_col1, e_col2, e_col3 = st.columns(3)
                    with e_col1:
                        e_merchant = st.text_input("Merchant", value=t.merchant)
                        e_date = st.date_input("Date", value=datetime.strptime(t.date, "%Y-%m-%d").date())
                    with e_col2:
                        e_cat_idx = CATEGORY_CHOICES.index(t.category) if t.category in CATEGORY_CHOICES else 0
                        e_category = st.selectbox("Category", CATEGORY_CHOICES, index=e_cat_idx)
                        e_total = st.number_input("Total Amount ($)", min_value=0.0, value=float(t.total), step=0.5)
                    with e_col3:
                        e_tax = st.number_input("Tax ($)", min_value=0.0, value=float(t.tax), step=0.25)
                        e_notes = st.text_input("Notes", value=t.notes)

                    sub_e1, sub_e2 = st.columns(2)
                    with sub_e1:
                        if st.form_submit_button("Save Changes", type="primary"):
                            db.update_transaction(
                                tx_id=t.id,
                                merchant=e_merchant,
                                date_str=e_date.strftime("%Y-%m-%d"),
                                category=e_category,
                                total=e_total,
                                tax=e_tax,
                                notes=e_notes,
                            )
                            st.session_state["edit_tx_id"] = None
                            st.success("Transaction updated!")
                            st.rerun()
                    with sub_e2:
                        if st.form_submit_button("Cancel"):
                            st.session_state["edit_tx_id"] = None
                            st.rerun()


# =============================================================================
# PAGE 4: SETTINGS & SAMPLE DATA
# =============================================================================
elif page == "⚙️ Settings & Sample Data":
    st.markdown(
        """
        <div style="font-size: 1.3rem; font-weight: 800; color: #0F172A; margin-bottom: 0.4rem;">
            Application Preferences & Tools
        </div>
        <p style="color: #64748B; font-size: 0.9rem;">
            Manage sample data, API keys, privacy toggles, and database storage.
        </p>
        """,
        unsafe_allow_html=True,
    )

    s_col1, s_col2 = st.columns(2)

    with s_col1:
        # Sample Data Section
        st.markdown(
            """
            <div class="ss-card">
                <div style="font-weight: 700; color: #0F172A; font-size: 1.05rem; margin-bottom: 0.4rem;">
                    ✨ Demo & Sample Data Generator
                </div>
                <div style="color: #64748B; font-size: 0.86rem; margin-bottom: 1rem;">
                    Instantly populates realistic fictional student receipts across August & September 2026
                    (groceries, university bookstore, campus coffee, transit pass, utilities).
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚀 Load Realistic Student Sample Data", type="primary", use_container_width=True):
            added = populate_sample_data(db)
            st.toast(f"Loaded {added} realistic student transactions!", icon="🎉")
            st.success(f"Success! {added} student transactions loaded into SQLite database.")

        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)

        # Clear Data Section
        st.markdown(
            """
            <div class="ss-card">
                <div style="font-weight: 700; color: #BE123C; font-size: 1.05rem; margin-bottom: 0.4rem;">
                    🗑️ Reset Database
                </div>
                <div style="color: #64748B; font-size: 0.86rem; margin-bottom: 1rem;">
                    Delete all recorded transactions and start completely fresh.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("⚠️ Clear All Transactions", use_container_width=True):
            st.session_state["confirm_reset"] = True

        if st.session_state.get("confirm_reset", False):
            st.warning("Are you sure? This cannot be undone.")
            c_del1, c_del2 = st.columns(2)
            with c_del1:
                if st.button("Yes, Clear Everything", type="primary"):
                    db.clear_all_transactions()
                    st.session_state["confirm_reset"] = False
                    st.success("All transactions cleared.")
                    st.rerun()
            with c_del2:
                if st.button("Cancel"):
                    st.session_state["confirm_reset"] = False
                    st.rerun()

    with s_col2:
        # Privacy & Storage
        st.markdown(
            """
            <div class="ss-card">
                <div style="font-weight: 700; color: #0F172A; font-size: 1.05rem; margin-bottom: 0.4rem;">
                    🔒 Privacy & Receipt Image Storage
                </div>
                <div style="color: #64748B; font-size: 0.86rem; margin-bottom: 0.8rem;">
                    By default, SpendSight adheres to strict privacy: only corrected structured text
                    and numeric data are saved in SQLite. Receipt images are discarded after extraction.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_retention = db.get_setting("retain_images", "false").lower() == "true"
        new_retention = st.toggle(
            "Retain receipt images in database",
            value=current_retention,
            help="When enabled, binary images of uploaded receipts are stored in the SQLite database.",
        )
        if new_retention != current_retention:
            db.set_setting("retain_images", str(new_retention).lower())
            st.success(f"Image retention setting updated to: {new_retention}")

        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)

        # Gemini API Key Setup
        st.markdown(
            """
            <div class="ss-card">
                <div style="font-weight: 700; color: #0F172A; font-size: 1.05rem; margin-bottom: 0.4rem;">
                    🔑 Google Gemini API Key (Optional)
                </div>
                <div style="color: #64748B; font-size: 0.86rem; margin-bottom: 0.8rem;">
                    Provide an API key to enable Gemini Vision multimodal OCR.
                    SpendSight remains 100% functional without an API key using offline heuristic templates.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        custom_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("custom_gemini_key", os.getenv("GEMINI_API_KEY", "")),
            type="password",
            help="Get your key at https://aistudio.google.com/",
        )
        if custom_key != st.session_state.get("custom_gemini_key", ""):
            st.session_state["custom_gemini_key"] = custom_key
            st.success("API key registered in active session.")


# -----------------------------------------------------------------------------
# Footer & Legal Disclaimer
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="ss-disclaimer">
        <b>Disclaimer:</b> SpendSight is an educational financial tool designed for students.
        It does not provide certified financial, accounting, investment, or tax advice.
        All insights, calculations, and suggestions are for informational and planning purposes only.
    </div>
    """,
    unsafe_allow_html=True,
)
