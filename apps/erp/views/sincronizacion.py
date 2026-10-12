import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime
from modules.data_manager import get_df, save_data, load_data, append_data


def render_sincronizacion_tab():
    """Pestaña principal con sub-pestañas: Buzón de entrada y Pedidos B2B."""
    st.subheader("📲 Sincronización y Pedidos")

    t1, t2 = st.tabs(["📥 Buzón de Entrada (POS)", "📦 Pedidos Mayoristas Pendientes"])

    with t2:
        from views.pedidos_b2b import render_pedidos_b2b
        render_pedidos_b2b()

    with t1:
        st.info("Acá llegan automáticamente los datos que enviás desde la feria o la calle.")

        try:
            df_buzon = get_df("Buzon_POS")
        except Exception:
            st.warning("No se pudo conectar con el buzón. Asegurate de que la pestaña 'Buzon_POS' exista.")
            return

        if df_buzon.empty:
            st.success("✔️ El buzón está vacío. No hay ventas pendientes de procesar.")
            return

        col_estado = [c for c in df_buzon.columns if "estado" in c.lower()]
        if not col_estado:
            st.error("Error crítico: La pestaña del buzón no tiene una columna 'Estado'.")
            return
        col_estado = col_estado[0]

        pendientes = df_buzon[df_buzon[col_estado].astype(str).str.upper() == "PENDIENTE"]

        if pendientes.empty:
            st.success("✔️ Todos los paquetes recibidos ya fueron procesados.")
            return

        st.warning(f"🔔 Tenés {len(pendientes)} paquete(s) de datos esperando ser procesados.")

        for idx, row in pendientes.iterrows():
            fecha_paquete = row.get("Fecha_Sincronizacion", "Fecha Desconocida")
            payload_str = str(row.get("Payload_JSON", "{}"))

            try:
                datos = json.loads(payload_str)
                cant_ventas = len(datos.get("ventas", []))
                cant_mayoristas = len(datos.get("pedidos_mayoristas", []))
                cant_contactos = len(datos.get("contactos_b2b", []))

                resumen = f"Paquete del {fecha_paquete} — Ventas: {cant_ventas} | B2B: {cant_mayoristas} | Contactos: {cant_contactos}"

                with st.expander(resumen):
                    st.json(datos)

                    if st.button("⚙️ Procesar este Paquete", key=f"proc_{idx}", type="primary"):
                        _procesar_paquete(datos, idx, df_buzon, col_estado)

            except json.JSONDecodeError:
                st.error(f"El paquete de la fila {idx} tiene un error de formato (JSON corrupto).")
                if st.button("🗑️ Descartar paquete roto", key=f"del_{idx}"):
                    df_buzon.at[idx, col_estado] = "ERROR_FORMATO"
                    save_data("Buzon_POS", df_buzon)
                    st.rerun()


