
# views/seguridad.py
import streamlit as st
import os
from modules.backup_manager import respaldo_local, respaldo_drive, BACKUP_BASE_DIR

def render_seguridad_tab():
    st.subheader("🛡️ Centro de Seguridad y Respaldos")
    st.info("Desde aquí puedes asegurar tu información tanto en tu computadora como en la nube.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💻 Respaldo en esta PC")
        st.write("Crea copias físicas comprimidas de todos tus datos (Ingredientes, Recetas, Stock, Ventas).")
        if st.button("🚀 Iniciar Respaldo Local", use_container_width=True):
            with st.spinner("Generando archivos locales..."):
                success, result = respaldo_local()
                if success:
                    st.success(f"¡Respaldo guardado exitosamente!")
                    st.code(f"Carpeta: {result}")
                else:
                    st.error(f"Error en respaldo local: {result}")
                    
    with col2:
        st.markdown("### ☁️ Réplica en Google Drive")
        st.write("Crea una copia completa de tu base de datos actual en tu unidad de Google Drive.")
        if st.button("📤 Crear Copia en la Nube", use_container_width=True):
            with st.spinner("Comunicando con Google Drive..."):
                success, result = respaldo_drive()
                if success:
                    st.success(f"¡Réplica creada en Drive con éxito!")
                    st.info(f"Nombre del archivo: {result}")
                else:
                    st.error(f"Error en réplica de Drive: {result}")

    st.divider()
    
    st.markdown("### 📂 Historial de Respaldos (Locales)")
    try:
        if os.path.exists(BACKUP_BASE_DIR):
            registros = [d for d in os.listdir(BACKUP_BASE_DIR) if os.path.isdir(os.path.join(BACKUP_BASE_DIR, d))]
            registros.sort(reverse=True)
            if registros:
                for r in registros[:5]: # Mostrar los últimos 5
                    st.text(f"📁 {r}")
            else:
                st.write("No se encontraron carpetas de respaldo todavía.")
    except Exception as e:
        st.write("No se pudo leer el historial de carpetas.")
