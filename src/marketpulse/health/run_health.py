"""Carga run_results.json en OPS y alerta por Telegram si algo falla o está viejo.

Uso: `python -m marketpulse.health.run_health --run-results dbt/target/run_results.json`
Se ejecuta en CI con `if: always()` para registrar también las corridas fallidas.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from marketpulse.config import load_alerts_config
from marketpulse.health.checks import check_freshness, check_volume
from marketpulse.health.run_results_parser import parse_run_results
from marketpulse.logging_utils import get_logger

log = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-results", default="dbt/target/run_results.json")
    p.add_argument("--no-telegram", action="store_true")
    args = p.parse_args(argv)

    import pandas as pd

    from marketpulse.snowflake_client import connect, merge_dataframe

    problems: list[str] = []
    cfg = load_alerts_config().get("health", {})
    with connect() as conn:
        if Path(args.run_results).exists():
            run, nodes = parse_run_results(args.run_results)
            merge_dataframe(conn, pd.DataFrame([run]), "OPS.DBT_RUNS", ["run_id"])
            merge_dataframe(
                conn, pd.DataFrame(nodes), "OPS.DBT_NODE_RESULTS", ["run_id", "unique_id"]
            )
            if run["status"] == "failed":
                failed = [n["name"] for n in nodes if n["status"] in ("error", "fail")]
                problems.append(f"dbt falló en {run['n_errors']} nodos: {', '.join(failed[:10])}")
        else:
            problems.append(f"No existe {args.run_results} (¿dbt no llegó a ejecutarse?)")

        cur = conn.cursor()
        cur.execute("SELECT MAX(trade_date) FROM RAW.PRICES_DAILY")
        last = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(DISTINCT ticker) FROM RAW.PRICES_DAILY "
            "WHERE trade_date = (SELECT MAX(trade_date) FROM RAW.PRICES_DAILY)"
        )
        n = cur.fetchone()[0] or 0
    for msg in (
        check_freshness(last, dt.date.today(), cfg.get("max_staleness_days", 4)),
        check_volume(n, cfg.get("min_rows_per_day", 5)),
    ):
        if msg:
            problems.append(msg)

    if problems:
        text = "🚨 <b>MarketPulse: problema en el pipeline</b>\n" + "\n".join(
            f"• {m}" for m in problems
        )
        log.error(text)
        if not args.no_telegram:
            from marketpulse.alerts.telegram import TelegramClient

            TelegramClient().send(text)
        return 1
    log.info("Pipeline sano")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
