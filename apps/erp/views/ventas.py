import streamlit as st
import pandas as pd
import uuid
import io
from datetime import datetime

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None
from modules.data_manager import get_df, save_data, load_data, append_data

def _clean_pdf_text(text):
    """Limpia caracteres fuera de latin-1 (ej: ō, —, •, etc.) para compatibilidad con FPDF."""
    if text is None:
        return ""
    s = str(text)
    replacements = {
        'ō': 'o', 'Ō': 'O',
        'ū': 'u', 'Ū': 'U',
        'ā': 'a', 'Ā': 'A',
        'ē': 'e', 'Ē': 'E',
        'ī': 'i', 'Ī': 'I',
        '—': '-', '–': '-', '―': '-',
        '•': '*', '▸': '>', '►': '>',
        '…': '...',
        '’': "'", '‘': "'", '`': "'",
        '“': '"', '”': '"', '«': '"', '»': '"',
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode('latin-1', 'replace').decode('latin-1')

def render_ventas_tab():
    st.subheader("💰 Módulo de Ventas, Ganancias y Costo por Kilo")
    
    df_v = get_df("ventas")
    df_lp = get_df("lotes_produccion")
    df_r = get_df("recetas")
    df_c = get_df("clientes")
    
    
    tab_stock_inicial, tab_venta, tab_ganancia = st.tabs(["📝 Stock Inicial de Lotes", "💰 Registrar Venta", "📈 Reporte de Ganancias"])
    
    # 5.1. Módulo de Stock Inicial de Lotes
    with tab_stock_inicial:
        # ... (Código de stock inicial sin cambios significativos, solo asegurar que use df_c si fuera necesario, pero no lo es aquí)
        st.markdown("### 📝 Registro de Stock Inicial de Producto Terminado (Pre-ERP)")
        st.warning("¡ADVERTENCIA! Use esta sección SOLO para cargar stock antiguo. NO descontará materia prima ni registrará trazabilidad.")
        
        productos_opts = sorted(df_r["Nombre"].unique()) if not df_r.empty else []

        if not productos_opts:
            st.info("Debe crear recetas en la Pestaña 2 primero.")
        else:
            st.info("Utilice esta sección para cargar stock que ya tiene en estantería (anterior al sistema).")
            
            p_sel = st.selectbox("1. Seleccionar Producto", productos_opts, help="Elija el producto del cual desea cargar stock inicial.")
            match_r = df_r[df_r["Nombre"] == p_sel]
            if match_r.empty:
                st.warning("No se encontró el producto seleccionado.")
                return
            r_data = match_r.iloc[0]
            codigo_receta = r_data["Codigo"] if pd.notna(r_data.get("Codigo")) else "SINC"
            lote_sugerido = f"{codigo_receta}-{datetime.now().strftime('%y%m%d')}"

            st.markdown("---")
            st.markdown("#### 📝 Datos del Lote")
            
            col_p1, col_p2 = st.columns(2)
            p_cant_kg = col_p1.number_input("Cantidad Producida Total (KG)", min_value=0.0, step=0.1)
            p_costo_unitario = col_p2.number_input("Costo Unitario REAL por KG ($)", min_value=0.0, step=100.0)
            
            col_l1, col_l2 = st.columns(2)
            p_lote = col_l1.text_input("Código de Lote", value=lote_sugerido)
            
            st.markdown("#### 📦 Información de Envases (Fraccionamiento)")
            col_e1, col_e2 = st.columns(2)
            p_cantidad_envases = col_e1.number_input("Cantidad de Envases (Unidades)", min_value=0, value=0, step=1)
            p_gramaje = col_e2.number_input("Contenido por Envase (gramos)", min_value=0.0, value=0.0, step=10.0)
            
            if p_cantidad_envases > 0 and p_gramaje > 0:
                calc_kg = (p_cantidad_envases * p_gramaje) / 1000
                if abs(calc_kg - p_cant_kg) > 0.01:
                    st.warning(f"⚠️ Atención: El peso total ({p_cant_kg} kg) no coincide con los envases ({p_cantidad_envases} x {p_gramaje}g = {calc_kg} kg).")

            st.markdown("---")
            if st.button("🚀 REGISTRAR STOCK INICIAL", type="primary", use_container_width=True):
                if p_cant_kg > 0 and p_costo_unitario > 0:
                    rid = r_data["Id"]
                    lote_produccion = p_lote if p_lote else lote_sugerido
                    costo_total = p_cant_kg * p_costo_unitario
                    nuevo_lote = {
                        "Lote_Produccion": lote_produccion,
                        "Id_Receta": rid,
                        "Producto": p_sel,
                        "Kilos_Producidos": float(p_cant_kg),
                        "Cantidad_Envases": float(p_cantidad_envases),
                        "Gramaje_Por_Envase": float(p_gramaje),
                        "Costo_Total_MateriaPrima": float(costo_total), 
                        "Costo_Unitario_KG": float(p_costo_unitario),
                        "Fecha_Produccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    # FIX BUG #7: Leer datos frescos de Google Sheets
                    df_lp_current = load_data("lotes_produccion")
                    save_data("lotes_produccion", pd.concat([df_lp_current, pd.DataFrame([nuevo_lote])], ignore_index=True))
                    # Forzar recarga del session_state
                    st.session_state["lotes_produccion"] = load_data("lotes_produccion")
                    st.success(f"✅ ¡Éxito! Se cargaron **{p_cant_kg} kg** de **{p_sel}** (Lote: {lote_produccion})")
                    st.rerun()

    # 5.2. Registrar Venta
    with tab_venta:
        st.markdown("### 🏪 Registro de Ventas")
        
        if df_c.empty:
            st.warning("⚠️ Debe registrar al menos un Cliente en la Pestaña 3 antes de vender.")
        elif df_lp.empty:
            st.warning("⚠️ No hay lotes de producción disponibles.")
        else:
            # --- PANEL DE CLIENTE, VENDEDOR Y PAGO (PERSISTENTE) ---
            st.markdown("#### 1. Identificación Comercial")
            col_c1, col_c2, col_c3 = st.columns(3)
            
            # Cargar vendedores desde DB
            df_vend = load_data("vendedores")
            if not df_vend.empty:
                vendedores_activos = df_vend[df_vend["Activo"].astype(str).str.upper().isin(["TRUE", "1", "YES"])]["Nombre"].tolist()
            else:
                vendedores_activos = []
            vendedores_list = ["Rojo Malbec (Directo)"] + sorted(vendedores_activos)
            
            vendedor_sel = col_c1.selectbox("Vendedor / Canal", vendedores_list)
            cliente_sel = col_c2.selectbox("Seleccionar Cliente", sorted(df_c["Nombre"].unique()))
            forma_pago = col_c3.selectbox("Forma de Pago", ["Efectivo", "Transferencia", "Cheque", "Cuenta Corriente", "Otro"])
            
            st.divider()
            
            # --- SELECCIÓN DE PRODUCTO/LOTE ---
            st.markdown("#### 2. Selección de Productos")
            # Construir etiquetas descriptivas para cada lote
            lote_display_map = {}
            for _, row_lp in df_lp.iterrows():
                _lote = row_lp["Lote_Produccion"]
                _prod = row_lp["Producto"]
                _fecha = str(row_lp.get("Fecha_Produccion", ""))[:10]
                _kg_vend = df_v[df_v['Lote_Produccion'] == _lote]['Cantidad_Vendida_KG'].sum() if not df_v.empty else 0
                _stock = row_lp["Kilos_Producidos"] - _kg_vend
                lote_display_map[_lote] = f"{_lote}  ▸  {_prod}  ▸  {_stock:.3f} kg  ▸  {_fecha}"

            lotes_opts = sorted(df_lp["Lote_Produccion"].unique())
            lote_sel = st.selectbox("Seleccionar Lote a Vender", lotes_opts, format_func=lambda x: lote_display_map.get(x, x))
            
            lote_match = df_lp[df_lp["Lote_Produccion"] == lote_sel]
            if lote_match.empty:
                st.warning("No se encontró información del lote seleccionado.")
                return
            lote_data = lote_match.iloc[0]
            producto_lote = lote_data['Producto']
            costo_unitario_lote = lote_data['Costo_Unitario_KG']
            kg_producidos = lote_data['Kilos_Producidos']
            cantidad_envases_lote = float(lote_data.get('Cantidad_Envases', 0))
            gramaje_envase = float(lote_data.get('Gramaje_Por_Envase', 0))
            
            # Stock disponible
            kg_vendidos = df_v[df_v['Lote_Produccion'] == lote_sel]['Cantidad_Vendida_KG'].sum() if not df_v.empty else 0
            stock_disponible_kg = kg_producidos - kg_vendidos
            
            # Obtener código del producto desde la receta
            _rid_info = lote_data.get("Id_Receta")
            _receta_panel = df_r[df_r["Id"] == _rid_info]
            if _receta_panel.empty:
                _receta_panel = df_r[df_r["Nombre"].apply(lambda x: " ".join(str(x).lower().split())) == " ".join(str(producto_lote).lower().split())]
            codigo_producto = "—"
            if not _receta_panel.empty:
                _cod_val = _receta_panel.iloc[0].get("Codigo")
                codigo_producto = str(_cod_val) if pd.notna(_cod_val) and str(_cod_val).strip().lower() != "nan" else "—"
            
            fecha_produccion_lote = str(lote_data.get("Fecha_Produccion", ""))[:10]
            
            # Panel informativo completo: Código + Producto + Fecha
            st.info(f"**📦 {producto_lote}** &nbsp;&nbsp;|&nbsp;&nbsp; **🔖 Código:** `{codigo_producto}` &nbsp;&nbsp;|&nbsp;&nbsp; **📅 Producción:** {fecha_produccion_lote}")
            
            col_i1, col_i2, col_i3 = st.columns(3)
            col_i1.metric("🏷️ Costo/kg", f"${costo_unitario_lote:,.2f}")
            col_i2.metric("📊 Stock Disponible", f"{stock_disponible_kg:.3f} kg")
            if cantidad_envases_lote > 0:
                env_disp = int((stock_disponible_kg * 1000) / gramaje_envase) if gramaje_envase > 0 else 0
                col_i3.metric("🎁 Envases Disponibles", f"{env_disp} ({gramaje_envase}g)")
            else:
                col_i3.metric("🎁 Envases", "Sin fraccionar")

            # --- CARRITO DE VENTAS (MODO SHOWROOM) ---
            if "carrito" not in st.session_state:
                st.session_state["carrito"] = []

            # --- PANEL DE SELECCIÓN DE PRECIOS Y MODO ---
            st.markdown("#### 3. Configuración de Venta")
            col_li1, col_li2 = st.columns(2)
            tipo_lista = col_li1.radio("Lista de Precios", ["Minorista", "Mayorista"], horizontal=True, key="tipo_lista_v6")
            
            tiene_envases = cantidad_envases_lote > 0 and gramaje_envase > 0
            modo_venta = col_li2.radio("Modo de Venta", ["Por Envases", "Por Kilogramos"] if tiene_envases else ["Por Kilogramos"], horizontal=True, key="modo_venta_v6")
            
            # Obtener precios guardados de la receta usando el ID (más robusto que el nombre)
            rid_lote = lote_data.get("Id_Receta")
            receta_match = df_r[df_r["Id"] == rid_lote]
            
            if receta_match.empty:
                # Fallback por nombre si el ID falla por alguna razón (ej: lotes viejos sin ID)
                producto_lote_clean = " ".join(str(producto_lote).lower().split())
                receta_match = df_r[df_r["Nombre"].apply(lambda x: " ".join(str(x).lower().split())) == producto_lote_clean]
            
            if receta_match.empty:
                st.error(f"❌ No se encontró la receta original para el producto '{producto_lote}'. Verifique que no haya sido eliminada.")
                return

            receta_info = receta_match.iloc[0]
            p_min = float(receta_info.get("Precio_Venta", 0)) if pd.notna(receta_info.get("Precio_Venta")) else 0.0
            p_may = float(receta_info.get("Precio_Mayorista", 0)) if pd.notna(receta_info.get("Precio_Mayorista")) else 0.0
            
            # Sugerir precio base según lista
            p_sugerido_unit = p_min if tipo_lista == "Minorista" else p_may
            

            st.markdown("##### 🛒 Detalle del Producto")
            col_v1, col_v2 = st.columns(2)
            
            # KEY DINÁMICA: Si cambia el producto, el lote, la lista o el modo, el widget se REGENERA con el valor sugerido.
            key_suffix = f"{producto_lote}_{lote_sel}_{tipo_lista}_{modo_venta}"

            if vendedor_sel == "Rojo Malbec (Directo)":
                if modo_venta == "Por Envases":
                    v_env = col_v1.number_input("Cantidad de Envases", min_value=1, step=1, key=f"v_env_{key_suffix}")
                    v_p_unit_final = col_v2.number_input("Precio por Envase ($)", value=float(p_sugerido_unit), min_value=0.0, step=10.0, key=f"v_p_unit_{key_suffix}")
                    v_cant = (v_env * gramaje_envase) / 1000
                    v_p_kg_final = (v_p_unit_final * 1000 / gramaje_envase) if gramaje_envase > 0 else 0
                    v_desc = f"{v_env} envases de {gramaje_envase}g"
                    
                    precio_facturado_cliente = v_p_unit_final * v_env
                    comision_vendedor = 0.0
                    st.info(f"📋 **Desglose RM:** {v_env} un. x ${v_p_unit_final:,.2f} = **${precio_facturado_cliente:,.2f}**")
                else:
                    p_sugerido_kg = (p_sugerido_unit * 1000 / gramaje_envase) if gramaje_envase > 0 else 0
                    v_cant = col_v1.number_input("Cantidad (KG)", min_value=0.001, max_value=float(max(stock_disponible_kg, 0.001)), step=0.1, key=f"v_cant_kg_{key_suffix}")
                    v_p_kg_final = col_v2.number_input("Precio por KG ($)", value=float(p_sugerido_kg), min_value=0.0, step=10.0, key=f"v_pkg_{key_suffix}")
                    v_p_unit_final = v_p_kg_final
                    v_desc = f"{v_cant:.3f} KG"
                    
                    precio_facturado_cliente = v_p_kg_final * v_cant
                    comision_vendedor = 0.0
                    st.info(f"📋 **Desglose RM:** {v_cant:.3f} KG x ${v_p_kg_final:,.2f} = **${precio_facturado_cliente:,.2f}**")
            else:
                # MODO PREVENTISTA (Doble Precio)
                col_v1.empty(); col_v2.empty()
                c_a, c_b, c_c = st.columns(3)
                if modo_venta == "Por Envases":
                    v_env = c_a.number_input("Cant. Envases", min_value=1, step=1, key=f"v_env_{key_suffix}")
                    v_p_unit_final = c_b.number_input("Precio RM (Base)", value=float(p_sugerido_unit), help="Lo que rinde a Rojo Malbec", step=10.0, key=f"v_p_unit_{key_suffix}")
                    v_p_cliente = c_c.number_input("Precio Remito (Cliente)", value=float(p_sugerido_unit*1.3), help="Lo que se cobra al cliente", step=10.0, key=f"v_p_cli_{key_suffix}")
                    
                    v_cant = (v_env * gramaje_envase) / 1000
                    v_p_kg_final = (v_p_unit_final * 1000 / gramaje_envase) if gramaje_envase > 0 else 0
                    v_desc = f"{v_env} envases de {gramaje_envase}g"
                    
                    precio_facturado_cliente = v_p_cliente * v_env
                    ingreso_rm = v_p_unit_final * v_env
                    comision_vendedor = precio_facturado_cliente - ingreso_rm
                    st.info(f"📋 **Facturado:** ${precio_facturado_cliente:,.2f} | 🏭 **Para RM:** ${ingreso_rm:,.2f} | 🤝 **Comisión:** ${comision_vendedor:,.2f}")
                else:
                    p_sugerido_kg = (p_sugerido_unit * 1000 / gramaje_envase) if gramaje_envase > 0 else 0
                    v_cant = c_a.number_input("Cantidad (KG)", min_value=0.001, max_value=float(max(stock_disponible_kg, 0.001)), step=0.1, key=f"v_cant_kg_{key_suffix}")
                    v_p_kg_final = c_b.number_input("Precio Base KG", value=float(p_sugerido_kg), step=10.0, key=f"v_pkg_{key_suffix}")
                    v_p_cliente_kg = c_c.number_input("Precio Remito KG", value=float(p_sugerido_kg*1.3), step=10.0, key=f"v_p_cli_kg_{key_suffix}")
                    v_p_unit_final = v_p_kg_final
                    v_desc = f"{v_cant:.3f} KG"
                    
                    precio_facturado_cliente = v_p_cliente_kg * v_cant
                    ingreso_rm = v_p_kg_final * v_cant
                    comision_vendedor = precio_facturado_cliente - ingreso_rm
                    st.info(f"📋 **Facturado:** ${precio_facturado_cliente:,.2f} | 🏭 **Para RM:** ${ingreso_rm:,.2f} | 🤝 **Comisión:** ${comision_vendedor:,.2f}")

            item_subtotal = v_cant * v_p_kg_final # Ingreso para RM
            
            if st.button("➕ AGREGAR AL CARRITO", use_container_width=True, type="primary"):
                if v_cant > stock_disponible_kg:
                    st.error("Stock insuficiente.")
                elif v_cant > 0:
                    item_carrito = {
                        "Producto": producto_lote,
                        "Lote": lote_sel,
                        "Descripción": v_desc,
                        "Cant_KG": float(v_cant),
                        "Precio_Unit": float(v_p_unit_final),
                        "Precio_KG": float(v_p_kg_final),
                        "Subtotal": float(item_subtotal), # Para RM
                        "Costo_KG": float(costo_unitario_lote),
                        "Vendedor": vendedor_sel,
                        "Precio_Facturado_Cliente": float(precio_facturado_cliente),
                        "Comision_Vendedor": float(comision_vendedor),
                        "Estado_Comision": "Pagada" if vendedor_sel == "Rojo Malbec (Directo)" else "Pendiente"
                    }
                    st.session_state["carrito"].append(item_carrito)
                    st.toast(f"✅ {producto_lote} agregado")
                    st.rerun()
                else:
                    st.error("Verifique cantidad.")

            # --- VISTA DEL CARRITO ---
            if st.session_state["carrito"]:
                st.markdown("---")
                st.markdown(f"### 🧾 Resumen de Venta: {cliente_sel}")
                
                for i, item in enumerate(st.session_state["carrito"]):
                    col_it1, col_it2, col_it3, col_it4 = st.columns([2, 2, 1, 0.5])
                    col_it1.write(f"**{item['Producto']}**")
                    col_it2.write(f"{item['Descripción']}")
                    
                    # Mostrar el precio de cara al cliente
                    precio_mostrar = item.get("Precio_Facturado_Cliente", item["Subtotal"])
                    col_it3.write(f"**${precio_mostrar:,.2f}**")
                    
                    if col_it4.button("❌", key=f"del_cart_{i}"):
                        st.session_state["carrito"].pop(i)
                        st.rerun()

                df_cart = pd.DataFrame(st.session_state["carrito"])
                total_venta = df_cart["Precio_Facturado_Cliente"].sum() if "Precio_Facturado_Cliente" in df_cart.columns else df_cart["Subtotal"].sum()
                st.markdown(f"#### 💰 TOTAL A PAGAR (Cliente): **$ {total_venta:,.2f}**")
                
                col_acc1, col_acc2 = st.columns(2)
                
                if col_acc1.button("🗑️ Vaciar Carrito", use_container_width=True):
                    st.session_state["carrito"] = []
                    st.rerun()
                
                if col_acc2.button("🚀 CONFIRMAR VENTA COMPLETA", type="primary", use_container_width=True):
                    # FIX BUG #1: Remito_ID con timestamp (evita duplicados)
                    remito_id = f"REM-{datetime.now().strftime('%y%m%d-%H%M%S')}"
                    
                    nuevas_ventas = []
                    for item in st.session_state["carrito"]:
                        ganancia = item["Cant_KG"] * (item["Precio_KG"] - item["Costo_KG"])
                        nueva_v = {
                            "UUID": str(uuid.uuid4()),
                            "Remito_ID": remito_id,
                            "Lote_Produccion": item["Lote"],
                            "Cliente": cliente_sel,
                            "Forma_Pago": forma_pago,
                            "Cantidad_Vendida_KG": float(item["Cant_KG"]),
                            "Precio_Venta_Unitario_KG": float(item["Precio_KG"]),
                            "Precio_Total": float(item["Subtotal"]),
                            "Ganancia_Neta": float(ganancia),
                            "Fecha_Venta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Vendedor": item.get("Vendedor", "Rojo Malbec (Directo)"),
                            "Precio_Facturado_Cliente": item.get("Precio_Facturado_Cliente", float(item["Subtotal"])),
                            "Comision_Vendedor": item.get("Comision_Vendedor", 0.0),
                            "Estado_Comision": item.get("Estado_Comision", "N/A")
                        }
                        nuevas_ventas.append(nueva_v)
                    
                    # FIX BUG #2: Leer datos FRESCOS de Google Sheets (no session_state viejo)
                    append_data("ventas", pd.DataFrame(nuevas_ventas))
                    
                    # Forzar recarga del session_state para evitar rebote
                    st.session_state["ventas"] = load_data("ventas")
                    
                    st.success(f"✅ Venta registrada — **{remito_id}** — Total: $ {total_venta:,.2f}")
                    st.session_state["carrito"] = []
                    st.rerun()

    # 5.3. Reporte de Ganancias
    with tab_ganancia:
        c_tit, c_btn = st.columns([3, 1])
        with c_tit:
            st.markdown("### 📈 Reporte Comercial y Historial")
        with c_btn:
            st.link_button("🧾 Facturar en ARCA", "https://www.afip.gob.ar/", use_container_width=True)
        if not df_v.empty:
            df_rep = pd.merge(df_v, df_lp[['Lote_Produccion', 'Producto']], on='Lote_Produccion', how='left')
            
            # Métricas Premium
            c1, c2, c3, c4 = st.columns(4)
            total_ingresos = df_rep['Precio_Total'].sum()
            total_ganancia = df_rep['Ganancia_Neta'].sum()
            margen_promedio = (total_ganancia / total_ingresos * 100) if total_ingresos > 0 else 0
            
            c1.metric("Ingresos Totales", f"$ {total_ingresos:,.2f}")
            c2.metric("Ganancia Neta", f"$ {total_ganancia:,.2f}")
            c3.metric("Margen Promedio", f"{margen_promedio:,.1f}%")
            c4.metric("Ventas Totales", len(df_rep))
            
            # Agregar columnas nuevas si no existen (retrocompatibilidad)
            if "Precio_Facturado_Cliente" not in df_rep.columns:
                df_rep["Precio_Facturado_Cliente"] = df_rep["Precio_Total"]
            if "Comision_Vendedor" not in df_rep.columns:
                df_rep["Comision_Vendedor"] = 0.0
            if "Vendedor" not in df_rep.columns:
                df_rep["Vendedor"] = "Rojo Malbec (Directo)"
                
            # --- PANEL DE LIQUIDACIÓN DE COMISIONES ---
            st.divider()
            st.markdown("#### 🤝 Liquidación de Vendedores")
            df_comisiones = df_rep[df_rep["Vendedor"] != "Rojo Malbec (Directo)"]
            if not df_comisiones.empty:
                liq = df_comisiones.groupby("Vendedor").agg(
                    Ventas_Totales_Facturadas=('Precio_Facturado_Cliente', 'sum'),
                    Ingreso_RM=('Precio_Total', 'sum'),
                    Comision_Total=('Comision_Vendedor', 'sum')
                ).reset_index()
                
                st.dataframe(liq.style.format({
                    'Ventas_Totales_Facturadas': '${:,.2f}',
                    'Ingreso_RM': '${:,.2f}',
                    'Comision_Total': '${:,.2f}'
                }), use_container_width=True, hide_index=True)
            else:
                st.info("No hay ventas registradas por preventistas externos todavía.")
            
            st.divider()
            st.markdown("#### 📄 Historial de Remitos")
            st.info("Cada remito agrupa todos los productos vendidos en una misma transacción. Puede anular remitos completos o descargar el PDF.")

            # Asignar Remito_ID a ventas antiguas que no lo tengan
            if "Remito_ID" not in df_rep.columns:
                df_rep["Remito_ID"] = ""
            df_rep["Remito_ID"] = df_rep["Remito_ID"].fillna("").astype(str)
            # Ventas sin remito: agrupar por Cliente + Fecha_Venta como fallback
            sin_remito = df_rep[df_rep["Remito_ID"].isin(["", "nan"])].copy()
            if not sin_remito.empty:
                sin_remito["Remito_ID"] = sin_remito.apply(
                    lambda r: f"PRE-{r['Cliente'][:3].upper()}-{str(r['Fecha_Venta'])[:10].replace('-','')}", axis=1
                )
                df_rep.update(sin_remito)
            
            # Agrupar por Remito_ID
            remitos = df_rep.groupby("Remito_ID").agg(
                Cliente=('Cliente', 'first'),
                Vendedor=('Vendedor', 'first'),
                Forma_Pago=('Forma_Pago', 'first'),
                Fecha=('Fecha_Venta', 'first'),
                Total_Ingreso_RM=('Precio_Total', 'sum'),
                Total_Facturado=('Precio_Facturado_Cliente', 'sum'),
                Comision_Remito=('Comision_Vendedor', 'sum'),
                Ganancia=('Ganancia_Neta', 'sum'),
                Kg_Total=('Cantidad_Vendida_KG', 'sum'),
                Cant_Items=('UUID', 'count')
            ).sort_values("Fecha", ascending=False).reset_index()
            
            for _, rem in remitos.iterrows():
                rem_id = rem["Remito_ID"]
                fecha_corta = str(rem['Fecha'])[:16]
                
                vendedor_badge = f"👤 {rem['Vendedor']}"
                
                with st.expander(f"📄 **{rem_id}** — {rem['Cliente']} — {fecha_corta} — {rem['Cant_Items']} items — **${rem['Total_Facturado']:,.2f}**"):
                    # Detalle de items del remito
                    items_rem = df_rep[df_rep["Remito_ID"] == rem_id].copy()
                    
                    st.markdown(f"**Cliente:** {rem['Cliente']} &nbsp;&nbsp;|&nbsp;&nbsp; {vendedor_badge} &nbsp;&nbsp;|&nbsp;&nbsp; **Pago:** {rem['Forma_Pago']} &nbsp;&nbsp;|&nbsp;&nbsp; **Fecha:** {fecha_corta}")
                    st.markdown("---")
                    
                    # Tabla de productos
                    for _, item in items_rem.iterrows():
                        prod_name = str(item.get('Producto', '—'))
                        prod_name_limpio = " ".join(prod_name.lower().split())
                        
                        # Buscar Gramaje para envases
                        lote_prod = str(item.get('Lote_Produccion', ''))
                        df_lp_match = df_lp[df_lp['Lote_Produccion'] == lote_prod]
                        gramaje = 1000
                        if not df_lp_match.empty:
                            g_val = df_lp_match.iloc[0].get('Gramaje_Por_Envase', 0)
                            if pd.notna(g_val) and float(g_val) > 0:
                                gramaje = float(g_val)
                                
                        # Buscar Código de Barra
                        df_r_match = df_r[df_r['Nombre'].apply(lambda x: " ".join(str(x).lower().split())) == prod_name_limpio]
                        codigo_barra = ""
                        if not df_r_match.empty:
                            c_val = df_r_match.iloc[0].get('Codigo', '')
                            if pd.notna(c_val) and str(c_val).strip() != 'nan':
                                codigo_barra = str(c_val).strip()
                        if not codigo_barra:
                            codigo_barra = f"L {prod_name[:4].upper()}"
                            
                        # Calcular envases
                        kg_totales = float(item['Cantidad_Vendida_KG'])
                        envases = int(round((kg_totales * 1000) / gramaje)) if gramaje > 0 else 0
                        if envases == 0: envases = 1
                        
                        col_p, col_c, col_e, col_t = st.columns([3, 2, 1, 1])
                        col_p.write(f"**{prod_name}**")
                        col_c.write(f"Cód: `{codigo_barra}`")
                        col_e.write(f"{envases} un.")
                        precio_item = item.get('Precio_Facturado_Cliente', item['Precio_Total'])
                        col_t.write(f"${precio_item:,.2f}")
                    
                    st.markdown("---")
                    
                    # Totales del remito (Nueva lógica 3 renglones)
                    if rem['Comision_Remito'] > 0:
                        st.info(f"🧾 **Total Facturado al Cliente:** ${rem['Total_Facturado']:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp; 🏭 **Ingreso RM:** ${rem['Total_Ingreso_RM']:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp; 🤝 **Comisión Vendedor:** ${rem['Comision_Remito']:,.2f}")
                    else:
                        st.info(f"🧾 **Total Facturado / Ingreso RM:** ${rem['Total_Facturado']:,.2f}")
                        
                    col_tot1, col_tot2 = st.columns(2)
                    col_tot1.metric("📦 Total KG", f"{rem['Kg_Total']:.3f} kg")
                    col_tot2.metric("📈 Ganancia Neta RM", f"${rem['Ganancia']:,.2f}")
                    
                    # Botones de acción
                    col_btn1, col_btn2 = st.columns(2)
                    
                    # Botón PDF
                    if FPDF is not None:
                        if col_btn1.button("📥 Descargar Remito PDF", key=f"pdf_{rem_id}", use_container_width=True):
                            try:
                                pdf = FPDF()
                                pdf.add_page()
                                pdf.set_auto_page_break(auto=True, margin=15)
                                
                                # Encabezado
                                pdf.set_font('Helvetica', 'B', 14)
                                pdf.cell(190, 8, _clean_pdf_text('Andrea Vanina Garcia'), ln=True, align='C')
                                pdf.set_font('Helvetica', 'B', 11)
                                pdf.cell(190, 6, _clean_pdf_text('Rojo Malbec - Sales & Blends de Especias y Tes'), ln=True, align='C')
                                pdf.set_font('Helvetica', '', 10)
                                pdf.cell(190, 5, _clean_pdf_text('CUIT: 27-28101369-1 | RNE: 04006325'), ln=True, align='C')
                                pdf.cell(190, 5, _clean_pdf_text('Ruta 14 s/n, CP. 5885, Los Hornillos - Cordoba'), ln=True, align='C')
                                pdf.ln(5)
                                
                                # Info remito
                                pdf.set_font('Helvetica', 'B', 12)
                                pdf.cell(190, 8, _clean_pdf_text(f'Remito: {rem_id}'), ln=True)
                                pdf.set_font('Helvetica', '', 11)
                                pdf.cell(95, 6, _clean_pdf_text(f'Cliente: {rem["Cliente"]}'))
                                pdf.cell(95, 6, _clean_pdf_text(f'Fecha: {fecha_corta}'), ln=True)
                                pdf.cell(95, 6, _clean_pdf_text(f'Forma de Pago: {rem["Forma_Pago"]}'))
                                pdf.ln(8)
                                
                                # Tabla header (190 total width)
                                pdf.set_font('Helvetica', 'B', 9)
                                pdf.set_fill_color(200, 200, 200)
                                pdf.cell(60, 8, 'Producto', 1, 0, 'C', True)
                                pdf.cell(40, 8, 'Cod. Barra', 1, 0, 'C', True)
                                pdf.cell(20, 8, 'Cant.', 1, 0, 'C', True)
                                pdf.cell(30, 8, 'P. Unitario', 1, 0, 'C', True)
                                pdf.cell(40, 8, 'Total', 1, 1, 'C', True)
                                
                                # Tabla body
                                pdf.set_font('Helvetica', '', 9)
                                for _, item in items_rem.iterrows():
                                    prod_name = str(item.get('Producto', ''))
                                    prod_name_limpio = " ".join(prod_name.lower().split())
                                    
                                    # Buscar Gramaje en df_lp para calcular envases
                                    lote_prod = str(item.get('Lote_Produccion', ''))
                                    df_lp_match = df_lp[df_lp['Lote_Produccion'] == lote_prod]
                                    gramaje = 1000 # default a 1kg si no encuentra
                                    if not df_lp_match.empty:
                                        g_val = df_lp_match.iloc[0].get('Gramaje_Por_Envase', 0)
                                        if pd.notna(g_val) and float(g_val) > 0:
                                            gramaje = float(g_val)
                                    
                                    # Buscar Codigo de Barras en df_r
                                    df_r_match = df_r[df_r['Nombre'].apply(lambda x: " ".join(str(x).lower().split())) == prod_name_limpio]
                                    codigo_barra = ""
                                    if not df_r_match.empty:
                                        c_val = df_r_match.iloc[0].get('Codigo', '')
                                        if pd.notna(c_val) and str(c_val).strip() != 'nan':
                                            codigo_barra = str(c_val).strip()
                                            
                                    if not codigo_barra:
                                        codigo_barra = f"L {prod_name[:4].upper()}" # Fallback
                                    
                                    # Calculos
                                    kg_totales = float(item['Cantidad_Vendida_KG'])
                                    envases = int(round((kg_totales * 1000) / gramaje)) if gramaje > 0 else 0
                                    if envases == 0: envases = 1 # Fallback de seguridad
                                    
                                    total_importe = float(item.get('Precio_Facturado_Cliente', item['Precio_Total']))
                                    p_unit = total_importe / envases
                                    
                                    pdf.cell(60, 7, _clean_pdf_text(prod_name[:30]), 1)
                                    pdf.cell(40, 7, _clean_pdf_text(codigo_barra[:18]), 1, 0, 'C')
                                    pdf.cell(20, 7, f"{envases} un", 1, 0, 'C')
                                    pdf.cell(30, 7, f"$ {p_unit:,.2f}", 1, 0, 'R')
                                    pdf.cell(40, 7, f"$ {total_importe:,.2f}", 1, 1, 'R')
                                
                                # Total
                                pdf.set_font('Helvetica', 'B', 11)
                                pdf.cell(150, 8, 'TOTAL', 1, 0, 'R')
                                pdf.cell(40, 8, f"$ {rem['Total_Facturado']:,.2f}", 1, 1, 'R')
                                pdf.ln(10)
                                
                                # Firma
                                pdf.set_font('Helvetica', '', 9)
                                pdf.cell(95, 6, '________________________')
                                pdf.cell(95, 6, '________________________', ln=True)
                                pdf.cell(95, 6, 'Firma Vendedor', 0, 0, 'C')
                                pdf.cell(95, 6, 'Firma Cliente', 0, 1, 'C')
                                
                                pdf_output = pdf.output()
                                pdf_bytes = bytes(pdf_output) if not isinstance(pdf_output, bytes) else pdf_output
                                st.download_button(
                                    "⬇️ Descargar PDF",
                                    data=pdf_bytes,
                                    file_name=f"{rem_id}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_{rem_id}"
                                )
                            except Exception as e:
                                st.error(f"Error generando PDF del remito: {e}")
                    
                    # Botón anular remito completo
                    if col_btn2.button("🗑️ Anular Remito Completo", key=f"del_rem_{rem_id}", type="secondary", use_container_width=True):
                        uuids_remito = items_rem['UUID'].tolist()
                        df_v_new = df_v[~df_v['UUID'].isin(uuids_remito)]
                        save_data("ventas", df_v_new)
                        st.success(f"Remito {rem_id} anulado. Se devolvieron los kg al stock.")
                        st.rerun()
        else:
            st.info("No hay ventas registradas aún.")
