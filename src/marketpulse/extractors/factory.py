"""Factory: elige la implementación por configuración (PRICE_SOURCE)."""

from __future__ import annotations

from marketpulse.config import env
from marketpulse.extractors.base import PriceExtractor
from marketpulse.extractors.stooq_extractor import StooqExtractor
from marketpulse.extractors.yfinance_extractor import YFinanceExtractor

_REGISTRY: dict[str, type[PriceExtractor]] = {
    "yfinance": YFinanceExtractor,
    "stooq": StooqExtractor,
}


def get_extractor(source: str | None = None) -> PriceExtractor:
    source = (source or env("PRICE_SOURCE", "yfinance")).lower()
    try:
        return _REGISTRY[source]()
    except KeyError as exc:
        raise ValueError(f"Fuente desconocida '{source}'. Opciones: {list(_REGISTRY)}") from exc
