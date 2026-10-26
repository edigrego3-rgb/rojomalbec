import streamlit as st
import pandas as pd
import os
import sys

# --- RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from modules.data_manager import load_catalog_data, guardar_visibilidad
from modules.utils import redondear_precio, extraer_descripcion, generar_mensaje_whatsapp

# --- CONFIGURACIÓN DE PÁGINA ---
if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = "collapsed"

st.set_page_config(
    page_title="Herramienta Preventa | Rojo Malbec",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state=st.session_state.sidebar_state
)


# --- SEGURIDAD: PANTALLA DE LOGIN ---
from modules.data_manager import load_catalog_data, guardar_visibilidad, get_vendedores_auth, get_estadisticas_vendedor
import time

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "vendedor_nombre" not in st.session_state:
    st.session_state.vendedor_nombre = ""

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align:center; color:#d4af37;'>🔒 Acceso Preventistas</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Por favor seleccioná tu nombre e ingresá tu clave oficial.</p>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1,2,1])
    with col_l2:
        diccionario_claves = get_vendedores_auth()
        nombres_vendedores = list(diccionario_claves.keys())
        
        vendedor_elegido = st.selectbox("¿Quién sos?", [""] + nombres_vendedores)
        clave = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", use_container_width=True, type="primary"):
            if not vendedor_elegido:
                st.error("❌ Por favor seleccioná tu nombre de la lista.")
            elif vendedor_elegido in diccionario_claves and clave == str(diccionario_claves[vendedor_elegido]):
                st.session_state.autenticado = True
                st.session_state.vendedor_nombre = vendedor_elegido
                st.success(f"✅ ¡Bienvenido, {vendedor_elegido}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Clave incorrecta para ese usuario.")
    
    st.stop()

# --- ESTILO CLON B2B ---

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

[data-testid="stAppViewContainer"] {
    background: linear-gradient(165deg, #0a0a0f 0%, #111118 50%, #0d0d14 100%);
    font-family: 'Inter', sans-serif;
}

/* Ocultar Streamlit Cloud */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important; display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="manage-app-button"] {display: none !important;}
[data-testid="viewerBadge"] {display: none !important;}
.stDeployButton {display: none !important;}
[class^="viewerBadge"] { display: none !important; }
[class*="viewerBadge"] { display: none !important; }
[class*="manage-app"] { display: none !important; }

