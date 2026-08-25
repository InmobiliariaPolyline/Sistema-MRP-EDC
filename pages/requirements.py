# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
from database import SessionLocal
from services.requirement_service import create_requirement, get_requirements, cancel_requirement
from services.budget_service import get_budgets
from services.warehouse_service import get_warehouses
from models.warehouse import Warehouse
from models.material import Material
from models.inventory import Inventory
from utils.auth import require_cliente, get_current_user_id
from utils.navbar import render_navbar, render_sidebar_menu
from datetime import datetime, timedelta

st.set_page_config(page_title="Requerimientos — Sistema MRP", layout="wide", initial_sidebar_state="expanded")

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
    transition: border-color .2s !important;
}
[data-testid="stExpander"]:hover { border-color: rgba(37,99,235,.32) !important; }
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
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] button:hover {
    opacity: .9 !important; transform: translateY(-1px) !important;
}
[data-testid="stAlert"] { border-radius: 10px !important; }

/* Status badges */
.badge-pending   { display:inline-block; padding:.18rem .65rem; border-radius:20px; font-size:.70rem; font-weight:700; background:rgba(234,179,8,.18);  color:#fbbf24; }
.badge-fulfilled { display:inline-block; padding:.18rem .65rem; border-radius:20px; font-size:.70rem; font-weight:700; background:rgba(16,185,129,.18); color:#34d399; }
.badge-partial   { display:inline-block; padding:.18rem .65rem; border-radius:20px; font-size:.70rem; font-weight:700; background:rgba(249,115,22,.18);  color:#fb923c; }
.badge-cancelled { display:inline-block; padding:.18rem .65rem; border-radius:20px; font-size:.70rem; font-weight:700; background:rgba(239,68,68,.18);   color:#f87171; }

/* Req card */
.req-card {
    padding: .75rem 1.1rem; border-radius: 12px;
    border: 1px solid rgba(37,99,235,.15); background: rgba(37,99,235,.04);
    margin-bottom: .5rem;
}
.req-id   { font-size: .78rem; font-weight: 800; color: #93c5fd; }
.req-date { font-size: .72rem; opacity: .55; }

/* Pagination */
.pg-info {
    text-align: center; font-size: .80rem; font-weight: 600;
    padding: .5rem 0; opacity: .70;
}

/* ── Cabecera del requerimiento dentro del expander ── */
.req-hdr {
    display: flex; gap: .5rem; flex-wrap: wrap;
    margin: .1rem 0 .85rem;
}
.req-hdr-chip {
    display: inline-flex; align-items: baseline; gap: .45rem;
    padding: .32rem .72rem; border-radius: 10px;
    background: rgba(37,99,235,.07);
    border: 1px solid rgba(37,99,235,.18);
}
.req-hdr-chip.req-hdr-proj {
    background: rgba(5,150,105,.10);
    border-color: rgba(5,150,105,.28);
}
.req-hdr-chip.req-hdr-proj-empty {
    background: rgba(239,68,68,.08);
    border-color: rgba(239,68,68,.22);
}
.req-hdr-lbl {
    font-size: .60rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .07em;
    color: rgba(148,163,184,.55);
}
.req-hdr-val { font-size: .82rem; font-weight: 800; color: #e2e8f0; }
.req-hdr-chip.req-hdr-proj .req-hdr-val { color: #6ee7b7; }
.req-hdr-chip.req-hdr-proj-empty .req-hdr-val { color: #fca5a5; font-style: italic; }

/* ── Tarjeta de ítem dentro del requerimiento ── */
.req-item-card {
    padding: .8rem 1.1rem; border-radius: 13px;
    border: 1px solid rgba(37,99,235,.18);
    background: linear-gradient(135deg, rgba(37,99,235,.06), rgba(79,70,229,.03));
    margin-bottom: .45rem;
}
.req-item-head {
    display: flex; align-items: center; gap: .65rem;
    margin-bottom: .55rem; padding-bottom: .4rem;
    border-bottom: 1px solid rgba(37,99,235,.14); flex-wrap: wrap;
}
.req-item-name { font-weight: 800; color: #f1f5f9; font-size: .92rem; flex: 1; min-width: 140px; }
.req-item-badge { flex-shrink: 0; }
.req-item-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
    gap: .45rem .8rem;
}
.req-item-field {
    display: flex; flex-direction: column; gap: .12rem;
    padding: .3rem .55rem;
    border-radius: 8px;
    background: rgba(15,23,42,.30);
    border: 1px solid rgba(255,255,255,.04);
}
.req-item-lbl {
    font-size: .58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .07em;
    color: rgba(148,163,184,.55);
}
.req-item-val { font-size: .85rem; font-weight: 800; color: #e2e8f0; line-height: 1.2; }
.req-item-val em { font-style: normal; opacity: .55; font-weight: 600; font-size: .75rem; }
.req-item-val.empty { color: rgba(148,163,184,.40); font-style: italic; font-weight: 500; }
.req-item-val.qty-blue  { color: #60a5fa; }
.req-item-val.qty-green { color: #34d399; }
.req-item-val.price-s   { color: #34d399; }
.req-item-val.price-d   { color: #60a5fa; }

.req-total-bar {
    display: flex; align-items: center; justify-content: flex-end;
    gap: .85rem; margin-top: .4rem; padding: .55rem 1.1rem;
    border-radius: 10px;
    border: 1px solid rgba(251,191,36,.22);
    background: rgba(251,191,36,.05); flex-wrap: wrap;
}
.req-total-lbl { font-size: .72rem; color: rgba(148,163,184,.65); font-weight: 600; margin-right: auto; }
.req-total-s   { font-size: .98rem; font-weight: 900; color: #fbbf24; }
.req-total-d   { font-size: .98rem; font-weight: 900; color: #60a5fa; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_menu()


st.title("📋 Requerimientos")

db       = SessionLocal()
owner_id = get_current_user_id()

all_user_warehouses = get_warehouses(db, owner_id=owner_id)
warehouses          = [w for w in all_user_warehouses if w.type == "obra"]
principal_warehouse = next((w for w in all_user_warehouses if w.type == "principal"), None)
wh_id_to_name       = {w.id: w.name for w in all_user_warehouses}

# Solo materiales que tienen inventario en el almacén principal del usuario
if principal_warehouse:
    _principal_inv     = db.query(Inventory).filter(Inventory.warehouse_id == principal_warehouse.id).all()
    _principal_mat_ids = {inv.material_id for inv in _principal_inv}
    materials          = db.query(Material).filter(Material.id.in_(_principal_mat_ids)).all()
else:
    materials = db.query(Material).all()

# IDs de todos los almacenes del usuario (para filtrar requerimientos)
owner_wh_ids = [w.id for w in all_user_warehouses]

# ── Hero ──────────────────────────────────────────────────────────────────────
_, total_reqs = get_requirements(db, skip=0, limit=1, warehouse_ids=owner_wh_ids)

st.markdown(f"""
<div class="op-hero">
  <div class="op-hero-left">
    <div class="op-hero-icon">&#128203;</div>
    <div>
      <h1>Requerimientos</h1>
      <p>Solicitudes de materiales para almacenes de obra</p>
    </div>
  </div>
  <div class="op-badge">{total_reqs} requerimientos en total</div>
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
    st.markdown("#### Requerimientos — Guía de uso")
    st.markdown("""
**Crear un requerimiento**
1. Selecciona el **almacén de obra** que recibirá los materiales.
2. Indica cuántos materiales necesitas y completa cada línea con material y cantidad.
3. Presiona **Crear Requerimiento**; el sistema reservará automáticamente el stock disponible.

**Estados del requerimiento**
- **Pendiente:** sin stock reservado aún (stock insuficiente o nulo).
- **Parcial:** stock reservado solo en parte; queda saldo pendiente.
- **Cumplido:** todo el stock está reservado y listo para despacho.

**Filtros y paginación**
- Usa los filtros por ID, estado y rango de fechas para localizar requerimientos.
- Navega con los botones **Anterior / Siguiente** para ver más resultados.
- Haz clic en **Ver detalle** de cualquier requerimiento para revisar sus ítems.

> Necesitas al menos un almacén de **obra** y un **material** creados antes de generar requerimientos.
""")

# ── Crear ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Nuevo Requerimiento</div>', unsafe_allow_html=True)


if not warehouses:
    if not all_user_warehouses:
        st.error("No tienes almacenes registrados. Ve a **Almacenes** y crea uno de tipo **principal** y otro de tipo **obra**.")
    else:
        tipos = ", ".join(set(w.type for w in all_user_warehouses))
        st.warning(
            f"Tienes {len(all_user_warehouses)} almacén(es) registrado(s) (tipo: {tipos}), "
            "pero ninguno es de tipo **obra**. "
            "Ve a **Almacenes**, crea o edita uno y selecciona tipo **obra**."
        )
elif not principal_warehouse:
    st.error("No tienes un almacén **principal** registrado. Ve a **Almacenes** y crea uno de tipo principal.")
elif not materials:
    st.warning(
        f"El almacén principal **{principal_warehouse.name}** no tiene materiales en inventario. "
        "Ve a **Inventario** y agrega stock primero."
    )
elif not [b for b in get_budgets(db) if b.is_active]:
    st.error(
        "No hay **proyectos activos** disponibles. "
        "Pide al administrador que cree y active un proyecto en la sección **Presupuestos** "
        "antes de generar requerimientos."
    )
else:
    if st.session_state.get("req_created_msg"):
        st.success(st.session_state.pop("req_created_msg"))

    with st.expander("Crear requerimiento", expanded=False):
        wh_dict  = {w.name: w.id for w in warehouses}
        mat_dict = {m.name: m.id for m in materials}

        selected_wh  = st.selectbox("Almacén de obra", list(wh_dict.keys()), key="req_wh")

        # ── Selector de proyecto (OBLIGATORIO — solo proyectos activos) ─────────
        _active_budgets = [b for b in get_budgets(db) if b.is_active]
        _bud_opts       = {b.name: b.id for b in _active_budgets}
        _proj_label = st.selectbox(
            "Proyecto *", list(_bud_opts.keys()), key="req_proj",
            help="El proyecto es obligatorio — el requerimiento se vinculará a él.",
        )
        _proj_id    = _bud_opts[_proj_label]

        num_items    = st.number_input("Cantidad de materiales", min_value=1, max_value=20, step=1, key="req_num")

        items = []
        for i in range(int(num_items)):
            col_m, col_q = st.columns([3, 1], gap="small")
            mat    = col_m.selectbox(f"Material {i+1}", list(mat_dict.keys()), key=f"req_mat_{i}")
            qty    = col_q.number_input("Cantidad", min_value=1, key=f"req_qty_{i}", label_visibility="visible")
            mat_id = mat_dict[mat]
            items.append({"material_id": mat_id, "qty": qty})

            # ── Indicador de stock disponible ──────────────────────────────────
            if principal_warehouse:
                _all_inv   = db.query(Inventory).filter(
                    Inventory.warehouse_id == principal_warehouse.id,
                    Inventory.material_id  == mat_id,
                ).all()
                _all_avail = sum(max(0, inv.stock - inv.reserved) for inv in _all_inv)

                if _proj_id:
                    _proj_inv   = next((inv for inv in _all_inv if inv.budget_id == _proj_id), None)
                    _proj_avail = max(0, (_proj_inv.stock - _proj_inv.reserved)) if _proj_inv else 0
                    if _proj_avail >= qty:
                        _sc = "#34d399"
                        _st = f"✓ {_proj_avail} disp. en proyecto · {_all_avail} total"
                    elif _all_avail >= qty:
                        _sc = "#fbbf24"
                        _st = f"⚠ {_proj_avail} en proyecto · {_all_avail} disp. total"
                    else:
                        _sc = "#f87171"
                        _st = f"✗ Stock insuf. — {_all_avail} disp. total"
                else:
                    _sc = "#34d399" if _all_avail >= qty else ("#fbbf24" if _all_avail > 0 else "#f87171")
                    _st = f"{_all_avail} disponible en almacén principal"

                col_m.markdown(
                    f"<div style='font-size:.70rem;font-weight:700;color:{_sc};"
                    f"margin-top:.05rem;padding-bottom:.1rem'>{_st}</div>",
                    unsafe_allow_html=True,
                )

        if st.button("Crear Requerimiento", type="primary", key="btn_create_req"):
            success, msg = create_requirement(
                db, wh_dict[selected_wh], items, budget_id=_proj_id, owner_id=owner_id
            )
            if success:
                for k in (["req_wh", "req_num", "req_proj"]
                          + [f"req_mat_{i}" for i in range(int(num_items))]
                          + [f"req_qty_{i}" for i in range(int(num_items))]):
                    st.session_state.pop(k, None)
                st.session_state["req_created_msg"] = msg
                st.rerun()
            else:
                st.error(msg)

# ── Filtros ───────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Lista de Requerimientos</div>', unsafe_allow_html=True)

with st.expander("Filtros", expanded=False):
    fc1, fc2, fc3, fc4 = st.columns(4, gap="small")
    filter_id     = fc1.number_input("ID", value=0, min_value=0, key="flt_id")
    filter_status = fc2.selectbox("Estado", ["", "pending", "fulfilled", "partial", "cancelled"], key="flt_st")
    filter_start  = fc3.date_input("Desde", value=datetime.now() - timedelta(days=30), key="flt_from")
    filter_end    = fc4.date_input("Hasta", value=datetime.now(), key="flt_to")

    bc1, bc2 = st.columns(2, gap="small")
    if bc1.button("Buscar", type="primary", use_container_width=True, key="btn_search_req"):
        st.session_state["req_page"] = 0
    if bc2.button("Limpiar", use_container_width=True, key="btn_clear_req"):
        for _fk in ["flt_id", "flt_st", "flt_from", "flt_to"]:
            st.session_state.pop(_fk, None)
        st.session_state["req_page"] = 0
        st.rerun()

# ── Paginación ────────────────────────────────────────────────────────────────
ITEMS_PER_PAGE = 10
if "req_page" not in st.session_state:
    st.session_state["req_page"] = 0

start_dt = datetime.combine(filter_start, datetime.min.time())
# +1 día extra cubre diferencias de zona horaria entre datetime.now() (local)
# y posibles registros históricos en UTC que caen un día adelante
end_dt   = datetime.combine(filter_end + timedelta(days=1), datetime.min.time())

requirements, total_count = get_requirements(
    db,
    skip           = st.session_state["req_page"] * ITEMS_PER_PAGE,
    limit          = ITEMS_PER_PAGE,
    requirement_id = int(filter_id) if filter_id > 0 else None,
    status         = filter_status if filter_status else None,
    start_date     = start_dt,
    end_date       = end_dt,
    warehouse_ids  = owner_wh_ids,
)

total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

# ── Resultados ────────────────────────────────────────────────────────────────
_STATUS_EMOJI = {
    "pending":   "⏳",
    "fulfilled": "✅",
    "partial":   "🔶",
    "cancelled": "❌",
}
_STATUS_TEXT = {
    "pending":   "Pendiente",
    "fulfilled": "Cumplido",
    "partial":   "Parcial",
    "cancelled": "Cancelado",
}
_ITEM_BADGE = {
    "reserved":  ('<span style="display:inline-block;padding:.15rem .55rem;border-radius:12px;'
                  'font-size:.70rem;font-weight:700;background:rgba(37,99,235,.18);'
                  'color:#93c5fd">Reservado</span>'),
    "pending":   ('<span style="display:inline-block;padding:.15rem .55rem;border-radius:12px;'
                  'font-size:.70rem;font-weight:700;background:rgba(234,179,8,.18);'
                  'color:#fbbf24">Pendiente</span>'),
    "partial":   ('<span style="display:inline-block;padding:.15rem .55rem;border-radius:12px;'
                  'font-size:.70rem;font-weight:700;background:rgba(249,115,22,.18);'
                  'color:#fb923c">Parcial</span>'),
    "fulfilled": ('<span style="display:inline-block;padding:.15rem .55rem;border-radius:12px;'
                  'font-size:.70rem;font-weight:700;background:rgba(16,185,129,.18);'
                  'color:#34d399">Cumplido</span>'),
}
_ITEM_CANCELLED = ('<span style="display:inline-block;padding:.15rem .55rem;border-radius:12px;'
                   'font-size:.70rem;font-weight:700;background:rgba(239,68,68,.18);'
                   'color:#f87171">Cancelado</span>')

if not requirements:
    st.info("No se encontraron requerimientos con los filtros aplicados.")
else:
    for r in requirements:
        wh_name    = wh_id_to_name.get(r.warehouse_id_obra, f"Almacén #{r.warehouse_id_obra}")
        n_items    = len(r.items) if r.items else 0
        fecha      = r.created_at.strftime("%d/%m/%Y %H:%M")
        can_cancel = r.status in ("pending", "partial")  # "fulfilled" = ya despachado, no se puede cancelar
        s_emoji    = _STATUS_EMOJI.get(r.status, "")
        s_text     = _STATUS_TEXT.get(r.status, r.status)
        proj_name  = getattr(r, "budget_name", None)

        req_cost = sum(
            it.requested_qty * float(it.material.unit_price or 0)
            for it in (r.items or [])
            if it.material
        )
        cost_str = f"💰 S/ {req_cost:,.2f}" if req_cost > 0 else ""

        exp_label = (
            f"#{r.id}  ·  {s_emoji} {s_text}"
            f"  ·  📅 {fecha}"
            f"  ·  🏢 {wh_name}"
            + (f"  ·  📂 {proj_name}" if proj_name else "")
            + f"  ·  {n_items} ítem{'s' if n_items != 1 else ''}"
            + (f"  ·  {cost_str}" if cost_str else "")
        )

        with st.expander(exp_label):
            # ── Cancelar ──────────────────────────────────────────────────
            if can_cancel:
                if st.button(
                    "🗑 Cancelar requerimiento",
                    key=f"cancel_btn_{r.id}",
                    type="secondary",
                ):
                    st.session_state["confirm_cancel_req"] = r.id

            if st.session_state.get("confirm_cancel_req") == r.id:
                c_msg, c_yes, c_no = st.columns([5, 1, 1], gap="small")
                c_msg.warning(
                    f"¿Cancelar el **Requerimiento #{r.id}**? "
                    "Se liberará todo el stock reservado. Esta acción no se puede deshacer."
                )
                if c_yes.button("Sí, cancelar", key=f"yes_cancel_req_{r.id}",
                                type="primary", use_container_width=True):
                    cancel_requirement(db, r.id, owner_id=owner_id)
                    del st.session_state["confirm_cancel_req"]
                    st.rerun()
                if c_no.button("No, mantener", key=f"no_cancel_req_{r.id}",
                               use_container_width=True):
                    del st.session_state["confirm_cancel_req"]
                    st.rerun()
                st.markdown("<hr style='margin:.5rem 0;border-color:rgba(37,99,235,.15)'>",
                            unsafe_allow_html=True)

            # ── Notas ─────────────────────────────────────────────────────
            if r.notes:
                st.markdown(
                    f"<div style='font-size:.82rem;color:rgba(148,163,184,.60);"
                    f"margin-bottom:.6rem'><strong>Notas:</strong> {r.notes}</div>",
                    unsafe_allow_html=True,
                )

            # ── Cabecera del requerimiento (proyecto + obra) ─────────────────
            _hdr_proj = (
                f'<span class="req-hdr-chip req-hdr-proj">'
                f'<span class="req-hdr-lbl">Proyecto</span>'
                f'<span class="req-hdr-val">{proj_name}</span></span>'
                if proj_name else
                '<span class="req-hdr-chip req-hdr-proj-empty">'
                '<span class="req-hdr-lbl">Proyecto</span>'
                '<span class="req-hdr-val">— sin proyecto —</span></span>'
            )
            st.markdown(
                '<div class="req-hdr">'
                f'<span class="req-hdr-chip"><span class="req-hdr-lbl">Almacén obra</span>'
                f'<span class="req-hdr-val">{wh_name}</span></span>'
                f'{_hdr_proj}'
                f'<span class="req-hdr-chip"><span class="req-hdr-lbl">Fecha</span>'
                f'<span class="req-hdr-val">{fecha}</span></span>'
                '</div>',
                unsafe_allow_html=True,
            )

            # ── Ítems ─────────────────────────────────────────────────────
            if not r.items:
                st.info("Sin ítems.")
            else:
                item_cost_total = 0.0
                item_cost_total_d = 0.0
                for it in r.items:
                    mat_name    = it.material.name if it.material else f"Material {it.material_id}"
                    mat_unit    = (it.material.unit or "").strip() if it.material else ""
                    unit_price  = float(it.material.unit_price or 0) if it.material else 0.0
                    unit_price_d = float(it.material.unit_price_dolares or 0) if it.material else 0.0
                    item_cost   = it.requested_qty * unit_price
                    item_cost_d = it.requested_qty * unit_price_d
                    item_cost_total   += item_cost
                    item_cost_total_d += item_cost_d
                    if r.status == "cancelled":
                        it_badge = _ITEM_CANCELLED
                    else:
                        it_badge = _ITEM_BADGE.get(it.status, it.status)
                    pct = int(it.fulfilled_qty / it.requested_qty * 100) if it.requested_qty else 0
                    qty_lbl  = mat_unit if mat_unit else "uds"
                    price_s_html = f"S/ {unit_price:,.2f}" if unit_price > 0 else "—"
                    price_d_html = f"$ {unit_price_d:,.2f}" if unit_price_d > 0 else "—"
                    price_s_cls  = "" if unit_price > 0 else "empty"
                    price_d_cls  = "" if unit_price_d > 0 else "empty"

                    item_html = (
                        '<div class="req-item-card">'
                          '<div class="req-item-head">'
                            f'<span class="req-item-name">{mat_name}</span>'
                            f'<span class="req-item-badge">{it_badge}</span>'
                          '</div>'
                          '<div class="req-item-grid">'
                            f'<div class="req-item-field"><span class="req-item-lbl">Cantidad solicitada</span>'
                            f'<span class="req-item-val qty-blue">{it.requested_qty}</span></div>'
                            f'<div class="req-item-field"><span class="req-item-lbl">Unidad</span>'
                            f'<span class="req-item-val">{qty_lbl}</span></div>'
                            f'<div class="req-item-field"><span class="req-item-lbl">Cumplido</span>'
                            f'<span class="req-item-val qty-green">{it.fulfilled_qty} <em>({pct}%)</em></span></div>'
                            f'<div class="req-item-field"><span class="req-item-lbl">Precio unit. S/.</span>'
                            f'<span class="req-item-val price-s {price_s_cls}">{price_s_html}</span></div>'
                            f'<div class="req-item-field"><span class="req-item-lbl">Precio unit. $</span>'
                            f'<span class="req-item-val price-d {price_d_cls}">{price_d_html}</span></div>'
                            f'<div class="req-item-field"><span class="req-item-lbl">Costo S/.</span>'
                            f'<span class="req-item-val price-s {price_s_cls}">{("S/ " + f"{item_cost:,.2f}") if unit_price > 0 else "—"}</span></div>'
                            f'<div class="req-item-field"><span class="req-item-lbl">Costo $</span>'
                            f'<span class="req-item-val price-d {price_d_cls}">{("$ " + f"{item_cost_d:,.2f}") if unit_price_d > 0 else "—"}</span></div>'
                          '</div>'
                        '</div>'
                    )
                    st.markdown(item_html, unsafe_allow_html=True)

                if item_cost_total > 0 or item_cost_total_d > 0:
                    _t_s = f'<span class="req-total-s">S/ {item_cost_total:,.2f}</span>' if item_cost_total > 0 else ""
                    _t_d = f'<span class="req-total-d">$ {item_cost_total_d:,.2f}</span>' if item_cost_total_d > 0 else ""
                    st.markdown(
                        '<div class="req-total-bar">'
                          '<span class="req-total-lbl">Costo estimado total del requerimiento</span>'
                          f'{_t_s}{_t_d}'
                        '</div>',
                        unsafe_allow_html=True,
                    )

# ── Navegación de páginas ─────────────────────────────────────────────────────
pg_prev, pg_info, pg_next = st.columns([1, 3, 1])

with pg_prev:
    if st.session_state["req_page"] > 0:
        if st.button("← Anterior", use_container_width=True, key="pg_prev_btn"):
            st.session_state["req_page"] -= 1
            st.rerun()

with pg_info:
    st.markdown(
        f'<div class="pg-info">Página {st.session_state["req_page"] + 1} de {total_pages} &nbsp;·&nbsp; {total_count} resultados</div>',
        unsafe_allow_html=True,
    )

with pg_next:
    if (st.session_state["req_page"] + 1) * ITEMS_PER_PAGE < total_count:
        if st.button("Siguiente →", use_container_width=True, key="pg_next_btn"):
            st.session_state["req_page"] += 1
            st.rerun()

db.close()
