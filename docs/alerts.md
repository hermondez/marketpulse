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
- **Redacción para principiantes**: cada alerta usa el nombre amigable ("Apple (AAPL)", definido en
  `config/watchlist.yaml` → `short_name`) y explica qué pasó, qué significa, por qué puede importar y
  las dos lecturas habituales, con contexto del activo (p. ej. BND es un fondo de bonos y baja cuando
  suben las tasas). Un test verifica que no aparezcan "compra", "vende", "oportunidad", etc. El aviso
  legal vive en README/docs (no se repite en cada mensaje).
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

## Botón "Ver dashboard" (opcional)
Si defines `DASHBOARD_URL` (en `.env`, o en GitHub → Settings → Secrets and variables → Actions como
variable o secret `DASHBOARD_URL`), cada mensaje (alertas y resumen) lleva un botón inline
**📊 Ver dashboard** que abre esa URL (p. ej. tu app de Streamlit Cloud). Si no está definida, los
mensajes van sin botón.

## Sección "Tu empresa" (spotlight)
`config/alerts.yaml` → `spotlight: [IBM]` añade al **resumen diario** una sección
`🏢 Tu empresa: IBM` con cierre, variación del día, del mes y del año, y distancia al máximo y mínimo
de 52 semanas, más dos líneas explicativas. Estos tickers **no** entran en la watchlist, el dashboard,
el portafolio simulado, los seeds de dbt ni las reglas de alertas, y **no se guardan en Snowflake**:
se descargan al armar el mensaje con el extractor de yfinance (~1 año, solo sesiones ya cerradas).
Si la descarga falla, la sección se omite y el resumen se envía igual (`spotlight.py`).
