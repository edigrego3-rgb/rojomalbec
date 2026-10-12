import urllib.parse
import math
import os
import re

def redondear_precio(valor):
    """Redondea hacia arriba a los 100 pesos más cercanos"""
    if valor <= 0:
        return 0
    return math.ceil(valor / 100.0) * 100

def extraer_descripcion(nombre_blend, filepath="Descripciones_RojoMalbec.md"):
    if not os.path.exists(filepath):
        return "Descripción no disponible."
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenido = f.read()
            
        nombre_buscar = nombre_blend.lower().replace("blend ", "").replace("vital ", "").replace("-", " ").strip()
        
        if "mole" in nombre_buscar: nombre_buscar = "mole"
        elif "quatre" in nombre_buscar or "epices" in nombre_buscar or "especies" in nombre_buscar: nombre_buscar = "quatre"
        elif "karak" in nombre_buscar: nombre_buscar = "karak"
        elif "pu erh" in nombre_buscar: nombre_buscar = "pu erh"
        elif "zoco" in nombre_buscar: nombre_buscar = "zoco"
        elif "rooibos" in nombre_buscar: nombre_buscar = "rooibos"
        elif "limon" in nombre_buscar and "chile" in nombre_buscar: nombre_buscar = "lim"
        elif "espa" in nombre_buscar and "profunda" in nombre_buscar: nombre_buscar = "profunda"
        elif "malbec" in nombre_buscar: nombre_buscar = "sal al malbec"
        elif "british" in nombre_buscar: nombre_buscar = "sal british"
        elif "desierto" in nombre_buscar: nombre_buscar = "sal del desierto"
        elif "hawaiana" in nombre_buscar: nombre_buscar = "sal negra"
        elif "svanetian" in nombre_buscar: nombre_buscar = "esvanetian"
        elif "burger" in nombre_buscar: nombre_buscar = "blend burger"
        elif "kebab" in nombre_buscar: nombre_buscar = "blend kebab"
        elif "barbacoa" in nombre_buscar or "bbq" in nombre_buscar: nombre_buscar = "bbq"
        elif "sloppy" in nombre_buscar or "sloopy" in nombre_buscar: nombre_buscar = "sloopy joe"
        elif "jerk" in nombre_buscar: nombre_buscar = "jerk"
        elif "nanami" in nombre_buscar: nombre_buscar = "nanami"
        elif "criolla" in nombre_buscar: nombre_buscar = "criolla"
        elif "panko" in nombre_buscar or "sesamo" in nombre_buscar: nombre_buscar = "crocante de panko"
        elif "gluhwein" in nombre_buscar or "glühwein" in nombre_buscar: nombre_buscar = "gluhwein"
        elif "pimienta negra" in nombre_buscar: nombre_buscar = "pimienta negra"
        elif "pimienta roja" in nombre_buscar: nombre_buscar = "pimienta roja"
        elif "honey" in nombre_buscar: nombre_buscar = "dry hot honey"
        elif "vikinga" in nombre_buscar: nombre_buscar = "vikinga"
        
        bloques = contenido.split("## ")
        for bloque in bloques:
            if not bloque.strip(): continue
            lineas = bloque.split("\n")
            header = lineas[0].lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ñ','n')
            nombre_buscar = nombre_buscar.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ñ','n')
            
            if nombre_buscar in header:
                descripcion_sucia = "\n".join(lineas[1:]).strip()
                if descripcion_sucia:
                    lineas_limpias = [l.strip() for l in descripcion_sucia.split('\n') if l.strip() and not l.startswith('---') and not l.startswith('|') and not l.startswith('#') and not l.startswith('═')]
                    texto_final = ""
                    for d in lineas_limpias:
                        d_clean = d.replace("**", "")
                        if d_clean.startswith('* Ingredientes:') or d_clean.startswith('Ingredientes:'):
                            texto_final += f"🥣 {d_clean.replace('* Ingredientes:', 'Ingredientes:')}\n"
                        elif d_clean.startswith('* Ideal para:') or d_clean.startswith('Ideal para:') or d_clean.startswith('Usos:'):
                            texto_final += f"🍽️ {d_clean.replace('* Ideal para:', 'Ideal para:')}\n"
                        elif d_clean.startswith('* Técnica:') or d_clean.startswith('Técnica:'):
                            texto_final += f"🔪 {d_clean}\n"
                        elif d_clean.startswith('* Modo') or d_clean.startswith('Modo'):
                            texto_final += f"✨ {d_clean.replace('* Modo', 'Modo')}\n"
                        elif d_clean.startswith('* '):
                            texto_final += f"• {d_clean[2:]}\n"
                        else:
                            texto_final += f"{d_clean}\n\n"
                    resultado = texto_final.strip()
                    if resultado: return resultado
    except Exception as e:
        pass
        
    return "Una creación premium de Rojo Malbec."

def generar_mensaje_whatsapp(carrito, total_pedido, telefono, datos_cliente):
    """
    Genera el link de WhatsApp con el pedido formateado.
    """
    nombre_local = datos_cliente.get("nombre", "Cliente B2B")
    cuit = datos_cliente.get("cuit", "")
    direccion = datos_cliente.get("direccion", "")
    
    texto = f"🌟 *NUEVO PEDIDO ROJO MALBEC* 🌟\n"
    texto += f"🏠 Local: {nombre_local}\n"
    if cuit: texto += f"📋 CUIT: {cuit}\n"
    if direccion: texto += f"📍 Envío: {direccion}\n"
    texto += "\n*DETALLE DEL PEDIDO:*\n"
    
    for item in carrito:
        texto += f"▪️ {item['cantidad']}x {item['nombre']} ($ {item['subtotal']:,})\n"
        
    texto += f"\n💰 *TOTAL A ABONAR:* $ {total_pedido:,}\n"
    texto += "\n_Aguardamos confirmación y datos de transferencia. ¡Gracias!_"
    
    texto_codificado = urllib.parse.quote(texto)
    # Asegurar formato internacional del teléfono (remover + si existe)
    tel_limpio = telefono.replace("+", "").replace(" ", "")
    
    return f"https://wa.me/{tel_limpio}?text={texto_codificado}"
