# ui/screens.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

from core.io import guardar_csv
from core.stock import descontar_stock, StockError
from .style import green_title, green_sub
from .helpers import generar_lote, registrar_movimiento


def render_inicio():
    green_title("Inicio · Rojo Malbec ERP v2")
    st.markdown("---")

    recetas = st.session_state.recetas
    stock = st.session_state.stock_productos
    ventas = st.session_state.ventas
    compras = st.session_state.compras

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recetas", len(recetas))
    c2.metric("Lotes PT en stock", len(stock))
    c3.metric("Ventas registradas", len(ventas))
    c4.metric("Compras registradas", len(compras))

    st.markdown("---")
    green_sub("Últimos movimientos de stock")
    mov = st.session_state.movimientos_stock
    if mov.empty:
        st.info("Todavía no hay movimientos registrados.")
    else:
        st.dataframe(mov.sort_values("Fecha", ascending=False).head(10))

    st.markdown("---")
    green_sub("Vencimientos próximos (MP)")
    lotes = st.session_state.lotes_ingredientes
    if lotes.empty:
        st.info("No hay lotes de materias primas.")
    else:
        df = lotes.copy()
        df["Fecha_vencimiento"] = pd.to_datetime(df["Fecha_vencimiento"], errors="coerce")
        hoy = datetime.now().date()
        df["Días_restantes"] = (df["Fecha_vencimiento"].dt.date - hoy).dt.days
        proximos = df[df["Días_restantes"] <= 30]
        if proximos.empty:
            st.success("No hay materias primas que venzan en los próximos 30 días.")
        else:
            st.dataframe(proximos.sort_values("Días_restantes"))


def render_ingredientes(archivos):
    green_title("Gestión de ingredientes")
    ingredientes = st.session_state.ingredientes
    tab1, tab2 = st.tabs(["➕ Nuevo / Editar", "📋 Listado"])

    with tab1:
        green_sub("Crear o actualizar ingrediente")
        nombres_existentes = sorted(ingredientes["Nombre"].dropna().unique().tolist())
        modo = st.radio("Modo", ["Crear nuevo", "Editar existente"])

        if modo == "Editar existente" and nombres_existentes:
            ing_sel = st.selectbox("Ingrediente", nombres_existentes)
            row = ingredientes[ingredientes["Nombre"] == ing_sel].iloc[0]
            nombre = st.text_input("Nombre", value=row["Nombre"])
            unidad = st.selectbox("Unidad base", ["g", "ml", "unidad"], index=0)
            costo = st.number_input("Costo unitario (por g/ml)", min_value=0.0, step=0.01, value=float(row["Costo_unitario"]))
        else:
            nombre = st.text_input("Nombre")
            unidad = st.selectbox("Unidad base", ["g", "ml", "unidad"], index=0)
            costo = st.number_input("Costo unitario (por g/ml)", min_value=0.0, step=0.01, value=0.0)

        if st.button("💾 Guardar ingrediente", use_container_width=True):
            if nombre.strip() == "":
                st.error("El nombre es obligatorio.")
            else:
                existe = ingredientes[ingredientes["Nombre"].str.lower() == nombre.lower()]
                if existe.empty:
                    nuevo_id = 1 if ingredientes.empty else int(ingredientes["Id"].max()) + 1
                    nuevo = {"Id": float(nuevo_id), "Nombre": nombre, "Unidad_base": unidad, "Costo_unitario": costo}
                    ingredientes = pd.concat([ingredientes, pd.DataFrame([nuevo])], ignore_index=True)
                else:
                    idx = existe.index[0]
                    ingredientes.at[idx, "Unidad_base"] = unidad
                    ingredientes.at[idx, "Costo_unitario"] = costo

                st.session_state.ingredientes = ingredientes
                guardar_csv(ingredientes, archivos["ingredientes"])
                st.success("Ingrediente guardado correctamente.")
                st.rerun()

    with tab2:
        green_sub("Listado de ingredientes")
        if ingredientes.empty:
            st.info("No hay ingredientes cargados.")
        else:
            st.dataframe(ingredientes.sort_values("Nombre"))


def render_proveedores(archivos):
    green_title("Gestión de Proveedores")
    proveedores = st.session_state.proveedores
    compras = st.session_state.compras
    tab1, tab2, tab3 = st.tabs(["➕ Nuevo", "📋 Listado", "✏️ Editar / Eliminar"])

    with tab1:
        green_sub("Registrar nuevo proveedor")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del proveedor")
            cuit = st.text_input("CUIT")
            telefono = st.text_input("Teléfono")
            email = st.text_input("Email")
        with col2:
            direccion = st.text_input("Dirección")
            notas = st.text_area("Notas")

        if st.button("💾 Guardar proveedor", use_container_width=True):
            if nombre.strip() == "":
                st.error("El nombre es obligatorio.")
            else:
                nuevo_id = 1 if proveedores.empty else int(proveedores["Id_Proveedor"].max()) + 1
                nuevo = {
                    "Id_Proveedor": float(nuevo_id),
                    "Nombre": nombre,
                    "CUIT": cuit,
                    "Telefono": telefono,
                    "Email": email,
                    "Direccion": direccion,
                    "Notas": notas,
                }
                proveedores = pd.concat([proveedores, pd.DataFrame([nuevo])], ignore_index=True)
                st.session_state.proveedores = proveedores
                guardar_csv(proveedores, archivos["proveedores"])
                st.success("Proveedor guardado.")
                st.rerun()

    with tab2:
        green_sub("Listado de proveedores")
        if proveedores.empty:
            st.info("No hay proveedores cargados.")
        else:
            st.dataframe(proveedores.sort_values("Nombre"))

    with tab3:
        if proveedores.empty:
            st.info("No hay proveedores para editar.")
        else:
            prov_sel = st.selectbox("Proveedor", sorted(proveedores["Nombre"].unique().tolist()))
            row = proveedores[proveedores["Nombre"] == prov_sel].iloc[0]

            col1, col2 = st.columns(2)
            with col1:
                new_nombre = st.text_input("Nombre", value=row["Nombre"])
                new_cuit = st.text_input("CUIT", value=row["CUIT"])
                new_tel = st.text_input("Teléfono", value=row["Telefono"])
                new_email = st.text_input("Email", value=row["Email"])
            with col2:
                new_dir = st.text_input("Dirección", value=row["Direccion"])
                new_notas = st.text_area("Notas", value=row["Notas"])

            colA, colB = st.columns(2)
            with colA:
                if st.button("💾 Guardar cambios"):
                    idx = proveedores[proveedores["Id_Proveedor"] == row["Id_Proveedor"]].index[0]
                    proveedores.at[idx, "Nombre"] = new_nombre
                    proveedores.at[idx, "CUIT"] = new_cuit
                    proveedores.at[idx, "Telefono"] = new_tel
                    proveedores.at[idx, "Email"] = new_email
                    proveedores.at[idx, "Direccion"] = new_dir
                    proveedores.at[idx, "Notas"] = new_notas
                    st.session_state.proveedores = proveedores
                    guardar_csv(proveedores, archivos["proveedores"])
                    st.success("Proveedor actualizado.")
                    st.rerun()
            with colB:
                if st.button("🗑 Eliminar proveedor"):
                    compras_asoc = compras[compras["Proveedor"] == prov_sel]
                    if not compras_asoc.empty:
                        st.error("No se puede eliminar: tiene compras asociadas.")
                    else:
                        proveedores = proveedores[proveedores["Nombre"] != prov_sel]
                        st.session_state.proveedores = proveedores
                        guardar_csv(proveedores, archivos["proveedores"])
                        st.success("Proveedor eliminado.")
                        st.rerun()


