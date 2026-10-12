
# views/calculadora.py
import streamlit as st
import pandas as pd
from modules.data_manager import get_df, calculate_recipe_cost_per_kg, calcular_stock_actual

def render_calculadora_tab():
    st.header("💵 Calculadora de Precios al Público")
    st.info("Calculá cuánto cobrar según gramos, envases y gastos de luz/alquiler.")

    df_i = get_df("ingredientes")
    df_r = get_df("recetas")
    df_rd = get_df("recetas_det")
    df_sl = get_df("stock_log")
    
    df_stock_actual = calcular_stock_actual(df_sl, df_i)
    cpp_map = df_stock_actual.set_index("Ingrediente")["Costo_Ponderado"].to_dict()

    col_izq, col_der = st.columns([1, 1])

    with col_izq:
        st.subheader("1. Configuración")
        tipo_v = st.radio("¿Qué vas a vender?", ["Blend", "Especia Suelta"], horizontal=True, key="radio_final_v7")
        
        costo_kg_base = 0.0
        nombre_p = ""

        if tipo_v == "Blend":
            if not df_r.empty:
                sel_b = st.selectbox("Elegir Blend", df_r["Nombre"].unique(), key="sb_final_v7")
                match_r = df_r[df_r["Nombre"] == sel_b]
                if not match_r.empty:
                    rid = match_r["Id"].iloc[0]
                    costo_kg_base, _ = calculate_recipe_cost_per_kg(rid, df_r, df_rd, df_i, cpp_map)
                    nombre_p = sel_b
                else:
                    st.warning("No se encontró la información del blend.")
        else:
            if not df_i.empty:
                sel_e = st.selectbox("Elegir Especia", df_i["Nombre"].unique(), key="se_final_v7")
                costo_kg_base = cpp_map.get(sel_e, 0.0) * 1000
                nombre_p = sel_e

        gramos_v = st.number_input("Gramos a vender", min_value=1.0, value=50.0, step=1.0)
        
        st.subheader("2. Gastos de Estructura y Extras")
        c_envase = st.number_input("Costos de Envase y Etiquetas ($)", min_value=0.0, value=0.0, step=10.0)
        
        tipo_estructura = st.radio("Cargar gastos de estructura (Luz, Alquiler, etc.) por:", ["Porcentaje (%)", "Monto Fijo ($)"], horizontal=True)
        
        if tipo_estructura == "Porcentaje (%)":
            p_fijos = st.slider("% sobre el costo (Estructura)", 0, 100, 0)
            monto_fijo_est = 0.0
            st.caption("Aplica un porcentaje extra sobre (Materia Prima + Envase).")
        else:
            monto_fijo_est = st.number_input("Monto extra por esta venta ($)", min_value=0.0, value=0.0, step=50.0)
            p_fijos = 0
            st.caption("Suma un valor fijo directo al costo total.")

        with st.expander("❓ ¿Cómo calcular mi porcentaje de estructura?"):
            st.info("Sumá todos tus gastos fijos mensuales y dividilos por tu venta estimada.")
            col_calc1, col_calc2 = st.columns(2)
            g_luz = col_calc1.number_input("Luz/Gas mensual", value=0)
            g_alq = col_calc2.number_input("Alquiler/Monotributo", value=0)
            v_est = st.number_input("Venta mensual estimada ($)", value=1000000, step=100000)
            if v_est > 0:
                sugerido = ((g_luz + g_alq) / v_est) * 100
                st.write(f"**Porcentaje Sugerido: {sugerido:.1f}%**")

        st.subheader("3. Ganancia")
        m_ganancia = st.number_input("% Margen de Ganancia deseado", min_value=0.0, value=100.0, step=10.0)

    with col_der:
        st.subheader("📊 Análisis de Precio")
        if costo_kg_base > 0:
            # 1. Costo Materia Prima
            costo_mp = (costo_kg_base / 1000) * gramos_v
            
            # 2. Sumamos Envase
            subtotal_base = costo_mp + c_envase
            
            # 3. Aplicamos Estructura (Porcentaje o Fijo)
            if tipo_estructura == "Porcentaje (%)":
                gasto_est_valor = subtotal_base * (p_fijos / 100)
            else:
                gasto_est_valor = monto_fijo_est
            
            costo_total_operativo = subtotal_base + gasto_est_valor
            
            # 4. Precio Final con Ganancia
            precio_final = costo_total_operativo * (1 + m_ganancia / 100)
            ganancia_neta = precio_final - costo_total_operativo

            st.metric("PRECIO DE VENTA SUGERIDO", f"${precio_final:,.2f}")
            
            with st.expander("🔍 Ver desglose detallado"):
                st.write(f"Materia Prima ({gramos_v}g): ${costo_mp:,.2f}")
                st.write(f"Envase y etiquetas: ${c_envase:,.2f}")
                if gasto_est_valor > 0:
                    st.write(f"Gastos de Estructura: ${gasto_est_valor:,.2f}")
                st.divider()
                st.write(f"**COSTO TOTAL (MP + Envase + Estructura): ${costo_total_operativo:,.2f}**")
                st.success(f"**GANANCIA NETA ESTIMADA: ${ganancia_neta:,.2f}**")
                
                if precio_final > 0:
                    rentabilidad = (ganancia_neta / precio_final) * 100
                    st.caption(f"Margen de rentabilidad sobre precio de venta: {rentabilidad:.1f}%")
        else:
            st.warning("No hay costo base. Verificá que el producto seleccionado tenga precio cargado en el Stock.")

