"""
procesador.py — Módulo de Procesamiento (Bloque: Transformación + Ética)
---------------------------------------------------------------------------
Aplica las transformaciones de negocio sobre los registros ya clasificados
como válidos o devoluciones, y aplica el criterio ético de anonimización
sobre el identificador de cliente antes de que el dato llegue a la base
destino y a la visualización.
"""
import pandas as pd


def enmascarar_cliente(customer_id):
    """
    Enmascara el CustomerID (dato semi-sensible): conserva solo los dos
    primeros dígitos. Ej: 17850 -> '17***'
    Se hace ANTES de guardar/visualizar -> principio de minimización de datos.
    """
    if pd.isna(customer_id):
        return None
    texto = str(int(customer_id))
    if len(texto) <= 2:
        return "*" * len(texto)
    return texto[:2] + "*" * (len(texto) - 2)


def procesar_ventas(df: pd.DataFrame, job_id: str) -> pd.DataFrame:
    """Transforma el lote de ventas válidas al formato de la tabla destino."""
    out = pd.DataFrame()
    out["invoice_no"] = df["InvoiceNo"].astype(str)
    out["stock_code"] = df["StockCode"].astype(str)
    out["description"] = df["Description"].astype(str).str.strip()
    out["quantity"] = df["Quantity"].astype(int)
    out["invoice_date"] = pd.to_datetime(df["InvoiceDate"]).astype(str)
    out["unit_price"] = df["UnitPrice"].astype(float)
    out["customer_id"] = df["CustomerID"].apply(enmascarar_cliente)
    out["total_venta"] = (out["quantity"] * out["unit_price"]).round(2)
    out["country"] = df["Country"].astype(str).str.strip()
    out["job_id"] = job_id
    out["fecha_carga"] = pd.Timestamp.now().isoformat()
    return out


def procesar_devoluciones(df: pd.DataFrame, job_id: str) -> pd.DataFrame:
    """Transforma el lote de devoluciones al formato de la tabla destino."""
    out = pd.DataFrame()
    out["invoice_no"] = df["InvoiceNo"].astype(str)
    out["stock_code"] = df["StockCode"].astype(str)
    out["description"] = df["Description"].astype(str).str.strip()
    out["quantity"] = df["Quantity"].astype(int)
    out["invoice_date"] = pd.to_datetime(df["InvoiceDate"]).astype(str)
    out["unit_price"] = df["UnitPrice"].astype(float)
    out["customer_id"] = df["CustomerID"].apply(enmascarar_cliente)
    out["total_devuelto"] = (out["quantity"] * out["unit_price"]).round(2)
    out["country"] = df["Country"].astype(str).str.strip()
    out["job_id"] = job_id
    out["fecha_carga"] = pd.Timestamp.now().isoformat()
    return out


def procesar_rechazos(df: pd.DataFrame, job_id: str) -> pd.DataFrame:
    """Transforma el lote de rechazados, conservando la causa para trazabilidad."""
    out = pd.DataFrame()
    out["invoice_no"] = df["InvoiceNo"].astype(str)
    out["stock_code"] = df["StockCode"].astype(str)
    out["description"] = df["Description"].astype(str)
    out["quantity"] = df["Quantity"]
    out["invoice_date"] = df["InvoiceDate"].astype(str)
    out["unit_price"] = df["UnitPrice"]
    out["customer_id"] = df["CustomerID"].apply(enmascarar_cliente)
    out["country"] = df["Country"].astype(str)
    out["causa"] = df["causa"]
    out["job_id"] = job_id
    out["fecha_carga"] = pd.Timestamp.now().isoformat()
    return out
