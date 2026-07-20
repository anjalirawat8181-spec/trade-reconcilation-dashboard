import pandas as pd


def load_trades(path: str) -> pd.DataFrame:
    """Load a CSV file into a pandas DataFrame and normalize the columns."""
    df = pd.read_csv(path, dtype={"trade_id": str})
    df = df.drop_duplicates().copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"]) 
    df["settlement_date"] = pd.to_datetime(df["settlement_date"]) 
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    return df


def classify_severity(break_type: str, broker_value=None, ledger_value=None) -> str:
    """Classify break severity based on type and mismatch size."""
    if break_type in {"missing_in_broker", "missing_in_ledger", "duplicate_in_broker", "duplicate_in_ledger"}:
        return "HIGH"

    if break_type == "quantity_mismatch":
        if broker_value is None or ledger_value is None:
            return "HIGH"
        diff_pct = abs(broker_value - ledger_value) / max(abs(ledger_value), 1)
        return "HIGH" if diff_pct >= 0.02 else "LOW"

    if break_type == "price_mismatch":
        if broker_value is None or ledger_value is None:
            return "HIGH"
        diff_pct = abs(broker_value - ledger_value) / max(abs(ledger_value), 0.01)
        return "HIGH" if diff_pct >= 0.01 else "LOW"

    if break_type == "settlement_date_mismatch":
        return "MEDIUM"

    return "LOW"


def reconcile_trades(broker_path: str, ledger_path: str) -> pd.DataFrame:
    """Compare broker and ledger trades and return a DataFrame of breaks."""
    broker = load_trades(broker_path)
    ledger = load_trades(ledger_path)

    broker_counts = broker["trade_id"].value_counts()
    ledger_counts = ledger["trade_id"].value_counts()

    duplicate_breaks = []
    for trade_id, count in broker_counts.items():
        if count > 1:
            duplicate_breaks.append({
                "trade_id": trade_id,
                "break_type": "duplicate_in_broker",
                "broker_quantity": broker[broker["trade_id"] == trade_id]["quantity"].tolist(),
                "ledger_quantity": None,
                "broker_price": broker[broker["trade_id"] == trade_id]["price"].tolist(),
                "ledger_price": None,
                "broker_settlement_date": broker[broker["trade_id"] == trade_id]["settlement_date"].dt.strftime("%Y-%m-%d").tolist(),
                "ledger_settlement_date": None,
            })

    for trade_id, count in ledger_counts.items():
        if count > 1:
            duplicate_breaks.append({
                "trade_id": trade_id,
                "break_type": "duplicate_in_ledger",
                "broker_quantity": None,
                "ledger_quantity": ledger[ledger["trade_id"] == trade_id]["quantity"].tolist(),
                "broker_price": None,
                "ledger_price": ledger[ledger["trade_id"] == trade_id]["price"].tolist(),
                "broker_settlement_date": None,
                "ledger_settlement_date": ledger[ledger["trade_id"] == trade_id]["settlement_date"].dt.strftime("%Y-%m-%d").tolist(),
            })

    broker_unique = broker.drop_duplicates(subset=["trade_id"]).set_index("trade_id")
    ledger_unique = ledger.drop_duplicates(subset=["trade_id"]).set_index("trade_id")

    all_ids = sorted(set(broker_unique.index) | set(ledger_unique.index))
    break_rows = []

    for trade_id in all_ids:
        broker_row = broker_unique.loc[trade_id] if trade_id in broker_unique.index else None
        ledger_row = ledger_unique.loc[trade_id] if trade_id in ledger_unique.index else None

        if broker_row is None:
            break_rows.append({
                "trade_id": trade_id,
                "break_type": "missing_in_broker",
                "broker_quantity": None,
                "ledger_quantity": ledger_row["quantity"],
                "broker_price": None,
                "ledger_price": ledger_row["price"],
                "broker_settlement_date": None,
                "ledger_settlement_date": ledger_row["settlement_date"].strftime("%Y-%m-%d"),
            })
            continue

        if ledger_row is None:
            break_rows.append({
                "trade_id": trade_id,
                "break_type": "missing_in_ledger",
                "broker_quantity": broker_row["quantity"],
                "ledger_quantity": None,
                "broker_price": broker_row["price"],
                "ledger_price": None,
                "broker_settlement_date": broker_row["settlement_date"].strftime("%Y-%m-%d"),
                "ledger_settlement_date": None,
            })
            continue

        if broker_row["quantity"] != ledger_row["quantity"]:
            break_rows.append({
                "trade_id": trade_id,
                "break_type": "quantity_mismatch",
                "broker_quantity": broker_row["quantity"],
                "ledger_quantity": ledger_row["quantity"],
                "broker_price": broker_row["price"],
                "ledger_price": ledger_row["price"],
                "broker_settlement_date": broker_row["settlement_date"].strftime("%Y-%m-%d"),
                "ledger_settlement_date": ledger_row["settlement_date"].strftime("%Y-%m-%d"),
            })
            continue

        if round(broker_row["price"], 2) != round(ledger_row["price"], 2):
            break_rows.append({
                "trade_id": trade_id,
                "break_type": "price_mismatch",
                "broker_quantity": broker_row["quantity"],
                "ledger_quantity": ledger_row["quantity"],
                "broker_price": broker_row["price"],
                "ledger_price": ledger_row["price"],
                "broker_settlement_date": broker_row["settlement_date"].strftime("%Y-%m-%d"),
                "ledger_settlement_date": ledger_row["settlement_date"].strftime("%Y-%m-%d"),
            })
            continue

        if broker_row["settlement_date"] != ledger_row["settlement_date"]:
            break_rows.append({
                "trade_id": trade_id,
                "break_type": "settlement_date_mismatch",
                "broker_quantity": broker_row["quantity"],
                "ledger_quantity": ledger_row["quantity"],
                "broker_price": broker_row["price"],
                "ledger_price": ledger_row["price"],
                "broker_settlement_date": broker_row["settlement_date"].strftime("%Y-%m-%d"),
                "ledger_settlement_date": ledger_row["settlement_date"].strftime("%Y-%m-%d"),
            })
    
    break_rows.extend(duplicate_breaks)

    for row in break_rows:
        row["severity"] = classify_severity(
            row["break_type"],
            row.get("broker_quantity"),
            row.get("ledger_quantity"),
        )

    return pd.DataFrame(break_rows)


if __name__ == "__main__":
    breaks = reconcile_trades("broker_trades.csv", "internal_ledger.csv")
    print(f"Found {len(breaks)} breaks")
    print(breaks[["break_type", "severity"]].value_counts())
