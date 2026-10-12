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

# --- CONTROL DE ACCESO SEGURO ---
def check_authentication():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    admin_cfg = st.secrets.get("admin_credentials", {})
    valid_user = admin_cfg.get("username", "eduardo")
    valid_pass = admin_cfg.get("password", "RojoMalbec2026!Seguro")

    col_izq, col_centro, col_der = st.columns([1, 1.2, 1])
    with col_centro:
        st.markdown("<div style='text-align: center; margin-top: 40px;'>", unsafe_allow_html=True)
        st.markdown("<h2>🌶️ Rojo Malbec ERP</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666;'>Acceso Restringido y Seguro</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            u_input = st.text_input("Usuario", placeholder="Ingresá tu usuario")
            p_input = st.text_input("Contraseña", type="password", placeholder="••••••••••••")
            btn_login = st.form_submit_button("Ingresar al Sistema", use_container_width=True)

            if btn_login:
                if u_input.strip() == valid_user and p_input.strip() == valid_pass:
                    st.session_state.authenticated = True
                    st.success("Acceso concedido.")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")

    return False

if not check_authentication():
    st.stop()

# --- CARGA DE DATOS (Solo para usuarios autenticados) ---
init_data()

# Barra lateral con botón de cierre de sesión
with st.sidebar:
    st.markdown("👤 **Sesión Activa:** `eduardo`")
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

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
