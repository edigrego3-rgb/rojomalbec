
# views/inventario.py
import streamlit as st
import pandas as pd
from modules.data_manager import get_df, save_data

def render_inventario_tab():
    st.subheader("📦 Inventario de Productos Terminados")
    
    df_lp = get_df("lotes_produccion")
    df_v = get_df("ventas")
    df_r = get_df("recetas")
    
    if df_lp.empty:
        st.info("No hay lotes de producción registrados. Vaya a la Pestaña 3 para producir.")
        return
    
    # Asegurar que las columnas de envases existan (para lotes antiguos)
    if "Cantidad_Envases" not in df_lp.columns:
        df_lp["Cantidad_Envases"] = 0.0
    if "Gramaje_Por_Envase" not in df_lp.columns:
        df_lp["Gramaje_Por_Envase"] = 0.0
    
    # Llenar NaN con 0
    df_lp["Cantidad_Envases"] = pd.to_numeric(df_lp["Cantidad_Envases"], errors='coerce').fillna(0)
    df_lp["Gramaje_Por_Envase"] = pd.to_numeric(df_lp["Gramaje_Por_Envase"], errors='coerce').fillna(0)
    
    tab_resumen, tab_detalle, tab_trazabilidad, tab_editar = st.tabs([
        "📊 Resumen por Producto", 
        "📋 Detalle por Lote", 
        "🔍 Trazabilidad ANMAT",
        "✏️ Completar Lotes Antiguos"
    ])
    
    # =============================================
    # TAB 1: RESUMEN POR PRODUCTO
    # =============================================
    with tab_resumen:
        st.markdown("### Stock Disponible por Producto")
        
        # FIX BUG #5: Calcular frascos disponibles LOTE POR LOTE (sin promediar gramaje)
        # 1. Calcular KG vendidos por lote
        ventas_kg_por_lote = df_v.groupby("Lote_Produccion")["Cantidad_Vendida_KG"].sum().to_dict() if not df_v.empty else {}
        
        # 2. Calcular por cada lote: KG disponibles y frascos disponibles (con SU gramaje)
        df_lp["KG_Vendidos"] = df_lp["Lote_Produccion"].map(ventas_kg_por_lote).fillna(0)
        df_lp["KG_Disponibles"] = df_lp["Kilos_Producidos"] - df_lp["KG_Vendidos"]
        
        def calc_frascos_lote(row):
            gramaje = float(row.get("Gramaje_Por_Envase", 0))
            kg_disp = float(row.get("KG_Disponibles", 0))
            if gramaje > 0 and kg_disp > 0:
                return int((kg_disp * 1000) / gramaje)
            return 0
        
        df_lp["Envases_Disponibles"] = df_lp.apply(calc_frascos_lote, axis=1)
        df_lp["Valor_Lote"] = df_lp["KG_Disponibles"] * df_lp["Costo_Unitario_KG"]
        
        # 3. Agrupar por producto: SUMAR frascos y kilos reales (NO promediar gramaje)
        resumen = df_lp.groupby("Producto").agg({
            "Envases_Disponibles": "sum",
            "KG_Disponibles": "sum",
            "Valor_Lote": "sum",
            "Gramaje_Por_Envase": "first"  # Solo para referencia visual (gramaje del lote más reciente)
        }).reset_index()
        
        resumen = resumen.rename(columns={"KG_Disponibles": "Stock_KG", "Valor_Lote": "Valor_Stock"})
        
        # Mostrar métricas principales
        col1, col2, col3, col4 = st.columns(4)
        total_envases = resumen["Envases_Disponibles"].sum()
        total_kg = resumen["Stock_KG"].sum()
        total_valor = resumen["Valor_Stock"].sum()
        productos_con_stock = len(resumen[resumen["Envases_Disponibles"] > 0])
        
        col1.metric("📦 Total Envases Disponibles", f"{total_envases:,.0f}")
        col2.metric("⚖️ Total Stock (KG)", f"{total_kg:,.2f} kg")
        col3.metric("💰 Valor Total Stock", f"$ {total_valor:,.2f}")
        col4.metric("🏷️ Productos con Stock", f"{productos_con_stock}")
        
        st.markdown("---")
        
        # Tabla resumen
        st.dataframe(
            resumen[["Producto", "Envases_Disponibles", "Stock_KG", "Valor_Stock"]].style.format({
                "Envases_Disponibles": "{:.0f} env",
                "Stock_KG": "{:.2f} kg",
                "Valor_Stock": "$ {:,.2f}"
            }),
            use_container_width=True,
            column_config={
                "Producto": "Producto",
                "Envases_Disponibles": st.column_config.NumberColumn("Envases en Stock"),
                "Stock_KG": st.column_config.NumberColumn("Kilos en Stock"),
                "Valor_Stock": st.column_config.NumberColumn("Valuación (Costo)")
            }
        )
        
        # Alertas de stock bajo
        st.markdown("### ⚠️ Alertas de Stock")
        sin_stock = resumen[resumen["Envases_Disponibles"] <= 0]
        if not sin_stock.empty:
            st.error(f"**{len(sin_stock)} producto(s) sin stock:** {', '.join(sin_stock['Producto'].tolist())}")
        else:
            st.success("✅ Todos los productos tienen stock disponible")
    
    # =============================================
    # TAB 2: DETALLE POR LOTE
    # =============================================
    with tab_detalle:
        st.markdown("### Detalle de Lotes de Producción")
        
        # Filtro por producto
        productos = ["Todos"] + sorted(df_lp["Producto"].unique().tolist())
        producto_sel = st.selectbox("Filtrar por Producto", productos)
        
        df_mostrar = df_lp.copy()
        if producto_sel != "Todos":
            df_mostrar = df_mostrar[df_mostrar["Producto"] == producto_sel]
        
        # Ordenar por fecha más reciente
        df_mostrar = df_mostrar.sort_values("Fecha_Produccion", ascending=False)
        
        st.dataframe(
            df_mostrar[["Lote_Produccion", "Producto", "Fecha_Produccion", "Cantidad_Envases", 
                        "Gramaje_Por_Envase", "Kilos_Producidos", "Costo_Unitario_KG"]].style.format({
                "Cantidad_Envases": "{:.0f}",
                "Gramaje_Por_Envase": "{:.0f} g",
                "Kilos_Producidos": "{:.3f} kg",
                "Costo_Unitario_KG": "$ {:.4f}"
            }),
            use_container_width=True,
            column_config={
                "Lote_Produccion": "Código Lote",
                "Producto": "Producto",
                "Fecha_Produccion": "Fecha Producción",
                "Cantidad_Envases": st.column_config.NumberColumn("Envases", help="Cantidad de envases producidos"),
                "Gramaje_Por_Envase": st.column_config.NumberColumn("Gramaje", help="Gramos por envase"),
                "Kilos_Producidos": st.column_config.NumberColumn("Kilos", help="Kilos totales producidos"),
                "Costo_Unitario_KG": st.column_config.NumberColumn("Costo/KG", help="Costo por kilo")
            }
        )
        
        # --- EXPORTACIÓN DE ETIQUETAS PNG ---
        st.markdown("---")
        st.subheader("🖨️ Generar Etiqueta de Lote (PNG)")
        st.caption("Seleccioná un lote de la tabla para descargar su etiqueta en formato imagen.")
        
        if not df_mostrar.empty:
            lotes_list = df_mostrar["Lote_Produccion"].unique()
            lote_seleccionado = st.selectbox("Lote a Imprimir:", lotes_list)
            
            if lote_seleccionado:
                lote_data = df_mostrar[df_mostrar["Lote_Produccion"] == lote_seleccionado].iloc[0]
                fecha_elab_str = str(lote_data.get("Fecha_Produccion", ""))[:10]
                
                try:
                    fecha_obj = pd.to_datetime(fecha_elab_str)
                    mes_elab = f"{fecha_obj.month:02d}/{fecha_obj.year}"
                    mes_vto = f"{fecha_obj.month:02d}/{fecha_obj.year + 1}"
                except:
                    mes_elab = "S/D"
                    mes_vto = "S/D"
                
                from modules.etiquetas_png import generar_etiqueta_lote_png
                png_data = generar_etiqueta_lote_png("RNE: 04006325 - RNPA E/T.", lote_seleccionado, mes_elab, mes_vto)
                
                if png_data:
                    st.download_button(
                        label="🖼️ Descargar Etiqueta (PNG)",
                        data=png_data,
                        file_name=f"Etiqueta_{lote_seleccionado}.png",
                        mime="image/png",
                        type="primary"
                    )

        # --- EXPORTACIÓN PARA INKJET ---
        st.markdown("---")
        st.subheader("📥 Exportar Lista para Impresora Inkjet (ASJet)")
        st.caption("Genera un CSV con Lote (incluye RNE/RNPA), Elaboración y Vencimiento (12 meses).")
        
        from modules.data_manager import prepare_inkjet_export
        # Usamos los datos filtrados (df_mostrar) para generar el texto
        txt_content = prepare_inkjet_export(df_mostrar)
        
        if txt_content:
            st.download_button(
                label="⬇️ Descargar TXT para ASJet",
                data=txt_content,
                file_name=f"lotes_asjet_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                help="Copiá este archivo .txt al pendrive para la impresora Asjet."
            )
            
            with st.expander("Ver vista previa del texto"):
                st.code(txt_content)
    
    # =============================================
    # TAB 3: TRAZABILIDAD ANMAT
    # =============================================
    with tab_trazabilidad:
        st.markdown("### 🔍 Trazabilidad ANMAT - Lotes de Ingredientes por Producción")
        st.info("Seleccione un lote de producción para ver qué lotes de ingredientes se usaron.")
        
        df_traz = get_df("lotes_produccion_det")
        
        if df_traz.empty:
            st.warning("⚠️ No hay datos de trazabilidad registrados. Los lotes producidos a partir de ahora incluirán esta información.")
        else:
            # Selector de lote
            lotes_con_traz = df_traz["Lote_Produccion"].unique().tolist()
            lote_sel_traz = st.selectbox("Seleccionar Lote de Producción", sorted(lotes_con_traz, reverse=True))
            
            if lote_sel_traz:
                # Mostrar info del lote
                lote_info = df_lp[df_lp["Lote_Produccion"] == lote_sel_traz]
                if not lote_info.empty:
                    info = lote_info.iloc[0]
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Producto", info["Producto"])
                    col_b.metric("Kilos Producidos", f"{info['Kilos_Producidos']:.3f} kg")
                    col_c.metric("Fecha", str(info["Fecha_Produccion"])[:10])
                
                st.markdown("---")
                st.markdown("#### Ingredientes Usados y sus Lotes de Origen:")
                
                # Mostrar detalle de trazabilidad
                df_detalle = df_traz[df_traz["Lote_Produccion"] == lote_sel_traz].copy()
                
                st.dataframe(
                    df_detalle[["Ingrediente", "Cantidad_Usada", "Unidad_Base", "Lote_Proveedor", "Fecha_Vencimiento"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Ingrediente": "Ingrediente",
                        "Cantidad_Usada": st.column_config.NumberColumn("Cantidad", format="%.3f"),
                        "Unidad_Base": "Unidad",
                        "Lote_Proveedor": "Lote Proveedor",
                        "Fecha_Vencimiento": "Vencimiento"
                    }
                )
                
                # Resumen para imprimir
                with st.expander("📄 Ver en formato para imprimir"):
                    st.markdown(f"### Trazabilidad Lote: {lote_sel_traz}")
                    if not lote_info.empty:
                        st.markdown(f"**Producto:** {info['Producto']}  \n**Fecha:** {info['Fecha_Produccion']}  \n**Cantidad:** {info['Kilos_Producidos']:.3f} kg")
                    st.markdown("---")
                    st.markdown("**Ingredientes utilizados:**")
                    for _, row in df_detalle.iterrows():
                        venc = row['Fecha_Vencimiento'] if row['Fecha_Vencimiento'] else 'N/A'
                        st.markdown(f"- {row['Ingrediente']}: {row['Cantidad_Usada']:.3f} {row['Unidad_Base']} → Lote: **{row['Lote_Proveedor']}** (Venc: {venc})")
    
    # =============================================
    # TAB 4: COMPLETAR LOTES ANTIGUOS
    # =============================================
    with tab_editar:
        st.markdown("### ✏️ Corregir Información de Lotes")
        st.info("Use esta sección para ajustar datos de lotes mal registrados o completar información faltante.")
        
        lote_sel = st.selectbox("Seleccionar Lote a Corregir", df_lp["Lote_Produccion"].tolist())
        
        if lote_sel:
            lote_match = df_lp[df_lp["Lote_Produccion"] == lote_sel]
            if lote_match.empty:
                st.warning("No se encontró información del lote seleccionado.")
                return
            lote_info = lote_match.iloc[0]
            
            # Formulario de corrección manual
            with st.form("form_corregir_lote"):
                st.markdown(f"**Lote:** {lote_sel} | **Producto:** {lote_info['Producto']}")
                
                col1, col2 = st.columns(2)
                # Si el usuario cambia los kilos, recalculamos el total para que sea transparente
                n_kilos = col1.number_input("Kilos Producidos Reales", value=float(lote_info['Kilos_Producidos']), format="%.3f")
                n_costo_kg = col2.number_input("Costo Unitario Real ($/KG)", value=float(lote_info['Costo_Unitario_KG']), format="%.2f")
                
                col3, col4 = st.columns(2)
                n_envases = col3.number_input("Cantidad de Envases", value=int(lote_info['Cantidad_Envases']), step=1)
                n_gramaje = col4.number_input("Gramaje por Envase (g)", value=float(lote_info['Gramaje_Por_Envase']), step=1.0)
                
                submitted = st.form_submit_button("💾 ACTUALIZAR DATOS DEL LOTE", type="primary")
                
                if submitted:
                    df_lp_current = get_df("lotes_produccion")
                    idx = df_lp_current[df_lp_current["Lote_Produccion"] == lote_sel].index[0]
                    
                    df_lp_current.at[idx, "Kilos_Producidos"] = n_kilos
                    df_lp_current.at[idx, "Costo_Unitario_KG"] = n_costo_kg
                    df_lp_current.at[idx, "Costo_Total_MateriaPrima"] = n_kilos * n_costo_kg
                    df_lp_current.at[idx, "Cantidad_Envases"] = n_envases
                    df_lp_current.at[idx, "Gramaje_Por_Envase"] = n_gramaje
                    
                    save_data("lotes_produccion", df_lp_current)
                    st.success(f"✅ Lote {lote_sel} actualizado: {n_kilos}kg a ${n_costo_kg}/kg.")
                    st.rerun()

            st.divider()
            
            # Herramienta de Recálculo Automático
            st.markdown("#### 🔄 Herramienta de Recálculo Teórico")
            st.markdown("Si el lote se registró con un costo erróneo (ej. $3/kg), use este botón para calcular lo que **debería** costar según los precios actuales de los ingredientes.")
            
            if st.button("Calcular Costo Teórico según Receta"):
                from modules.conversions import convertir_a_base
                # 1. Obtener datos necesarios
                rid = lote_info['Id_Receta']
                df_rd = get_df("recetas_det")
                df_r = get_df("recetas")
                df_i = get_df("ingredientes")
                
                r_match = df_r[df_r["Id"] == rid]
                if r_match.empty:
                    st.error("No se encontró la receta base.")
                    return
                r_data = r_match.iloc[0]
                base_g = r_data["Base_g"]
                # Usamos los kilos actuales del lote para el factor
                kilos_lote = float(lote_info['Kilos_Producidos'])
                if kilos_lote == 0: kilos_lote = 1.0 # Evitar división por cero
                
                factor = (kilos_lote * 1000) / base_g if base_g > 0 else 1
                detalles = df_rd[df_rd["Id_Receta"] == rid]
                cpp_map = df_i.set_index("Nombre")["Costo"].to_dict()
                
                nuevo_costo_total = 0
                for _, req in detalles.iterrows():
                    ing = req["Ingrediente"]
                    cant_base = convertir_a_base(req["Cantidad"] * factor, str(req["Unidad_Consumo"]).lower())
                    precio_ing = cpp_map.get(ing, 0.0)
                    nuevo_costo_total += cant_base * precio_ing
                
                nuevo_costo_unit = nuevo_costo_total / kilos_lote
                
                st.session_state['nuevo_costo_calc'] = {
                    'lote': lote_sel,
                    'unit': nuevo_costo_unit,
                    'total': nuevo_costo_total
                }

            if 'nuevo_costo_calc' in st.session_state and st.session_state['nuevo_costo_calc']['lote'] == lote_sel:
                calc = st.session_state['nuevo_costo_calc']
                st.warning(f"Costo Teórico Calculado: **${calc['unit']:,.2f} / KG** (Total: ${calc['total']:,.2f})")
                
                if st.button("CONFIRMAR Y APLICAR ESTE COSTO AL LOTE"):
                    df_lp_current = get_df("lotes_produccion")
                    idx = df_lp_current[df_lp_current["Lote_Produccion"] == lote_sel].index[0]
                    df_lp_current.at[idx, "Costo_Unitario_KG"] = calc['unit']
                    df_lp_current.at[idx, "Costo_Total_MateriaPrima"] = calc['total']
                    save_data("lotes_produccion", df_lp_current)
                    
                    del st.session_state['nuevo_costo_calc']
                    st.success("✅ Costo actualizado con éxito.")
                    st.rerun()
                
                if st.button("Cancelar Recálculo"):
                    del st.session_state['nuevo_costo_calc']
                    st.rerun()

            st.divider()
            
            # ZONA DE PELIGRO: Eliminar Lote
            st.markdown("#### ⚠️ Zona de Peligro: Eliminar Lote")
            st.error("¡Atención! Eliminar un lote es una acción irreversible.")
            
            # Verificar si tiene ventas
            df_v = get_df("ventas")
            ventas_lote = df_v[df_v["Lote_Produccion"] == lote_sel]
            
            if not ventas_lote.empty:
                st.warning(f"No se puede eliminar el lote **{lote_sel}** porque ya tiene {len(ventas_lote)} ventas registradas. Debe anular las ventas primero.")
            else:
                col_del1, col_del2 = st.columns(2)
                
                if col_del1.button("🔥 ELIMINAR LOTE (SIN REVERTIR STOCK)", help="Solo borra el lote del inventario, los ingredientes consumidos NO vuelven al stock."):
                    df_lp_current = get_df("lotes_produccion")
                    df_lp_current = df_lp_current[df_lp_current["Lote_Produccion"] != lote_sel]
                    save_data("lotes_produccion", df_lp_current)
                    st.success(f"Lote {lote_sel} eliminado.")
                    st.rerun()
                
                if col_del2.button("⏪ ELIMINAR Y REVERTIR CONSUMO STOCK", type="primary", help="Borra el lote y DEVUELVE los ingredientes al stock (borrando los consumos asociados)."):
                    # 1. Borrar Stock Log (Salidas asociadas a este lote)
                    df_sl_current = get_df("stock_log")
                    df_sl_current = df_sl_current[~((df_sl_current["Lote_Proveedor"] == lote_sel) & (df_sl_current["Tipo_Movimiento"] == "SALIDA"))]
                    save_data("stock_log", df_sl_current)
                    
                    # 2. Borrar Trazabilidad
                    df_traz_current = get_df("lotes_produccion_det")
                    df_traz_current = df_traz_current[df_traz_current["Lote_Produccion"] != lote_sel]
                    save_data("lotes_produccion_det", df_traz_current)
                    
                    # 3. Borrar Lote de Producción
                    df_lp_current = get_df("lotes_produccion")
                    df_lp_current = df_lp_current[df_lp_current["Lote_Produccion"] != lote_sel]
                    save_data("lotes_produccion", df_lp_current)
                    
                    st.success(f"✅ Lote {lote_sel} eliminado y stock de materiales restaurado.")
                    st.rerun()
