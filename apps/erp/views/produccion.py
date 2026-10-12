
# views/produccion.py
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from modules.data_manager import get_df, save_data, calcular_stock_actual, consumir_stock_fifo, auto_generar_codigo
from modules.conversions import convertir_a_base
from modules.etiquetas_png import generar_etiqueta_lote_png

# OBSOLETO: Esta función ya no se usa. La nueva lógica permite input manual del gramaje.
# Se mantiene comentada por referencia histórica.
# 
# def detectar_envases_receta(rid, df_rd, factor, base_g):
#     """
#     Detecta el envase principal en una receta.
#     Prioriza ingredientes con 'envase' o 'frasco' pero ignora 'etiqueta'.
#     """
#     detalles = df_rd[df_rd["Id_Receta"] == rid]
#     
#     # 1. Prioridad: Que diga 'envase' o 'frasco' y NO diga 'etiqueta'
#     for _, row in detalles.iterrows():
#         ing = str(row["Ingrediente"]).lower()
#         uni = str(row["Unidad_Consumo"]).lower()
#         if ("envase" in ing or "frasco" in ing) and "etiqueta" not in ing and uni == "unidades":
#             cant = row["Cantidad"] * factor
#             return round(cant, 0), round((base_g * factor) / cant, 2) if cant > 0 else 0
#             
#     # 2. Prioridad: Cualquier ingrediente en 'unidades' que no sea etiqueta
#     for _, row in detalles.iterrows():
#         ing = str(row["Ingrediente"]).lower()
#         uni = str(row["Unidad_Consumo"]).lower()
#         if uni == "unidades" and "etiqueta" not in ing:
#             cant = row["Cantidad"] * factor
#             return round(cant, 0), round((base_g * factor) / cant, 2) if cant > 0 else 0
#
#     return 0, 0



