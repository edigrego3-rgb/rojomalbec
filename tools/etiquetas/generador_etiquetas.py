import math
import textwrap
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ARABESCO_PATH = os.path.join(ASSETS_DIR, "arabesco_victoriano.png")

def render_curved_text_top(base_img, text, font, radius=405, center_x=512, center_y=512, letter_spacing=1.3, fill="black"):
    """Dibuja texto siguiendo un arco circular en la parte superior."""
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    
    char_widths = []
    char_images = []
    
    for char in text:
        bbox = dummy_draw.textbbox((0, 0), char, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        char_widths.append(max(w, 8))
        
        cw = max(w + 14, 24)
        ch = max(h + 14, 24)
        cimg = Image.new("RGBA", (cw, ch), (255, 255, 255, 0))
        cdraw = ImageDraw.Draw(cimg)
        cdraw.text((7 - bbox[0], 7 - bbox[1]), char, font=font, fill=fill)
        char_images.append((cimg, w, h))

    angles = [(w * letter_spacing) / radius for w in char_widths]
    total_angle = sum(angles)
    current_angle = -math.pi / 2 - (total_angle / 2)
    
    for i, (cimg, w, h) in enumerate(char_images):
        ang_step = angles[i]
        mid_angle = current_angle + (ang_step / 2)
        cx = center_x + radius * math.cos(mid_angle)
        cy = center_y + radius * math.sin(mid_angle)
        
        rot_deg = math.degrees(mid_angle + math.pi / 2)
        rotated = cimg.rotate(-rot_deg, resample=Image.BICUBIC, expand=True)
        rw, rh = rotated.size
        
        px = int(cx - rw / 2)
        py = int(cy - rh / 2)
        base_img.paste(rotated, (px, py), rotated)
        current_angle += ang_step

def generar_etiqueta_trasera_oficial(
    nombre_producto="SAL AL MALBEC & TÉ AHUMADO",
    subtitulo="(Lapsang Souchong)",
    ingredientes_lineas=None,
    sugerencias_texto="Cortes vacunos a la parrilla, guisados de olla, cordero, vegetales al rescoldo, mantecas compuestas.",
    modo_uso_texto="Aplicar sobre carnes crudas 20 min antes del fuego o durante el sellado a fuego vivo. Sal de cocción.",
    leyenda_sal="Sal Marina entrefina enriquecida para uso alimentario según ley N 17259",
    output_path=None
):
    size = 1024
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    
    # 1. DOS ANILLOS CONCÉNTRICOS EXACTOS
    m1 = 20
    draw.ellipse([m1, m1, size - m1, size - m1], outline="black", width=5)
    m2 = 36
    draw.ellipse([m2, m2, size - m2, size - m2], outline="black", width=9)

    # 2. TIPOGRAFÍAS DE WINDOWS
    font_arco = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 36)
    font_ing_title = ImageFont.truetype("C:\\Windows\\Fonts\\ARIALNB.TTF", 30)
    font_ing_body = ImageFont.truetype("C:\\Windows\\Fonts\\ARIALNB.TTF", 23)
    font_title_base = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 68)
    font_sub = ImageFont.truetype("C:\\Windows\\Fonts\\timesi.ttf", 38)
    font_block = ImageFont.truetype("C:\\Windows\\Fonts\\ARIALNB.TTF", 23)
    font_qr_title = ImageFont.truetype("C:\\Windows\\Fonts\\ARIALNB.TTF", 25)
    font_qr_body = ImageFont.truetype("C:\\Windows\\Fonts\\ARIALNB.TTF", 22)

    # 3. ARCO SUPERIOR
    render_curved_text_top(img, "PRODUCTO ARTESANAL · TRASLASIERRA", font_arco, radius=405, center_x=512, center_y=512, letter_spacing=1.3)

    def draw_centered(y, text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        x = (size - w) // 2
        draw.text((x, y), text, font=font, fill="black")
        return bbox[3] - bbox[1]

    # 4. INGREDIENTES
    cur_y = 166
    h = draw_centered(cur_y, "INGREDIENTES:", font_ing_title)
    cur_y += h + 8

    if not ingredientes_lineas:
        ingredientes_lineas = [
            "Sal marina al Malbec · Té negro",
            "Lapsang Souchong · Puerro · Hongo de pino",
            "patagónico · Pimienta larga · Tallo de shiitake"
        ]

    for line in ingredientes_lineas:
        h = draw_centered(cur_y, line, font_ing_body)
        cur_y += h + 5

    if leyenda_sal:
        h = draw_centered(cur_y, leyenda_sal, font_ing_body)
        cur_y += h + 5

    # 5. ARABESCO SUPERIOR
    if os.path.exists(ARABESCO_PATH):
        arab = Image.open(ARABESCO_PATH).convert("RGBA")
        aw, ah = arab.size
        target_w = 390
        target_h = int(ah * (target_w / aw))
        arab_resized = arab.resize((target_w, target_h), Image.Resampling.LANCZOS)
        ax = (size - target_w) // 2
        ay = cur_y + 12
        img.paste(arab_resized, (ax, ay), arab_resized)
        cur_y = ay + target_h + 16

    # 6. TÍTULO EN UNA LÍNEA (CONDENSADO AL 73%)
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    t_bb = dummy_draw.textbbox((0, 0), nombre_producto, font=font_title_base)
    tw = t_bb[2] - t_bb[0]
    th = t_bb[3] - t_bb[1]

    t_strip = Image.new("RGBA", (tw + 20, th + 20), (255, 255, 255, 0))
    t_draw = ImageDraw.Draw(t_strip)
    t_draw.text((10 - t_bb[0], 10 - t_bb[1]), nombre_producto, font=font_title_base, fill="black")

    cond_w = int((tw + 20) * 0.73)
    cond_h = th + 20
    t_condensed = t_strip.resize((cond_w, cond_h), Image.Resampling.LANCZOS)
    tx = (size - cond_w) // 2
    img.paste(t_condensed, (tx, cur_y), t_condensed)
    cur_y += cond_h + 2

    # 7. SUBTÍTULO
    if subtitulo:
        h = draw_centered(cur_y, subtitulo, font_sub)
        cur_y += h + 14

    # 8. ARABESCO INFERIOR (invertido)
    if os.path.exists(ARABESCO_PATH):
        arab_inv = arab_resized.transpose(Image.FLIP_TOP_BOTTOM)
        img.paste(arab_inv, (ax, cur_y), arab_inv)
        cur_y += target_h + 24

    # 9. SUGERENCIAS + MODO DE USO
    bloque_texto = f"SUGERENCIAS: {sugerencias_texto} MODO DE USO: {modo_uso_texto}"
    lineas_bloque = textwrap.wrap(bloque_texto, width=76)
    for l in lineas_bloque:
        h = draw_centered(cur_y, l, font_block)
        cur_y += h + 6

    # 10. QR + CONTACTO
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data("https://www.rojomalbec.com.ar")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_size = 114
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    t_lines = [
        ("Rojo Malbec Sales & Blends", font_qr_title),
        ("Los Hornillos, Córdoba", font_qr_body),
        ("Tel: 3544308380", font_qr_body),
        ("www.rojomalbec.com.ar", font_qr_body)
    ]
    
    t_width = max([draw.textbbox((0, 0), txt, font=fnt)[2] - draw.textbbox((0, 0), txt, font=fnt)[0] for txt, fnt in t_lines])
    spacing = 16
    total_block_w = qr_size + spacing + t_width
    start_block_x = (size - total_block_w) // 2
    
    qr_y = 808
    img.paste(qr_img, (start_block_x, qr_y))

    text_start_x = start_block_x + qr_size + spacing
    ty = qr_y + 4
    for txt, fnt in t_lines:
        draw.text((text_start_x, ty), txt, font=fnt, fill="black")
        bb = draw.textbbox((0, 0), txt, font=fnt)
        ty += (bb[3] - bb[1]) + 5

    if output_path:
        img.save(output_path, quality=98)
    return img
