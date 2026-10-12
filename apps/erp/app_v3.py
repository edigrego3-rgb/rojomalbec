# app_v3.py
import streamlit as st
import modules.styles as styles
from modules.data_manager import init_data

# Import Views
from views.ingredientes import render_ingredientes_tab
from views.recetas import render_recetas_tab
from views.stock import render_stock_tab
from views.clientes import render_clientes_tab
from views.produccion import render_produccion_tab
from views.inventario import render_inventario_tab
from views.ventas import render_ventas_tab
from views.simulador import render_simulador_tab
from views.mostrador import render_mostrador_tab
from views.seguridad import render_seguridad_tab
from views.lista_precios import render_lista_precios_tab
from views.gastos_fijos import render_gastos_fijos_tab
from views.sincronizacion import render_sincronizacion_tab

st.set_page_config(page_title="Rojo Malbec ERP", page_icon="🌶️", layout="wide")
styles.apply_styles()
init_data()

# --- ANCLA DE NAVEGACIÓN ---
# Esto evita que al hacer rerun volvamos al Mostrador
if "active_tab_index" not in st.session_state:
    st.session_state.active_tab_index = 0

st.markdown(f"<h1>🌶️ Rojo Malbec ERP</h1>", unsafe_allow_html=True)

tab_names = [
    "🏠 Mostrador", "🧂 1. Ingredientes", "📦 2. Stock MP", "👥 3. Clientes",
    "🧪 4. Recetas", "🛒 5. Producción", "📦 6. Inventario Productos",
    "💰 7. Ventas", "📊 8. Simulador", "📋 9. Lista de Precios", 
    "💼 10. Gastos Operativos", "🛡️ 11. Seguridad", "☁️ 12. Sincronizar POS"
]

# Creamos las pestañas con el índice persistente
tabs = st.tabs(tab_names)

with tabs[0]: render_mostrador_tab()
with tabs[1]: render_ingredientes_tab()
with tabs[2]: render_stock_tab()
with tabs[3]: render_clientes_tab()
with tabs[4]: render_recetas_tab()
with tabs[5]: render_produccion_tab()
with tabs[6]: render_inventario_tab()
with tabs[7]: render_ventas_tab()
with tabs[8]: render_simulador_tab()
with tabs[9]: render_lista_precios_tab()
with tabs[10]: render_gastos_fijos_tab()
with tabs[11]: render_seguridad_tab()

with tabs[12]: render_sincronizacion_tab()
