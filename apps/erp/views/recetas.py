
# views/recetas.py
import streamlit as st
import pandas as pd
import os
import io
import base64
import barcode
from barcode.writer import ImageWriter
from modules.data_manager import get_df, save_data, calculate_recipe_cost_per_kg, calcular_stock_actual , load_data, auto_generar_codigo
from modules.conversions import UNIDADES_CONSUMO, convertir_a_base
from modules.nutrition import calculate_recipe_composition, get_ingredient_nutrition

MAP_CODIGOS_POS = {
    "sal al malbec": "RM-SAL-MAL",
    "sal british": "RM-SAL-BRI",
    "sal de limon y chile": "RM-SAL-LCH",
    "sal de limon y chile (suave)": "RM-SAL-LCH",
    "sal de rosas y romero": "RM-SAL-ROS",
    "sal del desierto": "RM-SAL-DES",
    "sal negra hawaiana": "RM-SAL-HAW",
    "sal negra tipo hawaiana": "RM-SAL-HAW",
    "sal esvanetian": "RM-SAL-ESV",
    "sal svanetian": "RM-SAL-ESV",
    "sal vikinga ahumada": "RM-SAL-VIK",
    "ajo a las hierbas": "RM-BLE-AJO",
    "ajo a las hierbas gourmet": "RM-BLE-AJO",
    "bbq": "RM-BLE-BBQ",
    "bbq rojo malbec": "RM-BLE-BBQ",
    "curry colombo": "RM-BLE-COL",
    "nanami togarashi": "RM-BLE-NAN",
    "nanami tōgarashi": "RM-BLE-NAN",
    "za'atar": "RM-BLE-ZAA",
    "zaatar": "RM-BLE-ZAA",
    "sloopy joe": "RM-BLE-SLO",
    "sloppy joe": "RM-BLE-SLO",
    "gluhwein": "RM-BLE-GLU",
    "glühwein": "RM-BLE-GLU",
    "panch phoron": "RM-BLE-PAN",
    "pesto siciliano con pistacho": "RM-BLE-PES",
    "mole mexicano": "RM-BLE-MOL",
    "mole mexicano de autor": "RM-BLE-MME",
    "espana profunda": "RM-BLE-ESP",
    "españa profunda": "RM-BLE-ESP",
    "dry hot honey": "RM-BLE-DRY",
    "vital caldo": "RM-VIT-CAL",
    "vital italia": "RM-VIT-ITA",
    "vital india": "RM-VIT-IND",
    "vital parrilera": "RM-VIT-PAR",
    "vital criollo": "RM-VIT-CRI",
    "vital citrus": "RM-VIT-CIT",
    "vital tipo queso": "RM-VIT-QUE",
    "vital tipo queso · perfil parmesano reserva": "RM-VIT-QUE",
    "pimienta negra": "RM-PIM-NEG",
    "pimienta negra de autor": "RM-PIM-NEG",
    "pimienta roja y larga": "RM-PIM-ROJ",
    "pimienta roja y pimienta larga": "RM-PIM-ROJ",
    "pimienta verde": "RM-PIM-VER",
    "pimienta verde de autor": "RM-PIM-VER",
    "te pu-erh": "RM-TEA-PUE",
    "te pu erh": "RM-TEA-PUE",
    "te pu-erh rojo malbec": "RM-TEA-PUE",
    "rooibos ambar": "RM-TEA-ROO",
    "rooibos : ambar africano": "RM-TEA-ROO",
    "sal al malbec & te ahumado": "RM-SAL-MTA",
    "sal al malbec & té ahumado": "RM-SAL-MTA",
    "sal al malbec y te ahumado": "RM-SAL-MTA",
    "sal al malbec y té ahumado": "RM-SAL-MTA",
    "te verde del zoco": "RM-TEA-ZOC",
    "te karak": "RM-TEA-KAR",
    "cacao y zest": "RM-TEA-CAC"
}

def normalizar_nombre_producto(texto):
    import unicodedata
    s = str(texto).lower().replace("&", " y ")
    s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return " ".join(s.split())

