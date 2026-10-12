# Modelado dbt

## Qué
Proyecto en `dbt/` con capas:

| Capa | Modelos | Materialización |
|---|---|---|
| sources | `raw.prices_daily`, `raw.dividends` (con freshness) | — |
| staging | `stg_prices_daily`, `stg_dividends` | view |
| intermediate | `int_prices_returns`, `int_prices_indicators` | view / **incremental** |
| marts | `dim_ticker`, `fct_daily_metrics`, `mart_latest_metrics`, `fct_dividends` (**incremental**), `fct_portfolio_daily`, `mart_portfolio_summary` | table |
| seeds | `seed_ticker_metadata`, `seed_portfolio_holdings` (portafolio SIMULADO) | — |
| snapshot | `snap_portfolio_holdings` (SCD2, estrategia `check`) | — |

## Por qué
- **Staging** solo tipa y deduplica (`qualify row_number()`), igual que harías en Coalesce.
- **Incremental con lookback**: `int_prices_indicators` lee 400 días de historia (para que la SMA 200
  y las 52 semanas tengan datos) pero solo hace MERGE de los últimos 10 días.
- **Métricas de ventana no acotada** (retorno acumulado, drawdown) en `fct_daily_metrics` como `table`
  porque necesitan toda la historia y el volumen es pequeño (~8 tickers × 250 días/año).
- **Esquemas por entorno** (`generate_schema_name`): prod → `MARTS`; dev → `DEV_MARTS`; CI →
  `CI_PR_42_MARTS`.

## Tests
- Genéricos de dbt: `not_null`, `unique`, `accepted_values`, `relationships`.
- **Genéricos personalizados** (`tests/generic/`): `is_between`, `unique_combination_of_columns`,
  `not_in_future`.
- **Singulares** (`tests/*.sql`): `assert_high_gte_low`, `assert_daily_return_reasonable` (warn),
  `assert_holdings_in_watchlist`.
- Freshness de fuentes: warn a 3 días, error a 5.

## Macros
`safe_divide`, `sma`, `annualized_volatility`, `incremental_lookback_filter`, `generate_schema_name`,
`grant_select_to_reader` (post-hook en prod), `drop_schema_if_exists` (limpieza CI, solo `CI_*`).

## Alternativas
- `dbt_utils` / `dbt_expectations` en lugar de tests propios (se evitaron para que `dbt parse` funcione
  sin red y para mostrar cómo se escriben).
- Hacer `fct_daily_metrics` incremental guardando `running_max` del día anterior (más complejo).
- Calcular indicadores en Python (pandas) — más fácil para RSI de Wilder, pero sale de la capa SQL.

## Cuándo reutilizar
Plantilla para cualquier serie temporal diaria por entidad (ventas por tienda, métricas por sensor).
