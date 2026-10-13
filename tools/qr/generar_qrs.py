#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║        GENERADOR DE CÓDIGOS QR - ROJO MALBEC                 ║
║        Genera QR, imágenes y carteles para B2B y Preventa   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "salida")
LOGO_PATH = os.path.join(PROJECT_ROOT, "apps", "distribuidor", "logo.png")

os.makedirs(OUTPUT_DIR, exist_ok=True)

QR_CONFIGS = [
    {
        "id": "b2b",
        "url": "https://b2b.rojomalbec.com.ar",
        "titulo": "CATÁLOGO MAYORISTA / B2B",
        "subtitulo": "LISTA DE PRECIOS Y PEDIDOS",
        "bajada": "Escaneá con tu celular para ver productos y listas de precios",
        "file_base": "qr_b2b_distribuidor"
    },
    {
        "id": "preventa",
        "url": "https://preventa.rojomalbec.com.ar",
        "titulo": "PORTAL DE PREVENTA",
        "subtitulo": "PEDIDOS EXCLUSIVOS",
        "bajada": "Escaneá con tu celular para hacer tu reserva de preventa",
        "file_base": "qr_preventa"
    }
]

COLOR_VINO = (139, 0, 0)       # #8B0000
COLOR_DORADO = (212, 175, 55)   # #D4AF37
COLOR_OSCURO = (40, 40, 40)
COLOR_GRIS = (110, 110, 110)


