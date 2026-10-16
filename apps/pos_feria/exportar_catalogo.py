import os
import json
import tomllib
import gspread
from oauth2client.service_account import ServiceAccountCredentials

current_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
secrets_path = os.path.join(repo_dir, "apps", "erp", ".streamlit", "secrets.toml")

with open(secrets_path, "rb") as f:
    secrets = tomllib.load(f)

creds_dict = dict(secrets["gcp_service_account"])
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open('RojoMalbec DB').worksheet('recetas')
data = sheet.get_all_records()

catalogo = []
for row in data:
    if row.get('Codigo') and str(row.get('Archivada', '')).upper() != 'TRUE':
        pv = row.get('Precio_Venta', 0)
        pm = row.get('Precio_Mayorista', 0)
        try:
            pv = float(pv) if pv != '' else 0.0
        except:
            pv = 0.0
        try:
            pm = float(pm) if pm != '' else 0.0
        except:
            pm = 0.0
        catalogo.append({
            'Codigo': str(row['Codigo']).strip(),
            'Nombre': str(row['Nombre']).strip(),
            'Precio_Mayorista': int(pm) if pm.is_integer() else pm,
            'Precio_Venta': int(pv) if pv.is_integer() else pv
        })

js_path = os.path.join(current_dir, 'catalogo.js')
json_path = os.path.join(current_dir, 'catalogo.json')
json_str = json.dumps(catalogo, indent=4, ensure_ascii=False)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(f"const catalogo_data = {json_str};\n")

with open(json_path, 'w', encoding='utf-8') as f:
    f.write(json_str + "\n")

print(f"Catálogo exportado exitosamente: {len(catalogo)} productos.")
