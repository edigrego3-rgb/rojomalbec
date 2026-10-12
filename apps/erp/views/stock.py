
# views/stock.py
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from modules.data_manager import get_df, save_data, calcular_stock_actual
from modules.conversions import get_conversion_factor, ajustar_unidad_para_display, UNIDADES_CONSUMO
import re

def parse_input_number(s):
    """
    Parsea un string a float, manejando formatos locales (1.000,50) y texto extra.
    Ejemplos:
    - "2.250" -> 2.25 (Float nativo)
    - "2,250" -> 2.25 (Decimal con coma)
    - "2.250,00" -> 2250.0 (Miles con punto, decimal con coma)
    - "2.250 litros" -> 2.25 (Ignora 'litros')
    """
    if not s:
        return 0.0
    s = str(s).strip()
    
    # Eliminar texto no numérico (conservar dígitos, punto, coma, menos)
    s_clean = re.sub(r'[^\d.,-]', '', s)
    
    if not s_clean:
        return 0.0

    # Lógica heurística para determinar formato
    if '.' in s_clean and ',' in s_clean:
        last_dot = s_clean.rfind('.')
        last_comma = s_clean.rfind(',')
        
        if last_comma > last_dot: 
            # Formato 1.000,50 (Español/Latam)
            s_clean = s_clean.replace('.', '').replace(',', '.')
        else:
            # Formato 1,000.50 (US)
            s_clean = s_clean.replace(',', '')
            
    elif ',' in s_clean:
        # Solo hay coma, asumir decimal (1,5)
        s_clean = s_clean.replace(',', '.')
        
    try:
        return float(s_clean)
    except ValueError:
        return 0.0


