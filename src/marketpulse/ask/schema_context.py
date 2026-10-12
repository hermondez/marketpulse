"""Contexto de esquema para el LLM a partir de dbt docs (manifest.json + catalog.json).

Por qué: las descripciones que ya escribimos en los .yml de dbt son la mejor
documentación de las tablas. Reutilizarlas evita prompts desincronizados.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from marketpulse.ask.sql_guard import DEFAULT_ALLOWED_TABLES


def build_schema_context(
    target_dir: str | Path, allowed: frozenset[str] = DEFAULT_ALLOWED_TABLES, schema: str = "MARTS"
) -> str:
    target = Path(target_dir)
    if not (target / "manifest.json").exists():
        # Streamlit Cloud no ejecuta dbt y dbt/target/ no se versiona: usamos los .yml.
        return build_schema_context_from_yml(target.parent / "models", allowed, schema)
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    catalog_path = target / "catalog.json"
    catalog = (
        json.loads(catalog_path.read_text(encoding="utf-8"))
        if catalog_path.exists()
        else {"nodes": {}}
    )
    parts: list[str] = []
    for uid, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") != "model":
            continue
        name = (node.get("alias") or node["name"]).upper()
        if name not in allowed:
            continue
        cols = dict(node.get("columns", {}))
        # catalog.json aporta tipos reales de Snowflake (si se corrió `dbt docs generate`)
        for cname, cinfo in catalog.get("nodes", {}).get(uid, {}).get("columns", {}).items():
            cols.setdefault(cname.lower(), {}).setdefault("data_type", cinfo.get("type"))
        lines = [f"TABLA {schema}.{name}: {node.get('description', '').strip()}"]
        for cname, c in cols.items():
            dtype = c.get("data_type") or ""
            lines.append(f"  - {cname.upper()} {dtype}: {c.get('description', '').strip()}")
        parts.append("\n".join(lines))
    return "\n\n".join(sorted(parts))


def build_schema_context_from_yml(
    models_dir: str | Path, allowed: frozenset[str] = DEFAULT_ALLOWED_TABLES, schema: str = "MARTS"
) -> str:
    """Alternativa sin dbt: lee descripciones de los .yml de modelos (sin tipos de datos)."""
    parts: list[str] = []
    for yml in sorted(Path(models_dir).rglob("*.yml")):
        data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        for model in data.get("models", []):
            name = model["name"].upper()
            if name not in allowed:
                continue
            lines = [f"TABLA {schema}.{name}: {model.get('description', '').strip()}"]
            for col in model.get("columns", []):
                desc = (col.get("description") or "").strip()
                lines.append(f"  - {col['name'].upper()}: {desc}")
            parts.append("\n".join(lines))
    return "\n\n".join(sorted(parts))
