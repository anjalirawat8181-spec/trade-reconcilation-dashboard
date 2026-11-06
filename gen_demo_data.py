import csv
import datetime as dt
import random

random.seed(42)

HOLIDAYS = {dt.date(2026, 10, 2), dt.date(2026, 10, 20)}
N_TRADES = 66

COUNTERPARTIES = [
    "Alpha Securities", "Meridian Capital", "Orion Broking",
    "Zenith Markets", "Crestline Securities", "Vertex Financial",
]

BASE_PRICES = {
    "RELIANCE": 1400, "TCS": 3200, "HDFCBANK": 1000, "INFY": 1500,
    "ICICIBANK": 1300, "SBIN": 800, "ITC": 420, "LT": 3500,
    "BHARTIARTL": 1900, "AXISBANK": 1150, "KOTAKBANK": 2000, "MARUTI": 12000,
    "HINDUNILVR": 2400, "SUNPHARMA": 1700, "TATAMOTORS": 750,
    "ASIANPAINT": 2400, "BAJFINANCE": 900, "WIPRO": 260, "ONGC": 250, "NTPC": 340,
}
QTYS = [10, 25, 50, 75, 100, 150, 200, 250, 300, 500]


def is_bd(d):
    return d.weekday() < 5 and d not in HOLIDAYS


def next_bd(d):
    d += dt.timedelta(days=1)
    while not is_bd(d):
        d += dt.timedelta(days=1)
    return d


bdays, d = [], dt.date(2026, 9, 14)
while d <= dt.date(2026, 11, 4):
    if is_bd(d):
        bdays.append(d)
    d += dt.timedelta(days=1)

trades = []
for i in range(N_TRADES):
    sym = random.choice(list(BASE_PRICES))
    price = round(BASE_PRICES[sym] * (1 + random.uniform(-0.03, 0.03)), 2)
    td = random.choice(bdays)
    trades.append({
        "trade_id": "",
        "trade_date": td,
        "symbol": sym,
        "quantity": random.choice(QTYS),
        "price": price,
        "settlement_date": next_bd(td),
        "counterparty": random.choice(COUNTERPARTIES),
    })
trades.sort(key=lambda t: (t["trade_date"], t["symbol"]))
for i, t in enumerate(trades, 1):
    t["trade_id"] = f"T{i:05d}"

broker = [dict(t) for t in trades]
ledger = [dict(t) for t in trades]

notional = lambda t: t["quantity"] * t["price"]
by_notional = sorted(range(N_TRADES), key=lambda i: -notional(trades[i]))
price_big = by_notional[0]
rest = [i for i in range(N_TRADES) if i != price_big]
random.shuffle(rest)
qty_a, qty_b, price_small, date_b, cpty_b, miss_ledger = rest[:6]
tol_pool = [i for i in rest[6:] if trades[i]["price"] >= 400]
tol1, tol2 = tol_pool[:2]

key = []


ledger[price_big]["price"] = round(trades[price_big]["price"] * 1.012, 2)
key.append((trades[price_big]["trade_id"], "price_mismatch"))
ledger[price_small]["price"] = round(trades[price_small]["price"] * 0.9925, 2)
key.append((trades[price_small]["trade_id"], "price_mismatch"))


for i in (qty_a, qty_b):
    ledger[i]["quantity"] = trades[i]["quantity"] + 20
    key.append((trades[i]["trade_id"], "quantity_mismatch"))


ledger[date_b]["settlement_date"] = next_bd(trades[date_b]["settlement_date"])
key.append((trades[date_b]["trade_id"], "settlement_date_mismatch"))


other = [c for c in COUNTERPARTIES if c != trades[cpty_b]["counterparty"]]
ledger[cpty_b]["counterparty"] = random.choice(other)
key.append((trades[cpty_b]["trade_id"], "counterparty_mismatch"))


tol_ids = []
for i in (tol1, tol2):
    new_p = round(trades[i]["price"] * 1.0002, 2)
    bps = abs(new_p - trades[i]["price"]) / trades[i]["price"] * 1e4
    assert 0 < bps < 5, bps
    assert ledger[i]["trade_id"] == trades[i]["trade_id"]
    ledger[i]["price"] = new_p
    tol_ids.append(trades[i]["trade_id"])


missing_ledger_id = trades[miss_ledger]["trade_id"]
ledger = [t for t in ledger if t["trade_id"] != missing_ledger_id]
key.append((missing_ledger_id, "missing_in_ledger"))


extra_sym = "INFY"
extra_td = bdays[-1]
extra = {
    "trade_id": f"T{N_TRADES + 1:05d}",
    "trade_date": extra_td,
    "symbol": extra_sym,
    "quantity": 100,
    "price": round(BASE_PRICES[extra_sym] * 1.004, 2),
    "settlement_date": next_bd(extra_td),
    "counterparty": "Orion Broking",
}
ledger.append(extra)
key.append((extra["trade_id"], "missing_in_broker"))

FIELDS = ["trade_id", "trade_date", "symbol", "quantity", "price",
          "settlement_date", "counterparty"]


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in sorted(rows, key=lambda r: r["trade_id"]):
            w.writerow({k: (r[k].isoformat() if isinstance(r[k], dt.date) else r[k])
                        for k in FIELDS})


write("broker_trades.csv", broker)
write("internal_ledger.csv", ledger)

print(f"broker rows: {len(broker)}, ledger rows: {len(ledger)}")
print(f"unique trade ids: {len({t['trade_id'] for t in broker} | {t['trade_id'] for t in ledger})}")
print("expected breaks:")
by_id = {t["trade_id"]: t for t in trades}
for tid, kind in sorted(key):
    t = by_id.get(tid)
    n = f"{notional(t):,.0f}" if t else "-"
    print(f"  {tid}  {kind:26s} {t['symbol'] if t else extra_sym:11s} notional~{n}")
print("within tolerance (should NOT be flagged at 5 bps):", ", ".join(tol_ids))