def render_compras(archivos):
    green_title("Registro de Compras")
    compras = st.session_state.compras
    proveedores = st.session_state.proveedores
    ingredientes = st.session_state.ingredientes
    lotes = st.session_state.lotes_ingredientes

    green_sub("➕ Registrar nueva compra")
    col1, col2 = st.columns(2)
    with col1:
        proveedor_sel = st.selectbox("Proveedor", ["- Sin proveedor -"] + sorted(proveedores["Nombre"].dropna().unique().tolist()))
        nombres_ing = sorted(ingredientes["Nombre"].dropna().unique().tolist())
        nombre_ing = st.text_input("Nombre del ingrediente").strip()
        if nombres_ing:
            sugerencia = st.selectbox("Elegir de existentes (opcional)", ["-"] + nombres_ing)
            if sugerencia != "-" and nombre_ing == "":
                nombre_ing = sugerencia

        unidad = st.selectbox("Unidad de compra", ["g", "kg", "ml", "litro", "unidad"])
        cantidad = st.number_input("Cantidad comprada", min_value=0.0, step=0.1)

    with col2:
        precio_total = st.number_input("Precio total", min_value=0.0, step=0.1)
        fecha_compra = st.date_input("Fecha de compra", value=date.today())
        fecha_venc = st.date_input("Fecha de vencimiento", value=date.today())
        lote_prov = st.text_input("Lote del proveedor (opcional)")
        observ = st.text_area("Observaciones")

    if st.button("Guardar compra", use_container_width=True):
        if nombre_ing == "":
            st.error("Debe ingresar un nombre de ingrediente.")
        elif cantidad <= 0 or precio_total <= 0:
            st.error("Cantidad y precio deben ser mayores a cero.")
        else:
            cant_base = cantidad
            if unidad == "kg":
                cant_base = cantidad * 1000
            if unidad == "litro":
                cant_base = cantidad * 1000

            costo_unitario = precio_total / cant_base

            existe = ingredientes[ingredientes["Nombre"].str.lower() == nombre_ing.lower()]
            if existe.empty:
                nuevo_id_ing = 1 if ingredientes.empty else int(ingredientes["Id"].max()) + 1
                nuevo_ing = {"Id": float(nuevo_id_ing), "Nombre": nombre_ing, "Unidad_base": "g/ml", "Costo_unitario": costo_unitario}
                ingredientes = pd.concat([ingredientes, pd.DataFrame([nuevo_ing])], ignore_index=True)
            else:
                idx = existe.index[0]
                ingredientes.at[idx, "Costo_unitario"] = costo_unitario

            st.session_state.ingredientes = ingredientes
            guardar_csv(ingredientes, archivos["ingredientes"])

            nuevo_id_compra = 1 if compras.empty else int(compras["Id_Compra"].max()) + 1
            nueva_compra = {
                "Id_Compra": float(nuevo_id_compra),
                "Fecha_compra": fecha_compra.strftime("%Y-%m-%d"),
                "Proveedor": proveedor_sel if proveedor_sel != "- Sin proveedor -" else "",
                "Ingrediente": nombre_ing,
                "Cantidad": cant_base,
                "Unidad": "g/ml",
                "Precio_total": precio_total,
                "Lote_proveedor": lote_prov,
                "Fecha_vencimiento": fecha_venc.strftime("%Y-%m-%d"),
                "Observaciones": observ,
            }
            compras = pd.concat([compras, pd.DataFrame([nueva_compra])], ignore_index=True)
            st.session_state.compras = compras
            guardar_csv(compras, archivos["compras"])

            codigo_ing = nombre_ing.replace(" ", "").upper()[:7]
            lote_interno = generar_lote(archivos, codigo_ing)

            nuevo_id_lote = 1 if lotes.empty else int(lotes["Id_Lote"].max()) + 1
            nuevo_lote = {
                "Id_Lote": float(nuevo_id_lote),
                "Ingrediente": nombre_ing,
                "Lote_proveedor": lote_prov,
                "Lote_interno": lote_interno,
                "Fecha_compra": fecha_compra.strftime("%Y-%m-%d"),
                "Fecha_vencimiento": fecha_venc.strftime("%Y-%m-%d"),
                "Stock_inicial": cant_base,
                "Stock_actual": cant_base,
            }
            lotes = pd.concat([lotes, pd.DataFrame([nuevo_lote])], ignore_index=True)
            st.session_state.lotes_ingredientes = lotes
            guardar_csv(lotes, archivos["lotes_ingredientes"])

            registrar_movimiento(
                archivos,
                tipo="ENTRADA_MP",
                origen="Compras",
                referencia=lote_interno,
                detalle=f"Compra de {nombre_ing}",
                cantidad=cant_base,
                unidad="g",
                ingrediente=nombre_ing,
            )

            st.success(f"Compra registrada correctamente — Lote interno: {lote_interno}")
            st.rerun()

    st.markdown("---")
    green_sub("📦 Historial de compras")
    if compras.empty:
        st.info("Aún no hay compras registradas.")
    else:
        st.dataframe(compras.sort_values("Fecha_compra", ascending=False))


