# -*- coding: utf-8 -*-
import streamlit as st
from database import SessionLocal
import time
from services.warehouse_service import create_warehouse, get_warehouses, delete_warehouse, update_warehouse
from services.budget_service import get_budgets
from utils.auth import require_cliente, get_current_user_id
from utils.navbar import render_navbar, render_sidebar_menu

st.set_page_config(page_title="Almacenes — Sistema MRP", layout="wide", initial_sidebar_state="expanded")

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
.wh-card {
    display: flex; align-items: center; gap: 1rem;
    padding: .85rem 1.1rem; border-radius: 14px;
    border: 1px solid rgba(37,99,235,.15);
    background: linear-gradient(135deg, rgba(37,99,235,.07) 0%, rgba(79,70,229,.04) 100%);
    transition: border-color .18s, background .18s, box-shadow .18s;
    position: relative; overflow: hidden;
}
.wh-card::before {
    content:""; position:absolute; left:0; top:0; bottom:0;
    width:3px; border-radius:3px 0 0 3px;
    background: linear-gradient(180deg, #2563eb, #4f46e5);
}
.wh-card:hover {
    border-color: rgba(37,99,235,.32);
    background: linear-gradient(135deg, rgba(37,99,235,.12) 0%, rgba(79,70,229,.07) 100%);
    box-shadow: 0 4px 20px rgba(37,99,235,.12);
}
.wh-card-obra::before { background: linear-gradient(180deg, #0d9488, #0891b2); }
.wh-card-obra { border-color: rgba(13,148,136,.15); background: linear-gradient(135deg, rgba(13,148,136,.07) 0%, rgba(8,145,178,.04) 100%); }
.wh-card-obra:hover { border-color: rgba(13,148,136,.32); background: linear-gradient(135deg, rgba(13,148,136,.12) 0%, rgba(8,145,178,.07) 100%); box-shadow: 0 4px 20px rgba(13,148,136,.12); }
.wh-avatar {
    width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
    background: linear-gradient(135deg, #1d4ed8, #4f46e5);
    display: flex; align-items: center; justify-content: center;
    font-size: .95rem; font-weight: 800; color: #fff;
    box-shadow: 0 2px 10px rgba(37,99,235,.30);
}
.wh-avatar-obra { background: linear-gradient(135deg, #0d9488, #0891b2); box-shadow: 0 2px 10px rgba(13,148,136,.30); }
.wh-body { flex: 1; min-width: 0; }
.wh-title-row { display: flex; align-items: center; gap: .55rem; flex-wrap: wrap; margin-bottom: .2rem; }
.wh-name  { font-size: .90rem; font-weight: 800; color: #f1f5f9; }
.wh-meta  { display: flex; align-items: center; gap: .9rem; flex-wrap: wrap; }
.wh-meta-item { font-size: .72rem; color: rgba(148,163,184,.70); display: flex; align-items: center; gap: .28rem; }
.badge-principal { display:inline-block; padding:.18rem .62rem; border-radius:20px; font-size:.68rem; font-weight:700; background:rgba(37,99,235,.18); color:#60a5fa; border:1px solid rgba(37,99,235,.22); }
.badge-obra      { display:inline-block; padding:.18rem .62rem; border-radius:20px; font-size:.68rem; font-weight:700; background:rgba(13,148,136,.18); color:#2dd4bf; border:1px solid rgba(13,148,136,.22); }
.wh-del-btn { flex-shrink: 0; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_menu()

db = SessionLocal()
owner_id = get_current_user_id()
warehouses = get_warehouses(db, owner_id=owner_id)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="op-hero">
  <div class="op-hero-left">
    <div class="op-hero-icon">&#127970;</div>
    <div>
      <h1>Almacenes</h1>
      <p>Gestiona tus almacenes principales y de obra</p>
    </div>
  </div>
  <div class="op-badge">{len(warehouses)} almacenes registrados</div>
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
    st.markdown("#### Almacenes — Guía de uso")
    st.markdown("""
**Crear un almacén**
1. Despliega **Nuevo almacén** y completa: Nombre, Tipo, Ciudad/Distrito y Dirección.
2. Elige **principal** para tu almacén central o **obra** para el sitio de trabajo.
3. Presiona **Crear Almacén**; aparecerá en la lista de inmediato.

**Tipos de almacén**
- **Principal:** almacén central donde reside el stock disponible para despacho.
- **Obra:** almacén de sitio que recibe materiales via requerimientos y recepciones.

**Editar y eliminar**
- Usa **Editar almacén existente** para cambiar cualquier campo.
- El botón **Eliminar** borra el almacén permanentemente; esta acción no se puede deshacer.

> Necesitas al menos un almacén **principal** y uno de **obra** para poder crear requerimientos.
""")

# ── Crear ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Crear Almacén</div>', unsafe_allow_html=True)

if st.session_state.get("wh_created_msg"):
    st.success(st.session_state.pop("wh_created_msg"))

_fv = st.session_state.get("_wh_form_ver", 0)

with st.expander("Nuevo almacén", expanded=False):
    col_a, col_b = st.columns(2, gap="medium")
    name     = col_a.text_input("Nombre *", placeholder="Ej: Almacén Central", key=f"new_wh_name_{_fv}")
    type_    = col_b.selectbox("Tipo", ["principal", "obra"], key=f"new_wh_type_{_fv}")
    col_c, col_d = st.columns(2, gap="medium")
    location = col_c.text_input("Ciudad/Distrito *", placeholder="Ej: Lima - Miraflores", key=f"new_wh_loc_{_fv}")
    address  = col_d.text_input("Dirección *", placeholder="Ej: Av. Industrial 245, Piso 2", key=f"new_wh_addr_{_fv}")

    if st.button("Crear Almacén", type="primary", use_container_width=True, key="btn_new_wh"):
        missing = [f for f, v in [("Nombre", name), ("Ciudad/Distrito", location), ("Dirección", address)] if not v.strip()]
        if missing:
            st.error(f"Campos obligatorios faltantes: **{', '.join(missing)}**.")
        else:
            result = create_warehouse(db, name.strip(), type_, location.strip(),
                                      owner_id=owner_id, address=address.strip())
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["_wh_form_ver"] = _fv + 1
                st.session_state["wh_created_msg"] = "Almacén creado correctamente."
                st.rerun()

# ── Lista ─────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="sec-title">Almacenes Registrados ({len(warehouses)})</div>', unsafe_allow_html=True)

if not warehouses:
    st.info("No hay almacenes registrados. Crea el primero con el formulario de arriba.")
else:
    for w in warehouses:
        init       = w.name[0].upper() if w.name else "A"
        is_obra    = w.type == "obra"
        card_cls   = "wh-card wh-card-obra" if is_obra else "wh-card"
        avatar_cls = "wh-avatar wh-avatar-obra" if is_obra else "wh-avatar"
        badge      = '<span class="badge-obra">Obra</span>' if is_obra \
                     else '<span class="badge-principal">Principal</span>'

        loc_parts = [p for p in [w.location, w.address] if p]
        loc_icon  = "📍" if loc_parts else ""
        loc_text  = " &nbsp;·&nbsp; ".join(loc_parts) if loc_parts else "Sin dirección registrada"

        col_card, col_del = st.columns([11, 1], gap="small")
        with col_card:
            st.markdown(f"""
            <div class="{card_cls}">
              <div class="{avatar_cls}">{init}</div>
              <div class="wh-body">
                <div class="wh-title-row">
                  <span class="wh-name">{w.name}</span>
                  {badge}
                </div>
                <div class="wh-meta">
                  <span class="wh-meta-item">{loc_icon} {loc_text}</span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        with col_del:
            st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)
            if st.button("✕", key=f"del_{w.id}", use_container_width=True, type="primary",
                         help=f"Eliminar {w.name}"):
                st.session_state["confirm_del_id"] = w.id

        if st.session_state.get("confirm_del_id") == w.id:
            c_msg, c_yes, c_no = st.columns([5, 1, 1], gap="small")
            c_msg.warning(f"¿Seguro que deseas eliminar **{w.name}**? Esta acción no se puede deshacer.")
            if c_yes.button("Sí, eliminar", key=f"yes_del_{w.id}", type="primary", use_container_width=True):
                delete_warehouse(db, w.id)
                del st.session_state["confirm_del_id"]
                st.rerun()
            if c_no.button("Cancelar", key=f"no_del_{w.id}", use_container_width=True):
                del st.session_state["confirm_del_id"]
                st.rerun()

# if warehouses:

#     selected_name = st.selectbox(
#         "Selecciona un almacén",
#         [w.name for w in warehouses]
#     )

#     selected = next((w for w in warehouses if w.name == selected_name), None)

#     if selected:
#         new_name = st.text_input("Nombre", value=selected.name)
#         new_type = st.selectbox(
#             "Tipo",
#             ["principal", "obra"],
#             index=0 if selected.type == "principal" else 1
#         )
#         new_location = st.text_input("Ubicación", value=selected.location)

#         if st.button("Actualizar"):
#             accept=update_warehouse(db, selected.id, new_name, new_type, new_location)
            
#             # Crear un contenedor para el mensaje
#             mensaje_container = st.empty()
            
#             if "error" in accept:
#                 mensaje_container.error(accept["error"])
#             else:
#                 mensaje_container.success(accept["value"])
            
#             # Esperar 2 segundos y luego limpiar
#             time.sleep(2)
#             mensaje_container.empty()
#             st.rerun()
# else:
#     st.info("No hay almacenes registrados. Por favor, crea uno primero.")
#     st.write("Para crear un almacén, completa el formulario en la sección '➕ Crear Almacén' y haz clic en 'Crear'.")

# ── Editar ────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Editar Almacén</div>', unsafe_allow_html=True)

if warehouses:
    with st.expander("Editar almacén existente", expanded=False):
        selected_name = st.selectbox("Selecciona un almacén", [w.name for w in warehouses])
        selected = next((w for w in warehouses if w.name == selected_name), None)

        if selected:
            col_a, col_b = st.columns(2, gap="medium")
            new_name = col_a.text_input("Nombre", value=selected.name)
            new_type = col_b.selectbox("Tipo", ["principal", "obra"],
                                       index=0 if selected.type == "principal" else 1)
            col_c, col_d = st.columns(2, gap="medium")
            new_location = col_c.text_input("Ciudad/Distrito", value=selected.location or "")
            new_address  = col_d.text_input("Dirección",       value=getattr(selected, "address", "") or "")

            if st.button("Actualizar", type="primary", key="btn_update_wh"):
                result = update_warehouse(db, selected.id, new_name, new_type, new_location, address=new_address)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(result.get("value", "Almacén actualizado correctamente."))
                    st.rerun()
else:
    st.info("No hay almacenes para editar.")

db.close()
