# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime
import pandas as pd
from database import SessionLocal
from services.login_log_service import get_login_logs, get_failed_attempts, get_locked_accounts
from utils.auth import require_superadmin
from utils.navbar import render_navbar, render_sidebar_menu

st.set_page_config(
    page_title="Logs de Acceso — Sistema MRP",
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
.logs-hero {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: .5rem;
    padding: 1rem 1.5rem 1.2rem;
    border-radius: 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #1d4ed8 100%);
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(29,78,216,.28);
}
.logs-hero-left { display: flex; align-items: center; gap: 1rem; }
.logs-hero-icon {
    width: 60px; height: 60px; border-radius: 16px;
    background: rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; font-size: 1.8rem;
}
.logs-hero h1  { font-size: 1.55rem; font-weight: 900; color: #fff; margin: 0; }
.logs-hero p   { font-size: .82rem; color: rgba(255,255,255,.70); margin: 2px 0 0; }
.logs-badge {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,.25);
    border-radius: 30px; padding: .35rem 1rem;
    font-size: .78rem; font-weight: 700; color: #bfdbfe;
    white-space: nowrap;
}

/* ── KPI Cards ── */
.akpi { border-radius: 16px; padding: 1.2rem 1.4rem; color: #fff; position: relative; overflow: hidden; }
.akpi-label { font-size: .70rem; font-weight: 700; text-transform: uppercase; letter-spacing: .1em; opacity: .80; margin-bottom: .3rem; }
.akpi-val   { font-size: 2.4rem; font-weight: 900; line-height: 1; }
.akpi-sub   { font-size: .73rem; opacity: .65; margin-top: .2rem; }
.ak-blue    { background: linear-gradient(135deg, #1e3a8a, #2563eb); }
.ak-indigo  { background: linear-gradient(135deg, #312e81, #4f46e5); }
.ak-teal    { background: linear-gradient(135deg, #134e4a, #0d9488); }
.ak-red     { background: linear-gradient(135deg, #7f1d1d, #dc2626); }

/* ── Alert cards ── */
.alert-card {
    display: flex; align-items: center; gap: .9rem;
    padding: .75rem 1rem;
    border-radius: 12px;
    border: 1px solid rgba(239,68,68,.35);
    background: rgba(220,38,38,.10);
    margin-bottom: .45rem;
}
.alert-icon { font-size: 1.3rem; flex-shrink: 0; }
.alert-body { flex: 1; }
.alert-user { font-size: .88rem; font-weight: 700; color: #fca5a5; }
.alert-detail { font-size: .74rem; color: rgba(252,165,165,.70); margin-top: .1rem; }

/* ── Section title ── */
.sec-title {
    font-size: 1rem; font-weight: 800;
    display: flex; align-items: center; gap: .55rem;
    padding-left: .8rem;
    border-left: 4px solid #2563eb;
    margin: 2rem 0 .9rem;
}

/* ── Download button ── */
[data-testid="stBaseButton-secondary"] {
    border-radius: 10px !important;
    font-weight: 600 !important;
}

[data-testid="stAlert"] { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

render_navbar()
with st.sidebar:
    render_sidebar_menu()

# ── Hero ──────────────────────────────────────────────────────────────────────
now  = datetime.now()
user = st.session_state.get("username", "Superadmin")

st.markdown(f"""
<div class="logs-hero">
  <div class="logs-hero-left">
    <div class="logs-hero-icon">&#128203;</div>
    <div>
      <h1>Logs de Acceso</h1>
      <p>Historial de inicios de sesión &nbsp;·&nbsp; {now.strftime("%A %d de %B, %Y")}</p>
    </div>
  </div>
  <div class="logs-badge">&#9733; Superadmin: {user}</div>
</div>
""", unsafe_allow_html=True)

db = SessionLocal()
logs            = get_login_logs(db, limit=200)
locked_accounts = get_locked_accounts(db)
failed_attempts = get_failed_attempts(db, limit=200)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_logs    = len(logs)
unique_users  = len(set(l.username for l in logs)) if logs else 0
today_count   = sum(1 for l in logs if l.login_time.date() == datetime.utcnow().date()) if logs else 0
alert_count   = len(locked_accounts)

k1, k2, k3, k4 = st.columns(4, gap="medium")
k1.markdown(f"""<div class="akpi ak-blue">
  <div class="akpi-label">Accesos Registrados</div>
  <div class="akpi-val">{total_logs}</div>
  <div class="akpi-sub">Últimos 200 registros</div>
</div>""", unsafe_allow_html=True)

k2.markdown(f"""<div class="akpi ak-indigo">
  <div class="akpi-label">Usuarios con Acceso</div>
  <div class="akpi-val">{unique_users}</div>
  <div class="akpi-sub">Usuarios distintos</div>
</div>""", unsafe_allow_html=True)

k3.markdown(f"""<div class="akpi ak-teal">
  <div class="akpi-label">Accesos Hoy</div>
  <div class="akpi-val">{today_count}</div>
  <div class="akpi-sub">{now.strftime("%d/%m/%Y")}</div>
</div>""", unsafe_allow_html=True)

k4.markdown(f"""<div class="akpi ak-red">
  <div class="akpi-label">Alertas Activas</div>
  <div class="akpi-val">{alert_count}</div>
  <div class="akpi-sub">Cuentas bloqueadas ahora</div>
</div>""", unsafe_allow_html=True)

# ── Instrucciones ─────────────────────────────────────────────────────────────
_, _col_help_logs = st.columns([7, 1.5])
with _col_help_logs.popover("📋 Instrucciones", use_container_width=True):
    st.markdown("#### Guía de Logs de Acceso")
    st.markdown("""
**Alertas de Seguridad** — Muestra cuentas bloqueadas en tiempo real por exceder 5 intentos fallidos. El bloqueo dura 15 minutos desde el último intento.

**Intentos Fallidos** — Lista todos los accesos fallidos registrados (últimos 200), con usuario, fecha, IP y razón del fallo. Exportable a CSV.

**Historial de Accesos Exitosos** — Registro de todos los inicios de sesión exitosos. Exportable a CSV para auditoría.

---

**Reglas de seguridad:**
- 5 intentos fallidos consecutivos → cuenta bloqueada 15 min
- Sesiones expiran automáticamente tras 30 min de inactividad
- Las sesiones se invalidan al deshabilitar o eliminar un cliente
""")

# ── Alertas de Seguridad ──────────────────────────────────────────────────────
st.markdown('<div class="sec-title">&#9888; Alertas de Seguridad</div>', unsafe_allow_html=True)

if not locked_accounts:
    st.success("No hay cuentas bloqueadas en este momento. Todo en orden.")
else:
    st.error(f"**{alert_count} cuenta(s) bloqueada(s)** por demasiados intentos fallidos en los últimos 15 minutos.")
    for row in locked_accounts:
        st.markdown(f"""
        <div class="alert-card">
          <div class="alert-icon">&#128274;</div>
          <div class="alert-body">
            <div class="alert-user">{row.username}</div>
            <div class="alert-detail">{row.count} intentos fallidos &nbsp;·&nbsp; Bloqueado por 15 min desde el último intento</div>
          </div>
        </div>""", unsafe_allow_html=True)

# ── Intentos de Acceso Fallidos ───────────────────────────────────────────────
st.markdown('<div class="sec-title">&#128683; Intentos Fallidos Recientes</div>', unsafe_allow_html=True)

if not failed_attempts:
    st.info("No hay intentos de acceso fallidos registrados.")
else:
    search_fail = st.text_input(
        "Buscar en intentos fallidos",
        placeholder="Filtrar por usuario o IP...",
        label_visibility="collapsed",
        key="search_fail",
    )
    fail_data = [
        {
            "#":            i + 1,
            "Usuario":      f.username,
            "Fecha y Hora": f.attempt_time.strftime("%d/%m/%Y %H:%M:%S"),
            "IP":           f.ip_address or "—",
            "Razón":        f.reason or "—",
            "_ts":          f.attempt_time.timestamp(),
        }
        for i, f in enumerate(failed_attempts)
    ]
    df_fail = pd.DataFrame(fail_data).sort_values("_ts", ascending=False).drop(columns=["_ts"]).reset_index(drop=True)
    df_fail["#"] = range(1, len(df_fail) + 1)
    if search_fail:
        q = search_fail.lower()
        df_fail = df_fail[df_fail.apply(
            lambda r: q in r["Usuario"].lower() or q in r["IP"].lower(), axis=1
        )]
    st.dataframe(df_fail, use_container_width=True, hide_index=True)
    csv_fail = df_fail.to_csv(index=False, encoding="utf-8")
    st.download_button(
        label="Descargar CSV — Intentos fallidos",
        data=csv_fail,
        file_name=f"intentos_fallidos_{now.strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

# ── Tabla de logs ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">&#128203; Historial de Accesos Exitosos</div>', unsafe_allow_html=True)

if not logs:
    st.info("No hay registros de acceso aún.")
else:
    search = st.text_input(
        "Buscar",
        placeholder="Filtrar por usuario o IP...",
        label_visibility="collapsed",
    )

    logs_data = [
        {
            "#":            i + 1,
            "Usuario":      l.username,
            "Fecha y Hora": l.login_time.strftime("%d/%m/%Y %H:%M:%S"),
            "IP":           l.ip_address or "—",
            "_ts":          l.login_time.timestamp(),
        }
        for i, l in enumerate(logs)
    ]
    df = pd.DataFrame(logs_data).sort_values("_ts", ascending=False).drop(columns=["_ts"]).reset_index(drop=True)
    df["#"] = range(1, len(df) + 1)

    if search:
        q = search.lower()
        df = df[df.apply(lambda r: q in r["Usuario"].lower() or q in r["IP"].lower(), axis=1)]

    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False, encoding="utf-8")
    st.download_button(
        label="Descargar CSV — Accesos exitosos",
        data=csv,
        file_name=f"logs_acceso_{now.strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

db.close()