def render_recetas(archivos):
    green_title("Recetas Rojo Malbec")
    recetas = st.session_state.recetas
    det = st.session_state.recetas_detalle
    ingredientes = st.session_state.ingredientes

    tab1, tab2, tab3 = st.tabs(["➕ Nueva receta", "📋 Listado", "✏️ Editar / Eliminar"])

    with tab1:
        green_sub("Crear nueva receta")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre de la receta")
            codigo = st.text_input("Código interno (ej: SLM-1000)")
            tam_base = st.number_input("Tamaño de lote base (g)", min_value=1.0, value=1000.0, step=1.0)
        with col2:
            descripcion = st.text_area("Descripción (opcional)")
            vida_util = st.number_input("Vida útil estimada (días)", min_value=0.0, value=0.0, step=1.0)

        st.markdown("### Ingredientes del lote base")
        ingr_lista = sorted(ingredientes["Nombre"].dropna().tolist())
        if not ingr_lista:
            st.info("Primero cargá ingredientes en el módulo 🧂 Ingredientes.")
        else:
            ingr_sel = st.selectbox("Ingrediente", ingr_lista)
            cant = st.number_input("Cantidad (g)", min_value=0.0, step=1.0)
            if st.button("Agregar ingrediente a la receta"):
                if nombre.strip() == "":
                    st.error("Primero completá el nombre de la receta.")
                else:
                    st.session_state.temp_receta = st.session_state.get("temp_receta", [])
                    st.session_state.temp_receta.append((ingr_sel, cant))
                    st.success(f"{ingr_sel} agregado.")

        if "temp_receta" in st.session_state and st.session_state.temp_receta:
            st.write("Ingredientes cargados:")
            st.table(st.session_state.temp_receta)

        if st.button("💾 Guardar receta", use_container_width=True):
            if nombre.strip() == "":
                st.error("El nombre es obligatorio.")
            else:
                nuevo_id = 1 if recetas.empty else int(recetas["Id_Receta"].max()) + 1
                nueva_rec = {
                    "Id_Receta": float(nuevo_id),
                    "Nombre": nombre,
                    "Codigo": codigo,
                    "Tam_base": float(tam_base),
                    "Descripcion": descripcion,
                    "Ruta_foto": "",
                    "Costo_total": 0.0,
                    "Vida_util_dias": float(vida_util),
                }
                recetas = pd.concat([recetas, pd.DataFrame([nueva_rec])], ignore_index=True)
                st.session_state.recetas = recetas
                guardar_csv(recetas, archivos["recetas"])

                filas = []
                for ing, cant_ in st.session_state.get("temp_receta", []):
                    filas.append({"Id_Receta": float(nuevo_id), "Ingrediente": ing, "Cantidad": float(cant_), "Unidad": "g"})
                if filas:
                    det = pd.concat([det, pd.DataFrame(filas)], ignore_index=True)
                    st.session_state.recetas_detalle = det
                    guardar_csv(det, archivos["recetas_detalle"])

                if "temp_receta" in st.session_state:
                    del st.session_state["temp_receta"]

                st.success("Receta guardada correctamente.")
                st.rerun()

    with tab2:
        green_sub("Listado de recetas")
        if recetas.empty:
            st.info("No hay recetas cargadas.")
        else:
            st.dataframe(recetas[["Nombre", "Codigo", "Tam_base", "Vida_util_dias"]].sort_values("Nombre"))

    with tab3:
        if recetas.empty:
            st.info("No hay recetas para editar.")
        else:
            rec_sel = st.selectbox("Seleccionar receta", sorted(recetas["Nombre"].unique().tolist()))
            row = recetas[recetas["Nombre"] == rec_sel].iloc[0]

            col1, col2 = st.columns(2)
            with col1:
                new_nombre = st.text_input("Nombre", value=row["Nombre"])
                new_codigo = st.text_input("Código", value=row["Codigo"])
                new_base = st.number_input("Tamaño base (g)", min_value=1.0, value=float(row["Tam_base"]))
            with col2:
                new_descripcion = st.text_area("Descripción", value=row["Descripcion"])
                new_vida = st.number_input("Vida útil (días)", min_value=0.0, value=float(row.get("Vida_util_dias", 0.0)))

            if st.button("Guardar cambios en receta"):
                idx = recetas[recetas["Id_Receta"] == row["Id_Receta"]].index[0]
                recetas.at[idx, "Nombre"] = new_nombre
                recetas.at[idx, "Codigo"] = new_codigo
                recetas.at[idx, "Tam_base"] = new_base
                recetas.at[idx, "Descripcion"] = new_descripcion
                recetas.at[idx, "Vida_util_dias"] = new_vida
                st.session_state.recetas = recetas
                guardar_csv(recetas, archivos["recetas"])
                st.success("Receta actualizada.")
                st.rerun()

            st.markdown("---")
            green_sub("Ingredientes de la receta")
            det_rec = det[det["Id_Receta"] == row["Id_Receta"]]
            if det_rec.empty:
                st.info("Esta receta aún no tiene ingredientes asignados.")
            else:
                st.dataframe(det_rec)

            if st.button("🗑 Eliminar receta", type="secondary"):
                id_rec = row["Id_Receta"]
                recetas = recetas[recetas["Id_Receta"] != id_rec]
                det = det[det["Id_Receta"] != id_rec]
                st.session_state.recetas = recetas
                st.session_state.recetas_detalle = det
                guardar_csv(recetas, archivos["recetas"])
                guardar_csv(det, archivos["recetas_detalle"])
                st.success("Receta eliminada.")
                st.rerun()


