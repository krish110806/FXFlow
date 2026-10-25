"""
FXFlow — Dashboard · CSV Data Pipeline page.

World Bank Inflation pipeline monitor:
Ingestion, transformations, data quality verification, lineage, and warehouse operations.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fxflow.data_access_csv import (
    get_csv_cleaned,
    get_csv_freshness,
    get_csv_pipeline_runs,
)
from fxflow.pipeline.csv_orchestrator import (
    CLEANED_CSV,
    ANALYTICS_CSV,
    RAW_CSV,
    RUNS_CSV,
    run_csv_pipeline,
)
from fxflow.dashboard.theme import COLORS, apply_theme


def _switcher(current: str) -> None:
    """Render the REST API / CSV switcher and handle navigation."""
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
                type="primary" if current == "rest" else "secondary",
                use_container_width=True,
                help="Switch to the Frankfurter REST API pipeline",
            ):
                st.session_state["pipeline_source"] = "rest"
                st.rerun()
        with col_csv:
            if st.button(
                "CSV",
                key="switcher_to_csv",
                type="primary" if current == "csv" else "secondary",
                use_container_width=True,
                help="Switch to the World Bank CSV pipeline",
            ):
                st.session_state["pipeline_source"] = "csv"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render() -> None:
    """Render the CSV (World Bank Inflation) Data Pipeline page."""

    freshness = get_csv_freshness()
    runs = get_csv_pipeline_runs()
    cleaned_df = get_csv_cleaned()

    last_successful_run = freshness.get("last_successful_run")
    last_run_status = str(freshness.get("last_run_status") or "").lower()

    last_run_record: Dict[str, Any] = {}
    if not runs.empty:
        last_run_record = runs.iloc[-1].to_dict()
    stage_details = last_run_record.get("_stage_details", [])
    run_stages = {
        stage.get("stage"): stage
        for stage in stage_details
        if isinstance(stage, dict) and stage.get("stage")
    }

    def _count_text(value: Any) -> str:
        if value is None or pd.isna(value):
            return "—"
        return f"{int(value):,}"

    def _stage_status(name: str) -> str:
        stage = run_stages.get(name)
        return str(stage.get("status", "idle")).lower() if stage else "idle"

    # ── Switcher ────────────────────────────────────────────────────────
    _switcher("csv")

    # ── A. Compact Page Header & Controls ──────────────────────────────
    h_col1, h_col2 = st.columns([3, 1.2])

    with h_col1:
        last_run_str = (
            pd.Timestamp(last_successful_run).strftime("%Y-%m-%d %H:%M UTC")
            if last_successful_run else "Awaiting Execution"
        )
        st.markdown(
            f"""
            <div style="padding-bottom: 0.6rem; border-bottom: 1px solid #E5DED0; margin-bottom: 1rem;">
                <div class="fx-eyebrow">DATA PIPELINE &amp; WAREHOUSE OPERATIONS</div>
                <h1 style="margin: 0; font-size: 2.1rem; line-height: 1.15; color: #142B3B;">CSV Pipeline</h1>
                <p class="fx-subtext" style="margin: 0.25rem 0 0.5rem 0; font-size: 0.88rem; color: #68766F;">
                    World Bank Inflation Data · Ingestion, validation, transformation and warehouse.
                </p>
                <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
                            font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
                            color: #68766F; margin-top: 4px;">
                    <span style="background: #EDE7DC; padding: 2px 8px; border-radius: 4px;
                                 color: #142B3B; font-weight: 600;">
                        SOURCE: World Bank · FP.CPI.TOTL.ZG (Inflation, consumer prices %)
                    </span>
                    <span style="color: #A0ABA6;">•</span>
                    <span>
                        LAST SUCCESSFUL RUN: <strong>{last_run_str}</strong>
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
            run_btn = st.button(
                "Run Pipeline",
                use_container_width=True,
                help="Execute CSV ingestion: Extract → Validate → Transform → Analytics → Store",
                key="csv_run_pipeline_btn",
            )
        with btn_c2:
            refresh_btn = st.button(
                "Refresh",
                use_container_width=True,
                help="Reload persisted CSV pipeline data",
                key="csv_refresh_btn",
            )

    # Handle pipeline execution
    if run_btn:
        with st.spinner("Executing CSV pipeline: Extraction → Validation → Transformation → Analytics → Storage..."):
            try:
                summary = run_csv_pipeline()
                if summary.get("status") == "success":
                    st.success(
                        f"✓ CSV Pipeline complete: {summary.get('rows_fetched', 0):,} fetched, "
                        f"{summary.get('rows_valid', 0):,} valid, "
                        f"{summary.get('rows_committed', 0):,} committed to store."
                    )
                else:
                    st.error(
                        f"⚠️ CSV Pipeline error: {summary.get('error', 'Execution interrupted')}"
                    )
                st.rerun()
            except Exception as exc:
                st.error(f"CSV Pipeline execution failed: {exc}")

    if refresh_btn:
        st.rerun()

    # ── B. KPI Cards ────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        latest_yr = freshness.get("latest_year")
        oldest_yr = freshness.get("oldest_year")
        if latest_yr:
            yr_span = f"{oldest_yr}–{latest_yr}" if oldest_yr else str(latest_yr)
            st.metric(
                "Latest Data Year",
                str(latest_yr),
                delta=f"Coverage: {yr_span}",
                delta_color="off",
                help="Most recent year in the cleaned inflation dataset",
            )
        else:
            st.metric("Latest Data Year", "Not Ingested", delta="Awaiting Run", delta_color="off")

    with k2:
        total_raw = freshness.get("total_raw_rows", 0)
        total_cleaned = freshness.get("total_cleaned_rows", 0)
        st.metric(
            "Input / Output Records",
            f"{total_raw:,} → {total_cleaned:,}",
            delta=f"{total_cleaned:,} cleaned rows" if total_cleaned else "0 records",
            delta_color="normal" if total_cleaned > 0 else "off",
            help="Total raw records fetched vs. cleaned records in warehouse",
        )

    with k3:
        countries = freshness.get("countries", 0)
        st.metric(
            "Countries Tracked",
            str(countries),
            delta="World Bank Coverage",
            delta_color="off",
            help="Unique countries in the cleaned inflation dataset",
        )

    with k4:
        if last_run_status == "success":
            badge_class = "fx-badge-emerald"
            status_text = "SUCCESS"
        elif last_run_status == "error":
            badge_class = "fx-badge-terracotta"
            status_text = "FAILED"
        elif last_run_status == "running":
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
                <div style="font-size: 0.72rem; font-weight:600; letter-spacing:0.08em;
                            color:#68766F; text-transform:uppercase;">
                    LATEST RUN STATUS
                </div>
                <div style="display: flex; align-items: baseline;
                            justify-content: space-between; margin-top: 6px;">
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

    # ── C. Stage Execution Telemetry ────────────────────────────────────
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.6rem;">
            <div>
                <span class="fx-eyebrow">END-TO-END EXECUTION FLOW</span>
                <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem;
                            font-weight:600; color:#142B3B;">
                    Stage Execution Telemetry
                </div>
            </div>
            <div style="font-size:0.75rem; color:#68766F; font-family:'IBM Plex Mono', monospace;">
                World Bank API → Raw CSV → Validation → Cleaned Dataset → Analytics
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rows_raw_text = _count_text(last_run_record.get("rows_fetched"))
    rows_valid_text = _count_text(last_run_record.get("rows_valid"))
    rows_rejected_text = _count_text(last_run_record.get("rows_rejected"))
    rows_transformed_text = _count_text(
        run_stages.get("Transformation", {}).get("records_out")
    )
    rows_analytics_text = _count_text(
        run_stages.get("Analytics Preparation", {}).get("records_out")
    )
    rows_committed_text = _count_text(last_run_record.get("rows_committed"))
    rows_stored_text = f"{len(cleaned_df):,}" if not cleaned_df.empty else "0"

    s1_status = _stage_status("CSV Extraction")
    s2_status = _stage_status("Data Validation")
    s3_status = _stage_status("Transformation")
    s4_status = _stage_status("Analytics Preparation")
    s5_status = _stage_status("Warehouse / Local Storage")

    def _stage_badge(status: str) -> tuple:
        if status == "success":
            return "fx-badge-emerald", "ACTIVE"
        elif status == "error":
            return "fx-badge-terracotta", "ERROR"
        elif status == "warning":
            return "fx-badge-gold", "PARTIAL"
        else:
            return "fx-badge-navy", "NOT RUN"

    s_col1, a1, s_col2, a2, s_col3, a3, s_col4, a4, s_col5 = st.columns(
        [1.8, 0.25, 1.8, 0.25, 1.8, 0.25, 1.8, 0.25, 2.1]
    )

    with s_col1:
        badge, lbl = _stage_badge(s1_status)
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 01</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">CSV Extraction</div>
                    <div style="font-size:0.72rem; color:#68766F;">World Bank API v2</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Fetched: <strong>{rows_raw_text}</strong> rows<br>
                    Indicator: FP.CPI.TOTL.ZG
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a1:
        st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)

    with s_col2:
        badge, lbl = _stage_badge(s2_status)
        if lbl == "ACTIVE":
            lbl = "PASSED"
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 02</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">Data Validation</div>
                    <div style="font-size:0.72rem; color:#68766F;">Schema & Bounds Audit</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Valid: <strong>{rows_valid_text}</strong> rows<br>
                    Rejected: <strong>{rows_rejected_text}</strong> rows
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a2:
        st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)

    with s_col3:
        badge, lbl = _stage_badge(s3_status)
        if lbl == "ACTIVE":
            lbl = "COMPLETED"
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 03</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">Transformation</div>
                    <div style="font-size:0.72rem; color:#68766F;">Normalisation & Dedup</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Target: <strong>wb_inflation_cleaned</strong><br>
                    Transformed: <strong>{rows_transformed_text}</strong> rows
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a3:
        st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)

    with s_col4:
        badge, lbl = _stage_badge(s4_status)
        if lbl == "ACTIVE":
            lbl = "COMPLETED"
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 04</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">Analytics Engine</div>
                    <div style="font-size:0.72rem; color:#68766F;">YoY Change & Rolling Avg</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Computed: <strong>{rows_analytics_text}</strong> rows<br>
                    Windows: 5-year rolling
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with a4:
        st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)

    with s_col5:
        badge, lbl = _stage_badge(s5_status)
        if lbl == "ACTIVE":
            lbl = "CSV STORAGE"
        st.markdown(
            f"""
            <div class="pipeline-stage-card">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="pipeline-stage-num">STAGE 05</span>
                        <span class="fx-badge {badge}" style="font-size:0.65rem;">{lbl}</span>
                    </div>
                    <div class="pipeline-stage-title">Warehouse Load</div>
                    <div style="font-size:0.72rem; color:#68766F;">Local CSV Storage</div>
                </div>
                <div class="pipeline-stage-metrics">
                    Committed this run: <strong>{rows_committed_text}</strong><br>
                    Total stored: <strong>{rows_stored_text}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # ── D. Data Quality Report ───────────────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem;
                    font-weight:600; color:#142B3B; margin-bottom:0.2rem;">
            Data Quality &amp; Schema Integrity Report
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.9rem;">
            Validation pass rate = output records / (output + rejected). Missing values
            filtered before commitment; hyperinflation values (>500%) quarantined.
        </div>
        """,
        unsafe_allow_html=True,
    )

    validation_stage = run_stages.get("Data Validation")
    if validation_stage is None:
        st.info(
            "No validation results are recorded for the latest run. Click 'Run Pipeline' to execute a batch."
        )
    else:
        total_in = last_run_record.get("rows_fetched")
        total_out = last_run_record.get("rows_valid")
        total_rej = last_run_record.get("rows_rejected")
        transform_stage = run_stages.get("Transformation", {})
        dupes = transform_stage.get("duplicates_removed")
        missing_raw = validation_stage.get("missing_values")
        denominator = (
            total_out + total_rej
            if total_out is not None and total_rej is not None
            else 0
        )
        pass_rate = (total_out / denominator * 100) if denominator else None

        qc1, qc2, qc3, qc4, qc5, qc6 = st.columns(6)
        with qc1:
            st.metric("Input Records", _count_text(total_in), help="Fetched records in the latest run")
        with qc2:
            st.metric("Output Records", _count_text(total_out), help="Rows accepted by validation in the latest run")
        with qc3:
            st.metric(
                "Rejected Rows", _count_text(total_rej),
                delta="Clean" if total_rej == 0 else f"{_count_text(total_rej)} flagged",
                delta_color="normal" if total_rej == 0 else "inverse",
                help="Records rejected by range/schema checks",
            )
        with qc4:
            st.metric(
                "Duplicates Removed", _count_text(dupes),
                delta="None" if dupes == 0 else f"{_count_text(dupes)} removed",
                delta_color="normal" if dupes == 0 else "inverse",
                help="Duplicate (country_code, year) records removed during the latest transform",
            )
        with qc5:
            st.metric(
                "Missing Values (Run)", _count_text(missing_raw),
                delta="None" if missing_raw == 0 else f"{_count_text(missing_raw)} nulls",
                delta_color="normal" if missing_raw == 0 else "inverse",
                help="Missing inflation values counted during the latest validation",
            )
        with qc6:
            st.metric(
                "Validation Pass Rate", f"{pass_rate:.1f}%" if pass_rate is not None else "N/A",
                delta=("Optimal" if pass_rate >= 99.0 else "Sub-optimal") if pass_rate is not None else "No rows assessed",
                delta_color=("normal" if pass_rate >= 99.0 else "inverse") if pass_rate is not None else "off",
                help="Output records / (output + rejected) × 100",
            )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if total_rej == 0:
            st.markdown(
                """
                <div style="background: #EBF5F0; border: 1px solid #BEDECF; border-radius: 8px;
                            padding: 10px 14px; color: #1E7E5A; font-size: 0.82rem;
                            display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1rem;">✓</span>
                    <span><strong>Validation Clean:</strong> Zero rejected records — all ingested
                    rows passed numeric, range (−50% to +500%), year (1960+) and country code checks.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning(f"⚠️ {total_rej} record(s) failed validation and were quarantined.")

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # ── E. Data Lineage ──────────────────────────────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem;
                    font-weight:600; color:#142B3B; margin-bottom:0.2rem;">
            Data Lineage &amp; Storage Architecture
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.9rem;">
            Traceable path from World Bank source to analytics-ready cleaned store.
        </div>
        """,
        unsafe_allow_html=True,
    )

    ln1, ln2, ln3, ln4 = st.columns(4)

    with ln1:
        st.markdown(
            f"""
            <div class="lineage-node">
                <span class="lineage-tag">1. EXTERNAL INGESTION</span>
                <div style="font-weight:600; font-size:0.88rem; color:#142B3B; margin-bottom:4px;">
                    World Bank Source
                </div>
                <div style="font-size:0.72rem; color:#68766F; line-height:1.45;">
                    • Indicator: <code>FP.CPI.TOTL.ZG</code><br>
                    • Format: JSON → DataFrame<br>
                    • Countries: 10 (incl. India)<br>
                    • Latest: <code>data/raw/wb_inflation_raw.csv</code><br>
                    • Archived: timestamped <code>wb_inflation_raw_*.csv</code> snapshots
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with ln2:
        st.markdown(
            """
            <div class="lineage-node">
                <span class="lineage-tag">2. VALIDATION &amp; PURITY</span>
                <div style="font-weight:600; font-size:0.88rem; color:#142B3B; margin-bottom:4px;">
                    Rules Engine
                </div>
                <div style="font-size:0.72rem; color:#68766F; line-height:1.45;">
                    • Numeric inflation check<br>
                    • Range: <code>−50% to +500%</code><br>
                    • Year: <code>1960 – present</code><br>
                    • Null value filtration
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
                    wb_inflation_cleaned
                </div>
                <div style="font-size:0.72rem; color:#68766F; line-height:1.45;">
                    • Dedup: (country_code, year)<br>
                    • Grain: Annual country record<br>
                    • Store: <code>wb_inflation_cleaned.csv</code><br>
                    • Mode: Local CSV (idempotent)
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
                    wb_inflation_analytics
                </div>
                <div style="font-size:0.72rem; color:#68766F; line-height:1.45;">
                    • YoY Change: Annual % delta<br>
                    • Rolling: 5-year average<br>
                    • Store: <code>wb_inflation_analytics.csv</code><br>
                    • Serves: Trend analysis
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # ── F. Batch Throughput & Execution History ──────────────────────────
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem;
                    font-weight:600; color:#142B3B; margin-bottom:0.2rem;">
            Batch Throughput &amp; Execution History
        </div>
        <div style="font-size:0.8rem; color:#68766F; margin-bottom:0.9rem;">
            Audit trail of CSV ingestion batches, committed records, and operational errors.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if runs.empty:
        st.info(
            "No CSV pipeline runs recorded yet. Click 'Run Pipeline' to execute the first batch."
        )
    else:
        display_runs = runs.sort_values("started_at", ascending=False).head(20)

        if len(runs) >= 2:
            fig_runs = go.Figure()
            fig_runs.add_trace(
                go.Bar(
                    x=runs["started_at"],
                    y=runs["rows_committed"],
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
                title="CSV Pipeline Batch Throughput History",
                barmode="stack",
                xaxis_title="Execution Timestamp",
                yaxis_title="Record Count",
                height=300,
            )
            apply_theme(fig_runs)
            st.plotly_chart(fig_runs, use_container_width=True)

        disp_cols = [c for c in
            ["run_type", "status", "started_at", "rows_fetched",
             "rows_valid", "rows_committed", "rows_rejected", "error_message"]
            if c in display_runs.columns
        ]
        disp_table = display_runs[disp_cols].copy()
        rename_map = {
            "run_type": "Run Type", "status": "Status", "started_at": "Started At",
            "rows_fetched": "Fetched", "rows_valid": "Valid",
            "rows_committed": "Committed", "rows_rejected": "Rejected",
            "error_message": "Error Message",
        }
        disp_table.columns = [rename_map.get(c, c) for c in disp_cols]
        st.dataframe(disp_table, use_container_width=True, hide_index=True)
