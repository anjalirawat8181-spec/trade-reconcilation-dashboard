from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

import pandas as pd

import theme as t
from recon_engine import clean_trades

try:
    from babel.numbers import format_currency as _babel_format_currency
except Exception:
    _babel_format_currency = None

STATUSES: tuple[str, ...] = ("Open", "Investigating", "Resolved")
DEFAULT_STATUS = "Open"


@dataclass(frozen=True)
class Kpis:

    match_rate_pct: Optional[float]
    open_breaks: int
    open_notional: float
    oldest_open_days: Optional[int]


def attach_status(breaks: pd.DataFrame, statuses: Mapping[str, str]) -> pd.DataFrame:
    out = breaks.copy()
    out["status"] = out["trade_id"].map(statuses).fillna(DEFAULT_STATUS)
    return out


def latest_settlement(broker: pd.DataFrame, ledger: pd.DataFrame) -> Optional[pd.Timestamp]:
    dates = pd.concat([clean_trades(broker)["settlement_date"], clean_trades(ledger)["settlement_date"]])
    latest = dates.max()
    return None if pd.isna(latest) else latest


def compute_kpis(
    breaks: pd.DataFrame, total_trades: int, as_of: Optional[pd.Timestamp]
) -> Kpis:
    match_rate = None if total_trades <= 0 else round(100 * (1 - len(breaks) / total_trades), 1)
    open_breaks = breaks[breaks["status"] != "Resolved"]
    oldest: Optional[int] = None
    if not open_breaks.empty and as_of is not None:
        oldest = max(int((as_of - open_breaks["break_date"].min()).days), 0)
    return Kpis(
        match_rate_pct=match_rate,
        open_breaks=len(open_breaks),
        open_notional=float(open_breaks["notional"].sum()),
        oldest_open_days=oldest,
    )


def status_counts(breaks: pd.DataFrame) -> dict[str, int]:
    counts = breaks["status"].value_counts()
    return {s: int(counts.get(s, 0)) for s in STATUSES}


def _indian_group(value: int) -> str:
    s = str(abs(int(value)))
    if len(s) <= 3:
        return s
    last_three = s[-3:]
    rest = s[:-3]
    if len(rest) <= 2:
        return f"{rest},{last_three}"
    chunks: list[str] = []
    while len(rest) > 2:
        chunks.append(rest[-2:])
        rest = rest[:-2]
    if rest:
        chunks.append(rest)
    chunks.reverse()
    return ",".join(chunks + [last_three])


def format_inr(value: Optional[float], compact: bool = False) -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"

    if not compact and _babel_format_currency is not None:
        try:
            return _babel_format_currency(number, currency=t.CURRENCY_CODE, locale="en_IN")
        except Exception:
            pass

    if compact:
        abs_value = abs(number)
        if abs_value >= 1_00_00_000:
            return f"{('-' if number < 0 else '')}{t.CURRENCY_SYMBOL}{abs_value / 1_00_00_000:.1f} Cr"
        if abs_value >= 1_00_000:
            return f"{('-' if number < 0 else '')}{t.CURRENCY_SYMBOL}{abs_value / 1_00_000:.1f} L"
        return f"{('-' if number < 0 else '')}{t.CURRENCY_SYMBOL}{abs_value:,.0f}"

    sign = "-" if number < 0 else ""
    abs_value = abs(number)
    integer_part = int(abs_value)
    decimals = abs_value - integer_part
    integer_str = _indian_group(integer_part)
    decimal_str = f"{decimals:.2f}"[2:]
    return f"{sign}{t.CURRENCY_SYMBOL}{integer_str}.{decimal_str}"


def format_currency(value: Optional[float]) -> str:
    return format_inr(value)
