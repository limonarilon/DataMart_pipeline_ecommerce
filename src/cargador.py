"""
cargador.py — Módulo de Carga (Bloque: Almacenamiento + Optimización)
--------------------------------------------------------------------------
Se conecta a SQLite y realiza la carga usando `executemany` (bulk insert)
en lugar de un INSERT por fila -> reduce drásticamente el número de
operaciones contra la base de datos (optimización medible).
"""
import logging
import sqlite3
import pandas as pd

logger = logging.getLogger("datamart.cargador")


def inicializar_bd(db_path: str, schema_path: str):
    """Crea las tablas destino a partir del schema.sql si no existen."""
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    logger.info("Base de datos inicializada correctamente.")


def cargar_dataframe(db_path: str, tabla: str, df: pd.DataFrame):
    """Inserta un DataFrame completo en la tabla indicada usando bulk insert."""
    if df.empty:
        return 0
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(tabla, conn, if_exists="append", index=False, method="multi", chunksize=1000)
        conn.commit()
    except Exception as e:
        logger.error(f"Error al cargar en tabla '{tabla}': {e}")
        raise
    finally:
        conn.close()
    logger.info(f"Cargados {len(df)} registros en tabla '{tabla}'.")
    return len(df)


def registrar_log_ejecucion(db_path: str, log: dict):
    """Guarda el resumen de ejecución del job en la tabla de logs (trazabilidad)."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """INSERT INTO logs_ejecucion
           (job_id, fecha_inicio, total_leidos, total_validos,
            total_devoluciones, total_rechazados, tiempo_ms, origen_archivo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            log["job_id"], log["fecha_inicio"], log["total_leidos"],
            log["total_validos"], log["total_devoluciones"],
            log["total_rechazados"], log["tiempo_ms"], log["origen_archivo"],
        ),
    )
    conn.commit()
    conn.close()
