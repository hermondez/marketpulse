import datetime as dt

from marketpulse.health.checks import check_freshness, check_volume
from marketpulse.health.run_results_parser import parse_run_results
from marketpulse.market_calendar import is_trading_day
from marketpulse.snowflake_client import build_merge_sql


def test_merge_sql_is_idempotent_upsert():
    sql = build_merge_sql(
        "RAW.PRICES_DAILY", "STG", ["TICKER", "TRADE_DATE"], ["TICKER", "TRADE_DATE", "CLOSE"]
    )
    assert "ON t.TICKER = s.TICKER AND t.TRADE_DATE = s.TRADE_DATE" in sql
    assert "UPDATE SET t.CLOSE = s.CLOSE" in sql
    assert "t.TICKER = s.TICKER," not in sql.split("UPDATE SET")[1]


def test_parse_run_results(run_results_file):
    run, nodes = parse_run_results(run_results_file)
    assert run["status"] == "failed" and run["n_errors"] == 1 and run["command"] == "build"
    assert nodes[0]["resource_type"] == "model" and nodes[1]["failures"] == 4


def test_freshness_and_volume():
    today = dt.date(2026, 10, 12)
    assert check_freshness(dt.date(2026, 10, 9), today, 4) is None
    assert "desactualizados" in check_freshness(dt.date(2026, 10, 1), today, 4)
    assert check_freshness(None, today, 4)
    assert check_volume(3, 5) and check_volume(8, 5) is None


def test_calendar_holidays():
    assert is_trading_day(dt.date(2026, 10, 9)) is True  # viernes normal
    assert is_trading_day(dt.date(2026, 12, 25)) is False  # Navidad
    assert is_trading_day(dt.date(2026, 11, 26)) is False  # Thanksgiving
    assert is_trading_day(dt.date(2026, 10, 10)) is False  # sábado
