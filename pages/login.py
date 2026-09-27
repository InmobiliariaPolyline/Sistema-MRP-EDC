# -*- coding: utf-8 -*-
import streamlit as st
from sqlalchemy.exc import OperationalError
from database import SessionLocal
from services.auth_service import login_user
from services.login_log_service import log_login
from services.session_service import create_session
from utils.session_manager import init_session
from utils.theme import apply_public_theme

st.set_page_config(
    page_title="Acceso — Sistema MRP Polyline",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 0

MAX_ATTEMPTS = 5

# ── Redirigir si ya hay sesión activa ─────────────────────────────────────────
_db_early = SessionLocal()
for _k, _v in [("logged_in", False), ("user_id", None), ("username", None), ("session_token", None)]:
    st.session_state.setdefault(_k, _v)
if init_session():
    _db_early.close()
    _dest = "pages/dashboard.py"
    st.session_state["_current_page"] = _dest
    st.switch_page(_dest)
    st.stop()
_db_early.close()

st.markdown("""
<style>
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

/* ── Fondo ── */
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
    height: 640px !important;
    padding: 0 0 2.4rem 0 !important;
    margin-top: 4vh !important; margin-bottom: 4vh !important;
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
    0%,100% { box-shadow:0 0 0 0 rgba(37,99,235,.22),0 6px 20px rgba(37,99,235,.32); }
    50%      { box-shadow:0 0 0 5px rgba(37,99,235,.0),0 6px 20px rgba(37,99,235,.32); }
}

/* ── Hero ── */
.login-hero { display:flex;flex-direction:column;align-items:center;gap:.8rem;padding:2.4rem 2rem 1.4rem;animation:fadeUp .22s cubic-bezier(.22,1,.36,1) forwards; }
.hero-icon-outer {
    display:inline-flex;align-items:center;justify-content:center;
    width:64px;height:64px;border-radius:18px;
    background:linear-gradient(140deg,#1e3a8a 0%,#2563eb 55%,#4f46e5 100%);
    box-shadow:0 0 0 1px rgba(99,102,241,.16),0 0 0 5px rgba(37,99,235,.06),0 6px 20px rgba(37,99,235,.32);
    flex-shrink:0;animation:pulse-ring 3.2s ease-in-out infinite;
}
.hero-icon-outer svg { width:28px;height:28px;stroke:#fff;fill:none;stroke-linecap:round;stroke-linejoin:round; }
.hero-badge { display:inline-flex;align-items:center;gap:.5rem;padding:.28rem .95rem .28rem .65rem;border-radius:100px;background:rgba(37,99,235,.10);border:1px solid rgba(37,99,235,.24); }
.hero-badge-dot { width:6px;height:6px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px rgba(59,130,246,.8);flex-shrink:0; }
.hero-badge-text { font-size:.64rem;font-weight:800;text-transform:uppercase;letter-spacing:.18em;color:#60a5fa; }
.hero-text-group { display:flex;flex-direction:column;align-items:center;gap:.35rem; }
.hero-title { font-size:1.8rem;font-weight:800;background:linear-gradient(140deg,#f8fafc 20%,#cbd5e1 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-.6px;margin:0;line-height:1.12; }
.hero-sub { font-size:.76rem;color:#64748b;margin:0;letter-spacing:.015em;line-height:1.5; }

/* ── Divisor ── */
.form-divider { display:flex;align-items:center;gap:.6rem;margin:.4rem 0 .8rem;padding:0 2rem; }
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
[data-baseweb="input"] > div:focus-within { border-color:rgba(37,99,235,.55) !important;box-shadow:0 0 0 3px rgba(37,99,235,.10) !important; }
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
.stTextInput { margin:0 0 .6rem 0 !important; }

/* ── Botón primario ── */
[data-testid="stFormSubmitButton"] button,[data-testid="stBaseButton-primary"] {
    background:linear-gradient(135deg,#2563eb 0%,#1d4ed8 100%) !important;
    color:#fff !important;border:none !important;border-radius:10px !important;
    font-size:.875rem !important;font-weight:700 !important;letter-spacing:.04em !important;
    width:100% !important;padding:.76rem !important;
    box-shadow:0 2px 18px rgba(37,99,235,.36) !important;
    transition:opacity .15s,transform .13s !important;
    margin-top:.55rem !important;margin-bottom:.5rem !important;
}
[data-testid="stFormSubmitButton"] button:hover,[data-testid="stBaseButton-primary"]:hover {
    opacity:.92 !important;transform:translateY(-1px) !important;
    box-shadow:0 6px 24px rgba(37,99,235,.46) !important;
}

/* ── Enlace a registro ── */
[data-testid="stPageLink"] { margin:0 0 .5rem !important; }
[data-testid="stPageLink"] a {
    display:flex !important;justify-content:center !important;
    font-size:.82rem !important;font-weight:600 !important;color:#60a5fa !important;
    text-decoration:none !important;opacity:.75 !important;
    transition:opacity .15s !important;
}
[data-testid="stPageLink"] a:hover { opacity:1 !important; }

/* ── Info note ── */
.info-note { display:flex;align-items:flex-start;gap:.55rem;padding:.58rem .9rem;border-radius:10px;background:rgba(6,13,28,.45) !important;border:1px solid rgba(255,255,255,.09) !important;margin-top:.3rem;backdrop-filter:blur(12px) !important; }
.info-note svg { flex-shrink:0;margin-top:1px;opacity:.35; }
.info-note-text { font-size:.69rem;color:#3d5269;line-height:1.58; }
.info-note-text strong { color:#4d6580; }

/* ── Warn banner ── */
.warn-banner { display:flex;align-items:flex-start;gap:.6rem;padding:.6rem .9rem;border-radius:10px;background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.16);margin-bottom:.7rem;animation:fadeUp .2s ease; }
.warn-banner svg { flex-shrink:0;margin-top:1px; }
.warn-banner-text { font-size:.72rem;color:#d97706;font-weight:600;line-height:1.45; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius:10px !important;background:rgba(255,255,255,.03) !important; }
[data-testid="stAlert"] p { color:#e2e8f0 !important; }

/* ── Layout de contenido ── */
.stVerticalBlock,.stVerticalBlockBorderWrapper,.stElementContainer {
    padding-left:0 !important;padding-right:0 !important;
    margin-left:0 !important;margin-right:0 !important;
    width:100% !important;box-sizing:border-box !important;
}
[data-testid="stForm"],[data-testid="stForm"] .stTextInput,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
    max-width:100% !important;width:100% !important;margin-left:0 !important;margin-right:0 !important;
}
</style>
""", unsafe_allow_html=True)
apply_public_theme()

# ── Segunda verificación de sesión ────────────────────────────────────────────
for _k, _v in [("logged_in", False), ("user_id", None), ("username", None), ("session_token", None)]:
    st.session_state.setdefault(_k, _v)

db = SessionLocal()
if init_session():
    db.close()
    dest = "pages/dashboard.py"
    st.session_state["_current_page"] = dest
    st.switch_page(dest)
    st.stop()

# ── Banner de registro exitoso ────────────────────────────────────────────────
if st.session_state.get("register_success"):
    st.success("Cuenta creada exitosamente. Inicia sesion con tus credenciales.")
    st.session_state.register_success = False

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="login-hero">
  <div class="hero-icon-outer">
    <svg viewBox="0 0 24 24" stroke-width="1.9">
      <rect x="2" y="3" width="20" height="14" rx="2.5"/>
      <path d="M8 21h8M12 17v4"/>
      <polyline points="5 13 8.5 9 12 11.5 16 7 19 9.5" stroke-width="1.75"/>
      <circle cx="5"  cy="13"  r="1.1" fill="white" stroke="none"/>
      <circle cx="8.5" cy="9"  r="1.1" fill="white" stroke="none"/>
      <circle cx="12" cy="11.5" r="1.1" fill="white" stroke="none"/>
      <circle cx="16" cy="7"  r="1.1" fill="white" stroke="none"/>
      <circle cx="19" cy="9.5" r="1.1" fill="white" stroke="none"/>
    </svg>
  </div>
  <div class="hero-badge">
    <span class="hero-badge-dot"></span>
    <span class="hero-badge-text">Sistema MRP Polyline</span>
  </div>
  <div class="hero-text-group">
    <div class="hero-title">Bienvenido</div>
    <p class="hero-sub">Gestión de recursos y planificación de materiales</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Advertencia de intentos ───────────────────────────────────────────────────
attempts = st.session_state.login_attempts
if attempts >= 2:
    remaining = MAX_ATTEMPTS - attempts
    s = "s" if remaining != 1 else ""
    st.markdown(f"""
    <div class="warn-banner">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
           stroke="#d97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <span class="warn-banner-text">
        {remaining} intento{s} restante{s} antes del bloqueo de 15 minutos.
      </span>
    </div>""", unsafe_allow_html=True)

# ── Divisor ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="form-divider">
  <span class="form-divider-line"></span>
  <span class="form-divider-label">Credenciales</span>
  <span class="form-divider-line"></span>
</div>""", unsafe_allow_html=True)

# ── Formulario de login ───────────────────────────────────────────────────────
with st.form("login_form", clear_on_submit=False):
    username = st.text_input("Usuario o correo electronico", placeholder="usuario o email")
    password = st.text_input("Contraseña", type="password", placeholder="••••••••••")
    submit_login = st.form_submit_button("Continuar", use_container_width=True)

if submit_login:
    if not username or not password:
        st.error("Completa todos los campos.")
    else:
        try:
            with st.spinner("Verificando..."):
                success, user, msg = login_user(db, username, password)
        except OperationalError:
            db.rollback()
            st.error(
                "No se pudo conectar con la base de datos. Verifica "
                "DATABASE_URL en .env o Streamlit Secrets."
            )
        else:
            if success:
                st.session_state.login_attempts = 0
                log_login(db, user.id, user.username)
                token = create_session(db, user.id, user.username, role=user.role)
                st.session_state.logged_in     = True
                st.session_state.user_id       = user.id
                st.session_state.username      = user.username
                st.session_state.role          = user.role
                st.session_state.session_token = token
                db.close()
                st.session_state["_current_page"] = "pages/dashboard.py"
                st.switch_page("pages/dashboard.py")
            else:
                st.session_state.login_attempts += 1
                st.error(msg)

# ── Enlace a registro ─────────────────────────────────────────────────────────
st.page_link("pages/register.py", label="¿No tienes cuenta? Crear cuenta →")

# ── Nota informativa ─────────────────────────────────────────────────────────
st.markdown("""
<div class="info-note">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
       stroke="#64748b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
  <span class="info-note-text">
    La cuenta se bloquea <strong>15 minutos</strong> tras 5 intentos fallidos.
    Puedes ingresar con <strong>usuario o correo</strong>.
  </span>
</div>""", unsafe_allow_html=True)

db.close()
