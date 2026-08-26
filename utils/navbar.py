import streamlit as st

_PAGE_KEYS = {
    "pages/dashboard.py":       "menu_dashboard",
    "pages/warehouses.py":      "menu_warehouses",
    "pages/materials.py":       "menu_materials",
    "pages/requirements.py":    "menu_requirements",
    "pages/receipts.py":        "menu_receipts",
    "pages/dispatches.py":      "menu_dispatches",
    "pages/inventory.py":       "menu_inventory",
    "pages/inventory_obra.py":  "menu_inventory_obra",
    "pages/access_logs.py":     "menu_access_logs",
    "pages/presupuestos.py":    "menu_presupuestos",
    "pages/adicional.py":       "menu_adicional",
}

def _apply_theme():
    try:
        from utils.theme import apply_theme
        apply_theme()
    except Exception:
        pass

def _current_page() -> str:
    try:
        path = st.context.headers.get("Referer", "")
        for k in _PAGE_KEYS:
            slug = k.replace("pages/", "").replace(".py", "").replace("_", "-")
            if slug in path.lower():
                return k
    except Exception:
        pass
    return st.session_state.get("_current_page", "")

def render_navbar():
    """Oculta la navegación nativa y mantiene estable la transición entre páginas."""
    st.markdown("""
    <style>
    /* Oculta el nav nativo inmediatamente — múltiples selectores para mayor cobertura */
    [data-testid='stSidebarNav'],
    [data-testid='stSidebarNavItems'],
    [data-testid='stSidebarNavLink'],
    [data-testid='stSidebarNavSeparator'],
    nav[data-testid='stSidebarNav'],
    [data-testid='stSidebar'] > div > ul,
    [data-testid='stSidebar'] nav {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    /* El sidebar debe estar disponible desde el primer instante de la carga. */
    section[data-testid='stSidebar'] {
        opacity: 1;
    }

    /* Entrada breve: evita el parpadeo sin ocultar el contenido durante la carga. */
    @keyframes _pg_in {
        from { opacity: 0.92; }
        to   { opacity: 1; }
    }
    [data-testid="stMain"] {
        animation: _pg_in 0.16s ease-out both;
    }
    @media (prefers-reduced-motion: reduce) {
        [data-testid="stMain"] { animation: none; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_help_button(content_html: str) -> None:
    """Botón flotante de ayuda (?) que abre un drawer lateral con instrucciones de solo lectura."""
    st.markdown(f"""
    <style>
    .help-fab {{
        position: fixed; bottom: 1.3rem; right: 1.3rem; z-index: 9998;
        width: 44px; height: 44px; border-radius: 13px;
        background: rgba(10,22,40,.90); backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,.13); color: rgba(240,246,252,.90);
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1.1rem; font-weight: 800;
        box-shadow: 0 4px 20px rgba(0,0,0,.38), 0 0 0 1px rgba(37,99,235,.20);
        transition: all 0.2s cubic-bezier(.34,1.56,.64,1);
        user-select: none; font-family: sans-serif;
    }}
    .help-fab:hover {{
        transform: scale(1.10);
        background: rgba(37,99,235,.85);
        box-shadow: 0 6px 28px rgba(37,99,235,.45), 0 0 0 1px rgba(37,99,235,.50);
    }}
    .help-drawer {{
        position: fixed; top: 0; right: -400px; width: 370px; height: 100vh;
        background: rgba(6,12,26,.97); border-left: 1px solid rgba(255,255,255,.09);
        backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
        z-index: 9997; padding: 1.6rem 1.4rem;
        overflow-y: auto; overflow-x: hidden;
        transition: right 0.32s cubic-bezier(.22,1,.36,1);
        box-shadow: -12px 0 48px rgba(0,0,0,.48);
    }}
    .help-drawer.open {{ right: 0; }}
    .help-close {{
        position: absolute; top: 1rem; right: 1rem;
        background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.10);
        color: #94a3b8; cursor: pointer; width: 28px; height: 28px; border-radius: 7px;
        display: flex; align-items: center; justify-content: center; font-size: .85rem;
        transition: all .15s;
    }}
    .help-close:hover {{ background: rgba(255,255,255,.14); color: #e2e8f0; }}
    .help-drawer-title {{
        font-size: 1.05rem; font-weight: 800; color: #f1f5f9;
        margin: 0 2.2rem .3rem 0; line-height: 1.3;
    }}
    .help-drawer-badge {{
        display: inline-block; padding: .18rem .58rem;
        border-radius: 20px; font-size: .63rem; font-weight: 700;
        background: rgba(37,99,235,.14); border: 1px solid rgba(37,99,235,.24);
        color: #60a5fa; letter-spacing: .08em; text-transform: uppercase;
        margin-bottom: .85rem;
    }}
    .help-sec {{
        font-size: .63rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: .13em;
        color: rgba(148,163,184,.50);
        display: flex; align-items: center; gap: .45rem;
        margin: 1rem 0 .45rem;
    }}
    .help-sec::after {{
        content: ""; flex: 1; height: 1px; background: rgba(255,255,255,.07);
    }}
    .help-step {{
        display: flex; gap: .6rem; padding: .45rem .65rem;
        border-radius: 9px; border: 1px solid rgba(255,255,255,.055);
        background: rgba(255,255,255,.025); margin-bottom: .32rem;
    }}
    .help-step-n {{
        width: 20px; height: 20px; border-radius: 6px; flex-shrink: 0;
        background: rgba(37,99,235,.20); border: 1px solid rgba(37,99,235,.25);
        color: #60a5fa; font-size: .68rem; font-weight: 800;
        display: flex; align-items: center; justify-content: center;
    }}
    .help-step-t {{ font-size: .79rem; color: #cbd5e1; line-height: 1.5; }}
    .help-tip {{
        display: flex; gap: .5rem; padding: .5rem .65rem;
        border-radius: 9px; background: rgba(245,158,11,.06);
        border: 1px solid rgba(245,158,11,.14); margin-top: .6rem;
    }}
    .help-tip-t {{ font-size: .75rem; color: #d97706; line-height: 1.48; }}
    </style>

    <div class="help-fab" onclick="document.getElementById('__hd__').classList.toggle('open')" title="Ayuda &amp; Guía">?</div>

    <div id="__hd__" class="help-drawer">
        <div class="help-close" onclick="document.getElementById('__hd__').classList.remove('open')">&#10005;</div>
        {content_html}
    </div>
    """, unsafe_allow_html=True)

def render_sidebar_menu():
    """Renderiza el sidebar personalizado."""
    _apply_theme()

    st.markdown("""
    <style>
    /* ═══════════════════════════════════════════════════════════════
       BASE — layout fijo, sin scroll visible
    ═══════════════════════════════════════════════════════════════ */
    [data-testid="stSidebarNav"] { display: none !important; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1226 0%, #090d1c 55%, #060818 100%) !important;
        border-right: 1px solid rgba(99,102,241,.10) !important;
        overflow:     hidden !important;
    }
    section[data-testid="stSidebar"]::-webkit-scrollbar,
    section[data-testid="stSidebar"]                    { scrollbar-width: none !important; }

    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        position: relative !important; height: 100dvh !important;
        overflow: hidden !important; padding: 0 !important;
        background: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div {
        position: absolute !important; inset: 0 !important;
        padding: 0 !important; margin: 0 !important;
        overflow: hidden !important; height: 100% !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div > div:not([data-testid="stVerticalBlock"]) {
        height: 100% !important; padding: 0 !important; margin: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div > [data-testid="stVerticalBlock"],
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div > div > [data-testid="stVerticalBlock"] {
        display: flex !important; flex-direction: column !important;
        align-items: stretch !important; height: 100dvh !important;
        padding: 0 !important; margin: 0 !important;
        gap: 0 !important; overflow: hidden !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] [data-testid="stVerticalBlock"] {
        height: auto !important; min-height: 0 !important;
        display: block !important; overflow: visible !important;
    }
    section[data-testid="stSidebar"] [data-testid="stElementContainer"] {
        padding: 0 !important; margin: 0 !important; flex-shrink: 0 !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       HEADER
    ═══════════════════════════════════════════════════════════════ */
    .sb-header {
        padding: .95rem 1rem .85rem;
        border-bottom: 1px solid rgba(255,255,255,.055);
        flex-shrink: 0;
    }
    .sb-brand-row {
        display: flex; align-items: center; gap: .72rem;
        margin-bottom: .72rem;
    }
    @keyframes sb-logo-glow {
        0%, 100% { box-shadow: 0 0 0 1px rgba(124,58,237,.30), 0 4px 16px rgba(79,70,229,.38), 0 1px 3px rgba(0,0,0,.4); }
        50%       { box-shadow: 0 0 0 1px rgba(124,58,237,.50), 0 4px 22px rgba(99,102,241,.60), 0 1px 3px rgba(0,0,0,.4); }
    }
    .sb-logo {
        width: 36px; height: 36px; flex-shrink: 0;
        background: linear-gradient(140deg, #1e40af 0%, #4f46e5 50%, #7c3aed 100%);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        animation: sb-logo-glow 3.6s ease-in-out infinite;
    }
    .sb-logo-mark {
        display: grid; grid-template-columns: 1fr 1fr; gap: 3.5px;
    }
    .sb-logo-mark span { display: block; width: 9.5px; height: 9.5px; border-radius: 2.5px; }
    .slm-1 { background: #fff; }
    .slm-2 { background: rgba(255,255,255,.35); }
    .slm-3 { background: rgba(255,255,255,.35); }
    .slm-4 { background: #fff; }

    .sb-brand-text { min-width: 0; }
    .sb-brand-name {
        font-size: .94rem; font-weight: 700;
        color: #f1f5f9; margin: 0; line-height: 1.2; letter-spacing: -.018em;
    }
    .sb-brand-sub {
        font-size: .64rem; color: rgba(241,245,249,.28);
        margin: 2px 0 0; letter-spacing: .07em; text-transform: uppercase;
    }

    .sb-user-row {
        display: flex; align-items: center; gap: .6rem;
        background: rgba(99,102,241,.07);
        border: 1px solid rgba(99,102,241,.16);
        border-radius: 10px;
        padding: .48rem .65rem;
        transition: background .18s, border-color .18s;
    }
    .sb-user-row:hover {
        background: rgba(99,102,241,.12);
        border-color: rgba(99,102,241,.26);
    }
    .sb-avatar {
        width: 30px; height: 30px; flex-shrink: 0;
        background: linear-gradient(140deg, #2563eb 0%, #7c3aed 100%);
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: .76rem; font-weight: 800; color: #fff;
        box-shadow: 0 2px 8px rgba(124,58,237,.35);
    }
    .sb-user-info { flex: 1; min-width: 0; }
    .sb-user-name {
        font-size: .80rem; font-weight: 600; color: #e2e8f0;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.3;
    }
    .sb-user-role { font-size: .62rem; letter-spacing: .03em; line-height: 1.2; margin-top: 1px; }
    .sb-status-dot {
        width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
        background: #22c55e;
        box-shadow: 0 0 0 2px rgba(34,197,94,.18), 0 0 8px rgba(34,197,94,.45);
    }

    /* ═══════════════════════════════════════════════════════════════
       SECCIONES DE NAVEGACIÓN
    ═══════════════════════════════════════════════════════════════ */
    .sb-section {
        display: flex; align-items: center; gap: .5rem;
        font-size: .58rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: .13em;
        color: rgba(241,245,249,.28) !important;
        padding: 1rem 1rem .3rem; margin: 0;
    }
    .sb-section::after {
        content: ""; flex: 1; height: 1px;
        background: linear-gradient(90deg, rgba(255,255,255,.09), transparent);
    }

    /* ── Contenedor de botones nav: inset horizontal ── */
    section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(
        button[data-testid="stBaseButton-secondary"]
    ) {
        padding: 0 .5rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(
        button[data-testid="stBaseButton-primary"]
    ) {
        padding: 0 .5rem !important;
    }

    /* ── Botón inactivo ── */
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        border-radius: 8px !important;
        border: none !important;
        font-size: .835rem !important;
        font-weight: 500 !important;
        padding: .58rem .8rem !important;
        text-align: left !important;
        margin-bottom: 1px !important;
        width: 100% !important;
        letter-spacing: .005em !important;
        color: rgba(226,232,240,.58) !important;
        background: transparent !important;
        transition: background .13s ease, color .13s ease !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
        background: rgba(255,255,255,.075) !important;
        color: #f1f5f9 !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:focus-visible {
        outline: 2px solid rgba(99,102,241,.55) !important; outline-offset: 1px !important;
    }

    /* ── Botón activo ── */
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
        border-radius: 8px !important;
        border: none !important;
        font-size: .835rem !important;
        font-weight: 600 !important;
        padding: .58rem .8rem !important;
        text-align: left !important;
        margin-bottom: 1px !important;
        width: 100% !important;
        letter-spacing: .005em !important;
        background: linear-gradient(90deg, rgba(99,102,241,.22), rgba(124,58,237,.08)) !important;
        color: #c7d2fe !important;
        box-shadow:
            inset 3px 0 0 #818cf8,
            inset 0 0 0 1px rgba(99,102,241,.18),
            0 2px 12px rgba(99,102,241,.10) !important;
    }

    /* ── Iconos SVG via data-nav ── */
    [data-testid="stSidebar"] button[data-nav] {
        display: flex !important; align-items: center !important;
    }
    [data-testid="stSidebar"] button[data-nav]::before {
        content: ""; flex-shrink: 0; display: inline-block;
        width: 15px; height: 15px; margin-right: 9px;
        background: center / contain no-repeat; opacity: .58;
        transition: opacity .13s;
    }
    [data-testid="stSidebar"] button[data-nav]:hover::before,
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"][data-nav]::before {
        opacity: 1;
    }
    [data-testid="stSidebar"] button[data-nav="dashboard"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23a5b4fc' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='7' height='7'/%3E%3Crect x='14' y='3' width='7' height='7'/%3E%3Crect x='14' y='14' width='7' height='7'/%3E%3Crect x='3' y='14' width='7' height='7'/%3E%3C/svg%3E");
        opacity: .7;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"][data-nav="dashboard"]::before { opacity: 1; }
    [data-testid="stSidebar"] button[data-nav="warehouses"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e2e8f0' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/%3E%3Cpolyline points='9 22 9 12 15 12 15 22'/%3E%3C/svg%3E");
    }
    [data-testid="stSidebar"] button[data-nav="materials"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e2e8f0' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'/%3E%3Cpolyline points='3.27 6.96 12 12.01 20.73 6.96'/%3E%3Cline x1='12' y1='22.08' x2='12' y2='12'/%3E%3C/svg%3E");
    }
    [data-testid="stSidebar"] button[data-nav="requirements"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e2e8f0' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2'/%3E%3Crect x='8' y='2' width='8' height='4' rx='1'/%3E%3Cline x1='9' y1='12' x2='15' y2='12'/%3E%3Cline x1='9' y1='16' x2='13' y2='16'/%3E%3C/svg%3E");
    }
    [data-testid="stSidebar"] button[data-nav="receipts"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e2e8f0' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpolyline points='14 2 14 8 20 8'/%3E%3Cline x1='12' y1='18' x2='12' y2='12'/%3E%3Cpolyline points='15 15 12 18 9 15'/%3E%3C/svg%3E");
    }
    [data-testid="stSidebar"] button[data-nav="dispatches"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e2e8f0' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='1' y='3' width='15' height='13'/%3E%3Cpolygon points='16 8 20 8 23 11 23 16 16 16 16 8'/%3E%3Ccircle cx='5.5' cy='18.5' r='2.5'/%3E%3Ccircle cx='18.5' cy='18.5' r='2.5'/%3E%3C/svg%3E");
    }
    [data-testid="stSidebar"] button[data-nav="inventory"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e2e8f0' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='18' y1='20' x2='18' y2='10'/%3E%3Cline x1='12' y1='20' x2='12' y2='4'/%3E%3Cline x1='6' y1='20' x2='6' y2='14'/%3E%3C/svg%3E");
    }
    [data-testid="stSidebar"] button[data-nav="inventory_obra"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232dd4bf' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/%3E%3Cline x1='9' y1='22' x2='9' y2='16'/%3E%3Cline x1='15' y1='22' x2='15' y2='16'/%3E%3Cline x1='9' y1='12' x2='15' y2='12'/%3E%3C/svg%3E");
        opacity: .75;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"][data-nav="inventory_obra"]::before {
        opacity: 1;
    }
    [data-testid="stSidebar"] button[data-nav="presupuestos"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2334d399' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='12' y1='1' x2='12' y2='23'/%3E%3Cpath d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/%3E%3C/svg%3E");
        opacity: .75;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"][data-nav="presupuestos"]::before {
        opacity: 1;
    }
    [data-testid="stSidebar"] button[data-nav="adicional"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fbbf24' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='12' y1='8' x2='12' y2='16'/%3E%3Cline x1='8' y1='12' x2='16' y2='12'/%3E%3C/svg%3E");
        opacity: .75;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"][data-nav="adicional"]::before {
        opacity: 1;
    }
    [data-testid="stSidebar"] button[data-nav="access_logs"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fbbf24' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z'/%3E%3Cpath d='M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z'/%3E%3C/svg%3E");
        opacity: .75;
    }
    [data-testid="stSidebar"] button[data-nav="admin"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23fbbf24' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='9' cy='7' r='4'/%3E%3Cpath d='M23 21v-2a4 4 0 0 0-3-3.87'/%3E%3Cpath d='M16 3.13a4 4 0 0 1 0 7.75'/%3E%3C/svg%3E");
        opacity: .75;
    }
    [data-testid="stSidebar"] button[data-nav="logout"]::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23f87171' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4'/%3E%3Cpolyline points='16 17 21 12 16 7'/%3E%3Cline x1='21' y1='12' x2='9' y2='12'/%3E%3C/svg%3E");
        opacity: .68;
    }

    /* ═══════════════════════════════════════════════════════════════
       SPACER + FOOTER ANCLADO AL FONDO
    ═══════════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sb-divider) {
        flex-grow: 1 !important; flex-shrink: 1 !important;
        min-height: 0 !important; height: 0 !important;
        padding: 0 !important; margin: 0 !important; overflow: hidden !important;
    }

    /* Fondo unificado para todos los elementos debajo del spacer */
    section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sb-divider)
    ~ [data-testid="stElementContainer"] {
        background: rgba(255,255,255,.02) !important;
    }

    /* 1er sibling: cerrar sesión */
    section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sb-divider)
    + [data-testid="stElementContainer"] {
        border-top: 1px solid rgba(255,255,255,.065) !important;
        padding: .38rem .5rem .3rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sb-divider)
    + [data-testid="stElementContainer"] [data-testid="stBaseButton-secondary"] {
        color: rgba(248,113,113,.75) !important;
        font-size: .78rem !important; font-weight: 500 !important;
        background: transparent !important; border: none !important;
        padding: .48rem .8rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sb-divider)
    + [data-testid="stElementContainer"] [data-testid="stBaseButton-secondary"]:hover {
        background: rgba(239,68,68,.10) !important;
        color: #fca5a5 !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       IMPERSONATION BANNER
    ═══════════════════════════════════════════════════════════════ */
    .sb-imp-banner {
        display: flex; align-items: center; gap: .5rem;
        background: rgba(245,158,11,.10);
        border: 1px solid rgba(245,158,11,.28);
        border-radius: 10px;
        padding: .48rem .75rem;
        margin: .3rem .5rem .1rem;
        font-size: .73rem; color: #fbbf24; font-weight: 600;
    }
    .sb-imp-banner::before {
        content: ""; display: inline-block;
        width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
        background: #f59e0b;
        box-shadow: 0 0 0 2px rgba(245,158,11,.22), 0 0 8px rgba(245,158,11,.40);
        animation: _imp_pulse 1.8s ease-in-out infinite;
    }
    @keyframes _imp_pulse {
        0%, 100% { opacity: 1; } 50% { opacity: .45; }
    }

    /* Botón "Salir de vista" */
    section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(button[data-nav="exit_imp"]) {
        padding: .15rem .5rem .3rem !important;
    }
    section[data-testid="stSidebar"] button[data-nav="exit_imp"] {
        background: rgba(245,158,11,.12) !important;
        color: #fbbf24 !important;
        border: 1px solid rgba(245,158,11,.28) !important;
        border-radius: 8px !important;
        font-size: .76rem !important; font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] button[data-nav="exit_imp"]:hover {
        background: rgba(245,158,11,.22) !important;
        color: #fde68a !important;
    }

    /* Avatar impersonado */
    .sb-avatar-imp {
        background: linear-gradient(140deg, #d97706 0%, #f59e0b 100%) !important;
        box-shadow: 0 2px 8px rgba(245,158,11,.35) !important;
    }

    /* ── Espaciado extra entre secciones del superadmin ── */
    .sb-section-gap { height: .5rem; display: block; }

    /* Ajustes responsive sin cambiar la estructura del menú. */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            width: min(86vw, 19rem) !important;
        }
        .sb-header { padding: .8rem .85rem .7rem; }
        .sb-section { padding-left: .85rem; padding-right: .85rem; }
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
        [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
            min-height: 2.55rem !important;
        }
    }

    </style>
    """, unsafe_allow_html=True)

    # El menú mantiene sus botones; este script solo agrega sus iconos y estados.
    # Se usa un observador porque Streamlit vuelve a crear los botones al navegar.
    st.markdown("""
    <script>
    (function(){
      var N={
        'Dashboard':'dashboard','Almacenes':'warehouses','Materiales':'materials',
        'Requerimientos':'requirements','Recepciones':'receipts','Despachos':'dispatches',
        'Inventario Principal':'inventory','Inventario Obra':'inventory_obra',
    'Logs de Acceso':'access_logs','Cerrar sesión':'logout',
        'Panel de Usuarios':'admin','← Salir de vista':'exit_imp',
        'Presupuestos':'presupuestos','Adicional':'adicional'
      };
      function tag(){
        document.querySelectorAll('[data-testid="stSidebar"] button').forEach(function(b){
          var t=b.textContent.trim().replace(/\\s+/g,' ');
          if(N[t]) b.dataset.nav=N[t];
        });
      }
      tag();
      var obs=new MutationObserver(tag);
      var sb=document.querySelector('[data-testid="stSidebar"]');
      if(sb) obs.observe(sb,{childList:true,subtree:true});
      setTimeout(tag,200); setTimeout(tag,600);
    })();
    </script>
    """, unsafe_allow_html=True)

    logged_in = st.session_state.get("logged_in", False)
    if not logged_in:
        return

    username            = st.session_state.get("username", "Usuario")
    role                = st.session_state.get("role", "cliente")
    is_impersonating    = st.session_state.get("impersonating", False)
    imp_username        = st.session_state.get("impersonating_username", "")
    active              = _current_page()

    # Decide qué identidad mostrar en el header
    if is_impersonating:
        display_name    = imp_username
        display_initials= imp_username[0].upper() if imp_username else "C"
        role_label      = "Vista Cliente"
        role_color      = "#f59e0b"
        avatar_extra    = " sb-avatar-imp"
    else:
        display_name    = username
        display_initials= username[0].upper() if username else "U"
        role_label      = "Super Admin" if role == "superadmin" else "Cliente"
        role_color      = "#fbbf24" if role == "superadmin" else "rgba(241,245,249,.36)"
        avatar_extra    = ""

    # ── Header ───────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="sb-header">
      <div class="sb-brand-row">
        <div class="sb-logo">
          <div class="sb-logo-mark">
            <span class="slm-1"></span><span class="slm-2"></span>
            <span class="slm-3"></span><span class="slm-4"></span>
          </div>
        </div>
        <div class="sb-brand-text">
                <a href="/">
          <p class="sb-brand-name">Sistema MRP</p>
          <p class="sb-brand-sub">Gestión de Recursos</p>
                </a>
        </div>
      </div>
      <div class="sb-user-row">
        <div class="sb-avatar{avatar_extra}">{display_initials}</div>
        <div class="sb-user-info">
          <div class="sb-user-name">{display_name}</div>
          <div class="sb-user-role" style="color:{role_color};font-weight:600;">{role_label}</div>
        </div>
        <div class="sb-status-dot"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Banner + botón de salida cuando se impersona ─────────────────────────
    if is_impersonating:
        if st.button("← Salir de vista", key="exit_impersonation", use_container_width=True):
            st.session_state.pop("impersonating", None)
            st.session_state.pop("impersonating_user_id", None)
            st.session_state.pop("impersonating_username", None)
            st.switch_page("pages/admin.py")
        st.markdown(
            f'<div class="sb-imp-banner">Viendo cuenta: <b>{imp_username}</b></div>',
            unsafe_allow_html=True,
        )

    def _btn(label: str, page: str, key: str):
        t = "primary" if (active == page) else "secondary"
        if st.button(label, use_container_width=True, key=key, type=t):
            st.session_state["_current_page"] = page
            st.switch_page(page)

    def _operations_menu(enabled: bool = True):
        """Muestra Operaciones y evita abrir formularios sin cliente seleccionado."""
        st.markdown('<p class="sb-section">Operaciones</p>', unsafe_allow_html=True)
        operation_items = (
            ("Almacenes", "pages/warehouses.py", "menu_warehouses"),
            ("Materiales", "pages/materials.py", "menu_materials"),
            ("Inventario Principal", "pages/inventory.py", "menu_inventory"),
            ("Requerimientos", "pages/requirements.py", "menu_requirements"),
            ("Despachos", "pages/dispatches.py", "menu_dispatches"),
            ("Recepciones", "pages/receipts.py", "menu_receipts"),
            ("Inventario Obra", "pages/inventory_obra.py", "menu_inventory_obra"),
        )
        for label, page, key in operation_items:
            if enabled:
                _btn(label, page, key)
            else:
                st.button(
                    label, use_container_width=True, key=key, disabled=True,
                    help="Selecciona Visualizar en un cliente para usar este módulo.",
                )

    # ── Menú según rol / estado de impersonación ──────────────────────────────
    if role == "superadmin" and not is_impersonating:
        st.markdown('<p class="sb-section">Administración</p>', unsafe_allow_html=True)
        _btn("Panel de Usuarios", "pages/admin.py",         "menu_admin")

        st.markdown('<span class="sb-section-gap"></span>', unsafe_allow_html=True)
        st.markdown('<p class="sb-section">Finanzas</p>', unsafe_allow_html=True)
        _btn("Presupuestos",      "pages/presupuestos.py",  "menu_presupuestos")
        _btn("Adicional",         "pages/adicional.py",     "menu_adicional")

        st.markdown('<span class="sb-section-gap"></span>', unsafe_allow_html=True)
        st.markdown('<p class="sb-section">Monitoreo</p>', unsafe_allow_html=True)
        _btn("Logs de Acceso",   "pages/access_logs.py",   "menu_access_logs")
        # El módulo se mantiene visible, pero necesita un cliente seleccionado.
        _operations_menu(enabled=False)
    else:
        # Cliente normal o superadmin en modo vista
        st.markdown('<p class="sb-section">Principal</p>', unsafe_allow_html=True)
        _btn("Dashboard",        "pages/dashboard.py",    "menu_dashboard")

        # En este punto existe un propietario: el cliente actual o impersonado.
        _operations_menu()

    # ── Spacer ────────────────────────────────────────────────────────────────
    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # ── Logout ───────────────────────────────────────────────────────────────
    if st.button("Cerrar sesión", use_container_width=True, key="sidebar_logout_btn"):
        from utils.auth import logout
        logout()

