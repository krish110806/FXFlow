"""
FXFlow — Dashboard · Currency Explorer page.

Deep-dive instrument analysis for individual foreign exchange pairs
with customizable date intervals, moving averages, and range statistics.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fxflow.config import api_config
from fxflow.data_access import (
    get_exchange_rates,
    get_available_pairs,
    get_currency_map,
    fetch_live_rates,
)
from fxflow.pipeline.orchestrator import run_full_pipeline
from fxflow.dashboard.theme import (
    COLORS,
    SERIES_COLORS,
    apply_theme,
    render_header,
)


def render() -> None:
    """Render the Currency Explorer page."""
    render_header(
        title="Currency Explorer",
        subtitle="Individual currency pair surveillance, moving averages, and historical valuation bands",
        eyebrow="INSTRUMENT INTELLIGENCE",
        status_label="Pair Deep-Dive",
        status_badge_type="navy",
    )

    currency_map = get_currency_map()
    rates_df = get_exchange_rates()

    if rates_df.empty:
        st.info("⏳ Warehouse data not found. Fetching live rates from Frankfurter API …")
        with st.spinner("Fetching data …"):
            rates_df = fetch_live_rates(from_date=date.today() - timedelta(days=90))
        if rates_df.empty:
            st.error(
                "❌ No data available. Run the ingestion pipeline:\n\n"
                "```\npython -m fxflow.cli ingest --days 90\n```"
            )
            return

    # ── Instrument Selection Card ─────────────────────────────────────
    available_quotes = sorted(rates_df["quote_currency"].unique())
    available_bases = sorted(rates_df["base_currency"].unique())

    min_date_val = rates_df["rate_date"].min()
    max_date_val = rates_df["rate_date"].max()
    min_d = min_date_val.date() if hasattr(min_date_val, "date") else min_date_val
    max_d = max_date_val.date() if hasattr(max_date_val, "date") else max_date_val

    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom: 0.4rem;">
            <div style="font-family:'Newsreader', Georgia, serif; font-size:1.15rem; font-weight:600; color:#142B3B;">
                Instrument Parameters & Evaluation Window
            </div>
            <div style="font-size:0.75rem; color:#68766F; font-family:'IBM Plex Mono', monospace;">
                Source: Frankfurter API (ECB Reference Fixing)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5 = st.columns([1.1, 1.1, 1, 1, 0.9])
    with col1:
        base = st.selectbox(
            "Base Currency",
            available_bases,
            index=0,
            key="explorer_base",
        )
    with col2:
        quote = st.selectbox(
            "Target Quote Currency",
            available_quotes,
            index=available_quotes.index("EUR") if "EUR" in available_quotes else 0,
            key="explorer_quote",
        )
    with col3:
        from_d = st.date_input(
            "Evaluation From",
            value=max_d - timedelta(days=90),
            min_value=min_d,
            max_value=max_d,
            key="explorer_from",
        )
    with col4:
        to_d = st.date_input(
            "Evaluation To",
            value=max_d,
            min_value=min_d,
            max_value=max_d,
            key="explorer_to",
        )
    with col5:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        sync_btn = st.button("↻ Sync Rates", use_container_width=True, help="Safely fetch newest reference rates up to today via existing pipeline")

    if sync_btn:
        with st.spinner("Fetching latest exchange rate fixings from Frankfurter API..."):
            try:
                res = run_full_pipeline()
                if res.get("status") == "success":
                    st.success(f"✓ Synchronised {res.get('rows_fetched', 0)} rates. Warehouse is up to date.")
                else:
                    st.error(f"Sync error: {res.get('error', 'Execution interrupted')}")
                st.rerun()
            except Exception as e:
                st.error(f"Sync failed: {e}")

    # ── Filtered Data Selection ──────────────────────────────────────
    mask = (
        (rates_df["base_currency"] == base)
        & (rates_df["quote_currency"] == quote)
        & (rates_df["rate_date"] >= pd.Timestamp(from_d))
        & (rates_df["rate_date"] <= pd.Timestamp(to_d))
    )
    pair_df = rates_df[mask].sort_values("rate_date").reset_index(drop=True)

    if pair_df.empty:
        st.warning(f"No transactions recorded for {base}/{quote} in the specified interval.")
        return

    base_name = currency_map.get(base, base)
    quote_name = currency_map.get(quote, quote)

    # ── Summary Metrics Strip ────────────────────────────────────────
    latest_row = pair_df.iloc[-1]
    latest_rate = float(latest_row["rate"])
    latest_obs_date = latest_row["rate_date"]
    latest_obs_str = latest_obs_date.strftime("%b %d, %Y") if hasattr(latest_obs_date, "strftime") else str(latest_obs_date)

    first_rate = float(pair_df["rate"].iloc[0])
    pct_change = ((latest_rate - first_rate) / first_rate) * 100
    min_rate = float(pair_df["rate"].min())
    max_rate = float(pair_df["rate"].max())
    mean_rate = float(pair_df["rate"].mean())

    st.markdown(
        f"""
        <div style="margin-top: 0.75rem; margin-bottom: 1.25rem;">
            <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">
                <div style="font-family:'Newsreader', Georgia, serif; font-size:1.45rem; font-weight:600; color:#142B3B;">
                    {base}/{quote} · <span style="font-size:1rem; color:#68766F; font-weight:400;">{base_name} to {quote_name}</span>
                </div>
                <div style="font-family:'IBM Plex Mono', monospace; font-size:0.75rem; color:#68766F;">
                    {len(pair_df)} Observations ({from_d} → {to_d})
                </div>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 0.75rem; color: #68766F;">
                <span class="fx-badge fx-badge-teal">ECB Reference Fixing</span>
                <span>Observation Date: <strong style="color: #142B3B;">{latest_obs_str}</strong></span>
                <span>•</span>
                <span>Direction: <strong style="color: #142B3B;">1 {base} = {latest_rate:.4f} {quote}</strong></span>
                <span>•</span>
                <span style="color: #8C9DA8;">Daily official ECB published reference rate (not live streaming tick price)</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Latest Reference Rate",
        f"{latest_rate:.4f}",
        delta=f"As of {latest_obs_str}",
        delta_color="off",
        help=f"1 {base} = {latest_rate:.4f} {quote} as recorded by the European Central Bank on {latest_obs_str}.",
    )

    delta_label = f"{pct_change:+.2f}%"
    c2.metric(
        "Period Return",
        delta_label,
        delta=delta_label,
        help="Net percentage change over selected date range",
    )

    c3.metric(
        "Interval Low",
        f"{min_rate:.4f}",
        help="Lowest observed rate during window",
    )

    c4.metric(
        "Interval High",
        f"{max_rate:.4f}",
        help="Highest observed rate during window",
    )

    c5.metric(
        "Mean Valuation",
        f"{mean_rate:.4f}",
        help="Arithmetic mean exchange rate across selected observations",
    )

    st.markdown("<hr style='margin: 1.2rem 0;'>", unsafe_allow_html=True)

    # ── Interactive Chart ────────────────────────────────────────────
    fig = go.Figure()

    # Primary Spot Rate line
    fig.add_trace(
        go.Scatter(
            x=pair_df["rate_date"],
            y=pair_df["rate"],
            mode="lines",
            name=f"{base}/{quote} Spot",
            line=dict(color=COLORS["teal"], width=2.4),
            fill="tozeroy",
            fillcolor="rgba(40, 125, 107, 0.05)",
            hovertemplate=(
                f"<b>{base}/{quote} Spot</b><br>"
                "Date: %{x|%b %d, %Y}<br>"
                "Rate: <b>%{y:.4f}</b>"
                "<extra></extra>"
            ),
        )
    )

    # 20-Day Moving Average overlay
    if len(pair_df) >= 20:
        pair_copy = pair_df.copy()
        pair_copy["ma20"] = pair_copy["rate"].rolling(20).mean()
        fig.add_trace(
            go.Scatter(
                x=pair_copy["rate_date"],
                y=pair_copy["ma20"],
                mode="lines",
                name="20-Day Moving Avg",
                line=dict(color=COLORS["gold"], width=1.8, dash="dot"),
                hovertemplate="MA-20: <b>%{y:.4f}</b><extra></extra>",
            )
        )

    fig.update_layout(
        title=f"{base}/{quote} Exchange Rate Valuation & Moving Average",
        xaxis_title="Date",
        yaxis_title=f"Rate Value in {quote}",
        height=480,
        hovermode="x unified",
    )
    apply_theme(fig)

    st.plotly_chart(fig, width="stretch")

    # ── Raw Warehouse Ledger Table ───────────────────────────────────
    with st.expander("📋 Inspect Warehouse Records", expanded=False):
        disp = pair_df[["rate_date", "base_currency", "quote_currency", "rate"]].copy()
        disp["rate_date"] = disp["rate_date"].dt.strftime("%Y-%m-%d") if hasattr(disp["rate_date"].iloc[0], "strftime") else disp["rate_date"]
        disp.columns = ["Trade Date", "Base Currency", "Quote Currency", "Exchange Rate"]
        st.dataframe(disp, width="stretch", hide_index=True)
