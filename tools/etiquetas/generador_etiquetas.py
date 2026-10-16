import math
import textwrap
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

def render_curved_text_top(base_img, text, font, radius=392, center_x=500, center_y=500, letter_spacing=1.2, fill="black"):
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

def render_curved_text_bottom(base_img, text, font, radius=420, center_x=500, center_y=500, letter_spacing=1.1, fill="black"):
    """Dibuja texto siguiendo un arco circular en la parte inferior (ej: IND. ARG. 100g)."""
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
    current_angle = math.pi / 2 - (total_angle / 2)
    
    for i, (cimg, w, h) in enumerate(char_images):
        ang_step = angles[i]
        mid_angle = current_angle + (ang_step / 2)
        cx = center_x + radius * math.cos(mid_angle)
        cy = center_y + radius * math.sin(mid_angle)
        
        rot_deg = math.degrees(mid_angle - math.pi / 2)
        rotated = cimg.rotate(-rot_deg, resample=Image.BICUBIC, expand=True)
        rw, rh = rotated.size
        
        px = int(cx - rw / 2)
        py = int(cy - rh / 2)
        base_img.paste(rotated, (px, py), rotated)
        current_angle += ang_step

def draw_filigree_divider(draw, cx, cy, width=290):
    """Filete ornamental victoriano simétrico con hojas y volutas."""
    half_w = width // 2
    draw.line([(cx - half_w, cy), (cx - 40, cy)], fill="black", width=2)
    draw.line([(cx + 40, cy), (cx + half_w, cy)], fill="black", width=2)
    draw.line([(cx - half_w, cy - 3), (cx - half_w, cy + 3)], fill="black", width=2)
    draw.line([(cx + half_w, cy - 3), (cx + half_w, cy + 3)], fill="black", width=2)
    
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill="black")
    draw.arc([cx - 28, cy - 13, cx - 2, cy + 3], start=180, end=360, fill="black", width=2)
    draw.arc([cx + 2, cy - 13, cx + 28, cy + 3], start=180, end=360, fill="black", width=2)
    draw.arc([cx - 28, cy - 3, cx - 2, cy + 13], start=0, end=180, fill="black", width=2)
    draw.arc([cx + 2, cy - 3, cx + 28, cy + 13], start=0, end=180, fill="black", width=2)
    draw.ellipse([cx - 36, cy - 3, cx - 30, cy + 3], fill="black")
    draw.ellipse([cx + 30, cy - 3, cx + 36, cy + 3], fill="black")