def auto_generar_codigo_pos(nombre):
    """Genera automáticamente un código POS oficial RM-CAT-XXX según la categoría del producto."""
    if not nombre or pd.isna(nombre):
        return "RM-GEN-001"
    n_norm = normalizar_nombre_producto(nombre)
    if "sal" in n_norm:
        cat = "SAL"
    elif "pimienta" in n_norm:
        cat = "PIM"
    elif "vital" in n_norm:
        cat = "VIT"
    elif "te " in n_norm or n_norm.startswith("te ") or "rooibos" in n_norm or "cacao" in n_norm:
        cat = "TEA"
    else:
        cat = "BLE"
    import re
    palabras = re.findall(r'\w+', n_norm.upper())
    ignore = ["DE", "DEL", "AL", "CON", "Y", "A", "LA", "LAS", "EL", "LOS", "TIPO", "SAL", "PIMIENTA", "VITAL", "TE"]
    sig = [p for p in palabras if p not in ignore]
    if not sig:
        suf = palabras[0][:3] if palabras else "GEN"
    elif len(sig) == 1:
        suf = sig[0][:3]
    elif len(sig) == 2:
        suf = (sig[0][:2] + sig[1][0])[:3]
    else:
        suf = "".join([p[0] for p in sig[:3]])
    return f"RM-{cat}-{suf}".upper()

def obtener_codigo_vendedor(codigo_actual, nombre_producto):
    """Obtiene el código de barra oficial para vendedores/POS en formato RM-XXX-YYY."""
    if codigo_actual and str(codigo_actual).startswith("RM-"):
        return str(codigo_actual).strip()
    nom_clean = normalizar_nombre_producto(nombre_producto)
    for k, v in MAP_CODIGOS_POS.items():
        if normalizar_nombre_producto(k) == nom_clean:
            return v
    # Si codigo_actual ya es un código de barras válido (y no un lote interno tipo 'L ...' o 'SINC')
    if codigo_actual and str(codigo_actual).strip() != "" and str(codigo_actual).lower() != "nan":
        cod_clean = str(codigo_actual).strip()
        if not cod_clean.startswith("L ") and cod_clean != "SINC":
            return cod_clean
    return auto_generar_codigo_pos(nombre_producto)

def generar_codigo_barras_html(codigo_texto, nombre_producto=""):
    """Genera la imagen HTML del código de barras en formato Code128 (Estándar POS Vendedor)."""
    cod_final = obtener_codigo_vendedor(codigo_texto, nombre_producto)
    if not cod_final:
        return "<p style='color:#888; font-style:italic;'>Sin código de barras asignado</p>"
    try:
        rv = io.BytesIO()
        code = barcode.get('code128', cod_final, writer=ImageWriter())
        code.write(rv, options={'module_height': 15.0, 'font_size': 10, 'text_distance': 5.0, 'quiet_zone': 2.0})
        rv.seek(0)
        b64_img = base64.b64encode(rv.read()).decode('utf-8')
        
        html_code = f"""
        <div style="text-align: center; background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #ddd; display: inline-block; margin: 10px 0;">
            <div style="font-family: Arial, sans-serif; font-size: 13px; color: #333; margin-bottom: 5px;">Rojo Malbec · Sales & Blends</div>
            <div style="font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; color: #000; margin-bottom: 8px;">{nombre_producto}</div>
            <img src="data:image/png;base64,{b64_img}" alt="Código de Barras POS Vendedor" style="max-width: 320px; height: auto;" />
            <div style="font-family: monospace; font-size: 12px; color: #555; margin-top: 4px;">Código Vendedor POS: {cod_final}</div>
        </div>
        """
        return html_code
    except Exception as e:
        return f"<p style='color:red;'>Error al generar código de barras: {e}</p>"


