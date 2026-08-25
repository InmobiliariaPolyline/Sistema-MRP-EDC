# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
from database import SessionLocal
from services.material_service import (
    create_material,
    get_materials,
    delete_material,
    get_materials_filtered,
    update_material,
    delete_material_code,
)
from services.budget_service import get_budgets
from models.inventory import Inventory
from models.warehouse import Warehouse
from utils.auth import require_cliente, get_current_user_id
from utils.navbar import render_navbar, render_sidebar_menu

st.set_page_config(page_title="Materiales — Sistema MRP", layout="wide", initial_sidebar_state="expanded")

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
.mat-table { border-radius: 12px; overflow: hidden; border: 1px solid rgba(37,99,235,.15); }

/* ── Tarjeta de material ── */
.mat-info-card {
    padding: .92rem 1.25rem .85rem 1.55rem !important;
    border-radius: 14px !important;
    border: 1px solid rgba(37,99,235,.20) !important;
    background: linear-gradient(135deg, rgba(37,99,235,.08) 0%, rgba(79,70,229,.04) 100%) !important;
    position: relative !important;
    overflow: hidden !important;
    transition: border-color .18s, background .18s, box-shadow .18s !important;
    cursor: default !important;
}
.mat-info-card::before {
    content: "" !important;
    position: absolute !important;
    left: 0 !important; top: 0 !important; bottom: 0 !important;
    width: 4px !important;
    border-radius: 4px 0 0 4px !important;
    background: linear-gradient(180deg, #2563eb, #4f46e5) !important;
}
.mat-info-card:hover {
    border-color: rgba(37,99,235,.40) !important;
    background: linear-gradient(135deg, rgba(37,99,235,.13) 0%, rgba(79,70,229,.07) 100%) !important;
    box-shadow: 0 4px 22px rgba(37,99,235,.14) !important;
}
.mat-card-header {
    display: flex; align-items: center; gap: .65rem;
    flex-wrap: wrap; margin-bottom: .55rem;
    padding-bottom: .45rem;
    border-bottom: 1px solid rgba(37,99,235,.14);
}
.mat-card-name {
    font-weight: 800; color: #f1f5f9; font-size: 1.02rem;
    margin-right: auto;
}
.mat-id-chip {
    display: inline-flex; align-items: center;
    padding: .22rem .7rem; border-radius: 20px;
    font-size: .68rem; font-weight: 800;
    background: rgba(37,99,235,.22); color: #93c5fd;
    border: 1px solid rgba(37,99,235,.32);
    white-space: nowrap; letter-spacing: .03em;
    font-family: ui-monospace, SFMono-Regular, monospace;
}
.mat-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
    gap: .55rem .9rem;
}
.mat-field {
    display: flex; flex-direction: column;
    gap: .15rem;
    padding: .35rem .55rem;
    border-radius: 8px;
    background: rgba(15,23,42,.30);
    border: 1px solid rgba(255,255,255,.04);
}
.mat-field-lbl {
    font-size: .60rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .08em;
    color: rgba(148,163,184,.55);
}
.mat-field-val {
    font-size: .85rem; font-weight: 700;
    color: #e2e8f0; line-height: 1.2;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.mat-field-val.empty { color: rgba(148,163,184,.40); font-style: italic; font-weight: 500; }
.mat-field-val.price-s { color: #34d399; }
.mat-field-val.price-d { color: #60a5fa; }

/* ── Chips de proyectos usando el material ── */
.mat-proj-row {
    margin-top: .55rem;
    padding-top: .5rem;
    border-top: 1px dashed rgba(37,99,235,.18);
    display: flex; flex-wrap: wrap; gap: .35rem;
    align-items: center;
}
.mat-proj-lbl {
    font-size: .60rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .08em;
    color: rgba(148,163,184,.60);
    margin-right: .25rem;
}
.mat-proj-chip {
    display: inline-flex; align-items: center; gap: .3rem;
    padding: .15rem .55rem; border-radius: 20px;
    font-size: .68rem; font-weight: 700;
    background: rgba(5,150,105,.18); color: #6ee7b7;
    border: 1px solid rgba(5,150,105,.30);
    white-space: nowrap;
}
.mat-proj-chip.inactive {
    background: rgba(148,163,184,.12); color: #94a3b8;
    border-color: rgba(148,163,184,.28);
}
.mat-proj-qty {
    font-size: .62rem; font-weight: 800;
    background: rgba(255,255,255,.10);
    border-radius: 10px; padding: 0 .35rem;
}
.mat-noproj-chip {
    display: inline-flex; align-items: center;
    padding: .12rem .5rem; border-radius: 20px;
    font-size: .62rem; font-weight: 600;
    background: rgba(148,163,184,.08); color: rgba(148,163,184,.55);
    border: 1px dashed rgba(148,163,184,.25);
}

/* ── Paginación ── */
.mat-pag-info {
    text-align: center; font-size: .80rem;
    color: rgba(148,163,184,.65); font-weight: 600;
    padding: .3rem 0;
}

/* ── Alineación vertical de botones con tarjeta de material ── */
[data-testid="stHorizontalBlock"]:has(.mat-info-card) {
    align-items: center !important;
}
[data-testid="stHorizontalBlock"]:has(.mat-info-card) > [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}

/* ── Botón editar (etiquetado por JS con data-action=edit) ── */
[data-testid="stMain"] button[data-action="edit"] {
    background: linear-gradient(135deg, rgba(37,99,235,.18), rgba(79,70,229,.10)) !important;
    border: 1px solid rgba(37,99,235,.40) !important;
    color: #93c5fd !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    height: 42px !important;
    box-shadow: 0 2px 8px rgba(37,99,235,.10) !important;
    transition: all .18s !important;
}
[data-testid="stMain"] button[data-action="edit"]:hover {
    background: linear-gradient(135deg, rgba(37,99,235,.32), rgba(79,70,229,.20)) !important;
    border-color: rgba(37,99,235,.70) !important;
    color: #bfdbfe !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(37,99,235,.22) !important;
}
[data-testid="stMain"] button[data-action="edit"][data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, rgba(37,99,235,.40), rgba(79,70,229,.30)) !important;
    border: 1px solid rgba(37,99,235,.75) !important;
    color: #dbeafe !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.16) !important;
}

/* ── Botón eliminar (etiquetado por JS con data-action=delete) ── */
[data-testid="stMain"] button[data-action="delete"] {
    background: linear-gradient(135deg, rgba(239,68,68,.16), rgba(220,38,38,.08)) !important;
    border: 1px solid rgba(239,68,68,.40) !important;
    color: #fca5a5 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    height: 42px !important;
    box-shadow: 0 2px 8px rgba(239,68,68,.10) !important;
    transition: all .18s !important;
}
[data-testid="stMain"] button[data-action="delete"]:hover {
    background: linear-gradient(135deg, rgba(239,68,68,.30), rgba(220,38,38,.18)) !important;
    border-color: rgba(239,68,68,.65) !important;
    color: #fee2e2 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(239,68,68,.22) !important;
}
</style>
<script>
(function(){
    function tagMatBtns(){
        document.querySelectorAll('[data-testid="stMain"] button').forEach(function(b){
            var t=b.textContent.trim();
            if(t==='✏'||t==='✏️') b.dataset.action='edit';
            else if(t==='✕'||t==='X'||t==='×') b.dataset.action='delete';
        });
    }
    tagMatBtns();
    var obs=new MutationObserver(tagMatBtns);
    obs.observe(document.body,{childList:true,subtree:true});
    setTimeout(tagMatBtns,150);setTimeout(tagMatBtns,500);
})();
</script>
""", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_menu()

# st.title("📦 Gestión de Materiales")

# # Inyectar CSS para personalizar el botón de eliminación (tipo primary)
# st.markdown("""
# <style>
# /* Estilo para el botón de acción destructiva (rojo) */
# div[data-testid="stColumn"] button[data-testid="stBaseButton-primary"] {
#     background-color: #A63C29 !important;
#     color: white !important;
#     border: none !important;
#     border-radius: 8px !important;
#     transition: all 0.3s ease !important;
# }
# div[data-testid="stColumn"] button[data-testid="stBaseButton-primary"]:hover {
#     background-color: #7A3427 !important;
#     transform: scale(1.02) !important;
# }
# </style>
# """, unsafe_allow_html=True)


db = SessionLocal()
owner_id = get_current_user_id()
materials = get_materials(db)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="op-hero">
  <div class="op-hero-left">
    <div class="op-hero-icon">&#128230;</div>
    <div>
      <h1>Materiales</h1>
      <p>Catálogo de materiales disponibles en el sistema</p>
    </div>
  </div>
  <div class="op-badge">{len(materials)} materiales registrados</div>
</div>
""", unsafe_allow_html=True)


# with st.expander("⚙️Formulario de creación", expanded=True):
#     col1, col2, col3 = st.columns(3)

#     with col1:
#         code = st.text_input("Código")
    
#     with col2:
#         name = st.text_input("Nombre")
#     with col3:
#         unit = st.text_input("Unidad (kg, m, unidad, etc.)")

#     col4 = st.columns(1)[0]
#     with col4:
#         description = st.text_area("Descripción")
#     submit = st.button("✅Crear", use_container_width=True)

#     if submit:
#         if code and name:
#             created, info = create_material(db, code, name, unit, description)
#             if created:
#                 st.success("Material creado correctamente")
#                 time.sleep(2)
#                 st.rerun()

# ── Instrucciones + Presupuestos Activos ──────────────────────────────────────
_, _col_budgets, _col_help = st.columns([4.6, 1.5, 1])
with _col_budgets.popover("📊 Presupuestos", use_container_width=True):
    st.markdown("#### Presupuestos Activos")
    _active_buds = [b for b in get_budgets(db) if b.is_active]
    if not _active_buds:
        st.info("No hay presupuestos activos registrados.")
    else:
        from services.inventory_service import get_budget_available as _get_avail
        for _b in _active_buds:
            _av_s, _av_d = _get_avail(db, _b.id)
            st.markdown(f"""
<div style="padding:.55rem .8rem;border-radius:10px;border:1px solid rgba(5,150,105,.25);
            background:rgba(5,150,105,.07);margin-bottom:.45rem">
  <div style="font-weight:800;font-size:.88rem;color:#6ee7b7">{_b.name}</div>
  <div style="font-size:.72rem;color:rgba(255,255,255,.42);margin-top:.16rem">
    Total: S/ {_b.budget_soles:,.2f} &nbsp;·&nbsp; $ {_b.budget_dolares:,.2f}
  </div>
  <div style="font-size:.78rem;color:#34d399;margin-top:.10rem;font-weight:700">
    Disponible: S/ {_av_s:,.2f} &nbsp;·&nbsp; $ {_av_d:,.2f}
  </div>
</div>""", unsafe_allow_html=True)
with _col_help.popover("Instrucciones", use_container_width=True):
    st.markdown("#### Materiales — Guía de uso")
    st.markdown("""
**Crear un material**
1. Despliega **Nuevo material** e ingresa: Código, Nombre, Unidad, Descripción y costos.
2. El **Código** debe ser único (por ejemplo: MAT-001). El **Nombre** también debe ser único.
3. En **Unidad** indica la unidad de medida (kg, m, unidad, litro, etc.).
4. **Costo S/.** y **Costo $** son opcionales; se usan para calcular presupuestos.
5. Presiona **Crear Material**; aparecerá en el catálogo de inmediato.

**Catálogo**
- La tabla muestra todos los materiales con código, nombre, unidad, descripción y precios.

**Editar y eliminar**
- Presiona ✏ para editar un material (incluye los campos de costo).
- Presiona ✕ para eliminar; la eliminación es permanente.

> Si eliminas un material que ya tiene stock en inventario, los registros quedarán huérfanos. Verifica primero.
""")

# ── Crear ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Crear Material</div>', unsafe_allow_html=True)

with st.expander("Nuevo material", expanded=False):
    with st.form("create_material_form"):
        col_a, col_b = st.columns(2, gap="medium")
        code        = col_a.text_input("Código *", placeholder="Ej: MAT-001")
        name        = col_b.text_input("Nombre *", placeholder="Ej: Cemento Portland")
        unit        = col_a.text_input("Unidad", placeholder="Ej: kg, m, unidad")
        description = col_b.text_input("Descripción", placeholder="Descripción breve")
        col_c, col_d = st.columns(2, gap="medium")
        f_price_soles = col_c.number_input(
            "Costo unitario S/.",
            min_value=0.0, value=None, step=0.50, format="%.2f",
            placeholder="Ej. 10.50",
            help="Precio en soles peruanos. Deja vacío si no aplica, pero debe haber al menos un precio (S/. o $).",
        )
        f_price_dolar = col_d.number_input(
            "Costo unitario $",
            min_value=0.0, value=None, step=0.10, format="%.2f",
            placeholder="Ej. 2.80",
            help="Precio en dólares americanos. Deja vacío si no aplica, pero debe haber al menos un precio (S/. o $).",
        )
        submit      = st.form_submit_button("Crear Material", use_container_width=True)

    if submit:
        if code and name:
            unit_clean = unit.strip()
            _ps = f_price_soles or 0.0
            _pd = f_price_dolar or 0.0
            if unit_clean.startswith("-") and unit_clean.lstrip("-").replace(".", "").isdigit():
                st.error("La unidad no puede ser un número negativo.")
            elif _ps < 0 or _pd < 0:
                st.error("Los costos no pueden ser negativos.")
            elif _ps <= 0 and _pd <= 0:
                st.error("Debes ingresar un costo mayor a 0 — al menos en S/. o $.")
            else:
                created, info = create_material(
                    db, code, name, unit_clean, description,
                    unit_price=_ps,
                    unit_price_dolares=_pd,
                )
                if created:
                    st.success("Material creado correctamente.")
                    st.rerun()
                else:
#                     st.error("Error al crear el material")
#                 time.sleep(2)
#                 st.rerun()  
#         else:
#             st.error("Código y nombre son obligatorios")
#             time.sleep(2)
#             st.rerun()

# materials = get_materials(db)
# # -------------------------
# # EDITAR MATERIAL
# # -------------------------
# st.subheader("✏️ Editar Material")

# with st.expander("⚙️Formulario de edición", expanded=True):
    
#     if materials:

#         select = st.selectbox(
#         "Selecciona un material",
#         [m.name for m in materials])
        
#             # Obtener el ID del material seleccionado
#         selected_id = next((m.id for m in materials if m.name == select), None)

#         selected = next((m for m in materials if m.id == selected_id), None)

#         if selected:
#             col1, col2, col3 = st.columns(3)

#             with col1:
#                 new_code = st.text_input("Código", value=selected.code)
#             with col2:
#                 new_name = st.text_input("Nombre", value=selected.name)
#             with col3:
#                 new_unit = st.text_input("Unidad (kg, m, unidad, etc.)", value=selected.unit)
#             col4 = st.columns(1)[0]
#             with col4:
#                 new_description = st.text_area("Descripción", value=selected.description, key="edit_desc")
#             submit = st.button("✅Actualizar", use_container_width=True)

#             if submit:
#                 if new_code and new_name:
#                     updated, info = update_material(
#                         db,
#                         selected.id,
#                         new_code,
#                         new_name,
#                         new_unit,
#                         new_description
#                     )

#                     if updated:
#                         st.success("Material actualizado correctamente")
#                         #st.session_state["refresh"] = True
#                         time.sleep(2)
#                         st.rerun()
#                     else:
#                         if info == 'code':
#                             st.error("El código ya está en uso")
#                         elif info == 'name':
#                             st.error("El nombre ya está en uso")
#                         else:
#                             st.error("Error al actualizar el material")
#                         #st.session_state["refresh"] = True
#                         time.sleep(2)
#                         st.rerun()
                        
#                 else:
#                     st.error("Código y nombre son obligatorios")
#                     #st.session_state["refresh"] = True
#                     time.sleep(2)
#                     st.rerun()
#     else:
#         st.info("No hay materiales registrados")
#         st.write("Agrega un nuevo material usando el formulario de arriba.")
        
    
# # -------------------------
# # LISTAR MATERIALES
# # -------------------------
# st.subheader("📋 Lista de Materiales")

# # Inicializar estado de paginación
# if "page" not in st.session_state:
#     st.session_state.page = 0
# if "filters_applied" not in st.session_state:
#     st.session_state.filters_applied = False

# # SECTION: FILTROS
# with st.expander("🔍 Filtros", expanded=True):
#     col1, col2,col3 = st.columns(3)
    
#     with col1:
#         code_filter = st.text_input("Filtrar por código", value="", key="m_code",
#                                     help="Escribe parte del código para filtrar. Deja vacío para no filtrar por código.")
    
#     with col2:
#         name_filter = st.text_input("Filtrar por nombre", value="", key="m_name",
#                                     help="Escribe parte del nombre para filtrar. Deja vacío para no filtrar por nombre.")
    
#     with col3:
#         unit_filter = st.text_input("Filtrar por unidad", value="", key="m_unit",
#                                     help="Escribe parte de la unidad para filtrar. Deja vacío para no filtrar por unidad.")

#     col_search, col_clear = st.columns([1, 1])

#     with col_search:
#         if st.button("🔎 Buscar", use_container_width=True):
#             st.session_state.page = 0
#             st.session_state.filters_applied = True
    
#     def clear_materials_filters():
#         st.session_state["m_code"] = ""
#         st.session_state["m_name"] = ""
#         st.session_state["m_unit"] = ""
#         st.session_state.page = 0
#         st.session_state.filters_applied = False

#     with col_clear:
#         st.button("🔄 Limpiar Filtros", use_container_width=True, on_click=clear_materials_filters)


# # SECTION: OBTENER DATOS CON FILTROS
# items_per_page = 10

# # Aplicar filtros
# filter_code_val = code_filter if code_filter else None
# filter_name_val = name_filter if name_filter else None
# filter_unit_val = unit_filter if unit_filter else None

# materials, total_count = get_materials_filtered(
#     db,
#     skip=st.session_state.page * items_per_page,  
#     limit=items_per_page,
#     code_filter=filter_code_val,
#     name_filter=filter_name_val,
#     unit_filter=filter_unit_val
# )

# # Mostrar información de paginación
# st.info(f"📊 Total de materiales: **{total_count}** | Mostrando: **{len(materials)}** | Página: **{st.session_state.page + 1}**")  

# # SECTION: MOSTRAR MATERIALES

# if materials:
#     for m in materials:
#         col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
#         with col1:
#             st.write(f"**Código:** {m.code}")
#         with col2:
#             st.write(f"**Nombre:** {m.name}")
#         with col3:
#             st.write(f"**Unidad:** {m.unit}")
#         # BOTÓN ELIMINAR
#         if col4.button(
#             "🗑️ Eliminar", 
#             key=f"del_{m.id}", 
#             type="primary", 
#             use_container_width=True,
#             help="Eliminar este material. Ten en cuenta que esta acción no se puede deshacer."
#         ):
            
#             delete_material(db, m.id)
#             st.rerun()
        
#         with st.expander(f"👁️ Ver Detalle - Material #{m.id}"):
#             st.write(f"**Descripción:** {m.description if m.description else 'Sin descripción'}")
#             st.divider()
        

        
# else:
#     st.warning("❌ No se encontraron materiales con los filtros aplicados." if st.session_state.filters_applied else "No hay materiales registrados.")


# # SECTION: PAGINACIÓN
# col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

# with col1:
#     if st.session_state.page > 0:
#         if st.button("⬅️ Anterior", use_container_width=True):
#             st.session_state.page -= 1
#             st.rerun()

# with col5:
#     if len(materials) == items_per_page and (st.session_state.page + 1) * items_per_page < total_count:
#         if st.button("Siguiente ➡️", use_container_width=True):
#             st.session_state.page += 1
#             st.rerun()

# with col3:
#     st.markdown(f"<div style='text-align: center; padding: 10px;'>Página **{st.session_state.page + 1}** de **{(total_count + items_per_page - 1) // items_per_page}**</div>", unsafe_allow_html=True)

                    msgs = {"code": "El código ya está en uso.", "name": "El nombre ya está en uso."}
                    st.error(msgs.get(info, "Error al crear el material."))
        else:
            st.error("Código y nombre son obligatorios.")

# ── Catálogo + Gestión ────────────────────────────────────────────────────────
st.markdown(f'<div class="sec-title">Catálogo de Materiales ({len(materials)})</div>', unsafe_allow_html=True)

if st.session_state.get("mat_op_msg"):
    st.success(st.session_state.pop("mat_op_msg"))

# Mapeo material_id -> proyectos donde se usa (almacenes principales del cliente)
_principal_wh_ids = {
    w.id for w in db.query(Warehouse).filter(
        Warehouse.owner_id == owner_id,
        Warehouse.type == "principal",
    ).all()
}
_active_bud_names = {b.name for b in get_budgets(db) if b.is_active}

_mat_proj_map: dict = {}
if _principal_wh_ids:
    _inv_rows = (
        db.query(Inventory)
        .filter(
            Inventory.warehouse_id.in_(_principal_wh_ids),
            Inventory.is_active == True,
            Inventory.budget_id.isnot(None),
        )
        .all()
    )
    for _inv in _inv_rows:
        _key = _inv.material_id
        _entry = _mat_proj_map.setdefault(_key, {})
        _name  = _inv.budget_name or "—"
        _slot  = _entry.setdefault(_name, {"stock": 0, "active": _name in _active_bud_names})
        _slot["stock"] += int(_inv.stock or 0)

_all_proj_in_inv = sorted({n for sub in _mat_proj_map.values() for n in sub.keys()}, key=str.lower)

if not materials:
    st.info("No hay materiales registrados. Crea el primero con el formulario de arriba.")
else:
    # ── Filtros del catálogo ──────────────────────────────────────────────────
    _f1, _f2, _f3 = st.columns([3, 3, 2], gap="small")
    with _f1:
        _mat_search = st.text_input(
            "Buscar material",
            placeholder="Filtrar por código, nombre, unidad o descripción...",
            key="mat_search_text",
            label_visibility="collapsed",
        )
    _proj_filter_opts = ["Todos los proyectos"] + _all_proj_in_inv + ["Sin proyecto asignado"]
    with _f2:
        _mat_proj_filter = st.selectbox(
            "Filtrar por proyecto",
            _proj_filter_opts,
            key="mat_proj_filter",
            label_visibility="collapsed",
        )
    with _f3:
        if st.button("Limpiar filtros", key="clear_mat_filters", use_container_width=True):
            st.session_state["mat_search_text"] = ""
            st.session_state["mat_proj_filter"] = "Todos los proyectos"
            st.session_state["mat_page"] = 0
            st.rerun()

    # ── Aplicar filtros ───────────────────────────────────────────────────────
    _filtered_materials = materials
    if _mat_search:
        _s = _mat_search.lower()
        _filtered_materials = [
            m for m in _filtered_materials
            if _s in (m.code or "").lower()
            or _s in (m.name or "").lower()
            or _s in (m.unit or "").lower()
            or _s in (m.description or "").lower()
        ]
    if _mat_proj_filter == "Sin proyecto asignado":
        _filtered_materials = [
            m for m in _filtered_materials if not _mat_proj_map.get(m.id)
        ]
    elif _mat_proj_filter != "Todos los proyectos":
        _filtered_materials = [
            m for m in _filtered_materials
            if _mat_proj_filter in (_mat_proj_map.get(m.id) or {})
        ]

    if not _filtered_materials:
        st.info("No se encontraron materiales con los filtros aplicados.")
        db.close()
        st.stop()

    # ── Paginación (20 tarjetas por página) ───────────────────────────────────
    _MAT_PER_PAGE = 20
    _total_mat    = len(_filtered_materials)
    _total_pages  = max(1, (_total_mat + _MAT_PER_PAGE - 1) // _MAT_PER_PAGE)
    _page         = int(st.session_state.get("mat_page", 0))
    _page         = min(_page, _total_pages - 1)
    _page_items   = _filtered_materials[_page * _MAT_PER_PAGE:(_page + 1) * _MAT_PER_PAGE]

    st.caption(
        f"Mostrando {len(_page_items)} de {_total_mat} materiales"
        + (f" (página {_page + 1} de {_total_pages})" if _total_pages > 1 else "")
    )

    for m in _page_items:
        col_card, col_edit, col_del = st.columns([9, 1, 1], gap="small", vertical_alignment="center")

        with col_card:
            price_s = m.unit_price or 0.0
            price_d = m.unit_price_dolares or 0.0
            unit_val = (m.unit or "").strip() or "—"
            desc_val = (m.description or "").strip() or "Sin descripción"
            unit_cls = "" if (m.unit or "").strip() else "empty"
            desc_cls = "" if (m.description or "").strip() else "empty"
            price_s_html = f"S/ {price_s:,.2f}" if price_s > 0 else "—"
            price_d_html = f"$ {price_d:,.2f}" if price_d > 0 else "—"
            price_s_cls  = "price-s" if price_s > 0 else "empty"
            price_d_cls  = "price-d" if price_d > 0 else "empty"

            _proj_uses = _mat_proj_map.get(m.id) or {}
            if _proj_uses:
                _chips_html = "".join(
                    f'<span class="mat-proj-chip{"" if data["active"] else " inactive"}" '
                    f'title="Proyecto {"activo" if data["active"] else "desactivado"}">'
                    f'📂 {pname} '
                    f'<span class="mat-proj-qty">{data["stock"]}</span>'
                    f'</span>'
                    for pname, data in sorted(_proj_uses.items(), key=lambda kv: kv[0].lower())
                )
                proj_row_html = (
                    f'<div class="mat-proj-row">'
                    f'<span class="mat-proj-lbl">En proyectos:</span>'
                    f'{_chips_html}'
                    f'</div>'
                )
            else:
                proj_row_html = (
                    '<div class="mat-proj-row">'
                    '<span class="mat-proj-lbl">En proyectos:</span>'
                    '<span class="mat-noproj-chip">Sin uso registrado</span>'
                    '</div>'
                )

            card_html = (
                '<div class="mat-info-card">'
                  '<div class="mat-card-header">'
                    f'<span class="mat-id-chip">{m.code}</span>'
                    f'<span class="mat-card-name">{m.name}</span>'
                  '</div>'
                  '<div class="mat-card-grid">'
                    f'<div class="mat-field"><span class="mat-field-lbl">Unidad</span>'
                    f'<span class="mat-field-val {unit_cls}">{unit_val}</span></div>'
                    f'<div class="mat-field"><span class="mat-field-lbl">Descripción</span>'
                    f'<span class="mat-field-val {desc_cls}" title="{desc_val}">{desc_val}</span></div>'
                    f'<div class="mat-field"><span class="mat-field-lbl">Precio S/.</span>'
                    f'<span class="mat-field-val {price_s_cls}">{price_s_html}</span></div>'
                    f'<div class="mat-field"><span class="mat-field-lbl">Precio $</span>'
                    f'<span class="mat-field-val {price_d_cls}">{price_d_html}</span></div>'
                  '</div>'
                  f'{proj_row_html}'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

        with col_edit:
            editing = st.session_state.get("edit_mat_id") == m.id
            if st.button("✏", key=f"edit_mat_btn_{m.id}", use_container_width=True,
                         help="Editar material", type="primary" if editing else "secondary"):
                if editing:
                    st.session_state.pop("edit_mat_id", None)
                else:
                    st.session_state["edit_mat_id"] = m.id
                    st.session_state.pop("confirm_del_mat", None)
                st.rerun()

        with col_del:
            if st.button("✕", key=f"del_mat_btn_{m.id}", use_container_width=True,
                         help="Eliminar material"):
                st.session_state["confirm_del_mat"] = m.id
                st.session_state.pop("edit_mat_id", None)

        # ── Formulario de edición inline ──────────────────────────────────────
        if st.session_state.get("edit_mat_id") == m.id:
            with st.container():
                st.markdown(
                    "<div style='border-left:3px solid rgba(37,99,235,.40);padding-left:.8rem;"
                    "margin:.2rem 0 .5rem .1rem'>",
                    unsafe_allow_html=True)
                col_a, col_b = st.columns(2, gap="medium")
                new_code = col_a.text_input("Código *",      value=m.code,              key=f"ed_code_{m.id}")
                new_name = col_b.text_input("Nombre *",      value=m.name,              key=f"ed_name_{m.id}")
                new_unit = col_a.text_input("Unidad",        value=m.unit or "",        key=f"ed_unit_{m.id}")
                new_desc = col_b.text_input("Descripción",   value=m.description or "", key=f"ed_desc_{m.id}")
                col_c, col_d = st.columns(2, gap="medium")
                new_price_s = col_c.number_input(
                    "Costo S/.", min_value=0.0, step=0.50, format="%.2f",
                    value=float(m.unit_price or 0.0), key=f"ed_price_s_{m.id}",
                )
                new_price_d = col_d.number_input(
                    "Costo $", min_value=0.0, step=0.10, format="%.2f",
                    value=float(m.unit_price_dolares or 0.0), key=f"ed_price_d_{m.id}",
                )
                st.markdown("</div>", unsafe_allow_html=True)

                s_col, c_col = st.columns(2, gap="small")
                if s_col.button("Guardar cambios", type="primary", key=f"save_mat_{m.id}", use_container_width=True):
                    if new_code.strip() and new_name.strip():
                        unit_clean = new_unit.strip()
                        updated, info = update_material(
                            db, m.id, new_code.strip(), new_name.strip(),
                            unit_clean, new_desc.strip(),
                            unit_price=new_price_s,
                            unit_price_dolares=new_price_d,
                        )
                        if updated:
                            st.session_state.pop("edit_mat_id", None)
                            st.session_state["mat_op_msg"] = "Material actualizado correctamente."
                            st.rerun()
                        else:
                            msgs = {"code": "El código ya está en uso.", "name": "El nombre ya está en uso."}
                            st.error(msgs.get(info, "Error al actualizar."))
                    else:
                        st.error("Código y nombre son obligatorios.")
                if c_col.button("Cancelar edición", key=f"cancel_edit_{m.id}", use_container_width=True):
                    st.session_state.pop("edit_mat_id", None)
                    st.rerun()

        # ── Confirmación de eliminación ───────────────────────────────────────
        if st.session_state.get("confirm_del_mat") == m.id:
            c_msg, c_yes, c_no = st.columns([5, 1, 1], gap="small")
            c_msg.error(f"¿Eliminar permanentemente **{m.name}** ({m.code})? No se puede deshacer.")
            if c_yes.button("Sí, eliminar", key=f"yes_del_mat_{m.id}", type="primary", use_container_width=True):
                delete_material_code(db, m.code, user_id=owner_id)
                st.session_state.pop("confirm_del_mat", None)
                st.session_state["mat_op_msg"] = f"Material **{m.name}** eliminado correctamente."
                st.rerun()
            if c_no.button("Cancelar", key=f"no_del_mat_{m.id}", use_container_width=True):
                st.session_state.pop("confirm_del_mat", None)
                st.rerun()

    # ── Controles de paginación ───────────────────────────────────────────────
    if _total_pages > 1:
        _pp_prev, _pp_info, _pp_next = st.columns([1, 3, 1])
        _pp_info.markdown(
            f"<div class='mat-pag-info'>Página {_page + 1} de {_total_pages} "
            f"— {_total_mat} materiales</div>",
            unsafe_allow_html=True,
        )
        if _pp_prev.button("← Anterior", key="mat_prev",
                           disabled=(_page == 0), use_container_width=True):
            st.session_state["mat_page"] = _page - 1
            st.rerun()
        if _pp_next.button("Siguiente →", key="mat_next",
                           disabled=(_page == _total_pages - 1), use_container_width=True):
            st.session_state["mat_page"] = _page + 1
            st.rerun()

db.close()
