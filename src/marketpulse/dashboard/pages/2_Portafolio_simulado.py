import streamlit as st

from marketpulse.config import MARTS_SCHEMA
from marketpulse.dashboard.db import query

st.title("Portafolio simulado")
st.warning("Posiciones HIPOTÉTICAS definidas en un seed de dbt. No es dinero real.")
summary = query(f"SELECT * FROM {MARTS_SCHEMA}.MART_PORTFOLIO_SUMMARY ORDER BY ticker")
st.dataframe(summary, use_container_width=True)
daily = query(
    f"SELECT trade_date, SUM(market_value) AS valor, SUM(cost_basis) AS costo "
    f"FROM {MARTS_SCHEMA}.FCT_PORTFOLIO_DAILY GROUP BY trade_date ORDER BY trade_date"
)
st.line_chart(daily.set_index("trade_date"))
