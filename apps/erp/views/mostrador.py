
# views/mostrador.py
# Vista de Mostrador con Filtros por Categoría, Venta Rápida Multi-Cantidad y Escáner de Código de Barras
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from modules.data_manager import get_df, save_data, load_data
from views.recetas import obtener_codigo_vendedor, MAP_CODIGOS_POS

def detectar_categoria(nombre_producto):
    """Detecta la categoría de un producto basándose en su nombre."""
    nombre = str(nombre_producto).lower()
    if "sal " in nombre or nombre.startswith("sal"):
        return "🧂 Sales"
    elif "vital" in nombre:
        return "💚 Vital"
    elif "té " in nombre or "te " in nombre or "rooibos" in nombre or "karak" in nombre:
        return "🍵 Tés"
    elif "mocktail" in nombre:
        return "🍹 Mocktails"
    elif "pimienta" in nombre:
        return "🌶️ Pimientas"
    else:
        return "🌿 Blends"

def buscar_producto_por_codigo(codigo_escaneado, df_recetas):
    """
    Busca un producto por su código de barras escaneado (RM-XXX-YYY o Code128).
    Retorna el nombre del producto si encuentra coincidencia, None si no.
    """
    codigo_limpio = str(codigo_escaneado).strip().upper()
    
    # 1. Buscar directo en MAP_CODIGOS_POS (invertido: código -> nombre)
    codigo_a_nombre = {}
    for nombre_key, cod_val in MAP_CODIGOS_POS.items():
        codigo_a_nombre[cod_val.upper()] = nombre_key
    
    if codigo_limpio in codigo_a_nombre:
        nombre_pos = codigo_a_nombre[codigo_limpio]
        # Buscar el nombre real en recetas (con capitalización correcta)
        for _, row in df_recetas.iterrows():
            nom_clean = " ".join(str(row["Nombre"]).lower().split())
            if nom_clean == nombre_pos or nom_clean.startswith(nombre_pos.split(" (")[0]):
                return str(row["Nombre"])
        return nombre_pos.title()
    
    # 2. Buscar en la columna Codigo de recetas
    for _, row in df_recetas.iterrows():
        cod_receta = str(row.get("Codigo", "")).strip().upper()
        if cod_receta == codigo_limpio:
            return str(row["Nombre"])
    
    # 3. Buscar generando el código vendedor para cada receta
    for _, row in df_recetas.iterrows():
        cod_vendedor = obtener_codigo_vendedor(row.get("Codigo"), row["Nombre"]).upper()
        if cod_vendedor == codigo_limpio:
            return str(row["Nombre"])
    
    return None

