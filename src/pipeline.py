"""
pipeline.py — Orquestador principal del sistema DataMart
--------------------------------------------------------------------------
Ejecuta el flujo completo:

  Extracción (sync) -> Validación (sync) -> Procesamiento (sync)
        -> Carga a SQLite (sync, con batching)
        -> Tareas secundarias (async, en paralelo, no bloqueantes)
        -> Log de ejecución (trazabilidad)

Uso:
    python -m src.pipeline                  # ejecuta una vez, ahora
    python -m src.pipeline --file otro.xlsx  # usa otro archivo origen
"""
import argparse
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path

from src import config
from src.lector import leer_datos, generar_lotes
from src.validador import validar_lote
from src.procesador import procesar_ventas, procesar_devoluciones, procesar_rechazos
from src.cargador import inicializar_bd, cargar_dataframe, registrar_log_ejecucion
from src.async_tasks import lanzar_tareas_async


def configurar_logging(job_id: str):
    log_file = Path(config.LOGS_DIR) / f"job_{job_id}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
    )
    return log_file


def ejecutar_pipeline(archivo: str = None) -> dict:
    job_id = uuid.uuid4().hex[:8]
    log_file = configurar_logging(job_id)
    logger = logging.getLogger("datamart.pipeline")

    archivo = archivo or config.DATA_PATH
    logger.info(f"===== INICIO JOB {job_id} | origen: {archivo} =====")
    inicio = time.perf_counter()

    inicializar_bd(config.DB_PATH, config.SCHEMA_PATH)

    df_total = leer_datos(archivo)
    total_leidos = len(df_total)

    total_validos = total_devoluciones = total_rechazados = 0

    for lote in generar_lotes(df_total, config.BATCH_SIZE):
        validos, devoluciones, rechazados = validar_lote(lote)

        ventas_out = procesar_ventas(validos, job_id)
        devoluciones_out = procesar_devoluciones(devoluciones, job_id)
        rechazos_out = procesar_rechazos(rechazados, job_id)

        total_validos += cargar_dataframe(config.DB_PATH, "ventas", ventas_out)
        total_devoluciones += cargar_dataframe(config.DB_PATH, "devoluciones", devoluciones_out)
        total_rechazados += cargar_dataframe(config.DB_PATH, "rechazos", rechazos_out)

    tiempo_ms = round((time.perf_counter() - inicio) * 1000, 2)

    resumen = {
        "job_id": job_id,
        "fecha_inicio": datetime.now().isoformat(),
        "total_leidos": total_leidos,
        "total_validos": total_validos,
        "total_devoluciones": total_devoluciones,
        "total_rechazados": total_rechazados,
        "tiempo_ms": tiempo_ms,
        "origen_archivo": archivo,
    }

    # Los datos críticos YA están en la base -> ahora se disparan tareas
    # secundarias en segundo plano (async, no bloqueantes).
    registrar_log_ejecucion(config.DB_PATH, resumen)
    lanzar_tareas_async(resumen, config.LOGS_DIR, config.REPORTS_DIR)

    logger.info(f"===== FIN JOB {job_id} | {resumen} =====")
    print("\nResumen de ejecución:")
    for k, v in resumen.items():
        print(f"  {k}: {v}")
    print(f"\nLog completo en: {log_file}")

    return resumen


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline ETL DataMart")
    parser.add_argument("--file", type=str, default=None, help="Ruta alternativa del archivo origen")
    args = parser.parse_args()
    ejecutar_pipeline(args.file)
