import urllib.parse
import os

def redondear_precio(precio):
    return round(precio)

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

def generar_mensaje_whatsapp(carrito, total_costo, total_venta, telefono, datos_vendedor):
    """
    Genera el link de WhatsApp formateado específicamente para el preventista.
    """
    mensaje = "🛒 *NUEVO PEDIDO DE PREVENTA*\n"
    mensaje += "--------------------------------------\n"
    mensaje += f"👤 *Vendedor:* {datos_vendedor.get('nombre_vendedor', 'No especificado')}\n"
    mensaje += f"🏢 *Para entregar a:* {datos_vendedor.get('cliente_final', 'No especificado')}\n"
    
    if datos_vendedor.get('direccion'):
        mensaje += f"📍 *Dirección:* {datos_vendedor['direccion']}\n"
    if datos_vendedor.get('cuit'):
        mensaje += f"📄 *CUIT:* {datos_vendedor['cuit']}\n"
        
    mensaje += "--------------------------------------\n"
    mensaje += "*PRODUCTOS SOLICITADOS:*\n"
    
    for item in carrito:
        # Mostramos la cantidad y el nombre
        mensaje += f"• {item['cantidad']}x {item['nombre']}\n"
        # Opcional: mostrar a qué precio lo cerró con el cliente
        mensaje += f"  (Vendidos a ${item['precio_venta']:,} c/u)\n"
        
    mensaje += "--------------------------------------\n"
    mensaje += "💰 *RESUMEN FINANCIERO:*\n"
    mensaje += f"💸 *A transferir a Rojo Malbec (Costo):* $ {total_costo:,}\n"
    mensaje += f"🏷️ *Total Venta a Cliente:* $ {total_venta:,}\n"
    ganancia = total_venta - total_costo
    mensaje += f"📈 *(Ganancia Vendedor):* $ {ganancia:,}\n"
    
    mensaje_codificado = urllib.parse.quote(mensaje)
    return f"https://wa.me/{telefono}?text={mensaje_codificado}"
