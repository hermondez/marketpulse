import plotly.graph_objects as go
import streamlit as st

from marketpulse.config import MARTS_SCHEMA
from marketpulse.dashboard.db import query

st.title("Mercado")
latest = query(f"SELECT * FROM {MARTS_SCHEMA}.MART_LATEST_METRICS ORDER BY ticker")
st.dataframe(latest, use_container_width=True)

ticker = st.selectbox("Ticker", latest["ticker"].tolist() if not latest.empty else [])
if ticker:
    df = query(
        f"SELECT trade_date, adj_close, sma_50, sma_200, rsi_14, drawdown "
        f"FROM {MARTS_SCHEMA}.FCT_DAILY_METRICS WHERE ticker = %s ORDER BY trade_date",
        (ticker,),
    )
    fig = go.Figure()
    for col in ("adj_close", "sma_50", "sma_200"):
        fig.add_trace(go.Scatter(x=df["trade_date"], y=df[col], name=col))
    st.plotly_chart(fig, use_container_width=True)
    c1, c2 = st.columns(2)
    c1.line_chart(df.set_index("trade_date")["rsi_14"], height=200)
    c2.area_chart(df.set_index("trade_date")["drawdown"], height=200)
st.caption("Datos con retraso de fuentes gratuitas. Solo fines educativos.")
