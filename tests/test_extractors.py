import datetime as dt

import pandas as pd
import pytest

from marketpulse.extractors import get_extractor
from marketpulse.extractors.base import PRICE_COLUMNS, PriceExtractor
from marketpulse.extractors.stooq_extractor import StooqExtractor
from marketpulse.extractors.yfinance_extractor import YFinanceExtractor
from marketpulse.ingestion.run_ingestion import extract_all

CSV = "Date,Open,High,Low,Close,Volume\n2026-10-08,1,2,0.5,1.5,100\n2026-10-09,1.5,2,1,1.8,200\n"


def test_factory_by_config(monkeypatch):
    assert isinstance(get_extractor("yfinance"), YFinanceExtractor)
    monkeypatch.setenv("PRICE_SOURCE", "stooq")
    assert isinstance(get_extractor(), StooqExtractor)
    with pytest.raises(ValueError):
        get_extractor("bloomberg")


def test_stooq_parse():
    df = StooqExtractor().parse_csv("VOO", CSV)
    assert list(df.columns) == PRICE_COLUMNS
    assert len(df) == 2 and df["source"].eq("stooq").all()


def test_stooq_no_data():
    with pytest.raises(ValueError):
        StooqExtractor().parse_csv("XXX", "No data")


class FlakyExtractor(PriceExtractor):
    """Falla siempre en BAD: la ingesta debe seguir con los demás tickers."""

    name = "fake"

    def fetch_prices(self, ticker, start, end):
        if ticker == "BAD":
            raise ConnectionError("boom")
        return StooqExtractor().parse_csv(ticker, CSV)

    def fetch_dividends(self, ticker, start, end):
        return pd.DataFrame(columns=["ticker", "ex_date", "amount", "source"])


def test_extract_all_isolates_failures(monkeypatch):
    # Sin esperas de tenacity en el test
    import marketpulse.ingestion.run_ingestion as ri

    monkeypatch.setattr(ri._fetch_with_retry.retry, "wait", lambda *_a, **_k: 0)
    p, _d, failed = extract_all(
        FlakyExtractor(), ["VOO", "BAD"], dt.date(2026, 10, 1), dt.date(2026, 10, 9)
    )
    assert failed == ["BAD"] and set(p["ticker"]) == {"VOO"}


def test_last_completed_session_excludes_intraday():
    from zoneinfo import ZoneInfo

    from marketpulse.ingestion.run_ingestion import last_completed_session_date

    ny = ZoneInfo("America/New_York")
    assert last_completed_session_date(dt.datetime(2026, 10, 12, 10, 0, tzinfo=ny)) == dt.date(
        2026, 10, 11
    )
    assert last_completed_session_date(dt.datetime(2026, 10, 12, 18, 0, tzinfo=ny)) == dt.date(
        2026, 10, 12
    )


def test_empty_source_counts_as_failure(monkeypatch):
    import marketpulse.ingestion.run_ingestion as ri

    class Empty(FlakyExtractor):
        def fetch_prices(self, ticker, start, end):
            return pd.DataFrame(columns=PRICE_COLUMNS)

    monkeypatch.setattr(ri._fetch_with_retry.retry, "wait", lambda *_a, **_k: 0)
    _p, _d, failed = extract_all(Empty(), ["VOO"], dt.date(2026, 10, 1), dt.date(2026, 10, 9))
    assert failed == ["VOO"]
