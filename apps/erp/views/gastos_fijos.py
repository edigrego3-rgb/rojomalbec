# views/gastos_fijos.py
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from modules.data_manager import get_df, load_data, save_data

CATEGORIAS_GASTOS = [
    "🧹 Consumibles & Higiene (Cofias, Guantes, Papel, Sanitizantes)",
    "🖨️ Gráfica & Rotulado (Papel Autoadhesivo, Tintas, Ribbons)",
    "🏢 Estructura & Servicios (Alquiler, Luz, Agua, Internet)",
    "🚚 Logística & Envíos (Nafta, Viáticos, Encomiendas)",
    "💼 Fiscal & Administración (Monotributo, IIBB, Contador, Software)"
]

PERIODICIDAD_OPCIONES = [
    "Mensual (Recurrente)",
    "Ocasional / Compra Única",
    "Semanal / Por Lote"
]

def render_gastos_fijos_tab():
    st.subheader("💼 Control de Gastos Operativos y Estructura")
    st.info("ℹ️ **Uso Interno de Visualización:** Este módulo te permite llevar el control total de tus consumibles (cofias, guantes, tinta, alquiler, etc.) de forma prolija **sin alterar ni modificar los precios de venta** del Simulador.")

    # 1. Cargar Datos
    try:
        df_gastos = get_df("gastos_fijos")
    except:
        df_gastos = pd.DataFrame(columns=["UUID", "Fecha", "Categoria", "Item", "Monto", "Periodicidad", "Notas"])

    tab_registro, tab_tablero, tab_equilibrio = st.tabs([
        "📝 Registrar Gasto / Consumible", 
        "📊 Tablero de Control & Reportes", 
        "⚖️ Punto de Equilibrio & Métricas"
    ])

    # ---------------------------------------------------------
    # TAB 1: REGISTRAR GASTO
    # ---------------------------------------------------------
    with tab_registro:
        st.markdown("### ➕ Cargar Nuevo Gasto u Operativo")
        
        with st.form("form_nuevo_gasto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha_gasto = st.date_input("Fecha del Gasto", datetime.now())
                categoria_gasto = st.selectbox("Categoría del Gasto", CATEGORIAS_GASTOS)
                item_nombre = st.text_input("Ítem / Concepto", placeholder="Ej: 100u Cofias y Guantes de Nitrilo")
            
            with col2:
                monto_gasto = st.number_input("Monto Total ($)", min_value=0.0, step=500.0, format="%.2f")
                periodicidad_gasto = st.selectbox("Periodicidad / Frecuencia", PERIODICIDAD_OPCIONES)
                notas_gasto = st.text_input("Notas / Observaciones", placeholder="Ej: Compra en distribuidora central")

            btn_guardar = st.form_submit_button("💾 Guardar Registro de Gasto", type="primary", use_container_width=True)

            if btn_guardar:
                if not item_nombre.strip():
                    st.error("⚠️ El nombre del ítem o concepto es obligatorio.")
                elif monto_gasto <= 0:
                    st.error("⚠️ El monto debe ser mayor a 0.")
                else:
                    nuevo_registro = {
                        "UUID": str(uuid.uuid4())[:8],
                        "Fecha": fecha_gasto.strftime("%Y-%m-%d"),
                        "Categoria": categoria_gasto,
                        "Item": item_nombre.strip(),
                        "Monto": float(monto_gasto),
                        "Periodicidad": periodicidad_gasto,
                        "Notas": notas_gasto.strip()
                    }
                    
                    df_actual = load_data("gastos_fijos")
                    df_actualized = pd.concat([df_actual, pd.DataFrame([nuevo_registro])], ignore_index=True)
                    save_data("gastos_fijos", df_actualized)
                    st.cache_data.clear()
                    st.success(f"✅ Gasto '{item_nombre}' de $ {monto_gasto:,.2f} registrado correctamente.")
                    st.rerun()

    # ---------------------------------------------------------
    # TAB 2: TABLERO DE CONTROL & REPORTES
    # ---------------------------------------------------------
    with tab_tablero:
        st.markdown("### 📈 Historial y Distribución de Gastos")

        if df_gastos.empty:
            st.warning("Aún no hay gastos registrados. Utilizá la pestaña 'Registrar Gasto' para agregar el primero.")
        else:
            # Filtro por Fecha / Mes
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                cat_filtro = st.multiselect("Filtrar por Categoría", options=CATEGORIAS_GASTOS, default=CATEGORIAS_GASTOS)
            with col_f2:
                search_term = st.text_input("🔍 Buscar por palabra clave...", "")

            df_filt = df_gastos.copy()
            if cat_filtro:
                df_filt = df_filt[df_filt["Categoria"].isin(cat_filtro)]
            if search_term:
                df_filt = df_filt[df_filt["Item"].str.contains(search_term, case=False, na=False) | df_filt["Notas"].str.contains(search_term, case=False, na=False)]

            total_monto = df_filt["Monto"].sum()
            gastos_mensuales = df_filt[df_filt["Periodicidad"].str.contains("Mensual", na=False)]["Monto"].sum()
            gastos_ocasionales = df_filt[~df_filt["Periodicidad"].str.contains("Mensual", na=False)]["Monto"].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("💰 Total Gastos Filtrados", f"$ {total_monto:,.2f}")
            c2.metric("🏢 Gastos Fijos Mensuales", f"$ {gastos_mensuales:,.2f}")
            c3.metric("🧹 Consumibles / Ocasionales", f"$ {gastos_ocasionales:,.2f}")

            st.divider()

            # Resumen por Categoría
            st.markdown("#### 📊 Desglose por Categoría")
            cat_summary = df_filt.groupby("Categoria")["Monto"].sum().reset_index()
            cat_summary["Porcentaje"] = (cat_summary["Monto"] / total_monto * 100) if total_monto > 0 else 0
            
            st.dataframe(
                cat_summary.style.format({"Monto": "$ {:,.2f}", "Porcentaje": "{:.1f}%"}),
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.markdown("#### 📋 Detalle de Registros")
            st.dataframe(
                df_filt[["Fecha", "Categoria", "Item", "Monto", "Periodicidad", "Notas"]].sort_values("Fecha", ascending=False),
                use_container_width=True,
                hide_index=True
            )

            # Opción para eliminar registro
            st.markdown("---")
            with st.expander("🗑️ Eliminar un registro de gasto"):
                uuids_list = df_filt["UUID"].tolist()
                items_dict = {row["UUID"]: f"{row['Fecha']} - {row['Item']} (${row['Monto']:,.2f})" for _, row in df_filt.iterrows()}
                selected_uuid = st.selectbox("Seleccionar gasto a eliminar", options=uuids_list, format_func=lambda x: items_dict.get(x, x))
                
                if st.button("🔴 Confirmar Eliminación", type="primary"):
                    df_all = load_data("gastos_fijos")
                    df_all = df_all[df_all["UUID"] != selected_uuid]
                    save_data("gastos_fijos", df_all)
                    st.cache_data.clear()
                    st.success("Registro eliminado correctamente.")
                    st.rerun()

    # ---------------------------------------------------------
    # TAB 3: PUNTO DE EQUILIBRIO & MÉTRICAS DE ESTRUCTURA
    # ---------------------------------------------------------
    with tab_equilibrio:
        st.markdown("### ⚖️ Cálculo de Punto de Equilibrio (Break-Even Point)")
        st.info("Esta herramienta calcula **cuántos frascos de 50g necesitás vender al mes** exclusivamente para cubrir todos tus gastos fijos de estructura y consumibles.")

        total_gastos_est = df_gastos[df_gastos["Periodicidad"].str.contains("Mensual", na=False)]["Monto"].sum() if not df_gastos.empty else 0.0

        col_eq1, col_eq2 = st.columns(2)
        with col_eq1:
            g_fijos_input = st.number_input("Total Gastos Fijos Mensuales ($)", min_value=0.0, value=float(total_gastos_est), step=1000.0)
            precio_prom_frasco = st.number_input("Precio Promedio Venta Frasco ($)", min_value=1.0, value=5000.0, step=100.0)
        
        with col_eq2:
            costo_prom_frasco = st.number_input("Costo Materia Prima/Packaging por Frasco ($)", min_value=0.0, value=1250.0, step=50.0)
            margen_unitario = precio_prom_frasco - costo_prom_frasco
            st.metric("Margen Neto por Frasco", f"$ {margen_unitario:,.2f}")

        st.divider()

        if margen_unitario > 0 and g_fijos_input > 0:
            frascos_necesarios = int(g_fijos_input / margen_unitario) + 1
            kilos_necesarios = (frascos_necesarios * 50) / 1000.0
            facturacion_equilibrio = frascos_necesarios * precio_prom_frasco

            m_e1, m_e2, m_e3 = st.columns(3)
            m_e1.metric("📦 Frascos a Vender/Mes", f"{frascos_necesarios:,} unidades")
            m_e2.metric("⚖️ Kilos Totales a Vender", f"{kilos_necesarios:.2f} kg")
            m_e3.metric("💰 Facturación de Cobertura", f"$ {facturacion_equilibrio:,.2f}")

            st.success(f"🎯 **Objetivo de Cobertura:** Vendiendo **{frascos_necesarios} frascos al mes** ({kilos_necesarios:.2f} kg) cubrís el 100% de tus gastos fijos de $ {g_fijos_input:,.2f}. Todo lo que vendas a partir del frasco N° {frascos_necesarios + 1} es ganancia neta pura de bolsillo.")
        else:
            st.info("Ingresá tus gastos fijos mensuales y precios para calcular el punto de equilibrio.")

if __name__ == "__main__":
    render_gastos_fijos_tab()
