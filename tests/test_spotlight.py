import datetime as dt

import pandas as pd

from marketpulse.alerts.rules import FORBIDDEN_WORDS
from marketpulse.alerts.spotlight import (
    NY,
    append_spotlight,
    build_spotlight_sections,
    compute_metrics,
    last_completed_date,
)
from marketpulse.config import load_alerts_config, load_watchlist

NOW = dt.datetime(2026, 3, 10, 18, 0, tzinfo=NY)  # martes tras el cierre


def _df(ticker="IBM"):
    days = pd.bdate_range("2025-03-01", "2026-03-11")  # incluye una sesión "futura"
    closes = [100 + i * 0.1 for i in range(len(days))]
    return pd.DataFrame({"ticker": ticker, "trade_date": days.date, "close": closes})


def fake_fetch(ticker, start, end):
    return _df(ticker)


def test_last_completed_date():
    assert last_completed_date(NOW) == dt.date(2026, 3, 10)
    assert last_completed_date(NOW.replace(hour=11)) == dt.date(2026, 3, 9)


def test_metrics_values():
    df = pd.DataFrame(
        {
            "trade_date": [
                dt.date(2025, 6, 2),
                dt.date(2025, 12, 31),
                dt.date(2026, 2, 27),
                dt.date(2026, 3, 2),
                dt.date(2026, 3, 3),
            ],
            "close": [200.0, 100.0, 110.0, 120.0, 132.0],
        }
    )
    m = compute_metrics(df, "IBM")
    assert m["close"] == 132.0
    assert round(m["day_pct"], 4) == 0.10
    assert round(m["mtd_pct"], 4) == 0.20
    assert round(m["ytd_pct"], 4) == 0.32
    assert m["high_52w"] == 200.0 and m["low_52w"] == 100.0
    assert round(m["from_high_pct"], 4) == -0.34


def test_section_content_and_completed_sessions_only():
    secs = build_spotlight_sections(["IBM"], as_of="2026-03-10", fetcher=fake_fetch, now=NOW)
    assert len(secs) == 1
    s = secs[0]
    assert "🏢 <b>Tu empresa: IBM</b>" in s and "2026-03-10" in s and "2026-03-11" not in s
    for k in ("Cierre", "mes", "año", "máximo de 52 semanas", "mínimo de 52 semanas"):
        assert k in s
    assert not any(w in s.lower() for w in FORBIDDEN_WORDS)


def test_fetch_failure_is_skipped():
    def boom(*_):
        raise ConnectionError("yahoo caído")

    assert build_spotlight_sections(["IBM"], fetcher=boom, now=NOW) == []
    empty = build_spotlight_sections(
        ["IBM"], fetcher=lambda *_: pd.DataFrame(columns=["trade_date", "close"]), now=NOW
    )
    assert empty == []
    assert append_spotlight("RESUMEN", []) == "RESUMEN"
    assert append_spotlight("RESUMEN", ["X"]) == "RESUMEN\n\nX"


def test_spotlight_config_not_in_watchlist():
    cfg = load_alerts_config()
    assert "IBM" in cfg.get("spotlight", [])
    assert "IBM" not in {t.symbol for t in load_watchlist().tickers}
