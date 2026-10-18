"""
FXFlow — Dashboard · Volatility Lab page.

Quantitative risk analytics: daily return variance, rolling volatility
trajectories, and cross-currency risk ranking.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from fxflow.config import api_config, pipeline_config
from fxflow.data_access import (
    get_analytics,
    get_exchange_rates,
    get_currency_map,
    fetch_live_rates,
)
from fxflow.pipeline.analytics import compute_analytics
from fxflow.dashboard.theme import (
    COLORS,
    SERIES_COLORS,
    apply_theme,
    render_header,
)


def render() -> None:
    """Render the Volatility Lab page."""
    render_header(
        title="Volatility Lab",
        subtitle="Quantitative dispersion analysis, daily returns variance, and rolling risk bands",
        eyebrow="RISK ANALYTICS & VOLATILITY",
        status_label="Quantitative Engine",
        status_badge_type="gold",
    )

    currency_map = get_currency_map()

    # ── Load Analytics ────────────────────────────────────────────────
    analytics_df = get_analytics()

    if analytics_df.empty:
        rates_df = get_exchange_rates()
        if rates_df.empty:
            st.info("Streaming rates from Frankfurter API to compute quantitative risk metrics …")
            with st.spinner("Fetching data …"):
                rates_df = fetch_live_rates(from_date=date.today() - timedelta(days=180))
            if rates_df.empty:
                st.error("❌ No data available. Execute pipeline via CLI: `python -m fxflow.cli ingest`")
                return
        with st.spinner("Computing variance and rolling risk …"):
            analytics_df = compute_analytics(rates_df)

    if analytics_df.empty:
        st.warning("Insufficient transaction data to compute volatility distributions.")
        return

    # ── Control Parameters ───────────────────────────────────────────
    available_quotes = sorted(analytics_df["quote_currency"].unique())

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        default_quotes = [q for q in ["EUR", "GBP", "JPY", "CAD"] if q in available_quotes]
        selected = st.multiselect(
            "Selected Currency Crosses",
            available_quotes,
            default=default_quotes[:3] or available_quotes[:2],
            key="vol_quotes",
        )
    with col2:
        window = st.number_input(
            "Rolling Window (Trading Days)",
            min_value=5,
            max_value=90,
            value=int(pipeline_config.volatility_window),
            step=5,
            key="vol_window",
        )
    with col3:
        period = st.selectbox(
            "Observation Window",
            ["90 days", "180 days", "1 year", "All"],
            index=1,
            key="vol_period",
        )

    if not selected:
        st.warning("Select at least one currency cross to evaluate.")
        return

    # Dynamic recomputation if user modifies window size
    if window != pipeline_config.volatility_window:
        rates_df = get_exchange_rates()
        if rates_df.empty:
            rates_df = fetch_live_rates(from_date=date.today() - timedelta(days=365))
        analytics_df = compute_analytics(rates_df, window=window)

    # Date range filter
    max_date = analytics_df["rate_date"].max()
    period_days = {"90 days": 90, "180 days": 180, "1 year": 365, "All": None}
    days = period_days.get(period)
    if days:
        cutoff = max_date - pd.Timedelta(days=days)
        filt_df = analytics_df[analytics_df["rate_date"] >= cutoff]
    else:
        filt_df = analytics_df

    # ── Volatility Executive Cards ───────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem; font-weight:600; color:#142B3B; margin-top:0.6rem; margin-bottom:0.6rem;">
            Current Realized Volatility
        </div>
        """,
        unsafe_allow_html=True,
    )

    vol_cols = st.columns(len(selected))
    for i, quote in enumerate(selected):
        qdf = filt_df[filt_df["quote_currency"] == quote]
        with vol_cols[i]:
            if qdf.empty or qdf["rolling_volatility"].isna().all():
                st.metric(
                    f"{api_config.base_currency}/{quote}",
                    "—",
                    help="Insufficient observations for window",
                )
            else:
                curr_vol = float(qdf["rolling_volatility"].dropna().iloc[-1])
                avg_vol = float(qdf["rolling_volatility"].mean())
                delta = curr_vol - avg_vol

                delta_str = f"{delta:+.3f}% vs avg"
                st.metric(
                    f"{api_config.base_currency}/{quote}",
                    f"{curr_vol:.3f}%",
                    delta=delta_str,
                    delta_color="inverse",
                    help=f"{window}-day standard deviation of daily logarithmic returns",
                )

    st.markdown("<hr style='margin: 1.4rem 0;'>", unsafe_allow_html=True)

    # ── Dual-Subplot Visualisation: Daily Returns + Rolling Vol ──────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem; font-weight:600; color:#142B3B; margin-bottom:0.5rem;">
            Return Dispersion & Volatility Trajectories
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.45, 0.55],
        subplot_titles=("Daily Return Dynamics (%)", f"{window}-Day Rolling Standard Deviation (%)"),
    )

    for idx, quote in enumerate(selected):
        qdf = filt_df[filt_df["quote_currency"] == quote].sort_values("rate_date")
        if qdf.empty:
            continue

        color = SERIES_COLORS[idx % len(SERIES_COLORS)]
        label = f"{api_config.base_currency}/{quote}"

        # Subplot 1: Daily % Returns (Bars)
        fig.add_trace(
            go.Bar(
                x=qdf["rate_date"],
                y=qdf["daily_pct_change"],
                name=f"{label} Return",
                marker_color=color,
                opacity=0.65,
                hovertemplate=f"<b>{label}</b><br>Date: %{{x|%b %d}}<br>Return: <b>%{{y:.3f}}%</b><extra></extra>",
                showlegend=True,
            ),
            row=1,
            col=1,
        )

        # Subplot 2: Rolling Volatility (Lines)
        fig.add_trace(
            go.Scatter(
                x=qdf["rate_date"],
                y=qdf["rolling_volatility"],
                name=f"{label} {window}D Vol",
                mode="lines",
                line=dict(color=color, width=2.2),
                hovertemplate=f"<b>{label}</b><br>Date: %{{x|%b %d}}<br>Volatility: <b>%{{y:.3f}}%</b><extra></extra>",
                showlegend=True,
            ),
            row=2,
            col=1,
        )

    fig.update_yaxes(title_text="Return (%)", row=1, col=1)
    fig.update_yaxes(title_text="Volatility (%)", row=2, col=1)
    fig.update_xaxes(title_text="Trading Date", row=2, col=1)
    fig.update_layout(
        height=620,
        hovermode="x unified",
        barmode="group",
    )
    apply_theme(fig)

    st.plotly_chart(fig, width="stretch")

    # ── Volatility Ranking Matrix ────────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem; font-weight:600; color:#142B3B; margin-top:1.2rem; margin-bottom:0.5rem;">
            Cross-Currency Risk Matrix
        </div>
        """,
        unsafe_allow_html=True,
    )

    ranking_rows = []
    for quote in available_quotes:
        qdf = filt_df[filt_df["quote_currency"] == quote]
        vol_s = qdf["rolling_volatility"].dropna()
        if vol_s.empty:
            continue
        c_vol = float(vol_s.iloc[-1])
        a_vol = float(vol_s.mean())
        m_vol = float(vol_s.max())
        l_vol = float(vol_s.min())

        # Risk Classification
        if c_vol < 0.4:
            regime = "Low Dispersion"
        elif c_vol < 0.8:
            regime = "Moderate Dispersion"
        else:
            regime = "Elevated Risk"

        ranking_rows.append({
            "Currency Cross": f"{api_config.base_currency}/{quote}",
            "Full Currency Name": currency_map.get(quote, quote),
            "Current Volatility (%)": round(c_vol, 4),
            "Mean Window Vol (%)": round(a_vol, 4),
            "Peak Volatility (%)": round(m_vol, 4),
            "Trough Volatility (%)": round(l_vol, 4),
            "Risk Regime": regime,
        })

    if ranking_rows:
        rank_df = pd.DataFrame(ranking_rows).sort_values("Current Volatility (%)", ascending=False)
        st.dataframe(rank_df, width="stretch", hide_index=True)
