import streamlit as st
import pandas as pd
import os
import sys
import json
import urllib.request

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from modules.data_manager import load_catalog_data
from modules.utils import redondear_precio, extraer_descripcion

st.set_page_config(
    page_title="Rojo Malbec | Pedidos Mayoristas",
    page_icon="🍷",
    layout="wide"
)

CONFIG_FILE = os.path.join(current_dir, "config_b2b.json")
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"min_compra": 60000, "envio_gratis": 150000}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

config_b2b = load_config()

if "carrito_b2b" not in st.session_state:
    st.session_state.carrito_b2b = {}

# Layout principal
st.markdown("<h1 style='text-align:center; color:#d4af37;'>🍷 Rojo Malbec B2B</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Portal de Pedidos Mayoristas Exclusivo</p>", unsafe_allow_html=True)

# Banner dinámico
st.info(f"📦 **ATENCIÓN:** La compra mínima mayorista es de **$ {config_b2b['min_compra']:,}**. \n\n✨ ¡Superando los **$ {config_b2b['envio_gratis']:,}** el envío es **GRATIS**!")

# Funciones helper de imágenes
def buscar_imagenes(nombre_producto):
    img_dir = os.path.join(current_dir, "images")
    if not os.path.exists(img_dir): return None, None
    import glob
    def norm(t): return str(t).lower().replace(' ', '').replace('_', '').replace('-', '')
    archivos = glob.glob(os.path.join(img_dir, "*.png")) + glob.glob(os.path.join(img_dir, "*.jpg"))
    target = norm(nombre_producto)
    for f in archivos:
        b = norm(os.path.basename(f).split('.')[0])
        if b == target or b in target or target in b:
            return f, None
    return None, None

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
        st.markdown(f"<div style='background-color:#f9f9f9; padding:10px; border-radius:8px;'><b>Info del Producto:</b><br>{descripcion}</div>", unsafe_allow_html=True)
    
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

df_cat = load_catalog_data()
if not df_cat.empty:
    df_cat = df_cat[df_cat["Visible_B2B"].astype(str).str.upper().isin(["1", "TRUE", "SI", "SÍ"])]
    df_cat["Categoria"] = "Otros"
    df_cat.loc[df_cat["Nombre"].str.contains("Te |Té |Rooibos", case=False, na=False), "Categoria"] = "Tés"
    df_cat.loc[df_cat["Nombre"].str.contains("Pimienta", case=False, na=False), "Categoria"] = "Pimientas"
    df_cat.loc[df_cat["Nombre"].str.contains("Sal ", case=False, na=False), "Categoria"] = "Sales"
    
    mask_blends = ~df_cat["Categoria"].isin(["Sales", "Pimientas", "Tés"])
    df_cat.loc[mask_blends, "Categoria"] = "Blends"

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
            items_carrito.append({'nombre': nombre, 'cantidad': item_data['cantidad'], 'precio': item_data['costo']})
            st.markdown("---")
            
        st.markdown(f"### 💰 Total a Pagar: $ {total_costo:,}")
        
        # Logica de compra minima y envio
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
        
        if boton_habilitado:
            if st.button("Enviar Pedido a Rojo Malbec", type="primary", use_container_width=True):
                if not cliente_nombre or not cliente_tel:
                    st.error("Por favor completá tu nombre y teléfono.")
                else:
                    pedido_detalle = ""
                    for i in items_carrito:
                        pedido_detalle += f"- {i['cantidad']} unid. | {i['nombre']} | $ {i['precio']} c/u\n"
                    
                    payload = {
                        "_subject": f"🛒 NUEVO PEDIDO B2B - {cliente_nombre}",
                        "Cliente": cliente_nombre,
                        "Telefono": cliente_tel,
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
                        urllib.request.urlopen(req)
                        st.success("✅ ¡Pedido enviado con éxito! Nos contactaremos a la brevedad para coordinar el pago y envío.")
                        st.session_state.carrito_b2b = {}
                    except Exception as e:
                        st.error(f"Hubo un error al enviar el pedido: {e}")

# --- CATÁLOGO ---
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

if not df_cat.empty:
    for cat_name in categorias_list:
        cat_clean = cat_name.split(" ", 1)[1].strip()
        df_cat_tab = df_cat[df_cat["Categoria"] == cat_clean]
        
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
                
                qty_actual = st.session_state.carrito_b2b.get(nombre, {}).get("cantidad", 0)
                badge = f"🛒 [{qty_actual}] " if qty_actual > 0 else "➕ "
                
                if st.button(f"{badge} {nombre}", key=f"btn_{cat_clean}_{idx}", use_container_width=True):
                    modal_venta(nombre, img_front, descripcion, pvp_redondeado, costo_redondeado)

# --- PANEL ADMIN OCULTO ---
st.divider()
with st.expander("⚙️ Panel Admin (Solo Dueño)"):
    clave = st.text_input("Clave de acceso", type="password")
    if clave == "rojo2026": 
        st.success("Acceso concedido")
        nuevo_min = st.number_input("Compra Mínima ($)", value=config_b2b['min_compra'], step=10000)
        nuevo_envio = st.number_input("Envío Gratis a partir de ($)", value=config_b2b['envio_gratis'], step=10000)
        if st.button("Guardar Configuración"):
            save_config({"min_compra": nuevo_min, "envio_gratis": nuevo_envio})
            st.success("Configuración guardada con éxito. Actualizá la página.")
