"""Sección "Tu empresa" del resumen diario (tickers spotlight, p. ej. IBM).

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


def format_section(m: dict[str, Any]) -> str:
    t = m["ticker"]
    lines = [
        f"🏢 <b>Tu empresa: {t}</b> · cierre {m['trade_date']}",
        f"• Cierre: ${m['close']:,.2f} ({_pct(m['day_pct'])} en el día)",
        f"• En lo que va del mes: {_pct(m['mtd_pct'])}",
        f"• En lo que va del año: {_pct(m['ytd_pct'])}",
        f"• Frente al máximo de 52 semanas (${m['high_52w']:,.2f}): {_pct(m['from_high_pct'])}",
        f"• Frente al mínimo de 52 semanas (${m['low_52w']:,.2f}): {_pct(m['from_low_pct'])}",
        "",
        "<i>Cómo leerlo: el % del mes y del año compara el precio de hoy con el último cierre "
        "antes de que empezara ese periodo. El máximo y el mínimo de 52 semanas muestran en qué "
        "parte de su rango del último año está el precio.</i>",
        "<i>Es una sola empresa, así que se mueve más que un fondo diversificado. Si además "
        "trabajas ahí, tu sueldo y esta acción dependen de lo mismo: tenlo presente.</i>",
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
