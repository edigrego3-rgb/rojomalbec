---
name: etiquetas-gourmet
description: Guía y generador automatizado de etiquetas circulares frontales y traseras de autor para frascos y productos de Rojo Malbec según normativa visual y legal de la marca.
---

# Skill: Diseño y Generación de Etiquetas Gourmet – Rojo Malbec

Este skill estandariza la producción gráfica de etiquetas circulares (frontales y traseras) para tapas y frascos de Rojo Malbec en Los Hornillos, Traslasierra, Córdoba.

---

## 1. Identidad Visual y Estándar Geométrico

- **Formato:** Círculo perfecto de **1000 x 1000 px** (apto para impresión a 300 DPI).
- **Fondo:** **Blanco puro (`#FFFFFF`)** sobre papel adhesivo o vinilo blanco.
- **Marco Exterior:** Doble anillo concéntrico negro pleno:
  - Anillo 1 (exterior): Margen `20 px`, grosor `5 px`.
  - Anillo 2 (interior): Margen `36 px`, grosor `8 px`.
- **Tipografías estándar de Windows:**
  - Principal / Títulos: *Times New Roman Bold* (`C:\Windows\Fonts\timesbd.ttf`).
  - Subtítulos / Bajadas: *Times New Roman Italic* (`C:\Windows\Fonts\timesi.ttf`).
  - Textos descriptivos / Legales: *Times New Roman Regular* (`C:\Windows\Fonts\times.ttf`).

---

## 2. Anatomía de la Etiqueta Trasera

1. **Arco Curvo Superior:**  
   `PRODUCTO ARTESANAL · TRASLASIERRA` (Radio 392 px, letra curvada en arco de 180°).
2. **Bloque Ingredientes:**  
   `INGREDIENTES:` en negrita.  
   Lista de botánicos separados por puntos medios (`·`), en orden decreciente de peso según fórmula ANMAT/CAA del ERP.
3. **Separador Ornamental:**  
   Filete victoriano simétrico con volutas y hojas en el centro.
4. **Nombre Protagonista:**  
   Nombre de la receta en mayúsculas negrita contundente (1 o 2 líneas).  
   Subtítulo explicativo en cursiva entre paréntesis (ej: *(Sabores de Japón)* o *(Sal Marina con Té Ahumado y Hongos)*).
5. **Segundo Separador Ornamental.**
6. **Sugerencias y Modo de Uso:**  
   `SUGERENCIAS:` en negrita + maridajes recomendados.  
   `MODO DE USO:` en negrita + técnica de aplicación culinaria.
7. **Leyenda Legal de Sales (Solo si es Sal):**  
   `Sal entrefina enriquecida para uso alimentario según Ley Nac. N°17259`
8. **Pie de Contacto y Código QR:**  
   - Código QR a la izquierda (110x110 px) apuntando a `https://www.rojomalbec.com.ar`.
   - Bloque de texto a la derecha:
     - **Rojo Malbec Sales & Blends** (Bold)
     - Los Hornillos, Córdoba
     - Tel: 3544308380
     - www.rojomalbec.com.ar

---

## 3. Anatomía de la Etiqueta Frontal

1. **Arco Curvo Superior:**  
   Familia o procedencia del blend (ej: `SAL MARINA INFUSIONADA EN MALBEC` o `ESPECIAS TRADICIONALES DE JAPÓN`).
2. **Bloque de Marca:**  
   `Rojo Malbec`  
   `SALES & BLENDS DE ESPECIAS Y TÉS`
3. **Nombre del Producto + Bajada:**  
   Tipografía bold con serifa + breve descriptor (ej: `BLEND CON VINO MALBEC`).
4. **Ilustración Botánica Central:**  
   Grabado botánico vintage de los ingredientes clave.
5. **Sello Artesanal (Abajo a la izquierda):**  
   Doble círculo rústico inclinado con la leyenda `HECHO A MANO`.
6. **Arco Curvo Inferior:**  
   `IND. ARG. 100g` (Sales) o `IND. ARG. 50g` (Blends) en letra itálica.

---

## 4. Generador Automatizado en Python

El módulo oficial está disponible en:
`tools/etiquetas/generador_etiquetas.py`

### Ejemplo de uso rápido:
```python
from tools.etiquetas.generador_etiquetas import generar_etiqueta_trasera_oficial

generar_etiqueta_trasera_oficial(
    nombre_linea_1="SAL AL MALBEC",
    nombre_linea_2="& TÉ AHUMADO",
    subtitulo="(Sal Marina con Té Ahumado y Hongos)",
    ingredientes_texto="Sal marina entrefina · Vino malbec · Té ahumado Lapsang Souchong · Puerro deshidratado · Hongo de pino patagónico · Shiitake · Pimienta larga",
    sugerencias_texto="Carnes asadas, vegetales a la parrilla, cordero, hamburguesas gourmet, guisos y papas rústicas.",
    modo_uso_texto="Espolvorear durante la cocción o al finalizar el sellado para potenciar aromas ahumados y notas umami.",
    es_sal=True,
    output_path="etiqueta_trasera.png"
)
```
