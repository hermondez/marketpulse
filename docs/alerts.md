# Alertas por Telegram (Módulo 2)

## Qué
`mp-alerts` lee `MARTS.MART_LATEST_METRICS`, aplica reglas de `config/alerts.yaml` y envía mensajes:

| Regla | Dispara cuando |
|---|---|
| `daily_move` | \|retorno diario\| > X % (por defecto 2 %) |
| `sma200_cross` | el precio ajustado cruza la SMA 200 (ayer de un lado, hoy del otro) |
| `rsi_extreme` | RSI 14 ≥ 70 o ≤ 30 |
| `near_52w_low` | a ≤ 3 % del mínimo de 52 semanas |
| `daily_summary` | resumen de cierre de todos los tickers |

## Por qué así
- **Reglas como funciones puras** (`rules.py`): testeables sin Telegram ni Snowflake.
- **Deduplicación** con `OPS.ALERTS_LOG` (clave `regla:ticker:fecha`): re-ejecutar no repite mensajes.
- **Redacción informativa**: verbos descriptivos ("subió", "cruzó"). Un test verifica que no aparezcan
  "compra", "vende", "oportunidad", etc. Cada mensaje lleva aviso educativo.
- **Seguridad**: token en `TELEGRAM_BOT_TOKEN` (GitHub Secret). Solo se envía a `TELEGRAM_CHAT_ID`.
  El bot interactivo (`mp-bot`) ignora en silencio cualquier chat no autorizado.

## Push vs polling
El flujo principal es **push-only**: GitHub Actions envía y termina. No hay servidor 24/7.
`mp-bot` (long polling, comandos `/resumen`, `/ayuda`) es opcional y requiere un proceso encendido
(VPS, Raspberry Pi, contenedor). Alternativa: webhook en una función serverless.

## Alternativas
Email (SMTP), Slack/Discord webhooks, ntfy.sh. Telegram se eligió por ser gratis y simple.

## Cuándo reutilizar
Cualquier alerta de datos con deduplicación: anomalías de ventas, SLAs, umbrales de KPIs.
Ver `docs/telegram_botfather.md` para crear el bot.
