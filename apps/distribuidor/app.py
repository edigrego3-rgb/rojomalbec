import streamlit as st
import pandas as pd
import os
import sys
import json
import urllib.request

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from modules.data_manager import load_catalog_data, guardar_visibilidad
from modules.utils import redondear_precio, extraer_descripcion, generar_mensaje_whatsapp

st.set_page_config(
    page_title="Rojo Malbec B2B | Mayoristas",
    page_icon="🍷",
    layout="wide"
)

CONFIG_FILE = os.path.join(current_dir, "config_b2b.json")
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"min_compra": 300000, "envio_gratis": 350000}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

config_b2b = load_config()

if "carrito_b2b" not in st.session_state:
    st.session_state.carrito_b2b = {}

# --- UTILIDADES PARA IMÁGENES EXACTAMENTE COMO EL ORIGINAL ---
def buscar_imagenes(nombre_producto):
    images_dir = os.path.join(current_dir, "images")
    if not os.path.exists(images_dir): return None, None
        
    term = nombre_producto.lower()
    if "sloopy joe" in term or "sloppy" in term: term = "sloppyjoe"
    elif "sal al malbec" in term: term = "malbec"
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
    elif "pu erh" in term or "puerh" in term or "pu-erh" in term: term = "tepuerh"
    elif "mole" in term: term = "molemexicano"
    elif "burger" in term: term = "burger"
    elif "jerk" in term: term = "jerk"
    elif "nanami" in term: term = "nanami"
    elif "pesto" in term: term = "pesto"
    elif "za'atar" in term or "zaatar" in term: term = "zaatar"
    else: term = term.replace(" ", "")
        
    term = term.replace("&", "").replace("(", "").replace(")", "").replace("ñ", "n").replace("ü", "u").replace("'", "").replace("ó", "o")
    
    archivos_validos = []
    for f in os.listdir(images_dir):
        f_limpio = f.lower().replace("ñ", "n")
        if "trasera" in f_limpio or "back" in f_limpio: continue
        f_sin_espacios = f_limpio.replace("_", "").replace(" ", "")
        if term in f_sin_espacios or term in f_limpio.replace("_", " "):
            archivos_validos.append(f)
            
    if not archivos_validos: return None, None
        
    for f in archivos_validos:
        if "clean" in f.lower() or "frontal" in f.lower() or "color" in f.lower() or "premium" in f.lower():
            return os.path.join(images_dir, f), None
            
    return os.path.join(images_dir, archivos_validos[0]), None


# --- LAYOUT PRINCIPAL ---
col_logo, col_titulo, col_web = st.columns([1, 3, 1.5])
with col_logo:
    st.image(os.path.join(current_dir, "logo.png"), width=150)
with col_titulo:
    st.markdown('''
        <div style='padding-top: 10px;'>
            <h1 style='margin:0; font-size:2rem; color:#d4af37;'>Rojo Malbec</h1>
            <span style='color:#a0a0b0; font-size:1.1rem; display:block;'>Portal Mayorista B2B</span>
            <span style='color:#888888; font-size:0.9rem; font-style:italic;'>Sales Marinas, Blends de Especias y Tés.<br>Ruta 14 S/N Los Hornillos, Córdoba</span>
        </div>
    ''', unsafe_allow_html=True)
with col_web:
    st.markdown('''
        <div style='padding-top: 25px; text-align: right;'>
            <a href='https://rojomalbec.com.ar' target='_blank' style='color:#d4af37; text-decoration:none; font-size:1rem; border:1px solid #d4af37; padding:8px 16px; border-radius:8px;'>🌐 Visitá nuestra web</a>
        </div>
    ''', unsafe_allow_html=True)

# Banner dinámico
st.info(f"📦 **ATENCIÓN:** La compra mínima mayorista es de **$ {config_b2b['min_compra']:,}**. \n\n✨ ¡Superando los **$ {config_b2b['envio_gratis']:,}** el envío es **GRATIS**!")

