from __future__ import annotations

import io

import pandas as pd
import pytest

from recon_engine import (
    BREAK_COLUMNS,
    ReconConfig,
    clean_trades,
    count_unique_trades,
    data_quality,
    load_trades_csv,
    reconcile,
    validate_trades,
)

BASE = {
    "trade_id": "T1",
    "trade_date": "2026-05-01",
    "symbol": "AAPL",
    "quantity": 100,
    "price": 100.0,
    "settlement_date": "2026-05-04",
    "counterparty": "Alpha",
}


def trades(*overrides: dict) -> pd.DataFrame:
    return pd.DataFrame([{**BASE, **o} for o in overrides])


def one_break(broker_over: dict, ledger_over: dict, cfg: ReconConfig | None = None) -> pd.Series:
    result = reconcile(trades(broker_over), trades(ledger_over), cfg)
    assert len(result) == 1
    return result.iloc[0]


def test_no_breaks_when_identical():
    result = reconcile(trades({}), trades({}))
    assert result.empty
    assert list(result.columns) == list(BREAK_COLUMNS)


def test_quantity_mismatch():
    row = one_break({}, {"quantity": 60})
    assert row.break_type == "quantity_mismatch"
    assert row.severity == "MEDIUM"


def test_price_mismatch():
    row = one_break({}, {"price": 101.0})
    assert row.break_type == "price_mismatch"
    assert row.severity == "MEDIUM"


def test_settlement_date_mismatch_is_low():
    row = one_break({}, {"settlement_date": "2026-05-05"})
    assert row.break_type == "settlement_date_mismatch"
    assert row.severity == "LOW"


def test_counterparty_mismatch():
    row = one_break({}, {"counterparty": "Beta"})
    assert row.break_type == "counterparty_mismatch"
    assert row.severity == "MEDIUM"


def test_missing_in_broker():
    result = reconcile(trades({"trade_id": "X"}), trades({}))
    kinds = dict(zip(result.trade_id, result.break_type))
    assert kinds == {"X": "missing_in_ledger", "T1": "missing_in_broker"}
    assert set(result.severity) == {"HIGH"}


def test_missing_in_ledger_has_broker_notional():
    result = reconcile(trades({}), trades({"trade_id": "Z"}))
    row = result[result.trade_id == "T1"].iloc[0]
    assert row.break_type == "missing_in_ledger"
    assert row.notional == 10_000.0
    assert pd.isna(row.ledger_quantity)


@pytest.mark.parametrize("ledger_price,is_break", [(100.05, False), (100.06, True)])
def test_price_tolerance_boundary_bps(ledger_price, is_break):
    cfg = ReconConfig(price_tolerance_bps=5.0)
    result = reconcile(trades({"price": 100.0}), trades({"price": ledger_price}), cfg)
    assert (len(result) == 1) is is_break


def test_price_exactly_at_tolerance_is_not_a_break():
    result = reconcile(trades({"price": 100.0}), trades({"price": 100.0}), ReconConfig(price_tolerance_bps=0))
    assert result.empty


@pytest.mark.parametrize("ledger_qty,is_break", [(98, False), (97, True)])
def test_quantity_tolerance_boundary(ledger_qty, is_break):
    cfg = ReconConfig(quantity_tolerance=2)
    result = reconcile(trades({}), trades({"quantity": ledger_qty}), cfg)
    assert (len(result) == 1) is is_break


@pytest.mark.parametrize("ledger_date,is_break", [("2026-05-05", False), ("2026-05-06", True)])
def test_settlement_tolerance_boundary(ledger_date, is_break):
    cfg = ReconConfig(settlement_tolerance_days=1)
    result = reconcile(trades({}), trades({"settlement_date": ledger_date}), cfg)
    assert (len(result) == 1) is is_break


def test_high_notional_makes_any_break_high():
    big = {"quantity": 1000, "price": 10_000.0}
    row = one_break(big, {**big, "settlement_date": "2026-05-05"})
    assert row.break_type == "settlement_date_mismatch"
    assert row.severity == "HIGH"
    assert "threshold" in row.severity_reason


def test_minor_quantity_and_price_are_low():
    assert one_break({}, {"quantity": 98}).severity == "LOW"
    assert one_break({}, {"price": 100.10}).severity == "LOW"


def test_multiple_differences_use_most_severe_field():
    row = one_break({}, {"settlement_date": "2026-05-05", "counterparty": "Beta"})
    assert row.break_type == "counterparty_mismatch"
    assert row.severity == "MEDIUM"
    assert row.differing_fields == "settlement_date,counterparty"


def test_counterparty_compare_ignores_case_and_whitespace():
    assert reconcile(trades({}), trades({"counterparty": "  alpha "})).empty


def test_duplicate_trade_ids_are_collapsed():
    ledger = pd.concat([trades({}), trades({})], ignore_index=True)
    assert reconcile(trades({}), ledger).empty
    assert data_quality(ledger)["duplicate_ids"] == 1


def test_blank_trade_ids_are_dropped():
    broker = pd.concat([trades({}), trades({"trade_id": None}), trades({"trade_id": "  "})])
    assert len(clean_trades(broker)) == 1
    assert data_quality(broker)["blank_ids"] == 2


def test_string_numbers_are_coerced():
    broker = trades({"quantity": "100", "price": "100.0"})
    assert reconcile(broker, trades({})).empty


def test_unparseable_value_is_a_break_not_a_crash():
    row = one_break({}, {"price": "n/a"})
    assert row.break_type == "price_mismatch"
    assert data_quality(trades({"price": "n/a"}))["invalid_values"] == 1


def test_null_quantity_on_one_side_is_a_break():
    row = one_break({}, {"quantity": None})
    assert row.break_type == "quantity_mismatch"


def test_empty_inputs_return_empty_breaks():
    empty = trades({}).iloc[0:0]
    assert reconcile(empty, empty).empty
    result = reconcile(trades({}), empty)
    assert list(result.break_type) == ["missing_in_ledger"]


def test_count_unique_trades():
    assert count_unique_trades(trades({}, {"trade_id": "A"}), trades({"trade_id": "A"}, {"trade_id": "B"})) == 3


def test_validate_reports_missing_columns():
    errors = validate_trades(trades({}).drop(columns=["counterparty", "price"]))
    assert "counterparty" in errors[0] and "price" in errors[0]


def test_reconcile_raises_on_missing_column():
    with pytest.raises(ValueError, match="Missing required"):
        reconcile(trades({}).drop(columns=["price"]), trades({}))


def test_load_empty_file_raises_clear_error():
    with pytest.raises(ValueError, match="empty"):
        load_trades_csv(io.StringIO(""))


def test_header_only_file_fails_validation():
    df = load_trades_csv(io.StringIO(",".join(BASE) + "\n"))
    assert any("no trade rows" in e for e in validate_trades(df))


def test_sample_data_break_rate_is_realistic():
    broker = load_trades_csv("broker_trades.csv")
    ledger = load_trades_csv("internal_ledger.csv")
    rate = len(reconcile(broker, ledger)) / count_unique_trades(broker, ledger)
    assert 0.02 <= rate <= 0.04
    assert count_unique_trades(broker, ledger) >= 500