def render_produccion(archivos):
    green_title("Producción unificada")
    lotes = st.session_state.lotes_ingredientes
    recetas = st.session_state.recetas
    detalles = st.session_state.recetas_detalle
    stock = st.session_state.stock_productos

    if recetas.empty:
        st.warning("Todavía no cargaste recetas.")
        return

    receta_sel = st.selectbox("Seleccionar receta", sorted(recetas["Nombre"].unique().tolist()))
    receta_row = recetas[recetas["Nombre"] == receta_sel].iloc[0]
    base_lote = float(receta_row["Tam_base"])
    id_rec = int(receta_row["Id_Receta"])

    st.info(f"Base estándar: **{base_lote} g**")

    ing_receta = detalles[detalles["Id_Receta"] == id_rec]
    st.markdown("### Ingredientes base")
    st.dataframe(ing_receta)

    cantidad_producir = st.number_input("Cantidad a producir (g, granel)", min_value=1.0, value=base_lote, step=10.0)

    factor = cantidad_producir / base_lote
    tabla_scaled = ing_receta.copy()
    tabla_scaled["Cantidad_escalada"] = tabla_scaled["Cantidad"] * factor

    st.markdown("### Ingredientes requeridos (escalados)")
    st.dataframe(tabla_scaled)

    st.markdown("### Verificación de stock FIFO")

    errores = []
    consumo_fifo = []

    for _, row in tabla_scaled.iterrows():
        ing = row["Ingrediente"]
        req = float(row["Cantidad_escalada"])

        lotes_dispo = lotes[(lotes["Ingrediente"] == ing) & (lotes["Stock_actual"] > 0)].copy()
        lotes_dispo["Fecha_compra"] = pd.to_datetime(lotes_dispo["Fecha_compra"], errors="coerce")
        lotes_dispo = lotes_dispo.sort_values("Fecha_compra")

        restante = req
        trazas = []

        for _, lote in lotes_dispo.iterrows():
            if restante <= 0:
                break
            usar = min(restante, float(lote["Stock_actual"]))
            trazas.append({
                "Id_Lote": lote["Id_Lote"],
                "Ingrediente": ing,
                "Lote_interno": lote["Lote_interno"],
                "Cantidad_usada": float(usar)
            })
            restante -= float(usar)

        if restante > 0:
            errores.append(f"No hay suficiente **{ing}** (faltan {restante:.2f} g)")
        else:
            consumo_fifo.extend(trazas)

    if errores:
        st.error("No se puede producir:")
        for e in errores:
            st.write(e)
        return

    st.success("Stock suficiente para producir.")
    lote_granel = f"PT-{receta_row['Codigo']}-{datetime.now().strftime('%d%m%Y')}"
    st.info(f"Lote granel sugerido: **{lote_granel}**")

    if st.button("🚀 Ejecutar producción (granel)", use_container_width=True):
        # Descontar lotes MP con función anti-negativos
        for mov in consumo_fifo:
            idx = lotes[lotes["Id_Lote"] == mov["Id_Lote"]].index[0]
            try:
                lotes = descontar_stock(lotes, idx, mov["Cantidad_usada"], campo="Stock_actual")
            except StockError as e:
                st.error(f"Error de stock en producción: {e}")
                st.stop()

            registrar_movimiento(
                archivos,
                tipo="CONSUMO_MP",
                origen="Producción",
                referencia=mov["Lote_interno"],
                detalle=f"Uso en {lote_granel}",
                cantidad=mov["Cantidad_usada"],
                unidad="g",
                ingrediente=mov["Ingrediente"],
            )

        guardar_csv(lotes, archivos["lotes_ingredientes"])
        st.session_state.lotes_ingredientes = lotes

        prod = st.session_state.produccion
        new_id = 1 if prod.empty else int(prod["Id_Prod"].max()) + 1
        nuevo_reg = {
            "Id_Prod": float(new_id),
            "Receta": receta_sel,
            "Codigo_receta": receta_row["Codigo"],
            "Fecha": datetime.now().strftime("%Y-%m-%d"),
            "Lote_producto": lote_granel,
            "Cantidad_producida": float(cantidad_producir),
        }
        prod = pd.concat([prod, pd.DataFrame([nuevo_reg])], ignore_index=True)
        guardar_csv(prod, archivos["produccion"])
        st.session_state.produccion = prod

        prod_lotes = st.session_state.produccion_lotes
        prod_lotes = pd.concat([prod_lotes, pd.DataFrame(consumo_fifo)], ignore_index=True)
        guardar_csv(prod_lotes, archivos["produccion_lotes"])
        st.session_state.produccion_lotes = prod_lotes

        registrar_movimiento(
            archivos,
            tipo="PRODUCCION_PT",
            origen="Producción",
            referencia=lote_granel,
            detalle=f"Lote granel {receta_sel}",
            cantidad=cantidad_producir,
            unidad="g",
            producto=receta_sel,
        )

        st.success(f"Lote granel producido: {lote_granel}")
        st.rerun()

    st.markdown("---")
    st.markdown("## Envasado de lote granel existente")

    prod = st.session_state.produccion
    if prod.empty:
        st.info("Todavía no hay lotes granel producidos.")
        return

    lote_sel = st.selectbox("Lote granel", sorted(prod["Lote_producto"].unique().tolist()))
    row_p = prod[prod["Lote_producto"] == lote_sel].iloc[0]
    disponible = float(row_p["Cantidad_producida"])
    st.info(f"Cantidad disponible en granel: {disponible:.2f} g")

    peso_unit = st.number_input("Peso por unidad (g)", min_value=1.0, step=1.0, value=40.0)
    unidades = st.number_input("Cantidad de unidades a envasar", min_value=1, step=1, value=10)
    total_requerido = float(peso_unit) * float(unidades)
    st.write(f"Total requerido: {total_requerido:.2f} g")

    if st.button("💾 Confirmar envasado", use_container_width=True):
        if total_requerido > disponible:
            st.error("No hay suficiente producto granel.")
            st.stop()

        idxp = prod[prod["Lote_producto"] == lote_sel].index[0]
        try:
            prod = descontar_stock(prod, idxp, total_requerido, campo="Cantidad_producida")
        except StockError as e:
            st.error(f"Error en envasado: {e}")
            st.stop()

        guardar_csv(prod, archivos["produccion"])
        st.session_state.produccion = prod

        vida_dias = float(receta_row.get("Vida_util_dias", 0.0))
        fecha_venc = (datetime.now() + timedelta(days=vida_dias)).strftime("%Y-%m-%d") if vida_dias > 0 else ""

        nuevo_id_stock = 1 if stock.empty else int(stock["Id"].max()) + 1
        lote_final = f"F-{lote_sel}-{str(nuevo_id_stock).zfill(2)}"
        nuevo_stock = {
            "Id": float(nuevo_id_stock),
            "Producto": receta_sel,
            "Lote_producto": lote_final,
            "Cantidad_disponible": float(total_requerido),
            "Fecha_produccion": datetime.now().strftime("%Y-%m-%d"),
            "Peso_unitario": float(peso_unit),
            "Fecha_vencimiento": fecha_venc,
        }
        stock = pd.concat([stock, pd.DataFrame([nuevo_stock])], ignore_index=True)
        guardar_csv(stock, archivos["stock_productos"])
        st.session_state.stock_productos = stock

        registrar_movimiento(
            archivos,
            tipo="ENVASADO",
            origen="Producción",
            referencia=lote_final,
            detalle=f"Envasado desde {lote_sel}",
            cantidad=total_requerido,
            unidad="g",
            producto=receta_sel,
        )

        st.success(f"Envasado registrado — Lote final {lote_final}")
        st.rerun()


