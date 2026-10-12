"""Ingesta diaria (Módulo 1): watchlist -> extractor -> Snowflake RAW (MERGE).

Flujo:
1. Si hoy no es día hábil NYSE, termina sin error (salida 0).
2. Por cada ticker descarga OHLCV + dividendos con reintentos (tenacity).
3. Un ticker que falla no tumba el resto; al final, si hubo fallos, salida 1.
4. Carga idempotente vía tabla temporal + MERGE.
"""

from __future__ import annotations

import argparse
import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from marketpulse.config import load_watchlist
from marketpulse.extractors import PriceExtractor, get_extractor
from marketpulse.logging_utils import get_logger
from marketpulse.market_calendar import is_trading_day

log = get_logger(__name__)

PRICES_TABLE = "RAW.PRICES_DAILY"
DIVIDENDS_TABLE = "RAW.DIVIDENDS"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=30), reraise=True)
def _fetch_with_retry(extractor: PriceExtractor, ticker: str, start: dt.date, end: dt.date):
    """3 intentos con backoff exponencial: cubre errores de red/rate-limit transitorios."""
    return extractor.fetch_prices(ticker, start, end), extractor.fetch_dividends(ticker, start, end)


def extract_all(extractor: PriceExtractor, symbols: list[str], start: dt.date, end: dt.date):
    prices, divs, failed = [], [], []
    for sym in symbols:
        try:
            p, d = _fetch_with_retry(extractor, sym, start, end)
            if p.empty:
                # yfinance suele devolver vacío (no excepción) cuando Yahoo cambia algo:
                # lo tratamos como fallo para que CI y el health check se enteren.
                raise ValueError("la fuente devolvió 0 filas de precio")
            log.info("%s: %s filas de precio, %s dividendos", sym, len(p), len(d))
            prices.append(p)
            divs.append(d)
        except Exception as exc:  # noqa: BLE001 - registramos y seguimos
            log.error("Falló %s tras reintentos: %s", sym, exc)
            failed.append(sym)
    p_df = pd.concat(prices, ignore_index=True) if prices else pd.DataFrame()
    d_df = pd.concat(divs, ignore_index=True) if divs else pd.DataFrame()
    return p_df, d_df, failed


def last_completed_session_date(now: dt.datetime | None = None) -> dt.date:
    """Fecha máxima a cargar. Antes de las 16:30 de Nueva York la vela de hoy es
    intradía (incompleta), así que se carga hasta ayer."""
    now = now or dt.datetime.now(ZoneInfo("America/New_York"))
    now_et = now.astimezone(ZoneInfo("America/New_York"))
    if now_et.time() < dt.time(16, 30):
        return now_et.date() - dt.timedelta(days=1)
    return now_et.date()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingesta diaria de precios a Snowflake")
    parser.add_argument("--backfill", action="store_true", help="Carga histórica inicial")
    parser.add_argument("--force", action="store_true", help="Ignora el calendario")
    parser.add_argument("--dry-run", action="store_true", help="No escribe en Snowflake")
    args = parser.parse_args(argv)

    today = last_completed_session_date()
    if not args.force and not args.backfill and not is_trading_day(today):
        log.info("%s no es día hábil NYSE: se omite la ingesta", today)
        return 0

    wl = load_watchlist()
    days = wl.backfill_days if args.backfill else wl.lookback_days
    start = today - dt.timedelta(days=days)
    extractor = get_extractor()
    log.info("Fuente=%s tickers=%s rango=%s..%s", extractor.name, wl.symbols, start, today)

    prices, divs, failed = extract_all(extractor, wl.symbols, start, today)
    if args.dry_run:
        log.info("dry-run: %s precios, %s dividendos", len(prices), len(divs))
    else:
        from marketpulse.snowflake_client import connect, merge_dataframe

        now = pd.Timestamp.utcnow().tz_localize(None)
        with connect() as conn:
            if not prices.empty:
                merge_dataframe(
                    conn, prices.assign(ingested_at=now), PRICES_TABLE, ["ticker", "trade_date"]
                )
            if not divs.empty:
                merge_dataframe(
                    conn, divs.assign(ingested_at=now), DIVIDENDS_TABLE, ["ticker", "ex_date"]
                )
    if failed:
        log.error("Tickers con error: %s", failed)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
