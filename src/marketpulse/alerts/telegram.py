"""Cliente mínimo de Telegram Bot API (solo `requests`, sin SDK).

Seguridad: el token sale de TELEGRAM_BOT_TOKEN (GitHub Secret). Solo se envía al
chat configurado en TELEGRAM_CHAT_ID; nunca a un chat arbitrario.
"""

from __future__ import annotations

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from marketpulse.config import env

API = "https://api.telegram.org/bot{token}/{method}"


class TelegramClient:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = token or env("TELEGRAM_BOT_TOKEN", required=True)
        self.chat_id = str(chat_id or env("TELEGRAM_CHAT_ID", required=True))

    def _url(self, method: str) -> str:
        return API.format(token=self.token, method=method)

    def is_authorized(self, chat_id: int | str) -> bool:
        """El bot SOLO atiende al chat configurado."""
        return str(chat_id) == self.chat_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    def send(self, text: str) -> None:
        resp = requests.post(
            self._url("sendMessage"),
            json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        resp.raise_for_status()

    def get_updates(self, offset: int | None = None, timeout: int = 30) -> list[dict]:
        resp = requests.get(
            self._url("getUpdates"),
            params={"offset": offset, "timeout": timeout},
            timeout=timeout + 10,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])