@st.dialog("Detalle del Producto")
def modal_venta(nombre, img_front, descripcion, pvp_redondeado, costo_redondeado):
    st.markdown(f"<h4 style='text-align:center; color:#d4af37;'>{nombre}</h4>", unsafe_allow_html=True)
    if img_front:
        st.image(img_front, use_container_width=True)
    
    ganancia = pvp_redondeado - costo_redondeado
    
    st.markdown("### 💰 Tu Negocio")
    st.markdown(f"**Tu Costo Mayorista:** $ {costo_redondeado:,}")
    st.markdown(f"**PVP Sugerido (Público):** $ {pvp_redondeado:,}")
    st.success(f"✨ **Tu Ganancia Limpia:** $ {ganancia:,} por frasco")
    
    if descripcion:
        st.markdown(f"<div style='background-color:rgba(128,128,128,0.15); padding:10px; border-radius:8px;'><b>Info del Producto:</b><br>{descripcion}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    qty_actual = st.session_state.carrito_b2b.get(nombre, {}).get("cantidad", 0)
    opciones = list(range(0, 101))
    
    new_qty = st.selectbox("Seleccionar Cantidad:", options=opciones, index=qty_actual)
    
    if st.button("Guardar en el carrito", type="primary", use_container_width=True):
        if new_qty == 0 and nombre in st.session_state.carrito_b2b:
            del st.session_state.carrito_b2b[nombre]
        elif new_qty > 0:
            st.session_state.carrito_b2b[nombre] = {
                "cantidad": new_qty,
                "costo": costo_redondeado,
                "pvp": pvp_redondeado
            }
        st.rerun()

# CARGAR DATOS
df_catalogo = load_catalog_data()
df_catalogo["Categoria"] = "Otros"
df_catalogo.loc[df_catalogo["Nombre"].str.contains("Sal ", case=False, na=False), "Categoria"] = "Sales"
df_catalogo.loc[df_catalogo["Nombre"].str.contains("Pimienta", case=False, na=False), "Categoria"] = "Pimientas"
df_catalogo.loc[df_catalogo["Nombre"].str.contains("Te |Té |Rooibos", case=False, na=False), "Categoria"] = "Tés"
mask_blends = ~df_catalogo["Categoria"].isin(["Sales", "Pimientas", "Tés"])
df_catalogo.loc[mask_blends, "Categoria"] = "Blends"


# --- CARRITO ---
total_items = sum([item['cantidad'] for item in st.session_state.carrito_b2b.values()])
if total_items > 0:
    with st.expander(f"🛒 VER MI PEDIDO ({total_items} productos)", expanded=False):
        st.markdown("### 📝 Resumen del Pedido")
        total_costo = 0
        items_carrito = []
        
        for nombre, item_data in list(st.session_state.carrito_b2b.items()):
            sub_costo = item_data['cantidad'] * item_data['costo']
            total_costo += sub_costo
            st.markdown(f"**{nombre}**")
            st.write(f"{item_data['cantidad']} unid. x $ {item_data['costo']:,} = $ {sub_costo:,}")
            items_carrito.append({'nombre': nombre, 'cantidad': item_data['cantidad'], 'precio': item_data['costo'], 'subtotal': sub_costo})
            st.markdown("---")
            
        st.markdown(f"### 💰 Total a Pagar: $ {total_costo:,}")
        
        if total_costo < config_b2b['min_compra']:
            faltan = config_b2b['min_compra'] - total_costo
            st.error(f"❌ Faltan $ {faltan:,} para llegar al mínimo de compra.")
            boton_habilitado = False
        elif total_costo < config_b2b['envio_gratis']:
            faltan_envio = config_b2b['envio_gratis'] - total_costo
            st.warning(f"✔️ Compra Mínima alcanzada. ¡Sumá $ {faltan_envio:,} más para tener ENVÍO GRATIS!")
            boton_habilitado = True
        else:
            st.success("🎉 ¡Felicidades! Tenés ENVÍO GRATIS.")
            boton_habilitado = True
            
        st.markdown("### Datos para el envío")
        cliente_nombre = st.text_input("Nombre del Local / Comprador")
        cliente_tel = st.text_input("Teléfono de Contacto")
        cliente_dir = st.text_input("Dirección de Envío / Transporte")
        
        if boton_habilitado:
            col_wa, col_mail = st.columns(2)
            
            with col_wa:
                if st.button("📲 Pedir por WhatsApp", use_container_width=True):
                    if not cliente_nombre or not cliente_tel or not cliente_dir:
                        st.error("Completá nombre, teléfono y dirección.")
                    else:
                        datos_cli = {"nombre": cliente_nombre, "direccion": cliente_dir, "telefono": cliente_tel}
                        link = generar_mensaje_whatsapp(items_carrito, total_costo, "5493544308380", datos_cli)
                        st.markdown(f"<a href='{link}' target='_blank' style='display:block; text-align:center; background-color:#25D366; color:white; padding:8px; border-radius:5px; text-decoration:none;'>👉 Abrir WhatsApp</a>", unsafe_allow_html=True)
            with col_mail:
                if st.button("✉️ Pedir por Email", use_container_width=True):
                    if not cliente_nombre or not cliente_tel or not cliente_dir:
                        st.error("Completá nombre, teléfono y dirección.")
                    else:
                        pedido_detalle = ""
                        for i in items_carrito:
                            pedido_detalle += f"- {i['cantidad']} unid. | {i['nombre']} | $ {i['precio']} c/u\n"

                        
                        payload = {
                            "_subject": f"🍷 NUEVO PEDIDO B2B - {cliente_nombre}",
                            "Cliente": cliente_nombre,
                            "Telefono": cliente_tel,
                            "Direccion_Envio": cliente_dir,
                            "Total_Pedido": f"$ {total_costo:,}",
                            "Detalle_Pedido": pedido_detalle
                        }
                        
                        req = urllib.request.Request(
                            "https://formspree.io/f/mqpzjopo",
                            data=json.dumps(payload).encode("utf-8"),
                            headers={
                                "Content-Type": "application/json", 
                                "Accept": "application/json",
                                "User-Agent": "Mozilla/5.0"
                            }
                        )
                        try:
                            urllib.request.urlopen(req, timeout=3)
                            st.success("✅ ¡Pedido enviado con éxito! Nos contactaremos a la brevedad para coordinar el pago y envío.")
                            st.session_state.carrito_b2b = {}
                        except Exception as e:
                            st.error(f"Hubo un error al enviar el pedido: {e}")

# --- FILTRO CLIENTES NORMALES ---
if not st.session_state.get("admin_mode", False):
    df_visible = df_catalogo[df_catalogo["Visible_B2B"] == True]
else:
    df_visible = df_catalogo


# --- CATÁLOGO ESTILO ACORDEON ---
categorias_list = ["🧂 Sales", "🌿 Blends", "🍵 Tés", "🌶️ Pimientas", "📦 Otros"]
st.markdown('''
<style>
div[data-testid="stExpander"] details summary p {
    font-size: 1.3rem; font-weight: 700; color: #d4af37; text-transform: uppercase;
}
div[data-testid="stExpander"] button {
    margin-bottom: 8px !important; text-align: left !important; border-radius: 12px !important;
    border: 1px solid #d4af37 !important; background: linear-gradient(145deg, #ffffff, #f9f9f9) !important;
    color: #222 !important; font-weight: 600 !important; font-size: 1.05rem !important;
    padding: 12px 15px !important;
}
</style>
''', unsafe_allow_html=True)

if not df_visible.empty:
    for cat_name in categorias_list:
        cat_clean = cat_name.split(" ", 1)[1].strip()
        df_cat_tab = df_visible[df_visible["Categoria"] == cat_clean]
        
        if df_cat_tab.empty: continue
        
        with st.expander(cat_name, expanded=False):
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
                
                badge = "🛒" # SIEMPRE carrito, como pidio el dueño.
                
                if st.button(f"{badge} {nombre}", key=f"btn_{cat_clean}_{idx}", use_container_width=True):
                    modal_venta(nombre, img_front, descripcion, pvp_redondeado, costo_redondeado)

# --- PANEL ADMIN OCULTO ---
st.divider()

if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

col_admin_spacer, col_admin_btn = st.columns([6, 1])
with col_admin_btn:
    if st.button("⚙️", help="Panel de Administración"):
        st.session_state.show_admin_login = not st.session_state.get("show_admin_login", False)
        if st.session_state.admin_mode:
            st.session_state.admin_mode = False
            st.session_state.show_admin_login = False
            st.session_state.admin_initialized = False
        st.rerun()

if st.session_state.get("show_admin_login", False) and not st.session_state.admin_mode:
    with st.container():
        st.markdown("<div style='background-color:#f1f1f1; padding:15px; border-radius:10px;'><h3>Acceso Administrador</h3></div>", unsafe_allow_html=True)
        clave = st.text_input("Clave", type="password", key="admin_pass")
        if st.button("Ingresar", type="primary"):
            if clave == "Livia2112":
                st.session_state.admin_mode = True
                st.session_state.show_admin_login = False
                st.session_state.admin_initialized = False
                st.rerun()
            else:
                st.error("Clave incorrecta")

if st.session_state.admin_mode:
    st.markdown("<div style='background-color:#f1f1f1; padding:15px; border-radius:10px; margin-bottom:20px;'><h3>⚙️ Panel de Administración B2B</h3></div>", unsafe_allow_html=True)
    
    nuevo_min = st.number_input("Compra Mínima ($)", value=config_b2b['min_compra'], step=10000)
    nuevo_envio = st.number_input("Envío Gratis a partir de ($)", value=config_b2b['envio_gratis'], step=10000)
    if st.button("Guardar Configuración"):
        save_config({"min_compra": nuevo_min, "envio_gratis": nuevo_envio})
        st.success("Configuración guardada con éxito.")
    
    st.markdown("---")
    st.markdown("### Seleccionar Productos Visibles")
    todos_los_nombres = df_catalogo["Nombre"].tolist()
    nombres_visibles_set = set(df_catalogo[df_catalogo["Visible_B2B"] == True]["Nombre"].tolist())
    
    if not st.session_state.get("admin_initialized", False):
        for n in todos_los_nombres:
            st.session_state[f"vis_{n}"] = (n in nombres_visibles_set)
        st.session_state.admin_initialized = True
        
    categorias_admin = df_catalogo.groupby("Categoria")
    for cat_name, cat_df in categorias_admin:
        with st.expander(f"{cat_name} ({len(cat_df)} productos)", expanded=False):
            for _, row_admin in cat_df.iterrows():
                nombre_prod = row_admin["Nombre"]
                st.checkbox(nombre_prod, key=f"vis_{nombre_prod}")
                
    st.markdown("---")
    productos_seleccionados = [n for n in todos_los_nombres if st.session_state.get(f"vis_{n}", False)]
    if st.button("💾 GUARDAR VISIBILIDAD DE PRODUCTOS", type="primary", use_container_width=True):
        exito = guardar_visibilidad(productos_seleccionados, todos_los_nombres)
        if exito:
            st.success("Catálogo actualizado. Los cambios ya son visibles para Preventa y Clientes.")
            st.rerun()
        else:
            st.error("Error al guardar.")
