"""Reglas de alertas: funciones PURAS (fila de métricas -> lista de alertas).

Redacción: siempre descriptiva ("subió", "cruzó", "está cerca de"). Nunca
"compra", "vende", "oportunidad". Cada mensaje termina con un aviso educativo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DISCLAIMER = "ℹ️ Dato informativo y educativo, no es recomendación de inversión."
FORBIDDEN_WORDS = ("compra", "vende", "comprar", "vender", "oportunidad", "recomiendo")


@dataclass(frozen=True)
class Alert:
    rule: str
    ticker: str
    trade_date: str
    message: str

    @property
    def key(self) -> str:
        """Clave de deduplicación: una alerta por regla/ticker/día."""
        return f"{self.rule}:{self.ticker}:{self.trade_date}"


def _f(row: dict[str, Any], col: str) -> float | None:
    v = row.get(col)
    return None if v is None else float(v)


def evaluate(row: dict[str, Any], cfg: dict[str, Any]) -> list[Alert]:
    t, d = row["ticker"], str(row["trade_date"])
    alerts: list[Alert] = []

    ret = _f(row, "daily_return")
    c = cfg.get("daily_move", {})
    if c.get("enabled") and ret is not None and abs(ret) * 100 > c.get("threshold_pct", 2):
        verbo = "subió" if ret > 0 else "bajó"
        alerts.append(
            Alert(
                "daily_move",
                t,
                d,
                f"{t} {verbo} {ret * 100:+.2f}% hoy (umbral ±{c['threshold_pct']}%).",
            )
        )

    # Comparamos precio AJUSTADO con la SMA (también calculada sobre precio ajustado).
    keys = ("adj_close", "sma_200", "prev_adj_close", "prev_sma_200")
    close, sma, pc, psma = (_f(row, k) for k in keys)
    if cfg.get("sma200_cross", {}).get("enabled") and None not in (close, sma, pc, psma):
        if pc <= psma and close > sma:
            alerts.append(
                Alert(
                    "sma200_cross",
                    t,
                    d,
                    f"{t} cerró por ENCIMA de su media de 200 días ({sma:.2f}).",
                )
            )
        elif pc >= psma and close < sma:
            alerts.append(
                Alert(
                    "sma200_cross",
                    t,
                    d,
                    f"{t} cerró por DEBAJO de su media de 200 días ({sma:.2f}).",
                )
            )

    rsi = _f(row, "rsi_14")
    c = cfg.get("rsi_extreme", {})
    if c.get("enabled") and rsi is not None:
        if rsi >= c.get("high", 70):
            alerts.append(
                Alert(
                    "rsi_extreme",
                    t,
                    d,
                    f"{t} tiene RSI(14) = {rsi:.0f}: subidas recientes fuertes.",
                )
            )
        elif rsi <= c.get("low", 30):
            alerts.append(
                Alert(
                    "rsi_extreme", t, d, f"{t} tiene RSI(14) = {rsi:.0f}: caídas recientes fuertes."
                )
            )

    dist = _f(row, "pct_from_52w_low")
    c = cfg.get("near_52w_low", {})
    if c.get("enabled") and dist is not None and dist * 100 <= c.get("within_pct", 3):
        alerts.append(
            Alert("near_52w_low", t, d, f"{t} está a {dist * 100:.1f}% de su mínimo de 52 semanas.")
        )
    return alerts


def format_alert(alert: Alert) -> str:
    return f"🔔 <b>{alert.ticker}</b> ({alert.trade_date})\n{alert.message}\n{DISCLAIMER}"


def format_daily_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Sin datos de cierre para hoy."
    lines = [f"📊 <b>Resumen de cierre {rows[0]['trade_date']}</b>"]
    for r in sorted(rows, key=lambda x: x["ticker"]):
        ret = _f(r, "daily_return")
        ret_txt = "n/d" if ret is None else f"{ret * 100:+.2f}%"
        lines.append(f"• {r['ticker']}: {float(r['close']):.2f} ({ret_txt})")
    lines.append(DISCLAIMER)
    return "\n".join(lines)
