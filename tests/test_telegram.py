from marketpulse.alerts.telegram import TelegramClient


def _client():
    return TelegramClient(token="t", chat_id="1")


def test_dashboard_button_when_url_set(monkeypatch):
    monkeypatch.setenv("DASHBOARD_URL", "https://marketpulse.streamlit.app")
    p = _client().build_payload("hola")
    btn = p["reply_markup"]["inline_keyboard"][0][0]
    assert btn == {"text": "📊 Ver dashboard", "url": "https://marketpulse.streamlit.app"}


def test_no_button_when_unset(monkeypatch):
    monkeypatch.delenv("DASHBOARD_URL", raising=False)
    p = _client().build_payload("hola")
    assert "reply_markup" not in p and p["chat_id"] == "1" and p["parse_mode"] == "HTML"