def render_produccion_tab():
    st.subheader("🛒 Carrito de Producción: Requerimientos Consolidados y Costeo Real")
    
    df_r = get_df("recetas")
    df_rd = get_df("recetas_det")
    df_i = get_df("ingredientes")
    df_sl = get_df("stock_log")
    
    # Se calcula el stock actual para obtener el CPP
    df_stock_data = calcular_stock_actual(df_sl, df_i)
    cpp_map = df_stock_data.set_index("Ingrediente")["Costo_Ponderado"].to_dict()

    if df_r.empty:
        st.warning("Cree recetas en la pestaña 2 para usar la calculadora.")
    else:
        
        with st.expander("🖨️ Generar e Imprimir Etiqueta PNG para Inkjet", expanded=False):
            st.markdown("#### Generador de Etiquetas Adhesivas de Lote")
            
            recetas_nombres = df_r['Nombre'].tolist() if not df_r.empty else []
            prod_sel = st.selectbox("Seleccionar Producto / Blend / Té", options=["-- Seleccionar Producto --"] + recetas_nombres, key="prod_sel_etiqueta")
            
            lote_sugerido = f"L SLCH-{datetime.now().strftime('%d%m%y')}"
            if prod_sel and prod_sel != "-- Seleccionar Producto --":
                cod_pref = auto_generar_codigo(prod_sel)
                lote_sugerido = f"{cod_pref}-{datetime.now().strftime('%d%m%y')}"

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                p_rne = st.text_input("RNE / RNPA", value="RNE: 04006325 - RNPA E/T.", key="prod_rne_inp")
                p_lote = st.text_input("Código de Lote (Editable)", value=lote_sugerido, key=f"prod_lote_inp_{prod_sel}")
            with col_e2:
                p_elab = st.text_input("Fecha Elaboración", value=datetime.now().strftime("%m/%Y"), key="prod_elab_inp")
                # Vencimiento dinámico: mes/año de elaboración + 12 meses
                try:
                    elab_parts = p_elab.split("/")
                    elab_mes, elab_anio = int(elab_parts[0]), int(elab_parts[1])
                    vto_mes = elab_mes + 12
                    vto_anio = elab_anio
                    while vto_mes > 12:
                        vto_mes -= 12
                        vto_anio += 1
                    vto_default = f"{vto_mes:02d}/{vto_anio}"
                except:
                    vto_default = datetime.now().strftime("%m/%Y")
                p_vto = st.text_input("Fecha Vencimiento", value=vto_default, key="prod_vto_inp")
            
            png_data = generar_etiqueta_lote_png(p_rne, p_lote, p_elab, p_vto)
            st.image(png_data, caption=f"Vista previa para Inkjet - {p_lote}", width=380)
            st.download_button(
                label="🖼️ Descargar Etiqueta PNG (Para Impresora Inkjet)",
                data=png_data,
                file_name=f"etiqueta_{p_lote.replace(' ', '_')}.png",
                mime="image/png",
                use_container_width=True,
                key=f"btn_dl_etiqueta_png_{prod_sel}"
            )

        st.markdown("### Ingrese la Cantidad (kg) deseada para cada producto:")
        
        df_carrito = df_r.copy()
        df_carrito['Producir (kg)'] = 0.0
        
        edited_carrito = st.data_editor(
            df_carrito[['Nombre', 'Producir (kg)']],
            column_config={
                "Nombre": st.column_config.TextColumn(width="large"),
                "Producir (kg)": st.column_config.NumberColumn(min_value=0.0, default=0.0, step=1.0, width="small") 
            },
            key="carrito_produccion",
            hide_index=True,
            use_container_width=True
        )
        
        st.session_state['edited_carrito'] = edited_carrito

        if st.button("Calcular Requerimientos Consolidados", key="btn_calcular_req", type="primary"):
            st.session_state['ver_requerimientos'] = True
            # Inicializar los datos de fraccionamiento detectados
            st.session_state['fraccionamiento_manual'] = {}
            
        if st.session_state.get('ver_requerimientos', False):
            # Obtener datos del carrito
            recetas_a_producir = edited_carrito[edited_carrito['Producir (kg)'] > 0]
            
            if recetas_a_producir.empty:
                st.warning("Debe ingresar una cantidad a producir (kg) en al menos una receta.")
                st.session_state['ver_requerimientos'] = False
            else:
                requerimientos_consolidados = {}
                error_inconsistencia = False
                requerimientos_por_receta = {}

                for _, receta_row in recetas_a_producir.iterrows():
                    nombre_receta = receta_row['Nombre']
                    prod_kilos = receta_row['Producir (kg)']
                    
                    match_r = df_r[df_r["Nombre"] == nombre_receta]
                    if match_r.empty:
                        st.error(f"No se encontró la receta '{nombre_receta}'.")
                        error_inconsistencia = True; break
                    r_data = match_r.iloc[0]
                    rid = r_data["Id"]
                    base_g = r_data["Base_g"]
                    target_g = prod_kilos * 1000.0
                    factor = target_g / base_g if base_g > 0 else 0
                    
                    if factor == 0:
                        st.error(f"Error en Receta '{nombre_receta}': Base de la fórmula no puede ser cero.")
                        error_inconsistencia = True; break
                        
                    detalles_base = df_rd[df_rd["Id_Receta"] == rid]
                    costo_total_receta = 0
                    
                    for _, req in detalles_base.iterrows():
                        ingrediente = req["Ingrediente"]
                        unidad_receta = str(req["Unidad_Consumo"]).lower().strip()
                        if unidad_receta == 'nan':
                             st.error(f"Error de Unidad: El ingrediente '{ingrediente}' en '{nombre_receta}' tiene una unidad de consumo no definida.")
                             error_inconsistencia = True; break
                        
                        # FILTRO: Excluir packaging (unidades) de la tabla de requerimientos
                        # Los envases/etiquetas se gestionan en la sección de fraccionamiento
                        if unidad_receta == 'unidades':
                            continue  # Skip packaging items

                        cant_req = req["Cantidad"] * factor
                        cant_base_suma = convertir_a_base(cant_req, unidad_receta)
                        costo_unit_cpp = cpp_map.get(ingrediente, 0.0)
                        costo_item = cant_base_suma * costo_unit_cpp
                        costo_total_receta += costo_item
                        
                        # Acumulación Consolidada (solo ingredientes consumibles)
                        if ingrediente not in requerimientos_consolidados:
                            requerimientos_consolidados[ingrediente] = {
                                'Cantidad Requerida': cant_req,
                                'Unidad': unidad_receta,
                                'Cantidad_BASE_SUMA': cant_base_suma,
                                'Costo Estimado Total (CPP)': costo_item
                            }
                        else:
                            requerimientos_consolidados[ingrediente]['Cantidad Requerida'] += cant_req
                            requerimientos_consolidados[ingrediente]['Cantidad_BASE_SUMA'] += cant_base_suma
                            requerimientos_consolidados[ingrediente]['Costo Estimado Total (CPP)'] += costo_item
                    
                    
                    # Inicializar fraccionamiento con default si es primera vez
                    if nombre_receta not in st.session_state['fraccionamiento_manual']:
                        st.session_state['fraccionamiento_manual'][nombre_receta] = {
                            'Cantidad': 0,  # Se calculará automáticamente en la UI
                            'Gramaje': 100.0  # Default: 100g por envase
                        }


                    # Obtener código con fallback automático si está vacío o es nan
                    codigo_r = r_data.get('Codigo', "")
                    if pd.isna(codigo_r) or str(codigo_r).strip() == "" or str(codigo_r).lower() == "nan":
                        codigo_r = auto_generar_codigo(nombre_receta)

                    requerimientos_por_receta[nombre_receta] = {
                        'Id_Receta': rid,
                        'Kilos_Producidos': prod_kilos,
                        'Costo_Total_MateriaPrima': costo_total_receta,
                        'Lote': f"{codigo_r}-{datetime.now().strftime('%y%m%d')}"
                    }

                if not error_inconsistencia:
                    st.markdown("---")
                    st.success("✅ Cálculo de Requerimientos")
                    
                    df_final = pd.DataFrame.from_dict(requerimientos_consolidados, orient='index').reset_index().rename(columns={'index': 'Ingrediente'})
                    unidad_base_map = df_i.set_index("Nombre")["Unidad_Base"].to_dict()
                    df_final["Unidad_Base_Stock"] = df_final["Ingrediente"].map(unidad_base_map)
                    df_final["CPP_Unitario"] = df_final["Ingrediente"].map(cpp_map)

                    costo_total_final = df_final["Costo Estimado Total (CPP)"].sum()
                    st.metric("Costo Total Materia Prima", f"${costo_total_final:,.2f}")
                    
                    st.dataframe(df_final[['Ingrediente', 'Cantidad_BASE_SUMA', 'Unidad_Base_Stock', 'CPP_Unitario', 'Costo Estimado Total (CPP)']], use_container_width=True)
                        
                    st.markdown("---")
                    st.markdown("### 📦 Fraccionamiento y Envasado")
                    st.info("Elegí el gramaje por envase. El sistema calculará automáticamente cuántos envases necesitás.")
                    
                    # Mostrar editores para cada producto en la corrida
                    for producto in requerimientos_por_receta.keys():
                        kilos_producidos = requerimientos_por_receta[producto]['Kilos_Producidos']
                        total_gramos = kilos_producidos * 1000
                        
                        # Obtener datos previos o detectar automáticamente como default
                        data_frac = st.session_state['fraccionamiento_manual'].get(producto, {'Cantidad': 0, 'Gramaje': 0})
                        gramaje_default = data_frac['Gramaje'] if data_frac['Gramaje'] > 0 else 100.0
                        
                        st.markdown(f"**{producto}** — {kilos_producidos} kg a producir")
                        col_g, col_calc, col_info = st.columns([1, 1, 2])
                        
                        # INPUT: Usuario elige el gramaje por envase
                        gramaje = col_g.number_input(
                            f"Gramaje/envase (g)", 
                            value=float(gramaje_default),
                            min_value=1.0,
                            step=10.0,
                            key=f"inp_gramaje_{producto}"
                        )
                        
                        # CÁLCULO: Envases necesarios (automático)
                        envases_necesarios = round(total_gramos / gramaje) if gramaje > 0 else 0
                        col_calc.metric("Envases necesarios", f"{envases_necesarios} unidades")
                        
                        # INFO: Mostrar el cálculo
                        col_info.caption(f"Cálculo: {total_gramos:.0f}g ÷ {gramaje:.0f}g/envase = {envases_necesarios} envases")
                        
                        # GUARDAR para el registro del lote
                        st.session_state['fraccionamiento_manual'][producto] = {
                            'Cantidad': envases_necesarios,
                            'Gramaje': gramaje
                        }

                    st.markdown("---")
                    
                    # FIX BUG #6: Verificar stock antes de producir (aviso, no bloqueo)
                    stock_actual_map = df_stock_data.set_index("Ingrediente")["Stock_Actual"].to_dict()
                    ingredientes_faltantes = []
                    for ing, datos in requerimientos_consolidados.items():
                        stock_disponible = stock_actual_map.get(ing, 0.0)
                        cantidad_necesaria = datos["Cantidad_BASE_SUMA"]
                        if cantidad_necesaria > stock_disponible:
                            faltante = cantidad_necesaria - stock_disponible
                            unidad = datos.get("Unidad", "g")
                            ingredientes_faltantes.append(
                                f"- **{ing}**: Necesitás {cantidad_necesaria:,.3f}, tenés {stock_disponible:,.3f} (faltan {faltante:,.3f})"
                            )
                    
                    if ingredientes_faltantes:
                        st.warning(
                            "⚠️ **Aviso:** Los siguientes ingredientes no tienen stock suficiente registrado. "
                            "¿Olvidaste cargar una compra?\n\n" + "\n".join(ingredientes_faltantes) +
                            "\n\n*Podés producir igual, pero recordá cargar la compra después para que el stock y la trazabilidad queden bien.*"
                        )
                    
                    if st.button("🚀 CONFIRMAR Y REGISTRAR PRODUCCIÓN", key="btn_descargar", type="primary"):
                        df_sl_current = get_df("stock_log")
                        df_lp_current = get_df("lotes_produccion")
                        df_traz_current = get_df("lotes_produccion_det")
                        
                        nuevos_descargos = []
                        nuevos_lotes = []
                        nuevas_trazas = []
                        
                        for producto, data in requerimientos_por_receta.items():
                            lote_p = data['Lote']
                            
                            # 1. Registro del Lote (usando datos de fraccionamiento revisados)
                            frac = st.session_state['fraccionamiento_manual'].get(producto, {'Cantidad': 0, 'Gramaje': 0})
                            
                            nuevos_lotes.append({
                                "Lote_Produccion": lote_p,
                                "Id_Receta": data['Id_Receta'],
                                "Producto": producto,
                                "Kilos_Producidos": data['Kilos_Producidos'],
                                "Cantidad_Envases": frac['Cantidad'],
                                "Gramaje_Por_Envase": frac['Gramaje'],
                                "Costo_Total_MateriaPrima": data['Costo_Total_MateriaPrima'],
                                "Costo_Unitario_KG": data['Costo_Total_MateriaPrima'] / data['Kilos_Producidos'] if data['Kilos_Producidos'] > 0 else 0,
                                "Fecha_Produccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })

                            # 2. Descargos e Insumos (Trazabilidad)
                            p_match = df_r[df_r["Nombre"] == producto]
                            if p_match.empty:
                                st.error(f"Error crítico: No se encontró la receta para '{producto}'.")
                                continue
                            r_data = p_match.iloc[0]
                            factor_p = (data['Kilos_Producidos'] * 1000) / r_data["Base_g"] if r_data["Base_g"] > 0 else 1
                            detalles_p = df_rd[df_rd["Id_Receta"] == data['Id_Receta']]
                            
                            for _, req_p in detalles_p.iterrows():
                                ing = req_p["Ingrediente"]
                                cant_base = convertir_a_base(req_p["Cantidad"] * factor_p, str(req_p["Unidad_Consumo"]).lower())
                                
                                # FIFO y Trazabilidad
                                lotes_fifo = consumir_stock_fifo(ing, cant_base, df_sl_current)
                                for l_u in lotes_fifo:
                                    nuevas_trazas.append({
                                        "Lote_Produccion": lote_p,
                                        "Ingrediente": ing,
                                        "Cantidad_Usada": l_u['Cantidad_Usada'],
                                        "Unidad_Base": l_u['Unidad_Base'],
                                        "Lote_Proveedor": l_u['Lote_Proveedor'],
                                        "Fecha_Vencimiento": l_u['Fecha_Vencimiento']
                                    })
                                
                                # Registro en Log (Salida)
                                nuevos_descargos.append({
                                    "UUID": str(uuid.uuid4()),
                                    "Ingrediente": ing,
                                    "Cantidad": -cant_base,
                                    "Unidad_Base": unidad_base_map.get(ing, "kg"),
                                    "Tipo_Movimiento": "SALIDA",
                                    "Costo_Real": cpp_map.get(ing, 0.0),
                                    "Lote_Proveedor": lote_p,
                                    "Fecha_Movimiento": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })

                        # GUARDAR TODO
                        if nuevos_lotes:
                            save_data("lotes_produccion", pd.concat([df_lp_current, pd.DataFrame(nuevos_lotes)], ignore_index=True))
                        if nuevos_descargos:
                            save_data("stock_log", pd.concat([df_sl_current, pd.DataFrame(nuevos_descargos)], ignore_index=True))
                        if nuevas_trazas:
                            save_data("lotes_produccion_det", pd.concat([df_traz_current, pd.DataFrame(nuevas_trazas)], ignore_index=True))
                        
                        st.balloons()
                        st.success("✅ Producción registrada y stock actualizado.")
                        st.session_state['ver_requerimientos'] = False
                        if 'fraccionamiento_manual' in st.session_state: del st.session_state['fraccionamiento_manual']
                        st.rerun()
