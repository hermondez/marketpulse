# CI/CD y programación

## Qué
- `.github/workflows/ci.yml` (en cada PR): `ruff` → `pytest` → `dbt parse` → `dbt build` en esquema
  efímero `CI_PR_<n>_*` → limpieza de esos esquemas.
- `.github/workflows/daily.yml` (lun-vie): calendario → ingesta → dbt build prod → health → alertas
  → artefactos (`manifest.json`, `catalog.json`, `run_results.json`).

## Horario: UTC, EST y EDT
El cron de GitHub está en **UTC** y no sabe de cambios de horario. La NYSE cierra a las 16:00 de
Nueva York:
- EDT (verano, UTC-4): 20:00 UTC.  - EST (invierno, UTC-5): 21:00 UTC.

Usamos `30 22 * * 1-5` (22:30 UTC = 18:30 EDT / 17:30 EST / 16:30 Costa Rica). Siempre >1 h después
del cierre, sin tocar el cron dos veces al año. GitHub puede retrasar crons hasta ~15-30 min en horas
pico; no importa para un batch diario.

## Feriados
El primer paso ejecuta `python -m marketpulse.market_calendar` (exchange_calendars, `XNYS`). Si no es
sesión (Thanksgiving, Navidad, Viernes Santo...), los demás pasos se omiten y el job termina en verde.
`workflow_dispatch` con `force=true` permite ejecutar manualmente.

## Secrets (Settings → Secrets and variables → Actions)
`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
`LLM_API_KEY` (solo si usas OpenAI/Anthropic), `DASHBOARD_URL` (opcional, mejor como variable). Nunca en el código. Recomendado: autenticación
key-pair de Snowflake (`SNOWFLAKE_PRIVATE_KEY`) en vez de contraseña.

## Alternativas
Airflow/Dagster/Prefect; Snowflake Tasks (orquestación dentro de Snowflake, pero la ingesta Python
necesitaría Snowpark Container Services o External Access); dbt Cloud jobs.

## Cuándo reutilizar
Cualquier repo dbt: CI con esquema efímero por PR es un estándar de la industria ("slim CI" con
`state:modified+` es el siguiente paso).
