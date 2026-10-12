#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║       GENERADOR DE CATÁLOGO PDF - ROJO MALBEC               ║
║       Ejecutar: python generar_catalogo_pdf.py               ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import re
import unicodedata
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from PIL import Image

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(BASE_DIR, "claves", "rojomalbecapp-366a663c2610.json")
SHEET_NAME = "RojoMalbec DB"
FOTOS_CATALOGO_DIR = os.path.join(BASE_DIR, "Fotos_catalogo")
FOTOS_ETIQUETAS_DIR = os.path.join(BASE_DIR, "distribuidor_app", "images")
LOGO_PATH = os.path.join(BASE_DIR, "distribuidor_app", "logo.png")
DESC_PATH = os.path.join(BASE_DIR, "distribuidor_app", "Descripciones_RojoMalbec.md")
desktop_path = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), "Desktop", "catalogo")
OUTPUT_PDF = os.path.join(desktop_path, "Catalogo_RojoMalbec.pdf")

# Colores (R, G, B)
COLOR_VINO = (139, 0, 0)
COLOR_DORADO = (212, 175, 55)
COLOR_GRIS_OSCURO = (60, 60, 60)
COLOR_GRIS_CLARO = (150, 150, 150)
COLOR_FONDO_PRECIO = (245, 245, 245)
COLOR_BLANCO = (255, 255, 255)
COLOR_NEGRO = (0, 0, 0)


# ═══════════════════════════════════════════════════════════
# FUNCIONES DE DATOS
# ═══════════════════════════════════════════════════════════

def cargar_datos_gsheets():
    """Carga los productos desde Google Sheets (solo visibles en B2B)."""
    print("📡 Conectando con Google Sheets...")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)
    gc = gspread.authorize(creds)
    
    sh = gc.open(SHEET_NAME)
    ws = sh.worksheet("recetas")
    raw = ws.get_all_values()
    
    headers = [h.strip() for h in raw[0]]
    productos = []
    
    for row in raw[1:]:
        d = dict(zip(headers, row))
        
        # Filtrar solo visibles
        vis = str(d.get("Visible_B2B", "1")).strip().upper()
        if vis not in ["1", "TRUE", "SI", "SÍ", "YES", ""]:
            continue
        
        # Filtrar sin precio
        try:
            precio_may = float(str(d.get("Precio_Mayorista", "0")).replace(",", ".").strip())
        except:
            precio_may = 0
        if precio_may <= 0:
            continue
        
        # PVP sugerido
        try:
            pvp = float(str(d.get("PVP_Sugerido", "0")).replace(",", ".").strip())
        except:
            pvp = 0
        if pvp <= 0:
            try:
                markup = float(str(d.get("Markup_Revendedor", "0")).replace(",", ".").strip())
            except:
                markup = 0
            if markup > 0:
                pvp = precio_may * (1 + markup / 100)
            else:
                pvp = precio_may * 1.5
        
        productos.append({
            "nombre": str(d.get("Nombre", "")).strip(),
            "precio_mayorista": round(precio_may),
            "pvp_sugerido": round(pvp),
        })
    
    print(f"✅ {len(productos)} productos visibles cargados.")
    return sorted(productos, key=lambda x: x["nombre"])


def cargar_descripciones():
    """Carga las descripciones desde el archivo Markdown."""
    if not os.path.exists(DESC_PATH):
        print("⚠️ No se encontró el archivo de descripciones.")
        return {}
    
    with open(DESC_PATH, "r", encoding="utf-8") as f:
        contenido = f.read()
    
    descripciones = {}
    bloques = contenido.split("---")
    
    for bloque in bloques:
        lineas = [l.strip() for l in bloque.strip().split("\n") if l.strip()]
        if not lineas:
            continue
        
        # Buscar línea con ##
        nombre_linea = None
        for l in lineas:
            if l.startswith("##") and not l.startswith("###"):
                nombre_linea = l
                break
        
        if not nombre_linea:
            continue
        
        nombre = nombre_linea.replace("#", "").strip()
        # Quitar emojis del nombre
        nombre_limpio = re.sub(r'[^\w\s\(\)\-\'\&áéíóúüñÁÉÍÓÚÜÑ]', '', nombre).strip()
        
        # Juntar el resto como descripción
        idx = lineas.index(nombre_linea)
        desc_lineas = lineas[idx+1:]
        desc_texto = "\n".join(desc_lineas)
        
        descripciones[nombre_limpio] = desc_texto
    
    print(f"✅ {len(descripciones)} descripciones cargadas.")
    return descripciones


