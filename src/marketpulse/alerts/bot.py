"""Bot interactivo opcional (long polling). Responde SOLO al chat_id configurado.

Diseño: el flujo principal es "push-only" (GitHub Actions envía mensajes y termina).
Este proceso de polling es opcional porque requiere un servidor encendido 24/7
(ver crítica en README). Comandos: /ayuda, /resumen.
"""

from __future__ import annotations

from marketpulse.alerts.rules import format_daily_summary
from marketpulse.alerts.telegram import TelegramClient
from marketpulse.config import MARTS_SCHEMA
from marketpulse.logging_utils import get_logger

log = get_logger(__name__)

HELP = "Comandos: /resumen (último cierre), /ayuda. Herramienta educativa, sin asesoría."


def handle(text: str) -> str:
    cmd = (text or "").strip().split()[0].lower() if text else ""
    if cmd == "/resumen":
        from marketpulse.snowflake_client import connect

        with connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT ticker, trade_date, close, daily_return "
                f"FROM {MARTS_SCHEMA}.MART_LATEST_METRICS"
            )
            cols = [c[0].lower() for c in cur.description]
            rows = [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]
        return format_daily_summary(rows)
    return HELP


def main() -> int:
    tg = TelegramClient()
    offset = None
    log.info("Bot en marcha (polling). Ctrl+C para salir.")
    while True:
        for upd in tg.get_updates(offset=offset):
            offset = upd["update_id"] + 1
            msg = upd.get("message") or {}
            chat_id = (msg.get("chat") or {}).get("id")
            if not tg.is_authorized(chat_id):
                log.warning("Mensaje ignorado de chat no autorizado: %s", chat_id)
                continue  # silencio total: no confirmamos que el bot existe
            tg.send(handle(msg.get("text", "")))


if __name__ == "__main__":
    raise SystemExit(main())
