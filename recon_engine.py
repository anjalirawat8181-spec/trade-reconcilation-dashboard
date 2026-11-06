from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd

import theme as t

REQUIRED_COLUMNS: tuple[str, ...] = (
    "trade_id",
    "trade_date",
    "symbol",
    "quantity",
    "price",
    "settlement_date",
    "counterparty",
)

BREAK_TYPES: tuple[str, ...] = (
    "quantity_mismatch",
    "price_mismatch",
    "settlement_date_mismatch",
    "counterparty_mismatch",
    "missing_in_broker",
    "missing_in_ledger",
)

SEVERITIES: tuple[str, ...] = ("HIGH", "MEDIUM", "LOW")
_SEVERITY_RANK = {name: rank for rank, name in enumerate(SEVERITIES)}

_FIELD_BREAK_TYPE: dict[str, str] = {
    "quantity": "quantity_mismatch",
    "price": "price_mismatch",
    "settlement_date": "settlement_date_mismatch",
    "counterparty": "counterparty_mismatch",
}

BREAK_COLUMNS: tuple[str, ...] = (
    "trade_id",
    "break_type",
    "severity",
    "severity_reason",
    "differing_fields",
    "symbol",
    "trade_date",
    "break_date",
    "broker_quantity",
    "ledger_quantity",
    "broker_price",
    "ledger_price",
    "broker_settlement_date",
    "ledger_settlement_date",
    "broker_counterparty",
    "ledger_counterparty",
    "broker_notional",
    "ledger_notional",
    "notional",
)


@dataclass(frozen=True)
class ReconConfig:

    price_tolerance_bps: float = 5.0
    settlement_tolerance_days: int = 0
    quantity_tolerance: float = 0.0
    medium_notional_threshold: float = 1_000_000.0
    high_notional_threshold: float = 10_000_000.0
    minor_price_bps: float = 25.0
    minor_quantity: float = 5.0


def load_trades_csv(source: Any) -> pd.DataFrame:
    try:
        return pd.read_csv(source, dtype={"trade_id": str})
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The file is empty.") from exc
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValueError(f"The file is not a valid CSV ({exc}).") from exc


def validate_trades(df: pd.DataFrame) -> list[str]:
    columns = {str(c).strip().lower() for c in df.columns}
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    errors: list[str] = []
    if missing:
        errors.append("Missing required column(s): " + ", ".join(missing))
    if df.empty:
        errors.append("The file contains a header but no trade rows.")
    return errors


def clean_trades(df: pd.DataFrame) -> pd.DataFrame:
    errors = [e for e in validate_trades(df) if e.startswith("Missing")]
    if errors:
        raise ValueError(errors[0])

    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    out = out[list(REQUIRED_COLUMNS)]

    ids = out["trade_id"].astype("string").str.strip()
    out = out.assign(trade_id=ids)
    out = out[out["trade_id"].notna() & out["trade_id"].ne("")]
    out["trade_id"] = out["trade_id"].astype(str)

    for col in ("trade_date", "settlement_date"):
        out[col] = pd.to_datetime(out[col], errors="coerce").dt.normalize()
    for col in ("quantity", "price"):
        out[col] = pd.to_numeric(out[col], errors="coerce").astype(float)
    for col in ("symbol", "counterparty"):
        out[col] = out[col].fillna("").astype(str).str.strip()

    out = out.drop_duplicates(subset="trade_id", keep="first")
    return out.reset_index(drop=True)


def data_quality(df: pd.DataFrame) -> dict[str, int]:
    if not set(REQUIRED_COLUMNS) <= {str(c).strip().lower() for c in df.columns}:
        return {"rows": len(df), "blank_ids": 0, "duplicate_ids": 0, "invalid_values": 0}
    raw = df.copy()
    raw.columns = [str(c).strip().lower() for c in raw.columns]
    ids = raw["trade_id"].astype("string").str.strip()
    blank = ids.isna() | ids.eq("")
    dups = ids[~blank].duplicated().sum()
    invalid = 0
    for col in ("trade_date", "settlement_date"):
        invalid += int((pd.to_datetime(raw[col], errors="coerce").isna() & raw[col].notna()).sum())
    for col in ("quantity", "price"):
        invalid += int((pd.to_numeric(raw[col], errors="coerce").isna() & raw[col].notna()).sum())
    return {
        "rows": int(len(raw)),
        "blank_ids": int(blank.sum()),
        "duplicate_ids": int(dups),
        "invalid_values": invalid,
    }


