import random
from datetime import datetime, timedelta
import pandas as pd

# Realistic stock symbols and counterparties
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "BAC", "V", "NVDA", "DIS"]
COUNTERPARTIES = ["Goldman Sachs", "Morgan Stanley", "Citibank", "Barclays", "Deutsche Bank"]

BASE_DATE = datetime(2026, 6, 1)


def random_trade_date(index):
    return BASE_DATE + timedelta(days=index // 5)


def random_price(symbol):
    base = {
        "AAPL": 170,
        "MSFT": 360,
        "GOOGL": 145,
        "AMZN": 140,
        "TSLA": 230,
        "JPM": 145,
        "BAC": 30,
        "V": 235,
        "NVDA": 720,
        "DIS": 85,
    }
    return round(random.uniform(base[symbol] * 0.95, base[symbol] * 1.05), 2)


def random_quantity():
    return random.choice([100, 150, 200, 250, 300, 400, 500])


def generate_records(count=100):
    records = []
    for i in range(1, count + 1):
        symbol = random.choice(SYMBOLS)
        trade_date = random_trade_date(i)
        quantity = random_quantity()
        price = random_price(symbol)
        settlement_date = trade_date + timedelta(days=random.choice([1, 2, 3]))
        records.append(
            {
                "trade_id": f"T{i:04d}",
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "settlement_date": settlement_date.strftime("%Y-%m-%d"),
                "counterparty": random.choice(COUNTERPARTIES),
            }
        )
    return records


def introduce_mismatches(broker_records, ledger_records):
    # Randomly choose trades to mismatch
    mismatch_count = int(len(broker_records) * 0.18)
    mismatch_ids = random.sample([r["trade_id"] for r in broker_records], mismatch_count)

    for trade_id in mismatch_ids:
        if random.random() < 0.2:
            # Remove trade from ledger or broker to create a missing record
            if random.random() < 0.5 and ledger_records:
                ledger_records = [r for r in ledger_records if r["trade_id"] != trade_id]
            else:
                broker_records = [r for r in broker_records if r["trade_id"] != trade_id]
            continue

        # Apply mismatches for existing trades
        for record in ledger_records:
            if record["trade_id"] == trade_id:
                if random.random() < 0.4:
                    record["quantity"] = record["quantity"] + random.choice([-50, 50, 100])
                if random.random() < 0.4:
                    record["price"] = round(record["price"] * random.choice([0.97, 0.98, 1.02, 1.03]), 2)
                if random.random() < 0.4:
                    record["settlement_date"] = (
                        datetime.strptime(record["settlement_date"], "%Y-%m-%d")
                        + timedelta(days=random.choice([-1, 1]))
                    ).strftime("%Y-%m-%d")
                break

    # Duplicate a few ledger entries to simulate duplicate booking
    duplicate_ids = random.sample([r["trade_id"] for r in ledger_records], min(3, len(ledger_records)))
    for trade_id in duplicate_ids:
        for record in ledger_records:
            if record["trade_id"] == trade_id:
                ledger_records.append(record.copy())
                break

    return broker_records, ledger_records


def save_csv(records, filename):
    df = pd.DataFrame(records)
    df.to_csv(filename, index=False)
    print(f"Saved {len(records)} records to {filename}")


if __name__ == "__main__":
    broker = generate_records(count=100)
    ledger = [dict(r) for r in broker]

    broker, ledger = introduce_mismatches(broker, ledger)

    save_csv(broker, "broker_trades.csv")
    save_csv(ledger, "internal_ledger.csv")
