"""Ejecuta las reglas sobre la última fecha de MARTS y envía a Telegram con dedup.

Dedup: antes de enviar se consulta OPS.ALERTS_LOG; tras enviar se inserta la clave.
Así, re-ejecutar el job el mismo día no repite mensajes.
"""

from __future__ import annotations

from marketpulse.alerts.rules import Alert, evaluate, format_alert, format_daily_summary
from marketpulse.alerts.telegram import TelegramClient
from marketpulse.config import MARTS_SCHEMA, load_alerts_config
from marketpulse.logging_utils import get_logger

log = get_logger(__name__)

LATEST_SQL = f"SELECT * FROM {MARTS_SCHEMA}.MART_LATEST_METRICS"


def filter_new(alerts: list[Alert], sent_keys: set[str]) -> list[Alert]:
    return [a for a in alerts if a.key not in sent_keys]


def main() -> int:
    from marketpulse.snowflake_client import connect

    cfg = load_alerts_config()
    tg = TelegramClient()
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(LATEST_SQL)
        cols = [c[0].lower() for c in cur.description]
        rows = [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]
        if not rows:
            log.warning("MART_LATEST_METRICS vacío")
            return 0
        trade_date = str(rows[0]["trade_date"])
        cur.execute("SELECT alert_key FROM OPS.ALERTS_LOG WHERE trade_date = %s", (trade_date,))
        sent = {r[0] for r in cur.fetchall()}

        candidates = [a for r in rows for a in evaluate(r, cfg)]
        if cfg.get("daily_summary", {}).get("enabled"):
            candidates.append(Alert("daily_summary", "ALL", trade_date, format_daily_summary(rows)))
        for alert in filter_new(candidates, sent):
            text = alert.message if alert.rule == "daily_summary" else format_alert(alert)
            tg.send(text)
            cur.execute(
                "INSERT INTO OPS.ALERTS_LOG (alert_key, rule, ticker, trade_date, message) "
                "VALUES (%s, %s, %s, %s, %s)",
                (alert.key, alert.rule, alert.ticker, alert.trade_date, alert.message),
            )
            log.info("Enviada %s", alert.key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
