"""
benchmark.py — Evidencia medible de optimización (para informe y defensa)
--------------------------------------------------------------------------
Este script NO forma parte del flujo productivo del pipeline; es una
herramienta aparte para generar los números de "antes/después" que pide
la rúbrica en los indicadores de optimización (componentes 4 y 6, defensa
10 y 12).

Compara dos cosas, cada una por separado:

  1) CARGA: insertar fila por fila (INSERT individual) vs. bulk insert
     (to_sql con method="multi", que es lo que ya usa cargador.py).

  2) TAREAS SECUNDARIAS: ejecutarlas una tras otra (secuencial) vs.
     ejecutarlas con asyncio.gather() (en paralelo, que es lo que ya usa
     async_tasks.py).

No modifica datamart.db: crea y usa benchmark.db aparte, que se puede
borrar sin ningún problema.

Uso:
    python -m src.benchmark                 # usa 50.000 filas de muestra
    python -m src.benchmark --rows 100000    # ajustar tamaño de muestra
"""
import argparse
import asyncio
import sqlite3
import time
from pathlib import Path

from src import config
from src.lector import leer_datos
from src.async_tasks import generar_reporte_json, archivar_log, enviar_notificacion

BENCH_DB = str(Path(config.BASE_DIR) / "benchmark.db")


# ------------------------------------------------------------------
# 1) CARGA: fila por fila vs bulk insert
# ------------------------------------------------------------------
def preparar_tablas_benchmark():
    conn = sqlite3.connect(BENCH_DB)
    conn.execute("DROP TABLE IF EXISTS bench_fila_por_fila")
    conn.execute("DROP TABLE IF EXISTS bench_bulk_insert")
    ddl = """(invoice_no TEXT, stock_code TEXT, quantity INTEGER,
              unit_price REAL, country TEXT)"""
    conn.execute(f"CREATE TABLE bench_fila_por_fila {ddl}")
    conn.execute(f"CREATE TABLE bench_bulk_insert {ddl}")
    conn.commit()
    conn.close()


def benchmark_fila_por_fila(df) -> float:
    conn = sqlite3.connect(BENCH_DB)
    inicio = time.perf_counter()
    for row in df.itertuples(index=False):
        conn.execute(
            "INSERT INTO bench_fila_por_fila VALUES (?, ?, ?, ?, ?)",
            (str(row.InvoiceNo), str(row.StockCode), int(row.Quantity),
             float(row.UnitPrice), str(row.Country)),
        )
    conn.commit()
    duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
    conn.close()
    return duracion_ms


def benchmark_bulk_insert(df) -> float:
    conn = sqlite3.connect(BENCH_DB)
    out = df[["InvoiceNo", "StockCode", "Quantity", "UnitPrice", "Country"]].copy()
    out.columns = ["invoice_no", "stock_code", "quantity", "unit_price", "country"]
    inicio = time.perf_counter()
    out.to_sql("bench_bulk_insert", conn, if_exists="append", index=False,
               method="multi", chunksize=1000)
    conn.commit()
    duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
    conn.close()
    return duracion_ms


# ------------------------------------------------------------------
# 2) TAREAS SECUNDARIAS: secuencial vs paralelo (asyncio.gather)
# ------------------------------------------------------------------
async def _tareas_secuencial(resumen, logs_dir, reports_dir):
    inicio = time.perf_counter()
    await generar_reporte_json(resumen, reports_dir)
    await archivar_log(resumen["job_id"], logs_dir)
    await enviar_notificacion(resumen)
    return round((time.perf_counter() - inicio) * 1000, 2)


async def _tareas_paralelo(resumen, logs_dir, reports_dir):
    inicio = time.perf_counter()
    await asyncio.gather(
        generar_reporte_json(resumen, reports_dir),
        archivar_log(resumen["job_id"], logs_dir),
        enviar_notificacion(resumen),
    )
    return round((time.perf_counter() - inicio) * 1000, 2)


def benchmark_async() -> tuple:
    resumen_seq = {"job_id": "bench_secuencial", "total_validos": 0}
    resumen_par = {"job_id": "bench_paralelo", "total_validos": 0}
    t_secuencial = asyncio.run(_tareas_secuencial(resumen_seq, config.LOGS_DIR, config.REPORTS_DIR))
    t_paralelo = asyncio.run(_tareas_paralelo(resumen_par, config.LOGS_DIR, config.REPORTS_DIR))
    return t_secuencial, t_paralelo


# ------------------------------------------------------------------
def main(rows: int):
    print(f"Cargando muestra de {rows} filas desde {config.DATA_PATH} ...")
    df_total = leer_datos(config.DATA_PATH)
    df = df_total.head(rows).copy()

    print("\n=== 1) CARGA: fila por fila vs bulk insert ===")
    preparar_tablas_benchmark()
    t_fila = benchmark_fila_por_fila(df)
    t_bulk = benchmark_bulk_insert(df)
    mejora = round((1 - t_bulk / t_fila) * 100, 1) if t_fila > 0 else 0
    print(f"  Filas insertadas:        {len(df)}")
    print(f"  Fila por fila:           {t_fila} ms")
    print(f"  Bulk insert (multi):     {t_bulk} ms")
    print(f"  Mejora:                  {mejora}% más rápido con bulk insert")

    print("\n=== 2) TAREAS SECUNDARIAS: secuencial vs paralelo (asyncio.gather) ===")
    t_secuencial, t_paralelo = benchmark_async()
    mejora_async = round((1 - t_paralelo / t_secuencial) * 100, 1) if t_secuencial > 0 else 0
    print(f"  Secuencial (una tras otra): {t_secuencial} ms")
    print(f"  Paralelo (asyncio.gather):  {t_paralelo} ms")
    print(f"  Mejora:                     {mejora_async}% más rápido en paralelo")

    print(f"\nBenchmark completado. Base temporal: {BENCH_DB}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark de optimización DataMart")
    parser.add_argument("--rows", type=int, default=50000, help="Cantidad de filas de muestra a usar (default: 50000)")
    args = parser.parse_args()
    main(args.rows)
