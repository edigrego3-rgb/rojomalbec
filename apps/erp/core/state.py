# core/state.py
from pathlib import Path
import streamlit as st
import pandas as pd
from .io import cargar_csv

def get_paths(app_file: str):
    root = Path(app_file).parent
    data_dir = root / "data_v2"
    assets_dir = root / "assets"
    data_dir.mkdir(exist_ok=True)
    assets_dir.mkdir(exist_ok=True)
    archivos = {
        "ingredientes": data_dir / "ingredientes.csv",
        "proveedores": data_dir / "proveedores.csv",
        "compras": data_dir / "compras.csv",
        "lotes_ingredientes": data_dir / "lotes_ingredientes.csv",
        "recetas": data_dir / "recetas.csv",
        "recetas_detalle": data_dir / "recetas_detalle.csv",
        "produccion": data_dir / "produccion.csv",
        "produccion_lotes": data_dir / "produccion_lotes.csv",
        "stock_productos": data_dir / "stock_productos.csv",
        "clientes": data_dir / "clientes.csv",
        "ventas": data_dir / "ventas.csv",
        "gastos_fijos": data_dir / "gastos_fijos.csv",
        "margenes": data_dir / "margenes.csv",
        "stock_minimos": data_dir / "stock_minimos.csv",
        "stock_minimos_ing": data_dir / "stock_minimos_ing.csv",
        "movimientos_stock": data_dir / "movimientos_stock.csv",
    }
    return root, data_dir, assets_dir, archivos


def inicializar_estado(archivos):
    def init(nombre, columnas):
        if nombre not in st.session_state:
            st.session_state[nombre] = cargar_csv(archivos[nombre], columnas)

    init("ingredientes", {"Id": float, "Nombre": object, "Unidad_base": object, "Costo_unitario": float})
    init("proveedores", {
        "Id_Proveedor": float, "Nombre": object, "CUIT": object, "Telefono": object,
        "Email": object, "Direccion": object, "Notas": object
    })
    init("compras", {
        "Id_Compra": float, "Fecha_compra": object, "Proveedor": object,
        "Ingrediente": object, "Cantidad": float, "Unidad": object, "Precio_total": float,
        "Lote_proveedor": object, "Fecha_vencimiento": object, "Observaciones": object
    })
    init("lotes_ingredientes", {
        "Id_Lote": float, "Ingrediente": object, "Lote_proveedor": object,
        "Lote_interno": object, "Fecha_compra": object, "Fecha_vencimiento": object,
        "Stock_inicial": float, "Stock_actual": float
    })
    init("recetas", {
        "Id_Receta": float, "Nombre": object, "Codigo": object, "Tam_base": float,
        "Descripcion": object, "Ruta_foto": object, "Costo_total": float,
        "Vida_util_dias": float
    })
    init("recetas_detalle", {"Id_Receta": float, "Ingrediente": object, "Cantidad": float, "Unidad": object})
    init("produccion", {
        "Id_Prod": float, "Receta": object, "Codigo_receta": object,
        "Fecha": object, "Lote_producto": object, "Cantidad_producida": float
    })
    init("produccion_lotes", {
        "Id_Prod": float, "Ingrediente": object, "Lote_interno": object, "Cantidad_usada": float
    })
    init("stock_productos", {
        "Id": float, "Producto": object, "Lote_producto": object,
        "Cantidad_disponible": float, "Fecha_produccion": object,
        "Peso_unitario": float, "Fecha_vencimiento": object
    })
    init("clientes", {
        "Id_Cliente": float, "Nombre": object, "Tipo": object, "CUIT": object,
        "Telefono": object, "Email": object, "Direccion": object, "Localidad": object,
        "Provincia": object, "Lista_precios": object, "Notas": object
    })
    init("ventas", {
        "Id_Venta": float, "Fecha": object, "Cliente": object, "Tipo_cliente": object,
        "Producto": object, "Lote_producto": object, "Cantidad": float,
        "Precio_unitario": float, "Precio_total": float, "Forma_pago": object, "Notas": object
    })
    init("gastos_fijos", {"Id": float, "Categoria": object, "Monto_mensual": float, "Fecha": object, "Notas": object})
    init("margenes", {"Canal": object, "Margen": float})
    init("stock_minimos", {"Producto": object, "Minimo": float})
    init("stock_minimos_ing", {"Ingrediente": object, "Minimo": float})
    init("movimientos_stock", {
        "Id": float, "Fecha": object, "Tipo": object, "Origen": object,
        "Referencia": object, "Producto": object, "Ingrediente": object,
        "Detalle": object, "Cantidad": float, "Unidad": object
    })
