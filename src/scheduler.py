"""
scheduler.py — Calendarización (Bloque: Control de flujos / Automatización)
--------------------------------------------------------------------------
Evidencia que el sistema puede operar de forma programada, sin depender
de una ejecución manual. Equivalente en Python a un cron job.

Uso:
    python -m src.scheduler            # deja el proceso corriendo, programado
    python -m src.scheduler --now      # ejecuta un ciclo inmediato (demo en vivo)
"""
import argparse
import time
import schedule

from src.pipeline import ejecutar_pipeline


def job():
    print("Iniciando carga programada...")
    ejecutar_pipeline()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scheduler del pipeline DataMart")
    parser.add_argument("--now", action="store_true", help="Ejecuta un ciclo inmediatamente y termina")
    parser.add_argument("--hora", type=str, default="02:00", help="Hora diaria de ejecución (HH:MM)")
    args = parser.parse_args()

    if args.now:
        job()
    else:
        schedule.every().day.at(args.hora).do(job)
        print(f"Scheduler activo. Próxima carga automática todos los días a las {args.hora}.")
        print("Presiona Ctrl+C para detener.")
        while True:
            schedule.run_pending()
            time.sleep(30)
