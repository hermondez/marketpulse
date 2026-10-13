from marketpulse.alerts.rules import FORBIDDEN_WORDS, evaluate, format_alert, format_daily_summary
from marketpulse.alerts.run_alerts import filter_new

CFG = {
    "daily_move": {"enabled": True, "threshold_pct": 2.0},
    "sma200_cross": {"enabled": True},
    "rsi_extreme": {"enabled": True, "high": 70, "low": 30},
    "near_52w_low": {"enabled": True, "within_pct": 3.0},
}


def row(**kw):
    base = {
        "ticker": "VOO",
        "trade_date": "2026-10-09",
        "close": 100.0,
        "adj_close": 100.0,
        "daily_return": 0.001,
        "sma_200": 90.0,
        "prev_adj_close": 99.0,
        "prev_sma_200": 90.0,
        "rsi_14": 50.0,
        "pct_from_52w_low": 0.2,
    }
    base.update(kw)
    return base


def rules(r):
    return {a.rule for a in evaluate(r, CFG)}


def test_quiet_day_no_alerts():
    assert rules(row()) == set()


def test_daily_move():
    assert "daily_move" in rules(row(daily_return=-0.031))


def test_sma_cross_up_and_down():
    assert "sma200_cross" in rules(row(prev_adj_close=89.0, adj_close=91.0))
    assert "sma200_cross" in rules(row(prev_adj_close=91.0, adj_close=89.0))


def test_rsi_and_52w_low():
    assert "rsi_extreme" in rules(row(rsi_14=75))
    assert "near_52w_low" in rules(row(pct_from_52w_low=0.01))


def test_handles_nulls():
    assert rules(row(sma_200=None, rsi_14=None, daily_return=None)) == set()


def test_wording_never_advises():
    alerts = evaluate(row(daily_return=0.05, rsi_14=80, pct_from_52w_low=0.0), CFG)
    texts = [format_alert(a).lower() for a in alerts] + [format_daily_summary([row()]).lower()]
    for t in texts:
        assert not any(w in t for w in FORBIDDEN_WORDS), t


def test_dedup():
    alerts = evaluate(row(daily_return=0.05), CFG)
    assert filter_new(alerts, {alerts[0].key}) == []


def test_friendly_names_and_no_per_message_disclaimer():
    from marketpulse.alerts.rules import enrich_rows
    from marketpulse.config import load_watchlist

    rows = enrich_rows([row(ticker="AAPL", daily_return=0.05)], load_watchlist().tickers)
    text = format_alert(evaluate(rows[0], CFG)[0])
    assert "Apple (AAPL)" in text and "$100.00" in text
    assert "no es recomendación" not in text.lower()
    summary = format_daily_summary(rows)
    assert "Apple (AAPL)" in summary and "🟢" in summary


def test_bond_context_and_two_readings():
    from marketpulse.alerts.rules import enrich_rows
    from marketpulse.config import load_watchlist

    rows = enrich_rows([row(ticker="BND", pct_from_52w_low=0.01)], load_watchlist().tickers)
    text = format_alert(evaluate(rows[0], CFG)[0]).lower()
    assert "vanguard total bond (bnd)" in text and "tasas de interés" in text
    assert "algunos" in text and "otros" in text
