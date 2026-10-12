
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import uuid
from modules.data_manager import get_df, save_data

def render_pedidos_b2b():
    st.subheader("📦 Pedidos Mayoristas Pendientes")
    st.info("Revisá los pedidos B2B sincronizados desde el POS. Confirmalos para descontar stock y generar la venta.")
    
    try:
        df_pedidos = get_df("Pedidos_B2B")
    except Exception:
        st.warning("No se encontró la base de datos de Pedidos_B2B.")
        return

    if df_pedidos.empty:
        st.success("No hay pedidos B2B pendientes.")
        return
        
    pendientes = df_pedidos[df_pedidos["Estado"] == "Pendiente"]
    
    if pendientes.empty:
        st.success("No hay pedidos B2B pendientes.")
        return
        
    for idx, row in pendientes.iterrows():
        with st.expander(f"Pedido: {row['Cliente']} - {row['Fecha']} - Total: ${row['Total']}"):
            st.write(f"**ID Pedido:** {row['Pedido_ID']}")
            try:
                items = json.loads(row["Items_JSON"])
                df_items = pd.DataFrame(items)
                st.dataframe(df_items[["nombre", "cantidad", "precioFinal"]], use_container_width=True)
            except:
                st.write(row["Items_JSON"])
                
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Venta y Descontar Stock", key=f"conf_{idx}"):
                    confirmar_pedido(idx, row, df_pedidos)
                    st.rerun()
            with col2:
                if st.button("❌ Dar de Baja (Rechazar)", key=f"canc_{idx}"):
                    df_pedidos.at[idx, "Estado"] = "Cancelado"
                    save_data("Pedidos_B2B", df_pedidos)
                    st.rerun()

def confirmar_pedido(idx, row, df_pedidos):
    with st.spinner("Procesando pedido y descontando stock..."):
        try:
            items = json.loads(row["Items_JSON"])
        except:
            st.error("Error leyendo items del pedido.")
            return
            
        df_ventas = get_df("ventas")
        df_stock = get_df("lotes_produccion")
        df_recetas = get_df("recetas")
        
        info_recetas = {}
        for _, r in df_recetas.iterrows():
            info_recetas[" ".join(str(r["Nombre"]).lower().split())] = {
                "Gramaje": float(r["Base_g"]) if r["Base_g"] else 1000.0,
                "Nombre_Real": str(r["Nombre"])
            }
            
        nuevas_ventas = []
        fecha_vta = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        for it in items:
            nombre_clean = " ".join(str(it.get("nombre", "")).lower().split())
            cant = float(it.get("cantidad", 1))
            precio = float(it.get("precioFinal", 0))
            
            gramaje_g = info_recetas.get(nombre_clean, {}).get("Gramaje", 1000.0) # B2B suele ser por kilo
            kg_a_descontar = cant * (gramaje_g / 1000.0)
            precio_total_item = precio * cant
            
            lotes_prod = df_stock[df_stock["Producto"].apply(lambda x: " ".join(str(x).lower().split())) == nombre_clean] if not df_stock.empty else pd.DataFrame()
            
            if lotes_prod.empty:
                st.warning(f"Se vendió '{it.get('nombre')}' sin stock previo.")
                nuevas_ventas.append({"UUID": str(uuid.uuid4()), "Remito_ID": row["Pedido_ID"], "Lote_Produccion": f"SIN-LOTE: {it.get('nombre')}", "Cliente": row["Cliente"], "Forma_Pago": "B2B", "Cantidad_Vendida_KG": kg_a_descontar, "Precio_Venta_Unitario_KG": (precio_total_item / kg_a_descontar) if kg_a_descontar > 0 else 0, "Precio_Total": precio_total_item, "Ganancia_Neta": precio_total_item, "Fecha_Venta": fecha_vta, "Vendedor": "B2B POS", "Precio_Facturado_Cliente": precio_total_item, "Comision_Vendedor": 0.0, "Estado_Comision": ""})
                continue
                
            lotes_prod["Fecha_Produccion_DT"] = pd.to_datetime(lotes_prod["Fecha_Produccion"], errors='coerce')
            lotes_prod = lotes_prod.sort_values("Fecha_Produccion_DT")
            kg_restante = kg_a_descontar
            
            for idx_lote, lote_row in lotes_prod.iterrows():
                if kg_restante <= 0.001: break
                disponible = float(lote_row["KG_Disponibles"])
                if disponible <= 0.001: continue
                descuento = min(kg_restante, disponible)
                df_stock.at[idx_lote, "KG_Disponibles"] -= descuento
                kg_restante -= descuento
                precio_parcial = precio_total_item * (descuento / kg_a_descontar if kg_a_descontar > 0 else 0)
                ganancia = precio_parcial - (float(lote_row.get("Costo_Unitario_KG", 0)) * descuento)
                nuevas_ventas.append({"UUID": str(uuid.uuid4()), "Remito_ID": row["Pedido_ID"], "Lote_Produccion": str(lote_row["Lote_Produccion"]), "Cliente": row["Cliente"], "Forma_Pago": "B2B", "Cantidad_Vendida_KG": float(descuento), "Precio_Venta_Unitario_KG": float(precio_parcial / descuento if descuento > 0 else 0), "Precio_Total": float(precio_parcial), "Ganancia_Neta": float(ganancia), "Fecha_Venta": fecha_vta, "Vendedor": "B2B POS", "Precio_Facturado_Cliente": float(precio_parcial), "Comision_Vendedor": 0.0, "Estado_Comision": ""})
                
            if kg_restante > 0.001:
                ultimo_lote = lotes_prod.iloc[-1]
                df_stock.at[lotes_prod.index[-1], "KG_Disponibles"] -= kg_restante
                precio_parcial = precio_total_item * (kg_restante / kg_a_descontar if kg_a_descontar > 0 else 0)
                ganancia = precio_parcial - (float(ultimo_lote.get("Costo_Unitario_KG", 0)) * kg_restante)
                nuevas_ventas.append({"UUID": str(uuid.uuid4()), "Remito_ID": row["Pedido_ID"], "Lote_Produccion": str(ultimo_lote["Lote_Produccion"]), "Cliente": row["Cliente"], "Forma_Pago": "B2B", "Cantidad_Vendida_KG": float(kg_restante), "Precio_Venta_Unitario_KG": float(precio_parcial / kg_restante if kg_restante > 0 else 0), "Precio_Total": float(precio_parcial), "Ganancia_Neta": float(ganancia), "Fecha_Venta": fecha_vta, "Vendedor": "B2B POS", "Precio_Facturado_Cliente": float(precio_parcial), "Comision_Vendedor": 0.0, "Estado_Comision": ""})

        if nuevas_ventas:
            df_ventas = pd.concat([df_ventas, pd.DataFrame(nuevas_ventas)], ignore_index=True)
            save_data("ventas", df_ventas)
            
        save_data("lotes_produccion", df_stock)
        
        df_pedidos.at[idx, "Estado"] = "Confirmado"
        save_data("Pedidos_B2B", df_pedidos)
        st.success("¡Pedido confirmado y stock descontado con éxito!")