def count_unique_trades(broker: pd.DataFrame, ledger: pd.DataFrame) -> int:
    ids = pd.concat([clean_trades(broker)["trade_id"], clean_trades(ledger)["trade_id"]])
    return int(ids.nunique())


def _nan_mismatch(a: pd.Series, b: pd.Series) -> pd.Series:
    return a.isna() ^ b.isna()


def quantity_mismatch_mask(b: pd.Series, l: pd.Series, tolerance: float) -> pd.Series:
    diff = (b - l).abs().round(9)
    return _nan_mismatch(b, l) | (diff > tolerance)


def price_diff_bps(b: pd.Series, l: pd.Series) -> pd.Series:
    diff = (b - l).abs()
    denom = l.abs()
    with np.errstate(divide="ignore", invalid="ignore"):
        bps = np.where(denom > 0, diff / denom * 1e4, np.where(diff > 0, np.inf, 0.0))
    return pd.Series(bps, index=b.index).round(9)


def price_mismatch_mask(b: pd.Series, l: pd.Series, tolerance_bps: float) -> pd.Series:
    return _nan_mismatch(b, l) | (price_diff_bps(b, l) > tolerance_bps)


def date_mismatch_mask(b: pd.Series, l: pd.Series, tolerance_days: int) -> pd.Series:
    days = (b - l).dt.days.abs()
    return _nan_mismatch(b, l) | (days > tolerance_days)


def text_mismatch_mask(b: pd.Series, l: pd.Series) -> pd.Series:
    return b.fillna("").str.casefold() != l.fillna("").str.casefold()


def _notional(quantity: Any, price: Any) -> float:
    if pd.isna(quantity) or pd.isna(price):
        return 0.0
    return float(abs(quantity) * price)


def field_severity(field: str, row: pd.Series, notional: float, cfg: ReconConfig) -> tuple[str, str]:
    if notional >= cfg.high_notional_threshold:
        return "HIGH", (
            f"Notional {t.CURRENCY_SYMBOL}{notional:,.0f} is at or above the HIGH threshold "
            f"({t.CURRENCY_SYMBOL}{cfg.high_notional_threshold:,.0f})."
        )
    if notional >= cfg.medium_notional_threshold:
        return "MEDIUM", (
            f"Notional {t.CURRENCY_SYMBOL}{notional:,.0f} is at or above the MEDIUM threshold "
            f"({t.CURRENCY_SYMBOL}{cfg.medium_notional_threshold:,.0f})."
        )
    if field == "quantity":
        gap = abs(row["quantity_broker"] - row["quantity_ledger"])
        if gap <= cfg.minor_quantity:
            return "LOW", f"Quantity differs by {gap:g}, within the minor limit of {cfg.minor_quantity:g}."
        return "MEDIUM", f"Quantity differs by {gap:g}, above the minor limit of {cfg.minor_quantity:g}."
    if field == "price":
        bps = float(price_diff_bps(pd.Series([row["price_broker"]]), pd.Series([row["price_ledger"]])).iloc[0])
        if bps <= cfg.minor_price_bps:
            return "LOW", f"Price differs by {bps:.1f} bps, within the minor limit of {cfg.minor_price_bps:g} bps."
        return "MEDIUM", f"Price differs by {bps:.1f} bps, above the minor limit of {cfg.minor_price_bps:g} bps."
    if field == "counterparty":
        return "MEDIUM", "Counterparty differs between broker and ledger; settlement may go to the wrong party."
    return "LOW", "Settlement date differs; no change to economics, but timing risk."


