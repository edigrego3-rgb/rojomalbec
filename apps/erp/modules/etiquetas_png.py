import os
import io
from PIL import Image, ImageDraw, ImageFont

def generar_etiqueta_lote_png(rne_rnpa="RNE: 04006325 - RNPA E/T.", lote="L SLCH-260807", elab="07/2026", vto="07/2027", width=600, height=280):
    """
    Genera una etiqueta de lote individual en formato PNG lista para impresora inkjet.
    """
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_path = 'C:/Windows/Fonts/arialbd.ttf'
    if not os.path.exists(font_path):
        font_path = 'C:/Windows/Fonts/arial.ttf'

    try:
        font = ImageFont.truetype(font_path, 28)
    except Exception:
        font = ImageFont.load_default()

    lote_clean = lote.strip()
    if not lote_clean.upper().startswith("LOTE:"):
        lote_clean = f"LOTE: {lote_clean}"

    elab_clean = elab.strip()
    if not elab_clean.lower().startswith("elab:"):
        elab_clean = f"Elab: {elab_clean}"

    vto_clean = vto.strip()
    if not vto_clean.lower().startswith("vto"):
        vto_clean = f"Vto.: {vto_clean}"

    lines = [
        rne_rnpa.strip(),
        lote_clean,
        elab_clean,
        vto_clean
    ]

    x, y = 20, 20
    line_spacing = 14

    for line in lines:
        draw.text((x, y), line, fill=(0, 0, 0), font=font)
        bbox = font.getbbox(line) if hasattr(font, 'getbbox') else (0, 0, 200, 28)
        h = bbox[3] - bbox[1]
        y += h + line_spacing

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()
