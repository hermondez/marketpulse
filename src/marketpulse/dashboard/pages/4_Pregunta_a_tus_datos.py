"""Chat: pregunta en español -> SQL (LLM) -> validación -> confirmación -> ejecución."""

import streamlit as st

from marketpulse.ask.llm import generate_sql
from marketpulse.ask.schema_context import build_schema_context
from marketpulse.ask.sql_guard import GuardConfig, UnsafeSQLError, validate_sql
from marketpulse.config import MARTS_SCHEMA, REPO_ROOT
from marketpulse.snowflake_client import connect

st.title("Pregunta a tus datos")
st.caption("El SQL lo genera un LLM: puede equivocarse. Revísalo antes de ejecutar.")
cfg = GuardConfig(allowed_schema=MARTS_SCHEMA)


@st.cache_resource
def schema_ctx() -> str:
    return build_schema_context(REPO_ROOT / "dbt" / "target", schema=MARTS_SCHEMA)


if "sql" not in st.session_state:
    st.session_state.sql = None

question = st.chat_input("Ej.: ¿Qué ETF tuvo mayor volatilidad 20d la última semana?")
if question:
    st.chat_message("user").write(question)
    with connect(reader=True, schema=MARTS_SCHEMA, timeout_s=30) as conn:
        raw_sql = generate_sql(question, schema_ctx(), conn)
    try:
        st.session_state.sql = validate_sql(raw_sql, cfg)
    except UnsafeSQLError as exc:
        st.session_state.sql = None
        st.error(f"SQL rechazado por seguridad: {exc}")
        st.code(raw_sql, language="sql")

if st.session_state.sql:
    st.code(st.session_state.sql, language="sql")
    if st.button("Ejecutar consulta (solo lectura)"):
        # Rol de solo lectura + timeout 30 s: segunda y tercera capa de defensa.
        with connect(reader=True, schema=MARTS_SCHEMA, timeout_s=30) as conn:
            cur = conn.cursor()
            cur.execute(st.session_state.sql)
            st.dataframe(cur.fetch_pandas_all(), use_container_width=True)
