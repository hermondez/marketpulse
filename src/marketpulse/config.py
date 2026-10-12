"""Configuración centralizada.

Decisión: todo secreto viene de variables de entorno (localmente vía .env, en CI vía
GitHub Secrets) o, en Streamlit Community Cloud, de `st.secrets`. Nada sensible vive en
el código ni en YAML versionado.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:  # python-dotenv es opcional en runtime (en CI no hay .env)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

# Raíz del repo: src/marketpulse/config.py -> ../../
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = Path(os.getenv("MARKETPULSE_CONFIG_DIR", REPO_ROOT / "config"))


def _from_streamlit_secrets(name: str) -> str | None:
    """Busca `name` en st.secrets SOLO si Streamlit ya está cargado (el dashboard).

    No importamos streamlit aquí: la CLI, CI y Docker no lo necesitan ni lo instalan.
    Si no hay secrets.toml, st.secrets lanza excepción: la tratamos como "no existe".
    """
    st = sys.modules.get("streamlit")
    if st is None:
        return None
    try:
        value = st.secrets.get(name)
    except Exception:  # noqa: BLE001 - sin secrets.toml / fuera de un script Streamlit
        return None
    return None if value is None else str(value)


def env(name: str, default: str | None = None, required: bool = False) -> str | None:
    """Orden: variable de entorno -> st.secrets (Streamlit Cloud) -> default.

    Si es obligatoria y falta, falla con un mensaje claro (sin mostrar valores).
    """
    value = os.getenv(name) or _from_streamlit_secrets(name) or default
    if required and not value:
        raise RuntimeError(f"Falta la variable/secret obligatoria: {name}")
    return value


def load_yaml(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass(frozen=True)
class Ticker:
    symbol: str
    type: str = "etf"
    name: str = ""


@dataclass(frozen=True)
class Watchlist:
    tickers: list[Ticker] = field(default_factory=list)
    backfill_days: int = 400
    lookback_days: int = 7

    @property
    def symbols(self) -> list[str]:
        return [t.symbol for t in self.tickers]


def load_watchlist(name: str = "watchlist.yaml") -> Watchlist:
    raw = load_yaml(name)
    tickers = [Ticker(**t) for t in raw.get("tickers", [])]
    if not tickers:
        raise ValueError("La watchlist está vacía")
    return Watchlist(
        tickers=tickers,
        backfill_days=int(raw.get("backfill_days", 400)),
        lookback_days=int(raw.get("lookback_days", 7)),
    )


def load_alerts_config(name: str = "alerts.yaml") -> dict[str, Any]:
    return load_yaml(name)


# Esquema de marts que leen alertas, dashboard y "Pregunta a tus datos".
# En dev dbt crea DEV_MARTS (ver macro generate_schema_name).
MARTS_SCHEMA = env("MARTS_SCHEMA", "MARTS")
