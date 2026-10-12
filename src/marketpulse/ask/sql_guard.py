"""Validación de SQL generado por el LLM (Módulo 4). Defensa en profundidad:

1. Esta capa (sqlglot): solo UN statement, solo SELECT, sin DML/DDL anidado,
   solo tablas de la allowlist, LIMIT forzado.
2. Snowflake: rol de solo lectura con acceso únicamente a MARTS (infra/snowflake).
3. Timeout de sesión (STATEMENT_TIMEOUT_IN_SECONDS).
4. UI: se muestra el SQL antes de ejecutarlo.

Nunca confiamos en el LLM: el prompt puede ser manipulado (prompt injection).
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

DEFAULT_ALLOWED_TABLES = frozenset(
    {
        "DIM_TICKER",
        "FCT_DAILY_METRICS",
        "MART_LATEST_METRICS",
        "FCT_PORTFOLIO_DAILY",
        "MART_PORTFOLIO_SUMMARY",
        "FCT_DIVIDENDS",
    }
)

# Nodos prohibidos en cualquier parte del árbol. Se buscan por nombre de clase
# para ser robustos entre versiones de sqlglot (algunas clases cambian de nombre).
FORBIDDEN_NODE_NAMES = frozenset(
    {
        "Insert",
        "Update",
        "Delete",
        "Merge",
        "Drop",
        "Create",
        "Alter",
        "AlterTable",
        "TruncateTable",
        "Command",
        "Grant",
        "Revoke",
        "Use",
        "Set",
        "Copy",
        "Into",
        "Transaction",
        "Commit",
        "Rollback",
        "LoadData",
        "Describe",
        "Pragma",
    }
)
ALLOWED_ROOTS = (exp.Select, exp.Union, exp.Intersect, exp.Except)
# Funciones de Snowflake con efectos secundarios o que exponen metadatos del sistema.
FORBIDDEN_FUNCTION_PREFIXES = ("SYSTEM$", "SYSTEM_")


class UnsafeSQLError(ValueError):
    """El SQL no pasa las reglas de seguridad."""


@dataclass(frozen=True)
class GuardConfig:
    allowed_tables: frozenset[str] = DEFAULT_ALLOWED_TABLES
    allowed_schema: str = "MARTS"
    max_limit: int = 200


def validate_sql(sql: str, cfg: GuardConfig | None = None) -> str:
    """Devuelve SQL seguro (normalizado, con LIMIT) o lanza UnsafeSQLError."""
    cfg = cfg or GuardConfig()
    if not sql or not sql.strip():
        raise UnsafeSQLError("SQL vacío")
    try:
        statements = [s for s in sqlglot.parse(sql, read="snowflake") if s is not None]
    except ParseError as exc:
        raise UnsafeSQLError(f"SQL no parseable: {exc}") from exc
    if len(statements) != 1:
        raise UnsafeSQLError(f"Se permite exactamente 1 sentencia (recibidas {len(statements)})")
    tree = statements[0]

    if not isinstance(tree, ALLOWED_ROOTS):
        raise UnsafeSQLError(f"Solo se permiten SELECT (recibido {type(tree).__name__})")

    for node in tree.walk():
        name = type(node).__name__
        if name in FORBIDDEN_NODE_NAMES:
            raise UnsafeSQLError(f"Operación no permitida: {name}")
        if isinstance(node, exp.Func):
            fname = (
                node.sql_name() if not isinstance(node, exp.Anonymous) else str(node.this)
            ).upper()
            if fname.startswith(FORBIDDEN_FUNCTION_PREFIXES):
                raise UnsafeSQLError(f"Función no permitida: {fname}")

    cte_names = {cte.alias_or_name.upper() for cte in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        tname = table.name.upper()
        if not tname:  # p. ej. funciones de tabla como FLATTEN/TABLE(...)
            raise UnsafeSQLError("Funciones de tabla no permitidas")
        if tname in cte_names and not table.db:
            continue
        if tname not in cfg.allowed_tables:
            raise UnsafeSQLError(f"Tabla no permitida: {tname}")
        if table.db and table.db.upper() != cfg.allowed_schema.upper():
            raise UnsafeSQLError(f"Esquema no permitido: {table.db}")
        if table.catalog:
            raise UnsafeSQLError("No se permite referenciar otra base de datos")

    tree = _force_limit(tree, cfg.max_limit)
    # comments=False elimina comentarios: nada oculto llega a Snowflake.
    return tree.sql(dialect="snowflake", comments=False)


def _force_limit(tree: exp.Expression, max_limit: int) -> exp.Expression:
    """Añade LIMIT si falta o lo reduce si supera el máximo."""
    if isinstance(tree, exp.Select):
        current = tree.args.get("limit")
        if current is not None:
            try:
                value = int(current.expression.name)
            except (ValueError, AttributeError):
                value = max_limit + 1  # LIMIT no literal: lo reemplazamos
            if value <= max_limit:
                return tree
        return tree.limit(max_limit, copy=True)
    # UNION/INTERSECT/EXCEPT: envolvemos en un SELECT externo.
    return exp.select("*").from_(tree.subquery("q")).limit(max_limit)
