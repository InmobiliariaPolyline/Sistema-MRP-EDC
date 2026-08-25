# -*- coding: utf-8 -*-
"""
Utilidades de tema (dark / light mode).
Todas las páginas autenticadas obtienen el CSS via render_sidebar_menu().
La página de login lo aplica llamando apply_theme() directamente.
"""
import streamlit as st

_DARK_CSS = """
<style>
/* ════════════════════════ DARK MODE ════════════════════════ */
:root {
    --background-color:           #0f172a !important;
    --secondary-background-color: #1e293b !important;
    --text-color:                 #e2e8f0 !important;
    --primary-color:              #3b82f6 !important;
}

/* ── Fondo principal ── */
.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #0f172a !important;
    background-image:
        linear-gradient(180deg, rgba(30, 41, 59, .24), transparent 34rem),
        radial-gradient(circle at 100% 0, rgba(37, 99, 235, .08), transparent 34rem) !important;
}
[data-testid="stHeader"]            { background-color: #0f172a !important; }
[data-testid="stMain"]              { background-color: #0f172a !important; }
.block-container {
    background-color: transparent !important;
    max-width: 1480px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
}

/* ── Base visual system ── */
html, body, [class*="css"] {
    font-family: "Aptos", "Segoe UI", sans-serif !important;
    letter-spacing: 0 !important;
}
h1, h2, h3, h4, h5, h6 {
    letter-spacing: 0 !important;
    line-height: 1.2 !important;
}
[data-testid="stVerticalBlock"] { gap: .7rem; }
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stFormSubmitButton"] button {
    min-height: 2.45rem !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    transition: transform .16s ease, box-shadow .16s ease, background .16s ease !important;
}
[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(0, 0, 0, .22) !important;
}
[data-testid="stButton"] button:focus-visible,
[data-testid="stDownloadButton"] button:focus-visible,
[data-testid="stFormSubmitButton"] button:focus-visible {
    outline: 2px solid rgba(96, 165, 250, .75) !important;
    outline-offset: 2px !important;
}
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div,
[data-baseweb="select"] > div {
    min-height: 2.55rem;
    border-radius: 9px !important;
    transition: border-color .16s ease, box-shadow .16s ease !important;
}
[data-baseweb="input"] > div:focus-within,
[data-baseweb="textarea"] > div:focus-within,
[data-baseweb="select"] > div:focus-within {
    border-color: rgba(96, 165, 250, .85) !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, .16) !important;
}
[data-testid="stCaptionContainer"] { color: #94a3b8 !important; }
[data-testid="stAlert"] {
    border-radius: 10px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, .12) !important;
}

/* ── Texto ── */
p, span, li, h1, h2, h3, h4, h5, h6, label { color: #e2e8f0 !important; }
[data-testid="stMarkdownContainer"] *        { color: #e2e8f0 !important; }
label[data-testid="stWidgetLabel"] p         { color: #cbd5e1 !important; }

/* ── Inputs ── */
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
    background-color: #1e293b !important;
    border-color: #334155 !important;
}
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    color: #e2e8f0 !important;
    background-color: #1e293b !important;
}
[data-baseweb="input"] input::placeholder,
[data-baseweb="textarea"] textarea::placeholder { color: rgba(226,232,240,.35) !important; }

/* ── Select / dropdown ── */
[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    border-color: #334155 !important;
    color: #e2e8f0 !important;
}
[data-baseweb="popover"] ul           { background-color: #1e293b !important; }
[data-baseweb="option"]               { background-color: #1e293b !important; color: #e2e8f0 !important; }

/* ── Tabs ── */
[data-baseweb="tab-list"]                        { background-color: #1e293b !important; }
button[data-baseweb="tab"]                       { color: #94a3b8 !important; }
button[aria-selected="true"][data-baseweb="tab"] { background: #2563eb !important; color:#fff !important; }

/* ════════════════════════════════════════════════
   EXPANDERS — fondo oscuro, borde sutil, sin flash
   ════════════════════════════════════════════════ */
[data-testid="stExpander"],
details[data-testid="stExpander"] {
    background: rgba(6, 13, 28, 0.70) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    border-radius: 14px !important;
    box-shadow: none !important;
    overflow: hidden !important;
    transition: border-color .20s ease !important;
}
[data-testid="stExpander"]:hover,
details[data-testid="stExpander"]:hover {
    border-color: rgba(37, 99, 235, 0.35) !important;
}

/* Área de contenido expandido */
[data-testid="stExpanderDetails"] {
    background: rgba(6, 13, 28, 0.70) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.07) !important;
}

/* Cabecera / summary */
details[data-testid="stExpander"] > summary {
    background: transparent !important;
    color: #93c5fd !important;
    padding: .80rem 1.1rem !important;
    font-size: .88rem !important;
    font-weight: 700 !important;
    list-style: none !important;
    cursor: pointer !important;
    transition: background .15s ease !important;
}
details[data-testid="stExpander"] > summary:hover {
    background: rgba(255, 255, 255, 0.05) !important;
}
details[data-testid="stExpander"][open] > summary {
    border-bottom: 1px solid rgba(37, 99, 235, 0.15) !important;
}

/* Ícono de flecha — forzar blanco */
details[data-testid="stExpander"] > summary svg,
details[data-testid="stExpander"] > summary svg path,
details[data-testid="stExpander"] > summary svg polyline {
    stroke: #ffffff !important;
    fill: none !important;
    color: #ffffff !important;
}

/* ════════════════════════════════════════════════
   DATAFRAMES — oscuro nativo (base=dark en config)
   ════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.40) !important;
}
[data-testid="stDataFrame"] > div {
    background: rgba(10, 18, 35, 0.90) !important;
    border-radius: 14px !important;
}

/* ════════════════════════════════════════════════
   POPOVER (botón "Instrucciones") — Glassmorphism
   ════════════════════════════════════════════════ */
[data-testid="stPopoverBody"] {
    background: rgba(6, 13, 28, 0.92) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    box-shadow:
        0 8px 32px rgba(0, 0, 0, 0.55),
        0 0 0 1px rgba(37, 99, 235, 0.15) !important;
    border-radius: 14px !important;
}
[data-testid="stPopoverBody"] *            { color: #e2e8f0 !important; }
[data-testid="stPopoverBody"] h4           { color: #93c5fd !important; font-size: .95rem !important; }
[data-testid="stPopoverBody"] strong       { color: #f1f5f9 !important; }
[data-testid="stPopoverBody"] blockquote   {
    border-left: 3px solid rgba(37,99,235,.55) !important;
    background: rgba(37,99,235,.08) !important;
    padding: .45rem .75rem !important;
    border-radius: 0 8px 8px 0 !important;
    margin: .6rem 0 0 !important;
}
[data-testid="stPopoverBody"] blockquote p { color: #94a3b8 !important; font-size: .82rem !important; }

/* ── Alerts ── */
[data-testid="stAlert"]   { background-color: #1e293b !important; border-color: #334155 !important; }
[data-testid="stAlert"] p { color: #e2e8f0 !important; }

/* ── Metrics ── */
[data-testid="stMetric"]                        { background-color: #1e293b !important; }
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"]                   { color: #e2e8f0 !important; }

/* ── Login card ── */
.login-card { background: #1e293b !important; border-color: #334155 !important; }

/* ════════════════════════════════════════════════
   SCROLLBARS — finos, color azul oscuro
   ════════════════════════════════════════════════ */
::-webkit-scrollbar              { width: 5px; height: 5px; }
::-webkit-scrollbar-track        { background: transparent; }
::-webkit-scrollbar-thumb        { background: rgba(37, 99, 235, 0.38); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover  { background: rgba(37, 99, 235, 0.65); }
::-webkit-scrollbar-corner       { background: transparent; }
*                                { scrollbar-width: thin; scrollbar-color: rgba(37,99,235,.38) transparent; }
</style>
"""


