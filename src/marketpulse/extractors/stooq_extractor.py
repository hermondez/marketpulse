"""Fuente alternativa: Stooq (CSV público). Sin dividendos ni Adj Close separados.

Útil como respaldo si yfinance se rompe. Los tickers de EE.UU. llevan sufijo `.us`.
"""

from __future__ import annotations

import datetime as dt
import io

import pandas as pd
import requests

from marketpulse.extractors.base import DIVIDEND_COLUMNS, PriceExtractor

STOOQ_URL = "https://stooq.com/q/d/l/"


class StooqExtractor(PriceExtractor):
    name = "stooq"

    def __init__(self, session: requests.Session | None = None, timeout: int = 30):
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_prices(self, ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        params = {
            "s": f"{ticker.lower()}.us",
            "i": "d",
            "d1": start.strftime("%Y%m%d"),
            "d2": end.strftime("%Y%m%d"),
        }
        resp = self.session.get(STOOQ_URL, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return self.parse_csv(ticker, resp.text)

    def parse_csv(self, ticker: str, text: str) -> pd.DataFrame:
        """Separado de la llamada HTTP para poder testearlo sin red."""
        if not text.strip() or text.startswith("No data"):
            raise ValueError(f"Stooq no devolvió datos para {ticker}")
        raw = pd.read_csv(io.StringIO(text))
        df = pd.DataFrame(
            {
                "ticker": ticker,
                "trade_date": pd.to_datetime(raw["Date"]).dt.date,
                "open": raw["Open"],
                "high": raw["High"],
                "low": raw["Low"],
                "close": raw["Close"],
                # Stooq ya entrega precios ajustados por splits; no separa dividendos.
                "adj_close": raw["Close"],
                "volume": raw.get("Volume", 0).fillna(0).astype("int64"),
                "source": self.name,
            }
        )
        return self.validate_prices(df)

    def fetch_dividends(self, ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        # Limitación documentada: Stooq no ofrece dividendos en este endpoint.
        return pd.DataFrame(columns=DIVIDEND_COLUMNS)
