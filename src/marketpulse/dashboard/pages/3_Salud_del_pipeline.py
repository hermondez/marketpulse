import streamlit as st

from marketpulse.dashboard.db import query

st.title("Salud del pipeline")
runs = query("SELECT * FROM OPS.DBT_RUNS ORDER BY generated_at DESC LIMIT 50")
fresh = query(
    "SELECT MAX(trade_date) AS ultimo_dia, COUNT(DISTINCT ticker) AS tickers "
    "FROM RAW.PRICES_DAILY"
)
c1, c2, c3 = st.columns(3)
if not runs.empty:
    last = runs.iloc[0]
    c1.metric("Última corrida dbt", "✅ OK" if last["status"] == "success" else "❌ Falló")
    c2.metric("Errores", int(last["n_errors"]))
c3.metric("Último día con datos", str(fresh["ultimo_dia"].iloc[0]) if not fresh.empty else "n/d")
st.subheader("Historial de corridas")
st.dataframe(runs, use_container_width=True)
st.subheader("Nodos fallidos / más lentos (última corrida build/run/test)")
nodes = query(
    "SELECT name, resource_type, status, execution_time_s, message FROM OPS.DBT_NODE_RESULTS "
    "WHERE run_id = (SELECT run_id FROM OPS.DBT_RUNS WHERE command IN ('build', 'run', 'test') "
    "ORDER BY generated_at DESC LIMIT 1) "
    "ORDER BY (status IN ('error','fail')) DESC, execution_time_s DESC"
)
st.dataframe(nodes, use_container_width=True)
