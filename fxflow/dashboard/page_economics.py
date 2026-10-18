"""
FXFlow — Dashboard · Economic Insights page.

Macro cross-currency relative performance, return correlations,
and period return ranking.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fxflow.config import api_config
from fxflow.data_access import (
    get_exchange_rates,
    get_currency_map,
    fetch_live_rates,
)
from fxflow.dashboard.theme import (
    COLORS,
    SERIES_COLORS,
    apply_theme,
    render_header,
)


def render() -> None:
    """Render the Economic Insights page."""
    render_header(
        title="Economic Insights",
        subtitle="Cross-asset relative strength, return correlation matrix, and valuation leaderboards",
        eyebrow="MACRO CROSS-ASSET SURVEILLANCE",
        status_label="Macro Surveillance",
        status_badge_type="teal",
    )

    currency_map = get_currency_map()
    rates_df = get_exchange_rates()

    if rates_df.empty:
        with st.spinner("Fetching live rates from Frankfurter API …"):
            rates_df = fetch_live_rates(from_date=date.today() - timedelta(days=180))
        if rates_df.empty:
            st.error("❌ No data available. Execute pipeline via CLI: `python -m fxflow.cli ingest`")
            return

    available_quotes = sorted(rates_df["quote_currency"].unique())

    # ── Parameters ───────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])
    with col1:
        default_quotes = [q for q in ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD"] if q in available_quotes]
        selected = st.multiselect(
            "Currencies to Compare",
            available_quotes,
            default=default_quotes[:6] or available_quotes[:4],
            key="econ_quotes",
        )
    with col2:
        period = st.selectbox(
            "Evaluation Horizon",
            ["30 days", "90 days", "180 days", "1 year", "All"],
            index=2,
            key="econ_period",
        )

    if not selected:
        st.warning("Select at least one currency cross to analyze.")
        return

    # Filter data
    max_date = rates_df["rate_date"].max()
    period_days = {"30 days": 30, "90 days": 90, "180 days": 180, "1 year": 365, "All": None}
    days = period_days.get(period)
    if days:
        cutoff = max_date - pd.Timedelta(days=days)
        filt_df = rates_df[rates_df["rate_date"] >= cutoff]
    else:
        filt_df = rates_df

    # ── 1. Relative Performance (Base 100 Normalised) ────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.3rem; font-weight:600; color:#142B3B; margin-top:0.6rem; margin-bottom:0.2rem;">
            Relative Currency Performance
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.8rem;">
            Rebased to 100.0 at horizon inception to compare percentage trajectory irrespective of spot base magnitude.
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig_norm = go.Figure()
    for idx, quote in enumerate(selected):
        qdf = filt_df[filt_df["quote_currency"] == quote].sort_values("rate_date")
        if qdf.empty:
            continue
        base_rate = float(qdf["rate"].iloc[0])
        normalised = (qdf["rate"] / base_rate) * 100.0
        color = SERIES_COLORS[idx % len(SERIES_COLORS)]
        label = f"{api_config.base_currency}/{quote}"

        fig_norm.add_trace(
            go.Scatter(
                x=qdf["rate_date"],
                y=normalised,
                name=label,
                mode="lines",
                line=dict(color=color, width=2.2),
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "Date: %{x|%b %d, %Y}<br>"
                    "Indexed Level: <b>%{y:.2f}</b>"
                    "<extra></extra>"
                ),
            )
        )

    fig_norm.add_hline(
        y=100.0,
        line_dash="dot",
        line_color=COLORS["border_dark"],
        annotation_text="Base 100 Par",
        annotation_font_color=COLORS["slate"],
        annotation_font_size=10,
    )
    fig_norm.update_layout(
        title=f"Indexed Valuation Path (Base 100 = {period} Inception)",
        xaxis_title="Date",
        yaxis_title="Normalized Index Level",
        height=460,
        hovermode="x unified",
    )
    apply_theme(fig_norm)
    st.plotly_chart(fig_norm, width="stretch")

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # ── 2. Return Correlations Matrix ────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.3rem; font-weight:600; color:#142B3B; margin-bottom:0.2rem;">
            Cross-Asset Return Correlation Matrix
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.8rem;">
            Pearson pairwise correlation coefficient of daily percentage returns.
        </div>
        """,
        unsafe_allow_html=True,
    )

    returns_dict: dict[str, pd.Series] = {}
    for quote in selected:
        qdf = filt_df[filt_df["quote_currency"] == quote].sort_values("rate_date")
        if len(qdf) < 5:
            continue
        rets = qdf.set_index("rate_date")["rate"].pct_change().dropna()
        returns_dict[f"{api_config.base_currency}/{quote}"] = rets

    if len(returns_dict) >= 2:
        returns_df = pd.DataFrame(returns_dict).dropna()
        corr = returns_df.corr()

        # Tailored financial divergence heatmap: Terracotta (-1) -> Ivory (0) -> Deep Teal (+1)
        colorscale = [
            [0.0, COLORS["red"]],
            [0.5, COLORS["surface_card"]],
            [1.0, COLORS["teal"]],
        ]

        fig_corr = go.Figure(
            data=go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale=colorscale,
                zmin=-1.0,
                zmax=1.0,
                text=corr.values.round(3),
                texttemplate="%{text:.3f}",
                textfont=dict(family="'IBM Plex Mono', monospace", size=12, color=COLORS["navy"]),
                hovertemplate="%{x} vs %{y}<br>Pearson Correlation: <b>%{z:.3f}</b><extra></extra>",
            )
        )
        fig_corr.update_layout(
            title="Pearson Correlation Heatmap",
            height=430,
            xaxis=dict(side="bottom"),
        )
        apply_theme(fig_corr)
        st.plotly_chart(fig_corr, width="stretch")
    else:
        st.info("At least 2 currencies with overlapping observation dates are required for correlation analysis.")

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # ── 3. Period Return Ranking Leaderboard ──────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.3rem; font-weight:600; color:#142B3B; margin-bottom:0.2rem;">
            Period Performance Ranking
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.8rem;">
            Net percentage change over the evaluation horizon.
        </div>
        """,
        unsafe_allow_html=True,
    )

    changes = []
    for quote in selected:
        qdf = filt_df[filt_df["quote_currency"] == quote].sort_values("rate_date")
        if len(qdf) < 2:
            continue
        first_r = float(qdf["rate"].iloc[0])
        last_r = float(qdf["rate"].iloc[-1])
        net_pct = ((last_r - first_r) / first_r) * 100.0
        changes.append({
            "Cross": f"{api_config.base_currency}/{quote}",
            "Currency": currency_map.get(quote, quote),
            "Start Rate": round(first_r, 4),
            "End Rate": round(last_r, 4),
            "Net Change (%)": round(net_pct, 3),
        })

    if changes:
        change_df = pd.DataFrame(changes).sort_values("Net Change (%)", ascending=True)

        fig_bar = go.Figure()
        bar_colors = [
            COLORS["green"] if v >= 0 else COLORS["red"]
            for v in change_df["Net Change (%)"]
        ]
        fig_bar.add_trace(
            go.Bar(
                x=change_df["Net Change (%)"],
                y=change_df["Cross"],
                orientation="h",
                marker_color=bar_colors,
                text=[f"{v:+.2f}%" for v in change_df["Net Change (%)"]],
                textposition="outside",
                hovertemplate="%{y}<br>Return: <b>%{x:.3f}%</b><extra></extra>",
            )
        )
        fig_bar.update_layout(
            title=f"Relative Performance Delta over {period}",
            xaxis_title="Percentage Change (%)",
            yaxis_title="",
            height=max(280, len(selected) * 44),
        )
        apply_theme(fig_bar)
        st.plotly_chart(fig_bar, width="stretch")

        with st.expander("📋 Detailed Performance Breakdown", expanded=False):
            disp_change = pd.DataFrame(changes).sort_values("Net Change (%)", ascending=False)
            st.dataframe(disp_change, width="stretch", hide_index=True)
