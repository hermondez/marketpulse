"""Tests de seguridad del Módulo 4. Cada caso representa un ataque o error típico."""

import pytest

from marketpulse.ask.sql_guard import GuardConfig, UnsafeSQLError, validate_sql

CFG = GuardConfig(max_limit=100)

MALICIOUS = [
    "DROP TABLE MARTS.FCT_DAILY_METRICS",
    "UPDATE MARTS.DIM_TICKER SET name = 'x'",
    "DELETE FROM MARTS.FCT_DAILY_METRICS",
    "INSERT INTO MARTS.DIM_TICKER VALUES ('X')",
    "MERGE INTO MARTS.DIM_TICKER t USING MARTS.DIM_TICKER s ON t.ticker = s.ticker "
    "WHEN MATCHED THEN DELETE",
    "TRUNCATE TABLE MARTS.DIM_TICKER",
    "CREATE TABLE MARTS.X AS SELECT 1",
    "ALTER TABLE MARTS.DIM_TICKER ADD COLUMN y INT",
    "GRANT SELECT ON MARTS.DIM_TICKER TO ROLE PUBLIC",
    "CALL SYSTEM$WAIT(10)",
    "USE ROLE ACCOUNTADMIN",
    # multi-sentencia
    "SELECT * FROM MARTS.DIM_TICKER; DROP TABLE MARTS.DIM_TICKER",
    "SELECT 1; SELECT 2",
    # trucos con comentarios
    "SELECT * FROM MARTS.DIM_TICKER; -- inofensivo\nDELETE FROM MARTS.DIM_TICKER",
    "/* SELECT */ DROP TABLE MARTS.DIM_TICKER",
    "SELECT * FROM MARTS.DIM_TICKER /* ; */ ; UPDATE MARTS.DIM_TICKER SET name='x'",
    # tablas fuera de la allowlist
    "SELECT * FROM RAW.PRICES_DAILY",
    "SELECT * FROM OPS.ALERTS_LOG",
    "SELECT * FROM INFORMATION_SCHEMA.TABLES",
    "SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY",
    "SELECT * FROM OTHERDB.MARTS.DIM_TICKER",
    "SELECT * FROM RAW.DIM_TICKER",  # nombre permitido pero esquema no
    "SELECT * FROM MARTS.DIM_TICKER WHERE ticker IN (SELECT ticker FROM RAW.PRICES_DAILY)",
    "SELECT * FROM MARTS.DIM_TICKER JOIN STAGING.STG_PRICES_DAILY USING (ticker)",
    # CTE con DML o que esconde tabla prohibida
    "WITH x AS (DELETE FROM MARTS.DIM_TICKER) SELECT * FROM x",
    "WITH x AS (SELECT * FROM RAW.PRICES_DAILY) SELECT * FROM x",
    # funciones de sistema y SELECT INTO
    "SELECT SYSTEM$CANCEL_ALL_QUERIES(1)",
    "SELECT * INTO nueva FROM MARTS.DIM_TICKER",
    # vacío
    "",
    "   ",
]


@pytest.mark.parametrize("sql", MALICIOUS)
def test_rejects_unsafe(sql):
    with pytest.raises(UnsafeSQLError):
        validate_sql(sql, CFG)


def test_allows_simple_select_and_adds_limit():
    out = validate_sql("SELECT ticker, close FROM MARTS.MART_LATEST_METRICS", CFG)
    assert out.upper().endswith("LIMIT 100")


def test_keeps_smaller_limit():
    out = validate_sql("SELECT * FROM MARTS.DIM_TICKER LIMIT 5", CFG)
    assert "LIMIT 5" in out.upper()


def test_reduces_big_limit():
    out = validate_sql("SELECT * FROM MARTS.DIM_TICKER LIMIT 100000", CFG)
    assert "LIMIT 100" in out.upper() and "100000" not in out


def test_allows_unqualified_and_cte():
    sql = (
        "WITH v AS (SELECT ticker, AVG(volatility_20d) AS vol FROM FCT_DAILY_METRICS "
        "GROUP BY ticker) SELECT * FROM v ORDER BY vol DESC"
    )
    out = validate_sql(sql, CFG)
    assert "LIMIT 100" in out.upper()


def test_union_is_wrapped_with_limit():
    sql = "SELECT ticker FROM MARTS.DIM_TICKER UNION ALL SELECT ticker FROM MARTS.FCT_DIVIDENDS"
    out = validate_sql(sql, CFG)
    assert out.upper().endswith("LIMIT 100")


def test_comments_are_stripped():
    out = validate_sql("SELECT ticker /* hola */ FROM MARTS.DIM_TICKER -- fin", CFG)
    assert "/*" not in out and "--" not in out


def test_trailing_semicolon_single_statement_ok():
    assert validate_sql("SELECT * FROM MARTS.DIM_TICKER;", CFG)
