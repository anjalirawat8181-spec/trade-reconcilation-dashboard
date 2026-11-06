"""Single source of truth for the visual palette and presentation labels.

Colours are defined once here and reused by the CSS (styles.py), the charts
(charts.py) and the table badges (app.py). The same hex values appear in
.streamlit/config.toml, which Streamlit reads before Python runs.
"""
from __future__ import annotations

NAVY = "#0D1B2A"
MID_NAVY = "#1B3A5C"
ACCENT = "#7399C6"
TINT = "#E8EEF5"
PAGE_BG = "#FFFFFF"
BORDER = "#E5E7EB"
MUTED = "#5B6B7C"
CURRENCY_SYMBOL = "₹"
CURRENCY_CODE = "INR"

HIGH = "#B3261E"
MEDIUM = "#C98A1B"
LOW = "#7399C6"

SEVERITY_COLORS: dict[str, str] = {"HIGH": HIGH, "MEDIUM": MEDIUM, "LOW": LOW}
SEVERITY_ORDER: tuple[str, ...] = ("HIGH", "MEDIUM", "LOW")

FONT_FAMILY = "'Tinos', 'Times New Roman', Times, serif"
HEADING_FONT = "Newsreader, Georgia, 'Times New Roman', serif"
RADIUS_PX = 8

BREAK_TYPE_LABELS: dict[str, str] = {
    "quantity_mismatch": "Quantity mismatch",
    "price_mismatch": "Price mismatch",
    "settlement_date_mismatch": "Settlement date mismatch",
    "counterparty_mismatch": "Counterparty mismatch",
    "missing_in_broker": "Missing in broker",
    "missing_in_ledger": "Missing in ledger",
}


def tint(color: str, alpha_hex: str = "1F") -> str:
    """Return ``color`` with an 8-digit-hex alpha suffix (default ~12% opacity)."""
    return f"{color}{alpha_hex}"
