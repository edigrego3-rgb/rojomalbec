# Rojo Malbec – Monorepo

Arquitectura unificada y estructurada para el ecosistema de aplicaciones y herramientas operativas de **Rojo Malbec** (Mendoza, Argentina). Preparado para ejecución local y despliegue contenerizado en VPS (Hetzner Cloud con Docker y proxy reverso Caddy).

---

## 📁 Estructura del Monorepo

```text
C:\Proyectos\rojomalbec\
├── apps/
│   ├── erp/                  # ERP operativo (Streamlit, gestión de stock, recetas, producción, ventas)
│   ├── distribuidor/         # Portal de distribuidores y mayoristas B2B (Streamlit)
│   ├── preventa/             # Portal de preventa a clientes (Streamlit)
│   └── pos_feria/            # Terminal Punto de Venta para eventos/ferias (PWA / Web offline-first)
├── tools/
│   ├── catalogo/             # Generador automatizado de catálogo en PDF (generar_catalogo_pdf.py)
│   └── etiquetas/            # Generador y maquetador de etiquetas para frascos y pouches (make_label.py)
├── docker-compose.yml        # Orquestación de servicios para VPS
├── Caddyfile                 # Proxy reverso HTTPS automático (SSL Let's Encrypt)
├── SUBIR_CAMBIOS.bat         # Sincronizador Git automático con verificación de seguridad
├── .gitignore                # Escudo estricto contra secretos, credenciales y claves
└── README.md                 # Documentación técnica del proyecto
```

---

## 🔒 Seguridad y Manejo de Credenciales

Este repositorio implementa un **bloqueo estricto** en `.gitignore`:
- **NUNCA** se suben a Git archivos `secrets.toml`, credenciales JSON de Google Service Accounts (`claves/`), archivos `.env` ni configuraciones sensibles.
- En el VPS, las credenciales se montan de forma segura mediante volúmenes de solo lectura (`:ro`) referenciados en `docker-compose.yml`.

---

## 🚀 Despliegue en VPS (Hetzner Cloud)

Para levantar el ecosistema completo en el servidor de producción:

```bash
docker compose up -d --build
```

### Puertos y Dominios
| Servicio | Puerto Interno / Host | Dominio Público |
| :--- | :--- | :--- |
| **ERP** | 8501 | `erp.rojomalbec.com.ar` |
| **Distribuidor (B2B)** | 8502 | `b2b.rojomalbec.com.ar` |
| **Preventa** | 8503 | `preventa.rojomalbec.com.ar` |

El tráfico HTTP/HTTPS es administrado de manera transparente por **Caddy**, gestionando renovación automática de certificados SSL para los subdominios apuntados en Cloudflare.

---

## 💻 Operación Local en Windows

- **ERP**: Doble clic en el acceso directo de escritorio `Rojo Malbec ERP.lnk` (o ejecutando `apps\erp\Iniciar_RojoMalbec_v3.bat`).
- **Subir cambios**: Doble clic en `SUBIR_CAMBIOS.bat` en la raíz del repositorio. El script verifica que no haya secretos antes de hacer commit y push a la rama `main`.
