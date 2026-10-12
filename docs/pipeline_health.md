# Salud del pipeline (Módulo 3)

## Qué
`mp-health` (se ejecuta *siempre*, incluso si dbt falla):
1. Parsea `dbt/target/run_results.json` → `OPS.DBT_RUNS` (una fila por corrida) y
   `OPS.DBT_NODE_RESULTS` (una por modelo/test: estado, tiempo, fallos, mensaje).
2. **Frescura**: `MAX(trade_date)` en RAW no puede tener más de 4 días de retraso.
3. **Volumen**: al menos 5 tickers en el último día.
4. Si algo falla → mensaje a Telegram y código de salida 1.

La página "Salud del pipeline" muestra el estado de la última corrida, historial y nodos lentos/fallidos.

## Por qué
dbt ya produce artefactos ricos; guardarlos en Snowflake da historial consultable con SQL
(¿qué test falla más? ¿qué modelo se volvió lento?) sin herramientas de pago.
Los chequeos de frescura/volumen detectan el fallo silencioso más común: "todo verde pero sin datos
nuevos" (p. ej., yfinance devolvió vacío).

## Internos
`run_results.json`: `metadata.invocation_id` (id de corrida), `results[].status`
(`success|error|fail|warn|pass|skipped`), `execution_time`, `failures`, `message`.
La carga usa el mismo MERGE idempotente que la ingesta.

## Alternativas
`dbt source freshness` (incluido en el job diario), paquete `elementary` (observabilidad dbt completa),
dbt Cloud, Monte Carlo, `dbt_artifacts`.

## Cuándo reutilizar
Cualquier proyecto dbt: el parser no depende de MarketPulse.
