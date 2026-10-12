import json

import pytest


@pytest.fixture
def run_results_file(tmp_path):
    data = {
        "metadata": {
            "invocation_id": "abc-123",
            "generated_at": "2026-10-09T21:00:00Z",
            "dbt_version": "1.8.8",
        },
        "args": {"which": "build"},
        "elapsed_time": 12.5,
        "results": [
            {
                "unique_id": "model.marketpulse.stg_prices_daily",
                "status": "success",
                "execution_time": 1.2,
                "failures": None,
                "message": "SUCCESS 1",
            },
            {
                "unique_id": "test.marketpulse.not_null_x.ab12cd",
                "status": "fail",
                "execution_time": 0.3,
                "failures": 4,
                "message": "Got 4 results",
            },
        ],
    }
    p = tmp_path / "run_results.json"
    p.write_text(json.dumps(data))
    return p
