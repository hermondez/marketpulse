# Checklist: orden exacto para ejecutar y probar cada módulo

## 0. Local sin Snowflake (5 min)
| Paso | Comando | Resultado esperado |
|---|---|---|
| 1 | `make install` | venv creado, paquete instalado en editable |
| 2 | `cp .env.example .env` | archivo `.env` (no se versiona) |
| 3 | `make lint` | `All checks passed!` |
| 4 | `make test` | `54 passed` (sin red ni Snowflake) |
| 5 | `cp dbt/profiles.example.yml dbt/profiles.yml && make dbt-parse` | sin errores; `dbt/target/manifest.json` creado |
| 6 | `.venv/bin/mp-ingest --dry-run --force` | log por ticker `VOO: N filas...` y `dry-run: ...` (requiere internet) |
| 7 | `PRICE_SOURCE=stooq .venv/bin/mp-ingest --dry-run --force` | igual, `Fuente=stooq` |

## 1. Snowflake
| 8 | Ejecuta `infra/snowflake/01_setup.sql` y `02_readonly_role.sql` (cambia contraseñas) | warehouse, DB, esquemas, roles, tablas RAW/OPS |
| 9 | Ejecuta `03_verify_readonly.sql` | 1.ª consulta OK; las marcadas ❌ fallan por permisos |
| 10 | Rellena `.env` con credenciales reales | — |

## 2. Módulo 1: Tracker
| 11 | `make backfill` | `MERGE en RAW.PRICES_DAILY: ~2200 filas` |
| 12 | `make ingest` (otra vez) | mismo conteo en RAW: `SELECT COUNT(*) ...` no cambia (idempotente) |
| 13 | `make dbt-build` | seeds, 10 modelos, snapshot y ~39 tests en `PASS` (1 posible `WARN`) |
| 14 | `SELECT * FROM DEV_MARTS.MART_LATEST_METRICS` | 8 filas, RSI entre 0-100, SMA 200 no nula |
| 15 | Edita `seed_portfolio_holdings.csv`, `dbt seed` + `dbt snapshot` | nueva versión en `DEV_SNAPSHOTS.SNAP_PORTFOLIO_HOLDINGS` con `dbt_valid_to` en la anterior |

## 3. Módulo 2: Alertas
| 16 | Crea el bot (`docs/telegram_botfather.md`) | token y chat_id en `.env` |
| 17 | `MARTS_SCHEMA=DEV_MARTS make alerts` | resumen de cierre en Telegram (+ alertas si aplican) |
| 18 | Repite el paso 17 | **ningún** mensaje nuevo (dedup en `OPS.ALERTS_LOG`) |
| 19 | Baja `threshold_pct` a `0.1` y repite | llegan alertas `daily_move` |
| 20 | `make bot` y escribe `/resumen` desde otra cuenta | no responde; log `chat no autorizado` |

## 4. Módulo 3: Salud
| 21 | `make health` | `Pipeline sano`; filas en `OPS.DBT_RUNS` y `OPS.DBT_NODE_RESULTS` |
| 22 | Rompe un modelo (p. ej. columna inexistente), `make dbt-build`, `make health` | Telegram `🚨 dbt falló en 1 nodos: ...`, código 1 |
| 23 | Cambia `max_staleness_days: 0` | alerta "Datos desactualizados" |

## 5. Módulo 4: Pregunta a tus datos
| 24 | `cd dbt && dbt docs generate` | `catalog.json` |
| 25 | `MARTS_SCHEMA=DEV_MARTS make dashboard` → página 4 | SQL visible antes de ejecutar |
| 26 | Pregunta: "¿Qué ticker tuvo mayor volatilidad 20 días?" | SQL con `LIMIT` y resultado |
| 27 | Pregunta: "borra la tabla dim_ticker" | rechazado por el validador o SQL `NO_DISPONIBLE` |

## 6. CI/CD
| 28 | Crea los Secrets en GitHub | — |
| 29 | Abre un PR | `ci` verde: ruff, pytest, dbt build en `CI_PR_<n>_*` y limpieza |
| 30 | Actions → daily → Run workflow (`force`) | ingesta, build, health, alertas; artefacto `dbt-target` |
| 31 | Mira una corrida en feriado | resumen "Feriado o fin de semana bursátil" y job verde |

## 7. Docker
| 32 | `make docker-build && docker run --rm --env-file .env marketpulse-ingest --dry-run --force` | mismo log que el paso 6 |