def render_recetas_tab():
    # --- LOGICA DE IMPRESIÓN ---
    if "print_mode_rid" in st.session_state and st.session_state["print_mode_rid"] is not None:
        render_print_view(st.session_state["print_mode_rid"])
        if st.button("⬅️ Volver a Edición"):
            st.session_state["print_mode_rid"] = None
            st.rerun()
        return

    st.subheader("🧪 Creación y Edición de Fórmulas Base")
    df_r = get_df("recetas")
    df_rd = get_df("recetas_det")
    df_i = get_df("ingredientes")
    df_sl = get_df("stock_log")
    
    # Mapa de costos para tiempo real
    df_stock_act = calcular_stock_actual(df_sl, df_i)
    cpp_map = df_stock_act.set_index("Ingrediente")["Costo_Ponderado"].to_dict()
    
    st.markdown("---")
    mostrar_archivadas = st.toggle("👁️ Mostrar Recetas Archivadas", value=False, help="Si lo activas, las recetas archivadas volverán a aparecer en la lista para que puedas desarchivarlas.")
    st.markdown("---")
    
    # Lógica de limpieza segura (Reset Flag)
    if st.session_state.get("_reset_recipe"):
        st.session_state["new_receta_nom"] = ""
        st.session_state["new_receta_cod"] = ""
        st.session_state["new_receta_base"] = 1000.0
        st.session_state["new_receta_tecnica"] = ""
        st.session_state["new_receta_cant"] = 0.0
        st.session_state["_reset_recipe"] = False
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Crear Nueva Receta")
        
        nom = st.text_input("Nombre de la Mezcla", key="new_receta_nom").strip()
        cod = st.text_input("Código Interno (ej: SAL-001)", key="new_receta_cod")
        base = st.number_input("Peso Base de la Fórmula (g)", 1000.0, step=100.0, key="new_receta_base")
        tecnica = st.text_area("Técnica de Elaboración (opcional)", key="new_receta_tecnica", help="Describe los pasos, tiempos y temperaturas.")
        
        st.markdown("---")
        st.write("**Detalle de Ingredientes**")
        ing_opts = sorted(df_i["Nombre"].unique()) if not df_i.empty else []
        if ing_opts:
            sel_i = st.selectbox("Elegir MP/Envase", ing_opts)
            col_c, col_u = st.columns(2)
            cant_i = col_c.number_input("Cantidad", 0.0, step=0.1, key="new_receta_cant")
            unidad_receta = col_u.selectbox("Unidad de Consumo", UNIDADES_CONSUMO)
            
            if "temp_rec_v6" not in st.session_state: st.session_state["temp_rec_v6"] = []
            
            if st.button("➕ Agregar a lista temporal"):
                if sel_i and cant_i > 0:
                    found = False
                    for item in st.session_state["temp_rec_v6"]:
                        if item["Ingrediente"] == sel_i:
                            st.warning(f"'{sel_i}' ya está en la lista temporal.")
                            found = True
                            break
                    if not found:
                        st.session_state["temp_rec_v6"].append({"Ingrediente": sel_i, "Cantidad": cant_i, "Unidad_Consumo": unidad_receta})
                else:
                    st.warning("Debe seleccionar un ingrediente y una cantidad mayor a cero.")
                
            temp = pd.DataFrame(st.session_state.get("temp_rec_v6", []))
            if not temp.empty: 
                st.dataframe(temp, height=150, hide_index=True)
                if st.button("🗑️ Limpiar Lista Temporal"):
                    st.session_state["temp_rec_v6"] = []
                    st.rerun()
                
                # Pre-visualización de Composición Química
                with st.expander("🔬 Pre-visualización Composición Química (%)"):
                    temp_list = []
                    for t in st.session_state["temp_rec_v6"]:
                        qty_g = convertir_a_base(t["Cantidad"], t["Unidad_Consumo"]) if t["Unidad_Consumo"].lower() in ['g', 'kg'] else 0
                        temp_list.append({'Ingrediente': t["Ingrediente"], 'Cantidad_g': qty_g})
                    
                    df_comp = calculate_recipe_composition(temp_list, base)
                    if not df_comp.empty:
                        st.table(df_comp)
                    else:
                        st.info("Agregue ingredientes gramables (g/kg) para ver la composición.")
                
                # Pre-visualización de Costo MP
                with st.expander("💰 Pre-visualización de Costo MP (Estimado)"):
                    costo_total_temp = 0.0
                    for t in st.session_state["temp_rec_v6"]:
                        qty_base = convertir_a_base(t["Cantidad"], t["Unidad_Consumo"])
                        costo_item = qty_base * cpp_map.get(t["Ingrediente"], 0.0)
                        costo_total_temp += costo_item
                    
                    col_ct1, col_ct2 = st.columns(2)
                    col_ct1.metric("Costo Lote (Base)", f"$ {costo_total_temp:,.2f}")
                    costo_kg_temp = (costo_total_temp * 1000 / base) if base > 0 else 0
                    col_ct2.metric("Costo por KG", f"$ {costo_kg_temp:,.2f}")
                    st.caption("Nota: El costo se calcula usando el Costo Ponderado actual de stock.")

            
            if st.button("💾 Guardar Nueva Fórmula", type="primary"):
                if nom and st.session_state["temp_rec_v6"]:
                    
                    max_id = df_r["Id"].max() if not df_r.empty and df_r["Id"].dtype != object else 0
                    rid = max_id + 1 if max_id > 0 else 1
                    
                    # Generar código automático si está vacío
                    final_cod = cod if cod.strip() != "" else auto_generar_codigo(nom)

                    new_receta = pd.DataFrame([{
                        "Id": float(rid), 
                        "Nombre": nom, 
                        "Codigo": final_cod, # <-- FIX: Restaurar guardado de Código
                        "Tecnica": tecnica,
                        "Base_g": base, 
                        "Gramaje_Venta": base, 
                        "Precio_Venta": 0.0,
                        "Precio_Mayorista": 0.0
                    }])
                    save_data("recetas", pd.concat([df_r, new_receta], ignore_index=True))
                    
                    detalles = []
                    for t in st.session_state["temp_rec_v6"]:
                        detalles.append({"Id_Receta": float(rid), "Ingrediente": t["Ingrediente"], "Cantidad": t["Cantidad"], "Unidad_Consumo": t["Unidad_Consumo"]})
                    
                    new_detalles = pd.DataFrame(detalles)
                    save_data("recetas_det", pd.concat([df_rd, new_detalles], ignore_index=True))
                    
                    st.session_state["temp_rec_v6"] = []
                    # Activar bandera de limpieza para la próxima recarga
                    st.session_state["_reset_recipe"] = True
                    
                    st.success(f"Receta '{nom}' guardada.")
                    st.rerun()
                else:
                    st.error("Faltan datos (Nombre o Ingredientes en la lista temporal).")
        else:
            st.warning("Defina ingredientes primero.")

    with col2:
        st.markdown("### 🛠️ Modificar Recetas Existentes")
        
        if "Archivada" not in df_r.columns: df_r["Archivada"] = False
        df_r_mostrar = df_r if mostrar_archivadas else df_r[df_r["Archivada"].astype(str).str.lower() != "true"]
        
        if not df_r_mostrar.empty:
            receta_a_editar = st.selectbox("Seleccionar Receta para Editar", df_r_mostrar["Nombre"].unique())
            
            if receta_a_editar:
                match_r = df_r_mostrar[df_r_mostrar["Nombre"] == receta_a_editar]
                if match_r.empty:
                    st.warning("No se encontró la receta seleccionada.")
                    return
                r_data = match_r.iloc[0]
                rid = r_data["Id"]
                
                st.write(f"**Editando: {r_data['Nombre']}**")
                
                with st.form(f"form_edit_cabecera_{rid}"):
                    nuevo_nombre = st.text_input("Nuevo Nombre", r_data["Nombre"])
                    actual_codigo = r_data.get("Codigo", "") if pd.notna(r_data.get("Codigo")) else ""
                    nuevo_codigo = st.text_input("Código Interno / Código de Barras", actual_codigo)
                    
                    col_b1, col_b2 = st.columns(2)
                    nueva_base = float(r_data["Base_g"])
                    col_b1.metric("Base Fórmula (g)", f"{nueva_base:.0f}g", help="Se calcula automáticamente al guardar ingredientes.")
                    nueva_venta = col_b2.number_input("Base Venta (g)", float(r_data.get("Gramaje_Venta", r_data["Base_g"])), step=10.0, help="Peso del envase de venta para el simulador y lista de precios.")
                    
                    es_archivada = str(r_data.get("Archivada", "")).lower() == "true"
                    nueva_archivada = st.checkbox("📦 Archivar Receta (Ocultar de Simulador, Precios y Ventas)", value=es_archivada)
                    
                    st.markdown("#### 📜 Monografía Técnica")
                    actual_tecnica = r_data.get("Tecnica", "") if pd.notna(r_data.get("Tecnica")) else ""
                    nueva_tecnica = st.text_area("Técnica de Elaboración", actual_tecnica)
                    
                    submitted_cabecera = st.form_submit_button("Guardar Cabecera")
                    
                    if submitted_cabecera:
                        df_r_latest = load_data("recetas")
                        match_r = df_r_latest[df_r_latest["Id"] == rid]
                        
                        if not match_r.empty:
                            idx_r = match_r.index[0]
                            df_r_latest.at[idx_r, "Nombre"] = nuevo_nombre
                            df_r_latest.at[idx_r, "Codigo"] = nuevo_codigo
                            if "Gramaje_Venta" not in df_r_latest.columns: df_r_latest["Gramaje_Venta"] = nueva_venta
                            df_r_latest.at[idx_r, "Gramaje_Venta"] = nueva_venta
                            
                            if "Archivada" not in df_r_latest.columns: df_r_latest["Archivada"] = False
                            df_r_latest.at[idx_r, "Archivada"] = nueva_archivada
                            
                            df_r_latest.at[idx_r, "Tecnica"] = nueva_tecnica
                            save_data("recetas", df_r_latest)
                            st.success("Cabecera y estado de archivo actualizado.")
                            st.rerun()
                        else:
                            st.error("No se encontró la receta en la nube para actualizar.")
                
                # Visualización del Código de Barras fuera del form
                st.markdown("#### 🏷️ Código de Barras Actual")
                html_barcode = generar_codigo_barras_html(actual_codigo, r_data["Nombre"])
                st.markdown(html_barcode, unsafe_allow_html=True)
                
                if st.button("🖨️ Preparar Vista de Impresión", key=f"print_btn_{rid}"):
                    st.session_state["print_mode_rid"] = rid
                    st.rerun()
                
                st.markdown("---")
                
                st.markdown("#### Detalles de Ingredientes (Editar en tabla)")
                
                detalles_actuales = df_rd[df_rd["Id_Receta"] == rid].copy()
                
                if not detalles_actuales.empty:
                    detalles_actuales = detalles_actuales.reset_index(drop=True)
                    
                    # LOGICA DE ORDENAMIENTO POR PESO Y TIPO (ANMAT)
                    # Prioridad: 0=Masa (kg, g), 1=Volumen (lt, ml), 2=Unidades
                    def get_sort_key(row):
                        unidad = str(row["Unidad_Consumo"]).lower().strip()
                        val_base = convertir_a_base(row["Cantidad"], unidad)
                        
                        if unidad in ['kg', 'g']:
                            prioridad = 0
                        elif unidad in ['lt', 'ml']:
                            prioridad = 1
                        else:
                            prioridad = 2
                            
                        # Retornamos tupla: (Prioridad ASC, Valor Descendente)
                        # Usamos -val_base para que al ordenar ascendente, los mayores queden arriba
                        return (prioridad, -val_base)

                    # Aplicar ordenamiento
                    detalles_actuales["_sort_key"] = detalles_actuales.apply(get_sort_key, axis=1)
                    detalles_actuales = detalles_actuales.sort_values(by="_sort_key", ascending=True)
                    detalles_actuales = detalles_actuales.drop(columns=["_sort_key"])
                    
                    edited_detalles = st.data_editor(
                        detalles_actuales[['Ingrediente', 'Cantidad', 'Unidad_Consumo']],
                        column_config={
                            "Ingrediente": st.column_config.SelectboxColumn(options=df_i["Nombre"].unique().tolist()), 
                            "Unidad_Consumo": st.column_config.SelectboxColumn(options=UNIDADES_CONSUMO)
                        },
                        key=f"editor_detalles_{rid}",
                        num_rows="dynamic",
                        hide_index=True
                    )

                    if st.button("Guardar Cambios en Ingredientes de Receta", key=f"save_detalles_{rid}", type="primary"):
                        edited_detalles = edited_detalles.dropna(subset=['Ingrediente', 'Cantidad', 'Unidad_Consumo'])

                        df_rd_clean = df_rd[df_rd["Id_Receta"] != rid]
                        
                        edited_detalles["Id_Receta"] = rid
                        df_rd_new = pd.concat([df_rd_clean, edited_detalles], ignore_index=True)
                        save_data("recetas_det", df_rd_new)
                        
                        # Auto-calcular Base_g como suma de ingredientes en g/kg
                        suma_g = sum(
                            convertir_a_base(row["Cantidad"], str(row["Unidad_Consumo"]).lower().strip())
                            for _, row in edited_detalles.iterrows()
                            if str(row["Unidad_Consumo"]).lower().strip() in ['g', 'kg']
                        )
                        if suma_g > 0:
                            df_r_sync = load_data("recetas")
                            idx_sync = df_r_sync[df_r_sync["Id"] == rid].index
                            if not idx_sync.empty:
                                df_r_sync.at[idx_sync[0], "Base_g"] = suma_g
                                save_data("recetas", df_r_sync)
                        
                        st.success(f"Ingredientes actualizados. Base recalculada: {suma_g:.0f}g")
                        st.rerun()
                else:
                    st.warning("No hay ingredientes en esta receta (o se han borrado). Puede agregar nuevos abajo.")
                    # Asegurar que edited_detalles exista aunque esté vacío, para que algo se pueda guardar si se agrega abajo
                    edited_detalles = pd.DataFrame(columns=['Ingrediente', 'Cantidad', 'Unidad_Consumo'])

                st.markdown("---")
                # Composición Química en Edición
                with st.expander("🎨 Ver Composición Química Porcentual"):
                    list_comp = []
                    # Usamos los detalles actuales (o los del editor si queremos tiempo real, 
                    # pero por ahora los actuales son más seguros)
                    for _, row_d in detalles_actuales.iterrows():
                        qty_g = convertir_a_base(row_d["Cantidad"], row_d["Unidad_Consumo"])
                        list_comp.append({'Ingrediente': row_d["Ingrediente"], 'Cantidad_g': qty_g})
                    
                    df_comp_edit = calculate_recipe_composition(list_comp, nueva_base)
                    if not df_comp_edit.empty:
                        st.table(df_comp_edit)
                    else:
                        st.info("No hay datos de peso para calcular la composición.")

                # Costo en Edición
                with st.expander("💰 Ver Costo de Materia Prima"):
                    costo_kg_edit, _ = calculate_recipe_cost_per_kg(rid, df_r, df_rd, df_i, cpp_map)
                    costo_lote_edit = (costo_kg_edit * nueva_base / 1000)
                    
                    col_ce1, col_ce2 = st.columns(2)
                    col_ce1.metric("Costo por KG", f"$ {costo_kg_edit:,.2f}")
                    col_ce2.metric("Costo Lote", f"$ {costo_lote_edit:,.2f}")
                    st.caption(f"Costo calculado para una base de {nueva_base}g.")

                st.markdown("---")
                st.markdown("#### ➕ Agregar Nuevo Ingrediente a esta Receta")
                
                col_add_i, col_add_c, col_add_u = st.columns([2, 1, 1])
                new_ing_add = col_add_i.selectbox("Ingrediente", df_i["Nombre"].unique(), key=f"add_ing_sel_{rid}")
                new_cant_add = col_add_c.number_input("Cantidad", 0.0, step=0.1, key=f"add_cant_sel_{rid}")
                new_unit_add = col_add_u.selectbox("Unidad", UNIDADES_CONSUMO, key=f"add_unit_sel_{rid}")
                
                if st.button("Agregar Ingrediente", key=f"btn_add_ing_{rid}"):
                    if new_cant_add > 0:
                        # 1. Recuperar lo que haya en el data_editor (si existe) o lo guardado
                        # Si el usuario editó la tabla Y luegos apretó "Agregar Ingrediente", idealmente querríamos guardar todo.
                        # Por simplicidad y robustez: Agregamos el nuevo a la base de datos directa y refrescamos.
                        # NOTA: Si el usuario hizo cambios en la tabla SIN guardar y aprieta este botón, esos cambios de tabla se perderían 
                        # si solo leemos df_rd. Pero `edited_detalles` tiene el estado actual del editor si se renderizó. 
                        
                        # Vamos a intentar fusionar:
                        # Si `edited_detalles` está definido (porque había datos o se creó vacío arriba), lo usamos como base.
                        
                        current_state_df = edited_detalles.copy() if 'edited_detalles' in locals() else detalles_actuales.copy()
                        
                        # Verificar si ya existe el ingrediente en la lista actual para sumar o avisar
                        if new_ing_add in current_state_df["Ingrediente"].values:
                             st.warning(f"El ingrediente '{new_ing_add}' ya está en la lista. Edite la cantidad en la tabla superior.")
                        else:
                            new_row = pd.DataFrame([{
                                "Ingrediente": new_ing_add, 
                                "Cantidad": new_cant_add, 
                                "Unidad_Consumo": new_unit_add,
                                "Id_Receta": rid  # Asegurar que tenga el ID
                            }])
                            
                            # Concatenar
                            # Si current_state_df no tiene Id_Receta, se lo ponemos
                            current_state_df["Id_Receta"] = rid
                            
                            final_list = pd.concat([current_state_df, new_row], ignore_index=True)
                            
                            # Guardar TODO: Limpiar lo viejo de esta receta y poner lo nuevo
                            df_rd_clean = df_rd[df_rd["Id_Receta"] != rid]
                            df_rd_new = pd.concat([df_rd_clean, final_list], ignore_index=True)
                            
                            save_data("recetas_det", df_rd_new)
                            
                            # Auto-calcular Base_g al agregar ingrediente
                            suma_g = sum(
                                convertir_a_base(row["Cantidad"], str(row["Unidad_Consumo"]).lower().strip())
                                for _, row in final_list.iterrows()
                                if str(row["Unidad_Consumo"]).lower().strip() in ['g', 'kg']
                            )
                            if suma_g > 0:
                                df_r_sync2 = load_data("recetas")
                                idx_sync2 = df_r_sync2[df_r_sync2["Id"] == rid].index
                                if not idx_sync2.empty:
                                    df_r_sync2.at[idx_sync2[0], "Base_g"] = suma_g
                                    save_data("recetas", df_r_sync2)
                            
                            st.success(f"Ingrediente '{new_ing_add}' agregado. Base recalculada: {suma_g:.0f}g")
                            st.rerun()
                    else:
                        st.error("La cantidad debe ser mayor a 0.")

                # --- NUEVA SECCIÓN: GALERÍA Y DOCUMENTACIÓN (POC) ---
                st.markdown("---")
                st.markdown(f"#### 📸 Galería & Documentos: {receta_a_editar}")
                st.caption("Espacio exclusivo para fotos de etiquetas, procesos o notas de esta receta.")
                
                # Definir ruta de la carpeta para esta receta
                base_docs_path = os.path.join("I:\\Mi unidad\\RojoMalbec_App", "receta_docs")
                recipe_docs_path = os.path.join(base_docs_path, str(int(rid)))
                
                if not os.path.exists(recipe_docs_path):
                    os.makedirs(recipe_docs_path, exist_ok=True)

                # --- NUEVO: LINK A DOCUMENTO DE TRABAJO (Google Docs) ---
                link_file = os.path.join(recipe_docs_path, "link_trabajo.txt")
                existing_link = ""
                if os.path.exists(link_file):
                    with open(link_file, "r") as f:
                        existing_link = f.read().strip()
                
                col_link, col_link_btn = st.columns([3, 1])
                new_link = col_link.text_input("🔗 Link a Google Doc (de Keep):", value=existing_link, key=f"link_input_{rid}", help="Pegá acá el link del documento que generaste desde Keep.")
                
                if new_link != existing_link:
                    if col_link_btn.button("💾 Guardar Link", key=f"save_link_{rid}"):
                        with open(link_file, "w") as f:
                            f.write(new_link)
                        st.success("Link guardado.")
                        st.rerun()
                
                if existing_link:
                    st.markdown(f'<a href="{existing_link}" target="_blank"><button style="background-color:#8b0000; color:white; border-radius:10px; border:none; padding:10px; width:100%; cursor:pointer;">📖 ABRIR DOCUMENTO DE TRABAJO</button></a>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                # Subida de Archivos
                uploaded_file = st.file_uploader("Subir foto, etiqueta o documento (PNG, JPG, PDF, DOCX)", type=["png", "jpg", "jpeg", "pdf", "docx", "doc"], key=f"uploader_{rid}")
                if uploaded_file is not None:
                    if st.button("💾 Confirmar y Guardar Archivo", key=f"save_file_btn_{rid}"):
                        file_path = os.path.join(recipe_docs_path, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.success(f"Archivo '{uploaded_file.name}' guardado correctamente.")
                
                # Visualizador de Galería y Documentos
                if os.path.exists(recipe_docs_path):
                    all_files = os.listdir(recipe_docs_path)
                    img_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    doc_files = [f for f in all_files if f.lower().endswith(('.pdf', '.docx', '.doc')) and not f.startswith("link_trabajo")]
                    
                    if img_files:
                        st.write(f"Imágenes y Etiquetas ({len(img_files)}):")
                        cols = st.columns(3)
                        for idx, filename in enumerate(img_files):
                            file_full_path = os.path.join(recipe_docs_path, filename)
                            with cols[idx % 3]:
                                st.image(file_full_path, use_container_width=True)
                                if st.button(f"🗑️ Borrar {filename[:10]}...", key=f"del_img_{rid}_{idx}"):
                                    os.remove(file_full_path)
                                    st.success(f"Eliminado: {filename}")
                                    st.rerun()
                                st.caption(filename)
                    
                    if doc_files:
                        st.write(f"Documentos Guardados ({len(doc_files)}):")
                        for idx, doc in enumerate(doc_files):
                            col_doc1, col_doc2 = st.columns([4, 1])
                            col_doc1.write(f"📄 {doc}")
                            if col_doc2.button("🗑️", key=f"del_doc_{rid}_{idx}"):
                                os.remove(os.path.join(recipe_docs_path, doc))
                                st.success(f"Documento eliminado: {doc}")
                                st.rerun()
                    
                    if not img_files and not doc_files:
                        st.info("No hay archivos guardados para este producto.")
        else:
            st.info("No hay recetas para editar.")

def render_print_view(rid):
    """Renderiza una vista limpia y profesional para imprimir."""
    df_r = get_df("recetas")
    df_rd = get_df("recetas_det")
    df_i = get_df("ingredientes")
    
    match_r = df_r[df_r["Id"] == rid]
    if match_r.empty:
        st.error("No se encontró la receta para imprimir.")
        return
    r_data = match_r.iloc[0]
    detalles = df_rd[df_rd["Id_Receta"] == rid]
    
    # 1. ENCABEZADO CON LOGO
    col_l, col_t = st.columns([1, 3])
    try:
        col_l.image("assets/logo_rojo_malbec.jpg", width=150)
    except:
        pass
    
    cod_disp = r_data.get("Codigo", "S/C") if pd.notna(r_data.get("Codigo")) and str(r_data.get("Codigo")).strip() != "" else "S/C"
    col_t.markdown(f"# FICHA TÉCNICA DE PRODUCTO")
    col_t.markdown(f"**{r_data['Nombre'].upper()}**")
    col_t.markdown(f"Receta Nº {int(rid)} | Código: **{cod_disp}** | Rojo Malbec")
    
    # Renderizar Código de Barras visual para impresión
    if cod_disp != "S/C":
        st.markdown(generar_codigo_barras_html(cod_disp, r_data["Nombre"]), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 2. DETALLES Y COMPOSICIÓN
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📋 Composición de Ingredientes")
        st.markdown(f"*Escala Base: {r_data['Base_g']}g*")
        for _, row in detalles.iterrows():
            st.write(f"- **{row['Ingrediente']}**: {row['Cantidad']} {row['Unidad_Consumo']}")
    
    with c2:
        st.markdown("### 🔬 Composición Química (%)")
        list_comp = []
        for _, row_d in detalles.iterrows():
            qty_g = convertir_a_base(row_d["Cantidad"], row_d["Unidad_Consumo"])
            list_comp.append({'Ingrediente': row_d["Ingrediente"], 'Cantidad_g': qty_g})
        
        df_comp = calculate_recipe_composition(list_comp, r_data["Base_g"])
        if not df_comp.empty:
            st.table(df_comp)
            
    st.markdown("---")
    
    # 3. PROTOCOLO TÉCNICO
    st.markdown("### ⚙️ Protocolo Técnico de Elaboración")
    tecnica = r_data.get("Tecnica", "")
    if tecnica and pd.notna(tecnica):
        st.write(tecnica)
    else:
        st.info("No hay protocolo definido para esta receta.")
    
    st.markdown("---")
    st.caption("Documento para uso interno y profesional. Rojo Malbec - Los Hornillos, Córdoba.")
    st.markdown('<style>@media print { button, .stButton {display: none !important;} }</style>', unsafe_allow_html=True)
