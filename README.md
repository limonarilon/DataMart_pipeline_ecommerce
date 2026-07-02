# DataMart — Pipeline ETL para eCommerce (IDY1101 · EFT)

Sistema de ingesta, validación, procesamiento, carga y visualización del
dataset **Online Retail**, construido con Python + SQLite + Streamlit.

## 1. Instalación

Requisitos: Python 3.10+ instalado.

```bash
# 1) Crear y activar un entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2) Instalar dependencias
pip install -r requirements.txt
```

No necesitas instalar SQLite aparte: viene incluido en Python (`sqlite3`).
La base de datos (`datamart.db`) se crea automáticamente al ejecutar el pipeline.

## 2. Ejecutar el pipeline (carga de datos)

```bash
python -m src.pipeline
```

Esto:
1. Crea/inicializa `datamart.db` a partir de `db/schema.sql`.
2. Lee `data/Online_Retail.xlsx` en lotes de 20.000 filas.
3. Valida y clasifica cada fila en **ventas / devoluciones / rechazos**.
4. Enmascara el `customer_id` antes de guardar (ética).
5. Carga cada lote a SQLite con `bulk insert`.
6. Dispara en paralelo (async) la generación de reporte, el archivado de
   logs y una notificación simulada.
7. Registra un log de ejecución en la tabla `logs_ejecucion` y en `logs/`.

Al final verás un resumen en consola con: leídos, cargados, devoluciones,
rechazados y tiempo total.

## 3. Ver el dashboard

```bash
streamlit run dashboard/app.py
```

Se abrirá en el navegador (`http://localhost:8501`) con:
- KPIs del último job (leídos, cargados, devoluciones, rechazados, tiempo).
- Ventas por país y productos más vendidos.
- Evolución de ventas en el tiempo.
- Causas de rechazo.
- Historial de ejecuciones (trazabilidad).

## 4. Automatización (scheduler)

```bash
# Simula el cron: ejecuta un ciclo ahora mismo (para la demo en vivo)
python -m src.scheduler --now

# Deja el proceso corriendo, programado para todos los días a las 02:00
python -m src.scheduler
```

## 5. Estructura del proyecto

```
proyecto-datamart-eft/
├── README.md
├── requirements.txt
├── .env.example              # variables de entorno (copiar a .env si quieres cambiar algo)
├── data/
│   └── Online_Retail.xlsx    # archivo origen
├── db/
│   └── schema.sql            # esquema de la base destino
├── src/
│   ├── config.py             # configuración centralizada (paths, batch size)
│   ├── lector.py             # ingesta (SÍNCRONO) — lee y genera lotes
│   ├── validador.py          # calidad de datos + reglas de negocio
│   ├── procesador.py         # transformaciones + enmascaramiento (ética)
│   ├── cargador.py           # carga a SQLite (bulk insert = optimización)
│   ├── async_tasks.py        # tareas ASÍNCRONAS en paralelo (reporte/log/notificación)
│   ├── scheduler.py          # calendarización (equivalente a cron)
│   └── pipeline.py           # orquestador principal
├── dashboard/
│   └── app.py                # visualización (Streamlit)
└── logs/                     # logs de ejecución + reportes JSON (se generan solos)
```

## 6. Arquitectura y paradigma aplicado

```
Online_Retail.xlsx
        │
        ▼
 [Lector] (SÍNCRONO, por lotes)
        │
        ▼
 [Validador] — clasifica cada fila
        │
   ┌────┼────────────────┐
   ▼    ▼                ▼
Válidos  Devoluciones   Rechazados
(venta)  (Qty<0 o 'C')  (con causa)
   │        │                │
   ▼        ▼                ▼
[Procesador] — transforma + enmascara customer_id
   │        │                │
   ▼        ▼                ▼
tabla     tabla           tabla
ventas    devoluciones    rechazos     (SQLite)
   │
   ▼
[Tareas async en paralelo] → reporte JSON + log archivado + notificación
   │
   ▼
[Dashboard Streamlit] ← lee datamart.db
```

**Paradigma:** ETL por lotes (Batch) con separación de responsabilidades
tipo microservicios (cada módulo de `src/` hace una sola cosa), combinado
con una fase asíncrona para las tareas no críticas.

## 7. Datos de prueba para la defensa (casos límite)

Puedes armar un `datos_prueba.csv` pequeño con estas filas para demostrar
en vivo cada regla del validador:

| Caso | Fila de ejemplo | Resultado esperado |
|---|---|---|
| Válido | InvoiceNo=999901, Quantity=5, UnitPrice=2.5, CustomerID=12345 | → tabla `ventas` |
| Devolución | InvoiceNo=C999902, Quantity=-3 | → tabla `devoluciones` |
| Cliente no identificado | CustomerID vacío | → `rechazos`, causa `cliente_no_identificado` |
| Duplicado | misma fila repetida dos veces | → la segunda va a `rechazos`, causa `duplicado` |
| Precio inválido | UnitPrice=0 | → `rechazos`, causa `precio_invalido` |

Ejecuta luego: `python -m src.pipeline --file datos_prueba.csv` para
mostrar el flujo completo con un volumen pequeño y controlado.
