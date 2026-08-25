# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, date, timedelta
import plotly.graph_objects as go

from database import SessionLocal
from services.budget_service import (
    create_budget,
    get_budgets,
    delete_budget,
    update_budget,
    finish_budget,
    reactivate_budget,
    get_dispatch_costs,
    get_movement_summary,
    count_budget_inventory,
    deactivate_budget_with_reason,
    confirm_reactivation,
    extend_reactivation,
    get_extension_history,
)
from services.inventory_service import (
    get_floating_consumed, get_locked_consumed,
    get_lost_consumed, get_pending_deleted_consumed,
)
from utils.auth import require_superadmin
from utils.navbar import render_navbar, render_sidebar_menu

st.set_page_config(
    page_title="Presupuestos — Sistema MRP",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_superadmin()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stHeader"]     { background: transparent !important; }
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stAppViewBlockContainer"] { padding-top: 1.2rem !important; }

/* ── Hero ── */
.bud-hero {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: .5rem;
    padding: 1rem 1.5rem 1.2rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #064e3b 0%, #065f46 55%, #059669 100%);
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(5,150,105,.30);
}
.bud-hero-left  { display: flex; align-items: center; gap: 1rem; }
.bud-hero-icon  {
    width: 60px; height: 60px; border-radius: 16px;
    background: rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 1.8rem;
}
.bud-hero h1 { font-size: 1.55rem; font-weight: 900; color: #fff; margin: 0; }
.bud-hero p  { font-size: .82rem; color: rgba(255,255,255,.70); margin: 2px 0 0; }
.bud-badge {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,.25);
    border-radius: 30px; padding: .35rem 1rem;
    font-size: .78rem; font-weight: 700; color: #d1fae5;
    white-space: nowrap;
}

/* ── KPI Cards ── */
.bkpi { border-radius: 16px; padding: 1.2rem 1.4rem; color: #fff; position: relative; overflow: hidden; }
.bkpi-label { font-size: .70rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; opacity: .80; margin-bottom: .3rem; }
.bkpi-val   { font-size: 2.1rem; font-weight: 900; line-height: 1; }
.bkpi-sub   { font-size: .73rem; opacity: .65; margin-top: .2rem; }
.bk-violet  { background: linear-gradient(135deg, #4c1d95, #7c3aed); }
.bk-green   { background: linear-gradient(135deg, #064e3b, #059669); }
.bk-teal    { background: linear-gradient(135deg, #0e7490, #0891b2); }
.bk-orange  { background: linear-gradient(135deg, #92400e, #d97706); }

/* ── Section title ── */
.sec-title {
    font-size: 1rem; font-weight: 800;
    display: flex; align-items: center; gap: .55rem;
    padding-left: .8rem;
    border-left: 4px solid #059669;
    margin: 2rem 0 .9rem;
}

/* ── Status badge ── */
.stat-badge {
    display: inline-flex; align-items: center; gap: .30rem;
    padding: .18rem .60rem; border-radius: 20px;
    font-size: .67rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .07em;
    vertical-align: middle;
}
.stat-active    { background: rgba(5,150,105,.20); color: #34d399; border: 1px solid rgba(52,211,153,.28); }
.stat-inactive  { background: rgba(100,116,139,.14); color: #94a3b8; border: 1px solid rgba(148,163,184,.22); }
.stat-finished  { background: rgba(99,102,241,.18); color: #a5b4fc; border: 1px solid rgba(99,102,241,.28); }

/* ── Budget card ── */
.bud-card {
    display: flex; align-items: center; gap: 1rem;
    padding: .8rem 1.1rem;
    border-radius: 12px;
    border: 1px solid rgba(5,150,105,.20);
    background: rgba(5,150,105,.04);
    transition: background .15s;
}
.bud-card:hover { background: rgba(5,150,105,.09); }
.bud-card.inactive {
    border-color: rgba(100,116,139,.18);
    background: rgba(100,116,139,.04);
    opacity: .78;
}
.bud-card.inactive:hover { background: rgba(100,116,139,.09); opacity: 1; }
.bud-icon {
    width: 40px; height: 40px; border-radius: 12px; flex-shrink: 0;
    background: linear-gradient(135deg, #059669, #34d399);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem;
}
.bud-icon.inactive { background: linear-gradient(135deg, #475569, #64748b); }
.bud-info    { flex: 1; min-width: 0; }
.bud-name    { font-size: .90rem; font-weight: 700; display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; }
.bud-meta    { font-size: .73rem; opacity: .55; margin-top: 2px; }
.bud-amounts { text-align: right; flex-shrink: 0; }
.bud-soles   { font-size: .90rem; font-weight: 800; color: #34d399; }
.bud-dolares { font-size: .73rem; opacity: .60; margin-top: 2px; }

/* ── Progress bar ── */
.prog-wrap { margin: .6rem 0 .2rem; }
.prog-label {
    display: flex; justify-content: space-between; align-items: center;
    font-size: .72rem; margin-bottom: .3rem; font-weight: 600;
}
.prog-track {
    background: rgba(255,255,255,.08);
    border-radius: 100px; height: 6px; overflow: hidden;
}
.prog-fill { height: 100%; border-radius: 100px; transition: width .4s ease; }

/* ── Cost table (per-project) ── */
.cost-table { width: 100%; border-collapse: collapse; font-size: .82rem; margin-top: .5rem; }
.cost-table th {
    text-align: left; padding: .45rem .7rem;
    border-bottom: 1px solid rgba(255,255,255,.08);
    font-size: .67rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .1em;
    color: rgba(255,255,255,.42);
}
.cost-table td { padding: .45rem .7rem; border-bottom: 1px solid rgba(255,255,255,.04); }
.cost-table tr:last-child td { border-bottom: none; }
.cost-total { font-weight: 800; color: #34d399; }
.cost-foot td {
    font-weight: 800; padding: .55rem .7rem;
    border-top: 1px solid rgba(255,255,255,.14) !important;
}

/* ── No-price warning ── */
.no-price-hint {
    font-size: .76rem; color: #fbbf24;
    background: rgba(245,158,11,.08);
    border: 1px solid rgba(245,158,11,.22);
    border-radius: 9px; padding: .55rem .85rem;
    margin: .4rem 0 .8rem;
}

/* ── Edit form box ── */
.edit-form-box {
    border: 1px solid rgba(5,150,105,.22);
    border-radius: 12px; padding: .75rem 1rem .5rem;
    background: rgba(5,150,105,.05); margin: .2rem 0 .5rem;
}

/* ── Buttons ── */
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    box-shadow: 0 2px 14px rgba(5,150,105,.35) !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #047857 0%, #065f46 100%) !important;
    box-shadow: 0 6px 20px rgba(5,150,105,.45) !important;
}
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    box-shadow: 0 2px 12px rgba(5,150,105,.25) !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg, #047857 0%, #065f46 100%) !important;
    transform: translateY(-1px) !important;
}
/* ── Botón eliminar (secondary) ── */
[data-testid="stBaseButton-secondary"] {
    background: rgba(220,38,38,.12) !important;
    color: #fca5a5 !important;
    border: 1px solid rgba(220,38,38,.35) !important;
    border-radius: 10px !important; font-weight: 700 !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(220,38,38,.28) !important;
    border-color: rgba(220,38,38,.60) !important;
    color: #fff !important;
}
/* ── Botón confirmar eliminar ── */
.del-confirm-yes [data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
    box-shadow: 0 2px 12px rgba(220,38,38,.35) !important;
}
.del-confirm-yes [data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%) !important;
}
[data-testid="stAlert"] { border-radius: 10px !important; }
label[data-testid="stWidgetLabel"] p { font-size: .80rem !important; font-weight: 600 !important; }

/* ── Expanders ── */
[data-testid="stExpander"] {
    border-radius: 14px !important;
    border: 1px solid rgba(5,150,105,.18) !important;
    background: rgba(5,150,105,.03) !important;
    overflow: hidden !important; margin-bottom: .45rem !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(5,150,105,.32) !important;
}
details[data-testid="stExpander"] > summary {
    padding: .82rem 1.1rem !important;
    font-size: .86rem !important; font-weight: 700 !important;
    color: #6ee7b7 !important;
}
details[data-testid="stExpander"][open] > summary {
    border-bottom: 1px solid rgba(5,150,105,.14) !important;
}

/* ── Global History Section ── */
.glob-hist-header {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: .5rem;
    padding: .85rem 1.1rem;
    border-radius: 12px;
    background: rgba(14,116,144,.10);
    border: 1px solid rgba(14,116,144,.25);
    margin-bottom: 1rem;
}
.glob-hist-title { font-size: .87rem; font-weight: 800; color: #67e8f9; }
.glob-hist-range { font-size: .74rem; color: rgba(255,255,255,.45); }

/* Global history KPI */
.glob-kpi {
    border-radius: 13px; padding: .9rem 1.1rem; color: #fff;
    border: 1px solid rgba(255,255,255,.06);
}
.glob-kpi-label { font-size: .67rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; opacity: .72; margin-bottom: .25rem; }
.glob-kpi-val   { font-size: 1.65rem; font-weight: 900; line-height: 1; }
.glob-kpi-sub   { font-size: .68rem; opacity: .55; margin-top: .2rem; }
.gk-violet { background: linear-gradient(135deg, #4c1d95, #7c3aed); }
.gk-teal   { background: linear-gradient(135deg, #0e7490, #0891b2); }
.gk-green  { background: linear-gradient(135deg, #064e3b, #059669); }
.gk-blue   { background: linear-gradient(135deg, #1e3a5f, #2563eb); }

/* Global history table */
.gcost-table {
    width: 100%; border-collapse: separate; border-spacing: 0;
    font-size: .82rem; margin-top: .7rem;
    border-radius: 11px; overflow: hidden;
    border: 1px solid rgba(14,116,144,.22);
}
.gcost-table thead tr { background: rgba(14,116,144,.15); }
.gcost-table th {
    text-align: left; padding: .62rem .82rem;
    font-size: .66rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .1em;
    color: rgba(255,255,255,.52);
    border-bottom: 2px solid rgba(14,116,144,.30);
}
.gcost-table td {
    padding: .52rem .82rem;
    border-bottom: 1px solid rgba(255,255,255,.045);
    vertical-align: middle;
}
.gcost-table tbody tr:nth-child(even) td { background: rgba(14,116,144,.05); }
.gcost-table tbody tr:last-child td { border-bottom: none; }
.gcost-table tfoot td {
    background: rgba(14,116,144,.13);
    font-weight: 800; padding: .62rem .82rem;
    border-top: 2px solid rgba(14,116,144,.28) !important;
    border-bottom: none !important;
}
.mat-chip {
    display: inline-block;
    background: rgba(14,116,144,.22); color: #67e8f9;
    border-radius: 5px; padding: .05rem .42rem;
    font-size: .68rem; font-weight: 700;
    font-family: monospace; letter-spacing: .03em;
}
.gcost-green { color: #34d399; font-weight: 800; }
.gcost-blue  { color: #93c5fd; font-weight: 600; }
.gcost-dim   { color: rgba(255,255,255,.28); font-style: italic; font-size: .74rem; }
.gcost-chart-wrap {
    margin-top: .9rem;
    border-radius: 12px;
    border: 1px solid rgba(14,116,144,.18);
    background: rgba(14,116,144,.04);
    padding: .6rem .6rem .2rem;
}

/* ── Per-project cost history ── */
.hist-banner {
    display: flex; align-items: center; gap: .65rem;
    padding: .6rem 1rem;
    border-radius: 10px;
    background: rgba(5,150,105,.08);
    border: 1px solid rgba(5,150,105,.20);
    margin-bottom: .85rem;
}
.hist-banner-title { font-size: .84rem; font-weight: 800; color: #6ee7b7; }
.hist-banner-sub   { font-size: .72rem; color: rgba(255,255,255,.40); margin-left: auto; }

.hist-kpis {
    display: flex; gap: .65rem; margin-bottom: .85rem; flex-wrap: wrap;
}
.hist-kpi {
    flex: 1; min-width: 130px;
    display: flex; align-items: center; gap: .65rem;
    padding: .70rem .92rem;
    border-radius: 11px;
    border: 1px solid rgba(5,150,105,.18);
    background: rgba(5,150,105,.06);
}
.hist-kpi-icon {
    width: 34px; height: 34px; border-radius: 9px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; background: rgba(5,150,105,.20); color: #34d399;
}
.hist-kpi-val   { font-size: 1.10rem; font-weight: 800; color: #e2e8f0; line-height: 1; }
.hist-kpi-label { font-size: .64rem; text-transform: uppercase; letter-spacing: .09em;
                  color: rgba(255,255,255,.40); margin-top: .17rem; font-weight: 600; }

.proj-cost-table {
    width: 100%; border-collapse: separate; border-spacing: 0;
    font-size: .82rem; margin-top: .55rem;
    border-radius: 10px; overflow: hidden;
    border: 1px solid rgba(5,150,105,.18);
}
.proj-cost-table thead tr { background: rgba(5,150,105,.13); }
.proj-cost-table th {
    text-align: left; padding: .55rem .78rem;
    font-size: .64rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .1em;
    color: rgba(255,255,255,.45);
    border-bottom: 2px solid rgba(5,150,105,.26);
}
.proj-cost-table td {
    padding: .50rem .78rem;
    border-bottom: 1px solid rgba(255,255,255,.04);
    vertical-align: middle;
}
.proj-cost-table tbody tr:nth-child(even) td { background: rgba(5,150,105,.04); }
.proj-cost-table tbody tr:hover td { background: rgba(5,150,105,.09); }
.proj-cost-table tbody tr:last-child td { border-bottom: none; }
.proj-cost-table tfoot td {
    background: rgba(5,150,105,.13);
    font-weight: 800; padding: .58rem .78rem;
    border-top: 2px solid rgba(5,150,105,.26) !important;
    border-bottom: none !important;
}
.pcode {
    display: inline-block;
    background: rgba(5,150,105,.22); color: #6ee7b7;
    border-radius: 5px; padding: .04rem .44rem;
    font-size: .70rem; font-weight: 700; font-family: monospace;
}
.p-cost-green { color: #34d399; font-weight: 800; }
.p-cost-amber { color: #fbbf24; font-weight: 600; }
.p-cost-dim   { color: rgba(255,255,255,.28); font-style: italic; font-size: .74rem; }
</style>
""", unsafe_allow_html=True)

render_navbar()
with st.sidebar:
    render_sidebar_menu()

# ── Hero ──────────────────────────────────────────────────────────────────────
now  = datetime.now()
user = st.session_state.get("username", "Superadmin")

st.markdown(f"""
<div class="bud-hero">
  <div class="bud-hero-left">
    <div class="bud-hero-icon">&#128176;</div>
    <div>
      <h1>Presupuestos de Proyectos</h1>
      <p>Control de gastos y costos de materiales &nbsp;·&nbsp; {now.strftime("%A %d de %B, %Y")}</p>
    </div>
  </div>
  <div class="bud-badge">&#9733; {user}</div>
</div>
""", unsafe_allow_html=True)

db      = SessionLocal()
budgets = get_budgets(db)

# ── KPIs ──────────────────────────────────────────────────────────────────────
n_active          = sum(1 for b in budgets if b.is_active)
total_proyectos   = len(budgets)
total_soles_all   = sum(b.budget_soles   for b in budgets)
total_dolares_all = sum(b.budget_dolares for b in budgets)
costs_all, grand_total_all, grand_total_all_dol = get_dispatch_costs(db)
has_prices = any(r["unit_price"] > 0 for r in costs_all)

k1, k2, k3, k4 = st.columns(4, gap="medium")
k1.markdown(f"""<div class="bkpi bk-violet">
  <div class="bkpi-label">Total Proyectos</div>
  <div class="bkpi-val">{total_proyectos}</div>
  <div class="bkpi-sub">{n_active} activos &nbsp;/&nbsp; {total_proyectos - n_active} inactivos</div>
</div>""", unsafe_allow_html=True)

k2.markdown(f"""<div class="bkpi bk-green">
  <div class="bkpi-label">Presupuesto Total S/.</div>
  <div class="bkpi-val">S/ {total_soles_all:,.0f}</div>
  <div class="bkpi-sub">Soles peruanos</div>
</div>""", unsafe_allow_html=True)

k3.markdown(f"""<div class="bkpi bk-teal">
  <div class="bkpi-label">Presupuesto Total $</div>
  <div class="bkpi-val">$ {total_dolares_all:,.0f}</div>
  <div class="bkpi-sub">Dólares americanos</div>
</div>""", unsafe_allow_html=True)

k4.markdown(f"""<div class="bkpi bk-orange">
  <div class="bkpi-label">Costo Material (global)</div>
  <div class="bkpi-val">S/ {grand_total_all:,.0f}</div>
  <div class="bkpi-sub">Basado en despachos</div>
</div>""", unsafe_allow_html=True)

if costs_all and not has_prices:
    st.markdown("""<div class="no-price-hint">
    &#9888;&nbsp; Los materiales no tienen precio unitario configurado — el costo se muestra en S/ 0.00.
    Configure el precio de cada material en la página <strong>Materiales</strong>.
    </div>""", unsafe_allow_html=True)

# ── Tipo de cambio + Instrucciones ───────────────────────────────────────────
_tc_col, _tc_pad, _help_col = st.columns([2.6, 5.4, 1.5])
with _tc_col:
    _tc_default = float(st.session_state.get("_bud_tc", 3.75))
    tipo_cambio = st.number_input(
        "Tipo de cambio (S/. por $)",
        min_value=0.01, value=_tc_default, step=0.01, format="%.2f",
        help="Tasa usada para convertir gastos entre soles y dólares cuando el presupuesto o los precios de materiales están en una sola moneda.",
    )
    st.session_state["_bud_tc"] = tipo_cambio

with _help_col:
    with st.popover("📋 Instrucciones", use_container_width=True):
        st.markdown("#### Guía de Presupuestos")
        st.markdown("""
**Crear presupuesto** — Define el nombre del proyecto y los montos en soles y/o dólares.

**Tipo de cambio** — Tasa S/. por dólar usada para convertir gastos cuando los precios de materiales están solo en una moneda.

**Utilización del presupuesto** — Barra de progreso que compara el costo de materiales despachados vs. el presupuesto asignado.

**Conversión automática:**
- Si los materiales tienen precio en S/. pero el presupuesto es en $, el sistema convierte dividiendo entre el tipo de cambio.
- Si los materiales tienen precio en $ pero el presupuesto es en S/., se multiplica por el tipo de cambio.

**Finalizar obra** — Cierra el proyecto y registra la fecha de finalización. Se emiten alertas si el gasto superó o no llegó al presupuesto.

**Historial de costos** — Detalla cada material despachado desde el inicio del proyecto con su costo unitario y total.
""")

# ── Crear presupuesto ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">&#43; Nuevo Presupuesto de Proyecto</div>', unsafe_allow_html=True)

with st.expander("Registrar nuevo presupuesto", expanded=False):
    with st.form("form_new_budget", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 2, 2], gap="medium")
        with c1:
            f_name  = st.text_input(
                "Nombre del proyecto *",
                placeholder="Ej. Obra Residencial Norte 2025",
            )
        with c2:
            f_soles = st.number_input(
                "Presupuesto (S/.)",
                min_value=0.0, value=0.0, step=1000.0, format="%.0f",
                help="Solo valores positivos.",
            )
        with c3:
            f_dolar = st.number_input(
                "Presupuesto ($)",
                min_value=0.0, value=0.0, step=100.0, format="%.0f",
                help="Solo valores positivos.",
            )
        f_notes = st.text_area(
            "Notas (opcional)",
            placeholder="Descripción, alcance o detalles del proyecto...",
            height=70,
        )
        submitted = st.form_submit_button("Crear Presupuesto", use_container_width=True, type="primary")
        if submitted:
            if not f_name.strip():
                st.error("El nombre del proyecto es obligatorio.")
            elif f_soles < 0 or f_dolar < 0:
                st.error("Los montos del presupuesto no pueden ser negativos.")
            else:
                create_budget(db, f_name.strip(), f_soles, f_dolar, f_notes.strip() or None)
                st.success(f"Presupuesto **{f_name.strip()}** creado exitosamente.")
                st.rerun()

# ── Lista de presupuestos ─────────────────────────────────────────────────────
st.markdown('<div class="sec-title">&#128203; Proyectos Registrados</div>', unsafe_allow_html=True)

if not budgets:
    st.info("No hay presupuestos registrados. Crea el primero con el formulario de arriba.")
else:
    _bud_filter = st.text_input(
        "Buscar proyecto",
        placeholder="Filtrar por nombre de proyecto...",
        key="bud_name_filter",
        label_visibility="collapsed",
    )
    if _bud_filter:
        _q = _bud_filter.lower()
        budgets_show = [b for b in budgets if _q in (b.name or "").lower()]
        if not budgets_show:
            st.info(f"No hay proyectos que coincidan con «{_bud_filter}».")
    else:
        budgets_show = budgets

    for bud in budgets_show:
        is_editing = st.session_state.get(f"editing_bud_{bud.id}", False)

        _is_finished = getattr(bud, "is_finished", False)
        _deact_date  = getattr(bud, "deactivated_at", None)
        _react_date  = getattr(bud, "reactivation_date", None)
        _reactivation_due = (
            (not bud.is_active) and (not _is_finished)
            and _react_date is not None and _react_date <= datetime.utcnow()
        )
        if _is_finished:
            _fin_date   = bud.finished_at.strftime("%d/%m/%Y") if bud.finished_at else "—"
            card_class  = "bud-card inactive"
            icon_class  = "bud-icon inactive"
            status_html = f'<span class="stat-badge stat-finished">&#10003; Finalizado {_fin_date}</span>'
        elif bud.is_active:
            card_class  = "bud-card"
            icon_class  = "bud-icon"
            status_html = '<span class="stat-badge stat-active">&#9679; Activo</span>'
        else:
            card_class  = "bud-card inactive"
            icon_class  = "bud-icon inactive"
            if _reactivation_due:
                status_html = '<span class="stat-badge stat-inactive" style="background:rgba(245,158,11,.16);color:#fbbf24;border-color:rgba(245,158,11,.32)">&#9888; Reactivación pendiente</span>'
            else:
                status_html = '<span class="stat-badge stat-inactive">&#9675; Inactivo</span>'

        # ── Fila principal ────────────────────────────────────────────────────
        col_card, col_toggle, col_edit, col_fin, col_del = st.columns([4.5, 1.8, 1.2, 1.7, 1.3], gap="small")

        with col_card:
            fecha    = bud.created_at.strftime("%d/%m/%Y")
            nota_txt = f"&nbsp;·&nbsp; {bud.notes}" if bud.notes else ""
            _deact_info = ""
            # El TOTAL del presupuesto es fijo y solo cambia con Editar.
            # El "Disponible" se computa = total − bloqueado − pendiente − perdido − flotante.
            _locked_s, _locked_d = get_locked_consumed(db, bud.id)
            _pend_s,   _pend_d   = get_pending_deleted_consumed(db, bud.id)
            _lost_s,   _lost_d   = get_lost_consumed(db, bud.id)
            _floating_s = 0.0
            _floating_d = 0.0
            if (not bud.is_active) and (not _is_finished):
                _floating_s, _floating_d = get_floating_consumed(db, bud.id)
            _avail_soles   = max(0.0, float(bud.budget_soles)   - _locked_s - _pend_s - _lost_s - _floating_s)
            _avail_dolares = max(0.0, float(bud.budget_dolares) - _locked_d - _pend_d - _lost_d - _floating_d)
            _floating_note = ""
            if _floating_s > 0 or _floating_d > 0:
                _floating_note = (
                    f'<div style="font-size:.62rem;color:#fbbf24;margin-top:2px">'
                    f'⏳ Flotante: S/ {_floating_s:,.2f}'
                    f'</div>'
                )
            if (not bud.is_active) and (not _is_finished) and _deact_date:
                _d_str = _deact_date.strftime("%d/%m/%Y")
                _r_str = _react_date.strftime("%d/%m/%Y") if _react_date else "—"
                _reason_txt = bud.deactivation_reason or "—"
                _r_color = "#fbbf24" if _reactivation_due else "#94a3b8"
                _deact_info = (
                    f'<div class="bud-meta" style="margin-top:.25rem;color:rgba(148,163,184,.78)">'
                    f'<span style="color:#94a3b8">Desactivado: {_d_str}</span>'
                    f' &nbsp;·&nbsp; <span style="color:{_r_color}">Reactivación: {_r_str}</span>'
                    f' &nbsp;·&nbsp; <em>{_reason_txt}</em>'
                    f'</div>'
                )
            st.markdown(f"""
            <div class="{card_class}">
              <div class="{icon_class}">&#128188;</div>
              <div class="bud-info">
                <div class="bud-name">{bud.name} {status_html}</div>
                <div class="bud-meta">Creado: {fecha}{nota_txt}</div>
                {_deact_info}
              </div>
              <div class="bud-amounts">
                <div style="font-size:.60rem;color:rgba(148,163,184,.55);font-weight:700;text-transform:uppercase;letter-spacing:.07em;margin-bottom:1px">Presupuesto (fijo)</div>
                <div class="bud-soles">S/ {bud.budget_soles:,.2f}</div>
                <div class="bud-dolares">$ {bud.budget_dolares:,.2f}</div>
                <div style="font-size:.62rem;color:rgba(148,163,184,.55);margin-top:.30rem">
                  Disponible: <span style="color:#34d399;font-weight:700">S/ {_avail_soles:,.2f}</span>
                  &nbsp;·&nbsp; <span style="color:#34d399;font-weight:700">$ {_avail_dolares:,.2f}</span>
                </div>
                {_floating_note}
              </div>
            </div>""", unsafe_allow_html=True)

        with col_toggle:
            st.write("")
            if _is_finished:
                if st.button("Reactivar", key=f"toggle_{bud.id}", use_container_width=True, type="primary"):
                    reactivate_budget(db, bud.id)
                    st.rerun()
            elif bud.is_active:
                if st.button("Desactivar", key=f"toggle_{bud.id}", use_container_width=True):
                    st.session_state[f"deact_form_{bud.id}"] = True
                    st.rerun()
            else:
                if st.button("Activar", key=f"toggle_{bud.id}", use_container_width=True, type="primary"):
                    st.session_state[f"act_form_{bud.id}"] = True
                    st.rerun()

        with col_edit:
            st.write("")
            edit_label = "Cerrar ✕" if is_editing else "Editar"
            if st.button(edit_label, key=f"edit_btn_{bud.id}", use_container_width=True, type="primary"):
                st.session_state[f"editing_bud_{bud.id}"] = not is_editing
                st.rerun()

        with col_fin:
            st.write("")
            if not _is_finished:
                if st.button("🏁 Finalizar obra", key=f"fin_btn_{bud.id}", use_container_width=True):
                    st.session_state[f"confirm_fin_{bud.id}"] = True

        with col_del:
            st.write("")
            if st.button("🗑️ Eliminar", key=f"del_btn_{bud.id}", use_container_width=True, type="secondary"):
                st.session_state[f"confirm_del_{bud.id}"] = True

        # ── Confirmar finalización de obra ───────────────────────────────────
        if st.session_state.get(f"confirm_fin_{bud.id}"):
            _costs_fin, _total_fin_s, _total_fin_d = get_dispatch_costs(db, since=bud.created_at)
            _tc = st.session_state.get("_bud_tc", 3.75)

            st.markdown("---")
            st.markdown(f"**🏁 Finalizar obra: {bud.name}**")

            # Alerta en soles
            if bud.budget_soles > 0:
                _diff_s = bud.budget_soles - _total_fin_s
                _pct_s  = (_total_fin_s / bud.budget_soles * 100) if bud.budget_soles > 0 else 0
                if _total_fin_s > bud.budget_soles:
                    st.error(f"⚠️ **La obra superó el presupuesto en S/.** — Exceso: S/ {abs(_diff_s):,.2f} ({_pct_s:.1f}% utilizado)")
                elif _total_fin_s < bud.budget_soles:
                    st.warning(f"⚠️ **La obra no llegó al presupuesto esperado (S/.)** — Sin utilizar: S/ {_diff_s:,.2f} ({100 - _pct_s:.1f}% restante)")
                else:
                    st.success(f"✓ La obra se ejecutó exactamente en el presupuesto en soles.")

            # Alerta en dólares
            if bud.budget_dolares > 0:
                _cost_dol = _total_fin_d if _total_fin_d > 0 else (_total_fin_s / _tc if _tc > 0 else 0)
                _diff_d   = bud.budget_dolares - _cost_dol
                _pct_d    = (_cost_dol / bud.budget_dolares * 100) if bud.budget_dolares > 0 else 0
                if _cost_dol > bud.budget_dolares:
                    st.error(f"⚠️ **La obra superó el presupuesto en $** — Exceso: $ {abs(_diff_d):,.2f} ({_pct_d:.1f}% utilizado)")
                elif _cost_dol < bud.budget_dolares:
                    st.warning(f"⚠️ **La obra no llegó al presupuesto esperado ($)** — Sin utilizar: $ {_diff_d:,.2f} ({100 - _pct_d:.1f}% restante)")
                else:
                    st.success(f"✓ La obra se ejecutó exactamente en el presupuesto en dólares.")

            if bud.budget_soles == 0 and bud.budget_dolares == 0:
                st.info("No hay presupuesto asignado a esta obra.")

            st.markdown("¿Confirmar finalización? La obra quedará marcada como completada y se registrará la fecha.")
            _cy, _cn = st.columns(2)
            with _cy:
                if st.button("✓ Confirmar finalización", key=f"yes_fin_{bud.id}", use_container_width=True, type="primary"):
                    finish_budget(db, bud.id)
                    st.session_state.pop(f"confirm_fin_{bud.id}", None)
                    st.rerun()
            with _cn:
                if st.button("Cancelar", key=f"no_fin_{bud.id}", use_container_width=True):
                    st.session_state.pop(f"confirm_fin_{bud.id}", None)
                    st.rerun()
            st.markdown("---")

        # ── Formulario de desactivación ──────────────────────────────────────
        if st.session_state.get(f"deact_form_{bud.id}") and bud.is_active and not _is_finished:
            st.markdown("---")
            st.markdown(f"**🔻 Desactivar proyecto: {bud.name}**")
            with st.form(key=f"form_deact_{bud.id}"):
                _reason = st.text_area(
                    "Motivo de la desactivación *",
                    placeholder="Explica por qué se desactiva el proyecto…",
                    height=80,
                )
                _react = st.date_input(
                    "Fecha programada de reactivación *",
                    value=date.today() + timedelta(days=30),
                    min_value=date.today(),
                    help="Cuando llegue esta fecha, deberás confirmar la reactivación o extender la fecha con un nuevo motivo.",
                )
                _ds, _dc = st.columns(2)
                with _ds:
                    _confirm_deact = st.form_submit_button("Confirmar desactivación", use_container_width=True, type="primary")
                with _dc:
                    _cancel_deact  = st.form_submit_button("Cancelar", use_container_width=True)
                if _confirm_deact:
                    if not _reason.strip():
                        st.error("El motivo de desactivación es obligatorio.")
                    else:
                        _react_dt = datetime.combine(_react, datetime.min.time())
                        deactivate_budget_with_reason(db, bud.id, _reason.strip(), _react_dt)
                        st.session_state.pop(f"deact_form_{bud.id}", None)
                        st.success(f"Proyecto **{bud.name}** desactivado. Reactivación programada para {_react.strftime('%d/%m/%Y')}.")
                        st.rerun()
                if _cancel_deact:
                    st.session_state.pop(f"deact_form_{bud.id}", None)
                    st.rerun()
            st.markdown("---")

        # ── Formulario de activación manual ──────────────────────────────────
        if st.session_state.get(f"act_form_{bud.id}") and (not bud.is_active) and (not _is_finished):
            st.markdown("---")
            st.markdown(f"**🔓 Activar proyecto: {bud.name}**")
            _curr_react = _react_date.strftime("%d/%m/%Y") if _react_date else "—"
            st.caption(
                f"Motivo de desactivación: *{bud.deactivation_reason or '—'}*  \n"
                f"Reactivación programada: {_curr_react}"
            )
            with st.form(key=f"form_act_{bud.id}"):
                _act_note = st.text_area(
                    "Motivo de la reactivación *",
                    placeholder="Explica por qué se reactiva el proyecto…",
                    height=80,
                )
                _as, _ac = st.columns(2)
                with _as:
                    _confirm_act = st.form_submit_button("Confirmar activación", use_container_width=True, type="primary")
                with _ac:
                    _cancel_act  = st.form_submit_button("Cancelar", use_container_width=True)
                if _confirm_act:
                    if not _act_note.strip():
                        st.error("El motivo de reactivación es obligatorio.")
                    else:
                        confirm_reactivation(db, bud.id, note=_act_note.strip())
                        st.session_state.pop(f"act_form_{bud.id}", None)
                        st.success(f"Proyecto **{bud.name}** reactivado.")
                        st.rerun()
                if _cancel_act:
                    st.session_state.pop(f"act_form_{bud.id}", None)
                    st.rerun()
            st.markdown("---")

        # ── Confirmación / Extensión de reactivación ─────────────────────────
        if (not bud.is_active) and (not _is_finished) and _react_date is not None:
            _ext_history = get_extension_history(bud)
            with st.expander(
                f"🔔 Estado de reactivación — {bud.name}"
                + (" · ⚠️ pendiente" if _reactivation_due else ""),
                expanded=_reactivation_due,
            ):
                _d_str_full = _deact_date.strftime("%d/%m/%Y %H:%M") if _deact_date else "—"
                _r_str_full = _react_date.strftime("%d/%m/%Y")
                st.markdown(
                    f"**Desactivado:** {_d_str_full}  \n"
                    f"**Motivo original:** {bud.deactivation_reason or '—'}  \n"
                    f"**Reactivación programada:** {_r_str_full}"
                )

                if _ext_history:
                    st.markdown("**Historial de cambios:**")
                    for _idx, _h in enumerate(_ext_history, 1):
                        _type = _h.get("type") or "extension"
                        try:
                            _prev_dt = datetime.fromisoformat(_h["previous_date"]).strftime("%d/%m/%Y") if _h.get("previous_date") else "—"
                            _new_dt  = datetime.fromisoformat(_h["new_date"]).strftime("%d/%m/%Y") if _h.get("new_date") else None
                            _at_raw  = _h.get("reactivated_at") or _h.get("extended_at")
                            _at_str  = datetime.fromisoformat(_at_raw).strftime("%d/%m/%Y %H:%M") if _at_raw else "—"
                        except (ValueError, TypeError):
                            _prev_dt = _h.get("previous_date") or "—"
                            _new_dt  = _h.get("new_date")
                            _at_str  = _h.get("reactivated_at") or _h.get("extended_at") or "—"
                        if _type == "manual_reactivation":
                            _label = f"🔓 Reactivación manual (fecha programada era {_prev_dt})"
                        else:
                            _label = f"📅 Extensión: {_prev_dt} → {_new_dt or '—'}"
                        st.markdown(
                            f"&nbsp;&nbsp;**{_idx}.** {_label}"
                            f" &nbsp;·&nbsp; *{_h.get('reason') or '—'}*"
                            f" &nbsp;·&nbsp; <span style='color:rgba(148,163,184,.55);font-size:.74rem'>registrado: {_at_str}</span>",
                            unsafe_allow_html=True,
                        )

                if _reactivation_due:
                    st.warning(
                        f"La fecha de reactivación ({_r_str_full}) ya llegó. "
                        f"Confirma la reactivación o extiende la fecha con un nuevo motivo."
                    )
                    _ec1, _ec2 = st.columns(2)
                    if _ec1.button(
                        "✓ Confirmar reactivación",
                        key=f"confirm_react_{bud.id}",
                        use_container_width=True, type="primary",
                    ):
                        confirm_reactivation(db, bud.id)
                        st.success(f"Proyecto **{bud.name}** reactivado.")
                        st.rerun()
                    if _ec2.button(
                        "📅 Extender fecha",
                        key=f"open_extend_{bud.id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"extend_form_{bud.id}"] = True
                        st.rerun()

                    if st.session_state.get(f"extend_form_{bud.id}"):
                        with st.form(key=f"form_extend_{bud.id}"):
                            _new_date = st.date_input(
                                "Nueva fecha de reactivación *",
                                value=date.today() + timedelta(days=15),
                                min_value=date.today(),
                                key=f"ext_date_{bud.id}",
                            )
                            _ext_reason = st.text_area(
                                "Motivo de la extensión *",
                                placeholder="Explica por qué se extiende la fecha…",
                                height=70,
                                key=f"ext_reason_{bud.id}",
                            )
                            _xs, _xc = st.columns(2)
                            with _xs:
                                _save_ext = st.form_submit_button(
                                    "Guardar extensión", use_container_width=True, type="primary"
                                )
                            with _xc:
                                _cancel_ext = st.form_submit_button(
                                    "Cancelar", use_container_width=True
                                )
                            if _save_ext:
                                if not _ext_reason.strip():
                                    st.error("Debes indicar un motivo para extender la fecha.")
                                else:
                                    extend_reactivation(
                                        db, bud.id,
                                        datetime.combine(_new_date, datetime.min.time()),
                                        _ext_reason.strip(),
                                    )
                                    st.session_state.pop(f"extend_form_{bud.id}", None)
                                    st.success(
                                        f"Fecha de reactivación extendida hasta {_new_date.strftime('%d/%m/%Y')}."
                                    )
                                    st.rerun()
                            if _cancel_ext:
                                st.session_state.pop(f"extend_form_{bud.id}", None)
                                st.rerun()

        # ── Confirmar eliminación ─────────────────────────────────────────────
        if st.session_state.get(f"confirm_del_{bud.id}"):
            _frozen_count = count_budget_inventory(db, bud.id)
            st.error(f"⚠️ ¿Eliminar el presupuesto **{bud.name}** permanentemente? Esta acción no se puede deshacer.")
            if _frozen_count > 0:
                st.warning(
                    f"**{_frozen_count} registro{'s' if _frozen_count != 1 else ''} de inventario** "
                    f"vinculado{'s' if _frozen_count != 1 else ''} a este proyecto quedarán "
                    f"**congelados**. El cliente podrá redirigirlos desde su panel de Inventario Principal."
                )
            st.markdown('<div class="del-confirm-yes">', unsafe_allow_html=True)
            cy, cn = st.columns(2)
            with cy:
                if st.button("Sí, eliminar", key=f"yes_del_{bud.id}", use_container_width=True, type="primary"):
                    _ok, _cancelled = delete_budget(db, bud.id)
                    st.session_state.pop(f"confirm_del_{bud.id}", None)
                    _msgs = []
                    if _frozen_count > 0:
                        _msgs.append(
                            f"**{_frozen_count} registro{'s' if _frozen_count != 1 else ''} "
                            f"de inventario** congelado{'s' if _frozen_count != 1 else ''} — el cliente puede "
                            f"redirigirlos desde Inventario Principal."
                        )
                    if _cancelled > 0:
                        _msgs.append(
                            f"**{_cancelled} requerimiento{'s' if _cancelled != 1 else ''}** "
                            f"pendiente{'s' if _cancelled != 1 else ''} cancelado{'s' if _cancelled != 1 else ''} "
                            f"automáticamente."
                        )
                    if _msgs:
                        st.success("Proyecto eliminado. " + " ".join(_msgs))
                    st.rerun()
            with cn:
                if st.button("Cancelar", key=f"no_del_{bud.id}", use_container_width=True):
                    st.session_state.pop(f"confirm_del_{bud.id}", None)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Formulario de edición ─────────────────────────────────────────────
        if is_editing:
            _editing_inactive = (not bud.is_active) and (not _is_finished)
            st.markdown('<div class="edit-form-box">', unsafe_allow_html=True)
            with st.form(key=f"form_edit_{bud.id}"):
                ec1, ec2, ec3 = st.columns([3, 2, 2], gap="medium")
                with ec1:
                    en = st.text_input("Nombre", value=bud.name)
                with ec2:
                    es = st.number_input(
                        "Presupuesto S/.", min_value=0.0,
                        value=float(bud.budget_soles), step=1000.0, format="%.2f",
                    )
                with ec3:
                    ed = st.number_input(
                        "Presupuesto $", min_value=0.0,
                        value=float(bud.budget_dolares), step=100.0, format="%.2f",
                    )
                enotes  = st.text_area("Notas", value=bud.notes or "", height=60)

                # Cuando el proyecto está desactivado (no finalizado), permitir
                # editar la fecha y el motivo de reactivación desde aquí.
                _new_react_date_val   = None
                _new_react_reason_val = None
                if _editing_inactive:
                    st.markdown(
                        "<div style='font-size:.78rem;font-weight:700;color:#94a3b8;"
                        "margin:.4rem 0 .35rem'>Datos de desactivación</div>",
                        unsafe_allow_html=True,
                    )
                    erd1, erd2 = st.columns([1.4, 2], gap="medium")
                    with erd1:
                        _curr_react_date = (
                            _react_date.date() if _react_date else (date.today() + timedelta(days=30))
                        )
                        _new_react_date_val = st.date_input(
                            "Fecha de reactivación",
                            value=_curr_react_date,
                            key=f"edit_react_date_{bud.id}",
                            help="Modifica la fecha programada de reactivación.",
                        )
                    with erd2:
                        _new_react_reason_val = st.text_area(
                            "Motivo de la desactivación",
                            value=bud.deactivation_reason or "",
                            height=80,
                            key=f"edit_react_reason_{bud.id}",
                        )

                esave, ecancel = st.columns(2)
                with esave:
                    save_clicked = st.form_submit_button("Guardar cambios", use_container_width=True, type="primary")
                with ecancel:
                    cancel_clicked = st.form_submit_button("Cancelar", use_container_width=True)

                if save_clicked:
                    if not en.strip():
                        st.error("El nombre no puede estar vacío.")
                    elif es < 0 or ed < 0:
                        st.error("Los montos no pueden ser negativos.")
                    elif _editing_inactive and not (_new_react_reason_val or "").strip():
                        st.error("El motivo de desactivación no puede estar vacío.")
                    else:
                        update_budget(
                            db, bud.id,
                            name=en.strip(), budget_soles=es,
                            budget_dolares=ed, notes=enotes.strip() or None,
                        )
                        if _editing_inactive:
                            bud.reactivation_date   = datetime.combine(_new_react_date_val, datetime.min.time())
                            bud.deactivation_reason = _new_react_reason_val.strip()
                            db.commit()
                        st.session_state.pop(f"editing_bud_{bud.id}", None)
                        st.rerun()
                if cancel_clicked:
                    st.session_state.pop(f"editing_bud_{bud.id}", None)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Historial del proyecto (expandable) ───────────────────────────────
        with st.expander(f"📊 Historial de costos: {bud.name}"):
            costs, total_cost, total_cost_dol = get_dispatch_costs(db, since=bud.created_at)
            summary = get_movement_summary(db, since=bud.created_at)

            fecha_inicio = bud.created_at.strftime("%d/%m/%Y")
            n_mats       = len(costs)
            st.markdown(f"""
            <div class="hist-banner">
              <span style="font-size:1.05rem;">&#128202;</span>
              <span class="hist-banner-title">Resumen desde el inicio del proyecto</span>
              <span class="hist-banner-sub">
                Desde {fecha_inicio} &nbsp;·&nbsp; {n_mats} material{"es" if n_mats != 1 else ""}
              </span>
            </div>
            """, unsafe_allow_html=True)

            # ── Panel de utilización del presupuesto (por ingresos a inventario) ──
            # El total del presupuesto es fijo (sólo cambia con el botón Editar).
            # Consumo = activo (bloqueado, verde) + pendiente (sin resolver, verde) +
            #            perdido (definitivo, rojo) + flotante (proyecto desactivado, ámbar).
            _hlock_s, _hlock_d = get_locked_consumed(db, bud.id)
            _hpend_s, _hpend_d = get_pending_deleted_consumed(db, bud.id)
            _hlost_s, _hlost_d = get_lost_consumed(db, bud.id)
            _hflt_s,  _hflt_d  = get_floating_consumed(db, bud.id)
            _orig_s_h = float(bud.budget_soles)
            _orig_d_h = float(bud.budget_dolares)
            _green_s  = _hlock_s + _hpend_s   # consumo en uso o pendiente de resolución
            _green_d  = _hlock_d + _hpend_d
            _cons_s_h = _green_s + _hlost_s + _hflt_s
            _cons_d_h = _green_d + _hlost_d + _hflt_d
            _pct_s_h  = min(100.0, (_cons_s_h / _orig_s_h * 100.0) if _orig_s_h > 0 else 0.0)
            _pct_d_h  = min(100.0, (_cons_d_h / _orig_d_h * 100.0) if _orig_d_h > 0 else 0.0)
            _rem_s_h  = max(0.0, _orig_s_h - _cons_s_h)
            _rem_d_h  = max(0.0, _orig_d_h - _cons_d_h)

            def _seg_pct(val, original):
                return (val / original * 100.0) if original > 0 else 0.0

            _proj_state_pill = (
                '<span style="font-size:.62rem;font-weight:800;padding:.12rem .55rem;'
                'border-radius:20px;background:rgba(5,150,105,.18);color:#6ee7b7;'
                'border:1px solid rgba(5,150,105,.30);text-transform:uppercase;'
                'letter-spacing:.05em">Activo</span>'
                if bud.is_active else
                '<span style="font-size:.62rem;font-weight:800;padding:.12rem .55rem;'
                'border-radius:20px;background:rgba(148,163,184,.16);color:#94a3b8;'
                'border:1px solid rgba(148,163,184,.30);text-transform:uppercase;'
                'letter-spacing:.05em">Desactivado</span>'
            )
            _float_chip_h = (
                f'<span style="font-size:.62rem;font-weight:700;padding:.10rem .50rem;'
                f'border-radius:20px;background:rgba(245,158,11,.14);color:#fbbf24;'
                f'border:1px solid rgba(245,158,11,.28);margin-left:.4rem">⏳ Flotante S/ {_hflt_s:,.2f}</span>'
                if _hflt_s > 0 or _hflt_d > 0 else ""
            )
            _lost_chip_h = (
                f'<span style="font-size:.62rem;font-weight:700;padding:.10rem .50rem;'
                f'border-radius:20px;background:rgba(239,68,68,.14);color:#fca5a5;'
                f'border:1px solid rgba(239,68,68,.32);margin-left:.4rem">❌ Perdido S/ {_hlost_s:,.2f}</span>'
                if _hlost_s > 0 or _hlost_d > 0 else ""
            )

            def _util_bar_segmented(label, original, green_val, lost_val, float_val, remaining, currency):
                p_green = _seg_pct(green_val, original)
                p_lost  = _seg_pct(lost_val,  original)
                p_float = _seg_pct(float_val, original)
                p_total = min(100.0, p_green + p_lost + p_float)
                # Color del % total: si >90% rojo; 70-90% ámbar; sino verde — pero si hay perdido lo destacamos.
                if p_lost > 0:
                    total_color = "#f87171"
                elif p_total >= 90:
                    total_color = "#ef4444"
                elif p_total >= 70:
                    total_color = "#f59e0b"
                else:
                    total_color = "#22c55e"
                segments = (
                    f'<div style="height:100%;width:{p_green}%;background:#22c55e"></div>'
                    f'<div style="height:100%;width:{p_lost}%;background:#ef4444"></div>'
                    f'<div style="height:100%;width:{p_float}%;background:#f59e0b"></div>'
                )
                consumed_total = green_val + lost_val + float_val
                return (
                    f'<div style="margin-top:.5rem">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'font-size:.74rem;margin-bottom:.25rem;font-weight:600">'
                    f'<span style="color:rgba(148,163,184,.75)">{label}</span>'
                    f'<span style="color:{total_color}">{p_total:.1f}% &nbsp;·&nbsp; '
                    f'{currency} {consumed_total:,.2f} / {currency} {original:,.2f}  '
                    f'<span style="color:rgba(148,163,184,.55);font-weight:500">'
                    f'(disponible {currency} {remaining:,.2f})</span></span></div>'
                    f'<div style="background:rgba(255,255,255,.08);border-radius:100px;'
                    f'height:7px;overflow:hidden;display:flex">'
                    f'{segments}'
                    f'</div>'
                    f'<div style="display:flex;gap:.8rem;font-size:.65rem;color:rgba(148,163,184,.55);'
                    f'margin-top:.30rem">'
                    + (f'<span><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#22c55e;margin-right:.30rem"></span>'
                       f'En uso {currency} {green_val:,.2f}</span>' if green_val > 0 else "")
                    + (f'<span><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#ef4444;margin-right:.30rem"></span>'
                       f'Perdido {currency} {lost_val:,.2f}</span>' if lost_val > 0 else "")
                    + (f'<span><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#f59e0b;margin-right:.30rem"></span>'
                       f'Flotante {currency} {float_val:,.2f}</span>' if float_val > 0 else "")
                    + f'</div></div>'
                )

            st.markdown(
                f'<div style="border:1px solid rgba(37,99,235,.25);border-radius:14px;'
                f'background:linear-gradient(135deg,rgba(37,99,235,.07),rgba(79,70,229,.03));'
                f'padding:.85rem 1.1rem;margin:.4rem 0 .6rem">'
                f'<div style="display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;'
                f'margin-bottom:.15rem">'
                f'<span style="font-size:1rem">📊</span>'
                f'<span style="font-weight:800;color:#e2e8f0">Utilización del presupuesto '
                f'<span style="color:rgba(148,163,184,.55);font-weight:500;font-size:.78rem">'
                f'(actualizado por ingresos a inventario)</span></span>'
                f'{_proj_state_pill}{_lost_chip_h}{_float_chip_h}'
                f'</div>'
                + (_util_bar_segmented("Soles (S/.)", _orig_s_h, _green_s, _hlost_s, _hflt_s, _rem_s_h, "S/") if _orig_s_h > 0 else "")
                + (_util_bar_segmented("Dólares ($)", _orig_d_h, _green_d, _hlost_d, _hflt_d, _rem_d_h, "$")  if _orig_d_h > 0 else "")
                + f'<div style="display:flex;gap:1rem;font-size:.71rem;color:rgba(148,163,184,.65);'
                  f'margin-top:.55rem;flex-wrap:wrap">'
                  f'<span>🔒 Bloqueado: <strong style="color:#93c5fd">S/ {_hlock_s:,.2f}</strong> · '
                  f'<strong style="color:#93c5fd">$ {_hlock_d:,.2f}</strong></span>'
                  + (f'<span>⏸ Pendiente: <strong style="color:#fbbf24">S/ {_hpend_s:,.2f}</strong> · '
                     f'<strong style="color:#fbbf24">$ {_hpend_d:,.2f}</strong></span>'
                     if _hpend_s > 0 or _hpend_d > 0 else "")
                  + (f'<span>❌ Perdido: <strong style="color:#f87171">S/ {_hlost_s:,.2f}</strong> · '
                     f'<strong style="color:#f87171">$ {_hlost_d:,.2f}</strong></span>'
                     if _hlost_s > 0 or _hlost_d > 0 else "")
                  + (f'<span>⏳ Flotante: <strong style="color:#fbbf24">S/ {_hflt_s:,.2f}</strong> · '
                     f'<strong style="color:#fbbf24">$ {_hflt_d:,.2f}</strong></span>'
                     if _hflt_s > 0 or _hflt_d > 0 else "")
                  + f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            cost_color = (
                "#34d399" if bud.budget_soles == 0 or total_cost <= bud.budget_soles * 0.70
                else ("#fbbf24" if total_cost <= bud.budget_soles * 0.90 else "#f87171")
            )
            st.markdown(f"""
            <div class="hist-kpis">
              <div class="hist-kpi">
                <div class="hist-kpi-icon">&#8593;</div>
                <div>
                  <div class="hist-kpi-val">{summary['total_in']:,}</div>
                  <div class="hist-kpi-label">Unidades ingresadas</div>
                </div>
              </div>
              <div class="hist-kpi">
                <div class="hist-kpi-icon">&#8595;</div>
                <div>
                  <div class="hist-kpi-val">{summary['total_out']:,}</div>
                  <div class="hist-kpi-label">Unidades despachadas</div>
                </div>
              </div>
              <div class="hist-kpi" style="border-color:rgba(52,211,153,.24);background:rgba(52,211,153,.05);">
                <div class="hist-kpi-icon" style="background:rgba(52,211,153,.18);color:{cost_color};font-size:.75rem;font-weight:800;">S/</div>
                <div>
                  <div class="hist-kpi-val" style="color:{cost_color};">S/ {total_cost:,.2f}</div>
                  <div class="hist-kpi-label">Costo en materiales</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            _tc_hist = st.session_state.get("_bud_tc", 3.75)

            if not costs:
                st.info("Sin despachos registrados desde la creación de este proyecto.")
            else:
                rows_html = "".join(f"""
                <tr>
                  <td><span class="pcode">{r['code']}</span></td>
                  <td>{r['material']}</td>
                  <td style="text-align:center">{r['unit']}</td>
                  <td style="text-align:right">{r['total_qty']:,}</td>
                  <td style="text-align:right">
                    {"<span class='p-cost-amber'>S/ " + f"{r['unit_price']:,.2f}</span>" if r['unit_price'] > 0 else "<span class='p-cost-dim'>—</span>"}
                  </td>
                  <td style="text-align:right">
                    {"<span class='p-cost-green'>S/ " + f"{r['total_cost']:,.2f}</span>" if r['total_cost'] > 0 else "<span class='p-cost-dim'>—</span>"}
                  </td>
                  <td style="text-align:right">
                    {"<span style='color:#60a5fa;font-weight:700'>$ " + f"{r['unit_price_dolares']:,.2f}</span>" if r.get('unit_price_dolares', 0) > 0 else "<span class='p-cost-dim'>—</span>"}
                  </td>
                  <td style="text-align:right">
                    {"<span style='color:#34d399;font-weight:800'>$ " + f"{r['total_cost_dolares']:,.2f}</span>" if r.get('total_cost_dolares', 0) > 0 else "<span class='p-cost-dim'>—</span>"}
                  </td>
                </tr>""" for r in costs)

                st.markdown(f"""
                <table class="proj-cost-table">
                  <thead><tr>
                    <th>Código</th>
                    <th>Material</th>
                    <th style="text-align:center">Unidad</th>
                    <th style="text-align:right">Cant. Despachada</th>
                    <th style="text-align:right">Precio Unit. S/.</th>
                    <th style="text-align:right">Costo Total S/.</th>
                    <th style="text-align:right">Precio Unit. $</th>
                    <th style="text-align:right">Costo Total $</th>
                  </tr></thead>
                  <tbody>{rows_html}</tbody>
                  <tfoot><tr>
                    <td colspan="5" style="color:rgba(255,255,255,.52);">
                      Total costo materiales &nbsp;·&nbsp; desde inicio del proyecto
                    </td>
                    <td style="text-align:right;color:#34d399;">S/ {total_cost:,.2f}</td>
                    <td></td>
                    <td style="text-align:right;color:#34d399;">$ {total_cost_dol:,.2f}</td>
                  </tr></tfoot>
                </table>
                """, unsafe_allow_html=True)

# ── Historial Global de Costos de Materiales ──────────────────────────────────
st.markdown('<div class="sec-title">&#128202; Historial Global de Costos de Materiales</div>', unsafe_allow_html=True)

# Opciones: "Rango personalizado" + cada proyecto registrado
_proj_options = ["Rango personalizado"] + [b.name for b in budgets]
_proj_map     = {b.name: b for b in budgets}

col_sel, col_d1, col_d2, _pad = st.columns([2.6, 2.0, 2.0, 3.4])
with col_sel:
    _scope_sel = st.selectbox(
        "Ámbito",
        _proj_options,
        index=0,
        key="gbl_scope",
        help="Selecciona un proyecto para acotar el período entre su creación y su finalización (o hoy si sigue activo).",
    )

_is_proj_scope = _scope_sel != "Rango personalizado"
if _is_proj_scope:
    _sel_bud   = _proj_map[_scope_sel]
    _proj_from = _sel_bud.created_at.date() if _sel_bud.created_at else date.today()
    _proj_to   = (_sel_bud.finished_at.date() if _sel_bud.finished_at else date.today())
else:
    _proj_from = date.today() - timedelta(days=365)
    _proj_to   = date.today()

with col_d1:
    d_from = st.date_input(
        "Desde", value=_proj_from, key="gbl_from", disabled=_is_proj_scope,
    )
with col_d2:
    d_to   = st.date_input(
        "Hasta", value=_proj_to, key="gbl_to", disabled=_is_proj_scope,
    )

# Cuando hay proyecto seleccionado, el rango se fija a su ciclo de vida
if _is_proj_scope:
    d_from = _proj_from
    d_to   = _proj_to

desde  = datetime.combine(d_from, datetime.min.time())
hasta  = datetime.combine(d_to + timedelta(days=1), datetime.min.time())

_scope_budget_id = _sel_bud.id if _is_proj_scope else None
g_costs, g_total, g_total_dol = get_dispatch_costs(
    db, since=desde, until=hasta, budget_id=_scope_budget_id,
)
g_summary        = get_movement_summary(
    db, since=desde, until=hasta, budget_id=_scope_budget_id,
)

days_range = (d_to - d_from).days + 1
_scope_label = f"Proyecto: {_scope_sel}" if _is_proj_scope else "Rango personalizado"
st.markdown(f"""
<div class="glob-hist-header">
  <span class="glob-hist-title">&#128202; {_scope_label}</span>
  <span class="glob-hist-range">
    {d_from.strftime("%d/%m/%Y")} &nbsp;&#8594;&nbsp; {d_to.strftime("%d/%m/%Y")}
    &nbsp;·&nbsp; {days_range} día{"s" if days_range != 1 else ""}
    &nbsp;·&nbsp; {len(g_costs)} material{"es" if len(g_costs) != 1 else ""}
  </span>
</div>
""", unsafe_allow_html=True)

gk1, gk2, gk3, gk4 = st.columns(4, gap="medium")
gk1.markdown(f"""<div class="glob-kpi gk-violet">
  <div class="glob-kpi-label">Unidades Ingresadas</div>
  <div class="glob-kpi-val">{g_summary['total_in']:,}</div>
  <div class="glob-kpi-sub">Entradas al sistema</div>
</div>""", unsafe_allow_html=True)

gk2.markdown(f"""<div class="glob-kpi gk-teal">
  <div class="glob-kpi-label">Unidades Despachadas</div>
  <div class="glob-kpi-val">{g_summary['total_out']:,}</div>
  <div class="glob-kpi-sub">Salidas registradas</div>
</div>""", unsafe_allow_html=True)

gk3.markdown(f"""<div class="glob-kpi gk-green">
  <div class="glob-kpi-label">Costo Total S/.</div>
  <div class="glob-kpi-val">S/ {g_total:,.0f}</div>
  <div class="glob-kpi-sub">Basado en precios de materiales</div>
</div>""", unsafe_allow_html=True)

gk4.markdown(f"""<div class="glob-kpi gk-blue">
  <div class="glob-kpi-label">Costo Total $</div>
  <div class="glob-kpi-val">$ {g_total_dol:,.0f}</div>
  <div class="glob-kpi-sub">Basado en precios en dólares</div>
</div>""", unsafe_allow_html=True)

if not g_costs:
    st.info("No hay despachos en el período seleccionado.")
else:
    g_rows_html = "".join(f"""
    <tr>
      <td><span class="mat-chip">{r['code']}</span></td>
      <td>{r['material']}</td>
      <td style="text-align:center">{r['unit']}</td>
      <td style="text-align:right">{r['total_qty']:,}</td>
      <td style="text-align:right">
        {"<span class='gcost-blue'>S/ " + f"{r['unit_price']:,.2f}</span>" if r['unit_price'] > 0 else "<span class='gcost-dim'>—</span>"}
      </td>
      <td style="text-align:right">
        {"<span class='gcost-green'>S/ " + f"{r['total_cost']:,.2f}</span>" if r['total_cost'] > 0 else "<span class='gcost-dim'>—</span>"}
      </td>
      <td style="text-align:right">
        {"<span style='color:#60a5fa;font-weight:700'>$ " + f"{r['unit_price_dolares']:,.2f}</span>" if r.get('unit_price_dolares', 0) > 0 else "<span class='gcost-dim'>—</span>"}
      </td>
      <td style="text-align:right">
        {"<span style='color:#34d399;font-weight:700'>$ " + f"{r['total_cost_dolares']:,.2f}</span>" if r.get('total_cost_dolares', 0) > 0 else "<span class='gcost-dim'>—</span>"}
      </td>
    </tr>""" for r in g_costs)

    st.markdown(f"""
    <table class="gcost-table">
      <thead><tr>
        <th>Código</th>
        <th>Material</th>
        <th style="text-align:center">Unidad</th>
        <th style="text-align:right">Cant. Despachada</th>
        <th style="text-align:right">Precio Unit. S/.</th>
        <th style="text-align:right">Costo Total S/.</th>
        <th style="text-align:right">Precio Unit. $</th>
        <th style="text-align:right">Costo Total $</th>
      </tr></thead>
      <tbody>{g_rows_html}</tbody>
      <tfoot><tr>
        <td colspan="5" style="color:rgba(255,255,255,.55);">
          Total &nbsp;·&nbsp; período seleccionado
        </td>
        <td style="text-align:right;color:#34d399;">S/ {g_total:,.2f}</td>
        <td></td>
        <td style="text-align:right;color:#34d399;">$ {g_total_dol:,.2f}</td>
      </tr></tfoot>
    </table>
    """, unsafe_allow_html=True)

    top_chart = [r for r in g_costs if r["total_cost"] > 0][:10]
    if top_chart:
        st.markdown('<div class="gcost-chart-wrap">', unsafe_allow_html=True)
        fig = go.Figure(go.Bar(
            x=[r["material"] for r in top_chart],
            y=[r["total_cost"] for r in top_chart],
            marker=dict(
                color=[r["total_cost"] for r in top_chart],
                colorscale=[[0, "#0891b2"], [0.5, "#059669"], [1, "#34d399"]],
                showscale=False,
            ),
            text=[f"S/ {r['total_cost']:,.0f}" for r in top_chart],
            textposition="outside",
            textfont=dict(color="#94a3b8", size=10),
        ))
        fig.update_layout(
            title=dict(text="Top materiales por costo despachado (S/.)", font=dict(size=13, color="#94a3b8")),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", size=11),
            margin=dict(t=48, b=10, l=0, r=0),
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            yaxis=dict(gridcolor="rgba(255,255,255,.06)", tickprefix="S/ "),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    elif g_costs:
        st.info("Configure los precios unitarios en Materiales para visualizar el gráfico de costos.")

db.close()
