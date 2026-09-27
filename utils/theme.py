import streamlit as st


_SYSTEM_CSS = """
<style>
:root {
    --background-color: #f2f5f1 !important;
    --secondary-background-color: #ffffff !important;
    --text-color: #25342b !important;
    --primary-color: #31704f !important;
    --mrp-ink: #25342b;
    --mrp-muted: #66746a;
    --mrp-line: #dce4dc;
    --mrp-surface: #ffffff;
    --mrp-canvas: #f2f5f1;
    --mrp-green: #31704f;
    --mrp-copper: #b96332;
}
html, body, [class*="css"] { font-family: "Bahnschrift", "Aptos", "Segoe UI", sans-serif !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: #f2f5f1 !important;
    color: var(--mrp-ink) !important;
}
[data-testid="stHeader"] { background: rgba(242,245,241,.96) !important; }
.block-container { max-width: 1480px !important; padding: 1.4rem 2rem 3rem !important; }
[data-testid="stVerticalBlock"] { gap: .8rem; }
h1, h2, h3, h4, h5, h6 { color: #25342b !important; letter-spacing: 0 !important; line-height: 1.22 !important; }
p, span, li, label, [data-testid="stMarkdownContainer"] { color: #25342b; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: var(--mrp-muted) !important; }
label[data-testid="stWidgetLabel"] p { color: #45554a !important; font-size: .8rem !important; font-weight: 600 !important; }

section[data-testid="stSidebar"] { background: #1c2b22 !important; border-right: 1px solid #314237 !important; }
.sb-header { border-bottom: 1px solid rgba(255,255,255,.11) !important; }
.sb-logo { background: #c46b38 !important; animation: none !important; box-shadow: none !important; border-radius: 7px !important; }
.sb-avatar { background: #3f7655 !important; box-shadow: none !important; border-radius: 7px !important; }
.sb-user-row { background: rgba(255,255,255,.055) !important; border-color: rgba(255,255,255,.10) !important; border-radius: 7px !important; }
.sb-brand-name, .sb-user-name { color: #f3f6f2 !important; }
.sb-brand-sub, .sb-section { color: #a9b8ac !important; }
.sb-section::after { background: linear-gradient(90deg, rgba(255,255,255,.18), transparent) !important; }

[data-baseweb="input"] > div, [data-baseweb="textarea"] > div,
[data-baseweb="select"] > div, [data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input {
    background: #fff !important; border: 1px solid #cbd6cd !important;
    border-radius: 6px !important; color: #25342b !important;
}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea { color: #25342b !important; }
[data-baseweb="input"] input::placeholder, [data-baseweb="textarea"] textarea::placeholder { color: #849087 !important; }
[data-baseweb="input"] > div:focus-within, [data-baseweb="textarea"] > div:focus-within,
[data-baseweb="select"] > div:focus-within { border-color: #31704f !important; box-shadow: 0 0 0 2px rgba(49,112,79,.12) !important; }
[data-baseweb="popover"] ul, [data-baseweb="option"] { background: #fff !important; color: #25342b !important; }
[data-baseweb="option"]:hover { background: #edf4ee !important; }

[data-testid="stButton"] button, [data-testid="stDownloadButton"] button,
[data-testid="stFormSubmitButton"] button {
    min-height: 2.45rem !important; border-radius: 6px !important;
    font-weight: 650 !important; transition: background .15s ease, border-color .15s ease, transform .15s ease !important;
}
[data-testid="stBaseButton-primary"], [data-testid="stFormSubmitButton"] button {
    background: #31704f !important; border: 1px solid #31704f !important;
    color: #fff !important; box-shadow: none !important;
}
[data-testid="stBaseButton-primary"]:hover, [data-testid="stFormSubmitButton"] button:hover {
    background: #245b3e !important; border-color: #245b3e !important; transform: translateY(-1px) !important;
}
[data-testid="stBaseButton-secondary"] { background: #fff !important; border: 1px solid #cbd6cd !important; color: #34443a !important; }
[data-testid="stBaseButton-secondary"]:hover { background: #f2f6f2 !important; border-color: #9eafa2 !important; }
[data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #dce4dc !important; }
button[data-baseweb="tab"] { color: #66746a !important; }
button[aria-selected="true"][data-baseweb="tab"] { color: #245b3e !important; border-bottom-color: #31704f !important; }
[data-testid="stAlert"] { background: #fff !important; border: 1px solid #dce4dc !important; border-radius: 6px !important; }
[data-testid="stAlert"] p { color: #25342b !important; }

[data-testid="stDataFrame"], [data-testid="stTable"] { border: 1px solid #dce4dc !important; border-radius: 6px !important; overflow: hidden !important; box-shadow: none !important; }
[data-testid="stDataFrame"] > div { background: #fff !important; }
[data-testid="stMetric"] { background: #fff !important; border: 1px solid #dce4dc !important; border-left: 3px solid #548365 !important; border-radius: 6px !important; padding: .8rem 1rem !important; }
[data-testid="stMetricValue"] { color: #25342b !important; }
[data-testid="stMetricLabel"] { color: #66746a !important; }
[data-testid="stExpander"] { background: #fff !important; border: 1px solid #dce4dc !important; border-radius: 6px !important; }
[data-testid="stExpanderDetails"] { background: #fff !important; border-top-color: #e3e9e3 !important; }
details[data-testid="stExpander"] > summary { color: #34443a !important; }
details[data-testid="stExpander"] > summary:hover { background: #f5f8f5 !important; }

.op-hero, .dash-hero {
    background: #e7efe8 !important; border: 1px solid #d4e0d5 !important;
    border-left: 4px solid #31704f !important; border-radius: 7px !important; box-shadow: none !important;
}
.op-hero h1, .dash-hero h1 { color: #20372a !important; }
.op-hero p, .dash-hero p { color: #65736a !important; }
.op-hero-icon, .dash-hero-icon { background: #d7e7da !important; border-color: #c2d9c7 !important; }
.op-badge, .dash-hero-badge { background: #fff !important; border-color: #cad9cd !important; color: #3b6048 !important; }
.sec-title { border-left-color: #31704f !important; }
.sec-title svg { stroke: #31704f !important; }
.kpi-wrap { border-radius: 6px !important; box-shadow: none !important; }
.k-blue { background: #285c47 !important; }
.k-amber { background: #9a592e !important; }
.k-violet { background: #3f6862 !important; }
.k-teal { background: #46664c !important; }
.mat-info-card, .inv-card, .del-inv-card, .frozen-card {
    background: #fff !important; border-color: #dce4dc !important;
    border-radius: 6px !important; box-shadow: none !important;
}
.mat-info-card::before { background: #548365 !important; }
.mat-card-header { border-bottom-color: #e2e8e2 !important; }
.mat-card-name, .inv-wh { color: #25342b !important; }
.mat-id-chip { background: #edf4ee !important; border-color: #d3e2d5 !important; color: #356749 !important; }
.mat-field { background: #f6f8f6 !important; border-color: #e5eae5 !important; }
.mat-field-lbl, .inv-stat-lbl { color: #66746a !important; }
.mat-field-val { color: #25342b !important; }
.inv-mat { color: #356749 !important; }
.admin-hero, .logs-hero, .add-hero, .bud-hero {
    background: #e7efe8 !important; border: 1px solid #d4e0d5 !important;
    border-left: 4px solid #31704f !important; border-radius: 7px !important; box-shadow: none !important;
}
.admin-hero h1, .logs-hero h1, .add-hero h1, .bud-hero h1 { color: #20372a !important; }
.admin-hero p, .logs-hero p, .add-hero p, .bud-hero p { color: #65736a !important; }
.admin-badge, .logs-badge, .add-badge, .bud-badge {
    background: #fff !important; border-color: #cad9cd !important; color: #3b6048 !important;
}
.akpi, .bkpi { border-radius: 6px !important; box-shadow: none !important; }
.ak-violet, .bk-violet { background: #3f6862 !important; }
.ak-green, .bk-green { background: #285c47 !important; }
.ak-red, .bk-red { background: #9a4f42 !important; }
.user-card, .moves-wrap, .move-card, .edit-form-box, .wh-card, .req-card,
.disp-hist-card, .obra-mat-card, .bud-card, .add-card {
    background: #fff !important; border-color: #dce4dc !important;
    border-radius: 6px !important; box-shadow: none !important;
}
.user-card:hover, .move-card:hover, .wh-card:hover, .bud-card:hover, .add-card:hover { background: #f5f8f5 !important; }
.user-name, .user-email, .moves-title, .move-mat, .move-qty, .move-wh, .move-ts,
.move-ref, .edit-form-title, .wh-name, .req-card-title, .bud-card-name, .add-card-head {
    color: #25342b !important;
}
.user-avatar { background: #43815a !important; }
.edit-form-box, .pw-reqs { background: #f6f8f6 !important; border-color: #dce4dc !important; }
.pw-req-chip { background: #edf4ee !important; border-color: #d3e2d5 !important; color: #356749 !important; }
.badge-active { background: #e5f2e8 !important; color: #27613c !important; }
.badge-inactive { background: #fae9e6 !important; color: #923e34 !important; }
.help-fab { background: #1c2b22 !important; border-color: #314237 !important; }
.help-drawer { background: #fff !important; border-left-color: #dce4dc !important; }
.help-drawer-title { color: #25342b !important; }
.help-step { background: #f6f8f6 !important; border-color: #e1e8e1 !important; border-radius: 6px !important; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #c3cec4; border: 2px solid #f2f5f1; border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: #8c9b8f; }
@media (max-width: 768px) {
    .block-container { padding: 1rem .85rem 2rem !important; }
    .op-hero, .dash-hero { padding: .9rem 1rem !important; }
    .op-hero h1, .dash-hero h1 { font-size: 1.2rem !important; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; animation-duration: .01ms !important; transition-duration: .01ms !important; } }
</style>
"""

