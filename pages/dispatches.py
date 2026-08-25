# -*- coding: utf-8 -*-
import streamlit as st
import io, csv
from datetime import timezone, timedelta
from database import SessionLocal
from services.dispatch_service import create_dispatch, delete_dispatch
from services.budget_service import get_budgets
from models.dispatch import Dispatch
from models.requirement import Requirement
from models.warehouse import Warehouse
from utils.auth import require_cliente, get_current_user_id, get_current_username
from utils.navbar import render_navbar, render_sidebar_menu
from utils.pdf_generator import generate_dispatch_pdf
import time

_LIMA = timezone(timedelta(hours=-5))

def _fmt_lima(dt):
    if dt is None:
        return "—"
    return dt.replace(tzinfo=timezone.utc).astimezone(_LIMA).strftime("%d/%m/%Y %H:%M")

def _build_guia_html(dispatch, req_id, obra_name, principal_name, disp_date_str):
    def _price(it):
        return float(it.material.unit_price or 0) if it.material else 0.0
    rows = "".join(
        f"<tr><td>{i+1}</td>"
        f"<td>{(it.material.name if it.material else f'Material {it.material_id}')}</td>"
        f"<td>{(it.material.unit if it.material else '')}</td>"
        f"<td style='text-align:right'>{it.dispatched_qty}</td>"
        f"<td style='text-align:right'>{'S/ ' + f'{_price(it):,.2f}' if _price(it) > 0 else '—'}</td>"
        f"<td style='text-align:right'>{'S/ ' + f'{it.dispatched_qty * _price(it):,.2f}' if _price(it) > 0 else '—'}</td>"
        f"</tr>"
        for i, it in enumerate(dispatch.items)
    )
    total_qty  = sum(it.dispatched_qty for it in dispatch.items)
    total_cost = sum(it.dispatched_qty * _price(it) for it in dispatch.items)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Guía de Remisión {dispatch.guia_number}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Arial,sans-serif;color:#1a1a2e;padding:2cm;font-size:13px}}
