# -*- coding: utf-8 -*-
import re
import streamlit as st
from datetime import datetime


def _password_strength(pwd: str) -> int:
    if not pwd: return 0
    if len(pwd) >= 10: return 100
    score = 0
    if len(pwd) >= 8:                     score += 25
    if re.search(r'[a-z]', pwd):          score += 20
    if re.search(r'[A-Z]', pwd):          score += 20
    if re.search(r'\d', pwd):             score += 20
    if re.search(r'[^a-zA-Z\d\s]', pwd): score += 15
    return min(score, 100)
from database import SessionLocal
from services.auth_service import (
    get_all_clients,
    set_user_active,
    delete_client,
    register_user,
    update_client,
)
from services.session_service import delete_user_sessions
from utils.auth import require_superadmin
from utils.navbar import render_navbar, render_sidebar_menu
from models.movement import Movement
from models.warehouse import Warehouse
from models.material import Material

st.set_page_config(
    page_title="Panel Admin — Sistema MRP",
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
.admin-hero {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: .5rem;
    padding: 1rem 1.5rem 1.2rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #1a0a2e 0%, #3b1a6b 55%, #7c3aed 100%);
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(124,58,237,.28);
}
.admin-hero-left  { display: flex; align-items: center; gap: 1rem; }
.admin-hero-icon  {
    width: 60px; height: 60px; border-radius: 16px;
    background: rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 1.8rem;
}
.admin-hero h1    { font-size: 1.55rem; font-weight: 900; color: #fff; margin: 0; }
.admin-hero p     { font-size: .82rem; color: rgba(255,255,255,.70); margin: 2px 0 0; }
.admin-badge {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,.25);
    border-radius: 30px; padding: .35rem 1rem;
    font-size: .78rem; font-weight: 700; color: #fde68a;
    white-space: nowrap;
}

/* ── KPI Cards ── */
.akpi { border-radius: 16px; padding: 1.2rem 1.4rem; color: #fff; position: relative; overflow: hidden; }
.akpi-label { font-size: .70rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; opacity: .80; margin-bottom: .3rem; }
.akpi-val   { font-size: 2.4rem; font-weight: 900; line-height: 1; }
.akpi-sub   { font-size: .73rem; opacity: .65; margin-top: .2rem; }
.ak-violet  { background: linear-gradient(135deg, #4c1d95, #7c3aed); }
.ak-green   { background: linear-gradient(135deg, #064e3b, #059669); }
.ak-red     { background: linear-gradient(135deg, #7f1d1d, #dc2626); }

/* ── Section title ── */
.sec-title {
    font-size: 1rem; font-weight: 800;
    display: flex; align-items: center; gap: .55rem;
    padding-left: .8rem;
    border-left: 4px solid #7c3aed;
    margin: 2rem 0 .9rem;
}

/* ── Password requirements pill ── */
.pw-reqs {
    display: flex; flex-wrap: wrap; gap: .35rem;
    margin-top: .55rem; margin-bottom: .15rem;
    padding: .55rem .72rem;
    background: rgba(124,58,237,.04);
    border: 1px solid rgba(124,58,237,.12);
    border-radius: 10px;
}
.pw-req-chip {
    font-size: .68rem; font-weight: 600;
    padding: .22rem .58rem; border-radius: 20px;
    background: rgba(124,58,237,.10);
    border: 1px solid rgba(124,58,237,.22);
    color: #a78bfa;
    white-space: nowrap;
}

/* ── User cards ── */
.user-card {
    display: flex; align-items: center; gap: 1rem;
    padding: .75rem 1rem;
    border-radius: 12px;
    border: 1px solid rgba(124,58,237,.15);
    margin-bottom: .5rem;
    background: rgba(124,58,237,.04);
    transition: background .15s;
}
.user-card:hover { background: rgba(124,58,237,.09); }
.user-avatar {
    width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg, #7c3aed, #3b82f6);
    display: flex; align-items: center; justify-content: center;
    font-size: .9rem; font-weight: 800; color: #fff;
}
.user-info       { flex: 1; min-width: 0; }
.user-name       { font-size: .88rem; font-weight: 700; }
.user-email      { font-size: .74rem; opacity: .55; }
.badge-active    { display:inline-block; padding:.15rem .55rem; border-radius:20px;
                   font-size:.68rem; font-weight:700;
                   background:rgba(5,150,105,.18); color:#34d399; }
.badge-inactive  { display:inline-block; padding:.15rem .55rem; border-radius:20px;
                   font-size:.68rem; font-weight:700;
                   background:rgba(220,38,38,.15); color:#f87171; }

/* ── Botones secondary — estilo ámbar (Visualizar) ── */
[data-testid="stBaseButton-secondary"] {
    background: rgba(245,158,11,.10) !important;
    color: #fbbf24 !important;
    border: 1px solid rgba(245,158,11,.28) !important;
    border-radius: 10px !important;
    font-size: .76rem !important; font-weight: 600 !important;
    transition: background .15s, box-shadow .15s !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(245,158,11,.20) !important;
    box-shadow: 0 2px 10px rgba(245,158,11,.22) !important;
    color: #fde68a !important;
}

/* ── Historial de movimientos ── */
.moves-wrap {
    border: 1px solid rgba(99,102,241,.18);
    border-radius: 14px;
    background: rgba(99,102,241,.04);
    padding: .65rem .9rem .5rem;
    margin: .15rem 0 .3rem;
}
.moves-title {
    font-size: .76rem; font-weight: 700; color: #a5b4fc;
    margin-bottom: .55rem; display: flex; align-items: center; gap: .4rem;
}
.move-card {
    display: flex; align-items: center; gap: .65rem;
    padding: .62rem .95rem; border-radius: 12px;
    border: 1px solid rgba(99,102,241,.18);
    background: linear-gradient(135deg, rgba(99,102,241,.07), rgba(99,102,241,.02));
    margin-bottom: .42rem; font-size: .74rem;
    transition: background .12s, border-color .12s;
    flex-wrap: wrap;
}
.move-card:hover {
    background: linear-gradient(135deg, rgba(99,102,241,.12), rgba(99,102,241,.05));
    border-color: rgba(99,102,241,.30);
}
.move-badge-in  { padding:.14rem .48rem; border-radius:20px; font-size:.63rem; font-weight:800;
                  background:rgba(34,197,94,.16); color:#4ade80; border:1px solid rgba(34,197,94,.25);
                  white-space:nowrap; flex-shrink:0; }
.move-badge-out { padding:.14rem .48rem; border-radius:20px; font-size:.63rem; font-weight:800;
                  background:rgba(239,68,68,.16); color:#f87171; border:1px solid rgba(239,68,68,.25);
                  white-space:nowrap; flex-shrink:0; }
.move-mat  { flex:1; color:#e2e8f0; font-weight:700; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.move-qty  { color:#a5b4fc; font-weight:700; white-space:nowrap; flex-shrink:0; }
.move-wh   { color:rgba(148,163,184,.58); font-size:.69rem; white-space:nowrap; flex-shrink:0; }
.move-ts   { color:rgba(148,163,184,.40); font-size:.65rem; white-space:nowrap; flex-shrink:0; }
.move-ref  { padding:.06rem .38rem; border-radius:9px; font-size:.60rem; font-weight:700;
             background:rgba(148,163,184,.10); color:rgba(148,163,184,.50); white-space:nowrap; flex-shrink:0; }
.mv-pag-info {
    text-align: center; font-size: .72rem; color: rgba(148,163,184,.50);
    font-weight: 600; padding: .25rem 0;
}

/* ── Formulario de edición ── */
.edit-form-box {
    border: 1px solid rgba(124,58,237,.25);
    border-radius: 12px;
    padding: .75rem 1rem .5rem;
    background: rgba(124,58,237,.05);
    margin: .2rem 0 .7rem;
}
.edit-form-title {
    font-size: .82rem; font-weight: 700;
    color: #c4b5fd; margin-bottom: .5rem;
}

/* ── Search box ── */
.search-hint {
    font-size: .73rem;
    color: color-mix(in srgb, var(--text-color,#0f172a) 45%, transparent);
    margin-bottom: .5rem;
}

[data-testid="stAlert"] { border-radius: 10px !important; }

/* ── Form labels ── */
label[data-testid="stWidgetLabel"] p {
    font-size: .80rem !important;
    font-weight: 600 !important;
}

/* ── Submit button ── */
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 14px rgba(124,58,237,.35) !important;
    transition: background .2s, transform .15s, box-shadow .2s !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,.45) !important;
}

/* ── Expander "Crear cliente" ── */
[data-testid="stExpander"] {
    border-radius: 16px !important;
    border: 1px solid rgba(124,58,237,.20) !important;
    background: rgba(10,6,22,.40) !important;
    overflow: hidden !important;
    transition: border-color .2s, box-shadow .2s !important;
    margin-bottom: .4rem !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(124,58,237,.36) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,.07) !important;
}
details[data-testid="stExpander"] > summary {
    padding: .88rem 1.2rem !important;
    font-size: .88rem !important;
    font-weight: 700 !important;
    color: #c4b5fd !important;
}
details[data-testid="stExpander"][open] > summary {
    border-bottom: 1px solid rgba(124,58,237,.15) !important;
}

/* ── Sección label dentro del expander ── */
.form-sec {
    font-size: .63rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .14em;
    color: rgba(196,181,253,.55);
    display: flex; align-items: center; gap: .5rem;
    margin: .7rem 0 .6rem;
}
.form-sec::after {
    content: ""; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(124,58,237,.30), transparent);
}

/* ── Barra de fortaleza ── */
.strength-wrap { margin: .3rem 0 .6rem; }
.strength-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: .26rem;
}
.strength-section-label {
    font-size: .60rem; font-weight: 700; letter-spacing: .10em;
    text-transform: uppercase; color: rgba(196,181,253,.40);
}
.strength-track {
    background: rgba(255,255,255,.06);
    border-radius: 100px; height: 3.5px; overflow: hidden;
}
.strength-fill {
    height: 100%; border-radius: 100px;
    transition: width .4s cubic-bezier(.4,0,.2,1), background .4s ease;
}

/* ── Botón primario (violet, aplica a todos los botones type=primary) ── */
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 14px rgba(124,58,237,.35) !important;
    transition: background .2s, transform .15s, box-shadow .2s !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,.45) !important;
}
</style>
""", unsafe_allow_html=True)

render_navbar()
with st.sidebar:
    render_sidebar_menu()

# ── Hero ──────────────────────────────────────────────────────────────────────
now  = datetime.now()
user = st.session_state.get("username", "Superadmin")

st.markdown(f"""
<div class="admin-hero">
  <div class="admin-hero-left">
    <div class="admin-hero-icon">&#128737;</div>
    <div>
      <h1>Panel de Administración</h1>
      <p>Gestión de usuarios clientes &nbsp;·&nbsp; {now.strftime("%A %d de %B, %Y")}</p>
    </div>
  </div>
  <div class="admin-badge">&#9733; Superadmin: {user}</div>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()
clientes = get_all_clients(db)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total     = len(clientes)
activos   = sum(1 for c in clientes if c.is_active)
inactivos = total - activos

k1, k2, k3 = st.columns(3, gap="medium")
k1.markdown(f"""<div class="akpi ak-violet">
  <div class="akpi-label">Total Clientes</div>
  <div class="akpi-val">{total}</div>
  <div class="akpi-sub">Cuentas registradas</div>
</div>""", unsafe_allow_html=True)

k2.markdown(f"""<div class="akpi ak-green">
  <div class="akpi-label">Activos</div>
  <div class="akpi-val">{activos}</div>
  <div class="akpi-sub">Con acceso al sistema</div>
</div>""", unsafe_allow_html=True)

k3.markdown(f"""<div class="akpi ak-red">
  <div class="akpi-label">Deshabilitados</div>
  <div class="akpi-val">{inactivos}</div>
  <div class="akpi-sub">Sin acceso al sistema</div>
</div>""", unsafe_allow_html=True)

# ── Instrucciones ─────────────────────────────────────────────────────────────
_, _col_help_admin = st.columns([7, 1.5])
with _col_help_admin.popover("📋 Instrucciones", use_container_width=True):
    st.markdown("#### Guía del Panel de Administración")
    st.markdown("""
**Crear cliente** — Registra una nueva cuenta de tipo cliente con usuario, correo y contraseña. Los requisitos de contraseña se verifican en tiempo real.

**Deshabilitar / Habilitar** — Controla el acceso de un cliente al sistema sin eliminar su cuenta ni sus datos.

**Editar** — Modifica el usuario, correo o contraseña de un cliente existente. Si se cambia el usuario, sus sesiones activas se cierran automáticamente.

**Visualizar** — Accede al sistema como si fuera ese cliente (impersonación). Verás sus datos y podrás operar en su nombre. Aparece un banner naranja de aviso.

**Movimientos** — Consulta el historial de entradas y salidas de inventario del cliente (últimos 50 registros).

**Eliminar** — Elimina permanentemente la cuenta del cliente y todos sus datos asociados. Esta acción no se puede deshacer.

---

**Seguridad de contraseña:**
- Mínimo 8 caracteres
- Recomendado: mayúsculas, minúsculas, números y símbolos
""")

# ── Crear cliente ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">&#43; Crear nuevo cliente</div>', unsafe_allow_html=True)

with st.expander("Registrar nuevo cliente", expanded=False):
    st.markdown('<div class="form-sec">Datos de acceso</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        st.text_input("Usuario",            placeholder="3–20 caracteres, letras y números", key="ac_user")
        st.text_input("Correo electrónico", placeholder="ejemplo@empresa.com",               key="ac_email")
    with col_b:
        st.text_input("Contraseña",         type="password", placeholder="Mín. 8 caracteres",      key="ac_pwd")
        st.text_input("Confirmar contraseña", type="password", placeholder="Repite la contraseña", key="ac_pwd2")

    _pwd = st.session_state.get("ac_pwd", "")
    _str = _password_strength(_pwd)
    if   _str == 0:  _bar_c, _bar_l, _lbl_c = "transparent", "",           "#334155"
    elif _str < 40:  _bar_c, _bar_l, _lbl_c = "#ef4444",     "Insegura",   "#ef4444"
    elif _str < 70:  _bar_c, _bar_l, _lbl_c = "#f59e0b",     "Moderada",   "#d97706"
    else:            _bar_c = "#22c55e"; _bar_l = "Muy segura" if _str == 100 else "Segura"; _lbl_c = "#16a34a"

    st.markdown(f"""
    <div class="strength-wrap">
      <div class="strength-header">
        <span class="strength-section-label">Seguridad de la contraseña</span>
        <span style="font-size:.68rem;font-weight:700;color:{_lbl_c};transition:color .35s;">{_bar_l}</span>
      </div>
      <div class="strength-track">
        <div class="strength-fill" style="width:{_str}%;background:{_bar_c};"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Crear cliente", use_container_width=True, type="primary", key="btn_create_client"):
        u  = st.session_state.get("ac_user",  "").strip()
        e  = st.session_state.get("ac_email", "").strip()
        p1 = st.session_state.get("ac_pwd",   "")
        p2 = st.session_state.get("ac_pwd2",  "")
        if not u or not e or not p1 or not p2:
            st.error("Completa todos los campos.")
        elif p1 != p2:
            st.error("Las contraseñas no coinciden.")
        else:
            with st.spinner("Creando cliente..."):
                ok, msg = register_user(db, u, e, p1, p2, role="cliente")
            if ok:
                st.success(f"Cliente **{u}** creado correctamente.")
                for k in ["ac_user", "ac_email", "ac_pwd", "ac_pwd2"]:
                    st.session_state.pop(k, None)
                clientes = get_all_clients(db)
                st.rerun()
            else:
                st.error(msg)

# ── Lista de clientes ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">&#128101; Clientes registrados</div>', unsafe_allow_html=True)

if not clientes:
    st.info("No hay clientes registrados aún. Crea el primero con el formulario de arriba.")
else:
    # Search filter
    search_query = st.text_input(
        "Buscar cliente",
        placeholder="Filtrar por nombre o correo...",
        label_visibility="collapsed",
    )
    if search_query:
        q = search_query.lower()
        clientes_filtrados = [
            c for c in clientes
            if q in c.username.lower() or (c.email and q in c.email.lower())
        ]
    else:
        clientes_filtrados = clientes

    if not clientes_filtrados:
        st.warning(f"No se encontraron clientes con «{search_query}».")
    else:
        for cliente in clientes_filtrados:
            init  = cliente.username[0].upper()
            badge = '<span class="badge-active">Activo</span>' if cliente.is_active \
                    else '<span class="badge-inactive">Deshabilitado</span>'
            fecha = cliente.created_at.strftime("%d/%m/%Y") if cliente.created_at else "—"

            col_info, col_estado, col_edit, col_view, col_moves, col_actions = st.columns([4, 2, 2, 2, 2, 2])

            with col_info:
                st.markdown(f"""
                <div class="user-card">
                  <div class="user-avatar">{init}</div>
                  <div class="user-info">
                    <div class="user-name">{cliente.username} &nbsp; {badge}</div>
                    <div class="user-email">{cliente.email} &nbsp;·&nbsp; Creado: {fecha}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

            with col_estado:
                st.write("")
                if cliente.is_active:
                    if st.button("Deshabilitar", key=f"disable_{cliente.id}", use_container_width=True, type="primary"):
                        delete_user_sessions(db, cliente.id)
                        ok, msg = set_user_active(db, cliente.id, False)
                        st.success(msg) if ok else st.error(msg)
                        st.rerun()
                else:
                    if st.button("Habilitar", key=f"enable_{cliente.id}", use_container_width=True, type="primary"):
                        ok, msg = set_user_active(db, cliente.id, True)
                        st.success(msg) if ok else st.error(msg)
                        st.rerun()

            with col_edit:
                st.write("")
                is_editing = st.session_state.get(f"show_edit_{cliente.id}", False)
                edit_label = "Cerrar ✕" if is_editing else "Editar"
                if st.button(edit_label, key=f"edit_btn_{cliente.id}", use_container_width=True, type="primary"):
                    st.session_state[f"show_edit_{cliente.id}"] = not is_editing
                    st.rerun()

            with col_view:
                st.write("")
                if st.button("Visualizar", key=f"view_{cliente.id}", use_container_width=True):
                    st.session_state["impersonating"]          = True
                    st.session_state["impersonating_user_id"]  = cliente.id
                    st.session_state["impersonating_username"] = cliente.username
                    st.switch_page("pages/dashboard.py")

            with col_moves:
                st.write("")
                is_moves_open = st.session_state.get(f"show_moves_{cliente.id}", False)
                moves_label   = "Cerrar ✕" if is_moves_open else "Movimientos"
                if st.button(moves_label, key=f"moves_btn_{cliente.id}", use_container_width=True):
                    new_state = not is_moves_open
                    st.session_state[f"show_moves_{cliente.id}"] = new_state
                    if new_state:
                        st.session_state[f"moves_page_{cliente.id}"] = 0
                    st.rerun()

            with col_actions:
                st.write("")
                if st.button("Eliminar", key=f"delete_{cliente.id}", use_container_width=True, type="primary"):
                    st.session_state[f"confirm_delete_{cliente.id}"] = True

                if st.session_state.get(f"confirm_delete_{cliente.id}"):
                    st.warning(f"¿Eliminar **{cliente.username}** permanentemente?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Sí, eliminar", key=f"yes_{cliente.id}", use_container_width=True, type="primary"):
                            delete_user_sessions(db, cliente.id)
                            ok, msg = delete_client(db, cliente.id)
                            st.success(msg) if ok else st.error(msg)
                            st.session_state.pop(f"confirm_delete_{cliente.id}", None)
                            st.rerun()
                    with col_no:
                        if st.button("Cancelar", key=f"no_{cliente.id}", use_container_width=True, type="primary"):
                            st.session_state.pop(f"confirm_delete_{cliente.id}", None)
                            st.rerun()

            # ── Historial de movimientos (paginado) ───────────────────────────
            if st.session_state.get(f"show_moves_{cliente.id}"):
                _MV_PER_PAGE  = 10
                _mv_page      = int(st.session_state.get(f"moves_page_{cliente.id}", 0))

                _total_mvs = (
                    db.query(Movement)
                    .join(Warehouse, Movement.warehouse_id == Warehouse.id)
                    .filter(Warehouse.owner_id == cliente.id)
                    .count()
                )
                _mv_total_pages = max(1, (_total_mvs + _MV_PER_PAGE - 1) // _MV_PER_PAGE)
                _mv_page        = min(_mv_page, _mv_total_pages - 1)

                user_movements = (
                    db.query(Movement)
                    .join(Warehouse, Movement.warehouse_id == Warehouse.id)
                    .filter(Warehouse.owner_id == cliente.id)
                    .order_by(Movement.timestamp.desc())
                    .offset(_mv_page * _MV_PER_PAGE)
                    .limit(_MV_PER_PAGE)
                    .all()
                )
                mat_ids  = {m.material_id for m in user_movements if m.material_id}
                mat_map  = {
                    mat.id: mat.name
                    for mat in db.query(Material).filter(Material.id.in_(mat_ids)).all()
                } if mat_ids else {}
                wh_ids   = {m.warehouse_id for m in user_movements if m.warehouse_id}
                wh_map   = {
                    wh.id: wh.name
                    for wh in db.query(Warehouse).filter(Warehouse.id.in_(wh_ids)).all()
                } if wh_ids else {}

                _REF_LABELS = {
                    "manual":             "Ingreso manual",
                    "dispatch":           "Despacho",
                    "receipt":            "Recepción",
                    "material_eliminado": "Material eliminado",
                }

                if _total_mvs == 0:
                    rows_html = '<div style="font-size:.78rem;color:rgba(148,163,184,.55);padding:.4rem 0;">Sin movimientos registrados.</div>'
                else:
                    rows = []
                    for mv in user_movements:
                        badge = '<span class="move-badge-in">ENTRADA</span>' \
                                if mv.movement_type == "IN" else \
                                '<span class="move-badge-out">SALIDA</span>'
                        if mv.material_id is None:
                            mat_name = "Material eliminado"
                        else:
                            mat_name = mat_map.get(mv.material_id, "Material eliminado")
                        wh_name  = wh_map.get(mv.warehouse_id, f"Almacén #{mv.warehouse_id}")
                        qty_abs  = abs(mv.qty_change) if mv.qty_change is not None else 0
                        qty_sign = f"+{qty_abs}" if mv.movement_type == "IN" else f"-{qty_abs}"
                        ts_str   = mv.timestamp.strftime("%d/%m/%Y %H:%M") if mv.timestamp else "—"
                        if mv.reference_type == "dispatch" and mv.reference_id:
                            ref_lbl = f"Despacho #{mv.reference_id}"
                        elif mv.reference_type == "receipt" and mv.reference_id:
                            ref_lbl = f"Recepción #{mv.reference_id}"
                        else:
                            ref_lbl = _REF_LABELS.get(mv.reference_type or "", "")
                        ref_html = f'<span class="move-ref">{ref_lbl}</span>' if ref_lbl else ""
                        rows.append(
                            f'<div class="move-card">{badge}'
                            f'<span class="move-mat">{mat_name}</span>'
                            f'<span class="move-qty">{qty_sign} u.</span>'
                            f'<span class="move-wh">· {wh_name}</span>'
                            f'{ref_html}'
                            f'<span class="move-ts">{ts_str}</span>'
                            f'</div>'
                        )
                    rows_html = "".join(rows)

                st.markdown(
                    f'<div class="moves-wrap">'
                    f'<div class="moves-title">&#128200; Historial de movimientos — {cliente.username}</div>'
                    f'{rows_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if _mv_total_pages > 1:
                    _mv_prev_col, _mv_info_col, _mv_next_col = st.columns([1, 3, 1])
                    _mv_info_col.markdown(
                        f"<div class='mv-pag-info'>"
                        f"Página {_mv_page + 1} de {_mv_total_pages}"
                        f" &nbsp;·&nbsp; {_total_mvs} movimientos</div>",
                        unsafe_allow_html=True,
                    )
                    if _mv_prev_col.button(
                        "← Ant.", key=f"mv_prev_{cliente.id}",
                        disabled=(_mv_page == 0), use_container_width=True
                    ):
                        st.session_state[f"moves_page_{cliente.id}"] = _mv_page - 1
                        st.rerun()
                    if _mv_next_col.button(
                        "Sig. →", key=f"mv_next_{cliente.id}",
                        disabled=(_mv_page == _mv_total_pages - 1), use_container_width=True
                    ):
                        st.session_state[f"moves_page_{cliente.id}"] = _mv_page + 1
                        st.rerun()

            # ── Formulario de edición de credenciales ─────────────────────────
            if st.session_state.get(f"show_edit_{cliente.id}"):
                st.markdown(f'<div class="edit-form-box"><div class="edit-form-title">&#9998; Editar credenciales de <strong>{cliente.username}</strong></div></div>', unsafe_allow_html=True)
                with st.form(key=f"edit_form_{cliente.id}"):
                    fe1, fe2 = st.columns(2, gap="medium")
                    with fe1:
                        eu  = st.text_input("Usuario",            value=cliente.username)
                        ee  = st.text_input("Correo electrónico", value=cliente.email or "")
                    with fe2:
                        ep  = st.text_input("Nueva contraseña",    type="password", placeholder="Dejar vacío para no cambiar")
                        ep2 = st.text_input("Confirmar contraseña", type="password", placeholder="Repite la nueva contraseña")
                    fs1, fs2 = st.columns(2, gap="medium")
                    with fs1:
                        save = st.form_submit_button("Guardar cambios", use_container_width=True, type="primary")
                    with fs2:
                        cancel = st.form_submit_button("Cancelar", use_container_width=True)

                    if save:
                        if ep and ep != ep2:
                            st.error("Las contraseñas no coinciden.")
                        else:
                            old_username = cliente.username
                            ok, msg = update_client(
                                db, cliente.id,
                                new_username=eu.strip() or None,
                                new_email=ee.strip() or None,
                                new_password=ep or None,
                            )
                            if ok:
                                if eu.strip() != old_username:
                                    delete_user_sessions(db, cliente.id)
                                st.success(msg)
                                st.session_state.pop(f"show_edit_{cliente.id}", None)
                                st.rerun()
                            else:
                                st.error(msg)
                    if cancel:
                        st.session_state.pop(f"show_edit_{cliente.id}", None)
                        st.rerun()

db.close()