def apply_theme() -> None:
    """Inyecta CSS de dark mode (siempre activo)."""
    st.markdown(_DARK_CSS, unsafe_allow_html=True)


def render_theme_toggle(key: str = "theme_toggle") -> None:
    """Botón toggle de tema. Úsalo en la barra lateral."""
    is_dark = st.session_state.get("dark_mode", False)
    label = "☀️  Modo Claro" if is_dark else "🌙  Modo Oscuro"
    if st.button(label, use_container_width=True, key=key):
        st.session_state.dark_mode = not is_dark
        st.rerun()


def render_theme_fab(key: str = "theme_fab") -> None:
    """Botón FAB para el login. Muestra icono SVG de sol o luna via CSS."""
    is_dark = st.session_state.get("dark_mode", False)

    if is_dark:
        # Sol (stroke claro para fondo oscuro)
        svg_url = (
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
            "width='18' height='18' viewBox='0 0 24 24' fill='none' "
            "stroke='%23e2e8f0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E"
            "%3Ccircle cx='12' cy='12' r='5'/%3E"
            "%3Cline x1='12' y1='1' x2='12' y2='3'/%3E"
            "%3Cline x1='12' y1='21' x2='12' y2='23'/%3E"
            "%3Cline x1='4.22' y1='4.22' x2='5.64' y2='5.64'/%3E"
            "%3Cline x1='18.36' y1='18.36' x2='19.78' y2='19.78'/%3E"
            "%3Cline x1='1' y1='12' x2='3' y2='12'/%3E"
            "%3Cline x1='21' y1='12' x2='23' y2='12'/%3E"
            "%3Cline x1='4.22' y1='19.78' x2='5.64' y2='18.36'/%3E"
            "%3Cline x1='18.36' y1='5.64' x2='19.78' y2='4.22'/%3E"
            "%3C/svg%3E"
        )
    else:
        # Luna (stroke oscuro para fondo claro)
        svg_url = (
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
            "width='18' height='18' viewBox='0 0 24 24' fill='none' "
            "stroke='%23475569' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E"
            "%3Cpath d='M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z'/%3E"
            "%3C/svg%3E"
        )

    st.markdown(f"""<style>
    .theme-fab [data-testid="stBaseButton-secondary"] {{
        background-image: url("{svg_url}") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 18px 18px !important;
    }}
    .theme-fab [data-testid="stBaseButton-secondary"] p {{
        visibility: hidden !important;
        font-size: 0 !important;
    }}
    </style>""", unsafe_allow_html=True)

    if st.button("·", key=key):
        st.session_state.dark_mode = not is_dark
        st.rerun()


def render_settings_gear(key: str = "settings_gear") -> None:
    """FAB de configuracion. Abre un popover con toggle de tema."""
    is_dark = st.session_state.get("dark_mode", False)
    with st.popover("Config"):
        st.markdown(
            "<p style='font-size:.82rem;font-weight:700;margin:0 0 .65rem;letter-spacing:.01em;'>"
            "Apariencia</p>",
            unsafe_allow_html=True,
        )
        mode_label = "Cambiar a modo claro" if is_dark else "Cambiar a modo oscuro"
        if st.button(mode_label, key=key, use_container_width=True):
            st.session_state.dark_mode = not is_dark
            st.rerun()
        current = "Oscuro" if is_dark else "Claro"
        st.caption(f"Modo actual: **{current}**")