def detectar_categoria(nombre_producto):
    nombre = str(nombre_producto).lower()
    if "sal " in nombre or nombre.startswith("sal"):
        return "Sales Gourmet"
    elif "vital" in nombre:
        return "Línea Vital"
    elif "té " in nombre or nombre.startswith("te ") or " rooibos" in nombre or nombre.startswith("rooibos") or " karak" in nombre or nombre.startswith("karak"):
        return "Tés de Autor"
    elif "mocktail" in nombre:
        return "Mocktails"
    elif "pimienta" in nombre:
        return "Pimientas de Autor"
    else:
        return "Blends Especiados"


def normalizar(texto):
    """Normaliza texto para comparación."""
    t = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^a-zA-Z0-9]', '', t).lower()


def buscar_descripcion(nombre_producto, descripciones):
    """Busca la descripción de un producto en el diccionario."""
    norm_prod = normalizar(nombre_producto)
    for nombre_desc, texto in descripciones.items():
        if normalizar(nombre_desc) in norm_prod or norm_prod in normalizar(nombre_desc):
            return texto
    return ""


def buscar_foto(nombre_producto):
    """Busca foto: primero en Fotos_catalogo, luego en etiquetas."""
    
    # Diccionario de mapeo para fotos de catálogo
    mapeo_catalogo = {
        "sal al malbec": "sal al malbec",
        "sal british": "Sal British",
        "sal negra": "Sal Negra",
        "sal de limón": "Sal de limon y chile",
        "sal de limon": "Sal de limon y chile",
        "sal de rosas": "sal marina de rosas y romero",
        "sal del desierto": "Sal del desierto",
        "sal esvanetian": "sal tipo svanetian",
        "sal vikinga": None,
        "españa profunda": "España Profunda",
        "espana profunda": "España Profunda",
        "za'atar": "Za,atar",
        "zaatar": "Za,atar",
        "nanami": "nanami torigashi final",
        "barbacoa": "Barbacoa Rub",
        "ajo": "Ajos & Hierbas",
        "curry colombo": "Curry Colombo",
        "mole mexicano": "Mole Mexicano",
        "panch phoron": "panch phoron",
        "sloppy": "sloppy_joe_v2",
        "sloopy": "sloppy_joe_v2",
        "glühwein": "gluhwein",
        "gluhwein": "gluhwein",
        "vital": "vital_caldo_v2",
        "pimienta roja": "Pimienta Roja y Pimienta Larga",
        "pimienta larga": "Pimienta Roja y Pimienta Larga",
    }
    
    nombre_lower = nombre_producto.lower()
    
    # 1) Buscar en Fotos_catalogo
    if os.path.exists(FOTOS_CATALOGO_DIR):
        # Intentar con el mapeo
        for clave, archivo_base in mapeo_catalogo.items():
            if clave in nombre_lower and archivo_base:
                for ext in [".png", ".jpg", ".jpeg"]:
                    ruta = os.path.join(FOTOS_CATALOGO_DIR, archivo_base + ext)
                    if os.path.exists(ruta):
                        return ruta
        
        # Intentar búsqueda por nombre directo
        norm = normalizar(nombre_producto)
        for f in os.listdir(FOTOS_CATALOGO_DIR):
            if normalizar(os.path.splitext(f)[0]) in norm or norm in normalizar(os.path.splitext(f)[0]):
                return os.path.join(FOTOS_CATALOGO_DIR, f)
    
    # 2) Fallback: buscar etiqueta (misma lógica que la app B2B)
    if os.path.exists(FOTOS_ETIQUETAS_DIR):
        term = nombre_lower
        
        # Diccionario inteligente de etiquetas
        if "sloopy joe" in term or "sloppy" in term: term = "sloppyjoe"
        elif "sal al malbec" in term: term = "malbec"
        elif "sal negra" in term or "hawaiana" in term: term = "hawaiana"
        elif "ajo a las hierbas" in term: term = "ajohierbas"
        elif "bbq" in term or "barbacoa" in term: term = "barbacoa"
        elif "bosque y brasas" in term: term = "bosque"
        elif "kebab" in term: term = "kebab"
        elif "panko" in term or "sesamo y limon" in term: term = "sesamo"
        elif "españa profunda" in term or "espana" in term: term = "espana"
        elif "glühwein" in term or "gluhwein" in term: term = "gluhwein"
        elif "mocktail" in term: term = "botanico"
        elif "panch" in term: term = "panch"
        elif "criolla deshidratada" in term: term = "criolla"
        elif "rooibos" in term: term = "rooibos"
        elif "sal british" in term: term = "british"
        elif "esvanetian" in term: term = "svanetian"
        elif "rosas y romero" in term: term = "rosas"
        elif "del desierto" in term: term = "desierto"
        elif "vikinga" in term: term = "vikinga"
        elif "limon y chile" in term: term = "limonchile"
        elif "queso" in term: term = "queso"
        elif "parrilera" in term: term = "parrilera"
        elif "pimienta negra" in term: term = "pimientanegra"
        elif "pimienta roja" in term: term = "pimientaroja"
        elif "pimienta verde" in term: term = "pimientaverde"
        elif "jerk" in term: term = "jerk"
        elif "nanami" in term: term = "nanami"
        elif "pesto" in term: term = "pesto"
        elif "za'atar" in term or "zaatar" in term: term = "zaatar"
        else:
            term = term.replace(" ", "")
        
        term = term.replace("&", "").replace("(", "").replace(")", "").replace("ñ", "n").replace("ü", "u").replace("'", "").replace("ō", "o")
        
        archivos_validos = []
        for f in os.listdir(FOTOS_ETIQUETAS_DIR):
            f_limpio = f.lower().replace("ñ", "n")
            if "trasera" in f_limpio or "back" in f_limpio:
                continue
            f_sin_espacios = f_limpio.replace("_", "").replace(" ", "")
            if term in f_sin_espacios or term in f_limpio.replace("_", " "):
                archivos_validos.append(f)
        
        if archivos_validos:
            for f in archivos_validos:
                if "clean" in f.lower() or "frontal" in f.lower() or "color" in f.lower() or "premium" in f.lower():
                    return os.path.join(FOTOS_ETIQUETAS_DIR, f)
            return os.path.join(FOTOS_ETIQUETAS_DIR, archivos_validos[0])
    
    return None


