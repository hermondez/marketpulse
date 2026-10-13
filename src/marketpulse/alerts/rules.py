"""Reglas de alertas: funciones PURAS (fila de métricas -> lista de alertas).

Redacción pensada para un inversor principiante, en español simple. Cada alerta explica:
1) qué pasó, 2) qué significa, 3) por qué puede importar y 4) las dos lecturas habituales.
Siempre neutral: nunca "compra", "vende" ni "oportunidad" (hay un test que lo verifica).
El aviso legal completo vive en README/docs, no se repite en cada mensaje.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


def label(row: dict[str, Any]) -> str:
    """'Apple (AAPL)'. Usa display_name (watchlist) o name (dim_ticker) si existen."""
    t = row["ticker"]
    name = row.get("display_name") or row.get("name")
    return f"{name} ({t})" if name and name != t else t


def _is_bond(row: dict[str, Any]) -> bool:
    return row.get("asset_class") == "bonds"


def _context(row: dict[str, Any]) -> str:
    ctx = row.get("context")
    return f"\n📌 <i>{ctx}</i>" if ctx else ""


def _price(row: dict[str, Any]) -> str:
    close = _f(row, "close")
    return "" if close is None else f" Cerró en ${close:,.2f}."


def _daily_move(row: dict[str, Any], ret: float, threshold: float) -> str:
    up = ret > 0
    emoji = "📈" if up else "📉"
    verbo = "subió" if up else "bajó"
    bond_note = (
        "\n• En un fondo de bonos, un movimiento así es poco común: suele estar ligado a cambios "
        "en las tasas de interés o en las expectativas de inflación."
        if _is_bond(row)
        else ""
    )
    return (
        f"{emoji} <b>{label(row)}</b> {verbo} <b>{ret * 100:+.2f}%</b> hoy.{_price(row)}\n"
        f"<b>Qué significa:</b> fue un día de movimiento grande (tu aviso salta a partir de "
        f"±{threshold:g}%). Un solo día dice poco sobre el largo plazo.\n"
        f"<b>Por qué puede importar:</b> los movimientos fuertes suelen venir de noticias "
        f"(resultados, datos económicos, tasas de interés).{bond_note}\n"
        f"<b>Lecturas habituales:</b> algunos lo ven como ruido normal del mercado; otros como "
        f"señal de que algo cambió. Vale la pena buscar la noticia detrás."
        f"{_context(row)}"
    )


def _sma_cross(row: dict[str, Any], sma: float, up: bool) -> str:
    if up:
        head = f"⬆️ <b>{label(row)}</b> cerró por <b>encima</b> de su promedio de 200 días."
        meaning = (
            "el precio de hoy superó el precio promedio de los últimos ~10 meses, "
            "después de estar por debajo."
        )
        readings = (
            "algunos lo interpretan como el inicio de una tendencia al alza; otros recuerdan "
            "que estos cruces fallan a menudo y el precio puede volver a bajar pronto."
        )
    else:
        head = f"⬇️ <b>{label(row)}</b> cerró por <b>debajo</b> de su promedio de 200 días."
        meaning = (
            "el precio de hoy quedó por debajo del precio promedio de los últimos ~10 meses, "
            "después de estar por encima."
        )
        readings = (
            "algunos lo ven como señal de debilidad o cambio de tendencia; otros como una "
            "caída temporal dentro de una tendencia más larga."
        )
    return (
        f"{head}{_price(row)} Promedio 200 días: ${sma:,.2f}.\n"
        f"<b>Qué significa:</b> {meaning}\n"
        f"<b>Por qué puede importar:</b> el promedio de 200 días es una referencia muy seguida "
        f"para ver la tendencia de largo plazo.\n"
        f"<b>Lecturas habituales:</b> {readings}"
        f"{_context(row)}"
    )


def _rsi(row: dict[str, Any], rsi: float, high: bool) -> str:
    if high:
        head = f"🔥 <b>{label(row)}</b> tiene el RSI en <b>{rsi:.0f}</b> (zona alta, más de 70)."
        meaning = (
            "en las últimas ~3 semanas los días de subida pesaron mucho más que los de bajada."
        )
        readings = (
            "algunos lo ven como 'se calentó demasiado' y esperan una pausa; otros como señal "
            "de fuerza, porque en tendencias fuertes el RSI puede quedarse alto semanas."
        )
    else:
        head = f"🧊 <b>{label(row)}</b> tiene el RSI en <b>{rsi:.0f}</b> (zona baja, menos de 30)."
        meaning = (
            "en las últimas ~3 semanas los días de bajada pesaron mucho más que los de subida."
        )
        readings = (
            "algunos lo ven como 'cayó demasiado rápido' y esperan un rebote; otros como señal "
            "de debilidad que puede continuar. Revisa por qué ha bajado."
        )
    return (
        f"{head}{_price(row)}\n"
        f"<b>Qué significa:</b> el RSI va de 0 a 100 y mide la fuerza de los movimientos "
        f"recientes: {meaning}\n"
        f"<b>Por qué puede importar:</b> indica movimientos rápidos, que a veces se moderan "
        f"después. No predice qué pasará.\n"
        f"<b>Lecturas habituales:</b> {readings}"
        f"{_context(row)}"
    )


def _near_low(row: dict[str, Any], dist: float) -> str:
    bond_note = (
        "\n• En bonos, acercarse al mínimo del año suele coincidir con tasas de interés al alza."
        if _is_bond(row)
        else ""
    )
    low = _f(row, "low_52w")
    low_txt = f" (mínimo: ${low:,.2f})" if low is not None else ""
    return (
        f"🔻 <b>{label(row)}</b> está a solo <b>{dist * 100:.1f}%</b> de su precio más bajo "
        f"del último año{low_txt}.{_price(row)}\n"
        f"<b>Qué significa:</b> el precio está cerca del punto más bajo de las últimas 52 "
        f"semanas.\n"
        f"<b>Por qué puede importar:</b> muestra que ha tenido un periodo flojo; si rompe ese "
        f"mínimo, marcaría un nuevo mínimo anual.{bond_note}\n"
        f"<b>Lecturas habituales:</b> algunos lo ven como un precio bajo comparado con el "
        f"último año; otros como señal de debilidad. Revisa por qué bajó."
        f"{_context(row)}"
    )


def evaluate(row: dict[str, Any], cfg: dict[str, Any]) -> list[Alert]:
    t, d = row["ticker"], str(row["trade_date"])
    alerts: list[Alert] = []

    ret = _f(row, "daily_return")
    c = cfg.get("daily_move", {})
    threshold = c.get("threshold_pct", 2)
    if c.get("enabled") and ret is not None and abs(ret) * 100 > threshold:
        alerts.append(Alert("daily_move", t, d, _daily_move(row, ret, threshold)))

    # Comparamos precio AJUSTADO con la SMA (también calculada sobre precio ajustado).
    keys = ("adj_close", "sma_200", "prev_adj_close", "prev_sma_200")
    close, sma, pc, psma = (_f(row, k) for k in keys)
    if cfg.get("sma200_cross", {}).get("enabled") and None not in (close, sma, pc, psma):
        if pc <= psma and close > sma:
            alerts.append(Alert("sma200_cross", t, d, _sma_cross(row, sma, up=True)))
        elif pc >= psma and close < sma:
            alerts.append(Alert("sma200_cross", t, d, _sma_cross(row, sma, up=False)))

    rsi = _f(row, "rsi_14")
    c = cfg.get("rsi_extreme", {})
    if c.get("enabled") and rsi is not None:
        if rsi >= c.get("high", 70):
            alerts.append(Alert("rsi_extreme", t, d, _rsi(row, rsi, high=True)))
        elif rsi <= c.get("low", 30):
            alerts.append(Alert("rsi_extreme", t, d, _rsi(row, rsi, high=False)))

    dist = _f(row, "pct_from_52w_low")
    c = cfg.get("near_52w_low", {})
    if c.get("enabled") and dist is not None and dist * 100 <= c.get("within_pct", 3):
        alerts.append(Alert("near_52w_low", t, d, _near_low(row, dist)))
    return alerts


def format_alert(alert: Alert) -> str:
    return f"🔔 <b>Aviso MarketPulse</b> · {alert.trade_date}\n\n{alert.message}"


def format_daily_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "Sin datos de cierre para hoy."
    lines = [
        f"📊 <b>Resumen del cierre · {rows[0]['trade_date']}</b>",
        "Cómo terminó cada activo hoy (variación frente al cierre anterior):",
        "",
    ]
    rets = []
    for r in sorted(rows, key=lambda x: x["ticker"]):
        ret = _f(r, "daily_return")
        if ret is None:
            emoji, ret_txt = "⚪", "sin dato"
        else:
            rets.append(ret)
            emoji = "🟢" if ret > 0.0005 else "🔴" if ret < -0.0005 else "⚪"
            ret_txt = f"{ret * 100:+.2f}%"
        lines.append(f"{emoji} {label(r)}: ${float(r['close']):,.2f} ({ret_txt})")
    ups = sum(x > 0.0005 for x in rets)
    downs = sum(x < -0.0005 for x in rets)
    if ups > downs:
        mood = "Día mayormente positivo"
    elif downs > ups:
        mood = "Día mayormente negativo"
    else:
        mood = "Día mixto"
    lines += [
        "",
        f"<i>{mood}: {ups} subieron y {downs} bajaron. Un día aislado dice poco; "
        f"lo importante es la tendencia en meses y años.</i>",
    ]
    return "\n".join(lines)


def enrich_rows(rows: list[dict[str, Any]], tickers: list[Any]) -> list[dict[str, Any]]:
    """Añade display_name, context y asset_class desde la watchlist (config/watchlist.yaml)."""
    by_symbol = {t.symbol: t for t in tickers}
    out = []
    for r in rows:
        t = by_symbol.get(r["ticker"])
        extra = (
            {"display_name": t.display_name, "context": t.context, "asset_class": t.asset_class}
            if t
            else {}
        )
        out.append({**r, **extra})
    return out
