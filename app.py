
# # -*- coding: utf-8 -*-
# import streamlit as st
# from utils.navbar import render_navbar, render_sidebar_menu
# from utils.session_manager import init_session

# st.set_page_config(page_title="MRP System", layout="wide")

# # Ocultar navegador nativo de páginas de Streamlit del sidebar
# st.markdown("""
#     <style>
#         [data-testid="stSidebarNav"] { display: none !important; }
#     </style>
# """, unsafe_allow_html=True)

# # Verificar/restaurar sesión desde cookie
# session_valid = init_session()

# # Render navbar at the top
# st.markdown("---")
# render_navbar()
# st.markdown("---")

# # Check if user is logged in
# if not session_valid:
#     st.info("👋 Bienvenido. Por favor inicia sesión para continuar.")
#     st.switch_page("pages/login.py")

# # Render sidebar menu
# with st.sidebar:
#     render_sidebar_menu()

# # Main dashboard content
# st.title("📊 Dashboard Logístico")
# st.write(f"¡Bienvenido **{st.session_state.username}**!")

# from database import SessionLocal
# from services.dashboard_service import (
#     get_kpis,
#     get_recent_movements,
#     get_stock_by_warehouse
# )

# db = SessionLocal()

# # -------------------------
# # KPIs
# # -------------------------
# st.subheader("📈 KPIs")

# kpis = get_kpis(db)

# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     st.metric("📦 Stock Total", kpis["total_stock"])

# with col2:
#     st.metric("⚠️ Críticos", kpis["critical"])

# with col3:
#     st.metric("📋 Pendientes", kpis["pending_req"])

# with col4:
#     st.metric("🚚 Salidas", kpis["dispatch_today"])

# # -------------------------
# # Gráfico de Stock
# # -------------------------
# st.subheader("📊 Stock por Almacén")

# stock_by_wh = get_stock_by_warehouse(db)

# if stock_by_wh:
#     import pandas as pd
#     df_stock = pd.DataFrame(
#         list(stock_by_wh.items()), columns=["warehouse_name", "total_quantity"]
#     )
#     st.bar_chart(df_stock.set_index("warehouse_name")["total_quantity"])
# else:
#     st.info("No hay datos de stock disponibles")




# -*- coding: utf-8 -*-
import streamlit as st
from utils.navbar import render_navbar, render_sidebar_menu
from utils.session_manager import init_session

st.set_page_config(page_title="MRP System", layout="wide")

# Ocultar navegador nativo de páginas de Streamlit del sidebar
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# Verificar/restaurar sesión desde cookie
session_valid = init_session()

# Render navbar at the top
# st.markdown("---")
# render_navbar()
# st.markdown("---")

# Check if user is logged in
if not session_valid:
    st.info("👋 Bienvenido. Por favor inicia sesión para continuar.")
    st.switch_page("pages/login.py")

# Render sidebar menu
with st.sidebar:
    render_sidebar_menu()

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    /* Elimina márgenes y padding del contenedor principal */
    .block-container {
    /* 1. Ocultar el header nativo y la navegación por defecto */
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* 2. Eliminar paddings y márgenes del contenedor principal */
    .block-container, [data-testid="stAppViewBlockContainer"] {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    /* Hero ocupa toda la pantalla */
    /* 3. Ajuste del Hero para ocupar toda la pantalla sin gaps */
    .hero {
        background: linear-gradient(135deg, #000000, #1e3a8a);
        height: 100vh; /* 100% de la altura de la ventana */
        width: 100%;   /* 100% del ancho */
        height: 100vh;
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        color: white;
    }
    .hero h1 {
        font-size: 3em;
        margin-bottom: 20px;
    }
    .hero p {
        font-size: 1.2em;
        margin-bottom: 40px;
    }
    .hero button {
        background-color: #2563eb;
        color: white;
        border: none;
        padding: 12px 24px;
        margin: 5px;
        border-radius: 6px;
        font-size: 1em;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero">
        <h1>SISTEMA MRP MULTIALMACEN</h1>
        <p>Sistema MRP moderno y escalable.</p>
        <button>Explorar módulos</button>
        <button>Gestionar almacenes</button>
    </div>
    """,
    unsafe_allow_html=True
)
