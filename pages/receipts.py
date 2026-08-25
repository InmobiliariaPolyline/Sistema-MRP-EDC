# -*- coding: utf-8 -*-
import streamlit as st
import io, csv
from datetime import timezone, timedelta
from database import SessionLocal
from services.receipt_service import create_receipt
from services.budget_service import get_budgets
from models.dispatch import Dispatch
from models.requirement import Requirement
from models.warehouse import Warehouse
from utils.auth import require_cliente, get_current_user_id
from utils.navbar import render_navbar, render_sidebar_menu


st.set_page_config(page_title="Recepciones - MRP System", layout="wide")

_LIMA = timezone(timedelta(hours=-5))

def _fmt_lima(dt):
    if dt is None:
        return ""
    return dt.replace(tzinfo=timezone.utc).astimezone(_LIMA).strftime("%d/%m/%Y %H:%M")

st.set_page_config(page_title="Recepciones — Sistema MRP", layout="wide", initial_sidebar_state="expanded")

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
label[data-testid="stWidgetLabel"] p { font-size: .80rem !important; font-weight: 600 !important; }
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; box-shadow: 0 2px 14px rgba(37,99,235,.35) !important;
    transition: all .2s !important;
}
[data-testid="stBaseButton-primary"]:hover { opacity: .9 !important; transform: translateY(-1px) !important; }
[data-testid="stAlert"] { border-radius: 10px !important; }