def preparar_imagen(ruta_img, max_ancho=600, max_alto=600):
    """Redimensiona la imagen para que no sea demasiado grande y la convierte a JPG temporal."""
    try:
        img = Image.open(ruta_img)
        
        # Convertir RGBA a RGB si es necesario
        if img.mode in ('RGBA', 'P', 'LA'):
            fondo = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            fondo.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
            img = fondo
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar si es muy grande
        ratio = min(max_ancho / img.width, max_alto / img.height)
        if ratio < 1:
            nuevo_ancho = int(img.width * ratio)
            nuevo_alto = int(img.height * ratio)
            img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        
        # Guardar como JPG temporal
        temp_path = ruta_img + "_temp_catalog.jpg"
        img.save(temp_path, "JPEG", quality=85)
        return temp_path
    except Exception as e:
        print(f"  ⚠️ Error procesando imagen: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# CLASE PDF PERSONALIZADA
# ═══════════════════════════════════════════════════════════

def limpiar_texto(texto):
    reemplazos = {'\u014d': 'o', '\u016b': 'u', '\u00fc': 'u', '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"', '\u2013': '-', '\u2014': '-', '\u2026': '...'}
    for orig, reemplazo in reemplazos.items():
        texto = texto.replace(orig, reemplazo)
    return texto


class CatalogoPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font('Arial', '', r'C:\Windows\Fonts\arial.ttf', uni=True)
        self.add_font('Arial', 'B', r'C:\Windows\Fonts\arialbd.ttf', uni=True)
        self.add_font('Arial', 'I', r'C:\Windows\Fonts\ariali.ttf', uni=True)
    
    def header(self):
        """Cabecera de cada página."""
        # Línea dorada superior
        self.set_fill_color(*COLOR_DORADO)
        self.rect(0, 0, 210, 3, 'F')
        
    def footer(self):
        """Pie de cada página."""
        self.set_y(-12)
        self.set_font("Arial", "I", 8)
        self.set_text_color(*COLOR_GRIS_CLARO)
        self.cell(0, 10, f"Rojo Malbec · Los Hornillos, Traslasierra · Pág. {self.page_no()}", 0, 0, "C")
    
    def portada(self, logo_path):
        """Genera la portada del catálogo."""
        self.add_page()
        
        # Fondo vino
        self.set_fill_color(*COLOR_VINO)
        self.rect(0, 0, 210, 297, 'F')
        
        # Línea dorada superior gruesa
        self.set_fill_color(*COLOR_DORADO)
        self.rect(0, 0, 210, 5, 'F')
        
        # Logo
        if logo_path and os.path.exists(logo_path):
            temp_logo = preparar_imagen(logo_path, 300, 300)
            if temp_logo:
                self.image(temp_logo, x=55, y=40, w=100)
                os.remove(temp_logo)
        
        # Título
        self.set_y(160)
        self.set_font("Arial", "B", 32)
        self.set_text_color(*COLOR_DORADO)
        self.cell(0, 15, "Lista de Precios", 0, 1, "C")
        
        self.set_font("Arial", "", 16)
        self.set_text_color(*COLOR_BLANCO)
        self.cell(0, 10, "Sales & Blends de Especias y Tés", 0, 1, "C")
        
        # Línea decorativa
        self.set_y(195)
        self.set_fill_color(*COLOR_DORADO)
        self.rect(60, 195, 90, 0.5, 'F')
        
        # Fecha
        self.set_y(205)
        self.set_font("Arial", "I", 12)
        self.set_text_color(*COLOR_GRIS_CLARO)
        fecha = datetime.now().strftime("%d de %B de %Y")
        # Traducir meses al español
        meses = {"January": "Enero", "February": "Febrero", "March": "Marzo", 
                 "April": "Abril", "May": "Mayo", "June": "Junio",
                 "July": "Julio", "August": "Agosto", "September": "Septiembre",
                 "October": "Octubre", "November": "Noviembre", "December": "Diciembre"}
        for eng, esp in meses.items():
            fecha = fecha.replace(eng, esp)
        self.cell(0, 10, fecha, 0, 1, "C")
        
        # Línea dorada inferior
        self.set_fill_color(*COLOR_DORADO)
        self.rect(0, 292, 210, 5, 'F')
    
    def agregar_producto(self, nombre, precio_may, pvp, descripcion, foto_path):
        """Agrega un producto al catálogo con foto y descripción."""
        
        # Calcular espacio necesario (estimado)
        espacio_necesario = 90  # mínimo
        if self.get_y() + espacio_necesario > 270:
            self.add_page()
        
        y_inicio = self.get_y() + 5
        
        # ── FOTO (lado izquierdo) ──
        foto_ancho = 75
        foto_alto = 75
        foto_x = 10
        
        temp_img = None
        if foto_path and os.path.exists(foto_path):
            temp_img = preparar_imagen(foto_path, 500, 500)
            if temp_img:
                try:
                    self.image(temp_img, x=foto_x, y=y_inicio, w=foto_ancho, h=foto_alto)
                except:
                    temp_img = None
        
        # ── TEXTO (lado derecho) ──
        texto_x = 90
        texto_ancho = 110
        
        # Nombre del producto
        self.set_xy(texto_x, y_inicio)
        self.set_font("Arial", "B", 13)
        self.set_text_color(*COLOR_VINO)
        self.cell(texto_ancho, 7, limpiar_texto(nombre), 0, 1)
        
        # Línea dorada bajo el nombre
        self.set_fill_color(*COLOR_DORADO)
        self.rect(texto_x, self.get_y(), 50, 0.5, 'F')
        self.ln(3)
        
        # Descripción (recortada para que entre)
        if descripcion:
            self.set_x(texto_x)
            self.set_font("Arial", "", 8)
            self.set_text_color(*COLOR_GRIS_OSCURO)
            
            # Limpiar markdown
            desc_limpia = descripcion.replace("**", "").replace("*", "")
            # Tomar todas las líneas de la descripción
            lineas_desc = desc_limpia.split("\n")
            texto_corto = []
            for linea in lineas_desc:
                if linea.strip():
                    texto_corto.append(linea.strip())
            
            desc_final = " ".join(texto_corto)
            
            self.set_x(texto_x)
            self.multi_cell(texto_ancho, 4, limpiar_texto(desc_final))
        
        # ── PRECIOS ──
        precio_y = max(self.get_y() + 3, y_inicio + 60)
        
        # Fondo gris para precios
        self.set_fill_color(*COLOR_FONDO_PRECIO)
        self.rect(texto_x, precio_y, texto_ancho, 12, 'F')
        
        # Precio mayorista
        self.set_xy(texto_x + 2, precio_y + 2)
        self.set_font("Arial", "", 8)
        self.set_text_color(*COLOR_GRIS_CLARO)
        self.cell(50, 4, f"Precio Mayorista: $ {precio_may:,}", 0, 0)
        
        # PVP sugerido
        self.set_font("Arial", "B", 9)
        self.set_text_color(*COLOR_VINO)
        self.cell(55, 4, f"PVP Sugerido: $ {pvp:,}", 0, 0, "R")
        
        # Mover Y al final del producto
        final_y = max(precio_y + 15, y_inicio + foto_alto + 5)
        self.set_y(final_y)
        
        # Línea separadora
        self.set_draw_color(220, 220, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        
        # Limpiar imagen temporal
        if temp_img and os.path.exists(temp_img):
            try:
                os.remove(temp_img)
            except:
                pass


# ═══════════════════════════════════════════════════════════
# EJECUCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🍷 GENERADOR DE CATÁLOGO PDF - ROJO MALBEC")
    print("=" * 60)
    print()
    
    # 1. Cargar datos
    productos = cargar_datos_gsheets()
    descripciones = cargar_descripciones()
    
    if not productos:
        print("❌ No hay productos para generar el catálogo.")
        return
    
    # 2. Crear PDF
    print("\n📄 Generando PDF...")
    pdf = CatalogoPDF()
    
    # Portada
    pdf.portada(LOGO_PATH)
    
    # Agrupar productos
    categorias_dict = {}
    for prod in productos:
        cat = detectar_categoria(prod["nombre"])
        if cat not in categorias_dict:
            categorias_dict[cat] = []
        categorias_dict[cat].append(prod)

    orden_categorias = ["Sales Gourmet", "Blends Especiados", "Línea Vital", "Pimientas de Autor", "Mocktails", "Tés de Autor"]
    
    para_imprimir = []
    for c in orden_categorias:
        if c in categorias_dict:
            para_imprimir.append(c)
    for c in categorias_dict.keys():
        if c not in para_imprimir:
            para_imprimir.append(c)
            
    # Agregar cada categoría
    for cat_name in para_imprimir:
        lista_cat = categorias_dict[cat_name]
        print(f"📌 Agregando categoría: {cat_name} ({len(lista_cat)} productos)")
        
        # Título de Categoría en nueva página
        pdf.add_page()
        pdf.set_font("Arial", "B", 22)
        pdf.set_text_color(*COLOR_VINO)
        pdf.cell(0, 15, cat_name.upper(), 0, 1, "C")
        pdf.set_fill_color(*COLOR_DORADO)
        pdf.rect(60, pdf.get_y(), 90, 0.8, 'F')
        pdf.ln(12)
        
        for i, prod in enumerate(lista_cat):
            nombre = prod["nombre"]
            print(f"  📦 {nombre}")
            
            # Buscar descripción
            desc = buscar_descripcion(nombre, descripciones)
            
            # Buscar foto
            foto = buscar_foto(nombre)
            
            pdf.agregar_producto(
                nombre=nombre,
                precio_may=prod["precio_mayorista"],
                pvp=prod["pvp_sugerido"],
                descripcion=desc,
                foto_path=foto
            )
    
    # 3. Guardar
    pdf.output(OUTPUT_PDF)
    print(f"\n{'=' * 60}")
    print(f"✅ ¡CATÁLOGO GENERADO EXITOSAMENTE!")
    print(f"📂 Guardado en: {OUTPUT_PDF}")
    print(f"📊 Total productos: {len(productos)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

