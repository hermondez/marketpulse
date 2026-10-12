"""Chat: pregunta en español -> SQL (LLM) -> validación -> confirmación -> ejecución.

Protecciones de la página (además de sql_guard + rol de solo lectura + timeout):
- contraseña APP_ASK_PASSWORD (si no existe, la página queda deshabilitada);
- límite de preguntas por sesión (APP_ASK_MAX_QUESTIONS, por defecto 10).
"""

import streamlit as st

from marketpulse.ask.access import (
    DEFAULT_MAX_QUESTIONS,
    ask_enabled,
    check_password,
    remaining_questions,
)
from marketpulse.ask.llm import generate_sql
from marketpulse.ask.schema_context import build_schema_context
from marketpulse.ask.sql_guard import GuardConfig, UnsafeSQLError, validate_sql
from marketpulse.config import MARTS_SCHEMA, REPO_ROOT, env
from marketpulse.snowflake_client import connect

st.title("Pregunta a tus datos")

configured = env("APP_ASK_PASSWORD")
if not ask_enabled(configured):
    st.info(
        "Esta página está desactivada. Para activarla, configura el secret "
        "`APP_ASK_PASSWORD` (y un proveedor LLM). Ver docs/deploy_streamlit_cloud.md."
    )
    st.stop()

if not st.session_state.get("ask_ok"):
    pwd = st.text_input("Contraseña de acceso", type="password")
    if st.button("Entrar"):
        if check_password(pwd, configured):
            st.session_state.ask_ok = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.stop()

max_q = int(env("APP_ASK_MAX_QUESTIONS", str(DEFAULT_MAX_QUESTIONS)))
used = st.session_state.setdefault("ask_used", 0)
left = remaining_questions(used, max_q)
st.caption(
    f"El SQL lo genera un LLM: puede equivocarse. Revísalo antes de ejecutar. "
    f"Preguntas restantes en esta sesión: {left}/{max_q}."
)
cfg = GuardConfig(allowed_schema=MARTS_SCHEMA)


@st.cache_resource
def schema_ctx() -> str:
    return build_schema_context(REPO_ROOT / "dbt" / "target", schema=MARTS_SCHEMA)


if "sql" not in st.session_state:
    st.session_state.sql = None

question = st.chat_input(
    "Ej.: ¿Qué ETF tuvo mayor volatilidad 20d la última semana?", disabled=left == 0
)
if left == 0:
    st.warning("Alcanzaste el límite de preguntas de esta sesión.")
if question and left > 0:
    st.session_state.ask_used = used + 1  # cuenta aunque falle: el LLM ya costó
    st.chat_message("user").write(question)
    try:
        with connect(reader=True, schema=MARTS_SCHEMA, timeout_s=30) as conn:
            raw_sql = generate_sql(question, schema_ctx(), conn)
    except Exception as exc:  # noqa: BLE001 - mostrar error amigable, no traceback
        st.error(f"No se pudo generar el SQL: {type(exc).__name__}")
        st.stop()
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
