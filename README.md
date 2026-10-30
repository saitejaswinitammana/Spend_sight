# SpendSight — Smart Receipt & Budget Analyzer

> **A modern, privacy-first receipt scanner and mindful budget analyzer tailored for students managing monthly expenses.**

SpendSight is built with **Python 3.11+**, **Streamlit**, **Pillow**, **Pandas**, **Plotly**, and **SQLite**. It features a pluggable extraction layer supporting **Google Gemini Vision** (`google-genai` SDK) paired with a **100% offline rule-based fallback** and pre-built student expense archetypes. The application remains completely functional even when no API key is present.

---

## 🌟 Key Features

1. **Receipt Ingestion & Modern Image Preview**:
   - Accepts **JPG, JPEG, and PNG** formats.
   - Live image preview using current Streamlit container APIs (`st.image(..., use_container_width=True)`).
   - Real-time **blur and sharpness detection** (gradient edge variance analysis) flagging unreadable or low-resolution captures.
   - Mobile-friendly upload flow with camera input option.

2. **Pluggable Structured Extraction**:
   - Automatically extracts **Merchant**, **Date**, **Currency**, **Line Items** (Item Name, Qty, Unit Price, Total Price), **Tax**, **Discount**, and **Total**.
   - Displays **confidence levels** (`High`, `Medium`, `Low`) per field.
   - **User Confirmation Required**: Interactive line-item editor (`st.data_editor`) allowing full inspection and manual adjustment prior to saving.

3. **Discrepancy Validation & Duplicate Protection**:
   - **Math Verification**: Verifies that $\text{Sum}(\text{Line Items}) + \text{Tax} - \text{Discount} = \text{Total}$ (within \$0.02 tolerance) and highlights discrepancies with an amber alert box.
   - **Duplicate Detection**: Searches for transactions matching `(LOWER(merchant), date, total)` within a 2-day window to alert students before saving accidental duplicates.
   - **Untrusted Input Sanitization**: Strips malicious HTML/scripts, removes control characters, and cleans numeric fields.

4. **Student Expense Categories**:
   - Categorizes spending into:
     - 🍔 **Food**
     - 🚆 **Travel**
     - 📚 **Learning**
     - 💊 **Health**
     - 🎮 **Entertainment**
     - 💡 **Utilities**
     - 📦 **Other**
   - Auto-categorization engine using merchant and line-item keyword heuristics with 1-click manual dropdown overrides.

5. **Mindful Student Budget Dashboard**:
   - Set monthly student budget goals (e.g. \$650/month).
   - **Metric Cards**: Total Spend, Remaining Budget Cushion, Largest Purchase, and Period-over-Period comparisons ($\pm\$$ and $\%$ change vs. prior month).
   - **Budget Progress Indicator**: Color shifts from Emerald (safe zone $<75\%$), Amber (nearing limit $75\%-100\%$), to Rose (budget exceeded $>100\%$).
   - **Plotly Visualizations**:
     - Interactive Category Donut Chart with center spend callout.
     - Daily Spending Bar Chart & Cumulative Spend Pace Line.
     - Category Comparison Horizontal Bar Chart.

6. **Student Insight Cards (Zero Shame)**:
   - **Recurring Patterns**: Detects recurring monthly subscriptions (Spotify Student, Wi-Fi split) and habitual visits (campus cafe, dining hall).
   - **Notable Purchases**: Flags outlier expenses exceeding typical student spending.
   - **Empathetic Savings Tips**: Practical student advice (library textbook reserves, campus meal plan perks, student transit cards, streaming discounts) written in an encouraging, non-judgmental tone.

7. **Transaction Records & CSV Export**:
   - Search across merchants and notes.
   - Filter by category, date range, or discrepancy status.
   - Inline edit and delete with explicit confirmation modal to prevent accidental loss.
   - One-click CSV export with complete itemized line items.

8. **Privacy-First Design**:
   - Structured financial data is stored in a local SQLite database (`spendsight.db`).
   - By default, **receipt images are discarded immediately** after extraction. Image retention can be explicitly opted-in via settings.

---

## 📁 Project Architecture

```
spendsight/
├── app.py                      # Main Streamlit application entrypoint
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── README.md                   # Documentation & setup guide
├── spendsight.db               # Local SQLite database (auto-created on first run)
├── src/
│   ├── __init__.py
│   ├── models.py               # Dataclasses (ReceiptData, LineItem, ExpenseCategory, etc.)
│   ├── database.py             # SQLite DB manager, migrations, CRUD, duplicate detector, CSV exporter
│   ├── extractor.py            # GeminiVisionExtractor, RuleBasedFallbackExtractor, blur checker, sanitizer
│   ├── analytics.py            # Financial calculations, period comparison, pattern detector, tips engine
│   ├── ui_components.py        # Emerald/Charcoal CSS theme, Plotly charts, metric cards, progress bars
│   └── sample_data.py          # Generator for realistic student expenses (Aug & Sept 2026)
└── tests/
    ├── __init__.py
    ├── test_calculations.py    # Unit tests for line-item math, discrepancies, budget deltas
    ├── test_duplicate_detection.py # Unit tests for duplicate receipt identification
    └── test_extractor.py       # Unit tests for untrusted OCR input sanitization & fallback heuristics
```

