"""
validador.py — Módulo de Validación (Bloque: Calidad de datos + Reglas de negocio)
------------------------------------------------------------------------------------
Clasifica cada fila de un lote en 3 destinos, usando operaciones vectorizadas
de pandas (más eficiente que iterar fila por fila -> optimización):

  1. VÁLIDOS       -> venta real y completa
  2. DEVOLUCIONES  -> regla de NEGOCIO válida (Quantity < 0 / InvoiceNo empieza con 'C')
                      No es un error, así que no se descarta: se separa.
  3. RECHAZADOS    -> error de CALIDAD de datos, se guarda con su causa

Reglas aplicadas (en orden):
  - Fila duplicada exacta                -> rechazo "duplicado"
  - CustomerID nulo                      -> rechazo "cliente_no_identificado"
  - Description nula/vacía               -> rechazo "descripcion_faltante"
  - Quantity < 0  o InvoiceNo con 'C'    -> devolución
  - Quantity == 0                        -> rechazo "cantidad_cero"
  - UnitPrice <= 0                       -> rechazo "precio_invalido"
  - Resto                                -> válido
"""
import logging
import pandas as pd

logger = logging.getLogger("datamart.validador")


def validar_lote(df: pd.DataFrame):
    df = df.copy()
    df["causa"] = None

    # 1) Duplicados exactos (se conserva la primera ocurrencia)
    es_duplicado = df.duplicated(keep="first")
    df.loc[es_duplicado, "causa"] = "duplicado"

    # 2) Cliente no identificado
    sin_causa = df["causa"].isna()
    es_sin_cliente = sin_causa & df["CustomerID"].isna()
    df.loc[es_sin_cliente, "causa"] = "cliente_no_identificado"

    # 3) Descripción faltante
    sin_causa = df["causa"].isna()
    es_sin_desc = sin_causa & (df["Description"].isna() | (df["Description"].astype(str).str.strip() == ""))
    df.loc[es_sin_desc, "causa"] = "descripcion_faltante"

    # 4) Devoluciones (regla de negocio, no es error de calidad)
    sin_causa = df["causa"].isna()
    es_devolucion = sin_causa & (
        (df["Quantity"] < 0) | (df["InvoiceNo"].astype(str).str.startswith("C"))
    )

    # 5) Cantidad cero (entre lo que no es devolución)
    sin_causa = df["causa"].isna() & ~es_devolucion
    es_cantidad_cero = sin_causa & (df["Quantity"] == 0)
    df.loc[es_cantidad_cero, "causa"] = "cantidad_cero"

    # 6) Precio inválido
    sin_causa = df["causa"].isna() & ~es_devolucion
    es_precio_invalido = sin_causa & (df["UnitPrice"] <= 0)
    df.loc[es_precio_invalido, "causa"] = "precio_invalido"

    rechazados = df[df["causa"].notna()].copy()
    devoluciones = df[df["causa"].isna() & es_devolucion].copy()
    validos = df[df["causa"].isna() & ~es_devolucion].copy()

    logger.info(
        f"Lote clasificado -> válidos: {len(validos)}, "
        f"devoluciones: {len(devoluciones)}, rechazados: {len(rechazados)}"
    )
    return validos, devoluciones, rechazados