_DARK_MODE_OVERRIDES = """
<style>
:root {
    --background-color: #151a17 !important;
    --secondary-background-color: #202823 !important;
    --text-color: #e6ece7 !important;
    --primary-color: #6eaa7e !important;
    --mrp-ink: #e6ece7;
    --mrp-muted: #aeb9b1;
    --mrp-line: #3b4840;
    --mrp-surface: #202823;
    --mrp-canvas: #151a17;
    --mrp-green: #78b58a;
    --mrp-copper: #e29a64;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #151a17 !important; color: #e6ece7 !important; }
[data-testid="stHeader"] { background: rgba(21,26,23,.97) !important; }
h1, h2, h3, h4, h5, h6 { color: #edf2ee !important; }
p, span, li, label, [data-testid="stMarkdownContainer"] * { color: #e0e8e1 !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #aeb9b1 !important; }
label[data-testid="stWidgetLabel"] p { color: #c9d4cb !important; }

[data-baseweb="input"] > div, [data-baseweb="textarea"] > div,
[data-baseweb="select"] > div, [data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input { background: #202823 !important; border-color: #46544a !important; color: #e6ece7 !important; }
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea { color: #e6ece7 !important; }
[data-baseweb="input"] input::placeholder, [data-baseweb="textarea"] textarea::placeholder { color: #a2aea5 !important; }
[data-baseweb="input"] > div:focus-within, [data-baseweb="textarea"] > div:focus-within,
[data-baseweb="select"] > div:focus-within { border-color: #78b58a !important; box-shadow: 0 0 0 2px rgba(120,181,138,.18) !important; }
[data-baseweb="popover"] ul, [data-baseweb="option"] { background: #202823 !important; color: #e6ece7 !important; }
[data-baseweb="option"]:hover { background: #354139 !important; }

[data-testid="stBaseButton-primary"], [data-testid="stFormSubmitButton"] button { background: #3b7954 !important; border-color: #5c9b70 !important; color: #fff !important; }
[data-testid="stBaseButton-primary"]:hover, [data-testid="stFormSubmitButton"] button:hover { background: #4a8c62 !important; }
[data-testid="stBaseButton-secondary"] { background: #252e28 !important; border-color: #46544a !important; color: #e2e9e3 !important; }
[data-testid="stBaseButton-secondary"]:hover { background: #303b33 !important; border-color: #718276 !important; }
[data-baseweb="tab-list"] { background: #202823 !important; border-bottom-color: #3b4840 !important; }
button[data-baseweb="tab"] { color: #b7c2b9 !important; }
button[aria-selected="true"][data-baseweb="tab"] { color: #a8d4b1 !important; border-bottom-color: #78b58a !important; }
[data-testid="stAlert"] { background: #202823 !important; border-color: #46544a !important; }
[data-testid="stAlert"] p { color: #e6ece7 !important; }
[data-testid="stDataFrame"], [data-testid="stTable"] { border-color: #3b4840 !important; }
[data-testid="stDataFrame"] > div { background: #202823 !important; }
[data-testid="stMetric"] { background: #202823 !important; border-color: #3b4840 !important; border-left-color: #78b58a !important; }
[data-testid="stMetricValue"] { color: #edf2ee !important; }
[data-testid="stMetricLabel"] { color: #aeb9b1 !important; }
[data-testid="stExpander"], [data-testid="stExpanderDetails"] { background: #202823 !important; border-color: #3b4840 !important; }
details[data-testid="stExpander"] > summary { color: #e0e8e1 !important; }

.op-hero, .dash-hero, .admin-hero, .logs-hero, .add-hero, .bud-hero {
    background: #26352c !important; border-color: #405347 !important; border-left-color: #78b58a !important;
}
.op-hero h1, .dash-hero h1, .admin-hero h1, .logs-hero h1, .add-hero h1, .bud-hero h1 { color: #eff4ef !important; }
.op-hero p, .dash-hero p, .admin-hero p, .logs-hero p, .add-hero p, .bud-hero p { color: #bdc9bf !important; }
.op-badge, .dash-hero-badge, .admin-badge, .logs-badge, .add-badge, .bud-badge { background: #202823 !important; border-color: #536357 !important; color: #e6ece7 !important; }
.sec-title { border-left-color: #78b58a !important; color: #e6ece7 !important; }
.sec-title svg { stroke: #78b58a !important; }
.mat-info-card, .inv-card, .del-inv-card, .frozen-card, .user-card, .moves-wrap,
.move-card, .edit-form-box, .wh-card, .req-card, .disp-hist-card,
.obra-mat-card, .bud-card, .add-card { background: #202823 !important; border-color: #3b4840 !important; }
.mat-card-name, .inv-wh, .mat-field-val, .user-name, .user-email, .moves-title,
.move-mat, .move-qty, .move-wh, .move-ts, .move-ref, .edit-form-title { color: #e0e8e1 !important; }
.mat-field { background: #18201b !important; border-color: #344138 !important; }
.mat-field-lbl, .inv-stat-lbl { color: #aeb9b1 !important; }
.mat-id-chip, .pw-req-chip { background: #29392e !important; border-color: #435a49 !important; color: #b9ddc1 !important; }
.help-drawer { background: #202823 !important; border-left-color: #3b4840 !important; }
.help-drawer-title { color: #edf2ee !important; }
.help-step { background: #252e28 !important; border-color: #3b4840 !important; }
::-webkit-scrollbar-thumb { background: #64746a; border-color: #151a17; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition-duration: .01ms !important; } }
</style>
"""

