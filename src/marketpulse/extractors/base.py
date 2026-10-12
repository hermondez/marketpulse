"""Interfaz desacoplada de extracción de precios.

Por qué una clase abstracta: yfinance es una librería NO oficial y puede romperse.
Si el resto del código solo conoce `PriceExtractor`, cambiar de fuente es cambiar
una variable de entorno (PRICE_SOURCE), no reescribir la ingesta.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod

import pandas as pd

PRICE_COLUMNS = [
    "ticker",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "source",
]
DIVIDEND_COLUMNS = ["ticker", "ex_date", "amount", "source"]


class PriceExtractor(ABC):
    """Contrato: devolver DataFrames con columnas estándar, sin importar la fuente."""

    name: str = "base"

    @abstractmethod
    def fetch_prices(self, ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        """OHLCV diario en [start, end]. Columnas = PRICE_COLUMNS."""

    @abstractmethod
    def fetch_dividends(self, ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
        """Dividendos (fecha ex) en [start, end]. Columnas = DIVIDEND_COLUMNS."""

    @staticmethod
    def validate_prices(df: pd.DataFrame) -> pd.DataFrame:
        """Validaciones mínimas antes de cargar: columnas, nulos y precios positivos."""
        missing = set(PRICE_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Faltan columnas en precios: {missing}")
        df = df.dropna(subset=["close"])
        df = df[df["close"] > 0]
        return df[PRICE_COLUMNS].drop_duplicates(subset=["ticker", "trade_date"])
