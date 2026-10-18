"""
FXFlow — Editorial Finance Theme and Design System.

Crafted with an editorial-finance aesthetic inspired by private wealth
management terminals and modern institutional fintech platforms.

Palette:
  • Main background : Warm Ivory / Cream (#F4F0E7)
  • Card surfaces   : Soft Ivory (#FFFCF5)
  • Typography/Nav  : Midnight Navy (#142B3B)
  • Primary accent  : Muted Deep Teal (#287D6B)
  • Secondary accent: Champagne Gold (#C6A568)
  • Secondary text  : Muted Slate / Olive Grey (#68766F)
  • Positive delta  : Restrained Emerald Green (#1E7E5A)
  • Negative delta  : Muted Terracotta Red (#C25447)
  • Borders         : Subtle Warm Beige (#E5DED0)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import html
import plotly.graph_objects as go
import streamlit as st


# =====================================================================
# Centralised Colour Palette
# =====================================================================

COLORS = {
    # Surfaces & Canvas
    "bg_canvas":     "#F4F0E7",
    "surface_card":  "#FFFCF5",
    "surface_hover": "#FDF9F0",
    "surface_alt":   "#EDE7DC",

    # Brand & Typography
    "navy":          "#142B3B",
    "navy_dark":     "#0D1D28",
    "navy_light":    "#1D3A4F",
    "slate":         "#68766F",
    "slate_light":   "#8C9A93",
    "white":         "#FFFFFF",

    # Accents
    "teal":          "#287D6B",
    "teal_light":    "#369B86",
    "teal_soft":     "#E7F3F0",
    "gold":          "#C6A568",
    "gold_light":    "#D9BC85",
    "gold_soft":     "#F9F4EB",

    # Financial Movements
    "green":         "#1E7E5A",
    "green_soft":    "#EBF5F0",
    "red":           "#C25447",
    "red_soft":      "#FBF0EE",

    # Structure & Borders
    "border":        "#E5DED0",
    "border_dark":   "#D1C7B7",
    "border_light":  "#EFEAE0",
}

# Coordinated editorial palette for multi-line series
SERIES_COLORS = [
    "#287D6B",  # Deep Teal
    "#C6A568",  # Champagne Gold
    "#142B3B",  # Midnight Navy
    "#B86B52",  # Muted Terracotta
    "#3D6B8C",  # Prussian Blue
    "#6B7A4C",  # Muted Olive
    "#8A5E78",  # Antique Plum
    "#8C7A6B",  # Warm Taupe
    "#4D8C80",  # Sage Teal
    "#A8894D",  # Antique Ochre
]


# =====================================================================
# Plotly Theme Defaults
# =====================================================================

PLOTLY_LAYOUT = dict(
    font=dict(
        family="'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif",
        color=COLORS["navy"],
        size=12,
    ),
    paper_bgcolor=COLORS["surface_card"],
    plot_bgcolor="#FAF7F0",
    margin=dict(l=48, r=24, t=54, b=42),
    title_font=dict(
        family="'Newsreader', 'Georgia', serif",
        size=17,
        color=COLORS["navy"],
    ),
    legend=dict(
        bgcolor="rgba(255, 252, 245, 0.94)",
        bordercolor=COLORS["border"],
        borderwidth=1,
        font=dict(
            family="'Plus Jakarta Sans', sans-serif",
            size=11,
            color=COLORS["navy"],
        ),
    ),
    xaxis=dict(
        gridcolor="#EAE3D5",
        linecolor="#DCD4C4",
        zerolinecolor="#EAE3D5",
        tickfont=dict(
            family="'Plus Jakarta Sans', sans-serif",
            color=COLORS["slate"],
            size=11,
        ),
    ),
    yaxis=dict(
        gridcolor="#EAE3D5",
        linecolor="#DCD4C4",
        zerolinecolor="#EAE3D5",
        tickfont=dict(
            family="'Plus Jakarta Sans', sans-serif",
            color=COLORS["slate"],
            size=11,
        ),
    ),
    hoverlabel=dict(
        bgcolor=COLORS["navy"],
        font_color=COLORS["surface_card"],
        font_size=12,
        font_family="'IBM Plex Mono', 'Plus Jakarta Sans', monospace",
        bordercolor=COLORS["gold"],
    ),
)


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply the FXFlow editorial financial theme to any Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# =====================================================================
# Streamlit CSS Design System
# =====================================================================

CUSTOM_CSS = """
<style>
    /* ── Typography Imports ────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

    /* ── Global Layout & Canvas ────────────────────────────────────── */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #F4F0E7 !important;
        color: #142B3B !important;
        letter-spacing: -0.01em;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
        max-width: 1440px;
    }

    /* ── Editorial Headings ────────────────────────────────────────── */
    h1, .fx-title {
        font-family: 'Newsreader', Georgia, serif !important;
        font-weight: 600 !important;
        color: #142B3B !important;
        letter-spacing: -0.03em !important;
        margin-bottom: 0.25rem !important;
        line-height: 1.15 !important;
    }

    h2, .fx-subtitle {
        font-family: 'Newsreader', Georgia, serif !important;
        font-weight: 500 !important;
        color: #142B3B !important;
        letter-spacing: -0.02em !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.6rem !important;
    }

    h3, .fx-section-header {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        color: #142B3B !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 0.5rem !important;
    }

    p, span, label {
        color: #142B3B;
    }

    .fx-eyebrow {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.68rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 700;
        color: #C6A568;
        display: inline-block;
        margin-bottom: 0.35rem;
    }

    .fx-subtext {
        font-size: 0.92rem;
        color: #68766F;
        line-height: 1.5;
        margin-top: 0;
        margin-bottom: 1.25rem;
    }

    /* ── Midnight Navy Sidebar ─────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #142B3B !important;
        border-right: 1px solid #1D3A4F !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
        padding-left: 1.1rem;
        padding-right: 1.1rem;
    }

    section[data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }

    /* Hide the React Aria radio glyph, not its accessible input. */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-of-type > div:first-child > div:first-child {
        display: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 5px !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding: 9px 12px !important;
        border-radius: 6px !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: #8C9DA8 !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        cursor: pointer !important;
        margin: 0 !important;
        transition: all 0.15s ease !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        color: #FFFCF5 !important;
        background: rgba(255, 252, 245, 0.06) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:focus-within {
        outline: 2px solid #C6A568 !important;
        outline-offset: 2px !important;
    }

    /* Active Nav Item */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
        color: #FFFCF5 !important;
        font-weight: 600 !important;
        background: rgba(40, 125, 107, 0.24) !important;
        border-left: 3px solid #C6A568 !important;
        border-radius: 2px 6px 6px 2px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) * {
        color: #FFFCF5 !important;
        font-weight: 600 !important;
    }

    /* Lucide-style Outline SVG Icons */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p::before {
        content: "";
        display: inline-block;
        width: 16px;
        height: 16px;
        margin-right: 10px;
        flex: 0 0 16px;
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        opacity: 0.85;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        opacity: 1;
    }

    /* 1. Market Overview (LayoutDashboard) - Inactive: #8C9DA8, Active: #369B86 */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(1) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(1) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(1):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(1):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E") !important;
    }

    /* 2. Currency Explorer (ArrowLeftRight exchange arrows) */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(2) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(2) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 3 4 4-4 4'/%3E%3Cpath d='M20 7H4'/%3E%3Cpath d='m8 21-4-4 4-4'/%3E%3Cpath d='M4 17h16'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(2):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(2):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 3 4 4-4 4'/%3E%3Cpath d='M20 7H4'/%3E%3Cpath d='m8 21-4-4 4-4'/%3E%3Cpath d='M4 17h16'/%3E%3C/svg%3E") !important;
    }

    /* 3. Volatility Lab (Activity waveform) */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(3) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(3) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(3):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(3):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2'/%3E%3C/svg%3E") !important;
    }

    /* 4. Economic Insights (Globe2) */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(4) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(4) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpath d='M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20'/%3E%3Cpath d='M2 12h20'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(4):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(4):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpath d='M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20'/%3E%3Cpath d='M2 12h20'/%3E%3C/svg%3E") !important;
    }

    /* 5. Data Pipeline (Workflow connected nodes) */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(5) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(5) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='8' height='8' x='3' y='3' rx='2'/%3E%3Cpath d='M7 11v4a2 2 0 0 0 2 2h4'/%3E%3Crect width='8' height='8' x='13' y='13' rx='2'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(5):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(5):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='8' height='8' x='3' y='3' rx='2'/%3E%3Cpath d='M7 11v4a2 2 0 0 0 2 2h4'/%3E%3Crect width='8' height='8' x='13' y='13' rx='2'/%3E%3C/svg%3E") !important;
    }

    section[data-testid="stSidebar"] hr {
        border-top: 1px solid rgba(229, 222, 208, 0.12) !important;
        margin: 1.1rem 0 !important;
    }

    /* ── Hero Banner & Financial Quote Card ──────────────────────── */
    .fx-hero-banner {
        background-color: #142B3B;
        background-image: 
            radial-gradient(circle at 92% 18%, rgba(40, 125, 107, 0.22) 0%, transparent 48%),
            radial-gradient(circle at 8% 85%, rgba(198, 165, 104, 0.14) 0%, transparent 42%),
            linear-gradient(135deg, rgba(20, 43, 59, 0.96) 0%, rgba(13, 29, 40, 0.98) 100%);
        border: 1px solid rgba(229, 222, 208, 0.2);
        border-radius: 14px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 24px rgba(20, 43, 59, 0.08);
    }

    .fx-hero-quote-card {
        background: rgba(255, 252, 245, 0.06);
        border: 1px solid rgba(229, 222, 208, 0.16);
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.16);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* ── Benchmark Cards (2x3 Grid) ───────────────────────────────── */
    .fx-benchmark-card {
        background-color: #FFFCF5;
        border: 1px solid #E5DED0;
        border-radius: 10px;
        padding: 1.15rem 1.3rem;
        box-shadow: 0 2px 6px rgba(20, 43, 59, 0.03);
        transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 185px;
        margin-bottom: 0.9rem;
    }
    .fx-benchmark-card:hover {
        border-color: #C6A568;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(20, 43, 59, 0.07);
    }
    .fx-pair-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: #142B3B;
        letter-spacing: -0.01em;
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    .fx-pair-sub {
        font-size: 0.74rem;
        color: #68766F;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 1px;
    }
    .fx-rate-display {
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        font-size: 1.55rem;
        color: #142B3B;
        letter-spacing: -0.02em;
        margin-top: 6px;
        margin-bottom: 4px;
        white-space: nowrap;
    }
    .fx-card-footer {
        display: flex;
        justify-content: space-between;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        color: #68766F;
        padding-top: 8px;
        margin-top: 6px;
        border-top: 1px dashed #E5DED0;
    }

    /* ── Pipeline Stage Flow & Telemetry ─────────────────────────── */
    .pipeline-stage-card {
        background-color: #FFFCF5;
        border: 1px solid #E5DED0;
        border-radius: 8px;
        padding: 12px 13px;
        box-shadow: 0 1px 3px rgba(20, 43, 59, 0.03);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .pipeline-stage-card:hover {
        border-color: #C6A568;
        transform: translateY(-1px);
    }
    .pipeline-stage-num {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem;
        font-weight: 700;
        color: #C6A568;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .pipeline-stage-title {
        font-weight: 600;
        font-size: 0.88rem;
        color: #142B3B;
        line-height: 1.25;
        margin-bottom: 6px;
    }
    .pipeline-stage-metrics {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        color: #68766F;
        line-height: 1.45;
        margin-top: 6px;
        padding-top: 6px;
        border-top: 1px dashed #E5DED0;
    }
    .pipeline-flow-arrow {
        display: flex;
        align-items: center;
        justify-content: center;
        color: #C6A568;
        font-size: 1.15rem;
        font-weight: 700;
        padding-top: 2rem;
    }

    /* Lineage Node */
    .lineage-node {
        background-color: #FFFCF5;
        border: 1px solid #E5DED0;
        border-radius: 8px;
        padding: 12px 14px;
        box-shadow: 0 1px 3px rgba(20, 43, 59, 0.03);
        height: 100%;
        transition: border-color 0.15s ease;
    }
    .lineage-node:hover {
        border-color: #287D6B;
    }
    .lineage-tag {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        background: #EDE7DC;
        color: #142B3B;
        margin-bottom: 5px;
    }

    /* ── Soft Ivory Card Surfaces ─────────────────────────────────── */
    .fx-card {
        background-color: #FFFCF5;
        border: 1px solid #E5DED0;
        border-radius: 10px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 2px 6px rgba(20, 43, 59, 0.03), 0 1px 2px rgba(20, 43, 59, 0.02);
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        margin-bottom: 1rem;
    }

    .fx-card:hover {
        border-color: #D1C7B7;
        box-shadow: 0 4px 14px rgba(20, 43, 59, 0.06);
    }

    /* Benchmark Card Container Overrides */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFCF5 !important;
        border: 1px solid #E5DED0 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 6px rgba(20, 43, 59, 0.03), 0 1px 2px rgba(20, 43, 59, 0.02) !important;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #D1C7B7 !important;
        box-shadow: 0 4px 14px rgba(20, 43, 59, 0.06) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0.95rem 1rem !important;
        gap: 0.25rem !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] .stPlotlyChart {
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        box-shadow: none !important;
        margin: 0 !important;
    }

    /* Streamlit Metric Overrides */
    div[data-testid="stMetric"] {
        background-color: #FFFCF5 !important;
        border: 1px solid #E5DED0 !important;
        border-radius: 10px !important;
        padding: 1.1rem 1.25rem !important;
        box-shadow: 0 2px 6px rgba(20, 43, 59, 0.03) !important;
        transition: all 0.18s ease !important;
    }

    div[data-testid="stMetric"]:hover {
        border-color: #D1C7B7 !important;
        box-shadow: 0 4px 14px rgba(20, 43, 59, 0.06) !important;
        transform: translateY(-1px);
    }

    div[data-testid="stMetric"] label {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #68766F !important;
        font-weight: 600 !important;
        font-size: 0.72rem !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace !important;
        color: #142B3B !important;
        font-weight: 600 !important;
        font-size: 1.55rem !important;
        letter-spacing: -0.02em !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }

    /* ── Plotly Containers ─────────────────────────────────────────── */
    .stPlotlyChart {
        background-color: #FFFCF5 !important;
        border: 1px solid #E5DED0 !important;
        border-radius: 10px !important;
        padding: 8px 10px !important;
        box-shadow: 0 2px 6px rgba(20, 43, 59, 0.03) !important;
    }

    /* ── Form Controls & Filters ───────────────────────────────────── */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stDateInput > div > div,
    .stNumberInput > div > div {
        background-color: #FFFCF5 !important;
        border: 1px solid #E5DED0 !important;
        border-radius: 8px !important;
        color: #142B3B !important;
        font-size: 0.9rem !important;
    }

    .stSelectbox label,
    .stMultiSelect label,
    .stDateInput label,
    .stNumberInput label {
        color: #142B3B !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.02em !important;
    }

    /* MultiSelect Tags */
    span[data-baseweb="tag"] {
        background-color: #EDE7DC !important;
        border: 1px solid #DCD4C4 !important;
        border-radius: 5px !important;
        color: #142B3B !important;
    }

    /* ── Buttons ───────────────────────────────────────────────────── */
    .stButton > button {
        background-color: #287D6B !important;
        color: #FFFCF5 !important;
        border: 1px solid #206858 !important;
        border-radius: 7px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        padding: 0.45rem 1.25rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 3px rgba(40, 125, 107, 0.2) !important;
    }

    .stButton > button:hover {
        background-color: #206858 !important;
        box-shadow: 0 3px 8px rgba(40, 125, 107, 0.3) !important;
        transform: translateY(-1px);
    }

    /* ── Table & Dataframe Styling ─────────────────────────────────── */
    .stDataFrame {
        background-color: #FFFCF5 !important;
        border: 1px solid #E5DED0 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 6px rgba(20, 43, 59, 0.03) !important;
    }

    /* ── Expanders ─────────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background-color: #FFFCF5 !important;
        border: 1px solid #E5DED0 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #142B3B !important;
    }

    div[data-testid="stExpander"] {
        border: none !important;
        margin-top: 0.8rem !important;
    }

    /* ── Dividers ──────────────────────────────────────────────────── */
    hr {
        border: none !important;
        border-top: 1px solid #E5DED0 !important;
        margin: 1.4rem 0 !important;
    }

    /* ── Badges & Status Pills ─────────────────────────────────────── */
    .fx-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.55rem;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .fx-badge-gold {
        background: #F9F4EB;
        color: #8C6D2E;
        border: 1px solid #E6D7BE;
    }

    .fx-badge-teal {
        background: #E7F3F0;
        color: #1C6152;
        border: 1px solid #BDDCD5;
    }

    .fx-badge-navy {
        background: #E7EDF2;
        color: #142B3B;
        border: 1px solid #C4D3DE;
    }

    .fx-badge-emerald {
        background: #EBF5F0;
        color: #1E7E5A;
        border: 1px solid #BEDECF;
    }

    .fx-badge-terracotta {
        background: #FBF0EE;
        color: #C25447;
        border: 1px solid #ECCDC7;
    }

    .status-success {
        background: #EBF5F0;
        color: #1E7E5A;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.76rem;
        border: 1px solid #BEDECF;
        display: inline-block;
    }

    .status-error {
        background: #FBF0EE;
        color: #C25447;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.76rem;
        border: 1px solid #ECCDC7;
        display: inline-block;
    }

    .status-running {
        background: #E7F3F0;
        color: #287D6B;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.76rem;
        border: 1px solid #BDDCD5;
        display: inline-block;
    }

    /* Sidebar button navigation */
    section[data-testid="stSidebar"] .st-key-nav_menu {
        gap: 6px !important;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stButton"] button {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        height: 50px !important;
        min-height: 50px !important;
        box-sizing: border-box !important;
        padding: 0 12px !important;
        border: 1px solid transparent !important;
        border-left: 3px solid transparent !important;
        border-radius: 6px !important;
        background: transparent !important;
        color: #E2E8F0 !important;
        box-shadow: none !important;
        transform: none !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        text-align: left !important;
        transition: all 0.15s ease !important;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stButton"] button > div {
        width: 100% !important;
        justify-content: flex-start !important;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stButton"] button > div > span {
        width: 100% !important;
        flex: 1 1 auto !important;
        justify-content: flex-start !important;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stButton"] button:hover {
        background: rgba(255, 252, 245, 0.06) !important;
        color: #FFFCF5 !important;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stButton"] button:focus-visible {
        outline: 2px solid #C6A568 !important;
        outline-offset: 2px !important;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
        background: rgba(40, 125, 107, 0.24) !important;
        border-left: 3px solid #C6A568 !important;
        border-radius: 6px !important;
        color: #FFFCF5 !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stMarkdownContainer"] p {
        display: flex !important;
        width: 100% !important;
        justify-content: flex-start !important;
        align-items: center !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stMarkdownContainer"] p::before {
        content: "";
        display: inline-block;
        width: 24px;
        height: 24px;
        margin-right: 12px;
        flex: 0 0 24px;
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        opacity: 0.85;
    }

    section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p::before {
        opacity: 1;
    }

    .st-key-nav_market_overview [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
    }
    .st-key-nav_market_overview [data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E");
    }

    .st-key-nav_currency_explorer [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 3 4 4-4 4'/%3E%3Cpath d='M20 7H4'/%3E%3Cpath d='m8 21-4-4 4-4'/%3E%3Cpath d='M4 17h16'/%3E%3C/svg%3E");
    }
    .st-key-nav_currency_explorer [data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m16 3 4 4-4 4'/%3E%3Cpath d='M20 7H4'/%3E%3Cpath d='m8 21-4-4 4-4'/%3E%3Cpath d='M4 17h16'/%3E%3C/svg%3E");
    }

    .st-key-nav_volatility_lab [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2'/%3E%3C/svg%3E");
    }
    .st-key-nav_volatility_lab [data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.48 12H2'/%3E%3C/svg%3E");
    }

    .st-key-nav_economic_insights [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpath d='M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20'/%3E%3Cpath d='M2 12h20'/%3E%3C/svg%3E");
    }
    .st-key-nav_economic_insights [data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpath d='M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20'/%3E%3Cpath d='M2 12h20'/%3E%3C/svg%3E");
    }

    .st-key-nav_data_pipeline [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='8' height='8' x='3' y='3' rx='2'/%3E%3Cpath d='M7 11v4a2 2 0 0 0 2 2h4'/%3E%3Crect width='8' height='8' x='13' y='13' rx='2'/%3E%3C/svg%3E");
    }
    .st-key-nav_data_pipeline [data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='8' height='8' x='3' y='3' rx='2'/%3E%3Cpath d='M7 11v4a2 2 0 0 0 2 2h4'/%3E%3Crect width='8' height='8' x='13' y='13' rx='2'/%3E%3C/svg%3E");
    }
