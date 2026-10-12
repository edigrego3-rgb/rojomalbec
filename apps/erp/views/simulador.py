# views/simulador.py
import streamlit as st
import pandas as pd
from modules.data_manager import get_df, calcular_stock_actual, load_data, save_data
from modules.conversions import convertir_a_base

def render_simulador_tab():
    st.subheader("📊 Simulador de Precios")

    # 1. CARGA INICIAL
    try:
        df_r = get_df("recetas")
        # Ocultar recetas archivadas
        if "Archivada" not in df_r.columns: df_r["Archivada"] = False
        df_r = df_r[df_r["Archivada"].astype(str).str.lower() != "true"]
        
        df_rd = get_df("recetas_det")
        df_i = get_df("ingredientes")
        df_sl = get_df("stock_log")
    except:
        st.error("Error cargando datos."); return

    if df_r.empty:
        st.warning("No hay recetas."); return

    # --- [FIX DE ESTRUCTURA] ---
    if "Markup_Propio_Pct" not in df_r.columns:
        df_r["Markup_Propio_Pct"] = 0.0
    # ---------------------------

    # 2. SELECTOR DE PRODUCTO
    lista_prods = df_r["Nombre"].unique()
    prod_sel = st.selectbox("Seleccionar Producto", lista_prods, key="sel_final_visual_fix")
    
    row_prod = df_r[df_r["Nombre"] == prod_sel].iloc[0]
    rid = row_prod["Id"] 

    # 3. CARGA DE DATOS (Variables Base)
    if 'last_rid_vis' not in st.session_state or st.session_state.last_rid_vis != rid:
        st.session_state.last_rid_vis = rid
        
        def get_val(col, default=0):
            val = row_prod.get(col)
            try: return int(float(val)) if pd.notnull(val) else default
            except: return default

        def get_iibb(col, default=3.0):
            val = row_prod.get(col)
            try: return float(val) if pd.notnull(val) else default
            except: return default

        st.session_state['base_gastos'] = get_val('Gastos_Fijos_Pct', 0)
        st.session_state['base_iibb'] = get_iibb('IIBB_Pct', 0.0)
        st.session_state['base_iva'] = get_val('IVA_Pct', 21)
        st.session_state['base_fab'] = get_val('Margen_Fabrica_Pct', 0)
        st.session_state['base_may'] = get_val('Markup_Mayorista', 0)
        st.session_state['base_rev'] = get_val('Markup_Revendedor', 0)
        st.session_state['base_propio'] = get_val('Markup_Propio_Pct', 0)
        
        # --- [FIX GRAMOS] Cargar gramaje de venta de la BD al cambiar producto ---
        # Priorizar Gramaje_Venta, con fallback a Base_g o 100.0
        g_venta = row_prod.get('Gramaje_Venta')
        if pd.isnull(g_venta) or g_venta <= 0:
            g_venta = row_prod.get('Base_g', 100.0)
            
        st.session_state['num_vis'] = float(g_venta) if pd.notnull(g_venta) and g_venta > 0 else 100.0
        # ----------------------------------------------------------------
        
        st.rerun()

    # 4. CÁLCULO DE COSTOS
    c1, c2 = st.columns(2)
    granel = c1.toggle("Modo Granel", key="tg_vis")
    gramos = c2.number_input("Gramos", min_value=1.0, step=10.0, key="num_vis")

    stock = calcular_stock_actual(df_sl, df_i)
    precios_map = stock.set_index("Ingrediente")["Costo_Ponderado"].to_dict()

    col_id_rec = "Id_Receta" if "Id_Receta" in df_rd.columns else "Receta_Id"
    mis_ingredientes = df_rd[df_rd[col_id_rec] == rid].copy()

    mis_ingredientes = mis_ingredientes.merge(df_i[["Nombre", "Categoria"]], left_on="Ingrediente", right_on="Nombre", how="left")
    if "Nombre_y" in mis_ingredientes.columns: mis_ingredientes["Nombre"] = mis_ingredientes["Nombre_y"].fillna(mis_ingredientes["Ingrediente"])
    elif "Nombre" not in mis_ingredientes.columns: mis_ingredientes["Nombre"] = mis_ingredientes["Ingrediente"]

    mis_ingredientes["Costo_Unitario"] = mis_ingredientes["Nombre"].map(precios_map).fillna(0.0)
    mis_ingredientes["Cantidad_Base"] = mis_ingredientes.apply(
        lambda row: convertir_a_base(row["Cantidad"], str(row["Unidad_Consumo"]).lower().strip()) if "Unidad_Consumo" in row.index else row["Cantidad"], axis=1)
    mis_ingredientes["Costo_Total_Linea"] = mis_ingredientes["Cantidad_Base"] * mis_ingredientes["Costo_Unitario"]

    if granel:
        mask = mis_ingredientes['Categoria'].isin(['Envases', 'Etiquetas']) | mis_ingredientes['Nombre'].str.contains('Envase|Etiqueta|Cinta', case=False, na=False)
        mis_ingredientes = mis_ingredientes[~mask]

    costo_mp_real = (mis_ingredientes["Costo_Total_Linea"].sum() / 1000.0) * gramos

    st.divider()

    opciones = ["1. Materia Prima 🥩", "2. Operación ⚙️", "3. Fábrica 🏭", "4. ESTRATEGIA COMERCIAL 💰"]
    seccion = st.selectbox("📍 IR A SECCIÓN:", opciones, key="nav_vis")
    st.markdown("---")

    k_gastos = f"gv_{rid}"
    k_iibb = f"iv_{rid}"
    k_iva = f"av_{rid}"
    k_fab = f"fv_{rid}"
    k_propio = f"pv_{rid}"
    k_may = f"mv_{rid}"
    k_rev = f"rv_{rid}"

    if "1." in seccion:
        st.dataframe(mis_ingredientes[["Nombre", "Cantidad", "Costo_Unitario", "Costo_Total_Linea"]], use_container_width=True)
        st.metric("COSTO MATERIA PRIMA", f"$ {costo_mp_real:,.2f}")

    elif "2." in seccion:
        st.info("⚙️ Configura tus costos operativos.")
        v_gastos = st.slider("% Gastos Fijos", 0, 100, value=st.session_state.base_gastos, step=1, key=k_gastos)
        val_iibb_safe = float(st.session_state.base_iibb)
        if val_iibb_safe > 100.0: val_iibb_safe = 100.0
        v_iibb = st.number_input("% IIBB", 0.0, 100.0, value=val_iibb_safe, step=0.5, key=k_iibb)
        v_iva = st.selectbox("% IVA", [0.0, 10.5, 21.0], index=2, key=k_iva)
        
        st.session_state.base_gastos = v_gastos
        st.session_state.base_iibb = v_iibb
        st.session_state.base_iva = int(v_iva)
        costo_op = (costo_mp_real * (1 + v_gastos/100)) * (1 + v_iibb/100)
        st.metric("COSTO OPERATIVO TOTAL", f"$ {costo_op:,.2f}")

    elif "3." in seccion:
        st.info("🏭 Ganancia de Fábrica.")
        cg = st.session_state[k_gastos] if k_gastos in st.session_state else st.session_state.base_gastos
        ci = st.session_state[k_iibb] if k_iibb in st.session_state else st.session_state.base_iibb
        c_op = (costo_mp_real * (1 + cg/100)) * (1 + ci/100)
        v_fab = st.slider("% Margen Fábrica (Base)", 0, 300, value=st.session_state.base_fab, step=1, key=k_fab)
        st.session_state.base_fab = v_fab
        precio_fabrica = c_op * (1 + v_fab/100)
        c_izq, c_der = st.columns(2)
        c_izq.metric("PRECIO FÁBRICA", f"$ {precio_fabrica:,.2f}")
        c_der.metric("Ganancia Neta", f"$ {precio_fabrica - c_op:,.2f}")

    elif "4." in seccion:
        cg = st.session_state[k_gastos] if k_gastos in st.session_state else st.session_state.base_gastos
        ci = st.session_state[k_iibb] if k_iibb in st.session_state else st.session_state.base_iibb
        cf = st.session_state[k_fab] if k_fab in st.session_state else st.session_state.base_fab
        c_op = (costo_mp_real * (1 + cg/100)) * (1 + ci/100)
        p_fab = c_op * (1 + cf/100)

        st.markdown("### 🏷️ Estrategia de Canales")
        st.info(f"🔑 Precio Base Fábrica: **$ {p_fab:,.2f}**")
        st.divider()

        c_izq, c_der = st.columns(2)
        with c_izq:
            st.success("🏠 TU NEGOCIO")
            v_propio = st.slider("% Markup Tu Local", 0, 400, value=st.session_state.base_propio, step=1, key=k_propio)
            st.session_state.base_propio = v_propio
            precio_tu_local = p_fab * (1 + v_propio/100)
            st.metric("Cálculo Matemático", f"$ {precio_tu_local:,.2f}", delta="Mostrador")

        with c_der:
            st.info("📦 MAYORISTA")
            v_may = st.slider("% Markup al Mayorista", 0, 300, value=st.session_state.base_may, step=1, key=k_may)
            st.session_state.base_may = v_may
            precio_mayorista = p_fab * (1 + v_may/100)
            st.write(f"Cálculo Matemático: **$ {precio_mayorista:,.2f}**")
            st.markdown("---")
            v_rev = st.slider("% Markup Revendedor", 0, 300, value=st.session_state.base_rev, step=1, key=k_rev)
            st.session_state.base_rev = v_rev
            p_sug = precio_mayorista * (1 + v_rev/100)
            st.metric("Cálculo Matemático", f"$ {p_sug:,.2f}", delta="PVP")

        st.divider()
        st.markdown("### 🎯 Ajuste Final (Redondeo Manual)")
        st.caption("Los sliders de arriba calculan el precio exacto. Usá estas cajas para redondear el precio final que querés guardar.")
        
        # Leemos directo de la Base de Datos (de la receta seleccionada row_prod)
        db_loc = float(row_prod.get("Precio_Venta", 0.0)) if pd.notnull(row_prod.get("Precio_Venta")) else 0.0
        db_may = float(row_prod.get("Precio_Mayorista", 0.0)) if pd.notnull(row_prod.get("Precio_Mayorista")) else 0.0
        db_sug = float(row_prod.get("PVP_Sugerido", 0.0)) if pd.notnull(row_prod.get("PVP_Sugerido")) else 0.0
        
        # Iniciamos con el valor guardado en BD, si es 0, usamos la matemática del slider
        init_loc = db_loc if db_loc > 0 else float(round(precio_tu_local, 2))
        init_may = db_may if db_may > 0 else float(round(precio_mayorista, 2))
        init_sug = db_sug if db_sug > 0 else float(round(p_sug, 2))

        col_m1, col_m2, col_m3 = st.columns(3)
        final_local = col_m1.number_input("Precio Minorista ($)", value=init_loc, step=50.0, key=f"inp_loc_{rid}")
        final_may = col_m2.number_input("Precio Mayorista ($)", value=init_may, step=50.0, key=f"inp_may_{rid}")
        final_sug = col_m3.number_input("PVP Sugerido ($)", value=init_sug, step=50.0, key=f"inp_sug_{rid}")

        st.divider()
        if st.button("💾 GUARDAR TODOS LOS CAMBIOS", type="primary", use_container_width=True):
            df = load_data("recetas")
            idx = df[df["Id"] == rid].index[0]
            
            f_propio = st.session_state[k_propio] if k_propio in st.session_state else st.session_state.base_propio
            f_may = st.session_state[k_may] if k_may in st.session_state else st.session_state.base_may
            f_rev = st.session_state[k_rev] if k_rev in st.session_state else st.session_state.base_rev
            f_gastos = st.session_state[k_gastos] if k_gastos in st.session_state else st.session_state.base_gastos
            f_iibb = st.session_state[k_iibb] if k_iibb in st.session_state else st.session_state.base_iibb
            f_fab = st.session_state[k_fab] if k_fab in st.session_state else st.session_state.base_fab

            # Usar los valores manuales de las cajitas para la base de datos
            df.at[idx, "Precio_Venta"] = float(final_local)      
            df.at[idx, "Precio_Mayorista"] = float(final_may)
            df.at[idx, "PVP_Sugerido"] = float(final_sug) 
            df.at[idx, "Gastos_Fijos_Pct"] = f_gastos
            df.at[idx, "IIBB_Pct"] = f_iibb
            df.at[idx, "IVA_Pct"] = st.session_state.base_iva
            df.at[idx, "Margen_Fabrica_Pct"] = f_fab
            df.at[idx, "Markup_Mayorista"] = f_may
            df.at[idx, "Markup_Revendedor"] = f_rev
            df.at[idx, "Markup_Propio_Pct"] = int(f_propio)
            
            # --- [GUARDAR GRAMOS] Guardamos en Gramaje_Venta, NO en Base_g ---
            if "Gramaje_Venta" in df.columns:
                df.at[idx, "Gramaje_Venta"] = float(gramos)
            
            save_data("recetas", df)
            st.cache_data.clear()
            st.success("✅ Guardado Exitoso!")
            st.rerun()

if __name__ == "__main__":
    render_simulador_tab()