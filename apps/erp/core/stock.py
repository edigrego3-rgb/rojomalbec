# core/stock.py
# =========================
# Lógica central de stock (anti negativos)
# =========================

class StockError(Exception):
    """Error de stock o validación."""
    pass


def _get_float(df, idx, campo: str) -> float:
    try:
        return float(df.at[idx, campo])
    except Exception:
        # Si está vacío o mal, lo tratamos como 0 para no permitir descuentos
        return 0.0


def validar_stock(df, idx, cantidad: float, campo: str) -> bool:
    actual = _get_float(df, idx, campo)
    return actual >= float(cantidad)


def descontar_stock(df, idx, cantidad: float, campo: str):
    """Descuenta stock del dataframe en (idx, campo). Lanza StockError si no alcanza."""
    cantidad = float(cantidad)
    if cantidad <= 0:
        raise StockError("Cantidad inválida para descuento.")

    actual = _get_float(df, idx, campo)
    if actual < cantidad:
        raise StockError(f"Stock insuficiente. Disponible: {actual:.2f}, requerido: {cantidad:.2f}")

    df.at[idx, campo] = actual - cantidad
    return df


def sumar_stock(df, idx, cantidad: float, campo: str):
    """Suma stock al dataframe en (idx, campo)."""
    cantidad = float(cantidad)
    if cantidad <= 0:
        raise StockError("Cantidad inválida para suma.")
    actual = _get_float(df, idx, campo)
    df.at[idx, campo] = actual + cantidad
    return df
