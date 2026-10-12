import textwrap
import os
from PIL import Image, ImageDraw, ImageFont

img_size = 1000
img = Image.new('RGB', (img_size, img_size), 'white')
draw = ImageDraw.Draw(img)

margin1 = 20
margin2 = 35
draw.ellipse([margin1, margin1, img_size-margin1, img_size-margin1], outline='black', width=8)
draw.ellipse([margin2, margin2, img_size-margin2, img_size-margin2], outline='black', width=3)

try:
    font_title = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 65)
    font_sub = ImageFont.truetype("C:\\Windows\\Fonts\\timesi.ttf", 45)
    font_bold = ImageFont.truetype("C:\\Windows\\Fonts\\timesbd.ttf", 30)
    font_text = ImageFont.truetype("C:\\Windows\\Fonts\\times.ttf", 28)
except:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_bold = ImageFont.load_default()
    font_text = ImageFont.load_default()

def draw_center(y, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((img_size - w) / 2, y), text, font=font, fill='black')

y = 110
draw_center(y, "PRODUCTO ARTESANAL • TRASLASIERRA", font_bold)

y += 70
draw_center(y, "INGREDIENTES:", font_bold)

ing = "Sal marina, mostaza rubia, estragón francés, ajedrea, ajo deshidratado, cebolla morada, tomillo, pimienta blanca, pimentón dulce (paprika), semilla de coriandro, laurel, semilla de apio."
y += 40
for line in textwrap.wrap(ing, width=55):
    draw_center(y, line, font_text)
    y += 35

y += 40
draw_center(y, "SAL POULET RÔTI", font_title)
y += 75
draw_center(y, "(El Clásico Francés)", font_sub)
y += 20
draw.line([(250, y), (750, y)], fill='black', width=2)
y += 40

draw_center(y, "SUGERENCIAS:", font_bold)
sug = "Pollo al horno, al spiedo, pechugas a la plancha, papas rústicas al horno, manteca compuesta."
y += 40
for line in textwrap.wrap(sug, width=60):
    draw_center(y, line, font_text)
    y += 35

y += 30
draw_center(y, "MODO DE USO:", font_bold)
uso = "Frotar sobre el ave entera (15g por kg) y dejar reposar 2hs antes de hornear. Conservar en lugar fresco, seco y oscuro."
y += 40
for line in textwrap.wrap(uso, width=60):
    draw_center(y, line, font_text)
    y += 35

y += 60
draw_center(y, "Sal entrefina para uso alimentario según Ley Nac. N°17259", font_text)

y += 60
draw_center(y, "Rojo Malbec Sales & Blends • Los Hornillos, Córdoba", font_bold)
y += 40
draw_center(y, "Tel: 3544308380 • www.rojomalbec.com.ar", font_text)

out_path = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Etiqueta_Trasera_TEXTO_EXACTO.png')
img.save(out_path)
print("CREADO EN:", out_path)
