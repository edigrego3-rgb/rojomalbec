# core/io.py
import pandas as pd

def cargar_csv(ruta, columnas):
    if ruta.exists():
        try:
            df = pd.read_csv(ruta)
            for col, tipo in columnas.items():
                if col not in df.columns:
                    df[col] = pd.Series(dtype=tipo)
            df = df[list(columnas.keys())]
            return df.astype(columnas)
        except Exception:
            return pd.DataFrame(columns=columnas.keys()).astype(columnas)
    return pd.DataFrame(columns=columnas.keys()).astype(columnas)

def guardar_csv(df, ruta):
    df.to_csv(ruta, index=False)
