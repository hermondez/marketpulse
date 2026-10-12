"""Chequeo de calendario bursátil (NYSE).

Por qué: el cron de GitHub Actions corre lunes-viernes, pero no sabe de feriados
(Thanksgiving, Navidad...). En lugar de mantener una lista manual, usamos
exchange_calendars, que conoce los feriados oficiales de la NYSE.
"""

from __future__ import annotations

import datetime as dt

from marketpulse.logging_utils import get_logger

log = get_logger(__name__)


def is_trading_day(day: dt.date | None = None, exchange: str = "XNYS") -> bool:
    """True si `day` es sesión de mercado. Si la librería falla, asumimos True
    (preferimos intentar la ingesta y que sea idempotente a perder un día)."""
    day = day or dt.date.today()
    try:
        import exchange_calendars as xcals

        cal = xcals.get_calendar(exchange)
        return bool(cal.is_session(day.isoformat()))
    except Exception as exc:  # noqa: BLE001 - degradación controlada
        log.warning("No se pudo consultar el calendario (%s); se asume día hábil", exc)
        return day.weekday() < 5


def main() -> int:
    """Uso en CI: `python -m marketpulse.market_calendar` -> imprime is_trading_day=true/false."""
    result = is_trading_day()
    print(f"is_trading_day={'true' if result else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
