# views/lista_precios.py
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from modules.data_manager import get_df, load_data, calcular_stock_actual
from modules.conversions import convertir_a_base
from views.recetas import obtener_codigo_vendedor

try:
    from fpdf import FPDF
except ImportError:
    st.error("⚠️ El módulo 'fpdf2' no está instalado. Ejecuta: pip install fpdf2")
    FPDF = None

def clean_text(text):
    if text is None: return ""
    text = str(text)
    replacements = {
        "ō": "o", "Ō": "O", "ū": "u", "Ū": "U", "–": "-", "—": "-", 
        "'": "'", """: '"', """: '"', "á": "a", "é": "e", "í": "i", 
        "ó": "o", "ú": "u", "ñ": "n", "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    try:
        return text.encode('latin-1', 'replace').decode('latin-1')
    except:
        return text

def normalizar_nombre(nombre):
    """Limpia el nombre para facilitar la busqueda en el catalogo."""
    if not nombre: return ""
    n = str(nombre).lower().strip()
    for char in [":", "-", ".", ",", "(", ")", "&", "'"]:
        n = n.replace(char, " ")
    tildes = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u"}
    for t, n_t in tildes.items():
        n = n.replace(t, n_t)
    return " ".join(n.split())

CAT_ORDER = {
    "🧂 Sales": 1,
    "🌿 Blends": 2,
    "💚 Vital": 3,
    "🍵 Tés": 4,
    "🍹 Mocktails": 5,
    "🌶️ Pimientas": 6
}

def detectar_categoria(nombre_producto):
    """Detecta la categoría comercial del producto."""
    nombre = str(nombre_producto).lower()
    if "sal " in nombre or nombre.startswith("sal"):
        return "🧂 Sales"
    elif "vital" in nombre:
        return "💚 Vital"
    elif "té " in nombre or "te " in nombre or "rooibos" in nombre or "karak" in nombre:
        return "🍵 Tés"
    elif "mocktail" in nombre:
        return "🍹 Mocktails"
    elif "pimienta" in nombre:
        return "🌶️ Pimientas"
    else:
        return "🌿 Blends"

def generar_excel_mayorista(df_input):
    """Genera la planilla Excel (.xlsx) idéntica al formato comercial de vinería/distribuidor."""
    filas = []
    for _, r in df_input.iterrows():
        gv = r.get("Gramaje_Venta")
        gramaje = int(gv) if pd.notnull(gv) and gv > 0 else int(r.get("Base_g", 100))
        cat = r.get("Categoria") or detectar_categoria(r["Nombre"])
        cod_lote = r.get("Codigo", "") if pd.notna(r.get("Codigo")) and str(r.get("Codigo")).strip() != "" else f"L {r['Nombre'][:4].upper()}"
        cod_pos = obtener_codigo_vendedor(r.get("Codigo"), r["Nombre"])
        
        filas.append({
            "Categoría": cat,
            "Producto": r["Nombre"],
            "Gramaje (g)": gramaje,
            "Código Lote": cod_lote,
            "Código POS / Barras": cod_pos,
            "Precio Mayorista ($)": float(r["Precio_Mayorista"]),
            "PVP Sugerido ($)": float(r["PVP_Calculado"]),
            "Cat_Order": CAT_ORDER.get(cat, 99)
        })
    
    df_excel = pd.DataFrame(filas)
    df_excel = df_excel.sort_values(["Cat_Order", "Producto"]).drop(columns=["Cat_Order"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_excel.to_excel(writer, sheet_name='Lista Mayorista', index=False)
    buffer.seek(0)
    return buffer.getvalue()

# --- CATALOGO DE DESCRIPCIONES PROFESIONALES (Blender & Chef) ---
CATALOGO_DESCRIPCIONES = {
    # === SALES ===
    "sal al malbec": "Cristales de sal marina en reduccion de Malbec. Final elegante para carnes rojas y quesos anejos.",
    "sal british": "Sal marina infusionada en vinagre. El toque clasico para pescados, patatas fritas y vegetales.",
    "sal de hierbas ahumadas": "Aroma de fogones del sur. Ideal para carnes , legumbres y sopas rusticas.",
    "sal de limon y chile": "Frescura y fuego. Esencial para pescados, mariscos, ceviches, Aves o escarchar copas.",
    "sal de rosas y romero": "Alquimia floral. Ideal para cordero, quesos de cabra y ensaladas frescas.",
    "sal del desierto": "Especias de la Ruta de la Seda (Sumac, Cardamomo). Perfecta para kebabs, hummus y yogurt.",
    "sal negra hawaiana": "Contraste visual y sabor volcanico con carbon activado. Para huevos, Paltas y Carnes Rojas.",
    "sal negra tipo hawaiana": "Contraste visual y sabor volcanico con carbon activado. Para  huevos ,Paltas y Carnes Rojas.",
    "sal svanetian": "Secreto del Caucaso con ajo y calendula. Para frotar en piezas de carne o panes artesanales.",
    "sal esvanetian": "Secreto del Caucaso con ajo y calendula. Para frotar en piezas de carne o panes artesanales.",
    "sal vikinga ahumada": "Legado nordico con curcuma y cebolla quemada. Final ideal para salmon y vegetales asados.",
    
    # === BLENDS & SAZONADORES ===
    "advieh persa": "La Joya de Iran. Blend floral con rosas y azafran. Para arroces perfumados o cordero de autor.",
    "ajo a las hierbas gourmet": "Perfil provenzal con lavanda y estragon. Para pastas, pizzas o mantequillas compuestas.",
    "baharat": "El alma de Oriente. Calido y especiado; base fundamental para koftas y arroces arabes.",
    "bbq rojo malbec": "Rub premium con shiitake y cafe. Disenado para largas cocciones tipo brisket o costillar.",
    "criolla deshidratada": "Esencia pampeana con tomate y cebolla crispy. Para empanadas, salsas y sofritos criollos.",
    "curry colombo": "Fusion de las Antillas. Vital para platos con leche de coco, pescados e ingredientes tropicales.",
    "crocante panko sesamo limon": "Textura y frescura citrica. Rebozado final para pescados, mariscos o gratinados.",
    "khmeli suneli": "Bouquet georgiano herbal. Unico para estofados de invierno y zapallos asados.",
    "muddica atturrata": "Queso de los pobres. Terminacion siciliana crocante para pastas y ensaladas.",
    "nanami togarashi": "Sabores de Japon. Toque citrico y picante para ramens y platos asiaticos.",
    "panch phoron": "Cinco semillas de Bengala. Templar en ghee para aromatizar dals, Pescados o Legumbres.",
    "pesto siciliano con pistacho": "Oro verde con pistacho. Mezclar con aceite de oliva para pastas o crostini instantaneos.",
    "blend pescados y mariscos": "Brisa del Mediterraneo con eneldo y estragon. Para marinadas o terminacion de ceviches.",
    "tandoori masala": "Fuego de la India. Mezclar con yogurt para marinar aves y carnes blancas.",
    "zaatar": "Perfume de Oriente Medio. Untar en pan pita con oliva o espolvorear en hummus y huevos.",
    "blend burger": "Secreto ahumado profesional con pimienta larga y mostaza. Integrar directo a la carne picada.",
    "sloopy joe": "Salsa especiada estilo USA. Ideal para carnes desmenuzadas, hot dogs y sandwiches.",
    "dip ranch": "Sazonador para dips cremosos. Mezclar con crema agria o yogurt para picadas premium.",
    "blend bosque y brasas": "Perfil terroso con enebro y cacao. Potencia carnes de caza, picana y portobellos asados.",
    "blend kebab dip": "Marinado mediterraneo con menta y sumac. Para brochetas o salsas de yogurt frescas.",
    "blend kebab y dip": "Marinado mediterraneo con menta y sumac. Para brochetas o salsas de yogurt frescas.",
    "jerk jamaica": "Ritmo del Caribe. Rub intenso para carbon; ideal para pollo, cerdo y pescados al grill.",
    
    # === LINEA VITAL (0% Sodio) ===
    "vital caldo": "Puro Umami 0% Sodio. Concentrado de shiitake y levadura para sopas y arroces saludables.",
    "vital italia": "0% Sodio - Alma Mediterranea con tomate y albahaca. Para pastas y risottos intensos.",
    "vital india": "0% Sodio - Especias de Oriente. Ideal para currys, salteados y platos con coco.",
    "vital parrillera": "0% Sodio - Potenciador parrillero con pimenton ahumado. Para carnes o vegetales al grill.",
    "vital criollo": "0% Sodio - Esencia Argentina con laurel y verdeo. Para empanadas, guisos y estofados.",
    "vital citrus": "0% Sodio - Citricos y Hierbas. Realza pescados, aves y ensaladas frescas.",
    "vital tipo queso": "0% Sodio - Sabor Parmesano con sesamo tostado. Para polentas, pastas y gratinados.",
    
    # === PIMIENTAS DE AUTOR ===
    "pimienta negra de autor": "Tierra, sal y humo. Blend de Pimienta Larga con cardamomo negro para carnes intensas.",
    "pimienta roja y larga": "Dulzor especiado con mandarina y cacao. Para cerdo, pato o postres de chocolate.",
    "pimienta roja y pimienta larga": "Dulzor especiado con mandarina y cacao. Para cerdo, pato o postres de chocolate.",
    "pimienta verde de autor": "Perfil botanico con enebro y naranja amarga. Para pescados grasos o perfumar Gin Tonic.",
    
    # === MOCKTAILS (Bases 0% Alcohol) ===
    "mocktail floral hibiscus": "Flor de hibiscus y pomelo. Base para cocteles sin alcohol vibrantes y refrescantes.",
    "mocktail dorado especiado": "Manzana y canela. Para bebidas reconfortantes frias o calientes tipo Apple Pie.",
    "mocktail aperitivo botanico": "Esencia de Amari con genciana y enebro. Ideal para Spritz sin alcohol o tonica.",
    
    # === TES DE AUTOR ===
    "rooibos ambar africano": "Fusion sin cafeina con miel y rosa mosqueta. Dulzor natural para cualquier hora.",
    "te karak": "Intensidad del Golfo Persico. Hervir con leche y azucar para una experiencia arabe.",
    "te pu erh rojo malbec": "Te de guarda y vino. Notas terrosas y jengibre; maridaje ideal para un trozo de chocolate amargo.",
}

def obtener_descripcion(row):
    df_d = get_df("recetas_det")
    if df_d.empty: return ""
    rid = row["Id"]
    ingredientes = df_d[df_d["Id_Receta"] == rid]["Ingrediente"].tolist()
    
    # Limpiar strings, quitar nulos
    ingredientes = [str(x) for x in ingredientes if pd.notnull(x) and str(x).strip() != ""]
    
    # Filtrar descartables (envases, etiquetas)
    descartables = ["etiqueta", "envase", "cinta", "cuchara", "doy-pak", "doy pack", "frasco", "molinillo", "pet", "tubo"]
    ing_filtrados = []
    for ing in ingredientes:
        if not any(desc in ing.lower() for desc in descartables):
            ing_filtrados.append(ing)
            
    if not ing_filtrados: return ""
    
    # Solo los primeros 5 para que no sea un testamento
    desc = ", ".join(ing_filtrados[:5])
    if len(ing_filtrados) > 5:
        desc += "..."
    return desc

def render_lista_precios_tab():
    st.subheader("📋 Generador de Lista de Precios")
    
    df_r = get_df("recetas")
    if df_r.empty:
        st.warning("No hay recetas disponibles."); return

    # --- INICIO SCANNER RENTABILIDAD ---
    col_s1, col_s2 = st.columns([2, 1])
    search = col_s1.text_input("🔍 Buscar Producto...", "")
    modo_auditoria = col_s2.toggle("🚨 Modo Auditoría (Márgenes)", help="Calcula el margen real entre tu Costo de HOY y tu Precio Mayorista.")
    if modo_auditoria:
        col_s2.caption("*(🔴 < 15% | 🟡 15% - 35% | 🟢 > 35%)*")
    # --- FIN SCANNER RENTABILIDAD ---

    df_p = df_r.copy()
    
    # Ocultar recetas archivadas
    if "Archivada" not in df_p.columns: df_p["Archivada"] = False
    df_p = df_p[df_p["Archivada"].astype(str).str.lower() != "true"]
    
    if search:
        df_p = df_p[df_p["Nombre"].str.contains(search, case=False, na=False)]
    
    if "Markup_Revendedor" not in df_p.columns: df_p["Markup_Revendedor"] = 0.0
    if "Precio_Venta" not in df_p.columns: df_p["Precio_Venta"] = 0.0
    
    # Si por algun motivo no existe la columna (receta vieja), hace un fallback.
    if "PVP_Sugerido" not in df_p.columns: df_p["PVP_Sugerido"] = df_p["Precio_Mayorista"] * (1 + df_p.get("Markup_Revendedor", 0) / 100)

    # Ahora la Lista de Precios obedece 100% al redondeo manual guardado en el Simulador
    df_p["PVP_Calculado"] = df_p["PVP_Sugerido"]
    df_p["Precio_Mayorista"] = df_p["Precio_Mayorista"].fillna(0.0)
    df_p["Tu_Precio"] = df_p["Precio_Venta"].fillna(0.0)
    df_p["Categoria"] = df_p["Nombre"].apply(detectar_categoria)
    df_p["Cat_Order"] = df_p["Categoria"].map(lambda x: CAT_ORDER.get(x, 99))
    df_p = df_p.sort_values(["Cat_Order", "Nombre"])
    df_p["Desc_Final"] = df_p.apply(obtener_descripcion, axis=1)
    
    # Usar Gramaje_Venta para el nombre (fallback a Base_g)
    def get_display_gramaje(row):
        gv = row.get("Gramaje_Venta")
        if pd.notnull(gv) and gv > 0: return gv
        return row.get("Base_g", 100)
        
    df_p["Producto_Full"] = df_p.apply(lambda x: f"{x['Nombre']} ({get_display_gramaje(x):.0f}g)", axis=1)

    # --- LÓGICA DE AUDITORÍA DE COSTOS ---
    if modo_auditoria:
        df_rd = load_data("recetas_det")
        df_sl = load_data("stock_log")
        df_i = load_data("ingredientes")
        stock = calcular_stock_actual(df_sl, df_i)
        precios_map = stock.set_index("Ingrediente")["Costo_Ponderado"].to_dict()
        
        costos_reales = []
        estados = []
        margenes = []
        
        for idx, row in df_p.iterrows():
            rid = row["Id"]
            gramos = get_display_gramaje(row)
            
            # Cargar detalle
            mis_ing = df_rd[df_rd["Id_Receta"] == rid].copy()
            if mis_ing.empty:
                costos_reales.append(0)
                estados.append("⚪ Sin Datos")
                margenes.append("0%")
                continue
                
            mis_ing["Costo_Unitario"] = mis_ing["Ingrediente"].map(precios_map).fillna(0.0)
            mis_ing["Cantidad_Base"] = mis_ing.apply(
                lambda r: convertir_a_base(r["Cantidad"], str(r.get("Unidad_Consumo", "g")).lower().strip()), axis=1
            )
            mis_ing["Costo_Total_Linea"] = mis_ing["Cantidad_Base"] * mis_ing["Costo_Unitario"]
            
            # Costo del batch
            peso_batch_kg = mis_ing["Cantidad_Base"].sum() / 1000.0
            if peso_batch_kg <= 0: peso_batch_kg = 1.0
            costo_frasco = (mis_ing["Costo_Total_Linea"].sum() / peso_batch_kg) * (gramos / 1000.0)
            
            # Sumar Gastos Fijos, IIBB y Fabrica (Costo Operativo) para comparar manzanas con manzanas
            gf = float(row.get("Gastos_Fijos_Pct", 0.0))
            iibb = float(row.get("IIBB_Pct", 0.0))
            margen_fab = float(row.get("Margen_Fabrica_Pct", 0.0))
            
            # Costo total incluyendo fabrica
            c_op = (costo_frasco * (1 + gf/100)) * (1 + iibb/100)
            costo_fabrica = c_op * (1 + margen_fab/100)
            
            precio_may = row["Precio_Mayorista"]
            
            if precio_may > 0:
                margen_real_pct = ((precio_may - costo_fabrica) / precio_may) * 100
            else:
                margen_real_pct = 0.0
            
            costos_reales.append(costo_fabrica)
            margenes.append(f"{margen_real_pct:.1f}%")
            
            # Semáforo: Rojo si el margen es menor al 15% (muy bajo o negativo)
            if margen_real_pct < 15.0:
                estados.append("🔴 PELIGRO")
            elif margen_real_pct < 35.0:
                estados.append("🟡 ALERTA")
            else:
                estados.append("🟢 SANO")
                
        df_p["Costo_Base_Total"] = costos_reales
        df_p["Margen_Real"] = margenes
        df_p["Estado"] = estados
    
    # Agregar columna para seleccionar qué imprimir
    df_p.insert(0, "Imprimir", True)

    st.write("✏️ **Puedes desmarcar los productos que NO quieras incluir en el PDF:**")
    
    if modo_auditoria:
        cols_to_show = ["Imprimir", "Estado", "Producto_Full", "Costo_Base_Total", "Precio_Mayorista", "Margen_Real", "PVP_Calculado"]
        col_config = {
            "Imprimir": st.column_config.CheckboxColumn("🖨️ Imprimir", default=True),
            "Estado": st.column_config.TextColumn("Salud", disabled=True),
            "Producto_Full": st.column_config.TextColumn("Producto", disabled=True),
            "Costo_Base_Total": st.column_config.NumberColumn("Costo+Fábrica", format="$ %.2f", disabled=True),
            "Precio_Mayorista": st.column_config.NumberColumn("Precio Mayorista", format="$ %.2f", disabled=True),
            "Margen_Real": st.column_config.TextColumn("Margen %", disabled=True),
            "PVP_Calculado": st.column_config.NumberColumn("PVP Sugerido", format="$ %.2f", disabled=True)
        }
    else:
        cols_to_show = ["Imprimir", "Categoria", "Producto_Full", "Precio_Mayorista", "PVP_Calculado", "Tu_Precio"]
        col_config = {
            "Imprimir": st.column_config.CheckboxColumn("🖨️ Imprimir", default=True),
            "Categoria": st.column_config.TextColumn("Categoría", disabled=True),
            "Producto_Full": st.column_config.TextColumn("Producto (Presentación)", disabled=True),
            "Precio_Mayorista": st.column_config.NumberColumn("Precio Mayorista", format="$ %.0f", disabled=True),
            "PVP_Calculado": st.column_config.NumberColumn("PVP Sugerido", format="$ %.0f", disabled=True),
            "Tu_Precio": st.column_config.NumberColumn("Tu Precio", format="$ %.0f", disabled=True)
        }
        
    edited_df = st.data_editor(
        df_p[cols_to_show],
        column_config=col_config,
        use_container_width=True, 
        hide_index=True
    )

    df_p["Imprimir"] = edited_df["Imprimir"].values
    df_imprimir = df_p[df_p["Imprimir"] == True]

    st.divider()
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        titulo_reporte = st.text_input("Título del Reporte", "Rojo Malbec - Lista de Precios")
    
    with col2:
        btn_clientes = st.button("📄 PDF (Mayoristas)", type="primary", use_container_width=True)
    with col3:
        btn_local = st.button("📄 PDF (Mostrador)", type="primary", use_container_width=True)
    with col4:
        excel_bytes = generar_excel_mayorista(df_imprimir)
        st.download_button(
            label="📊 Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"Lista_Precios_Codigos_RojoMalbec_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    if btn_clientes or btn_local:
        tipo_pdf = "mayorista" if btn_clientes else "local"
        if FPDF is None:
            st.error("Instala fpdf2 para continuar."); return

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=35)
            
            # Encabezado
            pdf.set_font("Arial", "B", 16)
            pdf.cell(190, 10, clean_text(titulo_reporte), ln=True, align='C')
            pdf.set_font("Arial", "", 10)
            pdf.cell(190, 5, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
            if tipo_pdf == "local":
                pdf.set_font("Arial", "I", 10)
                pdf.cell(190, 5, clean_text("Lista Exclusiva Mostrador"), ln=True, align='C')
            pdf.ln(8)
            
            # Tabla Headers Generales
            pdf.set_fill_color(220, 220, 220)
            pdf.set_font("Arial", "B", 10)
            if tipo_pdf == "mayorista":
                pdf.cell(100, 8, "  PRODUCTO (PRESENTACION)", 1, 0, 'L', True)
                pdf.cell(45, 8, "MAYORISTA", 1, 0, 'R', True)
                pdf.cell(45, 8, "PVP SUG.", 1, 1, 'R', True)
            else:
                pdf.cell(145, 8, "  PRODUCTO (PRESENTACION)", 1, 0, 'L', True)
                pdf.cell(45, 8, "TU PRECIO", 1, 1, 'R', True)
            
            cat_actual = None
            for _, row in df_imprimir.iterrows():
                c = row["Categoria"]
                if c != cat_actual:
                    cat_actual = c
                    pdf.ln(3)
                    pdf.set_fill_color(139, 0, 0) # Rojo Malbec
                    pdf.set_font("Arial", "B", 10)
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(190, 7, clean_text(f"  {c.upper()}"), 1, 1, 'L', True)
                    pdf.set_text_color(0, 0, 0)

                # Usar Gramaje_Venta para el PDF
                gv = row.get("Gramaje_Venta")
                peso_g = gv if pd.notnull(gv) and gv > 0 else row.get("Base_g", 100)
                
                nom_txt = clean_text(f"{row['Nombre']} ({peso_g:.0f}g)")
                desc_txt = clean_text(row["Desc_Final"])

                # Nombre y Precios
                pdf.set_font("Arial", "B", 9.5)
                
                if tipo_pdf == "mayorista":
                    may_txt = f"$ {row['Precio_Mayorista']:,.0f}"
                    pvp_txt = f"$ {row['PVP_Calculado']:,.0f}"
                    pdf.cell(100, 6.5, "  " + nom_txt, 1, 0, 'L')
                    pdf.set_font("Arial", "", 9.5)
                    pdf.cell(45, 6.5, may_txt, 1, 0, 'R')
                    pdf.cell(45, 6.5, pvp_txt, 1, 1, 'R')
                else:
                    tu_txt = f"$ {row['Tu_Precio']:,.0f}"
                    pdf.cell(145, 6.5, "  " + nom_txt, 1, 0, 'L')
                    pdf.set_font("Arial", "", 9.5)
                    pdf.cell(45, 6.5, tu_txt, 1, 1, 'R')

                # Descripcion debajo
                pdf.set_font("Arial", "I", 8)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(190, 4.5, "  " + desc_txt, 0, 1, 'L')
                pdf.set_text_color(0, 0, 0)

            # Espacio antes del footer
            pdf.ln(15)

            # SECCION LEGAL Y BENEFICIOS
            pdf.set_font("Arial", "B", 10)
            pdf.cell(190, 8, clean_text("Politica Comercial y Logistica"), 0, 1, 'L')
            pdf.set_font("Arial", "", 9)
            l1 = "- Precios Sugeridos: Los valores de venta al publico (PVP) son una referencia."
            l2 = "- Beneficio de Envio: En pedidos superiores a $150.000, el flete corre por nuestra cuenta."
            pdf.cell(190, 5, clean_text(l1), 0, 1, 'L')
            pdf.set_font("Arial", "B", 9)
            pdf.cell(190, 5, clean_text(l2), 0, 1, 'L')
            pdf.ln(10)
            pdf.set_font("Arial", "I", 9)
            pdf.cell(190, 5, clean_text("Rojo Malbec Sales & Blends - Pasion por el Sabor."), 0, 1, 'C')
            
            pdf_bytes = bytes(pdf.output()) 
            sufijo = "Mostrador" if tipo_pdf == "local" else "Mayorista"
            st.download_button(label="💾 Descargar PDF", data=pdf_bytes, file_name=f"Lista_{sufijo}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
            st.success("¡PDF generado correctamente!")
            
        except Exception as e:
            st.error(f"Error tecnico: {e}")

if __name__ == "__main__":
    render_lista_precios_tab()