def render_stock(archivos):
    green_title("Stock general")
    lotes = st.session_state.lotes_ingredientes
    stock = st.session_state.stock_productos
    min_ing = st.session_state.stock_minimos_ing
    min_prod = st.session_state.stock_minimos

    tab1, tab2 = st.tabs(["Materias primas", "Productos terminados"])

    with tab1:
        green_sub("Stock de materias primas por ingrediente")
        if lotes.empty:
            st.info("No hay materias primas cargadas.")
        else:
            stock_ing = lotes.groupby("Ingrediente")["Stock_actual"].sum().reset_index()
            stock_ing = stock_ing.merge(min_ing, on="Ingrediente", how="left")
            stock_ing["Minimo"] = stock_ing["Minimo"].fillna(500.0)

            estados = []
            for _, row in stock_ing.iterrows():
                actual = row["Stock_actual"]; minimo = row["Minimo"]
                if actual <= 0: estados.append("❌ Sin stock")
                elif actual < minimo * 0.5: estados.append("🔴 Crítico")
                elif actual < minimo: estados.append("🟡 Bajo")
                else: estados.append("🟢 OK")
            stock_ing["Estado"] = estados
            st.dataframe(stock_ing.sort_values("Ingrediente"))

            st.markdown("### Configurar mínimos por ingrediente")
            ing_sel = st.selectbox("Ingrediente", sorted(stock_ing["Ingrediente"].unique().tolist()))
            valor_min = st.number_input("Stock mínimo (g)", min_value=0.0, step=50.0)
            if st.button("Guardar mínimo de ingrediente"):
                existe = min_ing[min_ing["Ingrediente"] == ing_sel]
                if existe.empty:
                    min_ing = pd.concat([min_ing, pd.DataFrame([{"Ingrediente": ing_sel, "Minimo": valor_min}])], ignore_index=True)
                else:
                    idx = existe.index[0]
                    min_ing.at[idx, "Minimo"] = valor_min
                st.session_state.stock_minimos_ing = min_ing
                guardar_csv(min_ing, archivos["stock_minimos_ing"])
                st.success("Mínimo actualizado.")
                st.rerun()

    with tab2:
        green_sub("Stock de productos terminados")
        if stock.empty:
            st.info("No hay productos terminados en stock.")
        else:
            df = stock.copy()
            hoy = datetime.now().date()
            df["Fecha_produccion"] = pd.to_datetime(df["Fecha_produccion"], errors="coerce")
            df["Fecha_vencimiento"] = pd.to_datetime(df["Fecha_vencimiento"], errors="coerce")
            df["Unidades_aprox"] = df.apply(lambda x: x["Cantidad_disponible"] / x["Peso_unitario"] if x["Peso_unitario"] > 0 else 0, axis=1)
            df["Días_restantes"] = df["Fecha_vencimiento"].apply(lambda x: (x.date() - hoy).days if pd.notnull(x) else None)

            agrupado = df.groupby("Producto").agg({"Cantidad_disponible": "sum", "Unidades_aprox": "sum"}).reset_index()
            agrupado = agrupado.merge(min_prod, on="Producto", how="left")
            agrupado["Minimo"] = agrupado["Minimo"].fillna(4000.0)

            estados = []
            for _, row in agrupado.iterrows():
                actual = row["Cantidad_disponible"]; minimo = row["Minimo"]
                if actual <= 0: estados.append("❌ Sin stock")
                elif actual < minimo * 0.5: estados.append("🔴 Crítico")
                elif actual < minimo: estados.append("🟡 Bajo")
                else: estados.append("🟢 OK")
            agrupado["Estado"] = estados
            st.dataframe(agrupado.sort_values("Producto"))

            st.markdown("### Configurar mínimos por producto")
            prod_sel = st.selectbox("Producto", sorted(agrupado["Producto"].unique().tolist()))
            valor_min_p = st.number_input("Stock mínimo (g) producto", min_value=0.0, step=100.0)
            if st.button("Guardar mínimo de producto"):
                existe = min_prod[min_prod["Producto"] == prod_sel]
                if existe.empty:
                    min_prod = pd.concat([min_prod, pd.DataFrame([{"Producto": prod_sel, "Minimo": valor_min_p}])], ignore_index=True)
                else:
                    idx = existe.index[0]
                    min_prod.at[idx, "Minimo"] = valor_min_p
                st.session_state.stock_minimos = min_prod
                guardar_csv(min_prod, archivos["stock_minimos"])
                st.success("Mínimo de producto actualizado.")
                st.rerun()

            st.markdown("### Lotes y vencimientos")
            st.dataframe(df[[
                "Producto", "Lote_producto", "Cantidad_disponible",
                "Unidades_aprox", "Fecha_produccion", "Fecha_vencimiento", "Días_restantes"
            ]].sort_values(["Producto", "Fecha_produccion"]))


def render_clientes(archivos):
    green_title("Gestión de Clientes")
    clientes = st.session_state.clientes
    tab1, tab2 = st.tabs(["➕ Nuevo", "📋 Listado"])
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre / Razón social")
            tipo = st.selectbox("Tipo de cliente", ["Minorista", "Mayorista", "Distribuidor", "Online"])
            cuit = st.text_input("CUIT / DNI")
        with col2:
            telefono = st.text_input("Teléfono")
            email = st.text_input("Email")
            direccion = st.text_input("Dirección")
            localidad = st.text_input("Localidad")
            provincia = st.text_input("Provincia")
            lista = st.text_input("Lista de precios (ej: A, B, Mayorista)")
        notas = st.text_area("Notas")

        if st.button("💾 Guardar cliente", use_container_width=True):
            if nombre.strip() == "":
                st.error("El nombre es obligatorio.")
            else:
                nuevo_id = 1 if clientes.empty else int(clientes["Id_Cliente"].max()) + 1
                nuevo = {
                    "Id_Cliente": float(nuevo_id),
                    "Nombre": nombre,
                    "Tipo": tipo,
                    "CUIT": cuit,
                    "Telefono": telefono,
                    "Email": email,
                    "Direccion": direccion,
                    "Localidad": localidad,
                    "Provincia": provincia,
                    "Lista_precios": lista,
                    "Notas": notas,
                }
                clientes = pd.concat([clientes, pd.DataFrame([nuevo])], ignore_index=True)
                st.session_state.clientes = clientes
                guardar_csv(clientes, archivos["clientes"])
                st.success("Cliente guardado.")
                st.rerun()

    with tab2:
        if clientes.empty:
            st.info("No hay clientes cargados.")
        else:
            st.dataframe(clientes.sort_values("Nombre"))


