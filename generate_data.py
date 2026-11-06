from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

SEED = 42
TRADE_COUNT = 600
BREAK_RATE = 0.03
BENIGN_RATE = 0.02
DUPLICATE_LEDGER_ROWS = 2
FIRST_TRADE_DATE = date(2026, 4, 1)
TRADE_DAYS = 120

SYMBOLS_BASE_PRICE = {
    "RELIANCE": 2900, "TCS": 3900, "HDFCBANK": 1700, "ICICIBANK": 1200,
    "INFY": 1600, "SBIN": 850, "LTIM": 6100, "HINDUNILVR": 2780,
    "BHARTIARTL": 980, "ITC": 440, "SUNPHARMA": 1650, "TATAMOTORS": 1010,
    "AXISBANK": 1150, "POWERGRID": 320, "KOTAKBANK": 1820, "NTPC": 390,
    "ASIANPAINT": 2800, "TATASTEEL": 160, "ULTRACEMCO": 11200, "INDUSINDBK": 1500,
    "BAJFINANCE": 7400,
}
COUNTERPARTIES = [
    "Northbridge Capital", "Harbor Street Securities", "Meridian Markets",
    "Atlas Prime", "Crestline Partners", "Summit Clearing",
    "Ironwood Trading", "Bluewater Brokers", "Keystone Securities", "Pinnacle Global",
]
QUANTITIES = [10, 25, 50, 75, 100, 150, 200, 300, 500]

BREAK_PLAN = (
    ["quantity_minor"] * 1 + ["quantity_major"] * 2
    + ["price_minor"] * 1 + ["price_major"] * 2
    + ["date"] * 5
    + ["counterparty"] * 3
    + ["missing_in_broker"] * 2 + ["missing_in_ledger"] * 2
)


def _business_day(start: date, offset: int) -> date:
    return pd.Timestamp(np.busday_offset(start.isoformat(), offset, roll="forward")).date()


def generate_records(rng: random.Random, count: int = TRADE_COUNT) -> list[dict[str, Any]]:
    symbols = list(SYMBOLS_BASE_PRICE)
    records = []
    for i in range(1, count + 1):
        symbol = rng.choice(symbols)
        trade_date = _business_day(FIRST_TRADE_DATE, rng.randint(0, TRADE_DAYS))
        records.append({
            "trade_id": f"T{i:05d}",
            "trade_date": trade_date.isoformat(),
            "symbol": symbol,
            "quantity": rng.choice(QUANTITIES),
            "price": round(SYMBOLS_BASE_PRICE[symbol] * rng.uniform(0.94, 1.06), 2),
            "settlement_date": _business_day(trade_date, 1).isoformat(),
            "counterparty": rng.choice(COUNTERPARTIES),
        })
    return records


def _apply_break(kind: str, rec: dict[str, Any], rng: random.Random) -> None:
    if kind == "quantity_minor":
        rec["quantity"] += rng.choice([-2, -1, 1, 2])
    elif kind == "quantity_major":
        rec["quantity"] = max(1, rec["quantity"] + rng.choice([-60, -40, 40, 60]))
    elif kind == "price_minor":
        rec["price"] = round(rec["price"] * (1 + rng.choice([-1, 1]) * rng.uniform(0.0010, 0.0020)), 2)
    elif kind == "price_major":
        rec["price"] = round(rec["price"] * (1 + rng.choice([-1, 1]) * rng.uniform(0.01, 0.03)), 2)
    elif kind == "date":
        shifted = _business_day(date.fromisoformat(rec["settlement_date"]), rng.choice([-1, 1]))
        rec["settlement_date"] = shifted.isoformat()
    elif kind == "counterparty":
        rec["counterparty"] = rng.choice([c for c in COUNTERPARTIES if c != rec["counterparty"]])


def introduce_mismatches(
    broker: list[dict[str, Any]], ledger: list[dict[str, Any]], rng: random.Random
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ids = [r["trade_id"] for r in broker]
    plan = list(BREAK_PLAN)
    rng.shuffle(plan)
    chosen = rng.sample(ids, len(plan) + round(len(ids) * BENIGN_RATE))
    break_ids, benign_ids = chosen[: len(plan)], chosen[len(plan):]

    ledger_by_id = {r["trade_id"]: r for r in ledger}
    drop_broker: set[str] = set()
    drop_ledger: set[str] = set()
    for trade_id, kind in zip(break_ids, plan):
        if kind == "missing_in_broker":
            drop_broker.add(trade_id)
        elif kind == "missing_in_ledger":
            drop_ledger.add(trade_id)
        else:
            _apply_break(kind, ledger_by_id[trade_id], rng)

    for trade_id in benign_ids:
        ledger_by_id[trade_id]["price"] = round(ledger_by_id[trade_id]["price"] + rng.choice([-0.01, 0.01]), 2)

    broker_out = [r for r in broker if r["trade_id"] not in drop_broker]
    ledger_out = [r for r in ledger if r["trade_id"] not in drop_ledger]
    for rec in rng.sample(ledger_out, DUPLICATE_LEDGER_ROWS):
        ledger_out.append(dict(rec))
    return broker_out, ledger_out


def save_csv(records: list[dict[str, Any]], filename: str) -> None:
    pd.DataFrame(records).to_csv(filename, index=False)
    print(f"Saved {len(records)} records to {filename}")


if __name__ == "__main__":
    generator = random.Random(SEED)
    broker_records = generate_records(generator)
    ledger_records = [dict(r) for r in broker_records]
    broker_records, ledger_records = introduce_mismatches(broker_records, ledger_records, generator)
    save_csv(broker_records, "broker_trades.csv")
    save_csv(ledger_records, "internal_ledger.csv")
