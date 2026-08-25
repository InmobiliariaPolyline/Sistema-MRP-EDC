# -*- coding: utf-8 -*-
"""
session_manager.py

MECANISMO DE SESIÓN:
- Primario:  st.query_params["token"] — escrito desde Python, persiste en la URL
             cuando el usuario presiona F5 o abre otra pestaña con la misma URL.
- Secundario: st.session_state — funciona durante la navegación sin recarga
              (st.switch_page preserva session_state, pero F5 lo borra).

POR QUÉ NO USAMOS COOKIES VÍA JS:
- components.html() sirve el iframe como data URL (data:text/html;base64,…).
  Los navegadores bloquean document.cookie desde data URLs, así que la cookie
  nunca se escribía en el browser. El enfoque JS de cookies fue descartado.
"""
import streamlit as st
import streamlit.components.v1 as components
from database import SessionLocal
from services.session_service import (
    get_valid_session,
    update_activity,
    delete_session,
)

COOKIE_NAME = "mrp_session_token"   # mantenido por si se lee via st.context.cookies
_PARAM_NAME  = "token"              # clave en st.query_params
_LOGIN_PATH  = "/login"


# ── helpers internos ──────────────────────────────────────────────────────────

def _persist_token_to_url(token: str) -> None:
    """Escribe el token en la URL (query param). Persiste al presionar F5."""
    try:
        if st.query_params.get(_PARAM_NAME) != token:
            st.query_params[_PARAM_NAME] = token
    except Exception:
        pass


def _remove_token_from_url() -> None:
    """Elimina el token de la URL (logout)."""
    try:
        if _PARAM_NAME in st.query_params:
            del st.query_params[_PARAM_NAME]
    except Exception:
        pass


def _clear_state() -> None:
    """Limpia el session_state de autenticación."""
    st.session_state.logged_in    = False
    st.session_state.user_id      = None
    st.session_state.username     = None
    st.session_state.session_token = None
    st.session_state.role         = None


def _js_expires(days: int = 1) -> str:
    from datetime import datetime, timedelta, timezone
    dt = datetime.now(timezone.utc) + timedelta(days=days)
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


# ── API pública ───────────────────────────────────────────────────────────────

def init_session() -> bool:
    """
    Verifica y restaura la sesión en cada carga de página.
    Retorna True si sesión válida, False si debe redirigir al login.

    Caso 1: session_state tiene logged_in=True  → navegación normal (st.switch_page
            preserva session_state). Escribe token en URL para F5.
    Caso 2: session_state vacío (F5 / nueva pestaña) → lee token de URL query
            params (principal) o st.context.cookies (fallback).
    """
    st.session_state.setdefault("logged_in",      False)
    st.session_state.setdefault("username",        None)
    st.session_state.setdefault("user_id",         None)
    st.session_state.setdefault("session_token",   None)
    st.session_state.setdefault("role",            "cliente")

    # ── Caso 1: sesión activa en memoria ─────────────────────────────────────
    if st.session_state.logged_in and st.session_state.session_token:
        db = SessionLocal()
        try:
            valid = get_valid_session(db, st.session_state.session_token)
            if valid:
                update_activity(db, st.session_state.session_token)
                _persist_token_to_url(st.session_state.session_token)
                return True
            else:
                _clear_state()
                _remove_token_from_url()
                return False
        finally:
            db.close()

    # ── Caso 2: F5 / nueva pestaña → leer token ──────────────────────────────
    token = st.query_params.get(_PARAM_NAME)

    # Fallback a cookie HTTP si el param no existe (compatibilidad)
    if not token:
        try:
            token = st.context.cookies.get(COOKIE_NAME)
        except Exception:
            token = None

    if not token:
        return False

    db = SessionLocal()
    try:
        valid = get_valid_session(db, token)
        if valid:
            st.session_state.logged_in     = True
            st.session_state.user_id       = valid.user_id
            st.session_state.username      = valid.username
            st.session_state.role          = valid.role
            st.session_state.session_token = token
            update_activity(db, token)
            _persist_token_to_url(token)
            return True
        else:
            _clear_state()
            _remove_token_from_url()
            return False
    finally:
        db.close()


def logout_session() -> None:
    """Elimina la sesión de la DB, limpia TODO el session_state + URL y redirige al login."""
    token = st.session_state.get("session_token")
    if token:
        db = SessionLocal()
        try:
            delete_session(db, token)
        finally:
            db.close()
    _remove_token_from_url()
    # Limpia TODO el estado (incluido estado de expansión del sidebar) para evitar
    # que la barra lateral reaparezca al navegar a login tras cerrar sesión.
    st.session_state.clear()
    st.switch_page("pages/login.py")


def logout_redirect() -> None:
    """Alias de logout_session() — mantenido por compatibilidad."""
    logout_session()


def login_redirect(token: str, path: str = None) -> None:
    """Navega a la página destino tras login. session_state se preserva con switch_page."""
    dest_page = "pages/admin.py" if path == "/admin" else "pages/dashboard.py"
    st.switch_page(dest_page)


def write_cookie_and_redirect(token: str, path: str = "/dashboard") -> None:
    """Mantenido por compatibilidad — ahora delega en switch_page."""
    dest_page = "pages/admin.py" if path == "/admin" else "pages/dashboard.py"
    st.switch_page(dest_page)
