import json

from marketpulse.ask.llm import extract_sql
from marketpulse.ask.schema_context import build_schema_context


def test_schema_context_only_allowlisted(tmp_path):
    manifest = {
        "nodes": {
            "model.mp.dim_ticker": {
                "resource_type": "model",
                "name": "dim_ticker",
                "description": "Tickers",
                "columns": {"ticker": {"description": "Símbolo"}},
            },
            "model.mp.stg_prices_daily": {
                "resource_type": "model",
                "name": "stg_prices_daily",
                "description": "secreto",
                "columns": {},
            },
        }
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    ctx = build_schema_context(tmp_path)
    assert "MARTS.DIM_TICKER" in ctx and "TICKER" in ctx and "secreto" not in ctx


def test_extract_sql_strips_markdown():
    assert extract_sql("```sql\nSELECT 1;\n```") == "SELECT 1"
