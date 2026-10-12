"""Fuente principal: yfinance (API no oficial de Yahoo Finance, gratis, con retraso)."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from marketpulse.extractors.base import DIVIDEND_COLUMNS, PRICE_COLUMNS, PriceExtractor


class YFinanceExtractor(PriceExtractor):
    name = "yfinance"

    def fetch_prices(self, ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        import yfinance as yf  # import perezoso: no se requiere para los tests

        # end es exclusivo en yfinance -> sumamos un día. auto_adjust=False para
        # conservar Close y Adj Close por separado.
        hist = yf.Ticker(ticker).history(
            start=start, end=end + dt.timedelta(days=1), auto_adjust=False, actions=False
        )
        if hist.empty:
            return pd.DataFrame(columns=PRICE_COLUMNS)
        hist = hist.reset_index()
        df = pd.DataFrame(
            {
                "ticker": ticker,
                "trade_date": pd.to_datetime(hist["Date"]).dt.date,
                "open": hist["Open"],
                "high": hist["High"],
                "low": hist["Low"],
                "close": hist["Close"],
                "adj_close": hist.get("Adj Close", hist["Close"]),
                "volume": hist["Volume"].astype("int64"),
                "source": self.name,
            }
        )
        return self.validate_prices(df)

    def fetch_dividends(self, ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        import yfinance as yf

        divs = yf.Ticker(ticker).dividends
        if divs is None or divs.empty:
            return pd.DataFrame(columns=DIVIDEND_COLUMNS)
        df = divs.reset_index()
        df.columns = ["ex_date", "amount"]
        df["ex_date"] = pd.to_datetime(df["ex_date"]).dt.date
        df = df[(df["ex_date"] >= start) & (df["ex_date"] <= end)]
        df["ticker"] = ticker
        df["source"] = self.name
        return df[DIVIDEND_COLUMNS]
