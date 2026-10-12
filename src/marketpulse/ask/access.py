"""Control de acceso y límite de uso para "Pregunta a tus datos".

Por qué: cada pregunta cuesta dinero (LLM + warehouse). En una app pública,
sin contraseña cualquiera podría gastar tus créditos. Funciones puras -> testeables.
"""

from __future__ import annotations

import hmac

DEFAULT_MAX_QUESTIONS = 10


def ask_enabled(configured_password: str | None) -> bool:
    """La página solo se habilita si hay APP_ASK_PASSWORD configurada."""
    return bool(configured_password and configured_password.strip())


def check_password(given: str | None, configured: str | None) -> bool:
    """Comparación en tiempo constante (evita ataques de timing)."""
    if not ask_enabled(configured) or not given:
        return False
    return hmac.compare_digest(given.encode(), configured.encode())


def remaining_questions(used: int, max_questions: int = DEFAULT_MAX_QUESTIONS) -> int:
    return max(0, max_questions - used)