_PUBLIC_THEME_CSS = """
<style>
.stApp { background: #f1f4ef !important; }
[data-testid="stAppViewContainer"] { background: transparent !important; }
.block-container {
    width: min(440px, calc(100vw - 2rem)) !important; max-width: 440px !important;
    height: auto !important; min-height: 0 !important; margin: 4vh auto !important;
    padding: 0 1rem 1.5rem !important; background: #fff !important;
    border: 1px solid #dce4dc !important; border-top: 3px solid #31704f !important;
    border-radius: 8px !important; box-shadow: 0 18px 48px rgba(34,54,41,.10) !important;
}
p, span, li, label, div { color: #25342b; }
.hero-icon-outer { background: #31704f !important; border-radius: 8px !important; box-shadow: none !important; animation: none !important; }
.hero-badge { background: #edf5ef !important; border-color: #cddfd2 !important; }
.hero-badge-dot { background: #31704f !important; box-shadow: none !important; }
.hero-badge-text { color: #31704f !important; }
.hero-title { background: none !important; color: #20372a !important; -webkit-text-fill-color: #20372a !important; }
.hero-sub { color: #65736a !important; }
.form-divider-line { background: #dce4dc !important; }
.form-divider-label, .strength-section-label { color: #718077 !important; }
label[data-testid="stWidgetLabel"] p { color: #44544a !important; }
[data-baseweb="input"] > div { background: #fff !important; border-color: #cbd6cd !important; border-radius: 6px !important; }
[data-baseweb="input"] > div:focus-within { border-color: #31704f !important; box-shadow: 0 0 0 2px rgba(49,112,79,.14) !important; }
[data-baseweb="input"] input { color: #25342b !important; }
[data-baseweb="input"] input::placeholder { color: #849087 !important; }
[data-testid="stFormSubmitButton"] button, [data-testid="stBaseButton-primary"] { background: #31704f !important; border: 1px solid #31704f !important; border-radius: 6px !important; box-shadow: none !important; color: #fff !important; }
[data-testid="stPageLink"] a { color: #31704f !important; }
.info-note { background: #f6f8f5 !important; border-color: #dce4dc !important; border-radius: 6px !important; }
.info-note-text, .info-note-text strong { color: #65736a !important; }
.warn-banner { background: #fff5e8 !important; border-color: #f0d4a9 !important; }
.warn-banner-text { color: #895018 !important; }
[data-testid="stAlert"] { background: #f6f8f5 !important; border-color: #dce4dc !important; }
[data-testid="stAlert"] p { color: #25342b !important; }
@media (max-width: 520px) { .block-container { margin: 1rem auto !important; padding: 0 .85rem 1.2rem !important; } .login-hero, .reg-hero { padding-top: 1.5rem !important; } }
</style>
"""


