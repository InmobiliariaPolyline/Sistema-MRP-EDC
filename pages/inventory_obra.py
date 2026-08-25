# -*- coding: utf-8 -*-
import streamlit as st
from database import SessionLocal
from models.warehouse import Warehouse
from models.inventory import Inventory
from models.receipt import Receipt
from models.dispatch import Dispatch
from models.requirement import Requirement
from services.inventory_service import remove_stock
from utils.auth import require_cliente, get_current_user_id
from utils.navbar import render_navbar, render_sidebar_menu

st.set_page_config(page_title="Inventario Obra — Sistema MRP", layout="wide", initial_sidebar_state="expanded")

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
    background: linear-gradient(135deg, #042f2e 0%, #0f4c45 50%, #0d9488 100%);
    margin-bottom: 1.5rem; box-shadow: 0 8px 32px rgba(13,148,136,.28);
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
    padding-left: .8rem; border-left: 4px solid #0d9488;
    margin: 1.8rem 0 .85rem;
}
label[data-testid="stWidgetLabel"] p { font-size: .80rem !important; font-weight: 600 !important; }
[data-testid="stAlert"] { border-radius: 10px !important; }

/* Material cards */
.obra-mat-card {
    display: flex; align-items: center; gap: 1.1rem;
    padding: .9rem 1.2rem; border-radius: 14px;
    border: 1px solid rgba(13,148,136,.20);
    background: linear-gradient(135deg, rgba(13,148,136,.07) 0%, rgba(5,150,105,.03) 100%);
    margin-bottom: .5rem; flex-wrap: wrap;
}
.obra-mat-icon {
    width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
    background: linear-gradient(135deg, #0f766e, #0d9488);
    display: flex; align-items: center; justify-content: center;
    font-size: .95rem; font-weight: 900; color: #fff;
    box-shadow: 0 2px 8px rgba(13,148,136,.30);
}
.obra-mat-info { flex: 1; min-width: 140px; }
.obra-mat-head {
    display: flex; align-items: baseline; gap: .45rem;
    margin-bottom: .35rem; padding-bottom: .3rem;
    border-bottom: 1px solid rgba(13,148,136,.18);
}
.obra-mat-hlbl {
    font-size: .58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .07em;
    color: rgba(148,163,184,.55);
}
.obra-mat-name { font-size: .92rem; font-weight: 800; color: #f1f5f9; }
.obra-mat-stock {
    text-align: right; min-width: 88px;
    display: flex; flex-direction: column; align-items: flex-end; gap: .04rem;
}
.obra-mat-stock-num {
    font-size: 1.7rem; font-weight: 900; line-height: 1;
    color: #2dd4bf;
}
.obra-mat-stock-lbl {
    font-size: .60rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .07em; color: rgba(148,163,184,.55);
}
.obra-mat-stock-unit {
    font-size: .68rem; color: rgba(148,163,184,.50);
    font-weight: 600; margin-top: .05rem;
}
.obra-mat-zero .obra-mat-stock-num { color: #f87171; }

.obra-mat-fields {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: .35rem .55rem;
}
.obra-mat-field {
    display: flex; flex-direction: column; gap: .1rem;
    padding: .25rem .5rem;
    border-radius: 8px;
    background: rgba(15,23,42,.32);
    border: 1px solid rgba(255,255,255,.04);
}
.obra-mat-flbl {
    font-size: .56rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .07em;
    color: rgba(148,163,184,.55);
}
.obra-mat-fval { font-size: .80rem; font-weight: 800; color: #e2e8f0; line-height: 1.2; }
.obra-mat-fval.price-s { color: #fbbf24; }
.obra-mat-fval.price-d { color: #60a5fa; }
.obra-mat-fval.value   { color: #c4b5fd; }
.obra-mat-fval.proj    { color: #6ee7b7; }
.obra-mat-fval.noproj  { color: rgba(148,163,184,.55); font-style: italic; font-weight: 600; }

.obra-mat-field.obra-proj-field {
    background: rgba(5,150,105,.10);
    border-color: rgba(5,150,105,.25);
}
.obra-mat-field.obra-noproj-field {
    background: rgba(239,68,68,.06);
    border-color: rgba(239,68,68,.18);
}

/* Retirar stock expander — red accent */
.ret-exp details[data-testid="stExpander"] {
    border-color: rgba(239,68,68,.25) !important;
}
.ret-exp details[data-testid="stExpander"] > summary { color: #f87171 !important; }

/* Receipt history cards */
.recv-hist-card {
    display: flex; gap: 1.2rem; padding: .85rem 1.2rem;
    border-radius: 14px; border: 1px solid rgba(13,148,136,.16);
    background: rgba(13,148,136,.04);
    margin-bottom: .5rem; flex-wrap: wrap; position: relative; overflow: hidden;
}
.recv-hist-card::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px; background: linear-gradient(180deg, #0d9488, #059669);
    border-radius: 3px 0 0 3px;
}
.recv-hist-guia {
    min-width: 120px; display: flex; flex-direction: column; gap: .14rem;
}
.recv-hist-lbl {
    font-size: .58rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .07em; color: rgba(148,163,184,.45);
}
.recv-hist-guia-num { font-size: .86rem; font-weight: 900; color: #2dd4bf; }
.recv-hist-date     { font-size: .68rem; color: rgba(148,163,184,.45); }
.recv-hist-pills    { flex: 1; min-width: 160px; display: flex; flex-wrap: wrap; align-content: center; gap: .2rem; }
.recv-hist-pill {
    display: inline-flex; align-items: center; gap: .35rem;
    background: rgba(13,148,136,.12); border: 1px solid rgba(13,148,136,.22);
    border-radius: 16px; padding: .18rem .6rem;
    font-size: .72rem; font-weight: 700; color: #5eead4;
}
.recv-hist-pill .pill-lbl {
    font-size: .58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .04em;
    color: rgba(148,163,184,.65);
}
.recv-hist-pill .pill-val { color: #5eead4; font-weight: 700; }
.recv-hist-pill .pill-sep { color: rgba(148,163,184,.30); margin: 0 .15rem; }

.recv-hist-meta-row {
    display: flex; gap: .3rem; flex-wrap: wrap; margin-top: .35rem;
    width: 100%;
}
.recv-hist-meta-chip, .recv-hist-proj-chip {
    display: inline-flex; align-items: baseline; gap: .35rem;
    padding: .14rem .55rem; border-radius: 8px;
    background: rgba(15,23,42,.40);
    border: 1px solid rgba(255,255,255,.05);
}
.recv-hist-proj-chip {
    background: rgba(5,150,105,.10);
    border-color: rgba(5,150,105,.25);
}
.recv-hist-proj-chip.empty {
    background: rgba(239,68,68,.06);
    border-color: rgba(239,68,68,.18);
}
.recv-hist-mini-lbl {
    font-size: .56rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .05em;
    color: rgba(148,163,184,.55);
}
.recv-hist-mini-val { font-size: .70rem; font-weight: 700; color: #e2e8f0; }
.recv-hist-proj-chip .recv-hist-mini-val { color: #6ee7b7; }
.recv-hist-proj-chip.empty .recv-hist-mini-val { color: #fca5a5; font-style: italic; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_menu()

if st.session_state.get("obra_rem_ok"):
    st.success(st.session_state.pop("obra_rem_ok"))

db       = SessionLocal()
owner_id = get_current_user_id()

all_warehouses   = db.query(Warehouse).filter(Warehouse.owner_id == owner_id).all()
obra_warehouses  = [w for w in all_warehouses if w.type == "obra"]

# ── Hero ──────────────────────────────────────────────────────────────────────
total_obra_stock = 0
if obra_warehouses:
    obra_ids = [w.id for w in obra_warehouses]
    all_obra_inv = db.query(Inventory).filter(Inventory.warehouse_id.in_(obra_ids)).all()
    total_obra_stock = sum(inv.stock for inv in all_obra_inv)

st.markdown(f"""
<div class="op-hero">
  <div class="op-hero-left">
    <div class="op-hero-icon">&#127970;</div>
    <div>
      <h1>Inventario de Obra</h1>
      <p>Stock en almacenes de obra — actualizado tras cada recepción</p>
    </div>
  </div>
  <div class="op-badge">Stock total obra: {total_obra_stock} unidades</div>
</div>
""", unsafe_allow_html=True)

if not obra_warehouses:
    st.info("No tienes almacenes de obra registrados. Crea uno en la sección Almacenes.")
    db.close()
    st.stop()

# ── Filtro de almacén ─────────────────────────────────────────────────────────
obra_opts   = {w.name: w.id for w in obra_warehouses}
sel_name    = st.selectbox(
    "Almacén de obra",
    list(obra_opts.keys()),
    key="inv_obra_sel",
    label_visibility="visible",
)
sel_id = obra_opts[sel_name]

# ── KPI del almacén seleccionado ──────────────────────────────────────────────
sel_inv = db.query(Inventory).filter(Inventory.warehouse_id == sel_id).all()
sel_total = sum(i.stock for i in sel_inv)
sel_mats  = len(sel_inv)

# Total S/ recibido en esta obra (acumulado de todas las recepciones, nunca resta)
_obra_receipts = (
    db.query(Receipt)
    .join(Dispatch, Receipt.dispatch_id == Dispatch.id)
    .join(Requirement, Dispatch.requirement_id == Requirement.id)
    .filter(Requirement.warehouse_id_obra == sel_id)
    .all()
)
total_received_soles = 0.0
for _rec in _obra_receipts:
    if _rec.dispatch and _rec.dispatch.items:
        for _dit in _rec.dispatch.items:
            _price = float(_dit.material.unit_price or 0) if _dit.material else 0.0
            total_received_soles += _dit.dispatched_qty * _price

# Valor actual = stock vigente × precio unitario
current_value_soles = sum(
    (i.stock or 0) * float(i.material.unit_price or 0)
    for i in sel_inv if i.material
)

k1, k2, k3, k4 = st.columns(4, gap="medium")
k1.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(13,148,136,.15),rgba(5,150,105,.06));
            border:1px solid rgba(13,148,136,.28);border-radius:16px;padding:1rem 1.3rem">
  <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
              color:rgba(148,163,184,.55);margin-bottom:.35rem">Unidades en almacén</div>
  <div style="font-size:2.2rem;font-weight:900;color:#2dd4bf;line-height:1">{sel_total}</div>
  <div style="font-size:.68rem;color:rgba(148,163,184,.40);margin-top:.2rem">stock actual en {sel_name}</div>
</div>""", unsafe_allow_html=True)

k2.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(13,148,136,.10),rgba(5,150,105,.04));
            border:1px solid rgba(13,148,136,.20);border-radius:16px;padding:1rem 1.3rem">
  <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
              color:rgba(148,163,184,.55);margin-bottom:.35rem">Materiales distintos</div>
  <div style="font-size:2.2rem;font-weight:900;color:#5eead4;line-height:1">{sel_mats}</div>
  <div style="font-size:.68rem;color:rgba(148,163,184,.40);margin-top:.2rem">tipos de material con stock</div>
</div>""", unsafe_allow_html=True)

_recv_color = "#fbbf24" if total_received_soles > 0 else "rgba(148,163,184,.40)"
k3.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(251,191,36,.10),rgba(217,119,6,.04));
            border:1px solid rgba(251,191,36,.22);border-radius:16px;padding:1rem 1.3rem">
  <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
              color:rgba(148,163,184,.55);margin-bottom:.35rem">Total ingresado S/</div>
  <div style="font-size:{'1.55rem' if total_received_soles >= 10000 else '2.2rem'};font-weight:900;color:{_recv_color};line-height:1">
    S/ {total_received_soles:,.2f}
  </div>
  <div style="font-size:.68rem;color:rgba(148,163,184,.40);margin-top:.2rem">
    acumulado en {len(_obra_receipts)} recepcion{'es' if len(_obra_receipts) != 1 else ''}
  </div>
</div>""", unsafe_allow_html=True)

_cur_color = "#c4b5fd" if current_value_soles > 0 else "rgba(148,163,184,.40)"
k4.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(168,85,247,.10),rgba(124,58,237,.04));
            border:1px solid rgba(168,85,247,.22);border-radius:16px;padding:1rem 1.3rem">
  <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;
              color:rgba(148,163,184,.55);margin-bottom:.35rem">Valor actual S/</div>
  <div style="font-size:{'1.55rem' if current_value_soles >= 10000 else '2.2rem'};font-weight:900;color:{_cur_color};line-height:1">
    S/ {current_value_soles:,.2f}
  </div>
  <div style="font-size:.68rem;color:rgba(148,163,184,.40);margin-top:.2rem">
    stock × precio unitario
  </div>
</div>""", unsafe_allow_html=True)

# ── Stock actual ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Stock Actual</div>', unsafe_allow_html=True)

if not sel_inv:
    st.info("Este almacén de obra no tiene stock registrado. El stock se actualiza automáticamente al confirmar recepciones.")
else:
    for inv in sorted(sel_inv, key=lambda x: (x.material.name if x.material else ""), ):
        mat_name    = inv.material.name if inv.material else f"Material {inv.material_id}"
        mat_unit    = (inv.material.unit or "").strip() if inv.material else ""
        mat_price   = float(inv.material.unit_price or 0.0) if inv.material else 0.0
        mat_price_d = float(inv.material.unit_price_dolares or 0.0) if inv.material else 0.0
        proj_name   = inv.budget_name if getattr(inv, "budget_name", None) else None
        initial     = mat_name[0].upper()
        zero_cls    = "obra-mat-zero" if inv.stock == 0 else ""
        unit_lbl    = mat_unit if mat_unit else "uds"
        stock_value = inv.stock * mat_price

        # Construye fields con labels (similar al inventario principal)
        fields = []
        fields.append(
            '<div class="obra-mat-field"><span class="obra-mat-flbl">Unidad</span>'
            f'<span class="obra-mat-fval">{unit_lbl}</span></div>'
        )
        if mat_price > 0:
            fields.append(
                '<div class="obra-mat-field"><span class="obra-mat-flbl">Precio S/.</span>'
                f'<span class="obra-mat-fval price-s">S/ {mat_price:,.2f}</span></div>'
            )
        if mat_price_d > 0:
            fields.append(
                '<div class="obra-mat-field"><span class="obra-mat-flbl">Precio $</span>'
                f'<span class="obra-mat-fval price-d">$ {mat_price_d:,.2f}</span></div>'
            )
        if stock_value > 0:
            fields.append(
                '<div class="obra-mat-field"><span class="obra-mat-flbl">Valor actual</span>'
                f'<span class="obra-mat-fval value">S/ {stock_value:,.2f}</span></div>'
            )
        if proj_name:
            fields.append(
                '<div class="obra-mat-field obra-proj-field"><span class="obra-mat-flbl">Proyecto</span>'
                f'<span class="obra-mat-fval proj">&#128196; {proj_name}</span></div>'
            )
        else:
            fields.append(
                '<div class="obra-mat-field obra-noproj-field"><span class="obra-mat-flbl">Proyecto</span>'
                '<span class="obra-mat-fval noproj">— sin proyecto —</span></div>'
            )

        fields_html = "".join(fields)

        st.markdown(
            f'<div class="obra-mat-card {zero_cls}">'
              f'<div class="obra-mat-icon">{initial}</div>'
              '<div class="obra-mat-info">'
                '<div class="obra-mat-head">'
                  '<span class="obra-mat-hlbl">Nombre</span>'
                  f'<span class="obra-mat-name">{mat_name}</span>'
                '</div>'
                f'<div class="obra-mat-fields">{fields_html}</div>'
              '</div>'
              '<div class="obra-mat-stock">'
                '<div class="obra-mat-stock-lbl">Stock</div>'
                f'<div class="obra-mat-stock-num">{inv.stock}</div>'
                f'<div class="obra-mat-stock-unit">{unit_lbl}</div>'
              '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

# ── Retirar stock del almacén de obra ─────────────────────────────────────────
st.markdown('<div class="sec-title">Retirar Stock</div>', unsafe_allow_html=True)

_obra_rem_n = st.session_state.get("obra_rem_form_n", 0)
st.markdown('<div class="ret-exp">', unsafe_allow_html=True)
with st.expander("Retirar stock del almacén de obra", expanded=False):
    if not sel_inv:
        st.info("Este almacén no tiene stock registrado.")
    else:
        mat_rem_opts = {
            (inv.material.name if inv.material else f"Material {inv.material_id}"): inv
            for inv in sorted(sel_inv, key=lambda x: x.material.name if x.material else "")
        }
        col_mat_r, col_qty_r = st.columns(2, gap="medium")
        sel_mat_rem_name = col_mat_r.selectbox(
            "Material", list(mat_rem_opts.keys()),
            key=f"obra_rem_mat_{_obra_rem_n}",
        )
        sel_mat_rem_inv = mat_rem_opts[sel_mat_rem_name]
        max_stock = sel_mat_rem_inv.stock
        mat_unit  = sel_mat_rem_inv.material.unit if sel_mat_rem_inv.material else ""

        if max_stock > 0:
            rem_qty_obra = col_qty_r.number_input(
                "Cantidad a retirar", min_value=1, max_value=max_stock,
                key=f"obra_rem_qty_{_obra_rem_n}",
            )
        else:
            with col_qty_r:
                st.markdown(
                    "<div style='padding-top:1.6rem;font-size:.82rem;color:#f87171;font-weight:700'>Sin stock</div>",
                    unsafe_allow_html=True,
                )
            rem_qty_obra = 0

        st.caption(f"Stock disponible: **{max_stock}** {mat_unit}")

        if st.button(
            "Retirar Stock", type="primary",
            key=f"obra_btn_rem_{_obra_rem_n}",
            disabled=(max_stock == 0),
        ):
            ok = remove_stock(
                db, sel_id, sel_mat_rem_inv.material_id, rem_qty_obra, user_id=owner_id
            )
            if ok:
                st.session_state["obra_rem_ok"] = (
                    f"Se retiraron **{rem_qty_obra}** {mat_unit} de "
                    f"**{sel_mat_rem_name}** del almacén **{sel_name}**."
                )
                st.session_state["obra_rem_form_n"] = _obra_rem_n + 1
                st.rerun()
            else:
                st.error("Stock insuficiente para realizar el retiro.")
st.markdown("</div>", unsafe_allow_html=True)

# ── Historial de recepciones del almacén seleccionado ─────────────────────────
st.markdown('<div class="sec-title">Recepciones Recibidas</div>', unsafe_allow_html=True)

recent_receipts = (
    db.query(Receipt)
    .join(Dispatch, Receipt.dispatch_id == Dispatch.id)
    .join(Requirement, Dispatch.requirement_id == Requirement.id)
    .filter(Requirement.warehouse_id_obra == sel_id)
    .order_by(Receipt.receipt_date.desc())
    .all()
)

if not recent_receipts:
    st.info("Aún no hay recepciones confirmadas para este almacén de obra.")
else:
    # ── Filtros ───────────────────────────────────────────────────────────────
    _proj_opts = ["Todos"] + sorted({
        (rec.dispatch.requirement.budget_name if rec.dispatch and rec.dispatch.requirement and rec.dispatch.requirement.budget_name else "— sin proyecto —")
        for rec in recent_receipts
    })
    _fc1, _fc2, _fc3, _fc4 = st.columns([2.2, 1.8, 1.8, 2.2], gap="small")
    _f_proj = _fc1.selectbox("Proyecto", _proj_opts, key=f"recv_obra_f_proj_{sel_id}")
    _f_from = _fc2.date_input("Desde", value=None, key=f"recv_obra_f_from_{sel_id}")
    _f_to   = _fc3.date_input("Hasta", value=None, key=f"recv_obra_f_to_{sel_id}")
    _f_guia = _fc4.text_input(
        "Guía", value="", key=f"recv_obra_f_guia_{sel_id}",
        placeholder="Buscar por nº de guía...",
    )

    _filtered = recent_receipts
    if _f_proj != "Todos":
        if _f_proj == "— sin proyecto —":
            _filtered = [r for r in _filtered if not (r.dispatch and r.dispatch.requirement and r.dispatch.requirement.budget_name)]
        else:
            _filtered = [r for r in _filtered if r.dispatch and r.dispatch.requirement and r.dispatch.requirement.budget_name == _f_proj]
    if _f_from:
        _filtered = [r for r in _filtered if r.receipt_date and r.receipt_date.date() >= _f_from]
    if _f_to:
        _filtered = [r for r in _filtered if r.receipt_date and r.receipt_date.date() <= _f_to]
    if _f_guia.strip():
        _q = _f_guia.strip().lower()
        _filtered = [r for r in _filtered if r.dispatch and (r.dispatch.guia_number or "").lower().find(_q) >= 0]

    st.caption(
        f"{len(_filtered)} recepci{'ones' if len(_filtered) != 1 else 'ón'} encontrada{'s' if len(_filtered) != 1 else ''} "
        f"(de {len(recent_receipts)} total{'es' if len(recent_receipts) != 1 else ''})."
    )

    if not _filtered:
        st.info("No se encontraron recepciones con los filtros aplicados.")

    for rec in _filtered:
        disp      = rec.dispatch
        guia      = disp.guia_number if disp else "—"
        recv_date = rec.receipt_date.strftime("%d/%m/%Y %H:%M") if rec.receipt_date else "—"
        req_obj   = disp.requirement if disp else None
        proj_n    = getattr(req_obj, "budget_name", None) if req_obj else None

        pills_html = "".join(
            f"<span class='recv-hist-pill'>"
            f"<span class='pill-lbl'>Nombre:</span>"
            f"<span class='pill-val'>{it.material.name if it.material else f'Mat.{it.material_id}'}</span>"
            f"<span class='pill-sep'>·</span>"
            f"<span class='pill-lbl'>Cant.:</span>"
            f"<span class='pill-val'>{it.dispatched_qty}"
            f"{(' ' + it.material.unit) if it.material and it.material.unit else ''}</span>"
            f"</span>"
            for it in (disp.items if disp else [])
        )

        proj_chip_o = (
            f"<span class='recv-hist-proj-chip'><span class='recv-hist-mini-lbl'>Proyecto:</span>"
            f"<span class='recv-hist-mini-val'>{proj_n}</span></span>"
            if proj_n else
            "<span class='recv-hist-proj-chip empty'>"
            "<span class='recv-hist-mini-lbl'>Proyecto:</span>"
            "<span class='recv-hist-mini-val'>— sin proyecto —</span></span>"
        )

        st.markdown(f"""
<div class="recv-hist-card">
  <div class="recv-hist-guia">
    <div class="recv-hist-lbl">Guía</div>
    <div class="recv-hist-guia-num">{guia}</div>
    <div class="recv-hist-lbl" style="margin-top:.32rem">Recibido</div>
    <div class="recv-hist-date">{recv_date}</div>
  </div>
  <div class="recv-hist-pills">
    {pills_html if pills_html else '<span style="font-size:.72rem;color:rgba(148,163,184,.35)">Sin ítems</span>'}
    <div class="recv-hist-meta-row">
      {proj_chip_o}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

db.close()
