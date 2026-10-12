import sys
import types

from marketpulse.config import env


def test_env_var_wins(monkeypatch):
    monkeypatch.setenv("MP_TEST_KEY", "desde_env")
    assert env("MP_TEST_KEY") == "desde_env"


def test_streamlit_secrets_fallback(monkeypatch):
    monkeypatch.delenv("MP_TEST_KEY", raising=False)
    fake = types.SimpleNamespace(secrets={"MP_TEST_KEY": "desde_secrets"})
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    assert env("MP_TEST_KEY") == "desde_secrets"


def test_broken_secrets_and_default(monkeypatch):
    class Broken:
        def get(self, _name):
            raise FileNotFoundError("sin secrets.toml")

    monkeypatch.delenv("MP_TEST_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "streamlit", types.SimpleNamespace(secrets=Broken()))
    assert env("MP_TEST_KEY", "def") == "def"


def test_cli_without_streamlit(monkeypatch):
    monkeypatch.delenv("MP_TEST_KEY", raising=False)
    monkeypatch.delitem(sys.modules, "streamlit", raising=False)
    assert env("MP_TEST_KEY") is None
