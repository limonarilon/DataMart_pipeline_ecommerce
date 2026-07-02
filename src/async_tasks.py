"""
async_tasks.py — Módulo Asíncrono (Bloque: Flujos síncronos/asíncronos)
----------------------------------------------------------------------------
La carga de datos en la base (lector -> validador -> procesador -> cargador)
es SÍNCRONA a propósito: el negocio necesita la certeza de que los datos
quedaron guardados antes de continuar.

Sin embargo, hay tareas secundarias que NO necesitan bloquear el pipeline:
  - Generar el reporte agregado (JSON) para el dashboard/evidencia
  - Archivar/comprimir el log de texto del job
  - "Notificar" que el proceso terminó (simulado)

Estas tres tareas se ejecutan de forma CONCURRENTE con asyncio.gather()
en lugar de una tras otra -> se reduce el tiempo total de las tareas
secundarias y no retrasan la disponibilidad del dato ya cargado.
"""
import asyncio
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("datamart.async")


async def generar_reporte_json(resumen: dict, reports_dir: str):
    """Escribe el resumen del job en un archivo JSON (evidencia para el dashboard)."""
    await asyncio.sleep(0.3)  # simula tiempo de escritura / I/O
    path = Path(reports_dir) / f"reporte_{resumen['job_id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    logger.info(f"[async] Reporte generado en {path}")
    return str(path)


async def archivar_log(job_id: str, logs_dir: str):
    """Simula el archivado/rotación del log de ejecución del job."""
    await asyncio.sleep(0.2)  # simula I/O de compresión
    logger.info(f"[async] Log del job {job_id} archivado correctamente.")
    return True


async def enviar_notificacion(resumen: dict):
    """Simula el envío de una notificación (correo/webhook) al finalizar el job."""
    await asyncio.sleep(0.4)  # simula latencia de red
    logger.info(
        f"[async] Notificación enviada: job {resumen['job_id']} "
        f"finalizado -> {resumen['total_validos']} ventas cargadas."
    )
    return True


async def _ejecutar_tareas(resumen: dict, logs_dir: str, reports_dir: str):
    inicio = time.perf_counter()
    resultados = await asyncio.gather(
        generar_reporte_json(resumen, reports_dir),
        archivar_log(resumen["job_id"], logs_dir),
        enviar_notificacion(resumen),
    )
    duracion = round((time.perf_counter() - inicio) * 1000, 2)
    logger.info(f"[async] Tareas secundarias completadas en {duracion} ms (ejecutadas en paralelo).")
    return resultados


def lanzar_tareas_async(resumen: dict, logs_dir: str, reports_dir: str):
    """
    Punto de entrada síncrono que dispara las tareas asíncronas.
    Se llama DESPUÉS de que los datos críticos ya están guardados en la BD,
    por lo que su tiempo de ejecución no afecta la disponibilidad del dato.
    """
    asyncio.run(_ejecutar_tareas(resumen, logs_dir, reports_dir))
