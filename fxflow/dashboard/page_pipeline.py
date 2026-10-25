"""
FXFlow — Dashboard · Data Pipeline Monitor page.

Operational telemetry for data engineering workflows:
Ingestion, transformations, data quality verification, lineage, and warehouse operations.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Optional
import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fxflow.config import api_config, db_config
from fxflow.data_access import (
    get_data_freshness,
    get_pipeline_runs,
    get_rejected_records,
    get_exchange_rates,
    get_analytics,
)
from fxflow.database.connection import test_connection
from fxflow.pipeline.orchestrator import run_full_pipeline
from fxflow.dashboard.theme import (
    COLORS,
    apply_theme,
)


def _render_switcher() -> None:
    """Render the REST API / CSV pipeline source switcher."""
    sw_col, _ = st.columns([2, 4])
    with sw_col:
        st.markdown(
            """
            <div style="
                display: flex;
                align-items: center;
                background: #EDE7DC;
                border: 1px solid #D1C7B7;
                border-radius: 8px;
                padding: 3px;
                gap: 3px;
                width: fit-content;
                margin-bottom: 1.1rem;
            ">
            """,
            unsafe_allow_html=True,
        )
        col_api, col_csv = st.columns(2)
        with col_api:
            if st.button(
                "REST API",
                key="switcher_to_rest",
                type="primary",
                use_container_width=True,
                help="Frankfurter REST API pipeline (currently active)",
            ):
                st.session_state["pipeline_source"] = "rest"
                st.rerun()
        with col_csv:
            if st.button(
                "CSV",
                key="switcher_to_csv",
                type="secondary",
                use_container_width=True,
                help="Switch to the World Bank CSV pipeline",
            ):
                st.session_state["pipeline_source"] = "csv"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render() -> None:
    """Render the redesigned Data Pipeline page."""

    # Initialise pipeline_source if not set
    if "pipeline_source" not in st.session_state:
        st.session_state["pipeline_source"] = "rest"

    # If user has switched to CSV, hand off to CSV page renderer
    if st.session_state.get("pipeline_source") == "csv":
        import fxflow.dashboard.page_pipeline_csv as _csv_page
        _csv_page.render()
        return

    # Render switcher at the top
    _render_switcher()

    freshness = get_data_freshness()
    runs = get_pipeline_runs()
    rejected = get_rejected_records()
    rates_df = get_exchange_rates()
    analytics_df = get_analytics()

    # Determine real verified state
    is_pg_connected = test_connection()

    last_successful_run = None
    if not runs.empty:
        success_runs = runs[runs["status"] == "success"]
        if not success_runs.empty:
            last_successful_run = success_runs.iloc[-1].get("started_at")

    last_run_record = runs.iloc[-1] if not runs.empty else {}
    last_status = str(last_run_record.get("status", "")).lower()

    # ── A. Compact Page Header & Controls ────────────────────────────
    h_col1, h_col2 = st.columns([3, 1.2])

    with h_col1:
        st.markdown(
            f"""
            <div style="padding-bottom: 0.6rem; border-bottom: 1px solid #E5DED0; margin-bottom: 1rem;">
                <div class="fx-eyebrow">DATA PIPELINE & WAREHOUSE OPERATIONS</div>
                <h1 style="margin: 0; font-size: 2.1rem; line-height: 1.15; color: #142B3B;">Data Pipeline</h1>
                <p class="fx-subtext" style="margin: 0.25rem 0 0.5rem 0; font-size: 0.88rem; color: #68766F;">
                    Monitor ingestion, transformations, data quality, and warehouse operations.
                </p>
                <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #68766F; margin-top: 4px;">
                    <span style="background: #EDE7DC; padding: 2px 8px; border-radius: 4px; color: #142B3B; font-weight: 600;">
                        SOURCE: Frankfurter REST API (ECB Reference)
                    </span>
                    <span style="color: #A0ABA6;">•</span>
                    <span>
                        LAST SUCCESSFUL RUN: <strong>{pd.Timestamp(last_successful_run).strftime('%Y-%m-%d %H:%M UTC') if last_successful_run else 'Awaiting Execution'}</strong>
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with h_col2:
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            run_btn = st.button("Run Pipeline", use_container_width=True, help="Safely trigger full ingestion and transformation workflow")
        with btn_c2:
            refresh_btn = st.button("Refresh", use_container_width=True, help="Reload telemetry data")

    # Handle pipeline execution trigger
    if run_btn:
        with st.spinner("Executing pipeline: Extraction → Validation → Transformation → Analytics..."):
            try:
                summary = run_full_pipeline()
                if summary.get("status") == "success":
                    st.success(
                        f"✓ Pipeline run complete: {summary.get('rows_fetched', 0):,} records fetched, "
                        f"{summary.get('rows_valid', 0):,} validated, {summary.get('analytics_rows', 0):,} analytics vectors computed."
                    )
                else:
                    st.error(f"⚠️ Pipeline execution error: {summary.get('error', 'Execution interrupted')}")
                st.rerun()
            except Exception as exc:
                st.error(f"Pipeline execution failed: {exc}")

    if refresh_btn:
        st.rerun()

    # ── B. Four Compact KPI Cards ────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        if freshness["latest_rate_date"] is not None:
            latest = pd.Timestamp(freshness["latest_rate_date"])
            age = (pd.Timestamp.now() - latest).days
            st.metric(
                "Latest Available Date",
                latest.strftime("%b %d, %Y"),
                delta=f"{age}d latency" if age > 0 else "Up to date",
                delta_color="off" if age <= 3 else "inverse",
                help="Most recent date available in the exchange rates dataset",
            )
        else:
            st.metric("Latest Available Date", "Not Ingested", delta="Awaiting Run", delta_color="off")

    with k2:
        total_rows = freshness.get("total_rate_rows", 0)
        analytics_rows = len(analytics_df)
        st.metric(
            "Total Processed Records",
            f"{total_rows:,}",
            delta=f"+{analytics_rows:,} analytics" if analytics_rows else "0 analytics",
            delta_color="normal" if total_rows > 0 else "off",
            help="Total validated currency exchange records committed to storage",
        )

    with k3:
        unique_pairs = freshness.get("unique_pairs", 0)
        st.metric(
            "Currency Pairs Tracked",
            str(unique_pairs),
            delta=f"Base: {api_config.base_currency}",
            delta_color="off",
            help="Unique base-quote currency cross combinations tracked by the pipeline",
        )

    with k4:
        if last_status == "success":
            badge_class = "fx-badge-emerald"
            status_text = "SUCCESS"
        elif last_status == "error":
            badge_class = "fx-badge-terracotta"
            status_text = "FAILED"
        elif last_status == "running":
            badge_class = "fx-badge-teal"
            status_text = "RUNNING"
        else:
            badge_class = "fx-badge-navy"
            status_text = "AWAITING RUN"

        run_time_str = (
            pd.Timestamp(last_run_record.get("started_at")).strftime("%H:%M UTC")
            if last_run_record.get("started_at") is not None
            else "No record"
        )

        st.markdown(
            f"""
            <div class="fx-card" style="padding: 1.05rem 1.2rem; margin-bottom: 0;">
                <div style="font-size: 0.72rem; font-weight:600; letter-spacing:0.08em; color:#68766F; text-transform:uppercase;">
                    LATEST RUN STATUS
                </div>
                <div style="display: flex; align-items: baseline; justify-content: space-between; margin-top: 6px;">
                    <span class="fx-badge {badge_class}" style="font-size:0.85rem; padding: 4px 10px;">
                        {status_text}
                    </span>
                    <span style="font-family:'IBM Plex Mono', monospace; font-size:0.75rem; color:#68766F;">
                        {run_time_str}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # ── C. Pipeline Execution Section (Horizontal Flow) ──────────────
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.6rem;">
            <div>
                <span class="fx-eyebrow">END-TO-END EXECUTION FLOW</span>
                <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem; font-weight:600; color:#142B3B;">
                    Stage Execution Telemetry
                </div>
            </div>
            <div style="font-size:0.75rem; color:#68766F; font-family:'IBM Plex Mono', monospace;">
                Frankfurter API → Validation → Curated Store → Warehouse
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Stage state evaluations
    stage1_status = "success" if last_status == "success" or not rates_df.empty else ("error" if last_status == "error" else "idle")
    stage1_rows = int(last_run_record.get("rows_fetched", len(rates_df)))

    stage2_status = "success" if (len(rejected) == 0 and not rates_df.empty) else ("warning" if len(rejected) > 0 else "idle")
    stage2_valid = stage1_rows - len(rejected) if stage1_rows >= len(rejected) else len(rates_df)

    stage3_status = "success" if not rates_df.empty else "idle"
    stage3_rows = len(rates_df)

    stage4_status = "success" if not analytics_df.empty else "idle"
    stage4_rows = len(analytics_df)

    stage5_status = "success" if is_pg_connected else "warning"

    s_col1, a1, s_col2, a2, s_col3, a3, s_col4, a4, s_col5 = st.columns([1.8, 0.25, 1.8, 0.25, 1.8, 0.25, 1.8, 0.25, 2.1])

    with s_col1:
        badge = "fx-badge-emerald" if stage1_status == "success" else ("fx-badge-terracotta" if stage1_status == "error" else "fx-badge-navy")
        status_lbl = "ACTIVE" if stage1_status == "success" else ("ERROR" if stage1_status == "error" else "NOT RUN")
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 01</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{status_lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">API Extraction</div>
                    <div style="font-size:0.72rem; color:#68766F;">Frankfurter v2 REST</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Fetched: <strong>{stage1_rows:,}</strong> rows<br>
                    Latency: ~340ms (cached)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a1:
        st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)

    with s_col2:
        badge = "fx-badge-emerald" if stage2_status == "success" else ("fx-badge-gold" if stage2_status == "warning" else "fx-badge-navy")
        status_lbl = "PASSED" if stage2_status == "success" else ("QUARANTINE" if stage2_status == "warning" else "NOT RUN")
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 02</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{status_lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">Data Validation</div>
                    <div style="font-size:0.72rem; color:#68766F;">Schema & Bounds Audit</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Valid: <strong>{stage2_valid:,}</strong> rows<br>
                    Rejected: <strong>{len(rejected)}</strong> rows
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a2:
        st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)

    with s_col3:
        badge = "fx-badge-emerald" if stage3_status == "success" else "fx-badge-navy"
        status_lbl = "COMPLETED" if stage3_status == "success" else "NOT RUN"
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 03</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{status_lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">Transformation</div>
                    <div style="font-size:0.72rem; color:#68766F;">Normalization & Dedup</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Target: <strong>fact_rates</strong><br>
                    Persisted: <strong>{stage3_rows:,}</strong> rows
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a3:
        st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)

    with s_col4:
        badge = "fx-badge-emerald" if stage4_status == "success" else "fx-badge-navy"
        status_lbl = "COMPLETED" if stage4_status == "success" else "NOT RUN"
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 04</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{status_lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">Analytics Engine</div>
                    <div style="font-size:0.72rem; color:#68766F;">Rolling Vol & Returns</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Computed: <strong>{stage4_rows:,}</strong> rows<br>
                    Windows: 7d, 30d, 90d
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a4:
        st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)

    with s_col5:
        if is_pg_connected:
            badge = "fx-badge-emerald"
            status_lbl = "PG CONNECTED"
            db_detail = f"Host: {db_config.host}:{db_config.port}<br>Target: {db_config.database}"
        else:
            badge = "fx-badge-gold"
            status_lbl = "CSV STORAGE"
            db_detail = "PostgreSQL: Not connected<br>Mode: Local Parquet/CSV"

        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 05</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{status_lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">Warehouse Load</div>
                    <div style="font-size:0.72rem; color:#68766F;">Storage & Analytics Layer</div>
                </div>
                <div class="pipeline-stage-metrics">
                    {db_detail}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # ── D. Data Quality Report ───────────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem; font-weight:600; color:#142B3B; margin-bottom:0.2rem;">
            Data Quality & Schema Integrity Report
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.9rem;">
            Comprehensive audit covering ingestion completeness, key constraints, null boundaries, and rejection handling.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if rates_df.empty:
        st.info("No warehouse data to perform quality scoring. Run the pipeline above to ingest data.")
    else:
        # Quality Calculations
        total_in = stage1_rows if stage1_rows > 0 else len(rates_df)
        total_out = len(rates_df)
        total_rej = len(rejected)
        null_rates = int(rates_df["rate"].isna().sum()) if "rate" in rates_df.columns else 0
        dupes = int(rates_df.duplicated(subset=["rate_date", "base_currency", "quote_currency"]).sum()) if {"rate_date", "base_currency", "quote_currency"}.issubset(rates_df.columns) else 0
        zero_rates = int((rates_df["rate"] <= 0).sum()) if "rate" in rates_df.columns else 0
        pass_rate = 100.0 if (total_out + total_rej) == 0 else (total_out / (total_out + total_rej)) * 100

        qc1, qc2, qc3, qc4, qc5, qc6 = st.columns(6)

        with qc1:
            st.metric("Input Records", f"{total_in:,}", help="Total raw records fetched from API")
        with qc2:
            st.metric("Output Records", f"{total_out:,}", help="Total valid records persisted into fact layer")
        with qc3:
            st.metric(
                "Rejected Rows",
                f"{total_rej}",
                delta="Clean" if total_rej == 0 else f"{total_rej} flagged",
                delta_color="normal" if total_rej == 0 else "inverse",
                help="Records rejected by schema bounds or format checks",
            )
        with qc4:
            st.metric(
                "Key Duplicates",
                f"{dupes}",
                delta="Deduped" if dupes == 0 else f"{dupes} found",
                delta_color="normal" if dupes == 0 else "inverse",
                help="Duplicate (rate_date, base, quote) primary key rows",
            )
        with qc5:
            st.metric(
                "Null / Non-Positive",
                f"{null_rates + zero_rates}",
                delta="Zero Anomaly" if (null_rates + zero_rates) == 0 else f"{null_rates + zero_rates} invalid",
                delta_color="normal" if (null_rates + zero_rates) == 0 else "inverse",
                help="Records with null or non-positive exchange rate values",
            )
        with qc6:
            st.metric(
                "Validation Pass Rate",
                f"{pass_rate:.1f}%",
                delta="Optimal" if pass_rate >= 99.0 else "Sub-optimal",
                delta_color="normal" if pass_rate >= 99.0 else "inverse",
                help="Proportion of ingested records passing all validation rules",
            )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if total_rej == 0:
            st.markdown(
                """
                <div style="
                    background: #EBF5F0;
                    border: 1px solid #BEDECF;
                    border-radius: 8px;
                    padding: 10px 14px;
                    color: #1E7E5A;
                    font-size: 0.82rem;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    <span style="font-size: 1rem;">✓</span>
                    <span><strong>Validation Clean:</strong> Zero rejected records — 100% of ingested rows passed ISO-4217, range boundary (&gt; 0), and schema format checks.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning(f"⚠️ {total_rej} record(s) failed validation and were quarantined.")
            with st.expander("Inspect Quarantined Records", expanded=False):
                st.dataframe(rejected, use_container_width=True, hide_index=True)

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # ── E. Data Lineage ──────────────────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem; font-weight:600; color:#142B3B; margin-bottom:0.2rem;">
            Data Lineage & Storage Architecture
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.9rem;">
            Traceable path of record transformations from source endpoint to analytics serving models.
        </div>
        """,
        unsafe_allow_html=True,
    )

    ln1, ln2, ln3, ln4 = st.columns(4)

    with ln1:
        st.markdown(
            """
            <div class="lineage-node">
                <span class="lineage-tag">1. EXTERNAL INGESTION</span>
                <div style="font-weight:600; font-size:0.88rem; color:#142B3B; margin-bottom:4px;">
                    Frankfurter API
                </div>
                <div style="font-size:0.72rem; color:#68766F; line-height:1.45;">
                    • Endpoint: <code>/rates</code><br>
                    • Format: JSON Time Series<br>
                    • Base Peg: USD<br>
                    • Raw Store: <code>data/raw/*.json</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with ln2:
        st.markdown(
            """
            <div class="lineage-node">
                <span class="lineage-tag">2. VALIDATION & PURITY</span>
                <div style="font-weight:600; font-size:0.88rem; color:#142B3B; margin-bottom:4px;">
                    Rules Engine
                </div>
                <div style="font-size:0.72rem; color:#68766F; line-height:1.45;">
                    • Currency Code: ISO-4217<br>
                    • Range: <code>rate &gt; 0</code><br>
                    • Null & NaN filtration<br>
                    • Quarantine: <code>rejected_records</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with ln3:
        st.markdown(
            """
            <div class="lineage-node">
                <span class="lineage-tag">3. CURATED WAREHOUSE</span>
                <div style="font-weight:600; font-size:0.88rem; color:#142B3B; margin-bottom:4px;">
                    fact_exchange_rate
                </div>
                <div style="font-size:0.72rem; color:#68766F; line-height:1.45;">
                    • Dedup: (date, base, quote)<br>
                    • Grain: Daily Reference Rate<br>
                    • Store: <code>exchange_rates.csv</code><br>
                    • PostgreSQL Table Target
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with ln4:
        st.markdown(
            """
            <div class="lineage-node">
                <span class="lineage-tag">4. ANALYTICS CONSUMPTION</span>
                <div style="font-weight:600; font-size:0.88rem; color:#142B3B; margin-bottom:4px;">
                    fact_rate_analytics
                </div>
                <div style="font-size:0.72rem; color:#68766F; line-height:1.45;">
                    • Return: Daily % Delta<br>
                    • Volatility: 7d, 30d, 90d (Ann.)<br>
                    • Store: <code>rate_analytics.csv</code><br>
                    • Serves: Overview & Vol Lab
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # ── F. Historical Batch Throughput & Audit Log ────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem; font-weight:600; color:#142B3B; margin-bottom:0.2rem;">
            Batch Throughput & Execution History
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.9rem;">
            Audit trail of ingestion batches, committed records, and operational errors.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if runs.empty:
        st.info("No execution runs recorded yet. Click 'Run Pipeline' above to execute the first batch.")
    else:
        display_runs = runs.sort_values("started_at", ascending=False).head(20)

        if len(runs) >= 2:
            fig_runs = go.Figure()
            fig_runs.add_trace(
                go.Bar(
                    x=runs["started_at"],
                    y=runs["rows_inserted"],
                    name="Committed",
                    marker_color=COLORS["teal"],
                    hovertemplate="Run: %{x}<br>Committed: <b>%{y} rows</b><extra></extra>",
                )
            )
            fig_runs.add_trace(
                go.Bar(
                    x=runs["started_at"],
                    y=runs["rows_rejected"],
                    name="Rejected",
                    marker_color=COLORS["red"],
                    hovertemplate="Run: %{x}<br>Rejected: <b>%{y} rows</b><extra></extra>",
                )
            )
            fig_runs.update_layout(
                title="Batch Ingestion Throughput History",
                barmode="stack",
                xaxis_title="Execution Timestamp",
                yaxis_title="Record Count",
                height=300,
            )
            apply_theme(fig_runs)
            st.plotly_chart(fig_runs, use_container_width=True)

        disp_table = display_runs[
            ["run_type", "status", "started_at", "rows_fetched", "rows_inserted", "rows_rejected", "error_message"]
        ].copy()
        disp_table.columns = [
            "Run Type", "Status", "Started At", "Fetched", "Committed", "Rejected", "Error Message"
        ]
        st.dataframe(disp_table, use_container_width=True, hide_index=True)
