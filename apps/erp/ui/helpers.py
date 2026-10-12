# ui/helpers.py
from datetime import datetime
import base64
import pandas as pd
import streamlit as st
from .style import green_card

def cargar_logo_base64(ruta):
    if not ruta.exists():
        return None
    with open(ruta, "rb") as img:
        return base64.b64encode(img.read()).decode()

def generar_lote(archivos, prefijo):
    hoy = datetime.now().strftime("%d%m%Y")
    base = f"RM-{prefijo}-{hoy}"
    archivo = archivos["lotes_ingredientes"]
    if archivo.exists():
        df = pd.read_csv(archivo)
        if "Lote_interno" in df.columns:
            coinc = df[df["Lote_interno"].astype(str).str.contains(base, na=False)]
            numero = len(coinc) + 1
        else:
            numero = 1
    else:
        numero = 1
    return f"{base}-{str(numero).zfill(2)}"

def registrar_movimiento(archivos, tipo, origen, referencia, detalle, cantidad, unidad, producto=None, ingrediente=None):
    mov = st.session_state.movimientos_stock
    nuevo_id = 1 if mov.empty else int(mov["Id"].max()) + 1
    nuevo = {
        "Id": float(nuevo_id),
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Tipo": tipo,
        "Origen": origen,
        "Referencia": referencia,
        "Producto": producto if producto is not None else "",
        "Ingrediente": ingrediente if ingrediente is not None else "",
        "Detalle": detalle,
        "Cantidad": float(cantidad),
        "Unidad": unidad,
    }
    mov = pd.concat([mov, pd.DataFrame([nuevo])], ignore_index=True)
    st.session_state.movimientos_stock = mov
    mov.to_csv(archivos["movimientos_stock"], index=False)
