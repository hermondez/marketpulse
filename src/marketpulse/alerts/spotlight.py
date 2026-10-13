"""Sección spotlight del resumen diario (tickers spotlight, p. ej. IBM).

Los tickers de `config/alerts.yaml` → `spotlight` NO están en la watchlist, el dashboard, el
portafolio ni los seeds de dbt, y sus datos NO se guardan en Snowflake: se descargan al momento
de armar el mensaje con el extractor de yfinance (~1 año de cierres diarios, solo sesiones ya
cerradas). Si la descarga falla, la sección se omite y el resumen sale igual.
Redacción neutral: nunca "compra", "vende" ni "oportunidad".
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from marketpulse.logging_utils import get_logger

log = get_logger(__name__)

NY = ZoneInfo("America/New_York")
CLOSE_CUTOFF = dt.time(16, 15)  # tras el cierre (16:00 ET) con margen
LOOKBACK_DAYS = 380

Fetcher = Callable[[str, dt.date, dt.date], pd.DataFrame]


def last_completed_date(now: dt.datetime | None = None) -> dt.date:
    """Último día cuya sesión ya cerró (hora de Nueva York). Hoy cuenta solo tras 16:15 ET."""
    now = (now or dt.datetime.now(tz=NY)).astimezone(NY)
    return now.date() if now.time() >= CLOSE_CUTOFF else now.date() - dt.timedelta(days=1)


def _default_fetcher(ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    from marketpulse.extractors.yfinance_extractor import YFinanceExtractor

    return YFinanceExtractor().fetch_prices(ticker, start, end)


def compute_metrics(df: pd.DataFrame, ticker: str) -> dict[str, Any] | None:
    """Métricas a partir de cierres diarios (columnas trade_date, close). None si no alcanza."""
    if df is None or df.empty:
        return None
    s = (
        df[["trade_date", "close"]]
        .dropna()
        .assign(trade_date=lambda d: pd.to_datetime(d["trade_date"]).dt.date)
        .drop_duplicates("trade_date")
        .sort_values("trade_date")
    )
    if len(s) < 2:
        return None
    dates, closes = list(s["trade_date"]), [float(x) for x in s["close"]]
    last_d, close, prev = dates[-1], closes[-1], closes[-2]

    def base_before(first_day: dt.date) -> float | None:
        prior = [c for d, c in zip(dates, closes, strict=True) if d < first_day]
        return prior[-1] if prior else None

    mtd_base = base_before(last_d.replace(day=1))
    ytd_base = base_before(last_d.replace(month=1, day=1))
    year_ago = last_d - dt.timedelta(days=365)
    window = [c for d, c in zip(dates, closes, strict=True) if d > year_ago]
    hi, lo = max(window), min(window)
    return {
        "ticker": ticker,
        "trade_date": last_d,
        "close": close,
        "day_pct": close / prev - 1,
        "mtd_pct": None if mtd_base is None else close / mtd_base - 1,
        "ytd_pct": None if ytd_base is None else close / ytd_base - 1,
        "high_52w": hi,
        "low_52w": lo,
        "from_high_pct": close / hi - 1,
        "from_low_pct": close / lo - 1,
    }


def _pct(x: float | None) -> str:
    return "sin dato" if x is None else f"{x * 100:+.2f}%"


def _range_line(m: dict[str, Any]) -> str:
    hi, lo, close = m["high_52w"], m["low_52w"], m["close"]
    if hi <= lo:
        return "Su precio casi no ha cambiado en el último año."
    pos = (close - lo) / (hi - lo)
    if pos < 0.45:
        return "Está más cerca de su precio más bajo del año que del más alto."
    if pos > 0.55:
        return "Está más cerca de su precio más alto del año que del más bajo."
    return "Está más o menos a mitad de camino entre su precio más bajo y el más alto del año."


def format_section(m: dict[str, Any]) -> str:
    below_hi = -m["from_high_pct"] * 100
    above_lo = m["from_low_pct"] * 100
    hi_txt = (
        "hoy está en ese nivel"
        if below_hi < 0.5
        else f"hoy está {below_hi:.0f}% más barata que eso"
    )
    lo_txt = "hoy está en ese nivel" if above_lo < 0.5 else f"hoy está {above_lo:.0f}% por encima"
    lines = [
        f"🏢 <b>{m['ticker']}</b> · cierre {m['trade_date']}",
        f"• Cierre: ${m['close']:,.2f} ({_pct(m['day_pct'])} en el día)",
        f"• En lo que va del mes: {_pct(m['mtd_pct'])}",
        f"• En lo que va del año: {_pct(m['ytd_pct'])}",
        f"• Lo más caro del último año: ${m['high_52w']:,.2f}; {hi_txt}",
        f"• Lo más barato del último año: ${m['low_52w']:,.2f}; {lo_txt}",
        _range_line(m),
        "",
        "<i>Cómo leerlo: el % del mes y del año compara el precio de hoy con el de antes de que "
        "empezara ese periodo.</i>",
        "<i>Es una sola empresa, así que se mueve más que un fondo diversificado.</i>",
    ]
    return "\n".join(lines)


def build_spotlight_sections(
    tickers: list[str],
    as_of: dt.date | str | None = None,
    fetcher: Fetcher | None = None,
    now: dt.datetime | None = None,
) -> list[str]:
    """Una sección por ticker. Cualquier error de descarga/cálculo omite ese ticker (no rompe)."""
    fetcher = fetcher or _default_fetcher
    end = last_completed_date(now)
    if as_of is not None:
        end = min(end, dt.date.fromisoformat(str(as_of)[:10]))
    start = end - dt.timedelta(days=LOOKBACK_DAYS)
    sections = []
    for t in tickers:
        try:
            df = fetcher(t, start, end)
            if df is not None and not df.empty:
                df = df[pd.to_datetime(df["trade_date"]).dt.date <= end]
            m = compute_metrics(df, t)
            if m is None:
                log.warning("Spotlight %s: sin datos suficientes; se omite", t)
                continue
            sections.append(format_section(m))
        except Exception as exc:  # noqa: BLE001 - degradación controlada
            log.warning("Spotlight %s: falló la descarga (%s); se omite", t, type(exc).__name__)
    return sections


def append_spotlight(summary: str, sections: list[str]) -> str:
    return "\n\n".join([summary, *sections]) if sections else summary