.header{{text-align:center;border-bottom:3px solid #2563eb;padding-bottom:1rem;margin-bottom:1.5rem}}
.title{{font-size:1.6rem;font-weight:bold;color:#2563eb;letter-spacing:.05em}}
.guia-num{{font-size:1rem;font-weight:bold;margin-top:.3rem;color:#1e40af}}
.subtitle{{font-size:.8rem;color:#6b7280;margin-top:.2rem}}
.info-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}}
.info-block{{border:1px solid #e2e8f0;border-radius:6px;padding:.75rem}}
.info-label{{font-size:.65rem;text-transform:uppercase;color:#6b7280;font-weight:bold;letter-spacing:.05em}}
.info-value{{font-size:.9rem;font-weight:bold;margin-top:.2rem;color:#1a1a2e}}
table{{width:100%;border-collapse:collapse;margin-bottom:1.5rem}}
th{{background:#2563eb;color:#fff;padding:.5rem .75rem;text-align:left;font-size:.78rem}}
td{{padding:.45rem .75rem;border-bottom:1px solid #e2e8f0;font-size:.85rem}}
tr:nth-child(even) td{{background:#f8fafc}}
.total-row td{{font-weight:bold;border-top:2px solid #2563eb;background:#eff6ff}}
.footer{{margin-top:1.5rem;text-align:center;font-size:.7rem;color:#9ca3af;border-top:1px solid #e2e8f0;padding-top:.75rem}}
.sign-grid{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;margin-top:2rem}}
.sign-box{{border-top:1px solid #9ca3af;padding-top:.4rem;font-size:.75rem;color:#6b7280;text-align:center}}
@media print{{body{{padding:.5cm}}}}
</style>
</head>
<body>
<div class="header">
  <div class="title">GUÍA DE REMISIÓN</div>
  <div class="guia-num">{dispatch.guia_number}</div>
  <div class="subtitle">Sistema MRP</div>
</div>
<div class="info-grid">
  <div class="info-block">
    <div class="info-label">Fecha de Despacho</div>
    <div class="info-value">{disp_date_str}</div>
  </div>
  <div class="info-block">
    <div class="info-label">N° Requerimiento</div>
    <div class="info-value">#{req_id}</div>
  </div>
  <div class="info-block">
    <div class="info-label">Almacén de Origen</div>
    <div class="info-value">{principal_name}</div>
  </div>
  <div class="info-block">
    <div class="info-label">Almacén de Destino (Obra)</div>
    <div class="info-value">{obra_name}</div>
  </div>
</div>
<table>
  <thead><tr><th>#</th><th>Material</th><th>Unidad</th><th style="text-align:right">Cantidad</th><th style="text-align:right">P. Unit.</th><th style="text-align:right">Total</th></tr></thead>
  <tbody>
    {rows}
    <tr class="total-row"><td colspan="3">TOTAL</td><td style="text-align:right">{total_qty}</td><td></td><td style="text-align:right">{'S/ ' + f'{total_cost:,.2f}' if total_cost > 0 else '—'}</td></tr>
  </tbody>
</table>
<div class="sign-grid">
  <div class="sign-box">Entregado por</div>
  <div class="sign-box">Recibido por</div>
</div>
<div class="footer">Generado por Sistema MRP · {disp_date_str} · Para imprimir use Ctrl+P</div>
</body>
</html>"""

st.set_page_config(page_title="Despachos — Sistema MRP", layout="wide", initial_sidebar_state="expanded")

render_navbar()
require_cliente()

st.markdown("""
<style>
[data-testid="stHeader"]     { background: transparent !important; }
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stAppViewBlockContainer"] { padding-top: 1.2rem !important; }
.op-hero {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: .5rem;
    padding: 1rem 1.5rem 1.2rem; border-radius: 20px;
    background: linear-gradient(135deg, #0a1628 0%, #1a3470 50%, #2563eb 100%);
    margin-bottom: 1.5rem; box-shadow: 0 8px 32px rgba(37,99,235,.28);
}
.op-hero-left { display: flex; align-items: center; gap: 1rem; }
.op-hero-icon {
    width: 52px; height: 52px; border-radius: 14px;
    background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,.18);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 1.5rem;
}
.op-hero h1 { font-size: 1.45rem; font-weight: 900; color: #fff; margin: 0; }
.op-hero p  { font-size: .80rem; color: rgba(255,255,255,.65); margin: 3px 0 0; }
.op-badge {
    background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,.22);
    border-radius: 30px; padding: .32rem .9rem;
    font-size: .75rem; font-weight: 700; color: rgba(255,255,255,.85); white-space: nowrap;
}
.sec-title {
    font-size: .95rem; font-weight: 800;
    display: flex; align-items: center; gap: .55rem;
    padding-left: .8rem; border-left: 4px solid #2563eb;
    margin: 1.8rem 0 .85rem;
}
[data-testid="stExpander"] {
    border-radius: 16px !important; border: 1px solid rgba(37,99,235,.18) !important;
    background: rgba(6,13,28,.35) !important; overflow: hidden !important;
}
details[data-testid="stExpander"] > summary {
    padding: .82rem 1.2rem !important; font-size: .88rem !important;
    font-weight: 700 !important; color: #93c5fd !important;
}
details[data-testid="stExpander"][open] > summary {
    border-bottom: 1px solid rgba(37,99,235,.15) !important;
}
label[data-testid="stWidgetLabel"] p { font-size: .80rem !important; font-weight: 600 !important; }
[data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; box-shadow: 0 2px 14px rgba(37,99,235,.35) !important;
    transition: all .2s !important;
}
[data-testid="stBaseButton-primary"]:hover { opacity: .9 !important; transform: translateY(-1px) !important; }
[data-testid="stAlert"] { border-radius: 10px !important; }

.badge-partial   { display:inline-block; padding:.18rem .65rem; border-radius:20px; font-size:.70rem; font-weight:700; background:rgba(249,115,22,.18);  color:#fb923c; }
.badge-fulfilled { display:inline-block; padding:.18rem .65rem; border-radius:20px; font-size:.70rem; font-weight:700; background:rgba(16,185,129,.18); color:#34d399; }

.disp-item {
    display: flex; align-items: center; justify-content: space-between;
    padding: .6rem 1rem; border-radius: 10px;
    border: 1px solid rgba(37,99,235,.12); background: rgba(37,99,235,.04);
    margin-bottom: .4rem;
}
.disp-item-name { font-size: .85rem; font-weight: 700; }
.disp-item-meta { font-size: .75rem; opacity: .60; }

/* ── Historial de despachos ── */
.disp-hist-card {
    display: flex; gap: 1.2rem; padding: .85rem 1.2rem;
    border-radius: 14px; border: 1px solid rgba(37,99,235,.16);
    background: rgba(37,99,235,.04);
    flex-wrap: wrap; position: relative; overflow: hidden;
}
.disp-hist-card::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px; background: linear-gradient(180deg, #2563eb, #1d4ed8);
    border-radius: 3px 0 0 3px;
}
.disp-hist-guia { min-width: 130px; display: flex; flex-direction: column; gap: .14rem; }
.disp-hist-lbl  { font-size: .58rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: rgba(148,163,184,.45); }
.disp-hist-num  { font-size: .88rem; font-weight: 900; color: #93c5fd; }
.disp-hist-date { font-size: .68rem; color: rgba(148,163,184,.45); }
.disp-hist-mats { flex: 1; min-width: 160px; }
.disp-hist-status { display: flex; align-items: center; }
.hist-mat-pill {
    display: inline-flex; align-items: center; gap: .35rem;
    background: rgba(37,99,235,.10); border: 1px solid rgba(37,99,235,.22);
    border-radius: 16px; padding: .18rem .6rem;
    font-size: .72rem; font-weight: 700; color: #93c5fd;
    margin: .1rem .2rem .1rem 0;
}
.hist-mat-pill .pill-lbl {
    font-size: .60rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .04em;
    color: rgba(148,163,184,.65);
}
.hist-mat-pill .pill-val { color: #93c5fd; font-weight: 700; }
.hist-mat-pill .pill-sep { color: rgba(148,163,184,.30); margin: 0 .1rem; }

.disp-hist-meta {
    display: flex; gap: .35rem; flex-wrap: wrap; margin-top: .42rem;
}
.hist-meta-chip, .disp-proj-chip {
    display: inline-flex; align-items: baseline; gap: .35rem;
    padding: .15rem .55rem; border-radius: 8px;
    background: rgba(15,23,42,.40);
    border: 1px solid rgba(255,255,255,.05);
}
.disp-proj-chip {
    background: rgba(5,150,105,.10);
    border-color: rgba(5,150,105,.25);
}
.disp-proj-chip.empty {
    background: rgba(239,68,68,.06);
    border-color: rgba(239,68,68,.18);
}
.hist-mini-lbl {
    font-size: .58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .05em;
    color: rgba(148,163,184,.55);
}
.hist-mini-val { font-size: .72rem; font-weight: 700; color: #e2e8f0; }
.disp-proj-chip .hist-mini-val { color: #6ee7b7; }
.disp-proj-chip.empty .hist-mini-val { color: #fca5a5; font-style: italic; }

/* ── Delete confirm strip ── */
.del-confirm-strip {
    display: flex; align-items: center; gap: .7rem;
    padding: .65rem 1rem; border-radius: 10px;
    border: 1px solid rgba(239,68,68,.28);
    background: rgba(239,68,68,.07);
    margin-bottom: .4rem; flex-wrap: wrap;
}
.del-confirm-strip span { flex: 1; font-size: .82rem; color: #fca5a5; font-weight: 600; }

/* ── Cabecera de "Materiales a Despachar" ── */
.disp-hdr {
    display: flex; gap: .5rem; flex-wrap: wrap;
    margin: .2rem 0 1rem;
}
.disp-hdr-chip {
    display: inline-flex; align-items: baseline; gap: .45rem;
    padding: .32rem .72rem; border-radius: 10px;
    background: rgba(37,99,235,.07);
    border: 1px solid rgba(37,99,235,.18);
}
.disp-hdr-chip.disp-hdr-proj {
    background: rgba(5,150,105,.10);
    border-color: rgba(5,150,105,.28);
}
.disp-hdr-chip.disp-hdr-proj-empty {
    background: rgba(239,68,68,.08);
    border-color: rgba(239,68,68,.22);
}
.disp-hdr-lbl {
    font-size: .60rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .07em;
    color: rgba(148,163,184,.55);
}
.disp-hdr-val { font-size: .82rem; font-weight: 800; color: #e2e8f0; }
.disp-hdr-chip.disp-hdr-proj .disp-hdr-val { color: #6ee7b7; }
.disp-hdr-chip.disp-hdr-proj-empty .disp-hdr-val { color: #fca5a5; font-style: italic; }

/* ── Tarjeta de ítem a despachar ── */
.disp-item-card {
    padding: .75rem 1.1rem; border-radius: 13px;
    border: 1px solid rgba(37,99,235,.18);
    background: linear-gradient(135deg, rgba(37,99,235,.06), rgba(79,70,229,.03));
    margin-bottom: .35rem;
}
.disp-item-card.disp-item-nostock {
    border-color: rgba(239,68,68,.30);
    background: linear-gradient(135deg, rgba(239,68,68,.07), rgba(220,38,38,.03));
}
.disp-item-name {
    font-weight: 800; color: #f1f5f9; font-size: .95rem;
    padding-bottom: .4rem; margin-bottom: .55rem;
    border-bottom: 1px solid rgba(37,99,235,.14);
}
.disp-item-card.disp-item-nostock .disp-item-name { color: #fca5a5; }
.disp-item-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
    gap: .45rem .8rem;
}
.disp-item-field {
    display: flex; flex-direction: column; gap: .12rem;
    padding: .3rem .55rem;
    border-radius: 8px;
    background: rgba(15,23,42,.30);
    border: 1px solid rgba(255,255,255,.04);
}
.disp-item-lbl {
    font-size: .58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .07em;
    color: rgba(148,163,184,.55);
}
.disp-item-val { font-size: .85rem; font-weight: 800; color: #e2e8f0; line-height: 1.2; }
.disp-item-val em { font-style: normal; opacity: .55; font-weight: 600; font-size: .75rem; }
.disp-item-val.pend     { color: #fbbf24; }
.disp-item-val.price-s  { color: #34d399; }
.disp-item-val.price-d  { color: #60a5fa; }
.disp-item-warn {
    margin-top: .55rem; padding: .4rem .7rem;
    border-radius: 8px; font-size: .74rem; font-weight: 700;
    color: #f87171; background: rgba(239,68,68,.10);
    border: 1px solid rgba(239,68,68,.22);
}

/* Cantidad a despachar */
.disp-qty-lbl {
    font-size: .68rem; font-weight: 700; color: rgba(148,163,184,.65);
    text-transform: uppercase; letter-spacing: .06em;
    padding: .55rem 0 0 .4rem;
}
.disp-qty-nostock {
    padding: .55rem .8rem; border-radius: 10px;
    border: 1px solid rgba(239,68,68,.30);
    background: rgba(239,68,68,.05);
    text-align: center; font-size: .82rem;
    font-weight: 700; color: #f87171;
}
.disp-qty-totalbox {
    display: flex; align-items: center; justify-content: flex-end;
    gap: .6rem; padding: .55rem .9rem; border-radius: 10px;
    border: 1px solid rgba(251,191,36,.22);
    background: rgba(251,191,36,.05);
    flex-wrap: wrap;
}
.disp-qty-totalbox.empty {
    border-color: rgba(148,163,184,.18);
    background: rgba(148,163,184,.05);
    color: rgba(148,163,184,.40); justify-content: center;
}
.disp-qty-totallbl {
    font-size: .65rem; font-weight: 700;
    color: rgba(148,163,184,.65);
    text-transform: uppercase; letter-spacing: .06em;
    margin-right: auto;
}
.disp-qty-s { font-size: .92rem; font-weight: 900; color: #fbbf24; }
.disp-qty-d { font-size: .92rem; font-weight: 900; color: #60a5fa; }
.disp-qty-empty { font-size: .76rem; color: rgba(148,163,184,.45); font-style: italic; }

.disp-total-bar {
    display: flex; align-items: center; justify-content: flex-end;
    gap: .9rem; margin: .35rem 0 .6rem;
    padding: .6rem 1.1rem; border-radius: 10px;
    border: 1px solid rgba(251,191,36,.24);
    background: rgba(251,191,36,.05);
    flex-wrap: wrap;
}
.disp-total-lbl { font-size: .74rem; color: rgba(148,163,184,.65); font-weight: 600; margin-right: auto; }
.disp-total-s   { font-size: 1rem; font-weight: 900; color: #fbbf24; }
.disp-total-d   { font-size: 1rem; font-weight: 900; color: #60a5fa; }

/* badge-pending para cabecera */
.badge-pending {
    display:inline-block; padding:.18rem .65rem; border-radius:20px;
    font-size:.70rem; font-weight:700;
    background:rgba(234,179,8,.18); color:#fbbf24;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_menu()


st.title("🚚 Despachos")

db       = SessionLocal()
owner_id = get_current_user_id()


requirements = (
    db.query(Requirement)
    .join(Warehouse, Requirement.warehouse_id_obra == Warehouse.id)
    .filter(
        Requirement.status.in_(["pending", "partial"]),
        Warehouse.owner_id == owner_id,
    )
    .order_by(Requirement.created_at.desc())
    .all()
)

all_warehouses_d = db.query(Warehouse).filter(Warehouse.owner_id == owner_id).all()
wh_id_to_name    = {w.id: w.name for w in all_warehouses_d}
principal_wh     = next((w for w in all_warehouses_d if w.type == "principal"), None)

all_dispatches = (
    db.query(Dispatch)
    .join(Requirement, Dispatch.requirement_id == Requirement.id)
    .join(Warehouse, Requirement.warehouse_id_obra == Warehouse.id)
    .filter(Warehouse.owner_id == owner_id)
    .filter(Dispatch.status != "cancelled")
    .order_by(Dispatch.dispatch_date.desc())
    .all()
)

# ── Mensajes post-acción ──────────────────────────────────────────────────────
if st.session_state.get("disp_del_ok"):
    st.success(st.session_state.pop("disp_del_ok"))
if st.session_state.get("disp_del_err"):
    st.error(st.session_state.pop("disp_del_err"))

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="op-hero">
  <div class="op-hero-left">
    <div class="op-hero-icon">&#128666;</div>
    <div>
      <h1>Despachos</h1>
      <p>Genera despachos a partir de requerimientos cumplidos o parciales</p>
    </div>
  </div>
  <div class="op-badge">{len(requirements)} req. disponibles · {len(all_dispatches)} despachos</div>
</div>
""", unsafe_allow_html=True)

# ── Instrucciones + Presupuestos Activos ──────────────────────────────────────
_, _col_budgets, _col_help = st.columns([4.6, 1.5, 1])
with _col_budgets.popover("📊 Presupuestos", use_container_width=True):
    st.markdown("#### Presupuestos Activos")
    _active_buds = [b for b in get_budgets(db) if b.is_active]
    if not _active_buds:
        st.info("No hay presupuestos activos registrados.")
    else:
        for _b in _active_buds:
            st.markdown(f"""
<div style="padding:.55rem .8rem;border-radius:10px;border:1px solid rgba(5,150,105,.25);
            background:rgba(5,150,105,.07);margin-bottom:.45rem">
  <div style="font-weight:800;font-size:.88rem;color:#6ee7b7">{_b.name}</div>
  <div style="font-size:.75rem;color:rgba(255,255,255,.55);margin-top:.18rem">
    S/ {_b.budget_soles:,.2f} &nbsp;·&nbsp; $ {_b.budget_dolares:,.2f}
  </div>
</div>""", unsafe_allow_html=True)
with _col_help.popover("Instrucciones", use_container_width=True):
    st.markdown("#### Despachos — Guía de uso")
    st.markdown("""
**Generar un despacho**
1. Selecciona un requerimiento **Pendiente** o **Parcial** que tenga materiales reservados.
2. Verifica la lista de materiales y ajusta las cantidades a despachar si lo necesitas (máximo: la cantidad reservada de cada ítem).
3. Presiona **Generar Despacho**; el sistema reducirá el stock reservado y registrará el despacho.

**Flujo completo**
- Requerimiento → **Despacho** → Recepción.
- Después de generar el despacho, ve a la sección **Recepciones** para confirmar la llegada del material al almacén de obra.

> Solo aparecen requerimientos con al menos un material con stock reservado listo para despachar.
""")

# ── Generar despacho ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Generar Despacho</div>', unsafe_allow_html=True)


if not requirements:
    st.info("No hay requerimientos con estado parcial o cumplido disponibles para despachar.")
else:
    _STATUS_DISP = {"pending": "Pendiente", "partial": "Parcial"}
    req_options = {
        f"Req #{r.id} — {_fmt_lima(r.created_at)} — {_STATUS_DISP.get(r.status, r.status)}": r.id
        for r in requirements
    }


    selected_label = st.selectbox("Selecciona requerimiento", list(req_options.keys()), key="disp_req_sel")
    req_id = req_options[selected_label]
    req    = next((r for r in requirements if r.id == req_id), None)

    if req:
        st.markdown('<div class="sec-title">Materiales a Despachar</div>', unsafe_allow_html=True)

        # Cabecera con proyecto + obra + estado
        _badge_cls  = "badge-partial" if req.status == "partial" else "badge-pending"
        _badge_txt  = "Parcial" if req.status == "partial" else "Pendiente"
        _req_obra   = wh_id_to_name.get(req.warehouse_id_obra, f"Almacén #{req.warehouse_id_obra}")
        _req_proj   = getattr(req, "budget_name", None)
        _proj_chip  = (
            f'<span class="disp-hdr-chip disp-hdr-proj">'
            f'<span class="disp-hdr-lbl">Proyecto</span>'
            f'<span class="disp-hdr-val">{_req_proj}</span></span>'
            if _req_proj else
            '<span class="disp-hdr-chip disp-hdr-proj-empty">'
            '<span class="disp-hdr-lbl">Proyecto</span>'
            '<span class="disp-hdr-val">— sin proyecto —</span></span>'
        )
        st.markdown(
            '<div class="disp-hdr">'
              f'<span class="disp-hdr-chip"><span class="disp-hdr-lbl">Requerimiento</span>'
              f'<span class="disp-hdr-val">#{req.id}</span></span>'
              f'{_proj_chip}'
              f'<span class="disp-hdr-chip"><span class="disp-hdr-lbl">Almacén obra</span>'
              f'<span class="disp-hdr-val">{_req_obra}</span></span>'
              f'<span class="disp-hdr-chip"><span class="disp-hdr-lbl">Estado</span>'
              f'<span class="disp-hdr-val"><span class="{_badge_cls}">{_badge_txt}</span></span></span>'
            '</div>',
            unsafe_allow_html=True,
        )

        items         = []
        has_pending   = False  # ítems sin stock (no se pueden despachar aún)
        has_remaining = False  # ítems con saldo pendiente de despacho
        disp_cost_total   = 0.0
        disp_cost_total_d = 0.0

        for i, item in enumerate(req.items):
            pendiente   = item.requested_qty - item.fulfilled_qty
            sin_stock   = item.status == "pending"  # nunca se reservó stock
            if pendiente <= 0:
                continue

            has_remaining = True
            mat_name     = item.material.name if item.material else f"Material {item.material_id}"
            mat_unit     = (item.material.unit or "").strip() if item.material else ""
            unit_price   = float(item.material.unit_price or 0) if item.material else 0.0
            unit_price_d = float(item.material.unit_price_dolares or 0) if item.material else 0.0
            qty_lbl      = mat_unit if mat_unit else "uds"

            # Bloque visual del material (1 línea con labels)
            st.markdown(
                f'<div class="disp-item-card {"disp-item-nostock" if sin_stock else ""}">'
                  f'<div class="disp-item-name">{mat_name}</div>'
                  '<div class="disp-item-grid">'
                    f'<div class="disp-item-field"><span class="disp-item-lbl">Cantidad pendiente</span>'
                    f'<span class="disp-item-val pend">{pendiente}</span></div>'
                    f'<div class="disp-item-field"><span class="disp-item-lbl">Unidad</span>'
                    f'<span class="disp-item-val">{qty_lbl}</span></div>'
                    f'<div class="disp-item-field"><span class="disp-item-lbl">Precio unit. S/.</span>'
                    f'<span class="disp-item-val price-s">{"S/ " + f"{unit_price:,.2f}" if unit_price > 0 else "—"}</span></div>'
                    f'<div class="disp-item-field"><span class="disp-item-lbl">Precio unit. $</span>'
                    f'<span class="disp-item-val price-d">{"$ " + f"{unit_price_d:,.2f}" if unit_price_d > 0 else "—"}</span></div>'
                  '</div>'
                + (
                    '<div class="disp-item-warn">⚠ Sin stock reservado — agrega stock en Inventario.</div>'
                    if sin_stock else ""
                ) + '</div>',
                unsafe_allow_html=True,
            )

            # Fila de cantidad a despachar
            qcol_lbl, qcol_input, qcol_total = st.columns([2, 2, 3], gap="small")
            qcol_lbl.markdown(
                '<div class="disp-qty-lbl">Cantidad a despachar</div>',
                unsafe_allow_html=True,
            )

            if sin_stock:
                has_pending = True
                qcol_input.markdown(
                    "<div class='disp-qty-nostock'>Sin stock</div>",
                    unsafe_allow_html=True,
                )
                qcol_total.markdown(
                    "<div class='disp-qty-totalbox empty'>—</div>",
                    unsafe_allow_html=True,
                )
            else:
                with qcol_input:
                    qty = st.number_input(
                        "Cantidad",
                        min_value=0, max_value=pendiente, value=pendiente,
                        key=f"disp_qty_{i}_{item.material_id}",
                        label_visibility="collapsed",
                    )
                    if qty > 0:
                        items.append({"material_id": item.material_id, "qty": qty})

                item_total   = qty * unit_price
                item_total_d = qty * unit_price_d
                disp_cost_total   += item_total
                disp_cost_total_d += item_total_d
                _it_s = f'<span class="disp-qty-s">S/ {item_total:,.2f}</span>' if unit_price > 0 else ""
                _it_d = f'<span class="disp-qty-d">$ {item_total_d:,.2f}</span>' if unit_price_d > 0 else ""
                _it_body = (_it_s + _it_d) or "<span class='disp-qty-empty'>Sin precio</span>"
                qcol_total.markdown(
                    f"<div class='disp-qty-totalbox'><span class='disp-qty-totallbl'>Costo</span>{_it_body}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='margin-bottom:.55rem'></div>", unsafe_allow_html=True)

        if (disp_cost_total > 0 or disp_cost_total_d > 0) and has_remaining:
            _ts = f'<span class="disp-total-s">S/ {disp_cost_total:,.2f}</span>' if disp_cost_total > 0 else ""
            _td = f'<span class="disp-total-d">$ {disp_cost_total_d:,.2f}</span>' if disp_cost_total_d > 0 else ""
            st.markdown(
                '<div class="disp-total-bar">'
                  '<span class="disp-total-lbl">Costo total estimado del despacho</span>'
                  f'{_ts}{_td}'
                '</div>',
                unsafe_allow_html=True,
            )

            if not has_remaining:
                st.info("Todos los ítems de este requerimiento ya han sido despachados.")
            else:
                if has_pending and not items:
                    st.warning(
                        "Todos los ítems de este requerimiento están sin stock reservado.  \n"
                        "Ve a **Inventario** y agrega stock al almacén principal; "
                        "el sistema reservará automáticamente los materiales pendientes."
                    )
        # Usamos una clave única que incluya el ID del requerimiento para evitar duplicados
        if st.button("Generar Despacho", type="primary", key=f"btn_gen_disp_{req.id}", use_container_width=False):
            if not items:
                st.warning("Debes ingresar al menos una cantidad mayor a 0.")
            else:
                success, result = create_dispatch(db, req_id, items, user_id=owner_id, owner_id=owner_id)
                if success:
                    guia     = result
                    username = get_current_username() or f"Usuario #{owner_id}"
                    st.success(
                        f"Despacho generado exitosamente.  \n"
                        f"**Guía de Remisión:** {guia}  \n"
                        f"**Creado por:** {username}"
                    )
                    st.rerun()
                else:
                    st.error(result)

# ── Historial de Despachos ────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Historial de Despachos</div>', unsafe_allow_html=True)

if not all_dispatches:
    st.info("Aún no hay despachos registrados.")
else:
    # ── Filtros ───────────────────────────────────────────────────────────────
    obra_whs = [w for w in all_warehouses_d if w.type == "obra"]
    obra_filter_opts = {"Todos": None}
    obra_filter_opts.update({w.name: w.id for w in obra_whs})

    fc1, fc2, fc3 = st.columns([2, 2, 2], gap="medium")
    sel_obra_f  = fc1.selectbox("Filtrar por obra", list(obra_filter_opts.keys()), key="hist_obra_filter")
    date_from   = fc2.date_input("Desde", value=None, key="hist_date_from")
    date_to     = fc3.date_input("Hasta", value=None, key="hist_date_to")

    filtered = all_dispatches
    if obra_filter_opts[sel_obra_f] is not None:
        _oid = obra_filter_opts[sel_obra_f]
        filtered = [d for d in filtered if d.requirement.warehouse_id_obra == _oid]
    if date_from:
        filtered = [d for d in filtered if d.dispatch_date and d.dispatch_date.date() >= date_from]
    if date_to:
        filtered = [d for d in filtered if d.dispatch_date and d.dispatch_date.date() <= date_to]

    # ── Paginación ────────────────────────────────────────────────────────────
    HIST_PG = 10
    total_h  = len(filtered)
    total_hp = max(1, (total_h + HIST_PG - 1) // HIST_PG)
    hist_pg  = st.session_state.get("hist_disp_page", 1)
    hist_pg  = max(1, min(hist_pg, total_hp))
    page_d   = filtered[(hist_pg - 1) * HIST_PG: hist_pg * HIST_PG]

    pc1, pc2, pc3 = st.columns([1, 4, 1])
    if pc1.button("← Anterior", key="hist_prev", disabled=hist_pg <= 1):
        st.session_state["hist_disp_page"] = hist_pg - 1
        st.rerun()
    pc2.markdown(
        f"<div style='text-align:center;font-size:.78rem;color:rgba(148,163,184,.60);padding:.45rem 0'>"
        f"Página {hist_pg} de {total_hp} &nbsp;·&nbsp; {total_h} despachos</div>",
        unsafe_allow_html=True,
    )
    if pc3.button("Siguiente →", key="hist_next", disabled=hist_pg >= total_hp):
        st.session_state["hist_disp_page"] = hist_pg + 1
        st.rerun()

    st.markdown("<div style='margin-bottom:.5rem'></div>", unsafe_allow_html=True)

    # ── Cards ─────────────────────────────────────────────────────────────────
    for dispatch in page_d:
        req_d      = dispatch.requirement
        obra_name  = wh_id_to_name.get(req_d.warehouse_id_obra, f"Almacén #{req_d.warehouse_id_obra}")
        princ_name = principal_wh.name if principal_wh else "Almacén Principal"
        disp_date_str = _fmt_lima(dispatch.dispatch_date)
        has_receipt   = dispatch.receipt is not None
        recv_badge    = "badge-fulfilled" if has_receipt else "badge-partial"
        recv_text     = "Recibido" if has_receipt else "En tránsito"

        confirming = st.session_state.get("confirm_del_disp") == dispatch.id

        if not confirming:
            pills_html = "".join(
                f"<span class='hist-mat-pill'>"
                f"<span class='pill-lbl'>Nombre:</span>"
                f"<span class='pill-val'>{(it.material.name if it.material else f'Mat.{it.material_id}')}</span>"
                f"<span class='pill-sep'>·</span>"
                f"<span class='pill-lbl'>Cant.:</span>"
                f"<span class='pill-val'>{it.dispatched_qty}"
                f"{(' ' + it.material.unit) if it.material and it.material.unit else ''}</span>"
                f"</span>"
                for it in dispatch.items
            )
            proj_name_h = getattr(req_d, "budget_name", None)
            proj_html   = (
                f"<span class='disp-proj-chip'><span class='hist-mini-lbl'>Proyecto:</span>"
                f"<span class='hist-mini-val'>{proj_name_h}</span></span>"
                if proj_name_h else
                "<span class='disp-proj-chip empty'>"
                "<span class='hist-mini-lbl'>Proyecto:</span>"
                "<span class='hist-mini-val'>— sin proyecto —</span></span>"
            )

            col_card, col_pdf, col_del = st.columns([7, 1, 1], gap="small")
            with col_card:
                st.markdown(f"""
<div class="disp-hist-card">
  <div class="disp-hist-guia">
    <div class="disp-hist-lbl">Guía de Remisión</div>
    <div class="disp-hist-num">{dispatch.guia_number or f'Despacho #{dispatch.id}'}</div>
    <div class="disp-hist-lbl" style="margin-top:.35rem">Fecha</div>
    <div class="disp-hist-date">{disp_date_str} (Lima)</div>
  </div>
  <div class="disp-hist-mats">
    <div class="disp-hist-lbl" style="margin-bottom:.25rem">Materiales</div>
    {pills_html or '<span style="font-size:.72rem;color:rgba(148,163,184,.35)">Sin ítems</span>'}
    <div class="disp-hist-meta">
      <span class="hist-meta-chip"><span class="hist-mini-lbl">Req.:</span>
        <span class="hist-mini-val">#{dispatch.requirement_id}</span></span>
      <span class="hist-meta-chip"><span class="hist-mini-lbl">Obra:</span>
        <span class="hist-mini-val">{obra_name}</span></span>
      {proj_html}
    </div>
  </div>
  <div class="disp-hist-status">
    <span class="{recv_badge}">{recv_text}</span>
  </div>
</div>""", unsafe_allow_html=True)

            guia_html = _build_guia_html(dispatch, req_d.id, obra_name, princ_name, disp_date_str)
            col_pdf.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            col_pdf.download_button(
                "PDF",
                data=guia_html.encode("utf-8"),
                file_name=f"{dispatch.guia_number or f'despacho_{dispatch.id}'}.html",
                mime="text/html",
                key=f"pdf_{dispatch.id}",
                use_container_width=True,
                help="Descargar guía de remisión (abrir en navegador e imprimir como PDF)",
            )
            col_del.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            if col_del.button("🗑", key=f"del_disp_{dispatch.id}", use_container_width=True,
                              help="Eliminar despacho"):
                st.session_state["confirm_del_disp"] = dispatch.id
                st.rerun()
        else:
            st.markdown(
                f"<div class='del-confirm-strip'><span>¿Eliminar despacho "
                f"<strong>{dispatch.guia_number}</strong>? "
                f"Se revertirán los cambios de inventario y se eliminará la recepción asociada si la hubiera.</span></div>",
                unsafe_allow_html=True,
            )
            c_yes, c_no = st.columns(2, gap="small")
            if c_yes.button("Confirmar eliminación", key=f"yes_disp_{dispatch.id}",
                            type="primary", use_container_width=True):
                ok, err = delete_dispatch(db, dispatch.id, owner_id)
                del st.session_state["confirm_del_disp"]
                if ok:
                    st.session_state["disp_del_ok"] = f"Despacho **{dispatch.guia_number}** eliminado correctamente."
                else:
                    st.session_state["disp_del_err"] = err
                st.rerun()
            if c_no.button("Cancelar", key=f"no_disp_{dispatch.id}", use_container_width=True):
                del st.session_state["confirm_del_disp"]
                st.rerun()

        st.markdown("<div style='margin-bottom:.3rem'></div>", unsafe_allow_html=True)

db.close()
