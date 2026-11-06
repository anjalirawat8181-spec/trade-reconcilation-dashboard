"""Pure dashboard maths (no Streamlit): KPIs, status handling, formatting."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

import pandas as pd

from recon_engine import clean_trades

STATUSES: tuple[str, ...] = ("Open", "Investigating", "Resolved")
DEFAULT_STATUS = "Open"


@dataclass(frozen=True)
class Kpis:
    """Headline numbers shown on the Overview tab."""

    match_rate_pct: Optional[float]
    open_breaks: int
    open_notional: float
    oldest_open_days: Optional[int]


def attach_status(breaks: pd.DataFrame, statuses: Mapping[str, str]) -> pd.DataFrame:
    """Return ``breaks`` with a ``status`` column (default ``Open``)."""
    out = breaks.copy()
    out["status"] = out["trade_id"].map(statuses).fillna(DEFAULT_STATUS)
    return out


def latest_settlement(broker: pd.DataFrame, ledger: pd.DataFrame) -> Optional[pd.Timestamp]:
    """Latest settlement date across both datasets; used as the 'as of' date for ageing."""
    dates = pd.concat([clean_trades(broker)["settlement_date"], clean_trades(ledger)["settlement_date"]])
    latest = dates.max()
    return None if pd.isna(latest) else latest


def compute_kpis(
    breaks: pd.DataFrame, total_trades: int, as_of: Optional[pd.Timestamp]
) -> Kpis:
    """Headline KPIs. ``breaks`` must carry a ``status`` column.

    * Match rate: share of unique trades with no break (resolution does not change it).
    * Open breaks / notional: every break whose status is not ``Resolved``.
    * Oldest open break: days between its settlement date and ``as_of``.
    """
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
    """Number of breaks per status, in display order (zeros included)."""
    counts = breaks["status"].value_counts()
    return {s: int(counts.get(s, 0)) for s in STATUSES}


def format_currency(value: Optional[float]) -> str:
    """``1234567.8`` -> ``$1,234,568``; None/NaN -> an em dash."""
    return "—" if value is None or pd.isna(value) else f"${value:,.0f}"
