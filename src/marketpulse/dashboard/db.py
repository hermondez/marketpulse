"""Helpers de datos para Streamlit. Caché de 10 min para no despertar el warehouse
en cada clic (cada consulta cuesta créditos si el warehouse está suspendido)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from marketpulse.snowflake_client import connect


@st.cache_data(ttl=600, show_spinner="Consultando Snowflake...")
def query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        df = cur.fetch_pandas_all()
    df.columns = [c.lower() for c in df.columns]
    # Snowflake NUMBER(p,s) llega como Decimal (dtype object) y los gráficos de
    # Streamlit lo tratan como texto: convertimos a float las columnas decimales.
    from decimal import Decimal

    for col in df.columns:
        if df[col].dtype == object and df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df