def crear_qr_estandar(url, output_path):
    """Genera un QR de alta resolución clásico (blanco y negro)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=20,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img.save(output_path, quality=95)
    print(f"  [OK] Creado: {os.path.basename(output_path)}")
    return output_path


def crear_qr_con_logo(url, logo_path, output_path):
    """Genera un QR con logo central integrado y corrección de error alta (H)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=20,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        
        # Tamaño del logo central: ~23% del ancho del QR
        qr_w, qr_h = qr_img.size
        logo_size = int(qr_w * 0.23)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

        padding = 16
        badge_size = logo_size + padding * 2
        badge = Image.new("RGBA", (badge_size, badge_size), (255, 255, 255, 255))
        badge.paste(logo, (padding, padding), mask=logo if "A" in logo.getbands() else None)

        pos = ((qr_w - badge_size) // 2, (qr_h - badge_size) // 2)
        qr_img.paste(badge, pos)

    qr_final = qr_img.convert("RGB")
    qr_final.save(output_path, quality=95)
    print(f"  [OK] Creado con logo: {os.path.basename(output_path)}")
    return output_path


def generar_ficha_pdf(cfg, qr_img_path, output_pdf_path):
    """Genera una ficha A4 lista para imprimir o poner en un cartel/mostrador."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    # Margen decorativo
    pdf.set_draw_color(*COLOR_VINO)
    pdf.set_line_width(1.5)
    pdf.rect(10, 10, 190, 277)

    pdf.set_draw_color(*COLOR_DORADO)
    pdf.set_line_width(0.5)
    pdf.rect(13, 13, 184, 271)

    # Logo superior
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=(210 - 46) / 2, y=22, w=46)

    # Título marca
    pdf.set_y(70)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*COLOR_VINO)
    pdf.cell(0, 10, "ROJO MALBEC", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*COLOR_DORADO)
    pdf.cell(0, 6, "ESPECIAS - BLENDS - SALES GOURMET", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Línea divisoria
    pdf.ln(3)
    pdf.set_draw_color(*COLOR_DORADO)
    pdf.set_line_width(0.4)
    pdf.line(40, pdf.get_y(), 170, pdf.get_y())
    pdf.ln(8)

    # Título de sección (B2B o Preventa)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*COLOR_OSCURO)
    pdf.cell(0, 8, cfg["titulo"].encode("latin-1", "replace").decode("latin-1"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Bajada
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, cfg["bajada"].encode("latin-1", "replace").decode("latin-1"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # QR Central
    pdf.ln(5)
    qr_w = 95
    qr_x = (210 - qr_w) / 2
    qr_y = pdf.get_y()
    pdf.image(qr_img_path, x=qr_x, y=qr_y, w=qr_w)

    # Enlace escrito al pie
    pdf.set_y(qr_y + qr_w + 8)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*COLOR_VINO)
    link_texto = cfg["url"].replace("https://", "")
    pdf.cell(0, 8, link_texto, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 120)
    pie = "Abri la camara de tu celular y apunta al codigo QR"
    pdf.cell(0, 5, pie, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(output_pdf_path)
    print(f"  [OK] Ficha PDF para imprimir: {os.path.basename(output_pdf_path)}")


def generar_cartel_imagen(cfg, qr_img_path, output_img_path):
    """Genera una imagen vertical (1080x1500) con texto y diseño para WhatsApp o redes."""
    ancho, alto = 1080, 1500
    lienzo = Image.new("RGB", (ancho, alto), (255, 255, 255))
    draw = ImageDraw.Draw(lienzo)

    # Marcos
    draw.rectangle([25, 25, ancho - 25, alto - 25], outline=COLOR_VINO, width=6)
    draw.rectangle([35, 35, ancho - 35, alto - 35], outline=COLOR_DORADO, width=2)

    # Fuentes
    try:
        font_marca = ImageFont.truetype("arialbd.ttf", 46)
        font_sub = ImageFont.truetype("arialbd.ttf", 22)
        font_titulo = ImageFont.truetype("arialbd.ttf", 36)
        font_bajada = ImageFont.truetype("arial.ttf", 24)
        font_url = ImageFont.truetype("arialbd.ttf", 32)
        font_tip = ImageFont.truetype("ariali.ttf", 20)
    except Exception:
        font_marca = ImageFont.load_default()
        font_sub = font_marca
        font_titulo = font_marca
        font_bajada = font_marca
        font_url = font_marca
        font_tip = font_marca

    # Logo Rojo Malbec
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.resize((170, 170), Image.Resampling.LANCZOS)
        lienzo.paste(logo, ((ancho - 170) // 2, 60), mask=logo if "A" in logo.getbands() else None)

    # Marca
    draw.text((ancho // 2, 255), "ROJO MALBEC", fill=COLOR_VINO, font=font_marca, anchor="mm")
    draw.text((ancho // 2, 295), "ESPECIAS · BLENDS · SALES GOURMET", fill=COLOR_DORADO, font=font_sub, anchor="mm")

    # Separador
    draw.line([(200, 325), (ancho - 200, 325)], fill=COLOR_DORADO, width=2)

    # Título y Bajada
    draw.text((ancho // 2, 375), cfg["titulo"], fill=COLOR_OSCURO, font=font_titulo, anchor="mm")
    draw.text((ancho // 2, 420), cfg["bajada"], fill=COLOR_GRIS, font=font_bajada, anchor="mm")

    # QR
    qr = Image.open(qr_img_path).convert("RGB")
    qr = qr.resize((620, 620), Image.Resampling.LANCZOS)
    lienzo.paste(qr, ((ancho - 620) // 2, 480))

    # URL y Ayuda
    draw.text((ancho // 2, 1160), cfg["url"].replace("https://", ""), fill=COLOR_VINO, font=font_url, anchor="mm")
    draw.text((ancho // 2, 1205), "Abrí la cámara de tu celular y apuntá al código QR", fill=COLOR_GRIS, font=font_tip, anchor="mm")

    lienzo.save(output_img_path, quality=95)
    print(f"  [OK] Cartel PNG para WhatsApp/Redes: {os.path.basename(output_img_path)}")


def main():
    print("=" * 60)
    print(" GENERADOR DE CODIGOS QR - ROJO MALBEC")
    print("=" * 60)
    print(f"Carpeta de salida: {OUTPUT_DIR}\n")

    for cfg in QR_CONFIGS:
        print(f"--> Procesando: {cfg['titulo']} ({cfg['url']})")
        
        # 1. QR estándar limpio
        path_std = os.path.join(OUTPUT_DIR, f"{cfg['file_base']}.png")
        crear_qr_estandar(cfg["url"], path_std)

        # 2. QR con Logo
        path_logo = os.path.join(OUTPUT_DIR, f"{cfg['file_base']}_con_logo.png")
        crear_qr_con_logo(cfg["url"], LOGO_PATH, path_logo)

        # 3. Cartel A4 imprimible en PDF
        path_pdf = os.path.join(OUTPUT_DIR, f"Cartel_{cfg['file_base'].upper()}.pdf")
        generar_ficha_pdf(cfg, path_logo, path_pdf)

        # 4. Cartel PNG para WhatsApp/Redes
        path_cartel_png = os.path.join(OUTPUT_DIR, f"Cartel_{cfg['file_base'].upper()}.png")
        generar_cartel_imagen(cfg, path_logo, path_cartel_png)

        print("-" * 60)

    print("\nTodos los codigos QR y carteles fueron generados con exito.")


if __name__ == "__main__":
    main()
