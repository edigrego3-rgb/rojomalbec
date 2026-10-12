import streamlit as st
import pandas as pd
import gspread

SHEET_NAME = "RojoMalbec DB"

def get_connection():
    if "gsheets_conn" not in st.session_state:
        try:
            creds_dict = {
                "type": st.secrets["gcp_service_account"]["type"],
                "project_id": st.secrets["gcp_service_account"]["project_id"],
                "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
                "private_key": st.secrets["gcp_service_account"]["private_key"],
                "client_email": st.secrets["gcp_service_account"]["client_email"],
                "client_id": st.secrets["gcp_service_account"]["client_id"],
                "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
                "token_uri": st.secrets["gcp_service_account"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
            }
            gc = gspread.service_account_from_dict(creds_dict)
            st.session_state["gsheets_conn"] = gc
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            return None
    return st.session_state["gsheets_conn"]

@st.cache_data(ttl=600) # Caché por 10 minutos para que sea rápido pero actualizado
def load_catalog_data():
    gc = get_connection()
    if not gc:
        return pd.DataFrame()
    
    try:
        sh = gc.open(SHEET_NAME)
        ws = sh.worksheet("recetas")
        raw_data = ws.get_all_values()
        
        if not raw_data:
            return pd.DataFrame()
            
        headers = [str(h).strip() for h in raw_data[0]]
        df = pd.DataFrame(raw_data[1:], columns=headers)
        
        # Filtrar solo columnas necesarias para el B2B
        cols_necesarias = ["Nombre", "Precio_Mayorista", "Precio_Venta", "PVP_Sugerido", "Markup_Revendedor", "Visible_B2B", "Archivada"]
        for col in cols_necesarias:
            if col not in df.columns:
                if col == "Visible_B2B":
                    df[col] = "1"  # Por defecto todos visibles
                elif col == "Archivada":
                    df[col] = "False"
                else:
                    df[col] = 0.0
                    
        # Excluir archivadas
        df = df[df["Archivada"].astype(str).str.lower() != "true"]
                
        # Limpiar números
        for col in ["Precio_Mayorista", "Precio_Venta", "PVP_Sugerido", "Markup_Revendedor"]:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
        
        # Parsear visibilidad: "1", "TRUE", "SI", "SÍ" = visible; todo lo demás = oculto
        df["Visible_B2B"] = df["Visible_B2B"].astype(str).str.strip().str.upper()
        df["Visible_B2B"] = df["Visible_B2B"].apply(lambda x: x in ["1", "TRUE", "SI", "SÍ", "YES", ""])
            
        # Filtrar solo los que tienen precio mayorista > 0
        df = df[df["Precio_Mayorista"] > 0]
        
        return df.sort_values("Nombre")
    except Exception as e:
        st.error(f"Error descargando datos: {e}")
        return pd.DataFrame()

def guardar_visibilidad(nombres_visibles, todos_los_nombres):
    """
    Guarda en la hoja de Google Sheets qué productos son visibles en el B2B.
    nombres_visibles: lista de nombres que deben estar visibles
    todos_los_nombres: lista de TODOS los nombres de productos
    """
    gc = get_connection()
    if not gc:
        return False
    
    try:
        sh = gc.open(SHEET_NAME)
        ws = sh.worksheet("recetas")
        raw_data = ws.get_all_values()
        headers = [str(h).strip() for h in raw_data[0]]
        
        # Buscar o crear la columna Visible_B2B
        if "Visible_B2B" in headers:
            col_idx = headers.index("Visible_B2B") + 1  # gspread usa 1-indexed
        else:
            # Agregar la columna al final
            col_idx = len(headers) + 1
            ws.update_cell(1, col_idx, "Visible_B2B")
        
        # Buscar la columna Nombre
        nombre_col_idx = headers.index("Nombre")
        
        # Actualizar cada fila
        celdas_a_actualizar = []
        for row_idx, row in enumerate(raw_data[1:], start=2):  # start=2 porque fila 1 es header
            nombre_fila = str(row[nombre_col_idx]).strip()
            if nombre_fila in nombres_visibles:
                valor = "1"
            elif nombre_fila in todos_los_nombres:
                valor = "0"
            else:
                continue
            celdas_a_actualizar.append(gspread.Cell(row_idx, col_idx, valor))
        
        if celdas_a_actualizar:
            ws.update_cells(celdas_a_actualizar)
        
        # Limpiar caché para que se reflejen los cambios
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"Error guardando visibilidad: {e}")
        return False

