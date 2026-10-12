"""Acceso a Snowflake. Import perezoso del conector para que los tests unitarios
no necesiten Snowflake instalado ni credenciales."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from marketpulse.config import env
from marketpulse.logging_utils import get_logger

log = get_logger(__name__)


@contextmanager
def connect(reader: bool = False, schema: str | None = None, timeout_s: int | None = None):
    """Abre conexión. `reader=True` usa el usuario/rol de SOLO LECTURA (Módulo 4)."""
    import snowflake.connector

    prefix = "SNOWFLAKE_READER_" if reader else "SNOWFLAKE_"
    params: dict[str, Any] = {
        "account": env("SNOWFLAKE_ACCOUNT", required=True),
        "user": env(f"{prefix}USER", required=True),
        "password": env(f"{prefix}PASSWORD", required=True),
        "role": env(f"{prefix}ROLE", required=True),
        "warehouse": env("SNOWFLAKE_WAREHOUSE", "MARKETPULSE_WH"),
        "database": env("SNOWFLAKE_DATABASE", "MARKETPULSE"),
    }
    if schema:
        params["schema"] = schema
    if timeout_s:
        # Timeout a nivel de sesión: Snowflake cancela consultas que lo superen.
        params["session_parameters"] = {"STATEMENT_TIMEOUT_IN_SECONDS": timeout_s}
    conn = snowflake.connector.connect(**params)
    if reader:
        # Las cuentas nuevas activan DEFAULT_SECONDARY_ROLES=('ALL'): sin esto, la sesión
        # heredaría privilegios de otros roles del usuario y el rol de solo lectura no aislaría.
        conn.cursor().execute("USE SECONDARY ROLES NONE")
    try:
        yield conn
    finally:
        conn.close()


def build_merge_sql(target: str, staging: str, keys: list[str], columns: list[str]) -> str:
    """Genera un MERGE idempotente staging -> target.

    Re-ejecutar la carga del mismo día no duplica filas: si la clave existe se
    actualiza, si no, se inserta. Función pura => fácil de testear.
    """
    on = " AND ".join(f"t.{k} = s.{k}" for k in keys)
    non_keys = [c for c in columns if c not in keys]
    update_set = ", ".join(f"t.{c} = s.{c}" for c in non_keys)
    cols = ", ".join(columns)
    vals = ", ".join(f"s.{c}" for c in columns)
    return (
        f"MERGE INTO {target} t USING {staging} s ON {on} "
        f"WHEN MATCHED THEN UPDATE SET {update_set} "
        f"WHEN NOT MATCHED THEN INSERT ({cols}) VALUES ({vals})"
    )


def _insert_rows(conn, df, table: str, chunk: int = 5000) -> None:
    """Carga por INSERT multi-fila con parámetros enlazados (sin stage ni S3).

    Para volúmenes pequeños (miles de filas/día) es suficiente y funciona en redes
    donde el PUT al stage interno (S3/Azure/GCS) está bloqueado.
    """
    cols = list(df.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    # object + None: convierte NaN/NaT y tipos numpy a tipos Python que el conector entiende
    clean = df.astype(object).where(df.notna(), None)
    rows = [
        tuple(v.to_pydatetime() if hasattr(v, "to_pydatetime") else v for v in r)
        for r in clean.itertuples(index=False, name=None)
    ]
    cur = conn.cursor()
    for i in range(0, len(rows), chunk):
        cur.executemany(sql, rows[i : i + chunk])


def merge_dataframe(conn, df, target: str, keys: list[str], method: str | None = None) -> int:
    """Carga un DataFrame en una tabla TEMPORAL y hace MERGE al destino.

    Por qué temp table: el MERGE da idempotencia y la temp table desaparece al cerrar
    la sesión. Métodos de carga (SNOWFLAKE_LOAD_METHOD):
    - insert (defecto): INSERT con binds; simple y sin dependencias de red extra.
    - write_pandas: PUT + COPY vía stage; más rápido con volúmenes grandes, pero requiere
      salida HTTPS al almacenamiento del stage de Snowflake.
    """
    method = (method or env("SNOWFLAKE_LOAD_METHOD", "insert")).lower()
    if df.empty:
        log.info("Nada que cargar en %s", target)
        return 0
    df = df.copy()
    df.columns = [c.upper() for c in df.columns]
    # La temp table se crea en el MISMO esquema que el destino (la conexión no fija esquema).
    schema, table = target.split(".")
    staging = f"{schema}.{table}_STG"
    cur = conn.cursor()
    cur.execute(f"CREATE OR REPLACE TEMPORARY TABLE {staging} LIKE {target}")
    if method == "write_pandas":
        from snowflake.connector.pandas_tools import write_pandas

        # use_logical_type=True: evita que los timestamps de pandas se carguen corruptos.
        write_pandas(
            conn,
            df,
            f"{table}_STG",
            schema=schema,
            auto_create_table=False,
            quote_identifiers=False,
            use_logical_type=True,
        )
    else:
        _insert_rows(conn, df, staging)
    sql = build_merge_sql(target, staging, [k.upper() for k in keys], list(df.columns))
    cur.execute(sql)
    log.info("MERGE en %s: %s filas procesadas (método=%s)", target, len(df), method)
    return len(df)