def draw_hecho_a_mano_stamp(base_img, x, y, size=130):
    """Dibuja el sello artesanal circular HECHO A MANO."""
    stamp = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    sdraw = ImageDraw.Draw(stamp)
    sdraw.ellipse([4, 4, size - 4, size - 4], outline="black", width=4)
    sdraw.ellipse([10, 10, size - 10, size - 10], outline="black", width=2)
    
    try:
        font_s = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 20)
    except:
        font_s = ImageFont.load_default()
        
    bb1 = sdraw.textbbox((0, 0), "HECHO", font=font_s)
    w1 = bb1[2] - bb1[0]
    sdraw.text(((size - w1) // 2, 38), "HECHO", font=font_s, fill="black")
    
    bb2 = sdraw.textbbox((0, 0), "A MANO", font=font_s)
    w2 = bb2[2] - bb2[0]
    sdraw.text(((size - w2) // 2, 64), "A MANO", font=font_s, fill="black")
    
    rotated_stamp = stamp.rotate(8, resample=Image.BICUBIC, expand=True)
    base_img.paste(rotated_stamp, (x, y), rotated_stamp)

def generar_etiqueta_trasera_oficial(
    nombre_linea_1,
    nombre_linea_2,
    subtitulo,
    ingredientes_texto,
    sugerencias_texto,
    modo_uso_texto,
    es_sal=True,
    output_path=None
):
    size = 1000
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    
    # 2 aros concéntricos negros
    m1 = 20
    draw.ellipse([m1, m1, size - m1, size - m1], outline="black", width=5)
    m2 = 36
    draw.ellipse([m2, m2, size - m2, size - m2], outline="black", width=8)

    try:
        font_arco = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 32)
        font_ing_title = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 27)
        font_ing_body = ImageFont.truetype("C:\\Windows\\Fonts\\times.ttf", 23)
        font_name = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 46)
        font_sub = ImageFont.truetype("C:\\Windows\\Fonts\\timesi.ttf", 30)
        font_bold_block = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 22)
        font_reg_block = ImageFont.truetype("C:\\Windows\\Fonts\\times.ttf", 22)
        font_ley = ImageFont.truetype("C:\\Windows\\Fonts\\times.ttf", 19)
        font_qr_title = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 23)
        font_qr_info = ImageFont.truetype("C:\\Windows\\Fonts\\times.ttf", 20)
    except:
        font_arco = font_ing_title = font_ing_body = font_name = font_sub = font_bold_block = font_reg_block = font_ley = font_qr_title = font_qr_info = ImageFont.load_default()

    # Arco superior
    render_curved_text_top(img, "PRODUCTO ARTESANAL · TRASLASIERRA", font_arco, radius=392, center_x=500, center_y=500, letter_spacing=1.2)

    def draw_centered_text(y, text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        x = (size - w) // 2
        draw.text((x, y), text, font=font, fill="black")
        return bbox[3] - bbox[1]

    # Ingredientes
    cur_y = 195
    h = draw_centered_text(cur_y, "INGREDIENTES:", font_ing_title)
    cur_y += h + 8

    ing_lines = textwrap.wrap(ingredientes_texto, width=54)
    for line in ing_lines:
        h = draw_centered_text(cur_y, line, font_ing_body)
        cur_y += h + 5

    # Separador 1
    cur_y += 12
    draw_filigree_divider(draw, 500, cur_y, width=290)
    cur_y += 20

    # Nombre
    if nombre_linea_2:
        h = draw_centered_text(cur_y, nombre_linea_1, font_name)
        cur_y += h + 4
        h = draw_centered_text(cur_y, nombre_linea_2, font_name)
        cur_y += h + 6
    else:
        h = draw_centered_text(cur_y, nombre_linea_1, font_name)
        cur_y += h + 6

    # Subtítulo
    if subtitulo:
        h = draw_centered_text(cur_y, subtitulo, font_sub)
        cur_y += h + 15

    # Separador 2
    draw_filigree_divider(draw, 500, cur_y, width=290)
    cur_y += 22

    # Sugerencias
    sug_full = f"SUGERENCIAS: {sugerencias_texto}"
    sug_lines = textwrap.wrap(sug_full, width=58)
    for line in sug_lines:
        if line.startswith("SUGERENCIAS:"):
            bold_part = "SUGERENCIAS: "
            reg_part = line[len(bold_part):]
            bb_b = draw.textbbox((0, 0), bold_part, font=font_bold_block)
            bb_r = draw.textbbox((0, 0), reg_part, font=font_reg_block)
            w_total = (bb_b[2] - bb_b[0]) + (bb_r[2] - bb_r[0])
            start_x = (size - w_total) // 2
            draw.text((start_x, cur_y), bold_part, font=font_bold_block, fill="black")
            draw.text((start_x + (bb_b[2] - bb_b[0]), cur_y), reg_part, font=font_reg_block, fill="black")
            cur_y += max(bb_b[3] - bb_b[1], bb_r[3] - bb_r[1]) + 4
        else:
            h = draw_centered_text(cur_y, line, font_reg_block)
            cur_y += h + 4

    cur_y += 6

    # Modo de uso
    modo_full = f"MODO DE USO: {modo_uso_texto}"
    modo_lines = textwrap.wrap(modo_full, width=58)
    for line in modo_lines:
        if line.startswith("MODO DE USO:"):
            bold_part = "MODO DE USO: "
            reg_part = line[len(bold_part):]
            bb_b = draw.textbbox((0, 0), bold_part, font=font_bold_block)
            bb_r = draw.textbbox((0, 0), reg_part, font=font_reg_block)
            w_total = (bb_b[2] - bb_b[0]) + (bb_r[2] - bb_r[0])
            start_x = (size - w_total) // 2
            draw.text((start_x, cur_y), bold_part, font=font_bold_block, fill="black")
            draw.text((start_x + (bb_b[2] - bb_b[0]), cur_y), reg_part, font=font_reg_block, fill="black")
            cur_y += max(bb_b[3] - bb_b[1], bb_r[3] - bb_r[1]) + 4
        else:
            h = draw_centered_text(cur_y, line, font_reg_block)
            cur_y += h + 4

    cur_y += 8

    # Leyenda sal
    if es_sal:
        h = draw_centered_text(cur_y, "Sal entrefina enriquecida para uso alimentario según Ley Nac. N°17259", font_ley)
        cur_y += h + 14
    else:
        cur_y += 10

    # QR + Datos
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data("https://www.rojomalbec.com.ar")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_size = 110
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    t_lines = [
        ("Rojo Malbec Sales & Blends", font_qr_title),
        ("Los Hornillos, Córdoba", font_qr_info),
        ("Tel: 3544308380", font_qr_info),
        ("www.rojomalbec.com.ar", font_qr_info)
    ]
    
    t_width = max([draw.textbbox((0, 0), txt, font=fnt)[2] - draw.textbbox((0, 0), txt, font=fnt)[0] for txt, fnt in t_lines])
    spacing = 18
    total_block_w = qr_size + spacing + t_width
    start_block_x = (size - total_block_w) // 2
    
    qr_y = 755
    img.paste(qr_img, (start_block_x, qr_y))

    text_start_x = start_block_x + qr_size + spacing
    ty = qr_y + 4
    for txt, fnt in t_lines:
        draw.text((text_start_x, ty), txt, font=fnt, fill="black")
        bb = draw.textbbox((0, 0), txt, font=fnt)
        ty += (bb[3] - bb[1]) + 5

    if output_path:
        img.save(output_path, quality=95)
    return img
