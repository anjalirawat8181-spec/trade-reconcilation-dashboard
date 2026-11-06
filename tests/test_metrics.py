"""Tests for the pure KPI helpers."""
import pandas as pd

from metrics import attach_status, compute_kpis, format_currency, status_counts


def sample_breaks() -> pd.DataFrame:
    return pd.DataFrame({
        "trade_id": ["A", "B", "C"],
        "break_date": pd.to_datetime(["2026-05-01", "2026-05-10", "2026-05-20"]),
        "notional": [1000.0, 2000.0, 4000.0],
    })


def test_kpis_all_open():
    b = attach_status(sample_breaks(), {})
    k = compute_kpis(b, total_trades=100, as_of=pd.Timestamp("2026-05-31"))
    assert (k.match_rate_pct, k.open_breaks, k.open_notional, k.oldest_open_days) == (97.0, 3, 7000.0, 30)


def test_resolved_breaks_leave_open_kpis_but_not_match_rate():
    b = attach_status(sample_breaks(), {"A": "Resolved", "B": "Investigating"})
    k = compute_kpis(b, total_trades=100, as_of=pd.Timestamp("2026-05-31"))
    assert k.open_breaks == 2 and k.open_notional == 6000.0 and k.oldest_open_days == 21
    assert k.match_rate_pct == 97.0
    assert status_counts(b) == {"Open": 1, "Investigating": 1, "Resolved": 1}


def test_no_open_breaks_gives_no_age():
    b = attach_status(sample_breaks(), {"A": "Resolved", "B": "Resolved", "C": "Resolved"})
    assert compute_kpis(b, 10, pd.Timestamp("2026-06-01")).oldest_open_days is None


def test_zero_trades_has_no_match_rate():
    b = attach_status(sample_breaks().iloc[0:0], {})
    assert compute_kpis(b, 0, None).match_rate_pct is None


def test_format_currency():
    assert format_currency(1234567.8) == "$1,234,568"
    assert format_currency(None) == "—"
