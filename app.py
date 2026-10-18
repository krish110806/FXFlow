"""
FXFlow — Editorial Financial Intelligence Platform.

Main Streamlit Application.
Run with:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

# ── page config (must be first Streamlit call) ───────────────────────
st.set_page_config(
    page_title="FXFlow — Foreign Exchange Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── theme CSS ────────────────────────────────────────────────────────
from fxflow.dashboard.theme import CUSTOM_CSS, COLORS

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    # Editorial Brand Monogram & Title
    st.markdown(
        """
        <div style="padding: 12px 6px 18px 6px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
                <!-- Professional SVG Logo: Geometric FX Monogram, Exchange Arrows & Upward Market Trend -->
                <svg width="42" height="42" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink: 0; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.25));">
                    <defs>
                        <linearGradient id="fxEmblemBg" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#1A384D"/>
                            <stop offset="100%" stop-color="#0E1E2A"/>
                        </linearGradient>
                        <linearGradient id="fxTealGrad" x1="0" y1="0" x2="44" y2="0" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#287D6B"/>
                            <stop offset="100%" stop-color="#3EB89B"/>
                        </linearGradient>
                    </defs>
                    <!-- Background Squircle Container -->
                    <rect x="1" y="1" width="42" height="42" rx="10" fill="url(#fxEmblemBg)" stroke="#C6A568" stroke-width="1.2" stroke-opacity="0.5"/>
                    <!-- Subtle Circular Orbit / Geometry Guide -->
                    <circle cx="22" cy="22" r="16.5" stroke="#287D6B" stroke-width="0.75" stroke-dasharray="2.5 3" stroke-opacity="0.35"/>
                    <!-- Geometric F: Vertical Stem & Crossbars (Champagne Gold) -->
                    <path d="M12 11V31" stroke="#C6A568" stroke-width="2.6" stroke-linecap="round"/>
                    <path d="M12 12H21" stroke="#C6A568" stroke-width="2.6" stroke-linecap="round"/>
                    <path d="M12 20H19" stroke="#C6A568" stroke-width="2.4" stroke-linecap="round"/>
                    <!-- Geometric X: Descending Diagonal (Champagne Gold) -->
                    <path d="M22 17L31 31" stroke="#C6A568" stroke-width="2.6" stroke-linecap="round"/>
                    <!-- Upward Market Trend: Ascending Diagonal (Teal) with Arrowhead -->
                    <path d="M20 31L31 14" stroke="url(#fxTealGrad)" stroke-width="2.8" stroke-linecap="round"/>
                    <path d="M26 13H33V20" stroke="#3EB89B" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                    <!-- Bilateral Exchange Arrows at Base (Currency Swap Telemetry) -->
                    <path d="M14 36H23M21 34L23 36L21 38" stroke="#C6A568" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M30 36H25M27 34L25 36L27 38" stroke="#3EB89B" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div>
                    <div style="
                        font-family: 'Newsreader', Georgia, serif;
                        font-size: 1.45rem;
                        font-weight: 600;
                        color: #FFFCF5;
                        letter-spacing: -0.02em;
                        line-height: 1.1;
                    ">FXFlow</div>
                    <div style="
                        font-family: 'Plus Jakarta Sans', sans-serif;
                        font-size: 0.65rem;
                        color: #C6A568;
                        letter-spacing: 0.12em;
                        text-transform: uppercase;
                        font-weight: 700;
                    ">MARKET INTELLIGENCE</div>
                </div>
            </div>
            <div style="
                font-size: 0.76rem;
                color: #8C9DA8;
                line-height: 1.4;
                padding-top: 4px;
            ">
                Institutional foreign exchange warehouse and volatility surveillance platform.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Navigation Label
    st.markdown(
        """
        <div style="
            font-size: 0.68rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
            color: #C6A568;
            margin-bottom: 6px;
            padding-left: 4px;
        ">SURVEILLANCE MODULES</div>
        """,
        unsafe_allow_html=True,
    )

    # Button navigation keeps the page selection without rendering radio markers.
    navigation_items = [
        ("Market Overview", "market_overview"),
        ("Currency Explorer", "currency_explorer"),
        ("Volatility Lab", "volatility_lab"),
        ("Economic Insights", "economic_insights"),
        ("Data Pipeline", "data_pipeline"),
    ]
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = navigation_items[0][0]

    def select_navigation_page(label: str) -> None:
        st.session_state["selected_page"] = label

    with st.container(key="nav_menu"):
        for label, key in navigation_items:
            st.button(
                label,
                key=f"nav_{key}",
                type="primary" if st.session_state["selected_page"] == label else "secondary",
                use_container_width=True,
                on_click=select_navigation_page,
                args=(label,),
            )

    page = st.session_state["selected_page"]

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Subtle Footer
    st.markdown(
        """
        <div style="
            padding: 16px 6px 8px 6px;
            font-size: 0.7rem;
            color: #728492;
            border-top: 1px solid rgba(229, 222, 208, 0.1);
            line-height: 1.5;
        ">
            <div style="font-weight: 600; color: #8C9DA8;">FXFlow Platform · v2.1</div>
            <div style="font-size: 0.65rem; color: #627482;">Institutional FX Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── page routing ─────────────────────────────────────────────────────
import importlib

if page == "Market Overview":
    import fxflow.dashboard.page_overview as page_overview
    importlib.reload(page_overview)
    page_overview.render()

elif page == "Currency Explorer":
    import fxflow.dashboard.page_explorer as page_explorer
    importlib.reload(page_explorer)
    page_explorer.render()

elif page == "Volatility Lab":
    import fxflow.dashboard.page_volatility as page_volatility
    importlib.reload(page_volatility)
    page_volatility.render()

elif page == "Economic Insights":
    import fxflow.dashboard.page_economics as page_economics
    importlib.reload(page_economics)
    page_economics.render()

elif page == "Data Pipeline":
    import fxflow.dashboard.page_pipeline as page_pipeline
    importlib.reload(page_pipeline)
    page_pipeline.render()
