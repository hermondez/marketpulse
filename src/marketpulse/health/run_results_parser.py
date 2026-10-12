"""Parsea dbt target/run_results.json en filas planas (Módulo 3).

run_results.json lo genera dbt en cada `run`/`test`/`build`. Contiene, por nodo:
status (success/error/fail/warn/skipped/pass), tiempo de ejecución y mensaje.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_run_results(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    meta = data.get("metadata", {})
    run_id = meta.get("invocation_id")
    args = data.get("args", {})
    run = {
        "run_id": run_id,
        "generated_at": meta.get("generated_at"),
        "dbt_version": meta.get("dbt_version"),
        "command": args.get("which", "unknown"),
        "elapsed_s": round(float(data.get("elapsed_time", 0)), 3),
    }
    nodes = []
    for r in data.get("results", []):
        uid = r.get("unique_id", "")
        nodes.append(
            {
                "run_id": run_id,
                "unique_id": uid,
                "resource_type": uid.split(".")[0],
                "name": uid.split(".")[-1],
                "status": r.get("status"),
                "execution_time_s": round(float(r.get("execution_time") or 0), 3),
                "failures": r.get("failures"),
                "message": (r.get("message") or "")[:1000],
            }
        )
    statuses = [n["status"] for n in nodes]
    run["n_nodes"] = len(nodes)
    run["n_errors"] = sum(s in ("error", "fail") for s in statuses)
    run["n_warnings"] = sum(s == "warn" for s in statuses)
    run["status"] = "failed" if run["n_errors"] else "success"
    return run, nodes