def render_mostrador_tab():

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("## 🏘️ Vista de Mostrador (Catálogo Rápido)")
    with c2:
        st.link_button("🧾 Facturar en AFIP/ARCA", "https://www.afip.gob.ar/", use_container_width=True)
    
    # =============================================
    # ESCÁNER DE CÓDIGO DE BARRAS (NUEVO)
    # =============================================
    st.markdown("---")
    col_scan1, col_scan2 = st.columns([3, 1])
    
    with col_scan1:
        codigo_escaneado = st.text_input(
            "📷 Escanear Código de Barras (USB / Bluetooth)",
            placeholder="Escaneá el código del frasco o escribí RM-XXX-YYY...",
            key="barcode_scanner_input",
            help="Conectá tu lector USB y escaneá el código de barras del frasco. El sistema buscará el producto automáticamente."
        )
    
    with col_scan2:
        cant_scanner = st.number_input("Cantidad", min_value=1, max_value=50, value=1, key="scanner_qty")

    # Procesar escaneo
    if codigo_escaneado:
        df_r_scan = get_df("recetas")
        producto_encontrado = buscar_producto_por_codigo(codigo_escaneado, df_r_scan)
        
        if producto_encontrado:
            st.success(f"✅ Producto encontrado: **{producto_encontrado}**")
            
            # Buscar si tiene stock
            df_lp_scan = get_df("lotes_produccion")
            df_v_scan = get_df("ventas")
            
            if not df_lp_scan.empty:
                ventas_por_lote_scan = df_v_scan.groupby("Lote_Produccion")["Cantidad_Vendida_KG"].sum().to_dict() if not df_v_scan.empty else {}
                # FIX BUG #8: Normalizar nombres eliminando espacios dobles
                nombre_normalizado = " ".join(producto_encontrado.lower().split())
                df_stock_scan = df_lp_scan[df_lp_scan["Producto"].apply(lambda x: " ".join(str(x).lower().split())) == nombre_normalizado].copy()
                
                if not df_stock_scan.empty:
                    df_stock_scan["KG_Vendidos"] = df_stock_scan["Lote_Produccion"].map(ventas_por_lote_scan).fillna(0)
                    df_stock_scan["KG_Disponibles"] = df_stock_scan["Kilos_Producidos"] - df_stock_scan["KG_Vendidos"]
                    
                    gramaje_g = float(df_stock_scan["Gramaje_Por_Envase"].max())
                    total_kg_disp = df_stock_scan["KG_Disponibles"].sum()
                    envases_disp = int((total_kg_disp * 1000) / gramaje_g) if gramaje_g > 0 else 0
                    
                    # Buscar precio (normalizado)
                    r_match = df_r_scan[df_r_scan["Nombre"].apply(lambda x: " ".join(str(x).lower().split())) == nombre_normalizado]
                    precio_pvp = float(r_match.iloc[0]["Precio_Venta"]) if not r_match.empty else 0.0
                    
                    # Buscar primer lote disponible
                    lote_disponible = None
                    for _, lt in df_stock_scan.iterrows():
                        if lt["KG_Disponibles"] > 0:
                            lote_disponible = lt["Lote_Produccion"]
                            break
                    
                    col_info1, col_info2, col_info3 = st.columns(3)
                    col_info1.metric("Stock Disponible", f"{envases_disp} un.")
                    col_info2.metric("Precio PVP", f"${precio_pvp:,.2f}")
                    col_info3.metric("Total Venta", f"${precio_pvp * cant_scanner:,.2f}")
                    
                    if envases_disp >= cant_scanner and lote_disponible:
                        # Bloqueo anti-doble-clic
                        btn_key = f"scan_sell_{codigo_escaneado}_{cant_scanner}"
                        if btn_key not in st.session_state:
                            st.session_state[btn_key] = False
                        
                        if st.button(f"🛒 VENDER {cant_scanner} un. de {producto_encontrado} = ${precio_pvp * cant_scanner:,.2f}", 
                                     key=f"btn_{btn_key}", use_container_width=True, type="primary",
                                     disabled=st.session_state.get(btn_key, False)):
                            st.session_state[btn_key] = True
                            _ejecutar_venta(producto_encontrado, cant_scanner, lote_disponible, gramaje_g, precio_pvp, df_lp_scan)
                    elif envases_disp < cant_scanner:
                        st.error(f"❌ Stock insuficiente. Solo hay {envases_disp} un. disponibles.")
                    else:
                        st.error("❌ Sin lote disponible para este producto.")
                else:
                    st.warning(f"⚠️ No hay lotes producidos para '{producto_encontrado}'.")
            else:
                st.warning("No hay stock registrado.")
        else:
            st.error(f"❌ Código **{codigo_escaneado}** no encontrado. Verificá que el código sea correcto.")
    
    st.markdown("---")
    
    # =============================================
    # 1. CATÁLOGO DE PRODUCTOS (ORIGINAL MEJORADO)
    # =============================================
    
    # 1. Cargar Datos
    df_lp = get_df("lotes_produccion")
    df_v = get_df("ventas")
    df_r = get_df("recetas")
    
    # 2. Buscador y Filtros
    col_h1, col_h2 = st.columns([2, 1])
    search_query = col_h1.text_input("🔍 Buscar Producto...", placeholder="Ej: Malbec, Sal, Blend...")
    solo_con_stock = col_h2.checkbox("Solo con Stock", value=True)
    
    # --- Filtros por Categoría ---
    st.markdown("#### Filtrar por Categoría:")
    categorias = ["🏠 Todos", "🧂 Sales", "🌿 Blends", "💚 Vital", "🍵 Tés", "🍹 Mocktails", "🌶️ Pimientas", "📦 Otros"]
    categoria_sel = st.radio("", categorias, horizontal=True, label_visibility="collapsed")
    
    # 3. Procesar Stock (Lógica similar a inventario)
    if df_lp.empty:
        st.info("No hay stock registrado. Produzca lotes para verlos aquí.")
        return

    # Calcular ventas por lote para obtener stock remanente
    ventas_por_lote = df_v.groupby("Lote_Produccion")["Cantidad_Vendida_KG"].sum().to_dict() if not df_v.empty else {}
    
    # Enriquecer df_lp con stock disponible
    df_stock = df_lp.copy()
    df_stock["KG_Vendidos"] = df_stock["Lote_Produccion"].map(ventas_por_lote).fillna(0)
    df_stock["KG_Disponibles"] = df_stock["Kilos_Producidos"] - df_stock["KG_Vendidos"]
    
    # Calcular unidades/envases disponibles
    def calc_envases(row):
        gramaje = float(row.get("Gramaje_Por_Envase", 0))
        if gramaje > 0:
            return int((row["KG_Disponibles"] * 1000) / gramaje)
        return 0
    
    df_stock["Envases_Disponibles"] = df_stock.apply(calc_envases, axis=1)
    
    # Consolidar por producto (Suma de envases de todos los lotes de ese producto)
    # Guardamos también el primer lote disponible para la venta rápida
    def get_first_lote(group):
        available = group[group["KG_Disponibles"] > 0]
        return available["Lote_Produccion"].iloc[0] if not available.empty else None
    
    lotes_disponibles = df_stock.groupby("Producto").apply(get_first_lote).to_dict()
    gramajes_producto = df_stock.groupby("Producto")["Gramaje_Por_Envase"].max().to_dict()
    
    resumen_mostrador = df_stock.groupby("Producto").agg({
        "Envases_Disponibles": "sum",
        "Gramaje_Por_Envase": "max"
    }).reset_index()
    
    # Unir con el Precio de Venta guardado en Recetas (usando nombres limpios sin doble espacio)
    df_r_copy = df_r[["Nombre", "Precio_Venta", "Codigo"]].copy()
    df_r_copy["Nombre_Limpio"] = df_r_copy["Nombre"].apply(lambda x: " ".join(str(x).lower().split()))
    resumen_mostrador["Nombre_Limpio"] = resumen_mostrador["Producto"].apply(lambda x: " ".join(str(x).lower().split()))
    
    resumen_mostrador = resumen_mostrador.merge(df_r_copy[["Nombre_Limpio", "Precio_Venta", "Codigo"]], on="Nombre_Limpio", how="left")
    
    # Agregar categoría detectada
    resumen_mostrador["Categoria"] = resumen_mostrador["Producto"].apply(detectar_categoria)
    
    # 4. Aplicar Filtros
    if search_query:
        resumen_mostrador = resumen_mostrador[resumen_mostrador["Producto"].str.contains(search_query, case=False)]
    
    if solo_con_stock:
        resumen_mostrador = resumen_mostrador[resumen_mostrador["Envases_Disponibles"] > 0]
    
    # Filtro por categoría
    if categoria_sel != "🏠 Todos":
        resumen_mostrador = resumen_mostrador[resumen_mostrador["Categoria"] == categoria_sel]

    # 5. Renderizado de Tarjetas (Grid)
    if resumen_mostrador.empty:
        st.warning("No se encontraron productos con los filtros seleccionados.")
    else:
        st.markdown(f"##### Mostrando {len(resumen_mostrador)} producto(s)")
        
        # Usamos columnas para crear un grid de 3 tarjetas por fila
        cols = st.columns(3)
        for i, (_, prod) in enumerate(resumen_mostrador.iterrows()):
            with cols[i % 3]:
                producto_nombre = prod['Producto']
                precio_pvp = float(prod['Precio_Venta']) if pd.notna(prod['Precio_Venta']) else 0.0
                stock_units = int(prod['Envases_Disponibles'])
                codigo = obtener_codigo_vendedor(prod['Codigo'], producto_nombre)
                categoria = prod['Categoria']
                gramaje = int(prod['Gramaje_Por_Envase']) if pd.notna(prod['Gramaje_Por_Envase']) else 0
                
                # Color de stock
                stock_color = '#28a745' if stock_units > 5 else ('#ffc107' if stock_units > 0 else '#dc3545')
                
                # Tarjeta HTML
                st.markdown(f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 12px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background-color: #f9f9f9;
                    box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
                    min-height: 200px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.8em; background: #eee; padding: 2px 8px; border-radius: 10px;">{categoria}</span>
                        <span style="font-size: 0.75em; color: #999;">{gramaje}g</span>
                    </div>
                    <h4 style="margin: 8px 0 5px 0; color: #b01a1a; font-size: 1.1em;">{producto_nombre}</h4>
                    <p style="margin: 0; color: #666; font-size: 0.8em;">Código: {codigo}</p>
                    <hr style="margin: 10px 0; border: 0.5px solid #eee;">
                    <div style="display: flex; justify-content: space-between; align-items: end;">
                        <div>
                            <span style="font-size: 0.7em; color: #888;">STOCK</span><br>
                            <span style="font-size: 1.1em; font-weight: bold; color: {stock_color};">
                                {stock_units} un.
                            </span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 0.7em; color: #888;">PRECIO PVP</span><br>
                            <span style="font-size: 1.3em; font-weight: bold; color: #333;">
                                ${precio_pvp:,.2f}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # --- SELECTOR DE CANTIDAD + BOTÓN DE VENTA RÁPIDA ---
                lote_para_venta = lotes_disponibles.get(producto_nombre)
                if lote_para_venta and stock_units > 0:
                    col_qty, col_btn = st.columns([1, 2])
                    
                    with col_qty:
                        cantidad = st.number_input(
                            "Cant.",
                            min_value=1,
                            max_value=stock_units,
                            value=1,
                            key=f"qty_{producto_nombre}_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with col_btn:
                        # Bloqueo anti-doble-clic
                        lock_key = f"lock_venta_{producto_nombre}"
                        
                        if st.button(
                            f"🛒 Vender {cantidad} un.",
                            key=f"venta_rapida_{producto_nombre}_{i}",
                            use_container_width=True,
                            disabled=st.session_state.get(lock_key, False)
                        ):
                            # Activar bloqueo
                            st.session_state[lock_key] = True
                            
                            gramaje_g = gramajes_producto.get(producto_nombre, 100)
                            _ejecutar_venta(producto_nombre, cantidad, lote_para_venta, gramaje_g, precio_pvp, df_lp)
                            
                elif stock_units == 0:
                    st.button("❌ Sin Stock", key=f"sin_stock_{producto_nombre}_{i}", disabled=True, use_container_width=True)


def _ejecutar_venta(producto_nombre, cantidad, lote_para_venta, gramaje_g, precio_pvp, df_lp):
    """
    Ejecuta la venta de N unidades de un producto, registra en Google Sheets,
    y fuerza la recarga del session_state para evitar el bug de rebote de stock.
    """
    kg_por_unidad = gramaje_g / 1000.0
    kg_vendido_total = kg_por_unidad * cantidad
    precio_total = precio_pvp * cantidad
    
    # Obtener costo del lote
    lote_match = df_lp[df_lp["Lote_Produccion"] == lote_para_venta]
    if not lote_match.empty:
        lote_info = lote_match.iloc[0]
        costo_kg = float(lote_info.get("Costo_Unitario_KG", 0))
        costo_venta = costo_kg * kg_vendido_total
        ganancia = precio_total - costo_venta
    else:
        st.error("No se pudo obtener la información del lote para calcular el costo.")
        return
    
    # Crear registro de venta (1 registro por la cantidad total)
    nueva_venta = {
        "UUID": str(uuid.uuid4()),
        "Remito_ID": "",
        "Lote_Produccion": lote_para_venta,
        "Cliente": "Mostrador",
        "Forma_Pago": "Efectivo",
        "Cantidad_Vendida_KG": kg_vendido_total,
        "Precio_Venta_Unitario_KG": precio_pvp * 1000 / gramaje_g if gramaje_g > 0 else 0,
        "Precio_Total": precio_total,
        "Ganancia_Neta": ganancia,
        "Fecha_Venta": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    # =============================================
    # FIX CRÍTICO: Cargar datos FRESCOS de Google Sheets antes de guardar
    # para evitar que el session_state sobreescriba con datos viejos.
    # =============================================
    df_ventas_fresco = load_data("ventas")
    df_ventas_fresco = pd.concat([df_ventas_fresco, pd.DataFrame([nueva_venta])], ignore_index=True)
    save_data("ventas", df_ventas_fresco)
    
    # =============================================
    # FIX CRÍTICO: Forzar recarga del session_state de ventas Y lotes
    # desde Google Sheets para que el stock se recalcule correctamente.
    # =============================================
    st.session_state["ventas"] = load_data("ventas")
    st.session_state["lotes_produccion"] = load_data("lotes_produccion")
    
    # Limpiar bloqueos anti-doble-clic
    keys_to_clean = [k for k in st.session_state if k.startswith("lock_venta_") or k.startswith("scan_sell_")]
    for k in keys_to_clean:
        del st.session_state[k]
    
    st.success(f"✅ ¡Vendido! {cantidad} x {producto_nombre} = ${precio_total:,.2f}")
    st.rerun()


if __name__ == "__main__":
    render_mostrador_tab()