def apply_theme() -> None:
    """Aplica el tema de operación a las páginas autenticadas."""
    css = _SYSTEM_CSS
    if st.session_state.get("dark_mode", False):
        css += _DARK_MODE_OVERRIDES
    st.markdown(css, unsafe_allow_html=True)


def apply_public_theme() -> None:
    """Aplica el tema a las páginas de acceso y registro."""
    st.markdown(_PUBLIC_THEME_CSS, unsafe_allow_html=True)


def render_theme_toggle(key: str = "theme_toggle") -> None:
    is_dark = st.session_state.get("dark_mode", False)
    label = "☀ Modo claro" if is_dark else "◐ Modo oscuro"
    if st.button(label, use_container_width=True, key=key):
        st.session_state.dark_mode = not is_dark
        st.rerun()


def render_theme_fab(key: str = "theme_fab") -> None:
    render_theme_toggle(key=key)


def render_settings_gear(key: str = "settings_gear") -> None:
    is_dark = st.session_state.get("dark_mode", False)
    with st.popover("Apariencia"):
        mode_label = "Cambiar a modo claro" if is_dark else "Cambiar a modo oscuro"
        if st.button(mode_label, key=key, use_container_width=True):
            st.session_state.dark_mode = not is_dark
            st.rerun()
        st.caption(f"Modo actual: {'Oscuro' if is_dark else 'Claro'}")