---

## 🚀 Setup & Installation Instructions

### Prerequisites
- **Python 3.11+** installed on your system.

### Step 1: Open the Project Directory
Navigate to the project root directory:
```bash
cd C:\Users\tejas\.gemini\antigravity\scratch\spendsight
```
*(Recommended: Set `C:\Users\tejas\.gemini\antigravity\scratch\spendsight` as your active workspace in your IDE).*

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment (Optional)
Copy the example environment file:
```bash
copy .env.example .env
```
Edit `.env` to configure your optional Google Gemini API key:
```env
# Optional: Google Gemini API Key for AI Vision receipt extraction.
# If omitted or left empty, SpendSight automatically uses offline mode!
GEMINI_API_KEY=your_gemini_api_key_here

# Default student monthly budget in dollars
DEFAULT_MONTHLY_BUDGET=650.00

# Privacy: retain binary images in SQLite (false by default)
SPENDSIGHT_RETAIN_IMAGES=false
```

> **Note**: You can also enter or update your Gemini API Key directly within the running application under the **⚙️ Settings & Sample Data** tab or sidebar.

### Step 4: Run the Application
Launch the Streamlit app:
```bash
python -m streamlit run app.py
```
Open your browser to the local URL (usually `http://localhost:8501`).

---

## 🧪 Running Unit Tests

SpendSight includes a comprehensive pytest suite covering financial math, line-item reconciliation, duplicate receipt detection, and input sanitization:

```bash
python -m pytest -v tests/
```

Expected output:
```
tests/test_calculations.py::test_line_item_total_match PASSED
tests/test_calculations.py::test_line_item_discrepancy_detection PASSED
tests/test_calculations.py::test_calculate_month_metrics_under_budget PASSED
tests/test_calculations.py::test_calculate_month_metrics_over_budget PASSED
tests/test_calculations.py::test_period_over_period_comparison PASSED
tests/test_calculations.py::test_category_breakdown_percentages PASSED
tests/test_calculations.py::test_daily_spending_trend_cumulative PASSED
tests/test_duplicate_detection.py::test_exact_duplicate_detection PASSED
tests/test_duplicate_detection.py::test_case_insensitive_merchant_duplicate PASSED
tests/test_duplicate_detection.py::test_day_window_duplicate_detection PASSED
tests/test_duplicate_detection.py::test_different_amount_not_duplicate PASSED
tests/test_duplicate_detection.py::test_exclude_self_during_update PASSED
tests/test_extractor.py::test_sanitize_text_strips_html_and_limits PASSED
tests/test_extractor.py::test_sanitize_float_handles_currency_symbols PASSED
tests/test_extractor.py::test_category_suggestion_keywords PASSED
tests/test_extractor.py::test_rule_based_fallback_extractor_without_key PASSED
tests/test_extractor.py::test_student_templates_validity PASSED
tests/test_extractor.py::test_image_quality_assessment PASSED
============================= 18 passed in 1.63s ==============================
```

---

## 🎯 Quick Demo Walkthrough

1. **Load Realistic Sample Data**:
   - Go to **⚙️ Settings & Sample Data** or click the sample data button on the **📊 Budget Dashboard**.
   - Click **"🚀 Load Realistic Student Sample Data"** to immediately populate 20 realistic student expenses (Trader Joe's, Campus Bookstore, Metro Pass, Boba Tea, Off-campus Wi-Fi split).
2. **Review Budget Dashboard**:
   - View the Total Spend, Remaining Budget Cushion, and Month-over-Month comparison vs. August 2026.
   - Explore the Category Donut Chart, Daily Spending Pace, and Student Financial Insight Cards.
3. **Scan a New Receipt**:
   - Go to **📸 Receipt Scanner & Entry**.
   - Upload an image or select a **Quick Student Template** (e.g., *Campus Bookstore / Learning Supplies*).
   - Review the extracted fields, line items, and confidence ratings.
   - Notice how SpendSight validates the line-item sum against the total and checks for duplicate receipts before saving.
4. **Manage Records & Export**:
   - Switch to **📋 Transactions & Export**.
   - Search by keyword, filter by category, expand line items, and click **📥 Export CSV** to download an itemized spreadsheet.

---

## ⚖️ Non-Financial Advice Disclaimer

SpendSight is an educational personal finance and expense-tracking application designed for students. It does not provide certified financial, accounting, legal, or tax advice. All computations, projections, and insight cards are generated for informational and planning purposes only.
