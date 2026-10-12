# Ingesta (Módulo 1)

## Qué
`mp-ingest` lee `config/watchlist.yaml`, descarga OHLCV + dividendos de cada ticker y los carga en
`RAW.PRICES_DAILY` y `RAW.DIVIDENDS`.

## Por qué así
- **Extractor desacoplado** (`extractors/base.py`): clase abstracta `PriceExtractor` con
  `fetch_prices` / `fetch_dividends`. Implementaciones `YFinanceExtractor` y `StooqExtractor`; la
  `factory` elige según `PRICE_SOURCE`. Patrón *Strategy + Factory*: cambiar de fuente no toca la
  ingesta.
- **Reintentos con tenacity**: 3 intentos con backoff exponencial (2 s, 4 s, …) para errores
  transitorios (red, rate-limit).
- **Aislamiento de fallos**: un ticker que falla se registra y se sigue; al final el proceso sale con
  código 1 para que CI lo marque.
- **Idempotencia**: `write_pandas` a una tabla TEMPORAL + `MERGE` por clave `(ticker, trade_date)`.
  Re-ejecutar el mismo día actualiza en vez de duplicar.
- **Lookback de 7 días**: cada corrida re-descarga la última semana para absorber correcciones.
- **Calendario**: si no es día hábil NYSE, termina con código 0.

## Internos
1. `is_trading_day()` (exchange_calendars, calendario `XNYS`).
2. `extract_all()` → DataFrames estándar (`PRICE_COLUMNS`) validados (sin nulos, precio > 0, sin dups).
3. `merge_dataframe()` → `CREATE TEMPORARY TABLE ... LIKE`, `write_pandas`, `MERGE`.

Flags: `--backfill` (400 días), `--force` (ignora calendario), `--dry-run` (no escribe).

## Alternativas
- `COPY INTO` desde stage S3 (mejor para volúmenes grandes).
- Snowpipe / conectores (Fivetran, Airbyte) si existe conector para la fuente.
- `DELETE + INSERT` por rango de fechas (más simple que MERGE, también idempotente).

## Cuándo reutilizar
El patrón "extractor abstracto + temp table + MERGE" sirve para cualquier API REST a Snowflake.