def _procesar_paquete(datos, idx_buzon, df_buzon, col_estado):
    """Procesa un paquete completo: Potenciales + Pedidos B2B a staging + Ventas Feria FIFO."""
    with st.spinner("Procesando paquete..."):
        ventas_feria = datos.get("ventas", [])
        pedidos_b2b = datos.get("pedidos_mayoristas", [])
        contactos_b2b = datos.get("contactos_b2b", [])

        # ============================================
        # 1. POTENCIALES (contactos de WhatsApp)
        # ============================================
        nuevos_leads = 0
        if contactos_b2b:
            try:
                df_pot = load_data("Potenciales")
            except Exception:
                df_pot = pd.DataFrame(columns=["Nombre", "Telefono", "Origen", "Fecha_Alta"])

            nuevos_pot = []
            for lead in contactos_b2b:
                tel = str(lead.get("contacto", "")).strip()
                nom = str(lead.get("nombre", "")).strip()
                tipo = str(lead.get("tipo", "feria")).strip()

                existe = False
                if not df_pot.empty:
                    if tel and tel in df_pot["Telefono"].astype(str).values:
                        existe = True
                    elif nom and nom in df_pot["Nombre"].astype(str).values:
                        existe = True

                if not existe and nom:
                    nuevos_pot.append({
                        "Nombre": nom,
                        "Telefono": tel,
                        "Origen": tipo.capitalize(),
                        "Fecha_Alta": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    nuevos_leads += 1

            if nuevos_pot:
                append_data("Potenciales", pd.DataFrame(nuevos_pot))

        # ============================================
        # 2. PEDIDOS B2B → STAGING (sin descontar stock)
        # ============================================
        nuevos_pedidos = 0
        if pedidos_b2b:
            lista_pendientes = []
            for p in pedidos_b2b:
                lista_pendientes.append({
                    "Pedido_ID": p.get("id", str(uuid.uuid4())),
                    "Fecha": p.get("fecha", ""),
                    "Cliente": p.get("cliente", "Mayorista B2B"),
                    "Items_JSON": json.dumps(p.get("items", [])),
                    "Total": p.get("total", 0),
                    "Estado": "Pendiente"
                })
            append_data("Pedidos_B2B", pd.DataFrame(lista_pendientes))
            nuevos_pedidos = len(lista_pendientes)

        # ============================================
        # 3. VENTAS DE FERIA → FIFO (descontar stock)
        # ============================================
        cant_ventas_ok = 0
        if ventas_feria:
            # Cargar bases de datos frescas para exactitud matemática
            df_v = load_data("ventas")
            df_lp = load_data("lotes_produccion")
            df_r = load_data("recetas")
            df_ing = load_data("ingredientes")

            nuevas_ventas = []
            nuevos_mov_stock = []

            # Mapear costo de insumos (ej: Bolsa de Friselina)
            costo_insumos = {}
            if not df_ing.empty:
                for _, row in df_ing.iterrows():
                    nombre = str(row.get("Nombre", "")).strip().lower()
                    costo_insumos[nombre] = float(row.get("Costo", 0))

            # Pre-calcular stock disponible por lote
            ventas_por_lote = (
                df_v.groupby("Lote_Produccion")["Cantidad_Vendida_KG"].sum().to_dict()
                if not df_v.empty else {}
            )
            df_stock = df_lp.copy()
            if not df_stock.empty:
                df_stock["KG_Vendidos"] = df_stock["Lote_Produccion"].map(ventas_por_lote).fillna(0)
                df_stock["KG_Disponibles"] = df_stock["Kilos_Producidos"] - df_stock["KG_Vendidos"]

            # Mapeo de gramajes desde recetas
            info_recetas = {}
            for _, row in df_r.iterrows():
                nombre_clean = " ".join(str(row["Nombre"]).lower().split())
                info_recetas[nombre_clean] = {
                    "Gramaje": float(row.get("Gramaje_Venta", 100)) if pd.notna(row.get("Gramaje_Venta")) else 100.0,
                    "Nombre_Real": str(row["Nombre"])
                }

            # --- Bucle principal FIFO ---
            for ticket in ventas_feria:
                tkt_id = ticket.get("id", str(uuid.uuid4()))
                forma_pago = ticket.get("medio", "Efectivo")
                fecha_tkt = ticket.get("fecha", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                fecha_tkt = fecha_tkt.replace("T", " ")[:16]

                items_a_procesar = []

                for item in ticket.get("items", []):
                    cant = float(item.get("cantidad", 1))

                    if item.get("esCombo", False):
                        sub_items = item.get("comboItems", [])
                        cant_subs = len(sub_items) if len(sub_items) > 0 else 1
                        precio_prorrateado = float(item.get("precioFinal", 0)) / cant_subs

                        for sub in sub_items:
                            items_a_procesar.append({
                                "nombre": sub, "cantidad": cant,
                                "precio": precio_prorrateado, "es_insumo": False
                            })
                        items_a_procesar.append({
                            "nombre": "Bolsa de Friselina", "cantidad": cant,
                            "precio": 0, "es_insumo": True
                        })
                    else:
                        items_a_procesar.append({
                            "nombre": item.get("nombre", "Desconocido"),
                            "cantidad": cant,
                            "precio": float(item.get("precioFinal", 0)),
                            "es_insumo": False
                        })

                for it in items_a_procesar:
                    if it["es_insumo"]:
                        costo_real = costo_insumos.get(it["nombre"].lower(), 0.0)
                        nuevos_mov_stock.append({
                            "UUID": str(uuid.uuid4()),
                            "Ingrediente": it["nombre"],
                            "Cantidad": -float(it["cantidad"]),
                            "Unidad_Base": "unidades",
                            "Tipo_Movimiento": "SALIDA (Feria)",
                            "Costo_Real": costo_real,
                            "Proveedor": "Consumo Combo POS",
                            "Lote_Proveedor": tkt_id,
                            "Fecha_Vencimiento": "",
                            "Fecha_Movimiento": fecha_tkt
                        })
                        continue

                    nombre_clean = " ".join(str(it["nombre"]).lower().split())
                    gramaje_g = info_recetas.get(nombre_clean, {}).get("Gramaje", 100.0)

                    kg_a_descontar = float(it["cantidad"]) * (gramaje_g / 1000.0)
                    precio_total_item = it["precio"] * it["cantidad"]

                    if df_stock.empty:
                        lotes_prod = pd.DataFrame()
                    else:
                        lotes_prod = df_stock[
                            df_stock["Producto"].apply(
                                lambda x: " ".join(str(x).lower().split())
                            ) == nombre_clean
                        ]

                    if lotes_prod.empty:
                        st.warning(f"⚠️ Vendiste '{it['nombre']}' pero NO TENÉS STOCK. Se registró como 'SIN-LOTE'.")
                        nuevas_ventas.append({
                            "UUID": str(uuid.uuid4()),
                            "Remito_ID": tkt_id,
                            "Lote_Produccion": f"SIN-LOTE: {it['nombre']}",
                            "Cliente": "Feria (POS)",
                            "Forma_Pago": forma_pago,
                            "Cantidad_Vendida_KG": kg_a_descontar,
                            "Precio_Venta_Unitario_KG": (precio_total_item / kg_a_descontar) if kg_a_descontar > 0 else 0,
                            "Precio_Total": precio_total_item,
                            "Ganancia_Neta": precio_total_item,
                            "Fecha_Venta": fecha_tkt,
                            "Vendedor": "Feria",
                            "Precio_Facturado_Cliente": precio_total_item,
                            "Comision_Vendedor": 0.0,
                            "Estado_Comision": ""
                        })
                        continue

                    lotes_prod = lotes_prod.copy()
                    lotes_prod["Fecha_Produccion_DT"] = pd.to_datetime(
                        lotes_prod["Fecha_Produccion"], errors='coerce'
                    )
                    lotes_prod = lotes_prod.sort_values("Fecha_Produccion_DT")

                    kg_restante = kg_a_descontar

                    for idx_lote, lote_row in lotes_prod.iterrows():
                        if kg_restante <= 0.001:
                            break

                        disponible = float(lote_row["KG_Disponibles"])
                        if disponible <= 0.001:
                            continue

                        descuento = min(kg_restante, disponible)
                        df_stock.at[idx_lote, "KG_Disponibles"] -= descuento
                        kg_restante -= descuento

                        proporcion = (descuento / kg_a_descontar) if kg_a_descontar > 0 else 0
                        precio_parcial = precio_total_item * proporcion
                        costo_kg = float(lote_row.get("Costo_Unitario_KG", 0))
                        ganancia = precio_parcial - (costo_kg * descuento)

                        nuevas_ventas.append({
                            "UUID": str(uuid.uuid4()),
                            "Remito_ID": tkt_id,
                            "Lote_Produccion": str(lote_row["Lote_Produccion"]),
                            "Cliente": "Feria (POS)",
                            "Forma_Pago": forma_pago,
                            "Cantidad_Vendida_KG": float(descuento),
                            "Precio_Venta_Unitario_KG": float((precio_parcial / descuento) if descuento > 0 else 0),
                            "Precio_Total": float(precio_parcial),
                            "Ganancia_Neta": float(ganancia),
                            "Fecha_Venta": str(fecha_tkt),
                            "Vendedor": "Feria",
                            "Precio_Facturado_Cliente": float(precio_parcial),
                            "Comision_Vendedor": 0.0,
                            "Estado_Comision": ""
                        })

                    if kg_restante > 0.001:
                        ultimo_lote = lotes_prod.iloc[-1]
                        idx_ultimo = lotes_prod.index[-1]
                        df_stock.at[idx_ultimo, "KG_Disponibles"] -= kg_restante

                        proporcion = (kg_restante / kg_a_descontar) if kg_a_descontar > 0 else 0
                        precio_parcial = precio_total_item * proporcion
                        costo_kg = float(ultimo_lote.get("Costo_Unitario_KG", 0))
                        ganancia = precio_parcial - (costo_kg * kg_restante)

                        nuevas_ventas.append({
                            "UUID": str(uuid.uuid4()),
                            "Remito_ID": tkt_id,
                            "Lote_Produccion": str(ultimo_lote["Lote_Produccion"]),
                            "Cliente": "Feria (POS)",
                            "Forma_Pago": forma_pago,
                            "Cantidad_Vendida_KG": float(kg_restante),
                            "Precio_Venta_Unitario_KG": float((precio_parcial / kg_restante) if kg_restante > 0 else 0),
                            "Precio_Total": float(precio_parcial),
                            "Ganancia_Neta": float(ganancia),
                            "Fecha_Venta": str(fecha_tkt),
                            "Vendedor": "Feria",
                            "Precio_Facturado_Cliente": float(precio_parcial),
                            "Comision_Vendedor": 0.0,
                            "Estado_Comision": ""
                        })

            if nuevas_ventas:
                df_nv = pd.DataFrame(nuevas_ventas)
                append_data("ventas", df_nv)
                cant_ventas_ok = len(df_nv)

            if nuevos_mov_stock:
                df_nm = pd.DataFrame(nuevos_mov_stock)
                append_data("stock_log", df_nm)

        # ============================================
        # 4. MARCAR COMO PROCESADO Y REFRESCAR
        # ============================================
        df_buzon.at[idx_buzon, col_estado] = "PROCESADO"
        save_data("Buzon_POS", df_buzon)

        resumen = f"✅ Paquete procesado: {cant_ventas_ok} registros de venta"
        if nuevos_pedidos > 0:
            resumen += f" | {nuevos_pedidos} pedidos B2B en revisión (pestaña 📦)"
        if nuevos_leads > 0:
            resumen += f" | {nuevos_leads} potenciales capturados"

        st.success(resumen)
        st.rerun()
