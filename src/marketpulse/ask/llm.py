"""Proveedores LLM intercambiables: Snowflake Cortex, API compatible OpenAI, Anthropic.

Cortex: el dato no sale de Snowflake y no hace falta otra API key; se paga en créditos.
OpenAI/Anthropic: requiere LLM_API_KEY (GitHub Secret / .env), el esquema (no los datos)
viaja al proveedor externo.
"""

from __future__ import annotations

import re

import requests

from marketpulse.config import env

SYSTEM_PROMPT = """Eres un asistente que traduce preguntas en español a UNA consulta SQL
de Snowflake. Reglas:
- Devuelve SOLO el SQL, sin explicación ni markdown.
- Solo SELECT. Solo puedes usar estas tablas (con su esquema):
{schema}
- Usa LIMIT 100 salvo que se pida otro número menor.
- Si la pregunta no se puede responder con estas tablas, devuelve: SELECT 'NO_DISPONIBLE' AS aviso
"""


def extract_sql(text: str) -> str:
    """Quita bloques ```sql ...``` si el modelo los añade."""
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    return (m.group(1) if m else text).strip().rstrip(";")


def generate_sql(question: str, schema_context: str, conn=None) -> str:
    provider = (env("LLM_PROVIDER", "cortex") or "cortex").lower()
    system = SYSTEM_PROMPT.format(schema=schema_context)
    if provider == "cortex":
        if conn is None:
            raise RuntimeError("Cortex necesita una conexión Snowflake")
        prompt = f"{system}\n\nPregunta: {question}\nSQL:"
        cur = conn.cursor()
        # Parámetros enlazados: la pregunta del usuario nunca se concatena en el SQL.
        cur.execute(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s)",
            (env("CORTEX_MODEL", "mistral-large2"), prompt),
        )
        return extract_sql(cur.fetchone()[0])
    key = env("LLM_API_KEY", required=True)
    model = env("LLM_MODEL", "gpt-4o-mini")
    if provider == "openai":  # cualquier API compatible OpenAI (OpenAI, Groq, Ollama...)
        base = env("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        r = requests.post(
            f"{base}/chat/completions",
            timeout=60,
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": question},
                ],
            },
        )
        r.raise_for_status()
        return extract_sql(r.json()["choices"][0]["message"]["content"])
    if provider == "anthropic":
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            timeout=60,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            json={
                "model": model,
                "max_tokens": 800,
                "system": system,
                "messages": [{"role": "user", "content": question}],
            },
        )
        r.raise_for_status()
        return extract_sql(r.json()["content"][0]["text"])
    raise ValueError(f"LLM_PROVIDER desconocido: {provider}")