.header-bar {
    background: linear-gradient(135deg, #8b0000 0%, #a02020 50%, #8b0000 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 0 0 15px 15px;
    margin-top: -50px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

.card {
    background: linear-gradient(145deg, #1a1a24 0%, #222230 100%);
    border-radius: 12px;
    padding: 15px;
    color: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    border: 1px solid #333;
    margin-bottom: 10px;
    position: relative;
}

.cart-badge {
    position: absolute;
    top: -10px;
    right: -10px;
    background: #d4af37;
    color: #000;
    font-weight: 800;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    z-index: 10;
}

.prod-name { font-size: 1.2rem; font-weight: 700; color: #d4af37; margin-bottom: 8px; }
.price-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.price-label { font-size: 0.8rem; color: #a0a0b0; text-transform: uppercase; letter-spacing: 0.5px; }
.price-main { font-size: 1.4rem; font-weight: 800; color: #fff; }
.price-pvp { text-align: right; }
.price-pvp-value { font-size: 1.1rem; color: #d4af37; font-weight: 600; }
.gain-badge {
    background: rgba(212, 175, 55, 0.1);
    color: #d4af37;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 600;
    text-align: center;
    margin-top: 5px;
    border: 1px solid rgba(212, 175, 55, 0.3);
}

/* --- MOBILE GRID --- */
@media (max-width: 640px) {
    [data-testid="column"] {
        flex: 1 1 auto !important;
        padding-left: 2px !important;
        padding-right: 2px !important;
    }
    
    /* Para columnas de 1/2 de ancho */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(n) {
        min-width: 30% !important;
    }
    
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 2%;
    }
    .card { padding: 10px; }
    .prod-name { font-size: 0.95rem; }
    .price-main, .price-pvp-value { font-size: 1rem; }
}
</style>
""", unsafe_allow_html=True)

# --- UTILIDADES PARA IMÁGENES ---
def buscar_imagenes(nombre_producto):
    img_dir = os.path.join(current_dir, "images")
    if not os.path.exists(img_dir):
        return None, None
        
    term = nombre_producto.lower()
    
    # --- DICCIONARIO INTELIGENTE ---
    if "sloopy joe" in term or "sloppy" in term: term = "sloppyjoe"
    elif "te ahumado" in term or "té ahumado" in term or "lapsang" in term: term = "salmalbecteahumado"
    elif "sal al malbec" in term: term = "salmarinaalmalbec"
    elif "sal negra" in term or "hawaiana" in term: term = "hawaiana"
    elif "ajo a las hierbas" in term: term = "ajohierbas"
    elif "bbq" in term or "barbacoa" in term: term = "barbacoa"
    elif "bosque y brasas" in term: term = "bosque"
    elif "kebab" in term: term = "kebab"
    elif "panko" in term or "sesamo y limon" in term: term = "sesamo"
    elif "españa profunda" in term or "espana" in term: term = "espana"
    elif "glühwein" in term or "gluhwein" in term: term = "gluhwein"
    elif "mocktail" in term: term = "botanico"
    elif "panch" in term: term = "panch"
    elif "criolla deshidratada" in term: term = "criolla"
    elif "rooibos" in term: term = "rooibos"
    elif "mole" in term: term = "molemexicano"
    elif "sal british" in term: term = "british"
    elif "esvanetian" in term: term = "svanetian"
    elif "rosas y romero" in term: term = "rosas"
    elif "del desierto" in term: term = "desierto"
    elif "vikinga" in term: term = "vikinga"
    elif "limon y chile" in term: term = "limonchile"
    elif "queso" in term: term = "queso"
    elif "parrilera" in term: term = "parrilera"
    elif "pimienta negra" in term: term = "pimientanegra"
    elif "pimienta roja" in term: term = "pimientaroja"
    elif "pimienta verde" in term: term = "pimientaverde"
    elif "jerk" in term: term = "jerk"
    elif "nanami" in term: term = "nanami"
    elif "pesto" in term: term = "pesto"
    elif "za'atar" in term or "zaatar" in term: term = "zaatar"
    else:
        term = term.replace(" ", "")
        
    term = term.replace("&", "").replace("(", "").replace(")", "").replace("ñ", "n").replace("ü", "u").replace("'", "").replace("ō", "o")
    
    archivos_validos = []
    for f in os.listdir(img_dir):
        f_limpio = f.lower().replace("ñ", "n")
        if "trasera" in f_limpio or "back" in f_limpio:
            continue
        f_sin_espacios = f_limpio.replace("_", "").replace(" ", "")
        if term in f_sin_espacios or term in f_limpio.replace("_", " "):
            archivos_validos.append(f)
            
    if not archivos_validos:
        return None, None
        
    for f in archivos_validos:
        if "clean" in f.lower() or "frontal" in f.lower() or "color" in f.lower() or "premium" in f.lower():
            return os.path.join(img_dir, f), None
            
    return os.path.join(img_dir, archivos_validos[0]), None

MAP_CODIGOS_POS = {
    'sal al malbec': 'RM-SAL-MAL', 'sal british': 'RM-SAL-BRI', 'sal de limon y chile': 'RM-SAL-LCH',
    'sal de limon y chile (suave)': 'RM-SAL-LCH', 'sal de rosas y romero': 'RM-SAL-ROS', 'sal del desierto': 'RM-SAL-DES',
    'sal negra hawaiana': 'RM-SAL-HAW', 'sal negra tipo hawaiana': 'RM-SAL-HAW', 'sal esvanetian': 'RM-SAL-ESV',
    'sal svanetian': 'RM-SAL-ESV', 'sal vikinga ahumada': 'RM-SAL-VIK', 'ajo a las hierbas': 'RM-BLE-AJO',
    'ajo a las hierbas gourmet': 'RM-BLE-AJO', 'bbq': 'RM-BLE-BBQ', 'bbq rojo malbec': 'RM-BLE-BBQ',
    'curry colombo': 'RM-BLE-COL', 'nanami togarashi': 'RM-BLE-NAN', 'nanami tōgarashi': 'RM-BLE-NAN',
    "za'atar": 'RM-BLE-ZAA', 'zaatar': 'RM-BLE-ZAA', 'sloopy joe': 'RM-BLE-SLO', 'sloppy joe': 'RM-BLE-SLO',
    'gluhwein': 'RM-BLE-GLU', 'glühwein': 'RM-BLE-GLU', 'panch phoron': 'RM-BLE-PAN', 'pesto siciliano con pistacho': 'RM-BLE-PES',
    'mole mexicano': 'RM-BLE-MOL', 'mole mexicano de autor': 'RM-BLE-MME', 'espana profunda': 'RM-BLE-ESP',
    'españa profunda': 'RM-BLE-ESP', 'dry hot honey': 'RM-BLE-DRY', 'vital caldo': 'RM-VIT-CAL',
    'vital italia': 'RM-VIT-ITA', 'vital india': 'RM-VIT-IND', 'vital parrilera': 'RM-VIT-PAR',
    'vital criollo': 'RM-VIT-CRI', 'vital citrus': 'RM-VIT-CIT', 'vital tipo queso': 'RM-VIT-QUE',
    'vital tipo queso · perfil parmesano reserva': 'RM-VIT-QUE', 'pimienta negra': 'RM-PIM-NEG',
    'pimienta negra de autor': 'RM-PIM-NEG', 'pimienta roja y larga': 'RM-PIM-ROJ', 'pimienta roja y pimienta larga': 'RM-PIM-ROJ',
    'pimienta verde': 'RM-PIM-VER', 'pimienta verde de autor': 'RM-PIM-VER', 'te pu-erh': 'RM-TEA-PUE',
    'te pu erh': 'RM-TEA-PUE', 'te pu-erh rojo malbec': 'RM-TEA-PUE', 'rooibos ambar': 'RM-TEA-ROO',
    'rooibos : ambar africano': 'RM-TEA-ROO', 'te verde del zoco': 'RM-TEA-ZOC', 'te karak': 'RM-TEA-KAR',
    'cacao y zest': 'RM-TEA-CAC',
    'sal al malbec & te ahumado': 'RM-SAL-MTA', 'sal al malbec & té ahumado': 'RM-SAL-MTA',
    'sal al malbec y te ahumado': 'RM-SAL-MTA', 'sal al malbec y té ahumado': 'RM-SAL-MTA'
}

def normalizar_nombre_prod(texto):
    import unicodedata
    s = str(texto).lower().replace("&", " y ")
    s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return " ".join(s.split())

def auto_generar_codigo(nombre):
    palabras = str(nombre).strip().upper().split()
    if not palabras: return 'RM-XXX-000'
    pref = palabras[0][:3]
    suf = palabras[1][:3] if len(palabras) > 1 else pref
    return f'RM-{pref}-{suf}'

def obtener_codigo_vendedor(codigo_actual, nombre_producto):
    if codigo_actual and str(codigo_actual).startswith('RM-'): return str(codigo_actual).strip()
    nom_norm = normalizar_nombre_prod(nombre_producto)
    for k, v in MAP_CODIGOS_POS.items():
        if normalizar_nombre_prod(k) == nom_norm:
            return v
    if codigo_actual and str(codigo_actual).strip() != '' and str(codigo_actual).lower() != 'nan':
        cod_clean = str(codigo_actual).strip()
        if not cod_clean.startswith("L ") and cod_clean != "SINC":
            return cod_clean
    return auto_generar_codigo(nombre_producto)

def detectar_categoria(nombre):
    n = nombre.lower()
    if "sal" in n or "sales" in n: return "🧂 Sales"
    if "blend" in n: return "🌿 Blends"
    if "vital" in n: return "💚 Vital"
    if "te " in n or "té " in n or n.startswith("te ") or n.startswith("té "): return "🍵 Tés"
    if "mocktail" in n: return "🍹 Mocktails"
    if "pimienta" in n: return "🌶️ Pimientas"
    return "🏠 Otros"

# --- ESTADO INICIAL ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = {}
if 'vendedor_nombre' not in st.session_state:
    st.session_state.vendedor_nombre = ""
if 'margen_global' not in st.session_state:
    st.session_state.margen_global = 30



# --- CARGA DE ESTADISTICAS REALES ---
stats = {'Comisiones': 0.0, 'Total_Envases': 0, 'Categorias': {'Sales': 0, 'Blends': 0, 'Tés': 0, 'Pimientas': 0, 'Otros': 0}}
if st.session_state.get('vendedor_nombre'):
    try:
        stats = get_estadisticas_vendedor(st.session_state.vendedor_nombre)
    except:
        pass

# --- HEADER COMPACTO ---
total_items = sum(item['cantidad'] for item in st.session_state.carrito.values())
col_logo, col_titulo, col_cart = st.columns([1, 4, 2])
with col_logo:
    ruta_logo = os.path.join(current_dir, "logo.png")
    if os.path.exists(ruta_logo):
        st.image(ruta_logo, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align:center;'>🍷</h1>", unsafe_allow_html=True)

with col_titulo:
    st.markdown(f"""
        <div style='padding-top: 10px;'>
            <h1 style='margin:0; font-size:2rem; color:#d4af37;'>Rojo Malbec</h1>
            <span style='color:#a0a0b0; font-size:1.1rem;'>Herramienta de Preventa - 👤 {st.session_state.vendedor_nombre}</span>
        </div>
    """, unsafe_allow_html=True)

with col_cart:
    st.markdown(f"""
        <div style='text-align:right; padding-top: 15px;'>
            <span style='font-size:1.8em; font-weight:800; color:#d4af37;'>🛒 {total_items}</span><br>
            <span style='color:#a0a0b0;'>productos</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin-top:0; border-color:#333;'>", unsafe_allow_html=True)

# --- CALCULADORA GLOBAL DE MARGEN ---
with st.expander("🧮 CALCULADORA DE GANANCIAS (Margen Base)", expanded=False):
    st.markdown("Elegí el porcentaje de ganancia base. Se aplicará a todo el catálogo como sugerencia, pero podés ajustar el precio manualmente debajo de cada producto.")
    nuevo_margen = st.slider("Margen sugerido (%)", min_value=0, max_value=150, value=st.session_state.margen_global, step=5)
    if nuevo_margen != st.session_state.margen_global:
        st.session_state.margen_global = nuevo_margen
        # Limpiar los inputs cacheados para forzar el recálculo visual
        for key in list(st.session_state.keys()):
            if key.startswith("precio_"):
                del st.session_state[key]
        st.rerun()

# --- CARRITO INTEGRADO ---
if total_items > 0:
    with st.expander(f"🛒 VER MI PEDIDO ({total_items} productos)", expanded=False):
        st.markdown("### 📝 Resumen del Pedido")
        total_costo = 0
        total_venta = 0
        items_carrito = []
        
        for nombre, item_data in st.session_state.carrito.items():
            if item_data['cantidad'] > 0:
                sub_costo = item_data['cantidad'] * item_data['costo']
                sub_venta = item_data['cantidad'] * item_data['precio_venta']
                total_costo += sub_costo
                total_venta += sub_venta
                
                st.markdown(f"**{nombre}**")
                cols_cart = st.columns([2, 2])
                with cols_cart[0]:
                    st.write(f"A ${item_data['precio_venta']:,} c/u")
                with cols_cart[1]:
                    # Selectbox también en el carrito
                    opciones_cart = list(range(0, 101))
                    if item_data['cantidad'] not in opciones_cart:
                        opciones_cart.append(item_data['cantidad'])
                        opciones_cart.sort()
                        
                    new_qty = st.selectbox("Unidades", options=opciones_cart, index=opciones_cart.index(item_data['cantidad']), key=f"cart_{nombre}", label_visibility="collapsed")
                    if new_qty != item_data['cantidad']:
                        if new_qty == 0:
                            del st.session_state.carrito[nombre]
                        else:
                            st.session_state.carrito[nombre]['cantidad'] = new_qty
                        st.rerun()
                st.markdown("---")
                
                items_carrito.append({
                    'nombre': nombre,
                    'cantidad': item_data['cantidad'],
                    'costo': item_data['costo'],
                    'precio_venta': item_data['precio_venta']
                })
        
        st.markdown(f"### 💰 A cobrar al cliente: $ {total_venta:,}")
        st.info(f"💸 Tu costo (A pagar a Rojo Malbec): $ {total_costo:,}\n\n📈 **Tu ganancia: $ {(total_venta - total_costo):,}**")
        
        st.markdown("#### Datos de Entrega")
        cliente_final = st.text_input("Local / Cliente final", key="cliente_final")
        direccion = st.text_input("Dirección", key="cliente_dir")
        
        c_enviar, c_mail, c_excel = st.columns([1, 1, 1])
        with c_enviar:
            if st.button("🟢 WhatsApp", use_container_width=True):
                if not cliente_final:
                    st.error("Ingresá el cliente.")
                else:
                    d_v = {"nombre_vendedor": st.session_state.vendedor_nombre, "cliente_final": cliente_final, "direccion": direccion}
                    link = generar_mensaje_whatsapp(items_carrito, total_costo, total_venta, "5493544308380", d_v)
                    st.markdown(f"<a href='{link}' target='_blank' style='display:block; text-align:center; background-color:#25D366; color:white; padding:8px; border-radius:5px; text-decoration:none;'>📲 Enviar</a>", unsafe_allow_html=True)
        with c_mail:
            if st.button("📧 Email", use_container_width=True):
                if not cliente_final:
                    st.error("Ingresá el cliente.")
                else:
                    import json
                    import urllib.request
                    
                    pedido_detalle = ""
                    for i in items_carrito:
                        pedido_detalle += f"- {i['cantidad']} unid. | {i['nombre']} | $ {i['precio_venta']} c/u\n"
                    
                    payload = {
                        "_subject": f"🚨 NUEVO PEDIDO - {st.session_state.vendedor_nombre} (Cliente: {cliente_final})",
                        "Vendedor": st.session_state.vendedor_nombre,
                        "Cliente_Final": cliente_final,
                        "Direccion": direccion,
                        "Total_Venta": f"$ {total_venta}",
                        "Costo_Base": f"$ {total_costo}",
                        "Detalle_Pedido": pedido_detalle
                    }
                    
                    req = urllib.request.Request(
                        "https://formspree.io/f/mqpzjopo",
                        data=json.dumps(payload).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json", 
                            "Accept": "application/json",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
                        }
                    )
                    try:
                        urllib.request.urlopen(req)
                        st.success("✅ ¡Mail enviado con éxito!")
                    except Exception as e:
                        st.error(f"Hubo un error al enviar el mail: {e}")
        with c_excel:
            import io
            df_cat = load_catalog_data()
            export_rows = []
            for item in items_carrito:
                match = df_cat[df_cat['Nombre'] == item['nombre']]
                if not match.empty:
                    row = match.iloc[0]
                    cat = detectar_categoria(item['nombre'])
                    gramaje = row.get('Gramaje_Venta', row.get('Base_g', 0))
                    cod_lote = row.get('Codigo', f"L {item['nombre'][:4].upper()}")
                    cod_pos = obtener_codigo_vendedor(cod_lote, item['nombre'])
                    
                    if "SAL-" in cod_pos:
                        cat = "🧂 Sales"
                    elif "BLE-" in cod_pos:
                        cat = "🌿 Blends"
                    elif "VIT-" in cod_pos:
                        cat = "💚 Vital"
                    elif "TEA-" in cod_pos:
                        cat = "🍵 Tés"
                    elif "PIM-" in cod_pos:
                        cat = "🌶️ Pimientas"
                    else:
                        cat = "🏠 Otros"
                        
                    costo_mayorista = float(row.get("Precio_Mayorista", 0))
                    pvp_guardado = float(row.get("PVP_Sugerido", 0))
                    if pvp_guardado > 0:
                        pvp_final = pvp_guardado
                    else:
                        markup_revendedor = float(row.get("Markup_Revendedor", 0))
                        if markup_revendedor > 0:
                            pvp_final = costo_mayorista * (1 + markup_revendedor / 100)
                        else:
                            pvp_final = costo_mayorista * 1.5
                    pvp_redondeado = redondear_precio(pvp_final)

                    export_rows.append({
                        "Categoría": cat,
                        "Producto": item['nombre'],
                        "Cantidad": item['cantidad'],
                        "Gramaje (g)": gramaje,
                        "Código Lote": cod_lote,
                        "Código POS / Barras": cod_pos,
                        "Precio Venta": item['precio_venta'],
                        "PVP Sugerido": pvp_redondeado
                    })
            if export_rows:
                df_ex = pd.DataFrame(export_rows)
                buffer = io.BytesIO()
                
                # Limpiar el nombre del cliente para que sea un nombre de pestaña válido (Excel permite máx 31 caracteres)
                nombre_pestana = f"Pedido {cliente_final}"
                nombre_pestana = "".join([c for c in nombre_pestana if c.isalnum() or c == " "])[:31]
                if not nombre_pestana.strip():
                    nombre_pestana = "Lista de Precios"
                    
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_ex.to_excel(writer, index=False, sheet_name=nombre_pestana)
                
                st.download_button(label="📊 Excel", data=buffer.getvalue(), file_name=f"Lista_{cliente_final}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
                
        if st.button("🗑️ Vaciar Carrito", use_container_width=True):
            st.session_state.carrito = {}
            st.rerun()

# --- CARGAR CATÁLOGO ---
with st.spinner("Actualizando catálogo..."):
    df_catalogo = load_catalog_data()

if df_catalogo.empty:
    st.error("No se pudo cargar el catálogo. Contacte a administración.")
    st.stop()

df_catalogo["Categoria"] = df_catalogo["Nombre"].apply(detectar_categoria)

# Filtramos solo los visibles (Comparte base con B2B)
df_catalogo = df_catalogo[df_catalogo["Visible_B2B"] == True]


# --- GAMIFICACIÓN Y METAS ---
st.markdown(f'''
<div style='background-color:#fff3cd; padding:10px; border-radius:10px; border-left:5px solid #ffc107; margin-bottom:15px;'>
    <div style='display:flex; justify-content:space-between; font-weight:bold; color:#856404;'>
        <span>🏆 Meta del Día: 100 Envases</span>
        <span>Llevás: {stats['Total_Envases']} Envases</span>
    </div>
    <div style='background:#e9ecef; border-radius:5px; height:10px; margin-top:5px; overflow:hidden;'>
        <div style='background:#ffc107; height:10px; width:{min(100, int(stats['Total_Envases']))}%;'></div>
    </div>
    <div style='font-size:0.8rem; color:#856404; margin-top:5px;'>🔥 ¡¡A vender se ha dicho! de tu bono diario!</div>
</div>
''', unsafe_allow_html=True)

# --- MODO VIDRIERA ---
c_vidriera, c_espacio = st.columns([1, 2])
with c_vidriera:
    modo_vidriera = st.toggle("🕶️ Modo Vidriera")

# --- BUSCADOR ---

c_buscar, c_mic = st.columns([4, 1])
with c_buscar:
    search = st.text_input("🔍 Buscar producto...", placeholder="Ej: Sal, Curry...", label_visibility="collapsed")
with c_mic:
    if st.button("🎙️", use_container_width=True):
        st.toast("🔴 Grabando... 'Armame un pedido de 3 sales...' (Prototipo)")
    


@st.dialog("🛒 Detalles y Venta")
def modal_venta(nombre, img_front, descripcion, pvp_redondeado, costo_redondeado, modo_vidriera=False):
    st.markdown(f"<h4 style='text-align:center; color:#d4af37;'>{nombre}</h4>", unsafe_allow_html=True)
    if img_front:
        st.image(img_front, use_container_width=True)
    
    if not modo_vidriera:
        st.markdown(f"<div style='text-align:center; margin-bottom:10px;'><b>PVP Sugerido:</b> $ {pvp_redondeado:,}<br><span style='color:#777; font-size:0.8em;'>Costo ref: $ {costo_redondeado:,}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='text-align:center; margin-bottom:10px; font-size:1.2rem;'><b>Precio:</b> $ {pvp_redondeado:,}</div>", unsafe_allow_html=True)
        
    qty_actual = st.session_state.carrito.get(nombre, {}).get("cantidad", 0)
    
    if qty_actual > 0:
        st.success(f"¡Ya tenés {qty_actual} en el pedido!")
        if st.button("🗑️ Quitar del pedido", use_container_width=True):
            del st.session_state.carrito[nombre]
            st.rerun()
    else:
        precio_sugerido = redondear_precio(costo_redondeado * (1 + (st.session_state.margen_global / 100)))
        
        if not modo_vidriera:
            c1, c2 = st.columns(2)
            with c1:
                cant = st.selectbox("Cantidad", options=list(range(1, 101)), index=0)
            with c2:
                precio = st.number_input("Precio a cobrar", min_value=int(costo_redondeado), value=int(precio_sugerido), step=100)
                
            if st.button("🛒 Confirmar Venta", type="primary", use_container_width=True):
                st.session_state.carrito[nombre] = {"cantidad": cant, "costo": costo_redondeado, "precio_venta": precio}
                st.rerun()
        else:
            st.info("🛍️ Pedile a tu vendedor que escanee este producto para agregarlo.")

    if descripcion:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(descripcion, unsafe_allow_html=True)


# --- RECALCULAR CATEGORÍAS REALES SEGÚN CÓDIGO POS ---
def get_real_category(nombre, cod_lote):
    cod_pos = obtener_codigo_vendedor(cod_lote, nombre)
    if "SAL-" in cod_pos: return "🧂 Sales"
    if "BLE-" in cod_pos: return "🌿 Blends"
    if "VIT-" in cod_pos: return "💚 Vital"
    if "TEA-" in cod_pos: return "🍵 Tés"
    if "PIM-" in cod_pos: return "🌶️ Pimientas"
    return "🏠 Otros"

for idx, row in df_catalogo.iterrows():
    cod = str(row.get('Codigo', f"L {row['Nombre'][:4].upper()}"))
    df_catalogo.at[idx, 'Categoria'] = get_real_category(row['Nombre'], cod)


# --- ESTADÍSTICAS DEL MES (PROTOTIPO) ---
st.markdown('''
<style>
.stat-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #d4af37; margin-bottom: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
.stat-title { font-size: 0.85rem; color: #555; text-transform: uppercase; font-weight: bold; letter-spacing: 0.5px; }
.stat-value { font-size: 1.8rem; color: #222; font-weight: 800; }
.top-item { display: flex; justify-content: space-between; padding: 10px 5px; border-bottom: 1px solid #eee; font-size:0.95rem; }
.top-item b { color: #d4af37; }
</style>
''', unsafe_allow_html=True)

with st.expander("📊 MIS ESTADÍSTICAS (Mensuales)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='stat-box'><div class='stat-title'>Mis Comisiones</div><div class='stat-value'>$ {stats['Comisiones']:,.0f}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='stat-box'><div class='stat-title'>Envases Vendidos</div><div class='stat-value'>{stats['Total_Envases']} unid.</div></div>", unsafe_allow_html=True)
        
    st.markdown("<h5 style='color:#d4af37; margin-top:5px; font-weight:bold;'>📈 Desglose por Familia</h5>", unsafe_allow_html=True)
    st.markdown(f'''
<div style='background:#fff; color:#222; padding:10px; border-radius:8px; border:1px solid #eee; margin-bottom:10px;'>
<div class='top-item' style='background:#f8f9fa; border-radius:5px 5px 0 0;'><span style='color:#222;'>🧂 <b>SALES ({stats['Categorias']['Sales']} envases)</b></span></div>
<div class='top-item' style='background:#f8f9fa; margin-top:10px;'><span style='color:#222;'>🌿 <b>BLENDS ({stats['Categorias']['Blends']} envases)</b></span></div>
<div class='top-item' style='background:#f8f9fa; margin-top:10px;'><span style='color:#222;'>🍵 <b>TÉS ({stats['Categorias']['Tés']} envases)</b></span></div>
<div class='top-item' style='background:#f8f9fa; margin-top:10px;'><span style='color:#222;'>🌶️ <b>PIMIENTAS ({stats['Categorias']['Pimientas']} envases)</b></span></div>
</div>
    ''', unsafe_allow_html=True)

# --- CATÁLOGO POR ACORDEONES (LISTA CON ONDA) ---

categorias_list = ["🧂 Sales", "🌿 Blends", "🍵 Tés", "🌶️ Pimientas", "🏠 Otros"]

st.markdown('''
<style>
div[data-testid="stExpander"] details summary p {
    font-size: 1.3rem;
    font-weight: 700;
    color: #d4af37;
    text-transform: uppercase;
    letter-spacing: 1px;
}
div[data-testid="stExpander"] button {
    margin-bottom: 8px !important;
    text-align: left !important;
    border-radius: 12px !important;
    border: 1px solid #d4af37 !important;
    background: linear-gradient(145deg, #ffffff, #f9f9f9) !important;
    color: #222 !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.08) !important;
    padding: 12px 15px !important;
    transition: all 0.2s ease-in-out !important;
}
.desc-text {
    font-size: 0.95rem; 
    color: #222 !important; 
    line-height: 1.5;
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 8px;
    border-left: 4px solid #d4af37;
}
</style>
''', unsafe_allow_html=True)

for cat in categorias_list:
    df_cat_tab = df_catalogo[df_catalogo["Categoria"] == cat]
    if search:
        df_cat_tab = df_cat_tab[df_cat_tab["Nombre"].str.contains(search, case=False)]
        
    if df_cat_tab.empty:
        continue
        
    with st.expander(cat, expanded=(search != "")):
        for idx, row in df_cat_tab.reset_index(drop=True).iterrows():
            nombre = row["Nombre"]
            costo_mayorista = float(row["Precio_Mayorista"])
            costo_redondeado = redondear_precio(costo_mayorista)
            
            pvp_guardado = float(row.get("PVP_Sugerido", 0))
            if pvp_guardado > 0: 
                pvp_final = pvp_guardado
            else: 
                pvp_final = costo_mayorista * (1 + (float(row.get("Markup_Revendedor", 0)) or 50) / 100)
            pvp_redondeado = redondear_precio(pvp_final)
            
            desc_path = os.path.join(current_dir, "Descripciones_RojoMalbec.md")
            descripcion = extraer_descripcion(nombre, desc_path)
            img_front, _ = buscar_imagenes(nombre)
            
            qty_actual = st.session_state.carrito.get(nombre, {}).get("cantidad", 0)
            badge = f"🟢 [{qty_actual}] " if qty_actual > 0 else "🛒 "
            
            if st.button(f"{badge} {nombre}", key=f"btn_{cat}_{idx}", use_container_width=True):
                soplon = ""
                if not modo_vidriera:
                    soplon = "<div style='background-color:#d4af371a; padding:10px; border-radius:8px; border:1px solid #d4af37; margin-bottom:15px; font-size:0.9rem;'>🔥 <b>Sugerencia IA:</b> Quien lleva este producto suele pedir también <b>Pimienta Roja Larga</b>. ¡Ofrecela por $ 0 extra!</div>"
                
                desc_html = soplon + (f"<div class='desc-text'><b>Info:</b> {descripcion}</div>" if descripcion else "")
                modal_venta(nombre, img_front, desc_html, pvp_redondeado, costo_redondeado, modo_vidriera)
