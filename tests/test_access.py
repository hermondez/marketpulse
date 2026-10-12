from marketpulse.ask.access import ask_enabled, check_password, remaining_questions


def test_disabled_without_password():
    assert not ask_enabled(None) and not ask_enabled("  ")
    assert not check_password("x", None)


def test_password_check():
    assert check_password("secreto", "secreto")
    assert not check_password("otro", "secreto")
    assert not check_password("", "secreto")


def test_rate_limit():
    assert remaining_questions(0, 10) == 10
    assert remaining_questions(12, 10) == 0
