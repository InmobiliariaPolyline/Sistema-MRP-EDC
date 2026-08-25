import streamlit as st


def require_login():
    """Verifica sesión activa; redirige al login si no hay sesión."""
    from utils.session_manager import init_session
    session_valid = init_session()
    if not session_valid:
        st.error("Debes iniciar sesión para acceder a esta página.")
        st.switch_page("pages/login.py")


def require_superadmin():
    """Solo permite acceso al superadmin; redirige al dashboard si es cliente."""
    require_login()
    if st.session_state.get("role") != "superadmin":
        st.error("Acceso denegado. Solo el superadmin puede acceder a esta sección.")
        st.switch_page("pages/dashboard.py")


def require_cliente():
    """Solo permite acceso a clientes; redirige al admin si es superadmin (salvo que esté impersonando)."""
    require_login()
    if st.session_state.get("role") == "superadmin":
        if not st.session_state.get("impersonating"):
            st.switch_page("pages/admin.py")


def get_current_user_id():
    if st.session_state.get("impersonating"):
        return st.session_state.get("impersonating_user_id")
    return st.session_state.get("user_id")


def get_current_username():
    return st.session_state.get("username")


def get_current_user_role() -> str:
    return st.session_state.get("role", "cliente")


def is_superadmin() -> bool:
    return st.session_state.get("role") == "superadmin"


def logout():
    from utils.session_manager import logout_session
    logout_session()