def render_stock_tab():
    st.subheader("📦 Gestión de Stock, Entradas (Compras) y Proveedores")

    df_i = get_df("ingredientes")
    df_p = get_df("proveedores")
    df_sl = get_df("stock_log")
    
    tab_p, tab_e, tab_s, tab_h, tab_log = st.tabs([
        "👥 Proveedores", 
        "🚚 Registrar Compra (ENTRADA)", 
        "📊 Reporte de Stock", 
        "📜 Historial por Proveedor",
        "🕒 Log de Movimientos"
    ])

    # 4.1. Módulo de Proveedores
    with tab_p:
        st.markdown("### 👥 Alta de Proveedores")
        col_new_p, col_list_p = st.columns([1, 2])
        
        with col_new_p:
            with st.form("form_crear_proveedor"):
                p_nom = st.text_input("Nombre del Proveedor").strip()
                p_cuit = st.text_input("CUIT/Identificación")
                
                if st.form_submit_button("Crear Proveedor"):
                    if p_nom:
                        max_id = df_p["Id"].max() if not df_p.empty else 0
                        new_id = max_id + 1 if max_id > 0 else 1
                        
                        new_prov = pd.DataFrame([{"Id": float(new_id), "Nombre": p_nom, "CUIT": p_cuit}])
                        save_data("proveedores", pd.concat([df_p, new_prov], ignore_index=True))
                        st.success("Proveedor creado.")
                        st.rerun()
                    else:
                        st.error("El nombre del proveedor no puede estar vacío.")

        with col_list_p:
            st.markdown("#### Lista de Proveedores Actuales")
            st.dataframe(df_p.drop(columns=['Id']), hide_index=True, use_container_width=True)

    
    # 4.2. Módulo de Entrada de Stock (Compra)
    with tab_e:
        st.markdown("### 🚚 Registrar Entrada de Mercadería (Compra)")
        
        proveedores_opts = sorted(df_p["Nombre"].unique()) if not df_p.empty else []
        ingredientes_opts = sorted(df_i["Nombre"].unique()) if not df_i.empty else []
        
        if not proveedores_opts or not ingredientes_opts:
            st.warning("⚠️ Asegúrese de haber cargado Proveedores e Ingredientes en las pestañas anteriores.")
        else:
            
            # --- WIDGETS DE ENTRADA (FUERA DE st.form) ---
            st.markdown("##### 1. Datos de la Compra")
            
            col_i1, col_i2 = st.columns(2)
            p_sel = col_i1.selectbox("Proveedor", proveedores_opts, key="proveedor_entrada")
            
            # Selector de Ingrediente (usado para claves dinámicas)
            i_sel = col_i2.selectbox(
                "Ingrediente (Materia Prima/Empaque)", 
                ingredientes_opts, 
                key="ingrediente_entrada"
            )
            
            # Obtener la UNIDAD BASE del ingrediente seleccionado
            ing_base_unit = 'g' # Default
            if i_sel and not df_i.empty:
                selected_match = df_i[df_i["Nombre"] == i_sel]
                if not selected_match.empty:
                    ing_base_unit = str(selected_match["Unidad_Base"].iloc[0]).lower().strip()
                else:
                    st.warning(f"No se encontró la unidad base para {i_sel}. Usando 'g' por defecto.")

            st.markdown("##### 2. Cantidad, Costo y Lote (Trazabilidad)")
            
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            
            # --- DEFINICIÓN DE CLAVES DINÁMICAS y st.text_input para estabilidad ---
            q_cant_compra_key = f"q_cant_compra_key_{i_sel}"
            q_costo_referencia_key = f"q_costo_referencia_key_{i_sel}"
            q_unidad_compra_key = f"q_unidad_compra_key_{i_sel}"
            q_unidad_referencia_key = f"q_unidad_referencia_key_{i_sel}"

            # Input 1: Cantidad Comprada (st.text_input para estabilidad)
            q_cant_compra_str = col_c1.text_input(
                "Cantidad Comprada", 
                value=st.session_state.get(q_cant_compra_key, ""), 
                key=q_cant_compra_key
            )
            
            # Input 2: Unidad de Compra (ej: 500 g)
            q_unidad_compra = col_c2.selectbox(
                "Unidad de Compra", 
                UNIDADES_CONSUMO, 
                key=q_unidad_compra_key
            )
            
            # Input 3: Costo por Unidad de Referencia (ej: 200)
            q_costo_referencia_str = col_c3.text_input(
                "Costo por Unidad de Referencia ($)", 
                value=st.session_state.get(q_costo_referencia_key, ""), 
                key=q_costo_referencia_key
            )
            
            # Input 4: Unidad de Referencia de Costo (ej: kg)
            q_unidad_referencia = col_c4.selectbox(
                "Unidad de Referencia de Costo", 
                UNIDADES_CONSUMO,
                key=q_unidad_referencia_key
            )

            q_lote = st.text_input("Lote/Factura del Proveedor", "N/A", key="q_lote_stock_entry")
            
            col_dates1, col_dates2 = st.columns(2)
            # Input 5: Fecha de Compra (Movimiento)
            q_fecha_compra = col_dates1.date_input("Fecha de Compra", value=datetime.today(), key="q_fecha_compra_stock_entry")
            # Input 6: Fecha de Vencimiento
            q_vencimiento = col_dates2.date_input("Fecha de Vencimiento", value=None, min_value=datetime.today(), key="q_vencimiento_stock_entry")


            # --- CONVERSIÓN DE CADENAS A NÚMEROS (PARA PREVIEW) ---
            # Usamos parse_input_number en lugar de lambda simple
            q_cant_compra = parse_input_number(q_cant_compra_str)
            q_costo_referencia = parse_input_number(q_costo_referencia_str)

            
            # --- CÁLCULOS PREVIOS (Para visualización) ---
            
            factor_compra_a_referencia = get_conversion_factor(q_unidad_compra, q_unidad_referencia)
            q_costo_total = 0.0
            if factor_compra_a_referencia != 0.0:
                cantidad_en_referencia = q_cant_compra * factor_compra_a_referencia
                q_costo_total = cantidad_en_referencia * q_costo_referencia
            
            factor_compra_a_base = get_conversion_factor(q_unidad_compra, ing_base_unit)
            q_cant_base = q_cant_compra * factor_compra_a_base
            
            costo_real_unitario = q_costo_total / q_cant_base if q_cant_base > 0 else 0
            
            st.markdown("---")
            st.markdown(f"**Costo TOTAL Calculado de esta Compra:** **$ {q_costo_total:,.2f}**")
            
            st.info(f"""
            **Detalle de Almacenamiento (Preview):**
            - Cantidad que ingresa a Stock (Unidad Base): **{q_cant_base:,.3f} {ing_base_unit.upper()}**
            - Costo unitario real (CPP por **{ing_base_unit.upper()}**): **$ {costo_real_unitario:.4f}**
            """)
            
            st.markdown("---")

            # --- BOTÓN DE REGISTRO (FUERA DE st.form) ---
            if st.button("REGISTRAR ENTRADA DE STOCK", type="primary", key="btn_register_entrada"):
                
                # RE-LECTURA DE VALORES DEL SESSION STATE (Garantizado que son los finales)
                submitted_q_cant_compra_str = st.session_state[q_cant_compra_key]
                submitted_q_costo_referencia_str = st.session_state[q_costo_referencia_key]
                submitted_q_unidad_compra = st.session_state[q_unidad_compra_key]
                submitted_q_unidad_referencia = st.session_state[q_unidad_referencia_key]
                submitted_p_sel = st.session_state["proveedor_entrada"]
                submitted_i_sel = st.session_state["ingrediente_entrada"]
                submitted_q_lote = st.session_state["q_lote_stock_entry"]
                submitted_q_vencimiento = st.session_state["q_vencimiento_stock_entry"]
                submitted_q_fecha_compra = st.session_state.get("q_fecha_compra_stock_entry", datetime.today())

                
                # CONVERSIÓN FINAL Y VALIDACIÓN (Usando la conversión segura)
                # CONVERSIÓN FINAL Y VALIDACIÓN (Usando la conversión segura)
                submitted_q_cant_compra = parse_input_number(submitted_q_cant_compra_str)
                submitted_q_costo_referencia = parse_input_number(submitted_q_costo_referencia_str)

                # Recalculando con valores finales leídos del state
                submitted_match = df_i[df_i["Nombre"] == submitted_i_sel]
                if submitted_match.empty:
                    st.error(f"Error crítico: No se encuentra el ingrediente '{submitted_i_sel}'.")
                    return
                submitted_ing_base_unit = str(submitted_match["Unidad_Base"].iloc[0]).lower().strip()
                submitted_factor_compra_a_referencia = get_conversion_factor(submitted_q_unidad_compra, submitted_q_unidad_referencia)
                submitted_cantidad_en_referencia = submitted_q_cant_compra * submitted_factor_compra_a_referencia
                submitted_q_costo_total = submitted_cantidad_en_referencia * submitted_q_costo_referencia
                
                submitted_factor_compra_a_base = get_conversion_factor(submitted_q_unidad_compra, submitted_ing_base_unit)
                submitted_q_cant_base = submitted_q_cant_compra * submitted_factor_compra_a_base
                
                submitted_costo_real_unitario = submitted_q_costo_total / submitted_q_cant_base if submitted_q_cant_base > 0 else 0
                
                
                # VALIDACIÓN FINAL
                if submitted_q_cant_base > 0 and submitted_q_costo_total > 0 and submitted_p_sel and submitted_i_sel:
                    new_uuid = str(uuid.uuid4())
                    
                    nuevo_registro = {
                        "UUID": new_uuid,
                        "Ingrediente": submitted_i_sel,
                        "Cantidad": submitted_q_cant_base, 
                        "Unidad_Base": submitted_ing_base_unit,
                        "Tipo_Movimiento": "ENTRADA",
                        "Costo_Real": submitted_costo_real_unitario, 
                        "Proveedor": submitted_p_sel,
                        "Lote_Proveedor": submitted_q_lote,
                        "Fecha_Vencimiento": submitted_q_vencimiento.strftime("%Y-%m-%d") if submitted_q_vencimiento else "",
                        "Fecha_Movimiento": submitted_q_fecha_compra.strftime("%Y-%m-%d 12:00:00") if hasattr(submitted_q_fecha_compra, 'strftime') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    new_log = pd.DataFrame([nuevo_registro])
                    save_data("stock_log", pd.concat([df_sl, new_log], ignore_index=True))
                    
                    # --- AUTO-ACTUALIZACION DE PRECIO MAESTRO Y PROVEEDOR ---
                    # Al registrar una compra, el precio de compra se convierte en el nuevo 
                    # Precio Maestro y el proveedor en el Proveedor Actualizado.
                    df_i_current = get_df("ingredientes")
                    idx_i = df_i_current[df_i_current["Nombre"] == submitted_i_sel].index
                    if not idx_i.empty:
                        df_i_current.at[idx_i[0], "Costo"] = submitted_costo_real_unitario
                        df_i_current.at[idx_i[0], "Ultimo_Proveedor"] = submitted_p_sel
                        save_data("ingredientes", df_i_current)
                    
                    st.success(f"🎉 ¡Éxito! Entrada registrada. Stock: {submitted_q_cant_base:,.3f} {submitted_ing_base_unit.upper()} (Costo Total: ${submitted_q_costo_total:,.2f}).")
                    st.rerun()
                else:
                    # DIAGNÓSTICO DE ERROR MEJORADO
                    error_msgs = []
                    
                    # 1. Chequeo de Compatibilidad de Unidades (Compra vs Base)
                    if submitted_factor_compra_a_base == 0:
                        error_msgs.append(f"- ❌ **Incompatibilidad de Unidades (Producto):** Estás ingresando una compra en **'{submitted_q_unidad_compra}'** pero el ingrediente '{submitted_i_sel}' se gestiona internamente en **'{submitted_ing_base_unit}'**.")
                        error_msgs.append("  (El sistema no puede convertir automáticamente entre Peso (kg/g) y Volumen (lt/ml). Por favor, usa la misma magnitud o crea un ingrediente nuevo con la unidad correcta).")
                    
                    # 2. Chequeo de Compatibilidad (Compra vs Referencia Costo)
                    if submitted_factor_compra_a_referencia == 0:
                        error_msgs.append(f"- ❌ **Incompatibilidad de Costo**: La unidad de compra es **'{submitted_q_unidad_compra}'** pero indicaste el precio por **'{submitted_q_unidad_referencia}'**.")

                    # 3. Chequeo de Valores Cero
                    if submitted_q_cant_compra <= 0:
                        error_msgs.append(f"- ❌ La Cantidad Comprada debe ser mayor a 0 (Valor detectado: {submitted_q_cant_compra}).")
                    
                    if submitted_q_costo_referencia <= 0:
                        error_msgs.append(f"- ❌ El Costo de Referencia debe ser mayor a 0 (Valor detectado: {submitted_q_costo_referencia}).")
                    
                    if not error_msgs:
                        error_msgs.append("- Error desconocido. Verifique que completó todos los campos.")

                    st.error("**⚠️ No se pudo registrar la entrada por los siguientes motivos:**\n\n" + "\n".join(error_msgs))



    # 4.3. Módulo de Reporte de Stock
    with tab_s:
        st.markdown("### 📊 Reporte de Stock Actual Consolidado y CPP")
        
        df_sl = get_df("stock_log")
        df_i = get_df("ingredientes")
        
        # --- ALERTAS DE VENCIMIENTO ---
        st.markdown("### ⚠️ Alertas de Vencimiento Próximo")
        from modules.data_manager import calcular_stock_por_lote
        df_lotes_stock = calcular_stock_por_lote(df_sl, df_i)
        
        if not df_lotes_stock.empty and 'Fecha_Vencimiento' in df_lotes_stock.columns:
            # Convertir a datetime
            df_lotes_stock['Fecha_Vencimiento_dt'] = pd.to_datetime(df_lotes_stock['Fecha_Vencimiento'], errors='coerce')
            
            # Filtrar próximos a vencer (< 15 días)
            hoy = pd.Timestamp.now()
            limite = hoy + pd.Timedelta(days=15)
            
            proximos_vencer = df_lotes_stock[
                (df_lotes_stock['Fecha_Vencimiento_dt'].notna()) & 
                (df_lotes_stock['Fecha_Vencimiento_dt'] <= limite) &
                (df_lotes_stock['Cantidad_Stock'] > 0)
            ].copy()
            
            if not proximos_vencer.empty:
                st.error(f"⚠️ **{len(proximos_vencer)} ingrediente(s) próximos a vencer en los próximos 15 días:**")
                for _, row in proximos_vencer.iterrows():
                    dias_restantes = (row['Fecha_Vencimiento_dt'] - hoy).days
                    emoji = "🔴" if dias_restantes <= 0 else "🟡" if dias_restantes <= 7 else "🟠"
                    venc_str = row['Fecha_Vencimiento_dt'].strftime('%d/%m/%Y') if pd.notna(row['Fecha_Vencimiento_dt']) else 'N/A'
                    st.markdown(f"{emoji} **{row['Ingrediente']}**: {row['Cantidad_Stock']:.2f} {row.get('Unidad_Base', '')} - Vence: {venc_str} ({dias_restantes} días)")
            else:
                st.success("✅ No hay ingredientes próximos a vencer")
        else:
            st.info("No hay datos de vencimiento registrados.")
        
        st.divider()
        
        # --- GESTIÓN DE PRECIOS SEGURA (FORMULARIO EXPLÍCITO) ---
        st.markdown("### 📝 Editar Precio de Producto (Modo Seguro)")
        st.info("Seleccione el producto para ver y modificar su precio fijo. El sistema ajusta automáticamente las unidades.")
        
        col_sel, col_val, col_act = st.columns([2, 2, 1])
        
        with col_sel:
            lista_ingredientes = sorted(df_i["Nombre"].unique())
            ing_a_editar = st.selectbox("Seleccione Producto", lista_ingredientes, key="sel_price_edit")
        
        # Obtener datos actuales
        match_ing = df_i[df_i["Nombre"] == ing_a_editar]
        if match_ing.empty:
            st.warning("⚠️ No se puede editar el precio. El ingrediente no está en la base de datos o hubo un error de conexión.")
            return

        row_ing = match_ing.iloc[0]
        base_unit_edit = str(row_ing["Unidad_Base"]).lower().strip()
        current_base_cost = float(row_ing.get("Costo", 0.0))
        
        # Calcular display actual
        # Lógica Permisiva de Unidades:
        # Gramos: g, gr, grs, gramo, gramos
        # Mililitros: ml, cc, cm3, mls
        # Kilos: kg, kgs, kilo, kilos
        # Litros: lt, lts, litro, litros
        
        is_gram_like = base_unit_edit in ['g', 'gr', 'grs', 'gramo', 'gramos']
        is_ml_like = base_unit_edit in ['ml', 'cc', 'cm3', 'mls']
        is_kg_like = base_unit_edit in ['kg', 'kgs', 'kilo', 'kilos']
        is_lt_like = base_unit_edit in ['lt', 'lts', 'litro', 'litros']
        
        comm_unit_edit = base_unit_edit
        current_comm_cost = current_base_cost
        factor_display = 1.0
        
        if is_gram_like or is_ml_like:
            comm_unit_edit = 'kg' if is_gram_like else 'lt'
            current_comm_cost = current_base_cost * 1000.0
            factor_display = 1000.0
        elif is_kg_like or is_lt_like:
            # Si la unidad base YA es comercial (ej: se compra por saco de Kilo),
            # entonces el costo base ya es por kilo. No se multiplica.
            comm_unit_edit = base_unit_edit
            current_comm_cost = current_base_cost 
            
        with col_val:
            st.metric(
                label=f"Precio Actual (por {comm_unit_edit.upper()})", 
                value=f"$ {current_comm_cost:,.2f}",
                delta=f"Base: $ {current_base_cost:,.4f} / {base_unit_edit}"
            )
            
        with col_act:
            # Botón para FIX DE MILLONES (Limpieza rápida)
            with st.popover("🧹 Limpiar Ceros Extra"):
                st.write("Si ve precios exagerados (millones), use esto.")
                if st.button("Corregir Precios > $1000/g"):
                    c_fix = 0
                    for idx, r in df_i.iterrows():
                        u = str(r["Unidad_Base"]).lower().strip()
                        c = float(r.get("Costo", 0))
                        
                        # Chequeo permisivo dentro del loop de corrección
                        u_is_g = u in ['g', 'gr', 'grs', 'gramo', 'gramos', 'ml', 'cc', 'cm3']
                        
                        if u_is_g and c > 500: # Umbral de seguridad ($500 el gramo es carísimo, $500.000 el kilo)
                             df_i.at[idx, "Costo"] = c / 1000.0
                             c_fix += 1
                    if c_fix > 0:
                        save_data("ingredientes", df_i)
                        st.success(f"Se corrigieron {c_fix} precios.")
                        st.rerun()
                    else:
                        st.warning("No se detectaron precios erróneos extremos.")

        # FORMULARIO DE EDICIÓN
        with st.form("form_update_price"):
            col_inp1, col_inp2 = st.columns(2)
            new_price_input = col_inp1.number_input(
                f"Nuevo Precio por {comm_unit_edit.upper()}", 
                min_value=0.0, 
                value=current_comm_cost, 
                step=100.0,
                format="%.2f"
            )
            
            # Recuperar Proveedor Actual
            prov_actual = str(row_ing.get("Ultimo_Proveedor", "N/A"))
            prov_opts = sorted(df_p["Nombre"].unique().tolist())
            if prov_actual not in prov_opts:
                prov_opts = [prov_actual] + prov_opts if prov_actual != "N/A" else prov_opts
                
            new_prov_sel = col_inp2.selectbox(
                "Proveedor Relacionado", 
                prov_opts, 
                index=prov_opts.index(prov_actual) if prov_actual in prov_opts else 0
            )
            
            if st.form_submit_button("💾 GUARDAR NUEVO PRECIO"):
                # Conversión inversa explícita
                # Si es KG, el usuario entra X. Nosotros guardamos X / 1000.
                final_cost_save = new_price_input
                
                # Usar los boléanos calculados arriba
                if is_gram_like or is_ml_like:
                    final_cost_save = new_price_input / 1000.0
                
                # Guardar en df_ingredientes
                idx_to_update = df_i[df_i["Nombre"] == ing_a_editar].index
                if not idx_to_update.empty:
                    df_i.at[idx_to_update[0], "Costo"] = final_cost_save
                    df_i.at[idx_to_update[0], "Ultimo_Proveedor"] = new_prov_sel # Actualizar proveedor también
                    save_data("ingredientes", df_i)
                    
                    # Generar Log Audit (Inherit last expiration to avoid 'breaking' visibility)
                    last_exp_date = ""
                    try:
                        hist = df_sl[df_sl["Ingrediente"] == ing_a_editar]
                        if not hist.empty:
                            last_exp_date = hist.sort_values("Fecha_Movimiento").iloc[-1]["Fecha_Vencimiento"]
                    except: pass

                    new_uuid = str(uuid.uuid4())
                    log_entry = {
                        "UUID": new_uuid,
                        "Ingrediente": ing_a_editar,
                        "Cantidad": 0.0,
                        "Unidad_Base": base_unit_edit,
                        "Tipo_Movimiento": "AJUSTE_MANUAL_COSTO",
                        "Costo_Real": final_cost_save,
                        "Lote_Proveedor": f"PRECIO FIJO: {new_prov_sel}",
                        "Fecha_Movimiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Fecha_Vencimiento": last_exp_date # Mantener ultima fecha conocida
                    }
                    df_sl = pd.concat([get_df("stock_log"), pd.DataFrame([log_entry])], ignore_index=True)
                    save_data("stock_log", df_sl)
                    
                    st.success(f"Precio actualizado: ${new_price_input:,.2f}/{comm_unit_edit} ({new_prov_sel})")
                    st.rerun()

        st.divider()

        df_stock_data = calcular_stock_actual(df_sl, df_i)

        # --- PREPARACIÓN PARA DISPLAY (Forzar Unidad Comercial: KG/LT) ---
        # Para evitar confusiones al editar precio, SIEMPRE mostramos en KG o LT, 
        # aunque el stock sea pequeño (ej: 0.500 kg en lugar de 500 g).
        
        def forzar_unidad_comercial(row):
            qty = row['Stock_Actual']
            unit = str(row['Unidad_Base']).lower().strip()
            cpp = row['Costo_Ponderado']
            
            # g -> kg (Permisivo)
            if unit in ['g', 'gr', 'grs', 'gramo', 'gramos']:
                row['Unidad_Base'] = 'kg'
                row['Stock_Actual'] = qty / 1000.0
                row['Costo_Ponderado'] = cpp * 1000.0
            # ml -> lt (Permisivo)
            elif unit in ['ml', 'cc', 'cm3', 'mls']:
                row['Unidad_Base'] = 'lt'
                row['Stock_Actual'] = qty / 1000.0
                row['Costo_Ponderado'] = cpp * 1000.0
            
            return row

        df_stock_display = df_stock_data.copy()
        
        # Ordenar alfabéticamente por Ingrediente
        df_stock_display = df_stock_display.sort_values(by='Ingrediente')
        
        df_stock_display = df_stock_display.apply(forzar_unidad_comercial, axis=1)
        
        # Calcular Valor Total en Moneda (Cantidad * Precio)
        df_stock_display['Valor_Total_Display'] = df_stock_display['Stock_Actual'] * df_stock_display['Costo_Ponderado']
        
        # Tabla solo lectura
        st.markdown("#### Stock Actual y Valorización")
        st.dataframe(
            df_stock_display,
            key="stock_report_view",
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Ingrediente": st.column_config.TextColumn("Ingrediente"),
                "Unidad_Base": st.column_config.TextColumn("Unidad"),
                "Stock_Actual": st.column_config.NumberColumn("Stock Disponible", format="%.3f"),
                "Costo_Ponderado": st.column_config.NumberColumn(
                    "Precio Unitario (Ref)", 
                    format="$ %.2f", 
                    help="Este es el precio configurado arriba."
                ),
                "Proveedor": st.column_config.TextColumn("Proveedor"),
                "Valor_Total_Display": st.column_config.NumberColumn("Valor Total", format="$ %.2f"),
                "Total_Qty_In": None 
            }
        )
        
        # --- NUEVA SECCIÓN: EXPORTACIÓN EXCEL ---
        st.markdown("---")
        st.markdown("#### 📥 Exportar Reporte de Inventario")
        
        if st.button("📊 Generar Reporte Detallado (Excel)"):
            from modules.data_manager import calcular_stock_por_lote
            import io
            
            # 1. Calcular Datos Detallados
            df_det = calcular_stock_por_lote(df_sl, df_i)
            
            if not df_det.empty:
                # 2. Convertir unidades para el reporte (g -> kg, ml -> lt)
                def formatear_para_excel(row):
                    unit_e = str(row['Unidad_Base']).lower().strip()
                    qty_e = row['Cantidad_Stock']
                    prc_e = row['Precio_Unitario']
                    
                    if unit_e in ['g', 'gr', 'grs', 'gramo']:
                        row['Unidad_Base'] = 'kg'
                        row['Cantidad_Stock'] = qty_e / 1000.0
                        row['Precio_Unitario'] = prc_e * 1000.0
                    elif unit_e in ['ml', 'cc', 'cm3']:
                        row['Unidad_Base'] = 'lt'
                        row['Cantidad_Stock'] = qty_e / 1000.0
                        row['Precio_Unitario'] = prc_e * 1000.0
                    
                    row['Valor_Total'] = row['Cantidad_Stock'] * row['Precio_Unitario']
                    return row

                df_excel = df_det.apply(formatear_para_excel, axis=1)
                
                # 3. Formatear nombres de columnas
                df_excel.columns = [
                    'Producto', 'Unidad', 'Stock Disponible', 'Precio Unitario ($)', 
                    'Valor Total ($)', 'Lote / Factura', 'Fecha Vencimiento', 'Fecha Ingreso'
                ]
                
                # 4. Crear archivo Excel en memoria
                output = io.BytesIO()
                try:
                    # Intentar usar openpyxl (más común) o el motor por defecto de pandas
                    try:
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_excel.to_excel(writer, index=False, sheet_name='Stock_Detallado')
                    except:
                        # Fallback: motor automático
                        with pd.ExcelWriter(output) as writer:
                            df_excel.to_excel(writer, index=False, sheet_name='Stock_Detallado')
                    
                    st.download_button(
                        label="💾 DESCARGAR ARCHIVO EXCEL",
                        data=output.getvalue(),
                        file_name=f"Reporte_Stock_RojoMalbec_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e_excel:
                    st.error(f"Error generando Excel: {e_excel}")
                    st.info("Intentando generar un archivo CSV como alternativa...")
                    csv = df_excel.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="💾 DESCARGAR ARCHIVO CSV (Compatible con Excel)",
                        data=csv,
                        file_name=f"Reporte_Stock_RojoMalbec_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No hay stock remanente para generar el reporte.")

    # 4.4. Historial por Proveedor
    with tab_h:
        st.markdown("### 📜 Historial de Compras por Proveedor")
        
        if df_p.empty:
            st.info("No hay proveedores registrados.")
        else:
            p_sel_hist = st.selectbox("Seleccionar Proveedor para ver Historial", sorted(df_p["Nombre"].unique()), key="hist_p_sel")
            
            if p_sel_hist:
                # Filtrar log por proveedor
                # Nota: Los registros antiguos no tendrán el campo 'Proveedor', así que filtramos con cuidado
                if "Proveedor" in df_sl.columns:
                    mask = (df_sl["Proveedor"] == p_sel_hist) & (df_sl["Tipo_Movimiento"] == "ENTRADA")
                    df_hist = df_sl[mask].copy()
                else:
                    df_hist = pd.DataFrame()
                
                if df_hist.empty:
                    st.warning(f"No hay registros de compras para '{p_sel_hist}' en el log nuevo.")
                    st.info("Nota: Las compras registradas antes de esta versión no aparecen en este historial específico.")
                else:
                    st.markdown(f"#### Compras a: {p_sel_hist}")
                    
                    # Formatear para visualización
                    df_hist = df_hist.sort_values("Fecha_Movimiento", ascending=False)
                    df_hist_view = df_hist[[
                        "Fecha_Movimiento", "Ingrediente", "Cantidad", "Unidad_Base", "Costo_Real", "Lote_Proveedor", "Fecha_Vencimiento"
                    ]].copy()
                    
                    st.dataframe(
                        df_hist_view.style.format({
                            "Costo_Real": "$ {:,.4f}",
                            "Cantidad": "{:,.2f}"
                        }),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Fecha_Movimiento": "Fecha Compra",
                            "Costo_Real": "Costo Unitario",
                            "Lote_Proveedor": "Lote/Factura",
                            "Fecha_Vencimiento": "Vencimiento"
                        }
                    )
                    
                    # Métricas de compras a este proveedor
                    col_m1, col_m2 = st.columns(2)
                    total_compras = len(df_hist)
                    ultima_compra = df_hist["Fecha_Movimiento"].max()
                    col_m1.metric("Total de Ingresos", total_compras)
                    col_m2.metric("Último Ingreso", str(ultima_compra)[:10])

    # 4.5. Log de Movimientos (Trazabilidad Básica)
    with tab_log:
        st.markdown("### 📜 Log de Movimientos (Trazabilidad)")
        
        if not df_sl.empty:
            # 1. Preparar DataFrame para visualización y edición
            # Mantenemos UUID para identificar filas, pero lo ocultamos
            df_display = df_sl.sort_values(by="Fecha_Movimiento", ascending=False).copy()
            
            # Ajustes visuales (Cantidad absoluta para display, Fechas a datetime)
            df_display['Cantidad_Abs'] = df_display['Cantidad'].abs() # Columna temporal para mostrar bonito
            df_display['Fecha_Vencimiento'] = pd.to_datetime(df_display['Fecha_Vencimiento'], errors='coerce')
            
            # --- FORMATEO DE COSTO PARA DISPLAY ---
            # Para ENTRADA/SALIDA: Costo_Real es precio unitario.
            # Para REVALUO: Costo_Real es el delta total.
            def format_costo(row):
                tm = str(row['Tipo_Movimiento']).upper()
                if tm == 'REVALUO':
                     return f"Ajuste Total: ${row['Costo_Real']:,.2f}"
                elif tm == 'AJUSTE_MANUAL_COSTO':
                     return f"Fijar Precio: ${row['Costo_Real']:,.2f}"
                else:
                     return f"${row['Costo_Real']:,.2f}"
            
            df_display['Costo_Display'] = df_display.apply(format_costo, axis=1)

            # AGREGAR COLUMNA ELIMINAR
            df_display['Eliminar'] = False

            # 2. Editor de Datos
            edited_df = st.data_editor(
                df_display,
                key="editor_movimientos_log",
                hide_index=True,
                use_container_width=True,
                column_config={
                    "UUID": None, # Ocultar columna ID
                    "Cantidad": None, # Ocultar la cantidad original (con signo)
                    "Costo_Real": None, # Ocultar el costo raw
                    "Eliminar": st.column_config.CheckboxColumn(
                        "¿Borrar?",
                        help="Seleccione para eliminar este movimiento permanentemente",
                        default=False
                    ),
                    "Cantidad_Abs": st.column_config.NumberColumn("Cantidad", format="%.3f", disabled=True),
                    "Fecha_Movimiento": st.column_config.TextColumn("Fecha", disabled=True),
                    "Ingrediente": st.column_config.TextColumn("Ingrediente", disabled=True),
                    "Unidad_Base": st.column_config.TextColumn("Unidad", disabled=True),
                    "Tipo_Movimiento": st.column_config.TextColumn("Tipo", disabled=True),
                    "Costo_Display": st.column_config.TextColumn("Costo / Valor", disabled=True),
                    "Lote_Proveedor": st.column_config.TextColumn("Lote Prov.", disabled=True),
                    "Fecha_Vencimiento": st.column_config.DateColumn(
                        "Vencimiento (Editar)", 
                        format="DD/MM/YYYY", 
                        min_value=datetime(2020, 1, 1),
                        step=1,
                        help="Doble clic para editar la fecha de vencimiento."
                    ),
                },
                column_order=[
                    "Eliminar", "Fecha_Movimiento", "Ingrediente", "Cantidad_Abs", "Unidad_Base", 
                    "Tipo_Movimiento", "Costo_Display", "Lote_Proveedor", "Fecha_Vencimiento"
                ]
            )
            
            # --- LÓGICA DE ELIMINACIÓN ---
            rows_to_delete = edited_df[edited_df["Eliminar"] == True]
            if not rows_to_delete.empty:
                st.warning(f"⚠️ Ha seleccionado {len(rows_to_delete)} movimiento(s) para eliminar.")
                if st.button("🗑️ Eliminar Movimientos Seleccionados", type="primary"):
                    uuids_to_delete = rows_to_delete["UUID"].tolist()
                    
                    # Filtrar fuera los UUIDs eliminados del DF principal
                    df_sl = df_sl[~df_sl['UUID'].isin(uuids_to_delete)]
                    
                    save_data("stock_log", df_sl)
                    st.success("Log actualizado. Los movimientos seleccionados han sido eliminados.")
                    st.rerun()

            # 3. Lógica para Guardar Cambios (Fecha Vencimiento)
            # Detectamos si hubo cambios comparando con el estado original (cargado en df_sl)
            # Como st.data_editor devuelve el estado actual, verificamos diferencias.
            
            cambios_para_guardar = False
            
            # Optimizacion: Solo iterar si las series de fechas difieren
            # NOTA: Debemos ignorar filas que podrían haberse marcado para borrar pero aun no se borraron (aunque el rerun ocurre antes)
            # De todas formas, filtramos df_sl solo si se ejecuto el borrado. Si no, seguimos aqui.
            
            # Convertimos la columna original de df_sl a datetime para comparar rápido
            fechas_originales = pd.to_datetime(df_sl.set_index("UUID")["Fecha_Vencimiento"], errors="coerce")
            
            # Solo consideramos las filas que aun existen en edited_df (aunque tengan eliminar checked, si no se dio click, estan ahi)
            fechas_editadas = edited_df.set_index("UUID")["Fecha_Vencimiento"]
            
            # Alinear indices (Intersectando UUIDs)
            common_uuids = fechas_editadas.index.intersection(fechas_originales.index)
            fechas_originales = fechas_originales.loc[common_uuids]
            fechas_editadas = fechas_editadas.loc[common_uuids]
            
            
            # Normalizar a fecha (date) para comparar y evitar diferencias de timestamp
            try:
                # Comparamos string YYYY-MM-DD, llenando nulos con string vacío para evitar NaT != NaT
                val_orig = fechas_originales.dt.strftime('%Y-%m-%d').fillna("")
                val_edit = fechas_editadas.dt.strftime('%Y-%m-%d').fillna("")
                
                diff_mask = val_orig != val_edit
                diff_uuids = diff_mask.index[diff_mask].tolist()
            except Exception:
                diff_uuids = []

            if diff_uuids:
                for uuid_mod in diff_uuids:
                    nueva_fecha = fechas_editadas.loc[uuid_mod]
                    if pd.notnull(nueva_fecha):
                        nueva_fecha_str = nueva_fecha.strftime("%Y-%m-%d")
                    else:
                        nueva_fecha_str = ""
                    
                    # Actualizar en el DataFrame Maestro (df_sl)
                    idx_maestro = df_sl[df_sl["UUID"] == uuid_mod].index
                    if not idx_maestro.empty:
                        df_sl.at[idx_maestro[0], "Fecha_Vencimiento"] = nueva_fecha_str
                        cambios_para_guardar = True
            
            if cambios_para_guardar:
                save_data("stock_log", df_sl)
                st.toast("✅ Fecha de vencimiento actualizada correctamente.", icon="💾")
                # Rerun para refrescar la carga inicial y limpiar el estado de 'cambio detectado' para la UI
                st.rerun()
        else:
            st.info("No hay movimientos registrados todavía.")
