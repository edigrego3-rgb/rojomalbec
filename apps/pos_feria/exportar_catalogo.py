import pandas as pd
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

creds_dict = json.load(open(r'I:\Mi unidad\RojoMalbec_App\claves\rojomalbecapp-366a663c2610.json'))
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open('RojoMalbec DB').worksheet('recetas')
data = sheet.get_all_records()

catalogo = []
for row in data:
    if row.get('Codigo') and str(row.get('Archivada', '')).upper() != 'TRUE':
        catalogo.append({
            'Codigo': row['Codigo'],
            'Nombre': row['Nombre'],
            'Precio_Mayorista': row['Precio_Mayorista'] if row['Precio_Mayorista'] != '' else 0,
            'Precio_Venta': row['Precio_Venta'] if row['Precio_Venta'] != '' else 0
        })

output_path = r'I:\Mi unidad\RojoMalbec_App\pos_feria\catalogo.js'
with open(output_path, 'w', encoding='utf-8') as f:
    json_str = json.dumps(catalogo, indent=4, ensure_ascii=False)
    f.write(f"const catalogo_data = {json_str};")
