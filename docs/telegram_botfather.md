# Crear el bot de Telegram (BotFather) y obtener tu chat_id

1. En Telegram, abre **@BotFather** (verifica la insignia azul).
2. Envía `/newbot`, elige nombre (p. ej. `MarketPulse Edgardo`) y usuario terminado en `bot`
   (p. ej. `marketpulse_edgardo_bot`).
3. BotFather responde con el **token** (`123456789:AA...`). Es una contraseña: guárdalo en `.env`
   (`TELEGRAM_BOT_TOKEN`) y en GitHub Secrets. **Nunca** en el código ni en capturas.
4. Abre tu bot y envíale cualquier mensaje (p. ej. `hola`). Sin esto, `getUpdates` sale vacío.
5. Obtén tu `chat_id`:
   ```bash
   curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates" | python -m json.tool
   ```
   Busca `"chat": {"id": 123456789, ...}`. Ese número va en `TELEGRAM_CHAT_ID`.
   (Para un grupo, añade el bot al grupo; el id será negativo, p. ej. `-100...`.)
6. Prueba el envío:
   ```bash
   curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="$TELEGRAM_CHAT_ID" -d text="MarketPulse conectado ✅"
   ```
7. Opcional en BotFather: `/setprivacy` → Enable; `/setjoingroups` → Disable (nadie puede añadir tu
   bot a otros grupos).

**Si el token se filtra**: BotFather → `/revoke`, genera uno nuevo y actualiza `.env` y Secrets.

Nota: `getUpdates` no funciona si el bot tiene un webhook configurado (`deleteWebhook` lo quita), y
si `mp-bot` está corriendo consumirá los mensajes antes que tu `curl`.
