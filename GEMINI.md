# Directrices de Proyecto y Arquitectura – Rojo Malbec

Este archivo es leído automáticamente por Antigravity / Gemini al iniciar cualquier sesión en este workspace. Define el contexto del negocio, la infraestructura y las reglas innegociables.

---

## 1. Contexto del Negocio y Entorno
- **Negocio:** Rojo Malbec (especias, blends, sales gourmet de autor y catálogo gastronómico en Traslasierra, Córdoba / Mendoza, Argentina).
- **Idioma Obligatorio:** Español rioplatense/argentino profesional en toda comunicación, comentarios, documentación, interfaces y planes.
- **Dueño / Usuario:** Eduardo (no programador: explicar siempre en criollo, simple, paso por paso, sin dar por sentado conocimientos técnicos).

---

## 2. Infraestructura y Despliegue en Producción
- **VPS en Hetzner Cloud:**
  - **IP Pública:** `2.31.10.225` (Ubuntu 24.04 con Docker Engine y Docker Compose).
  - **Conexión SSH automática:** Configurada en el usuario local de Windows (`~/.ssh/config` como `rojomalbec-vps` con clave `id_ed25519`). Se conecta directamente con:
    ```bash
    ssh root@2.31.10.225
    ```
  - **Ruta del proyecto en el VPS:** `/root/rojomalbec`
- **Dominios y DNS (Gestionados en Cloudflare con SSL automático vía Caddy):**
  - **ERP:** `https://erp.rojomalbec.com.ar` (Puerto local 8501)
  - **Distribuidor / B2B:** `https://b2b.rojomalbec.com.ar` (Puerto local 8502)
  - **Preventa:** `https://preventa.rojomalbec.com.ar` (Puerto local 8503)
  - **Catálogo Web Público:** `https://www.rojomalbec.com.ar` (GitHub Pages)

---

## 3. Estructura del Monorepo (`C:\Proyectos\rojomalbec`)
```text
C:\Proyectos\rojomalbec\
├── apps/
│   ├── erp/                  # ERP principal (app_v3.py, stock, recetas, ventas, mostrador)
│   ├── distribuidor/         # Portal mayorista B2B (Streamlit)
│   ├── preventa/             # Portal de preventas (Streamlit)
│   └── pos_feria/            # Punto de venta offline-first para ferias
├── tools/
│   ├── catalogo/             # Generador de catálogo PDF (generar_catalogo_pdf.py)
│   └── etiquetas/            # Generador de etiquetas (make_label.py)
├── docker-compose.yml        # Orquestación de servicios en producción (VPS)
├── Caddyfile                 # Proxy reverso HTTPS con Let's Encrypt automático
├── SUBIR_CAMBIOS.bat         # Script para Edu: commit + push con doble clic
├── .gitignore                # Escudo estricto contra credenciales y secretos
└── README.md                 # Documentación técnica general
```

---

## 4. Reglas Innegociables de Seguridad y Código
1. **PROHIBIDO subir secretos a GitHub:**  
   Nunca commitear `secrets.toml`, credenciales JSON de Google (`claves/`), ni archivos `.env`.  
   Antes de cada commit, verificar siempre con:
   ```powershell
   git ls-files --cached | Select-String "secrets|claves|\.json$|\.toml$"
   ```
   Si devuelve algo, frenar inmediatamente.
2. **Google Sheets:**  
   La base de datos es la planilla "RojoMalbec DB". En el ERP, `load_data` NUNCA debe llevar `@st.cache_data` para evitar pisar ventas en mostrador/POS. La apertura de la planilla se optimiza con `@st.cache_resource` y las cargas iniciales se hacen en batch (`values_batch_get`).
3. **Flujo de Deploy al VPS:**  
   Cuando se aprueban cambios de código:
   - Se commitean y suben a GitHub (`main`).
   - En el VPS se corre `git pull origin main` y `docker compose up -d --build <servicio>`.
