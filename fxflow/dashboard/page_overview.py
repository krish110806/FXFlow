"""
FXFlow — Dashboard · Market Overview page.

Presents key currency exchange benchmarks, historical trends,
and market surveillance telemetry in an editorial finance layout.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fxflow.config import api_config
from fxflow.data_access import (
    get_exchange_rates,
    get_latest_rates,
    get_data_freshness,
    fetch_live_rates,
    get_currency_map,
)
from fxflow.dashboard.theme import (
    COLORS,
    SERIES_COLORS,
    apply_theme,
)

# Key global benchmark pairs to highlight
_KEY_PAIRS = [
    ("USD", "EUR"),
    ("USD", "GBP"),
    ("USD", "JPY"),
    ("USD", "CHF"),
    ("USD", "CAD"),
    ("USD", "AUD"),
]


def render() -> None:
    """Render the Market Overview page."""
    currency_map = get_currency_map()
    rates_df = get_exchange_rates()
    data_source = "local"

    if rates_df.empty:
        st.info(
            "📡 No local repository detected. Establishing connection to Frankfurter API …"
        )
        with st.spinner("Streaming benchmark rates …"):
            rates_df = fetch_live_rates(
                from_date=date.today() - timedelta(days=90),
            )
        if rates_df.empty:
            st.error(
                "❌ Live rate ingestion failed. Run the pipeline to populate the warehouse:\n\n"
                "```\npython -m fxflow.cli ingest --days 90\n```"
            )
            return
        data_source = "live"

    # Real data metrics for hero banner and summary strip
    unique_pairs_count = rates_df["quote_currency"].nunique() if not rates_df.empty else 0
    total_obs_count = len(rates_df) if not rates_df.empty else 0
    min_date = rates_df["rate_date"].min() if not rates_df.empty else None
    max_date = rates_df["rate_date"].max() if not rates_df.empty else None

    min_str = (
        min_date.strftime("%b %d, %Y")
        if hasattr(min_date, "strftime")
        else (str(min_date) if min_date else "—")
    )
    max_str = (
        max_date.strftime("%b %d, %Y")
        if hasattr(max_date, "strftime")
        else (str(max_date) if max_date else "Awaiting Data")
    )

    # ── 1. REQUIRED: HERO BANNER ─────────────────────────────────────
    hero_html = (
        '<div style="background-color: #142B3B; background-image: radial-gradient(circle at 92% 20%, rgba(40, 125, 107, 0.25) 0%, transparent 45%), radial-gradient(circle at 8% 80%, rgba(198, 165, 104, 0.15) 0%, transparent 40%), linear-gradient(135deg, rgba(20, 43, 59, 0.98) 0%, rgba(13, 29, 40, 0.99) 100%); border: 1px solid rgba(229, 222, 208, 0.22); border-radius: 14px; padding: 2rem 2.4rem; margin-bottom: 1.25rem; position: relative; overflow: hidden; box-shadow: 0 6px 24px rgba(20, 43, 59, 0.12);">'
        '<svg style="position: absolute; right: -50px; top: -60px; width: 440px; height: 440px; pointer-events: none; opacity: 0.14;" viewBox="0 0 400 400" fill="none">'
        '<circle cx="200" cy="200" r="185" stroke="#C6A568" stroke-width="1.5" stroke-dasharray="6 8"/>'
        '<circle cx="200" cy="200" r="145" stroke="#369B86" stroke-width="1.5"/>'
        '<circle cx="200" cy="200" r="105" stroke="#FFFCF5" stroke-width="1.2" stroke-dasharray="3 5"/>'
        '<circle cx="200" cy="200" r="65" stroke="#C6A568" stroke-width="1"/>'
        '</svg>'
        '<svg style="position: absolute; left: 22%; bottom: -90px; width: 300px; height: 300px; pointer-events: none; opacity: 0.08;" viewBox="0 0 300 300" fill="none">'
        '<circle cx="150" cy="150" r="130" stroke="#369B86" stroke-width="1.5" stroke-dasharray="5 7"/>'
        '<circle cx="150" cy="150" r="85" stroke="#C6A568" stroke-width="1"/>'
        '</svg>'
        '<div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 2rem; position: relative; z-index: 2;">'
        '<div style="flex: 1 1 540px; min-width: 290px;">'
        '<div style="display: inline-flex; align-items: center; gap: 8px; font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 700; color: #369B86; margin-bottom: 0.75rem;">'
        '<span style="width: 7px; height: 7px; border-radius: 50%; background: #369B86; display: inline-block; box-shadow: 0 0 8px #369B86;"></span>'
        'FOREIGN EXCHANGE INTELLIGENCE'
        '</div>'
        '<div style="font-family: \'Newsreader\', Georgia, serif; font-size: 2.35rem; font-weight: 600; line-height: 1.15; color: #FFFCF5; letter-spacing: -0.025em; margin-bottom: 0.85rem;">'
        'Decode currency movements.<br>'
        '<span style="color: #7FB7A5;">Trust every rate.</span>'
        '</div>'
        '<p style="font-size: 0.95rem; color: #B2C3CF; line-height: 1.6; max-width: 560px; margin-bottom: 1.6rem; font-weight: 400;">'
        'Explore currency trends, uncover unusual market movements, and understand the quality behind every exchange rate — all in one clear view.'
        '</p>'
        '<div style="display: flex; flex-wrap: wrap; gap: 1.6rem; align-items: center; padding-top: 1rem; border-top: 1px solid rgba(229, 222, 208, 0.15);">'
        '<div style="display: flex; align-items: center; gap: 10px;">'
        '<div style="width: 32px; height: 32px; border-radius: 6px; background: rgba(54, 155, 134, 0.18); border: 1px solid rgba(54, 155, 134, 0.3); display: flex; align-items: center; justify-content: center;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#369B86" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>'
        '</div>'
        '<div>'
        '<div style="font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: #8C9DA8; font-weight: 600;">PAIRS TRACKED</div>'
        f'<div style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.95rem; font-weight: 600; color: #FFFCF5;">{unique_pairs_count} Crosses</div>'
        '</div>'
        '</div>'
        '<div style="display: flex; align-items: center; gap: 10px;">'
        '<div style="width: 32px; height: 32px; border-radius: 6px; background: rgba(198, 165, 104, 0.18); border: 1px solid rgba(198, 165, 104, 0.3); display: flex; align-items: center; justify-content: center;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C6A568" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>'
        '</div>'
        '<div>'
        '<div style="font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: #8C9DA8; font-weight: 600;">OBSERVATIONS</div>'
        f'<div style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.95rem; font-weight: 600; color: #FFFCF5;">{total_obs_count:,} Rows</div>'
        '</div>'
        '</div>'
        '<div style="display: flex; align-items: center; gap: 10px;">'
        '<div style="width: 32px; height: 32px; border-radius: 6px; background: rgba(54, 155, 134, 0.18); border: 1px solid rgba(54, 155, 134, 0.3); display: flex; align-items: center; justify-content: center;">'
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#369B86" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>'
        '</div>'
        '<div>'
        '<div style="font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; color: #8C9DA8; font-weight: 600;">LATEST DATE</div>'
        f'<div style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.95rem; font-weight: 600; color: #FFFCF5;">{max_str}</div>'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
        '<div style="flex: 0 1 310px; min-width: 260px; background: #1D3A4F; border: 1px solid rgba(229, 222, 208, 0.2); border-radius: 12px; padding: 1.5rem 1.6rem; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.22); display: flex; flex-direction: column; justify-content: space-between;">'
        '<div>'
        '<div style="font-family: \'Newsreader\', Georgia, serif; font-size: 3.2rem; line-height: 0.6; color: #C6A568; opacity: 0.9; margin-bottom: 0.6rem;">“</div>'
        '<div style="font-family: \'Newsreader\', Georgia, serif; font-style: italic; font-size: 1.18rem; color: #FFFCF5; line-height: 1.45; letter-spacing: -0.01em;">'
        'Better decisions begin with data you can trust.'
        '</div>'
        '<div style="width: 36px; height: 3px; background: #287D6B; border-radius: 2px; margin-top: 0.9rem;"></div>'
        '</div>'
        '<div style="font-family: \'Plus Jakarta Sans\', sans-serif; font-size: 0.68rem; color: #8C9DA8; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 1.1rem; font-weight: 600;">'
        'FXFlow Benchmark Integrity'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # ── 2. COVERAGE SUMMARY STRIP ────────────────────────────────────
    active_crosses = rates_df["quote_currency"].nunique() if not rates_df.empty else 0
    total_records = len(rates_df) if not rates_df.empty else 0
    pricing_mode = "Local Warehouse (Validated)" if data_source == "local" else "Live Direct API"

    summary_html = (
        '<div style="display: flex; flex-wrap: wrap; gap: 1.5rem; background: #FFFCF5; border: 1px solid #E5DED0; border-radius: 8px; padding: 10px 18px; margin-bottom: 1.4rem; align-items: center; font-size: 0.8rem; color: #68766F; box-shadow: 0 1px 3px rgba(20, 43, 59, 0.02);">'
        f'<div><strong style="color:#142B3B;">Coverage Horizon:</strong> {min_str} — {max_str}</div>'
        f'<div style="border-left: 1px solid #E5DED0; padding-left: 1.25rem;"><strong style="color:#142B3B;">Total Warehouse Records:</strong> {total_records:,}</div>'
        f'<div style="border-left: 1px solid #E5DED0; padding-left: 1.25rem;"><strong style="color:#142B3B;">Active Currency Crosses:</strong> {active_crosses}</div>'
        f'<div style="border-left: 1px solid #E5DED0; padding-left: 1.25rem;"><strong style="color:#142B3B;">Pricing Mode:</strong> {pricing_mode}</div>'
        '</div>'
    )
    st.markdown(summary_html, unsafe_allow_html=True)

    # ── 3. PRIMARY FX BENCHMARKS (2x3 Grid) ──────────────────────────
    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:0.75rem;">
            <div>
                <span class="fx-eyebrow">GLOBAL BENCHMARK TELEMETRY</span>
                <div style="font-family:'Newsreader', Georgia, serif; font-size:1.35rem; font-weight:600; color:#142B3B;">
                    Primary FX Benchmarks
                </div>
            </div>
            <div style="font-size:0.75rem; color:#68766F; font-family:'IBM Plex Mono', monospace;">
                Spot rates relative to USD (1 USD = Quote)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_kpis(rates_df, currency_map)

    st.markdown("<hr style='margin: 1.6rem 0;'>", unsafe_allow_html=True)

    # ── 4. HISTORICAL TRAJECTORIES ───────────────────────────────────
    _render_trend_chart(rates_df, currency_map)


# =====================================================================
# KPI Grid Renderer (2 rows x 3 columns)
# =====================================================================

def _build_sparkline(
    dates: pd.Series,
    rates: pd.Series,
    delta_pct: Optional[float] = None,
) -> go.Figure:
    """Build a minimal, elegant Plotly sparkline for a benchmark card."""
    fig = go.Figure()
    if delta_pct is not None and delta_pct >= 0:
        line_color = COLORS["green"]
        fill_color = "rgba(30, 126, 90, 0.08)"
    elif delta_pct is not None and delta_pct < 0:
        line_color = COLORS["red"]
        fill_color = "rgba(194, 84, 71, 0.08)"
    else:
        line_color = COLORS["teal"]
        fill_color = "rgba(40, 125, 107, 0.08)"

    if not rates.empty:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=rates,
                mode="lines",
                line=dict(color=line_color, width=1.8),
                fill="tozeroy",
                fillcolor=fill_color,
                hoverinfo="none",
            )
        )
    fig.update_layout(
        margin=dict(l=0, r=0, t=2, b=2),
        height=48,
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _render_kpis(df: pd.DataFrame, cmap: Dict[str, str]) -> None:
    """Render distinctive wealth-management cards for benchmark pairs in a 2x3 grid."""
    max_date = df["rate_date"].max()
    latest_df = df[df["rate_date"] == max_date]

    # Find previous trading day for daily percentage delta
    unique_dates = sorted(df["rate_date"].unique())
    prev_date = unique_dates[-2] if len(unique_dates) >= 2 else None
    prev_df = df[df["rate_date"] == prev_date] if prev_date is not None else pd.DataFrame()

    # Split into 2 rows of 3 columns for balanced, un-cramped display
    row1_pairs = _KEY_PAIRS[:3]
    row2_pairs = _KEY_PAIRS[3:]

    for row_idx, pairs_batch in enumerate([row1_pairs, row2_pairs]):
        cols = st.columns(3)
        for col_idx, (base, quote) in enumerate(pairs_batch):
            row = latest_df[
                (latest_df["base_currency"] == base) & (latest_df["quote_currency"] == quote)
            ]
            with cols[col_idx]:
                with st.container(border=True):
                    quote_name = cmap.get(quote, quote)
                    clean_pair = f"{base}/{quote}"
                    clean_name = quote_name

                    if row.empty:
                        delta_html = '<span class="fx-badge fx-badge-navy" style="font-size:0.7rem; white-space:nowrap; flex-shrink:0;">—</span>'
                        st.markdown(
                            f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px; gap:8px;">'
                            f'<div style="min-width:0; overflow:hidden;">'
                            f'<div class="fx-pair-title">{clean_pair}</div>'
                            f'<div class="fx-pair-sub" title="{clean_name}">{clean_name} · 1 {base} = {quote}</div>'
                            f'</div>'
                            f'{delta_html}'
                            f'</div>'
                            f'<div class="fx-rate-display">—</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        rate = float(row["rate"].values[0])
                        delta_pct = None
                        if not prev_df.empty:
                            p_row = prev_df[
                                (prev_df["base_currency"] == base) & (prev_df["quote_currency"] == quote)
                            ]
                            if not p_row.empty:
                                prev_rate = float(p_row["rate"].values[0])
                                delta_pct = ((rate - prev_rate) / prev_rate) * 100

                        # Historical observation series for sparkline and range
                        pair_history = df[
                            (df["base_currency"] == base) & (df["quote_currency"] == quote)
                        ].sort_values("rate_date")
                        min_val = float(pair_history["rate"].min()) if not pair_history.empty else None
                        max_val = float(pair_history["rate"].max()) if not pair_history.empty else None

                        if delta_pct is not None:
                            if delta_pct >= 0:
                                delta_class = "fx-badge-emerald"
                                delta_symbol = "▲"
                                delta_text = f"+{delta_pct:.3f}%"
                            else:
                                delta_class = "fx-badge-terracotta"
                                delta_symbol = "▼"
                                delta_text = f"{delta_pct:.3f}%"
                            delta_html = (
                                f'<span class="fx-badge {delta_class}" '
                                f'style="font-family:\'IBM Plex Mono\', monospace; font-size:0.75rem; white-space:nowrap; flex-shrink:0; padding:2px 8px;">'
                                f'{delta_symbol} {delta_text}</span>'
                            )
                        else:
                            delta_html = '<span class="fx-badge fx-badge-navy" style="font-size:0.7rem; white-space:nowrap; flex-shrink:0;">—</span>'

                        # Card Header
                        st.markdown(
                            f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px; gap:8px;">'
                            f'<div style="min-width:0; overflow:hidden;">'
                            f'<div class="fx-pair-title">{clean_pair}</div>'
                            f'<div class="fx-pair-sub" title="{clean_name}">{clean_name} · 1 {base} = {quote}</div>'
                            f'</div>'
                            f'{delta_html}'
                            f'</div>'
                            f'<div class="fx-rate-display">{rate:.4f}</div>',
                            unsafe_allow_html=True,
                        )

                        # Plotly sparkline
                        spark_fig = _build_sparkline(
                            dates=pair_history["rate_date"],
                            rates=pair_history["rate"],
                            delta_pct=delta_pct,
                        )
                        st.plotly_chart(
                            spark_fig,
                            width="stretch",
                            config={"displayModeBar": False, "staticPlot": True},
                        )

                        # Range footer with real period low/high
                        if min_val is not None and max_val is not None:
                            st.markdown(
                                f'<div style="display:flex; justify-content:space-between; font-family:\'IBM Plex Mono\', monospace; '
                                f'font-size:0.7rem; color:#68766F; padding-top:6px; border-top:1px dashed #E5DED0;">'
                                f'<span>PERIOD LOW: <strong>{min_val:.4f}</strong></span>'
                                f'<span>HIGH: <strong>{max_val:.4f}</strong></span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )


# =====================================================================
# Trend Chart Renderer
# =====================================================================

def _render_trend_chart(df: pd.DataFrame, cmap: Dict[str, str]) -> None:
    """Render historical trend lines with institutional styling."""
    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:0.8rem;">
            <div>
                <span class="fx-eyebrow">HISTORICAL SURVEILLANCE</span>
                <div style="font-family:'Newsreader', Georgia, serif; font-size:1.35rem; font-weight:600; color:#142B3B;">
                    Exchange Rate Trajectories
                </div>
            </div>
            <div style="font-size:0.75rem; color:#68766F; font-family:'IBM Plex Mono', monospace;">
                Multi-Currency Time Series Overlay
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filter Controls
    col_period, col_pairs = st.columns([1, 2])
    with col_period:
        period = st.selectbox(
            "Evaluation Horizon",
            ["30 days", "90 days", "180 days", "1 year", "All"],
            index=1,
            key="overview_period",
        )
    with col_pairs:
        available_quotes = sorted(df["quote_currency"].unique())
        default_quotes = [q for q in ["EUR", "GBP", "JPY", "CAD"] if q in available_quotes]
        selected_quotes = st.multiselect(
            "Active Currency Crosses",
            available_quotes,
            default=default_quotes or available_quotes[:3],
            key="overview_quotes",
        )

    if not selected_quotes:
        st.warning("Select at least one currency cross to chart.")
        return

    # Date range slice
    max_date = df["rate_date"].max()
    period_map = {
        "30 days": 30,
        "90 days": 90,
        "180 days": 180,
        "1 year": 365,
        "All": None,
    }
    days = period_map.get(period)
    if days:
        cutoff = max_date - pd.Timedelta(days=days)
        plot_df = df[df["rate_date"] >= cutoff]
    else:
        plot_df = df

    fig = go.Figure()

    for idx, quote in enumerate(selected_quotes):
        series_data = plot_df[plot_df["quote_currency"] == quote].sort_values("rate_date")
        if series_data.empty:
            continue

        color = SERIES_COLORS[idx % len(SERIES_COLORS)]
        quote_name = cmap.get(quote, quote)

        fig.add_trace(
            go.Scatter(
                x=series_data["rate_date"],
                y=series_data["rate"],
                name=f"{api_config.base_currency}/{quote}",
                mode="lines",
                line=dict(color=color, width=2.2),
                hovertemplate=(
                    f"<b>{api_config.base_currency}/{quote}</b> ({quote_name})<br>"
                    "Date: %{x|%b %d, %Y}<br>"
                    "Rate: <b>%{y:.4f}</b>"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"Exchange Rate Dynamics · {period} Window",
        xaxis_title="Date",
        yaxis_title="Exchange Rate Value",
        height=480,
        hovermode="x unified",
    )
    apply_theme(fig)

    st.plotly_chart(fig, width="stretch")
