import random
from datetime import datetime, timedelta
import pandas as pd

# More realistic symbol set and larger counterparty universe
SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "BAC", "V", "NVDA", "DIS",
    "NFLX", "KO", "PFE", "CSCO", "CRM", "BA", "IBM", "WMT", "MCD", "PEP",
]
COUNTERPARTIES = [
    "Goldman Sachs",
    "Morgan Stanley",
    "Citibank",
    "Barclays",
    "Deutsche Bank",
    "UBS",
    "Credit Suisse",
    "HSBC",
    "BofA Securities",
    "Nomura",
]

BASE_DATE = datetime(2026, 4, 1)
DATE_RANGE_DAYS = 90


def random_trade_date():
    return BASE_DATE + timedelta(days=random.randint(0, DATE_RANGE_DAYS))


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
        "NFLX": 360,
        "KO": 60,
        "PFE": 42,
        "CSCO": 55,
        "CRM": 220,
        "BA": 210,
        "IBM": 145,
        "WMT": 160,
        "MCD": 300,
        "PEP": 190,
    }
    return round(random.uniform(base[symbol] * 0.94, base[symbol] * 1.06), 2)


def random_quantity():
    return random.choice([50, 75, 100, 150, 200, 250, 300, 400, 500])


def generate_records(count=500):
    records = []
    for i in range(1, count + 1):
        symbol = random.choice(SYMBOLS)
        trade_date = random_trade_date()
        quantity = random_quantity()
        price = random_price(symbol)
        settlement_date = trade_date + timedelta(days=random.choice([1, 2, 3]))
        records.append(
            {
                "trade_id": f"T{i:05d}",
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
    # Keep the break rate realistic, around 12-18% of trades.
    mismatch_count = int(len(broker_records) * 0.15)
    mismatch_ids = random.sample([r["trade_id"] for r in broker_records], mismatch_count)

    for trade_id in mismatch_ids:
        action = random.choices(
            ["date", "price_low", "quantity_low", "price_high", "quantity_high", "missing"],
            weights=[0.30, 0.20, 0.20, 0.05, 0.05, 0.20],
            k=1,
        )[0]

        if action == "missing":
            if random.random() < 0.5:
                ledger_records = [r for r in ledger_records if r["trade_id"] != trade_id]
            else:
                broker_records = [r for r in broker_records if r["trade_id"] != trade_id]
            continue

        for record in ledger_records:
            if record["trade_id"] != trade_id:
                continue

            if action == "date":
                record["settlement_date"] = (
                    datetime.strptime(record["settlement_date"], "%Y-%m-%d")
                    + timedelta(days=random.choice([-1, 1]))
                ).strftime("%Y-%m-%d")
            elif action == "price_low":
                record["price"] = round(record["price"] * random.uniform(0.995, 1.005), 2)
            elif action == "quantity_low":
                record["quantity"] = max(1, record["quantity"] + random.choice([-2, -1, 1, 2, 3]))
            elif action == "price_high":
                record["price"] = round(record["price"] * random.uniform(0.93, 0.97), 2)
            elif action == "quantity_high":
                record["quantity"] = max(1, record["quantity"] + random.choice([-80, -60, 60, 80]))
            break

    duplicate_ids = random.sample([r["trade_id"] for r in ledger_records], min(10, len(ledger_records)))
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
    broker = generate_records(count=500)
    ledger = [dict(r) for r in broker]

    broker, ledger = introduce_mismatches(broker, ledger)

    save_csv(broker, "broker_trades.csv")
    save_csv(ledger, "internal_ledger.csv")
