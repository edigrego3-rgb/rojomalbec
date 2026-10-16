---
name: etiquetas-gourmet
description: Guía, especificación técnica y generador automatizado de etiquetas circulares de 3 pulgadas (frontales y traseras) para frascos y sales/blends de autor de Rojo Malbec.
---

# Skill: Diseño y Fabricación de Etiquetas Gourmet – Rojo Malbec

Este skill estandariza la producción gráfica de etiquetas circulares de autor para frascos y tapas de Rojo Malbec en Los Hornillos, Traslasierra, Córdoba.

---

## 1. Especificaciones Físicas y de Imprenta (Reglas Innegociables)

- **Medida Física Real:** **3 pulgadas de diámetro exactas (76,2 mm / 3.0")**.
- **Resolución de Imprenta:** **300 DPI mínimo** (900 x 900 px netos, o 1024 x 1024 px a escala).
- **Fondo:** **Blanco puro (`#FFFFFF`)**, sin sombras, viñetas ni tonalidades cremas artificiales (apto para impresión directa sobre papel blanco autoadhesivo o vinilo).
- **Encuadre Geométrico:** Dos aros concéntricos negros de trazo limpio:
  - Aro 1 (exterior): Margen perimetral fino.
  - Aro 2 (interior): Grosor más marcado, equidistante y concéntrico.

---

## 2. Anatomía de la Contraetiqueta (Etiqueta Trasera Oficial)

Toda etiqueta trasera debe seguir estrictamente la jerarquía visual del **Patrón Oro Oficial** (`tools/etiquetas/assets/patron_oro_trasera_sal_malbec_te_ahumado.png`):

1. **Arco Curvo Superior:**
   - Texto: `PRODUCTO ARTESANAL · TRASLASIERRA`
   - Tipografía: Palo seco bold (`Arial Bold`), curvada a lo largo del semicírculo superior.
   - **Regla de Aire:** Debe mantener espacio libre y NUNCA tocar la línea del aro negro ni los textos inferiores.

2. **Bloque Ingredientes y Leyenda Legal:**
   - `INGREDIENTES:` (en negrita condensada).
   - Lista de ingredientes en orden decreciente de peso (según receta oficial ANMAT/CAA del ERP).
   - Al pie del bloque de ingredientes (4° renglón):  
     `Sal Marina entrefina enriquecida para uso alimentario según ley N 17259` *(solo en sales)*.
   - **Regla de Espaciado:** El bloque debe respirar; ningún lateral debe tocar el arco curvo superior.

3. **Separador Ornamental Superior:**
   - Arabesco victoriano simétrico oficial (`tools/etiquetas/assets/arabesco_victoriano.png`).

4. **Nombre del Producto (Protagonista):**
   - Tipografía: **Serif Condensada de autor**, en **UNA SOLA LÍNEA HORIZONTAL COMPLETA** (ej: `SAL AL MALBEC & TÉ AHUMADO`).  
     *No dividir en dos líneas.* Si el nombre es largo, condensar proporcionalmente el ancho (73%–75%).
   - Subtítulo en cursiva/itálica elegante entre paréntesis: `(Lapsang Souchong)`.

5. **Separador Ornamental Inferior:**
   - Mismo arabesco invertido verticalmente.

6. **Bloque Continuo de Sugerencias y Modo de Uso:**
   - Disposición en bloque compacto continuo de 3 líneas para no saturar el espacio vertical de las 3 pulgadas:  
     `SUGERENCIAS: [Maridajes recomendados]. MODO DE USO: [Técnica culinaria de aplicación]. Sal de cocción.`
   - Tipografía: Palo seco condensado (`Arial Narrow Bold`), perfectamente legible en el frasco físico.

7. **Pie de Trazabilidad (Código QR + Contacto):**
   - A la izquierda: **Código QR cuadrado** (apuntando a `https://www.rojomalbec.com.ar`).
   - A la derecha:
     - **Rojo Malbec Sales & Blends**
     - Los Hornillos, Córdoba
     - Tel: 3544308380
     - www.rojomalbec.com.ar

---

## 3. Anatomía de la Etiqueta Frontal Oficial

1. **Arco Superior:** Tipo de sal y origen geográfico en `Arial Bold` con radio 405 (ej: `SAL MARINA DE AUTOR · TRASLASIERRA`).
2. **Bloque de Marca:**  
   `Rojo Malbec`  
   `SALES & BLENDS DE ESPECIAS Y TÉS`
3. **Nombre Protagonista + Descriptor:**  
   `SAL AL MALBEC`  
   `& TÉ AHUMADO`  
   *(Lapsang Souchong)*  
   `CON HONGOS DEL BOSQUE, PUERRO Y PIMIENTA LARGA`
4. **Ilustración Botánica de Autor:**  
   Grabado botánico vintage de los ingredientes reales (copa de vino, hongos, uvas, puerro, hebras de té, pimienta larga) sobre fondo blanco puro `#FFFFFF`.
5. **Sello Artesanal:** `HECHO A MANO` (doble anillo rústico con inclinación sobre la izquierda).
6. **Arco Inferior:** `IND. ARG. 100g` (Sales) o `IND. ARG. 50g` (Blends), con tipografía cursiva serif en arco inferior natural.

---

## 4. Archivos de Referencia y Patrón Oro

- **Patrón Oro Trasero Oficial:** `tools/etiquetas/assets/patron_oro_trasera_sal_malbec_te_ahumado.png`
- **Patrón Oro Frontal Oficial:** `tools/etiquetas/assets/patron_oro_frontal_sal_malbec_te_ahumado.png`
- **Arabesco Oficial:** `tools/etiquetas/assets/arabesco_victoriano.png`
- **Generador Oficial:** `tools/etiquetas/generador_etiquetas.py` (funciones `generar_etiqueta_trasera_oficial` y `generar_etiqueta_frontal_oficial`)
- **Salida para el Usuario:** Siempre exportar con resolución calibrada a 3 pulgadas al Escritorio:  
  `C:\Users\Eduardo\Desktop\Etiqueta_Trasera_[Nombre_Producto]_OFICIAL.png`  
  `C:\Users\Eduardo\Desktop\Etiqueta_Frontal_[Nombre_Producto]_OFICIAL.png`

