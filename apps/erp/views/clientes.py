
# views/clientes.py
import streamlit as st
import pandas as pd
from modules.data_manager import get_df, save_data

def render_clientes_tab():
    st.subheader("👥 Gestión Comercial (Compradores y Fuerza de Venta)")

    tab_cli, tab_vend = st.tabs(["👥 Clientes", "🤝 Vendedores y Preventistas"])

    with tab_cli:
        df_c = get_df("clientes")
        
        col_new_c, col_list_c = st.columns([1, 2])
        
        with col_new_c:
            st.markdown("#### ➕ Alta de Nuevo Cliente")
            with st.form("form_crear_cliente", clear_on_submit=True):
                c_nom = st.text_input("Nombre / Razón Social").strip()
                c_cuit = st.text_input("CUIT / DNI")
                c_dir = st.text_input("Dirección")
                c_loc = st.text_input("Localidad")
                c_tel = st.text_input("Teléfono")
                
                if st.form_submit_button("Guardar Cliente"):
                    if c_nom:
                        max_id = df_c["Id"].max() if not df_c.empty else 0
                        new_id = max_id + 1 if max_id > 0 else 1
                        
                        new_cliente = {
                            "Id": float(new_id), 
                            "Nombre": c_nom, 
                            "CUIT": c_cuit,
                            "Direccion": c_dir,
                            "Localidad": c_loc,
                            "Telefono": c_tel
                        }
                        
                        new_df = pd.concat([df_c, pd.DataFrame([new_cliente])], ignore_index=True)
                        save_data("clientes", new_df)
                        st.success(f"Cliente '{c_nom}' guardado.")
                        st.rerun()
                    else:
                        st.error("El nombre es obligatorio.")

        with col_list_c:
            st.markdown("#### 📜 Lista de Clientes")
            if df_c.empty:
                st.info("No hay clientes registrados aún.")
            else:
                edited_clientes = st.data_editor(
                    df_c,
                    column_config={"Id": None},
                    use_container_width=True,
                    hide_index=True,
                    key="editor_clientes"
                )
                
                if st.button("💾 Guardar Cambios en Lista"):
                    save_data("clientes", edited_clientes)
                    st.success("Cambios guardados exitosamente.")
                    st.rerun()

                csv = df_c.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Exportar Clientes (CSV)", data=csv, file_name="clientes.csv", mime="text/csv")

    with tab_vend:
        import uuid
        df_v = get_df("vendedores")
        
        col_new_v, col_list_v = st.columns([1, 2])
        
        with col_new_v:
            st.markdown("#### ➕ Alta de Vendedor")
            st.info("Agregá a tus preventistas o revendedores para asociarlos a las ventas y calcular sus comisiones.")
            with st.form("form_crear_vendedor", clear_on_submit=True):
                v_nom = st.text_input("Nombre Completo o Empresa").strip()
                v_tel = st.text_input("Teléfono (Opcional)")
                v_clave = st.text_input("Clave de Acceso (App Preventa)")
                
                if st.form_submit_button("Guardar Vendedor"):
                    if v_nom:
                        if v_nom.lower().startswith("rojo malbec"):
                            st.error("Ese nombre ya está reservado por el sistema para tus ventas directas.")
                        else:
                            new_v = {
                                "UUID": str(uuid.uuid4()), 
                                "Nombre": v_nom, 
                                "Telefono": v_tel,
                                "Clave": v_clave if 'v_clave' in locals() else "",
                                "Activo": True
                            }
                            new_df_v = pd.concat([df_v, pd.DataFrame([new_v])], ignore_index=True) if not df_v.empty else pd.DataFrame([new_v])
                            save_data("vendedores", new_df_v)
                            st.success(f"Vendedor '{v_nom}' guardado.")
                            st.rerun()
                    else:
                        st.error("El nombre es obligatorio.")

        with col_list_v:
            st.markdown("#### 🤝 Equipo de Ventas Activo")
            if df_v.empty:
                st.info("No hay vendedores externos registrados. (Rojo Malbec Directo siempre está activo).")
            else:
                edited_v = st.data_editor(
                    df_v,
                    column_config={
                        "UUID": None, 
                        "Activo": st.column_config.CheckboxColumn("¿Activo?", default=True)
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="editor_vendedores"
                )
                
                if st.button("💾 Guardar Cambios", key="btn_save_vend"):
                    save_data("vendedores", edited_v)
                    st.success("Cambios guardados.")
                    st.rerun()
