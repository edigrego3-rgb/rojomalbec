
# views/ingredientes.py
import streamlit as st
import pandas as pd
from modules.data_manager import get_df, save_data
from modules.conversions import UNIDADES_BASE

# Categorías disponibles
CATEGORIAS_INGREDIENTES = ["Especias", "Sales", "Envases", "Etiquetas", "Tés", "Frutas/Deshidratados", "Otros"]

def render_ingredientes_tab():
    st.subheader("🧂 Definición y Edición de Materiales (Costo Referencia)")
    df_i = get_df("ingredientes")
    
    # Asegurar que la columna Categoria existe
    if "Categoria" not in df_i.columns:
        df_i["Categoria"] = "Otros"
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Crear Nuevo Material")
        with st.form("form_crear_ingrediente"):
            n_nom = st.text_input("Nombre (ej: Pimienta, Frasco 50g)").strip()
            n_cat = st.selectbox("Categoría", CATEGORIAS_INGREDIENTES)
            n_uni = st.selectbox("Unidad Base de STOCK (g, ml, unidades)", UNIDADES_BASE)
            n_costo = st.number_input(f"Costo por 1 unidad base (REFERENCIA)", min_value=0.0) 
            
            if st.form_submit_button("Crear Material"):
                if n_nom and n_nom not in df_i["Nombre"].values:
                    max_id = df_i["Id"].max() if not df_i.empty and df_i["Id"].dtype != object else 0
                    new_id = max_id + 1 if max_id > 0 else 1
                    
                    new = {"Id": float(new_id), "Nombre": n_nom, "Unidad_Base": n_uni, "Categoria": n_cat, "Costo": n_costo}
                    
                    new_df = pd.DataFrame([new])
                    
                    save_data("ingredientes", pd.concat([df_i, new_df], ignore_index=True))
                    st.success("Ingrediente creado.")
                    st.rerun()
                elif n_nom:
                     st.warning("Ese ingrediente ya existe o falta el nombre.")
                else:
                    st.error("El nombre del material no puede estar vacío.")

    with col2:
        st.markdown("### ✍️ Editar / Eliminar Ingredientes")
        
        # Filtro por categoría
        categorias_filter = ["Todas"] + CATEGORIAS_INGREDIENTES
        cat_filtro = st.selectbox("Filtrar por Categoría", categorias_filter, key="filtro_cat_ing")
        
        if not df_i.empty:
            df_display = df_i.copy()
            
            # Aplicar filtro
            if cat_filtro != "Todas":
                df_display = df_display[df_display["Categoria"] == cat_filtro]
            
            df_display = df_display.drop(columns=['Id'])
            
            # Ordenar alfabéticamente
            df_display = df_display.sort_values("Nombre")
            
            edited_df = st.data_editor(
                df_display,
                key="edit_ingredientes",
                column_config={
                    "Nombre": st.column_config.TextColumn("Nombre"),
                    "Categoria": st.column_config.SelectboxColumn("Categoría", options=CATEGORIAS_INGREDIENTES, required=True),
                    "Unidad_Base": st.column_config.SelectboxColumn("Unidad", options=UNIDADES_BASE, required=True),
                    "Costo": st.column_config.NumberColumn(label="Costo Ref.", format="$%.4f"),
                    "Ultimo_Proveedor": st.column_config.TextColumn("Último Prov.")
                },
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True
            )
            
            if st.button("Guardar Cambios en Ingredientes", type="primary"):
                if len(edited_df) > 0:
                    # FIX BUG #3: Preservar IDs originales usando Nombre como clave
                    if cat_filtro == "Todas":
                        # Sin filtro: actualizar el DF completo
                        # Recuperar IDs originales por nombre
                        id_map = df_i.set_index("Nombre")["Id"].to_dict()
                        edited_df["Id"] = edited_df["Nombre"].map(id_map)
                        # Ingredientes nuevos (agregados con num_rows="dynamic") obtienen ID nuevo
                        max_id = df_i["Id"].max() if not df_i.empty else 0
                        for idx in edited_df[edited_df["Id"].isna()].index:
                            max_id += 1
                            edited_df.at[idx, "Id"] = float(max_id)
                        save_data("ingredientes", edited_df)
                    else:
                        # Con filtro: actualizar SOLO las filas de la categoría filtrada
                        # dentro del DataFrame original completo
                        df_completo = df_i.copy()
                        id_map = df_completo[df_completo["Categoria"] == cat_filtro].set_index("Nombre")["Id"].to_dict()
                        edited_df["Id"] = edited_df["Nombre"].map(id_map)
                        # Ingredientes nuevos
                        max_id = df_completo["Id"].max() if not df_completo.empty else 0
                        for idx in edited_df[edited_df["Id"].isna()].index:
                            max_id += 1
                            edited_df.at[idx, "Id"] = float(max_id)
                        # Reemplazar solo las filas de la categoría filtrada
                        df_completo = df_completo[df_completo["Categoria"] != cat_filtro]
                        df_completo = pd.concat([df_completo, edited_df], ignore_index=True)
                        save_data("ingredientes", df_completo)
                    
                    st.success("Cambios en ingredientes guardados.")
                    st.rerun()
                else:
                    if cat_filtro == "Todas":
                        save_data("ingredientes", pd.DataFrame(columns=df_i.columns))
                        st.warning("Todos los ingredientes han sido eliminados.")
                    st.rerun()
        else:
            st.info("Cargue ingredientes primero.")

