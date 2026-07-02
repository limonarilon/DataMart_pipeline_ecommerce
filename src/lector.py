"""
lector.py — Módulo de Ingesta (Bloque: Lectura/Procesamiento, flujo SÍNCRONO)
------------------------------------------------------------------------------
Responsabilidad única: leer el archivo origen y entregarlo en lotes (batches).
Es síncrono a propósito: el resto del pipeline necesita los datos leídos
ANTES de poder validar y cargar, por lo tanto se espera su respuesta.

Entrada:  ruta de archivo (xlsx/csv)
Salida:   generador de DataFrames (lotes) + total de filas leídas
"""
import logging
import pandas as pd

logger = logging.getLogger("datamart.lector")

COLUMNAS_ESPERADAS = [
    "InvoiceNo", "StockCode", "Description", "Quantity",
    "InvoiceDate", "UnitPrice", "CustomerID", "Country",
]


def leer_datos(path: str) -> pd.DataFrame:
    """
    Lee el archivo completo de forma controlada, validando que exista
    y que tenga la estructura mínima esperada. Maneja errores de
    conexión/lectura sin dejar caer el sistema completo.
    """
    logger.info(f"Iniciando lectura del archivo origen: {path}")
    try:
        if path.endswith(".csv"):
            df = pd.read_csv(path, encoding="ISO-8859-1")
        else:
            df = pd.read_excel(path)
    except FileNotFoundError:
        logger.error(f"Archivo no encontrado: {path}")
        raise
    except Exception as e:
        logger.error(f"Error al leer el archivo origen: {e}")
        raise

    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    if faltantes:
        logger.error(f"El archivo no tiene las columnas esperadas: {faltantes}")
        raise ValueError(f"Columnas faltantes en el origen: {faltantes}")

    logger.info(f"Lectura completa: {len(df)} registros encontrados.")
    return df


def generar_lotes(df: pd.DataFrame, batch_size: int):
    """
    Divide el DataFrame en lotes (batching) para procesar por partes en
    lugar de todo de una vez -> mejora rendimiento y memoria (optimización).
    """
    total = len(df)
    for inicio in range(0, total, batch_size):
        lote = df.iloc[inicio: inicio + batch_size].copy()
        logger.info(f"Lote generado: filas {inicio} a {inicio + len(lote)}")
        yield lote
