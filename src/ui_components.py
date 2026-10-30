"""UI components, theme styling, and Plotly visualizations for SpendSight.

Emerald, Charcoal, and Off-White design system tailored for student budgeting.
"""

from typing import Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Color Palette Constants
COLOR_EMERALD = "#10B981"
COLOR_EMERALD_DARK = "#059669"
COLOR_EMERALD_LIGHT = "#D1FAE5"
COLOR_CHARCOAL_DARK = "#0F172A"
COLOR_CHARCOAL_CARD = "#1E293B"
COLOR_CHARCOAL_TEXT = "#334155"
COLOR_OFFWHITE_BG = "#F8FAFC"
COLOR_WHITE = "#FFFFFF"
COLOR_AMBER = "#F59E0B"
COLOR_ROSE = "#F43F5E"
COLOR_CYAN = "#06B6D4"


def inject_custom_theme() -> None:
    """Inject modern emerald, charcoal, and off-white CSS styling into Streamlit."""
    st.markdown(
        f"""
        <style>
            /* Base container & typography */
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

            html, body, [class*="css"] {{
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            }}

            /* Top App Header Banner */
            .spendsight-header {{
                background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #064E3B 100%);
                padding: 1.6rem 2rem;
                border-radius: 16px;
                color: #FFFFFF;
                margin-bottom: 1.5rem;
                box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            .spendsight-header h1 {{
                font-size: 2rem;
                font-weight: 800;
                margin: 0;
                letter-spacing: -0.02em;
                color: #FFFFFF;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }}
            .spendsight-header p {{
                font-size: 0.95rem;
                color: #94A3B8;
                margin: 0.4rem 0 0 0;
            }}
            .spendsight-badge {{
                background-color: {COLOR_EMERALD};
                color: #FFFFFF;
                font-size: 0.75rem;
                font-weight: 700;
                padding: 0.2rem 0.65rem;
                border-radius: 9999px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}

            /* Card Containers */
            .ss-card {{
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                padding: 1.25rem 1.4rem;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
                margin-bottom: 1rem;
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }}
            .ss-card:hover {{
                box-shadow: 0 6px 16px rgba(16, 185, 129, 0.08);
                border-color: #CBD5E1;
            }}

            /* Metric Cards */
            .ss-metric-box {{
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                padding: 1.1rem 1.2rem;
                box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04);
                height: 100%;
            }}
            .ss-metric-title {{
                font-size: 0.8rem;
                font-weight: 600;
                color: #64748B;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                display: flex;
                align-items: center;
                gap: 0.4rem;
                margin-bottom: 0.4rem;
            }}
            .ss-metric-val {{
                font-size: 1.75rem;
                font-weight: 800;
                color: #0F172A;
                line-height: 1.2;
                margin-bottom: 0.3rem;
            }}
            .ss-metric-delta-pos {{
                color: #10B981;
                font-size: 0.82rem;
                font-weight: 600;
            }}
            .ss-metric-delta-neg {{
                color: #F43F5E;
                font-size: 0.82rem;
                font-weight: 600;
            }}
            .ss-metric-delta-neutral {{
                color: #64748B;
                font-size: 0.82rem;
                font-weight: 600;
            }}

            /* Insight / Tip Card */
            .ss-insight-card {{
                border-left: 4px solid {COLOR_EMERALD};
                background: #F0FDF4;
                padding: 1rem 1.2rem;
                border-radius: 10px;
                margin-bottom: 0.75rem;
                border-top: 1px solid #DCFCE7;
                border-right: 1px solid #DCFCE7;
                border-bottom: 1px solid #DCFCE7;
            }}
            .ss-insight-title {{
                font-weight: 700;
                color: #065F46;
                font-size: 0.95rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.3rem;
            }}
            .ss-insight-body {{
                color: #1F2937;
                font-size: 0.88rem;
                line-height: 1.45;
                margin: 0;
            }}

            /* Discrepancy Banner */
            .ss-discrepancy-box {{
                border-left: 4px solid #F59E0B;
                background: #FFFBEB;
                padding: 0.9rem 1.2rem;
                border-radius: 10px;
                margin: 0.8rem 0;
                border: 1px solid #FDE68A;
            }}
            .ss-discrepancy-title {{
                font-weight: 700;
                color: #92400E;
                font-size: 0.92rem;
            }}

            /* Confidence Badges */
            .ss-badge-high {{
                background-color: #DCFCE7;
                color: #15803D;
                padding: 0.15rem 0.5rem;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 700;
            }}
            .ss-badge-medium {{
                background-color: #FEF3C7;
                color: #B45309;
                padding: 0.15rem 0.5rem;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 700;
            }}
            .ss-badge-low {{
                background-color: #FEE2E2;
                color: #B91C1C;
                padding: 0.15rem 0.5rem;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 700;
            }}

            /* Progress Bar Container */
            .ss-progress-container {{
                background-color: #E2E8F0;
                border-radius: 9999px;
                height: 14px;
                overflow: hidden;
                margin: 0.5rem 0 0.2rem 0;
            }}
            .ss-progress-bar {{
                height: 100%;
                border-radius: 9999px;
                transition: width 0.3s ease;
            }}

            /* Disclaimer Box */
            .ss-disclaimer {{
                font-size: 0.75rem;
                color: #64748B;
                text-align: center;
                padding: 1.5rem 0;
                border-top: 1px solid #E2E8F0;
                margin-top: 2rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(
    title: str,
    value: str,
    subtext: str = "",
    delta: str = "",
    delta_type: str = "neutral",  # "pos", "neg", "neutral"
    icon: str = "📊",
) -> None:
    """Render a styled HTML metric box in Streamlit."""
    delta_class = "ss-metric-delta-neutral"
    if delta_type == "pos":
        delta_class = "ss-metric-delta-pos"
    elif delta_type == "neg":
        delta_class = "ss-metric-delta-neg"

    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""
    subtext_html = f'<div style="font-size: 0.78rem; color: #64748B; margin-top: 0.2rem;">{subtext}</div>' if subtext else ""

    st.markdown(
        f"""
        <div class="ss-metric-box">
            <div class="ss-metric-title">{icon} {title}</div>
            <div class="ss-metric-val">{value}</div>
            {delta_html}
            {subtext_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_budget_progress(total_spend: float, monthly_budget: float) -> None:
    """Render a visual student budget progress bar with status color shifts."""
    pct = (total_spend / monthly_budget * 100.0) if monthly_budget > 0 else 0.0
    pct_clamped = min(pct, 100.0)

    if pct < 75.0:
        bar_color = COLOR_EMERALD
        status_text = "🟢 Safe zone — great pacing"
        text_color = "#047857"
    elif pct <= 100.0:
        bar_color = COLOR_AMBER
        status_text = "🟡 Nearing monthly budget threshold"
        text_color = "#B45309"
    else:
        bar_color = COLOR_ROSE
        status_text = "🔴 Budget ceiling reached / exceeded"
        text_color = "#BE123C"

    st.markdown(
        f"""
        <div class="ss-card" style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div>
                    <span style="font-weight: 700; color: #0F172A; font-size: 1.05rem;">Monthly Budget Pace</span>
                    <span style="font-size: 0.85rem; color: {text_color}; font-weight: 600; margin-left: 0.6rem;">{status_text}</span>
                </div>
                <div style="font-weight: 800; font-size: 1.15rem; color: #0F172A;">
                    ${total_spend:,.2f} <span style="font-size: 0.85rem; font-weight: 500; color: #64748B;">/ ${monthly_budget:,.2f} ({pct:.1f}%)</span>
                </div>
            </div>
            <div class="ss-progress-container">
                <div class="ss-progress-bar" style="width: {pct_clamped}%; background-color: {bar_color};"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #94A3B8; margin-top: 0.35rem;">
                <span>$0.00</span>
                <span>50%</span>
                <span>${monthly_budget:,.2f} (Target)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_category_donut_chart(category_df: pd.DataFrame, total_spend: float) -> go.Figure:
    """Generate an emerald & charcoal themed Plotly donut chart."""
    df_filtered = category_df[category_df["total"] > 0]

    if df_filtered.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No expenses recorded yet",
            showarrow=False,
            font=dict(size=14, color="#64748B"),
        )
        fig.update_layout(
            height=320,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    fig = go.Figure(
        data=[
            go.Pie(
                labels=[f"{row['icon']} {row['category']}" for _, row in df_filtered.iterrows()],
                values=df_filtered["total"],
                hole=0.62,
                marker=dict(colors=df_filtered["color"].tolist(), line=dict(color="#FFFFFF", width=2)),
                textinfo="percent",
                textposition="inside",
                hovertemplate="<b>%{label}</b><br>Spent: $%{value:.2f}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )

    # Center spend label
    fig.update_layout(
        annotations=[
            dict(
                text=f"<span style='font-size:12px;color:#64748B;font-weight:600;'>TOTAL SPEND</span><br><b style='font-size:20px;color:#0F172A;'>${total_spend:,.2f}</b>",
                x=0.5,
                y=0.5,
                font=dict(size=16),
                showarrow=False,
            )
        ],
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=340,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def create_daily_trend_chart(trend_df: pd.DataFrame, monthly_budget: float) -> go.Figure:
    """Generate a combined daily spending bar and cumulative spend line chart."""
    fig = go.Figure()

    # Daily spending bars
    fig.add_trace(
        go.Bar(
            x=trend_df["day"],
            y=trend_df["daily_spend"],
            name="Daily Spend",
            marker=dict(color="#6EE7B7", opacity=0.85, line=dict(color="#059669", width=1)),
            hovertemplate="Day %{x}: $%{y:.2f}<extra></extra>",
        )
    )

    # Cumulative spending line
    fig.add_trace(
        go.Scatter(
            x=trend_df["day"],
            y=trend_df["cumulative_spend"],
            name="Cumulative Total",
            mode="lines+markers",
            line=dict(color="#0F172A", width=3),
            marker=dict(size=6, color="#059669"),
            hovertemplate="Cumulative (Day %{x}): $%{y:.2f}<extra></extra>",
        )
    )

    # Reference budget line
    if monthly_budget > 0:
        fig.add_hline(
            y=monthly_budget,
            line_dash="dot",
            line_color="#F43F5E",
            annotation_text=f"Monthly Target (${monthly_budget:.0f})",
            annotation_position="top left",
            annotation_font_color="#F43F5E",
        )

    fig.update_layout(
        height=340,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Day of Month",
            tickmode="linear",
            dtick=2,
            gridcolor="#E2E8F0",
            showline=True,
            linecolor="#CBD5E1",
        ),
        yaxis=dict(
            title="Amount ($)",
            gridcolor="#E2E8F0",
            showline=True,
            linecolor="#CBD5E1",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    return fig


def create_category_bar_chart(category_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart comparing category totals."""
    df_sorted = category_df[category_df["total"] > 0].sort_values(by="total", ascending=True)

    fig = go.Figure(
        go.Bar(
            x=df_sorted["total"],
            y=[f"{row['icon']} {row['category']}" for _, row in df_sorted.iterrows()],
            orientation="h",
            marker=dict(color=df_sorted["color"].tolist()),
            text=[f"${v:.2f}" for v in df_sorted["total"]],
            textposition="auto",
            hovertemplate="%{y}: $%{x:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        height=320,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Spend ($)", gridcolor="#E2E8F0"),
        yaxis=dict(gridcolor="#E2E8F0"),
    )
    return fig


def get_confidence_badge_html(level: str) -> str:
    """Return HTML badge for confidence scores."""
    clean = (level or "Medium").capitalize()
    cls = "ss-badge-medium"
    if clean == "High":
        cls = "ss-badge-high"
    elif clean == "Low":
        cls = "ss-badge-low"
    return f'<span class="{cls}">{clean} Confidence</span>'