def render_carga_manual_stock(archivos):
    green_title("🏷 Carga manual de stock terminado")
    stock = st.session_state.stock_productos
    recetas = st.session_state.recetas

    st.info("Usá este módulo solo para cargar lotes que ya tenés envasados, sin descontar ingredientes ni registrar una producción real.")

    col1, col2 = st.columns(2)
    with col1:
        modo = st.radio("Origen del producto", ["Desde receta existente", "Nombre manual"])
        if modo == "Desde receta existente":
            if recetas.empty:
                st.warning("Todavía no hay recetas cargadas. Podés usar 'Nombre manual'.")
                nombre_prod = st.text_input("Nombre del producto")
            else:
                opciones_prod = sorted(recetas["Nombre"].dropna().unique())
                nombre_prod = st.selectbox("Receta / producto", opciones_prod)
        else:
            nombre_prod = st.text_input("Nombre del producto")
        lote_prod = st.text_input("Lote del producto (como figura en la etiqueta)")

    with col2:
        fecha_prod = st.date_input("Fecha de producción", value=date.today())
        fecha_venc = st.date_input("Fecha de vencimiento", value=date.today())

    col3, col4 = st.columns(2)
    with col3:
        cant_lote = st.number_input("Cantidad total del lote (g)", min_value=0.0, step=1.0)
    with col4:
        peso_unit = st.number_input("Peso por envase / unidad (g)", min_value=0.0, step=1.0)

    if st.button("Guardar lote manual", use_container_width=True):
        if not nombre_prod:
            st.error("Debe indicar el nombre del producto.")
            st.stop()
        if cant_lote <= 0 or peso_unit <= 0:
            st.error("Cantidad total y peso por envase deben ser mayores a cero.")
            st.stop()
        if not lote_prod:
            lote_prod = f"MAN-{fecha_prod.strftime('%Y%m%d')}"
        stock_df = stock
        nuevo_id = int(stock_df["Id"].max() + 1) if not stock_df.empty else 1
        nuevo = {
            "Id": float(nuevo_id),
            "Producto": nombre_prod,
            "Lote_producto": lote_prod,
            "Cantidad_disponible": float(cant_lote),
            "Fecha_produccion": fecha_prod.strftime("%Y-%m-%d"),
            "Peso_unitario": float(peso_unit),
            "Fecha_vencimiento": fecha_venc.strftime("%Y-%m-%d"),
        }
        stock_df = pd.concat([stock_df, pd.DataFrame([nuevo])], ignore_index=True)
        st.session_state.stock_productos = stock_df
        guardar_csv(stock_df, archivos["stock_productos"])
        unidades = int(cant_lote / peso_unit) if peso_unit > 0 else 0
        st.success(f"Lote cargado correctamente. Unidades aproximadas: {unidades}")
        st.rerun()

    st.markdown("---")
    green_sub("📦 Stock actual de productos terminados")
    if stock.empty:
        st.info("Todavía no hay stock cargado.")
    else:
        st.dataframe(stock)


def render_ventas(archivos):
    green_title("Registro de Ventas")
    ventas = st.session_state.ventas
    clientes = st.session_state.clientes
    stock_prod = st.session_state.stock_productos

    if stock_prod.empty:
        st.warning("No hay stock de productos terminados.")
    else:
        st.subheader("Nueva venta")
        col1, col2 = st.columns(2)
        with col1:
            clientes_op = sorted(clientes["Nombre"].unique().tolist()) if not clientes.empty else []
            cliente_sel = st.selectbox("Cliente", ["Venta mostrador"] + clientes_op)
        with col2:
            tipo_cliente = st.selectbox("Tipo de cliente", ["Minorista", "Mayorista", "Distribuidor", "Online"])

        producto_sel = st.selectbox("Producto", sorted(stock_prod["Producto"].unique().tolist()))
        lotes_disp = stock_prod[stock_prod["Producto"] == producto_sel].copy()
        lotes_disp["Fecha_produccion"] = pd.to_datetime(lotes_disp["Fecha_produccion"], errors="coerce")
        lotes_disp = lotes_disp[lotes_disp["Cantidad_disponible"] > 0].sort_values("Fecha_produccion")

        if lotes_disp.empty:
            st.error("No hay stock disponible para este producto.")
        else:
            peso_unitario_ref = lotes_disp["Peso_unitario"].mode().iloc[0] if lotes_disp["Peso_unitario"].notna().any() else 40.0
            cantidad_unidades = st.number_input("Cantidad de unidades", min_value=1, step=1)
            precio_unit = st.number_input("Precio por unidad", min_value=0.0, step=10.0)
            forma_pago = st.selectbox("Forma de pago", ["Efectivo", "Transferencia", "Mercado Pago", "Cuenta corriente"])
            notas = st.text_area("Notas (opcional)")

            gramos_totales = float(cantidad_unidades) * float(peso_unitario_ref)
            st.info(f"Equivalente aproximado: {gramos_totales:.2f} g")

            restante = gramos_totales
            movimientos = []
            for _, lote in lotes_disp.iterrows():
                if restante <= 0:
                    break
                disponible = float(lote["Cantidad_disponible"])
                usar = min(restante, disponible)
                if usar > 0:
                    movimientos.append({"Lote_producto": lote["Lote_producto"], "Usado": float(usar)})
                    restante -= float(usar)

            if restante > 0:
                st.error("Stock insuficiente para completar la venta.")
            else:
                st.write("Lotes que se usarán:")
                st.dataframe(pd.DataFrame(movimientos))

                if st.button("💾 Confirmar venta", use_container_width=True):
                    for mov in movimientos:
                        idx = stock_prod[stock_prod["Lote_producto"] == mov["Lote_producto"]].index[0]
                        try:
                            stock_prod = descontar_stock(stock_prod, idx, mov["Usado"], campo="Cantidad_disponible")
                        except StockError as e:
                            st.error(f"Error de stock en venta: {e}")
                            st.stop()

                        registrar_movimiento(
                            archivos,
                            tipo="VENTA_PT",
                            origen="Ventas",
                            referencia=mov["Lote_producto"],
                            detalle=f"Venta {producto_sel}",
                            cantidad=mov["Usado"],
                            unidad="g",
                            producto=producto_sel,
                        )

                    st.session_state.stock_productos = stock_prod
                    guardar_csv(stock_prod, archivos["stock_productos"])

                    nuevo_id = 1 if ventas.empty else int(ventas["Id_Venta"].max()) + 1
                    precio_total = float(precio_unit) * float(cantidad_unidades)
                    reg = {
                        "Id_Venta": float(nuevo_id),
                        "Fecha": datetime.now().strftime("%Y-%m-%d"),
                        "Cliente": cliente_sel,
                        "Tipo_cliente": tipo_cliente,
                        "Producto": producto_sel,
                        "Lote_producto": ", ".join([f"{m['Lote_producto']}({m['Usado']}g)" for m in movimientos]),
                        "Cantidad": float(gramos_totales),
                        "Precio_unitario": float(precio_unit),
                        "Precio_total": float(precio_total),
                        "Forma_pago": forma_pago,
                        "Notas": notas,
                    }
                    ventas = pd.concat([ventas, pd.DataFrame([reg])], ignore_index=True)
                    st.session_state.ventas = ventas
                    guardar_csv(ventas, archivos["ventas"])
                    st.success("Venta registrada correctamente.")
                    st.rerun()

    st.markdown("---")
    st.subheader("Historial de ventas")
    if ventas.empty:
        st.info("Todavía no registraste ventas.")
    else:
        st.dataframe(ventas.sort_values("Fecha", ascending=False))