.recv-item {
    display: flex; align-items: center; gap: .75rem;
    padding: .65rem 1rem; border-radius: 10px;
    border: 1px solid rgba(16,185,129,.15); background: rgba(16,185,129,.04);
    margin-bottom: .4rem;
}
.recv-icon {
    width: 34px; height: 34px; border-radius: 8px; flex-shrink: 0;
    background: linear-gradient(135deg, #065f46, #059669);
    display: flex; align-items: center; justify-content: center;
    font-size: .85rem; font-weight: 800; color: #fff;
}
.recv-name { font-size: .85rem; font-weight: 700; }
.recv-qty  { font-size: .78rem; opacity: .85; }
.recv-done { font-size: .75rem; color: #6b7280; font-style: italic; }
.recv-lbl {
    font-size: .62rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .06em;
    color: rgba(148,163,184,.55); margin-right: .25rem;
}

/* ── Historial de recepciones ── */
.hist-card {
    display: flex; gap: 1.4rem; padding: 1rem 1.3rem;
    border-radius: 16px; border: 1px solid rgba(16,185,129,.18);
    background: linear-gradient(135deg, rgba(16,185,129,.06) 0%, rgba(5,150,105,.03) 100%);
    margin-bottom: .75rem; flex-wrap: wrap; position: relative; overflow: hidden;
}
.hist-card::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0;
    width: 4px; background: linear-gradient(180deg, #10b981, #059669);
    border-radius: 4px 0 0 4px;
}
.hist-guia {
    min-width: 130px; display: flex; flex-direction: column; gap: .18rem;
}
.hist-label {
    font-size: .60rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .07em; color: rgba(148,163,184,.50);
}
.hist-guia-num { font-size: .92rem; font-weight: 900; color: #34d399; }
.hist-guia-date { font-size: .70rem; color: rgba(148,163,184,.50); }
.hist-mats { flex: 1; min-width: 180px; }
.hist-mat-pill {
    display: inline-flex; align-items: center; gap: .45rem;
    background: rgba(16,185,129,.10); border: 1px solid rgba(16,185,129,.20);
    border-radius: 20px; padding: .22rem .75rem;
    font-size: .74rem; font-weight: 700; color: #6ee7b7;
    margin: .15rem .2rem .15rem 0;
}
.hist-mat-pill .pill-lbl {
    font-size: .58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .04em;
    color: rgba(148,163,184,.65);
}
.hist-mat-pill .pill-val   { color: #6ee7b7; font-weight: 700; }
.hist-mat-pill .pill-sep   { color: rgba(148,163,184,.30); margin: 0 .15rem; }

.hist-meta-row {
    display: flex; gap: .35rem; flex-wrap: wrap; margin-top: .42rem;
}
.recv-meta-chip, .recv-proj-chip {
    display: inline-flex; align-items: baseline; gap: .35rem;
    padding: .15rem .55rem; border-radius: 8px;
    background: rgba(15,23,42,.40);
    border: 1px solid rgba(255,255,255,.05);
}
.recv-proj-chip {
    background: rgba(5,150,105,.10);
    border-color: rgba(5,150,105,.25);
}
.recv-proj-chip.empty {
    background: rgba(239,68,68,.06);
    border-color: rgba(239,68,68,.18);
}
.recv-mini-lbl {
    font-size: .58rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .05em;
    color: rgba(148,163,184,.55);
}
.recv-mini-val { font-size: .72rem; font-weight: 700; color: #e2e8f0; }
.recv-proj-chip .recv-mini-val { color: #6ee7b7; }
.recv-proj-chip.empty .recv-mini-val { color: #fca5a5; font-style: italic; }
.hist-recv-info {
    min-width: 140px; display: flex; flex-direction: column;
    align-items: flex-end; gap: .18rem; text-align: right;
}
.hist-recv-check {
    display: inline-flex; align-items: center; justify-content: center;
    width: 26px; height: 26px; border-radius: 50%;
    background: linear-gradient(135deg, #059669, #10b981);
    font-size: .82rem; font-weight: 900; color: #fff;
    margin-bottom: .18rem;
}
.hist-recv-date { font-size: .78rem; font-weight: 700; color: #34d399; }
.hist-obra { font-size: .68rem; color: rgba(148,163,184,.45); }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_menu()


st.title("📥 Recepción de Materiales")

db       = SessionLocal()
owner_id = get_current_user_id()

# Mapa id → nombre para los almacenes del usuario
_all_wh     = db.query(Warehouse).filter(Warehouse.owner_id == owner_id).all()
wh_id_name  = {w.id: w.name for w in _all_wh}

# Solo despachos del usuario actual que aún no tienen recepción
dispatches = (
    db.query(Dispatch)
    .join(Requirement, Dispatch.requirement_id == Requirement.id)
    .join(Warehouse, Requirement.warehouse_id_obra == Warehouse.id)
    .filter(Warehouse.owner_id == owner_id)
    .filter(Dispatch.status != "cancelled")
    .filter(~Dispatch.receipt.has())
    .order_by(Dispatch.dispatch_date.desc())
    .all()
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="op-hero">
  <div class="op-hero-left">
    <div class="op-hero-icon">&#128229;</div>
    <div>
      <h1>Recepciones</h1>
      <p>Confirma la llegada de materiales al almacén de obra</p>
    </div>
  </div>
  <div class="op-badge">{len(dispatches)} despacho{'s' if len(dispatches) != 1 else ''} pendiente{'s' if len(dispatches) != 1 else ''} de recepción</div>
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
    st.markdown("#### Recepciones — Guía de uso")
    st.markdown("""
**Confirmar una recepción**
1. Selecciona el **despacho** que llegó al almacén de obra.
2. Verifica la lista de materiales y las cantidades despachadas.
3. Presiona **Confirmar Recepción**; el stock del almacén de obra aumentará automáticamente.

**Flujo completo**
- Requerimiento → Despacho → **Recepción**.
- La recepción es el último paso del proceso. Una vez confirmada, el material queda registrado en el almacén de obra.

> Los materiales que ya fueron recibidos se muestran en gris. Solo los que tienen cantidad mayor a 0 generan movimiento de inventario.
""")

# ── Confirmar recepción ───────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Confirmar Recepción</div>', unsafe_allow_html=True)


if not dispatches:
    st.info("No hay despachos disponibles. Genera uno desde la sección Despachos.")
else:
    disp_options = {
        f"Despacho #{d.id} — {d.guia_number or 'Sin guía'} — {d.dispatch_date.strftime('%d/%m/%Y %H:%M') if d.dispatch_date else 'Sin fecha'}": d.id
        for d in dispatches
    }

    selected_label = st.selectbox("Selecciona despacho", list(disp_options.keys()), key="recv_disp_sel")
    dispatch_id    = disp_options[selected_label]
    dispatch       = db.query(Dispatch).filter(Dispatch.id == dispatch_id).first()

    st.markdown('<div class="sec-title">Materiales del Despacho</div>', unsafe_allow_html=True)

    if dispatch and dispatch.items:
        has_pending = False
        recv_cost_total = 0.0

        # Header con proyecto + obra del despacho
        _disp_req   = dispatch.requirement
        _disp_proj  = getattr(_disp_req, "budget_name", None) if _disp_req else None
        _disp_obra  = wh_id_name.get(_disp_req.warehouse_id_obra, f"Almacén #{_disp_req.warehouse_id_obra}") if _disp_req else "—"
        _proj_chip  = (
            f"<span class='recv-proj-chip'><span class='recv-mini-lbl'>Proyecto:</span>"
            f"<span class='recv-mini-val'>{_disp_proj}</span></span>"
            if _disp_proj else
            "<span class='recv-proj-chip empty'>"
            "<span class='recv-mini-lbl'>Proyecto:</span>"
            "<span class='recv-mini-val'>— sin proyecto —</span></span>"
        )
        st.markdown(
            "<div class='hist-meta-row' style='margin-bottom:.7rem'>"
              f"<span class='recv-meta-chip'><span class='recv-mini-lbl'>Despacho:</span>"
              f"<span class='recv-mini-val'>{dispatch.guia_number or f'#{dispatch.id}'}</span></span>"
              f"<span class='recv-meta-chip'><span class='recv-mini-lbl'>Obra:</span>"
              f"<span class='recv-mini-val'>{_disp_obra}</span></span>"
              f"{_proj_chip}"
            "</div>",
            unsafe_allow_html=True,
        )

        for item in dispatch.items:
            mat_name     = item.material.name if item.material else f"Material {item.material_id}"
            mat_unit     = (item.material.unit or "").strip() if item.material else ""
            unit_price   = float(item.material.unit_price or 0) if item.material else 0.0
            unit_price_d = float(item.material.unit_price_dolares or 0) if item.material else 0.0
            item_cost    = item.dispatched_qty * unit_price
            item_cost_d  = item.dispatched_qty * unit_price_d
            init         = mat_name[0].upper()
            qty_lbl      = mat_unit if mat_unit else "uds"
            if item.dispatched_qty > 0:
                has_pending = True
                recv_cost_total += item_cost
                _ps  = f"<span class='pill-lbl'>Precio S/.:</span> <span class='pill-val'>S/ {unit_price:,.2f}</span>" if unit_price > 0 else ""
                _pd  = f"<span class='pill-lbl' style='margin-left:.4rem'>Precio $:</span> <span class='pill-val'>$ {unit_price_d:,.2f}</span>" if unit_price_d > 0 else ""
                _cst = (
                    f"<div style='font-size:.72rem;color:rgba(148,163,184,.65);margin-top:.18rem'>"
                    f"{_ps}{_pd}"
                    + (f" <span class='pill-lbl' style='margin-left:.55rem'>Total:</span> <span style='color:#fbbf24;font-weight:700'>S/ {item_cost:,.2f}</span>" if unit_price > 0 else "")
                    + (f" <span class='pill-lbl' style='margin-left:.35rem'>/</span> <span style='color:#60a5fa;font-weight:700'>$ {item_cost_d:,.2f}</span>" if unit_price_d > 0 else "")
                    + "</div>"
                )
                st.markdown(f"""
                <div class="recv-item">
                  <div class="recv-icon">{init}</div>
                  <div style="flex:1">
                    <div class="recv-name"><span class="recv-lbl">Nombre:</span> {mat_name}</div>
                    <div class="recv-qty"><span class="recv-lbl">Cantidad:</span> <b>{item.dispatched_qty}</b> {qty_lbl}</div>
                    {_cst}
                  </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="recv-item" style="opacity:.45">
                  <div class="recv-icon" style="background:linear-gradient(135deg,#374151,#6b7280)">{init}</div>
                  <div>
                    <div class="recv-name"><span class="recv-lbl">Nombre:</span> {mat_name}</div>
                    <div class="recv-done">Ya recibido anteriormente</div>
                  </div>
                </div>""", unsafe_allow_html=True)

        if recv_cost_total > 0 and has_pending:
            st.markdown(f"""
<div style="display:flex;justify-content:flex-end;align-items:center;gap:.6rem;
            margin:.3rem 0 .5rem;padding:.5rem 1rem;border-radius:10px;
            border:1px solid rgba(251,191,36,.22);background:rgba(251,191,36,.05)">
  <span style="font-size:.72rem;color:rgba(148,163,184,.55);font-weight:600">
    Costo total de materiales a recibir
  </span>
  <span style="font-size:.95rem;font-weight:900;color:#fbbf24">S/ {recv_cost_total:,.2f}</span>
</div>""", unsafe_allow_html=True)


# -------------------------
# DETALLE
# -------------------------
# dispatch = db.query(Dispatch).filter(
#     Dispatch.id == dispatch_id
# ).first()

# st.subheader("Materiales despachados")


# if dispatch and dispatch.items:
#     for item in dispatch.items:
#         if item.dispatched_qty > 0:
#             st.write(f"Material {item.material_id} - Cantidad: {item.dispatched_qty}")
#         else:
#             st.write(f"Material {item.material_id} - Cantidad: 0 (ya se ha recibido)")
#     if st.button("Confirmar Recepción"):
#         success, msg = create_receipt(db, dispatch_id)

#         if success:
#             st.success(msg)
#             st.rerun()
#         else:

#             st.error(msg)
# else:
#     st.info("No hay materiales despachados para este despacho o el despacho no existe.")



        if has_pending:
            st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
            if st.button("Confirmar Recepción", type="primary", key="btn_confirm_recv"):
                success, msg = create_receipt(db, dispatch_id, user_id=owner_id, owner_id=owner_id)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("Todos los materiales de este despacho ya han sido recibidos.")
    else:
        st.info("No hay materiales en este despacho.")

# ── Historial de recepciones ──────────────────────────────────────────────────
st.markdown('<div class="sec-title">Historial de Recepciones</div>', unsafe_allow_html=True)

received_dispatches = (
    db.query(Dispatch)
    .join(Requirement, Dispatch.requirement_id == Requirement.id)
    .join(Warehouse, Requirement.warehouse_id_obra == Warehouse.id)
    .filter(Warehouse.owner_id == owner_id)
    .filter(Dispatch.receipt.has())
    .order_by(Dispatch.dispatch_date.desc())
    .all()
)

if not received_dispatches:
    st.info("Aún no hay recepciones registradas.")
else:
    # ── Filtros ───────────────────────────────────────────────────────────────
    _obra_options = ["Todas"] + sorted({
        wh_id_name.get(d.requirement.warehouse_id_obra, f"Almacén #{d.requirement.warehouse_id_obra}")
        for d in received_dispatches if d.requirement
    })
    _proj_options = ["Todos"] + sorted({
        (d.requirement.budget_name if d.requirement and d.requirement.budget_name else "— sin proyecto —")
        for d in received_dispatches
    })

    _rf1, _rf2, _rf3, _rf4, _rf5 = st.columns([1.8, 1.8, 1.5, 1.5, 1.8], gap="small")
    _rf_obra = _rf1.selectbox("Obra", _obra_options, key="recv_hist_f_obra")
    _rf_proj = _rf2.selectbox("Proyecto", _proj_options, key="recv_hist_f_proj")
    _rf_from = _rf3.date_input("Desde", value=None, key="recv_hist_f_from")
    _rf_to   = _rf4.date_input("Hasta", value=None, key="recv_hist_f_to")
    _rf_guia = _rf5.text_input(
        "Guía", value="", key="recv_hist_f_guia",
        placeholder="Buscar por nº de guía...",
    )

    _filtered_recv = received_dispatches
    if _rf_obra != "Todas":
        _filtered_recv = [
            d for d in _filtered_recv
            if d.requirement and wh_id_name.get(d.requirement.warehouse_id_obra, "") == _rf_obra
        ]
    if _rf_proj != "Todos":
        if _rf_proj == "— sin proyecto —":
            _filtered_recv = [d for d in _filtered_recv if not (d.requirement and d.requirement.budget_name)]
        else:
            _filtered_recv = [d for d in _filtered_recv if d.requirement and d.requirement.budget_name == _rf_proj]
    if _rf_from:
        _filtered_recv = [
            d for d in _filtered_recv
            if d.receipt and d.receipt.receipt_date and d.receipt.receipt_date.date() >= _rf_from
        ]
    if _rf_to:
        _filtered_recv = [
            d for d in _filtered_recv
            if d.receipt and d.receipt.receipt_date and d.receipt.receipt_date.date() <= _rf_to
        ]
    if _rf_guia.strip():
        _q = _rf_guia.strip().lower()
        _filtered_recv = [d for d in _filtered_recv if (d.guia_number or "").lower().find(_q) >= 0]

    st.caption(
        f"{len(_filtered_recv)} recepci{'ones' if len(_filtered_recv) != 1 else 'ón'} encontrada{'s' if len(_filtered_recv) != 1 else ''} "
        f"(de {len(received_dispatches)} total{'es' if len(received_dispatches) != 1 else ''})."
    )

    if not _filtered_recv:
        st.info("No se encontraron recepciones con los filtros aplicados.")
        db.close()
        st.stop()

    RECV_PG   = 10
    total_r   = len(_filtered_recv)
    total_rp  = max(1, (total_r + RECV_PG - 1) // RECV_PG)
    recv_pg   = st.session_state.get("recv_hist_page", 1)
    recv_pg   = max(1, min(recv_pg, total_rp))
    page_recv = _filtered_recv[(recv_pg - 1) * RECV_PG: recv_pg * RECV_PG]

    # ── CSV download + pagination controls (respeta los filtros) ─────────────
    _csv_buf = io.StringIO()
    _csv_w   = csv.writer(_csv_buf)
    _csv_w.writerow(["Guía", "Req.", "Almacén Obra", "Proyecto", "Material", "Unidad", "Cantidad", "Fecha Despacho", "Fecha Recepción"])
    for _d in _filtered_recv:
        _rec      = _d.receipt
        _obra_n   = wh_id_name.get(_d.requirement.warehouse_id_obra, f"Almacén #{_d.requirement.warehouse_id_obra}")
        _dd       = _fmt_lima(_d.dispatch_date)
        _rd       = _fmt_lima(_rec.receipt_date) if _rec else ""
        _proj_n = (_d.requirement.budget_name or "") if _d.requirement else ""
        for _it in _d.items:
            _csv_w.writerow([
                _d.guia_number, _d.requirement_id, _obra_n, _proj_n,
                (_it.material.name if _it.material else f"Material {_it.material_id}"),
                (_it.material.unit if _it.material else ""),
                _it.dispatched_qty, _dd, _rd,
            ])
    _csv_data = _csv_buf.getvalue()

    dl_col, pg_col = st.columns([2, 4], gap="medium")
    with dl_col:
        st.download_button(
            "Descargar CSV",
            data=_csv_data.encode("utf-8"),
            file_name="historial_recepciones.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Para imprimir: usa Ctrl+P en el navegador")

    with pg_col:
        pp1, pp2, pp3 = st.columns([1, 3, 1])
        if pp1.button("← Ant.", key="recv_prev", disabled=recv_pg <= 1):
            st.session_state["recv_hist_page"] = recv_pg - 1
            st.rerun()
        pp2.markdown(
            f"<div style='text-align:center;font-size:.78rem;color:rgba(148,163,184,.60);padding:.45rem 0'>"
            f"Página {recv_pg} de {total_rp} &nbsp;·&nbsp; {total_r} registros</div>",
            unsafe_allow_html=True,
        )
        if pp3.button("Sig. →", key="recv_next", disabled=recv_pg >= total_rp):
            st.session_state["recv_hist_page"] = recv_pg + 1
            st.rerun()

    st.markdown("<div style='margin-bottom:.5rem'></div>", unsafe_allow_html=True)

    for d in page_recv:
        receipt    = d.receipt
        obra_name  = wh_id_name.get(d.requirement.warehouse_id_obra, f"Almacén #{d.requirement.warehouse_id_obra}")
        disp_date  = _fmt_lima(d.dispatch_date) or "—"
        recv_date  = _fmt_lima(receipt.receipt_date) if receipt else "—"

        recv_total_cost = sum(
            it.dispatched_qty * float(it.material.unit_price or 0)
            for it in d.items if it.material
        )

        mats_html = "".join(
            f"<span class='hist-mat-pill'>"
            f"<span class='pill-lbl'>Nombre:</span>"
            f"<span class='pill-val'>{it.material.name if it.material else f'Mat.{it.material_id}'}</span>"
            f"<span class='pill-sep'>·</span>"
            f"<span class='pill-lbl'>Cant.:</span>"
            f"<span class='pill-val'>{it.dispatched_qty}"
            f"{(' ' + it.material.unit) if it.material and it.material.unit else ''}</span>"
            f"</span>"
            for it in d.items
        )

        cost_badge = (
            f"<div style='margin-top:.35rem;display:inline-flex;align-items:center;gap:.3rem;"
            f"background:rgba(251,191,36,.10);border:1px solid rgba(251,191,36,.22);"
            f"border-radius:8px;padding:.18rem .55rem;font-size:.70rem;font-weight:700;color:#fbbf24'>"
            f"<span class='recv-mini-lbl'>Costo total:</span> S/ {recv_total_cost:,.2f}</div>"
            if recv_total_cost > 0 else ""
        )

        _h_proj = getattr(d.requirement, "budget_name", None) if d.requirement else None
        _proj_chip_h = (
            f"<span class='recv-proj-chip'><span class='recv-mini-lbl'>Proyecto:</span>"
            f"<span class='recv-mini-val'>{_h_proj}</span></span>"
            if _h_proj else
            "<span class='recv-proj-chip empty'>"
            "<span class='recv-mini-lbl'>Proyecto:</span>"
            "<span class='recv-mini-val'>— sin proyecto —</span></span>"
        )

        st.markdown(f"""
<div class="hist-card">
  <div class="hist-guia">
    <div class="hist-label">Guía</div>
    <div class="hist-guia-num">{d.guia_number or f'Despacho #{d.id}'}</div>
    <div class="hist-label" style="margin-top:.32rem">Despachado</div>
    <div class="hist-guia-date">{disp_date}</div>
  </div>
  <div class="hist-mats">
    <div class="hist-label" style="margin-bottom:.3rem">Materiales recibidos</div>
    {mats_html if mats_html else '<span style="font-size:.75rem;color:rgba(148,163,184,.40)">Sin ítems</span>'}
    <div class="hist-meta-row">
      <span class="recv-meta-chip"><span class="recv-mini-lbl">Req.:</span>
        <span class="recv-mini-val">#{d.requirement_id}</span></span>
      <span class="recv-meta-chip"><span class="recv-mini-lbl">Obra:</span>
        <span class="recv-mini-val">{obra_name}</span></span>
      {_proj_chip_h}
    </div>
    {cost_badge}
  </div>
  <div class="hist-recv-info">
    <div class="hist-recv-check">✓</div>
    <div class="hist-label">Recibido el</div>
    <div class="hist-recv-date">{recv_date}</div>
    <div class="hist-obra">hora Lima (UTC-5)</div>
  </div>
</div>""", unsafe_allow_html=True)

db.close()
