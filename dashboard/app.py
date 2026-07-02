"""
dashboard/app.py — Visualización (Bloque: Visualización)
--------------------------------------------------------------------------
Dashboard Streamlit que lee directamente desde la base de datos destino
(datamart.db) y muestra las métricas clave para la toma de decisiones.

Ejecutar con:
    streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

import pandas as pd
import sqlite3
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src import config

st.set_page_config(page_title="DataMart · eCommerce Analytics", layout="wide")


@st.cache_data(ttl=30)
def cargar_tabla(nombre: str) -> pd.DataFrame:
    conn = sqlite3.connect(config.DB_PATH)
    try:
        df = pd.read_sql(f"SELECT * FROM {nombre}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


st.title("DataMart · Panel de Análisis eCommerce")
st.caption("Dataset: Online Retail · Fuente: archivo transaccional cargado vía pipeline ETL")

logs = cargar_tabla("logs_ejecucion")
ventas = cargar_tabla("ventas")
devoluciones = cargar_tabla("devoluciones")
rechazos = cargar_tabla("rechazos")

if logs.empty:
    st.warning("Aún no hay datos cargados. Ejecuta primero: `python -m src.pipeline`")
    st.stop()

ultimo_job = logs.sort_values("id", ascending=False).iloc[0]

st.subheader(f"Última ejecución — job `{ultimo_job['job_id']}`")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Leídos", int(ultimo_job["total_leidos"]))
c2.metric("Ventas cargadas", int(ultimo_job["total_validos"]))
c3.metric("Devoluciones", int(ultimo_job["total_devoluciones"]))
c4.metric("Rechazados", int(ultimo_job["total_rechazados"]))
c5.metric("Tiempo (ms)", f"{ultimo_job['tiempo_ms']:.0f}")

st.divider()

col_izq, col_der = st.columns(2)

with col_izq:
    st.markdown("### Ventas por país (Top 10)")
    if not ventas.empty:
        top_paises = (
            ventas.groupby("country")["total_venta"].sum().sort_values(ascending=False).head(10)
        )
        st.bar_chart(top_paises)
    else:
        st.info("Sin ventas cargadas todavía.")

with col_der:
    st.markdown("### Productos más vendidos (Top 10 por cantidad)")
    if not ventas.empty:
        top_productos = (
            ventas.groupby("description")["quantity"].sum().sort_values(ascending=False).head(10)
        )
        st.bar_chart(top_productos)
    else:
        st.info("Sin ventas cargadas todavía.")

st.markdown("### Evolución de ventas en el tiempo")
if not ventas.empty:
    ventas["invoice_date"] = pd.to_datetime(ventas["invoice_date"])
    serie = ventas.set_index("invoice_date").resample("D")["total_venta"].sum()
    st.line_chart(serie)

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### Causas de rechazo")
    if not rechazos.empty:
        causas = rechazos["causa"].value_counts()
        st.bar_chart(causas)
        st.dataframe(causas.reset_index().rename(columns={"index": "causa", "causa": "cantidad"}))
    else:
        st.info("No hay registros rechazados en la última carga.")

with col_b:
    st.markdown("### Historial de ejecuciones (trazabilidad)")
    st.dataframe(
        logs[[
            "job_id", "fecha_inicio", "total_leidos", "total_validos",
            "total_devoluciones", "total_rechazados", "tiempo_ms",
        ]].sort_values("fecha_inicio", ascending=False),
        use_container_width=True,
    )

st.divider()
st.caption(
    "Nota de ética y privacidad: el identificador de cliente (customer_id) se "
    "almacena y visualiza ENMASCARADO (ej: '17***'). Nunca se expone el dato "
    "completo en el dashboard ni en los reportes generados."
)

with st.expander("Ver muestra de ventas cargadas (customer_id enmascarado)"):
    st.dataframe(ventas.head(50), use_container_width=True)