def render_costos(archivos):
    green_title("Costos, Precios y Análisis")
    recetas = st.session_state.recetas
    det = st.session_state.recetas_detalle
    ingredientes = st.session_state.ingredientes
    gastos = st.session_state.gastos_fijos
    margenes = st.session_state.margenes
    ventas = st.session_state.ventas

    tab1, tab2, tab3 = st.tabs(["Recalcular costos", "Márgenes y precios", "Resumen rápido"])

    with tab1:
        green_sub("Actualizar precios de ingredientes y recalcular recetas")
        if ingredientes.empty:
            st.info("No hay ingredientes cargados.")
        else:
            ing_sel = st.selectbox("Ingrediente a actualizar", sorted(ingredientes["Nombre"].unique().tolist()))
            row = ingredientes[ingredientes["Nombre"] == ing_sel].iloc[0]
            costo_actual = float(row["Costo_unitario"])
            nuevo_costo = st.number_input("Nuevo costo unitario (por g/ml)", min_value=0.0, value=costo_actual, step=0.1)

            if st.button("Actualizar costo y recalcular recetas"):
                ingredientes.loc[ingredientes["Nombre"] == ing_sel, "Costo_unitario"] = nuevo_costo
                guardar_csv(ingredientes, archivos["ingredientes"])
                st.session_state.ingredientes = ingredientes

                afectadas = det[det["Ingrediente"] == ing_sel]["Id_Receta"].unique()
                resultados = []
                for rid in afectadas:
                    rec = recetas[recetas["Id_Receta"] == rid].iloc[0]
                    base = float(rec["Tam_base"])
                    det_rec = det[det["Id_Receta"] == rid]
                    costo_total_nuevo = 0.0
                    for _, d in det_rec.iterrows():
                        ing = d["Ingrediente"]
                        cant = float(d["Cantidad"])
                        costo_ing = float(ingredientes[ingredientes["Nombre"] == ing]["Costo_unitario"].iloc[0])
                        costo_total_nuevo += cant * costo_ing
                    recetas.loc[recetas["Id_Receta"] == rid, "Costo_total"] = costo_total_nuevo
                    costo_unit = costo_total_nuevo / base if base > 0 else 0
                    resultados.append([rec["Nombre"], costo_total_nuevo, costo_unit])

                guardar_csv(recetas, archivos["recetas"])
                st.session_state.recetas = recetas
                if resultados:
                    st.dataframe(pd.DataFrame(resultados, columns=["Receta", "Costo base", "Costo por g"]))
                st.success("Costos actualizados correctamente.")

    with tab2:
        green_sub("Configurar márgenes por canal")
        if margenes.empty:
            margenes = pd.DataFrame({"Canal": ["Venta directa", "Distribuidor", "Mayorista", "Online"], "Margen": [40, 30, 20, 35]})
        nuevos = []
        for _, row in margenes.iterrows():
            canal = row["Canal"]
            margen_actual = int(row["Margen"])
            nuevo = st.slider(f"Margen para {canal}", min_value=0, max_value=100, value=margen_actual)
            nuevos.append(nuevo)
        margenes["Margen"] = nuevos
        st.session_state.margenes = margenes
        guardar_csv(margenes, archivos["margenes"])
        st.success("Márgenes actualizados.")

        st.markdown("---")
        green_sub("Simulador de precios por receta")
        if recetas.empty:
            st.info("No hay recetas.")
        else:
            rec_sel = st.selectbox("Receta", sorted(recetas["Nombre"].unique().tolist()))
            rec_row = recetas[recetas["Nombre"] == rec_sel].iloc[0]
            costo_base = float(rec_row.get("Costo_total", 0.0))
            tam_base = float(rec_row["Tam_base"])
            costo_por_g = costo_base / tam_base if tam_base > 0 else 0.0
            peso_unidad = st.number_input("Peso por unidad (g)", min_value=1.0, value=40.0, step=1.0)
            gasto_fijo_unidad = st.number_input("Gasto fijo estimado por unidad", min_value=0.0, value=0.0, step=1.0)

            costo_unitario = costo_por_g * peso_unidad
            costo_total_unidad = costo_unitario + gasto_fijo_unidad
            st.write(f"Costo directo por unidad: ${costo_unitario:.2f}")
            st.write(f"Costo total por unidad (con fijo): ${costo_total_unidad:.2f}")

            st.markdown("### Precios sugeridos por canal")
            for _, row in margenes.iterrows():
                canal = row["Canal"]
                margen = float(row["Margen"])
                precio = costo_total_unidad * (1 + margen / 100) if costo_total_unidad > 0 else 0
                st.write(f"{canal}: **${precio:.2f}**")

    with tab3:
        green_sub("Resumen de ventas y productos")
        if ventas.empty:
            st.info("Todavía no hay ventas.")
        else:
            df = ventas.copy()
            df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
            total_ventas = df["Precio_total"].sum()
            cant_total = df["Cantidad"].sum()
            st.write(f"Ventas totales: ${total_ventas:,.2f}")
            st.write(f"Cantidad vendida total (g): {cant_total:,.2f}")
            ranking = df.groupby("Producto")["Precio_total"].sum().sort_values(ascending=False)
            st.markdown("### Productos por facturación")
            st.dataframe(ranking.reset_index())


