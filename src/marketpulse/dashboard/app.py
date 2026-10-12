"""Portada del dashboard. Ejecutar: `streamlit run src/marketpulse/dashboard/app.py`."""

import streamlit as st

st.set_page_config(page_title="MarketPulse", page_icon="📈", layout="wide")
st.title("📈 MarketPulse")
st.markdown(
    """
Herramienta **educativa** con datos públicos (con retraso) y un portafolio **simulado**.

**No es asesoría financiera.** No hay conexión con brokers ni dinero real.

Páginas:
1. **Mercado**: precios e indicadores de la watchlist.
2. **Portafolio simulado**: valor y rendimiento de posiciones hipotéticas.
3. **Salud del pipeline**: historial de corridas dbt y estado actual.
4. **Pregunta a tus datos**: preguntas en español convertidas a SQL (solo lectura).
"""
)