</style>
"""


# =====================================================================
# Reusable UI Component Renderers
# =====================================================================

def render_header(
    title: str,
    subtitle: str,
    eyebrow: Optional[str] = "FXFlow Intelligence",
    status_label: Optional[str] = "Archive Live",
    status_badge_type: str = "teal",
) -> None:
    """Render an editorial finance page header with status indicator."""
    badge_class = f"fx-badge-{status_badge_type}"
    eyebrow_html = (
        f'<div class="fx-eyebrow">{html.escape(eyebrow)}</div>'
        if eyebrow else ""
    )
    status_html = ""
    if status_label:
        status_html = f"""
        <div style="text-align: right;">
            <span class="fx-badge {badge_class}">
                <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:currentColor;"></span>
                {html.escape(status_label)}
            </span>
            <div style="font-family:'IBM Plex Mono', monospace; font-size:0.7rem; color:#68766F; margin-top:4px;">
                BASE: USD · UTC
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 0.8rem; margin-bottom: 0.5rem; border-bottom: 1px solid #E5DED0;">
            <div>
                {eyebrow_html}
                <h1 style="margin: 0; font-size: 2.15rem; line-height: 1.15;">{html.escape(title)}</h1>
                <p class="fx-subtext" style="margin-bottom: 0; margin-top: 0.25rem;">{html.escape(subtitle)}</p>
            </div>
            {status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card_html(
    pair: str,
    rate_str: str,
    delta_pct: Optional[float] = None,
    quote_name: str = "",
    min_rate: Optional[float] = None,
    max_rate: Optional[float] = None,
) -> str:
    """Return an HTML snippet for a bespoke wealth management KPI card."""
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
            f'style="font-family:\'IBM Plex Mono\', monospace; font-size:0.72rem; white-space:nowrap; flex-shrink:0;">'
            f'{delta_symbol} {delta_text}</span>'
        )
    else:
        delta_html = '<span class="fx-badge fx-badge-navy" style="font-size:0.7rem; white-space:nowrap; flex-shrink:0;">—</span>'

    range_html = ""
    if min_rate is not None and max_rate is not None and min_rate > 0:
        range_html = (
            f'<div style="display:flex; justify-content:space-between; font-family:\'IBM Plex Mono\', monospace; '
            f'font-size:0.68rem; color:#68766F; margin-top:8px; padding-top:6px; border-top:1px dashed #E5DED0;">'
            f'<span>L: {min_rate:.4f}</span><span>H: {max_rate:.4f}</span></div>'
        )

    clean_pair = html.escape(pair)
    clean_name = html.escape(quote_name)

    return (
        f'<div class="fx-card" style="padding:1.05rem 1.15rem; margin-bottom:0.75rem;">'
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px; gap:4px;">'
        f'<div style="min-width:0; overflow:hidden;">'
        f'<div style="font-weight:700; font-size:1.05rem; color:#142B3B; letter-spacing:-0.01em;">{clean_pair}</div>'
        f'<div style="font-size:0.72rem; color:#68766F; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="{clean_name}">{clean_name}</div>'
        f'</div>'
        f'{delta_html}'
        f'</div>'
        f'<div style="font-family:\'IBM Plex Mono\', monospace; font-weight:600; font-size:1.5rem; color:#142B3B; letter-spacing:-0.02em; margin-top:4px;">'
        f'{rate_str}'
        f'</div>'
        f'{range_html}'
        f'</div>'
    )