def render_trazabilidad(archivos):
    green_title("Trazabilidad completa")
    recetas = st.session_state.recetas
    recetas_det = st.session_state.recetas_detalle
    lotes_ing = st.session_state.lotes_ingredientes
    produccion = st.session_state.produccion
    prod_lotes = st.session_state.produccion_lotes
    ventas = st.session_state.ventas

    tab1, tab2 = st.tabs(["🔙 Desde lote PT", "🔜 Desde lote MP"])

    with tab1:
        green_sub("Desde un lote de producto granel hacia materias primas")
        if produccion.empty or prod_lotes.empty:
            st.info("Todavía no hay producción con trazabilidad.")
        else:
            lote_producto = st.selectbox("Seleccionar lote granel", sorted(produccion["Lote_producto"].unique().tolist()))
            prod_row = produccion[produccion["Lote_producto"] == lote_producto].iloc[0]
            receta_sel = prod_row["Receta"]
            id_prod = prod_row["Id_Prod"]

            st.markdown(f"### Receta utilizada: **{receta_sel}**")
            receta_row = recetas[recetas["Nombre"] == receta_sel].iloc[0]
            id_rec = receta_row["Id_Receta"]
            ingredientes_rec = recetas_det[recetas_det["Id_Receta"] == id_rec]
            st.markdown("#### Ingredientes declarados")
            st.dataframe(ingredientes_rec)

            green_sub("Lotes de materias primas consumidos")
            lotes_usados = prod_lotes[prod_lotes["Id_Prod"] == id_prod].merge(
                lotes_ing,
                on="Lote_interno",
                how="left",
                suffixes=("", "_mp")
            )
            if lotes_usados.empty:
                st.info("No se encontraron lotes asociados.")
            else:
                st.dataframe(lotes_usados)

    with tab2:
        green_sub("Desde un lote de materia prima hacia productos terminados")
        if lotes_ing.empty:
            st.info("No hay lotes de materias primas.")
        else:
            lote_mp = st.selectbox("Seleccionar lote MP", sorted(lotes_ing["Lote_interno"].unique().tolist()))
            lote_row = lotes_ing[lotes_ing["Lote_interno"] == lote_mp].iloc[0]

            st.markdown(
                f"**Ingrediente:** {lote_row['Ingrediente']}  \n"
                f"**Fecha compra:** {lote_row['Fecha_compra']}  \n"
                f"**Vencimiento:** {lote_row['Fecha_vencimiento']}  "
            )

            usados_en = prod_lotes[prod_lotes["Lote_interno"] == lote_mp].merge(
                produccion,
                on="Id_Prod",
                how="left",
                suffixes=("_uso", "_prod")
            )
            if usados_en.empty:
                st.info("Este lote aún no se usó en producción.")
            else:
                st.dataframe(usados_en)


def render_configuracion(archivos):
    green_title("Configuración general")
    gastos = st.session_state.gastos_fijos
    green_sub("Gastos fijos mensuales")
    if gastos.empty:
        st.info("Todavía no cargaste gastos fijos.")
    else:
        st.dataframe(gastos)

    with st.form("nuevo_gasto"):
        col1, col2 = st.columns(2)
        with col1:
            categoria = st.text_input("Categoría (ej: Luz, Internet, Monotributo)")
            monto = st.number_input("Monto mensual", min_value=0.0, step=100.0)
        with col2:
            fecha = st.date_input("Fecha", value=date.today())
            notas = st.text_area("Notas")
        enviar = st.form_submit_button("Agregar gasto")
        if enviar:
            nuevo_id = 1 if gastos.empty else int(gastos["Id"].max()) + 1
            nuevo = {"Id": float(nuevo_id), "Categoria": categoria, "Monto_mensual": monto, "Fecha": fecha.strftime("%Y-%m-%d"), "Notas": notas}
            gastos = pd.concat([gastos, pd.DataFrame([nuevo])], ignore_index=True)
            st.session_state.gastos_fijos = gastos
            guardar_csv(gastos, archivos["gastos_fijos"])
            st.success("Gasto agregado.")
            st.rerun()


def render_reset_parcial(archivos):
    green_title("Reset parcial – Producción y Recetas")
    st.warning("""Esto eliminará SOLO:
    - Recetas
    - Detalles de recetas
    - Producción (lotes granel)
    - Trazabilidad de producción
    - Stock de productos terminados
    - Mínimos de stock de productos
    NO se borrará: Compras, Proveedores, Ingredientes, Lotes MP, Mínimos MP, Clientes, Ventas, Gastos, Movimientos.
    """)
    confirmar = st.checkbox("Entiendo y deseo borrar producción y recetas")
    if confirmar and st.button("Ejecutar reset parcial", use_container_width=True):
        claves_borrar = ["recetas", "recetas_detalle", "produccion", "produccion_lotes", "stock_productos", "stock_minimos"]
        for clave in claves_borrar:
            df_vacio = pd.DataFrame(columns=st.session_state[clave].columns)
            st.session_state[clave] = df_vacio
            guardar_csv(df_vacio, archivos[clave])
        st.success("Producción y recetas reiniciadas correctamente.")
        st.balloons()
        st.rerun()


def render_reset_total(archivos):
    green_title("Reset COMPLETO del ERP v2")
    st.error("""⚠ Esto borrará TODOS los datos de la versión v2 (carpeta data_v2). Tu app original y /data NO se tocan.""")
    confirmar = st.checkbox("Entiendo y deseo borrar absolutamente todo (v2)")
    if confirmar and st.button("🧼 Ejecutar reset total", use_container_width=True):
        for nombre, ruta in archivos.items():
            columnas = st.session_state[nombre].dtypes.to_dict()
            df_vacio = pd.DataFrame(columns=columnas.keys())
            guardar_csv(df_vacio, ruta)
            st.session_state[nombre] = df_vacio
        st.success("ERP v2 reiniciado completamente.")
        st.balloons()
        st.rerun()
