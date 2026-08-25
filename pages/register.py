# -*- coding: utf-8 -*-
import re
import streamlit as st
from database import SessionLocal
from services.auth_service import register_user
from utils.session_manager import init_session

st.set_page_config(
    page_title="Crear cuenta — Sistema MRP Polyline",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Redirigir si ya hay sesión activa ─────────────────────────────────────────
_db_early = SessionLocal()
for _k, _v in [("logged_in", False), ("user_id", None), ("username", None), ("session_token", None)]:
    st.session_state.setdefault(_k, _v)
if init_session():
    _db_early.close()
    _dest = "pages/admin.py" if st.session_state.get("role") == "superadmin" else "pages/dashboard.py"
    st.switch_page(_dest)
    st.stop()
_db_early.close()

def _password_strength(pwd: str) -> int:
    if not pwd:
        return 0
    if len(pwd) >= 10:
        return 100
    score = 0
    if len(pwd) >= 8:                     score += 25
    if re.search(r'[a-z]', pwd):          score += 20
    if re.search(r'[A-Z]', pwd):          score += 20
    if re.search(r'\d',    pwd):          score += 20
    if re.search(r'[^a-zA-Z\d\s]', pwd): score += 15
    return min(score, 100)

st.markdown("""
<style>
/* ── Overlay de transición — cubre el flash del sidebar al entrar o al re-renderizar ── */
@keyframes _mrp_overlay_out {
    0%   { opacity: 1; }
    100% { opacity: 0; visibility: hidden; pointer-events: none; }
}
#_mrp_pg_cover {
    position: fixed !important; inset: 0 !important;
    background: #040b16;
    z-index: 999999 !important;
    pointer-events: none !important;
    animation: _mrp_overlay_out 0.08s ease-out 0.01s forwards !important;
}

/* ── Reset total + sidebar forzado completamente fuera del layout ── */
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
section[data-testid="stSidebar"],[data-testid="stSidebarNav"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    position: fixed !important;
    left: -9999px !important;
    pointer-events: none !important;
}
[data-testid="stMain"] { padding-top: 0 !important; }
html { scrollbar-width: none !important; }
::-webkit-scrollbar { display: none !important; }
h1 a,h2 a,h3 a,.anchor-link { display: none !important; }
[data-testid="InputInstructions"] { display: none !important; }

/* ── Contenedores transparentes ── */
[data-testid="stVerticalBlock"],[data-testid="stVerticalBlockBorderWrapper"],.stForm {
    background: transparent !important; border: none !important; box-shadow: none !important;
}

/* ── Fondo (mismo que login) ── */
.stApp {
    background-image:
        radial-gradient(ellipse 700px 500px at 50% -60px,rgba(37,99,235,.16) 0%,transparent 65%),
        radial-gradient(ellipse 500px 400px at 85% 95%,rgba(79,70,229,.07) 0%,transparent 55%),
        radial-gradient(ellipse 300px 200px at 10% 80%,rgba(15,98,254,.05) 0%,transparent 55%),
        url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?fm=jpg&q=60&w=3000&auto=format&fit=crop&ixlib=rb-4.1.0');
    background-size: auto,auto,auto,cover;
    background-position: 0 0,0 0,0 0,center;
    background-attachment: auto,auto,auto,fixed;
    background-color: #040b16;
}
[data-testid="stAppViewContainer"] { background: transparent !important; }

/* ── Card central ── */
.block-container {
    position: relative; z-index: 1;
    max-width: 420px !important; width: 100% !important;
    height: 830px !important;
    padding: 0 1rem 2.4rem !important;
    margin-top: 3vh !important; margin-bottom: 3vh !important;
    background: rgba(6,13,28,.72) !important;
    border: 1px solid rgba(255,255,255,.090) !important;
    border-radius: 24px !important;
    backdrop-filter: blur(24px) !important; -webkit-backdrop-filter: blur(24px) !important;
    box-shadow:
        0 0 0 1px rgba(37,99,235,.05),
        0 48px 100px rgba(0,0,0,.60),
        0 12px 36px rgba(0,0,0,.40),
        inset 0 1px 0 rgba(255,255,255,.06) !important;
    overflow: visible !important;
}

/* ── Textos globales ── */
p,span,li,label,div { color: #e2e8f0; }

/* ── Animaciones ── */
@keyframes fadeUp { from { opacity:0;transform:translateY(14px); } to { opacity:1;transform:translateY(0); } }
@keyframes pulse-ring {
    0%,100% { box-shadow:0 0 0 0 rgba(79,70,229,.22),0 6px 20px rgba(79,70,229,.32); }
    50%      { box-shadow:0 0 0 5px rgba(79,70,229,.0),0 6px 20px rgba(79,70,229,.32); }
}

/* ── Hero ── */
.reg-hero { display:flex;flex-direction:column;align-items:center;gap:.8rem;padding:2.2rem 1rem 1.2rem;animation:fadeUp .22s cubic-bezier(.22,1,.36,1) forwards; }
.hero-icon-outer {
    display:inline-flex;align-items:center;justify-content:center;
    width:64px;height:64px;border-radius:18px;
    background:linear-gradient(140deg,#2e1065 0%,#4f46e5 55%,#7c3aed 100%);
    box-shadow:0 0 0 1px rgba(99,102,241,.16),0 0 0 5px rgba(79,70,229,.06),0 6px 20px rgba(79,70,229,.32);
    flex-shrink:0;animation:pulse-ring 3.2s ease-in-out infinite;
}
.hero-icon-outer svg { width:28px;height:28px;stroke:#fff;fill:none;stroke-linecap:round;stroke-linejoin:round; }
.hero-badge { display:inline-flex;align-items:center;gap:.5rem;padding:.28rem .95rem .28rem .65rem;border-radius:100px;background:rgba(79,70,229,.10);border:1px solid rgba(99,102,241,.24); }
.hero-badge-dot { width:6px;height:6px;border-radius:50%;background:#818cf8;box-shadow:0 0 6px rgba(129,140,248,.8);flex-shrink:0; }
.hero-badge-text { font-size:.64rem;font-weight:800;text-transform:uppercase;letter-spacing:.18em;color:#a5b4fc; }
.hero-text-group { display:flex;flex-direction:column;align-items:center;gap:.35rem; }
.hero-title { font-size:1.7rem;font-weight:800;background:linear-gradient(140deg,#f8fafc 20%,#cbd5e1 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.6px;margin:0;line-height:1.12; }
.hero-sub { font-size:.76rem;color:#64748b;margin:0;letter-spacing:.015em;line-height:1.5; }

/* ── Divisor ── */
.form-divider { display:flex;align-items:center;gap:.6rem;margin:.4rem 0 .8rem;padding:0 1rem; }
.form-divider-line { flex:1;height:1px;background:rgba(255,255,255,.065); }
.form-divider-label { font-size:.60rem;font-weight:700;text-transform:uppercase;letter-spacing:.16em;color:#2d3f56; }

/* ── Labels ── */
label[data-testid="stWidgetLabel"] p { font-size:.76rem !important;font-weight:700 !important;letter-spacing:.02em !important;color:#8898a8 !important;margin-bottom:.25rem !important; }

/* ── Inputs ── */
[data-baseweb="input"] { background:transparent !important;border:none !important;box-shadow:none !important;outline:none !important;width:100% !important; }
[data-baseweb="input"] > div {
    position:relative !important;display:flex !important;align-items:center !important;
    background-color:#030c1c !important;border:1px solid rgba(255,255,255,.09) !important;
    border-radius:10px !important;box-shadow:none !important;outline:none !important;
    width:100% !important;min-height:2.6rem !important;
    transition:border-color .18s,box-shadow .18s !important;
}
[data-baseweb="input"] > div:focus-within { border-color:rgba(99,102,241,.55) !important;box-shadow:0 0 0 3px rgba(99,102,241,.10) !important; }
[data-baseweb="input"] input { color:#e2e8f0 !important;background:transparent !important;font-size:.875rem !important;border:none !important;outline:none !important;box-shadow:none !important;width:100% !important; }
[data-baseweb="input"] input[type="password"] { padding-right:2.2rem !important; }
[data-baseweb="input"] input::placeholder { color:#253347 !important; }
[data-baseweb="input"] input:-webkit-autofill,
[data-baseweb="input"] input:-webkit-autofill:hover,
[data-baseweb="input"] input:-webkit-autofill:focus {
    -webkit-box-shadow:0 0 0 100px #030c1c inset !important;
    -webkit-text-fill-color:#e2e8f0 !important;
    transition:background-color 5000s ease !important;
}
[data-baseweb="input"] button {
    position:absolute !important;right:8px !important;top:50% !important;transform:translateY(-50%) !important;
    background:transparent !important;border:none !important;box-shadow:none !important;
    color:#3d5269 !important;width:20px !important;height:20px !important;min-width:0 !important;
    cursor:pointer !important;z-index:2 !important;padding:0 !important;margin:0 !important;outline:none !important;
    display:flex !important;align-items:center !important;justify-content:center !important;
}
[data-baseweb="input"] button:hover { color:#5d7a96 !important; }
.stTextInput { margin:0 0 .5rem 0 !important; }

/* ── Barra de fortaleza ── */
.strength-wrap { margin:.05rem 0 .6rem;width:100%; }
.strength-header { display:flex;justify-content:space-between;align-items:center;margin-bottom:.26rem; }
.strength-section-label { font-size:.60rem;font-weight:700;letter-spacing:.10em;text-transform:uppercase;color:#2d3f56; }
.strength-track { background:rgba(255,255,255,.06);border-radius:100px;height:3.5px;overflow:hidden; }
.strength-fill { height:100%;border-radius:100px;transition:width .4s cubic-bezier(.4,0,.2,1),background .4s ease; }

/* ── Botón primario ── */
[data-testid="stBaseButton-primary"] {
    background:linear-gradient(135deg,#4f46e5 0%,#3730a3 100%) !important;
    color:#fff !important;border:none !important;border-radius:10px !important;
    font-size:.875rem !important;font-weight:700 !important;letter-spacing:.04em !important;
    width:100% !important;padding:.76rem !important;
    box-shadow:0 2px 18px rgba(79,70,229,.36) !important;
    transition:opacity .15s,transform .13s !important;
    margin-top:.45rem !important;margin-bottom:.4rem !important;
}
[data-testid="stBaseButton-primary"]:hover {
    opacity:.92 !important;transform:translateY(-1px) !important;
    box-shadow:0 6px 24px rgba(79,70,229,.46) !important;
}

/* ── Botón secundario (Volver) ── */
[data-testid="stBaseButton-secondary"] {
    background:rgba(255,255,255,.04) !important;
    color:rgba(226,232,240,.65) !important;border:1px solid rgba(255,255,255,.09) !important;
    border-radius:10px !important;
    font-size:.82rem !important;font-weight:600 !important;
    width:100% !important;padding:.62rem !important;
    transition:all .15s !important;
    margin-bottom:.5rem !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    background:rgba(255,255,255,.09) !important;
    color:#e2e8f0 !important;border-color:rgba(255,255,255,.18) !important;
}

/* ── Info note ── */
.info-note { display:flex;align-items:flex-start;gap:.55rem;padding:.58rem .9rem;border-radius:10px;background:rgba(6,13,28,.45) !important;border:1px solid rgba(255,255,255,.09) !important;margin-top:.3rem;backdrop-filter:blur(12px) !important; }
.info-note svg { flex-shrink:0;margin-top:1px;opacity:.35; }
.info-note-text { font-size:.69rem;color:#3d5269;line-height:1.58; }
.info-note-text strong { color:#4d6580; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius:10px !important;background:rgba(255,255,255,.03) !important; }
[data-testid="stAlert"] p { color:#e2e8f0 !important; }

/* ── Layout de contenido ── */
.stVerticalBlock,.stVerticalBlockBorderWrapper,.stElementContainer {
    padding-left:0 !important;padding-right:0 !important;
    margin-left:0 !important;margin-right:0 !important;
    width:100% !important;box-sizing:border-box !important;
}
</style>
<div id="_mrp_pg_cover"></div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="reg-hero">
  <div class="hero-icon-outer">
    <svg viewBox="0 0 24 24" stroke-width="1.9">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
      <line x1="19" y1="8" x2="19" y2="14"/>
      <line x1="16" y1="11" x2="22" y2="11"/>
    </svg>
  </div>
  <div class="hero-badge">
    <span class="hero-badge-dot"></span>
    <span class="hero-badge-text">Sistema MRP Polyline</span>
  </div>
  <div class="hero-text-group">
    <div class="hero-title">Crear cuenta</div>
    <p class="hero-sub">Completa los datos para acceder al sistema</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Divisor ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="form-divider">
  <span class="form-divider-line"></span>
  <span class="form-divider-label">Datos de acceso</span>
  <span class="form-divider-line"></span>
</div>""", unsafe_allow_html=True)

# ── Formulario de registro ────────────────────────────────────────────────────
reg_username = st.text_input("Usuario", placeholder="3-20 caracteres (letras, numeros, _)", key="reg_user")
reg_email    = st.text_input("Correo electronico", placeholder="ejemplo@empresa.com", key="reg_email")
reg_password = st.text_input("Contrasena", type="password", placeholder="Minimo 8 caracteres", key="reg_pwd")

# ── Barra de fortaleza ────────────────────────────────────────────────────────
strength = _password_strength(reg_password)
if strength == 0:
    bar_color = "transparent"; bar_label = ""; lbl_color = "#334155"
elif strength < 40:
    bar_color = "#ef4444"; bar_label = "Insegura"; lbl_color = "#ef4444"
elif strength < 70:
    bar_color = "#f59e0b"; bar_label = "Moderada"; lbl_color = "#d97706"
else:
    bar_color = "#22c55e"
    bar_label = "Muy segura" if strength == 100 else "Segura"
    lbl_color = "#16a34a"

st.markdown(f"""
<div class="strength-wrap">
  <div class="strength-header">
    <span class="strength-section-label">Seguridad de la contrasena</span>
    <span style="font-size:.68rem;font-weight:700;color:{lbl_color};transition:color .35s;">{bar_label}</span>
  </div>
  <div class="strength-track">
    <div class="strength-fill" style="width:{strength}%;background:{bar_color};"></div>
  </div>
</div>
""", unsafe_allow_html=True)

reg_password2 = st.text_input("Confirmar contrasena", type="password", placeholder="Repite la contrasena", key="reg_pwd2")

# ── Botón crear cuenta ────────────────────────────────────────────────────────
if st.button("Crear cuenta", use_container_width=True, type="primary", key="btn_create"):
    u  = st.session_state.get("reg_user",  "").strip()
    e  = st.session_state.get("reg_email", "").strip()
    p1 = st.session_state.get("reg_pwd",   "")
    p2 = st.session_state.get("reg_pwd2",  "")

    if not u or not e or not p1 or not p2:
        st.error("Completa todos los campos.")
    elif p1 != p2:
        st.error("Las contrasenas no coinciden.")
    else:
        db = SessionLocal()
        with st.spinner("Creando cuenta..."):
            ok, msg = register_user(db, username=u, email=e, password=p1, password_confirm=p2, role="cliente")
        db.close()
        if ok:
            for k in ["reg_user", "reg_email", "reg_pwd", "reg_pwd2"]:
                st.session_state.pop(k, None)
            st.session_state.register_success = True
            st.switch_page("pages/login.py")
        else:
            st.error(msg)

# ── Botón volver al login ─────────────────────────────────────────────────────
if st.button("← Volver al inicio de sesion", use_container_width=True, type="secondary", key="btn_back"):
    st.switch_page("pages/login.py")

# ── Nota informativa ─────────────────────────────────────────────────────────
st.markdown("""
<div class="info-note">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
       stroke="#64748b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
  </svg>
  <span class="info-note-text">
    Al registrarte obtienes acceso como <strong>cliente</strong>.
    Ya tienes cuenta? Ve a <strong>Iniciar sesion</strong>.
  </span>
</div>""", unsafe_allow_html=True)
