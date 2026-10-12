"""Chequeos de frescura y volumen (lógica pura + consultas)."""

from __future__ import annotations

import datetime as dt


def check_freshness(last_date: dt.date | None, today: dt.date, max_days: int) -> str | None:
    """Devuelve mensaje de problema o None si está OK."""
    if last_date is None:
        return "No hay datos en RAW.PRICES_DAILY."
    lag = (today - last_date).days
    if lag > max_days:
        return f"Datos desactualizados: último día {last_date} ({lag} días de retraso)."
    return None


def check_volume(rows_last_day: int, min_rows: int) -> str | None:
    if rows_last_day < min_rows:
        return f"Volumen bajo: solo {rows_last_day} tickers en el último día (mínimo {min_rows})."
    return None