def classify_break(row: pd.Series, fields: list[str], cfg: ReconConfig) -> tuple[str, str, str]:
    if row["_merge"] == "left_only":
        return "missing_in_ledger", "HIGH", "Broker reports this trade but it is not booked in the ledger."
    if row["_merge"] == "right_only":
        return "missing_in_broker", "HIGH", "Ledger holds this trade but the broker has no matching record."

    notional = _notional(row["quantity_broker"], row["price_broker"])
    assessed = [(f, *field_severity(f, row, notional, cfg)) for f in fields]
    best = min(assessed, key=lambda a: _SEVERITY_RANK[a[1]])
    return _FIELD_BREAK_TYPE[best[0]], best[1], best[2]


def _empty_breaks() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in BREAK_COLUMNS})


def _differing_fields(m: pd.DataFrame, cfg: ReconConfig) -> pd.DataFrame:
    both = m["_merge"] == "both"
    masks = {
        "quantity": quantity_mismatch_mask(m["quantity_broker"], m["quantity_ledger"], cfg.quantity_tolerance),
        "price": price_mismatch_mask(m["price_broker"], m["price_ledger"], cfg.price_tolerance_bps),
        "settlement_date": date_mismatch_mask(
            m["settlement_date_broker"], m["settlement_date_ledger"], cfg.settlement_tolerance_days
        ),
        "counterparty": text_mismatch_mask(m["counterparty_broker"], m["counterparty_ledger"]),
    }
    return pd.DataFrame({k: v & both for k, v in masks.items()})


def _build_break_row(row: pd.Series, fields: list[str], cfg: ReconConfig) -> dict[str, Any]:
    break_type, severity, reason = classify_break(row, fields, cfg)
    b_notional = _notional(row["quantity_broker"], row["price_broker"]) if row["_merge"] != "right_only" else np.nan
    l_notional = _notional(row["quantity_ledger"], row["price_ledger"]) if row["_merge"] != "left_only" else np.nan
    from_broker = row["_merge"] != "right_only"
    pick = (lambda col: row[f"{col}_broker"]) if from_broker else (lambda col: row[f"{col}_ledger"])
    return {
        "trade_id": row["trade_id"],
        "break_type": break_type,
        "severity": severity,
        "severity_reason": reason,
        "differing_fields": ",".join(fields),
        "symbol": pick("symbol"),
        "trade_date": pick("trade_date"),
        "break_date": pick("settlement_date"),
        "broker_quantity": row["quantity_broker"],
        "ledger_quantity": row["quantity_ledger"],
        "broker_price": row["price_broker"],
        "ledger_price": row["price_ledger"],
        "broker_settlement_date": row["settlement_date_broker"],
        "ledger_settlement_date": row["settlement_date_ledger"],
        "broker_counterparty": row["counterparty_broker"] if from_broker else np.nan,
        "ledger_counterparty": row["counterparty_ledger"] if row["_merge"] != "left_only" else np.nan,
        "broker_notional": b_notional,
        "ledger_notional": l_notional,
        "notional": b_notional if from_broker else l_notional,
    }


def reconcile(broker: pd.DataFrame, ledger: pd.DataFrame, config: Optional[ReconConfig] = None) -> pd.DataFrame:
    cfg = config or ReconConfig()
    b = clean_trades(broker)
    l = clean_trades(ledger)
    merged = b.merge(l, on="trade_id", how="outer", suffixes=("_broker", "_ledger"), indicator=True)
    if merged.empty:
        return _empty_breaks()

    flags = _differing_fields(merged, cfg)
    broken = (merged["_merge"] != "both") | flags.any(axis=1)
    if not broken.any():
        return _empty_breaks()

    records = []
    for idx in merged.index[broken]:
        fields = [f for f in _FIELD_BREAK_TYPE if flags.at[idx, f]]
        records.append(_build_break_row(merged.loc[idx], fields, cfg))

    out = pd.DataFrame.from_records(records, columns=list(BREAK_COLUMNS))
    out["_rank"] = out["severity"].map(_SEVERITY_RANK)
    out = out.sort_values(["_rank", "trade_id"], kind="stable").drop(columns="_rank")
    return out.reset_index(drop=True)


if __name__ == "__main__":
    result = reconcile(load_trades_csv("broker_trades.csv"), load_trades_csv("internal_ledger.csv"))
    print(f"Found {len(result)} breaks")
    print(result[["break_type", "severity"]].value_counts())
