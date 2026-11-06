"""Settlement Reconciliation Workbench: Streamlit UI only.

All reconciliation logic lives in recon_engine.py, KPI maths in metrics.py,
charts in charts.py, palette in theme.py and CSS in styles.py.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from html import escape
from typing import Optional

import pandas as pd
import streamlit as st

import charts
import metrics
import recon_engine as engine
import theme as t
from styles import inject_styles

PRODUCT_NAME = "Settlement Reconciliation Workbench"
SAMPLE_BROKER = "broker_trades.csv"
SAMPLE_LEDGER = "internal_ledger.csv"
DASH = "—"

st.set_page_config(page_title=PRODUCT_NAME, page_icon="▦", layout="wide")
inject_styles()


# --------------------------------------------------------------------------
# Data loading (sidebar)
# --------------------------------------------------------------------------
@dataclass
class Dataset:
    """Validated broker + ledger frames, plus notes about data quality."""

    broker: pd.DataFrame
    ledger: pd.DataFrame
    notes: list[str]


def _read_upload(label: str, upload) -> tuple[Optional[pd.DataFrame], list[str]]:
    """Parse and validate one uploaded CSV; return (frame, error messages)."""
    try:
        df = engine.load_trades_csv(io.BytesIO(upload.getvalue()))
    except ValueError as exc:
        return None, [f"{label}: {exc}"]
    errors = engine.validate_trades(df)
    if errors:
        return None, [f"{label}: {e}" for e in errors]
    return df, []


def _quality_notes(label: str, df: pd.DataFrame) -> list[str]:
    q = engine.data_quality(df)
    checks = [
        ("blank_ids", "row(s) without a trade_id ignored"),
        ("duplicate_ids", "duplicate trade_id(s) collapsed (first row kept)"),
        ("invalid_values", "unparseable value(s) treated as missing"),
    ]
    return [f"{label}: {q[key]} {text}" for key, text in checks if q[key]]


def sidebar_controls() -> tuple[Optional[Dataset], engine.ReconConfig]:
    """Render the sidebar; return the dataset (None if not ready) and tolerances."""
    sb = st.sidebar
    sb.markdown("### Data")
    use_sample = sb.toggle("Use sample data", value=True)
    broker_up = sb.file_uploader("Broker trades (CSV)", type="csv", disabled=use_sample, key="broker_up")
    ledger_up = sb.file_uploader("Ledger trades (CSV)", type="csv", disabled=use_sample, key="ledger_up")
    sb.caption("Required columns: " + ", ".join(engine.REQUIRED_COLUMNS))

    sb.markdown("---")
    sb.markdown("### Tolerances")
    cfg = engine.ReconConfig(
        price_tolerance_bps=sb.number_input("Price tolerance (bps)", 0.0, 1000.0, 5.0, 0.5,
                                            help="Price differences up to this many basis points are not breaks."),
        settlement_tolerance_days=int(sb.number_input("Settlement date tolerance (days)", 0, 10, 0, 1)),
        quantity_tolerance=sb.number_input("Quantity tolerance (units)", 0.0, 10000.0, 0.0, 1.0),
    )

    dataset = None
    if use_sample:
        broker, ledger = engine.load_trades_csv(SAMPLE_BROKER), engine.load_trades_csv(SAMPLE_LEDGER)
    elif broker_up is None or ledger_up is None:
        broker = ledger = None
    else:
        broker, errors_b = _read_upload("Broker file", broker_up)
        ledger, errors_l = _read_upload("Ledger file", ledger_up)
        for message in errors_b + errors_l:
            sb.error(message)
    if broker is not None and ledger is not None:
        notes = _quality_notes("Broker", broker) + _quality_notes("Ledger", ledger)
        dataset = Dataset(broker, ledger, notes)
        if notes:
            sb.markdown("---")
            sb.markdown("### Data quality")
            for note in notes:
                sb.caption("• " + note)
    return dataset, cfg


# --------------------------------------------------------------------------
# Session state: investigation status and notes
# --------------------------------------------------------------------------
def init_state(breaks: pd.DataFrame) -> None:
    """Reset statuses/notes when the set of breaks changes (new data or tolerances)."""
    signature = hash(tuple(breaks["trade_id"]))
    if st.session_state.get("signature") != signature:
        st.session_state.update(signature=signature, statuses={}, notes={})


def _save_status(trade_id: str) -> None:
    st.session_state.statuses[trade_id] = st.session_state[f"status_{trade_id}"]


def _save_note(trade_id: str) -> None:
    st.session_state.notes[trade_id] = st.session_state[f"note_{trade_id}"]


# --------------------------------------------------------------------------
# Presentation helpers
# --------------------------------------------------------------------------
def render_header() -> None:
    st.markdown(
        f"""<div class="wb-header"><div>
        <div class="wb-title">{PRODUCT_NAME}</div>
        <div class="wb-sub">Match broker confirmations against the internal ledger, surface breaks and triage them by severity.</div>
        </div><span class="wb-badge">Synthetic data</span></div>""",
        unsafe_allow_html=True,
    )


def severity_badge(severity: str) -> str:
    return f'<span class="badge badge-{severity}">{severity}</span>'


def kpi_card(label: str, value: str, note: str = "") -> str:
    return (f'<div class="kpi"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-note">{note}&nbsp;</div></div>')


def fmt_qty(v) -> str:
    return DASH if pd.isna(v) else f"{v:,.0f}"


def fmt_price(v) -> str:
    return DASH if pd.isna(v) else f"${v:,.2f}"


def fmt_date(v) -> str:
    return DASH if pd.isna(v) else pd.Timestamp(v).strftime("%Y-%m-%d")


def fmt_text(v) -> str:
    return DASH if pd.isna(v) or v == "" else escape(str(v))


# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------
def tab_overview(breaks: pd.DataFrame, kpis: metrics.Kpis, total_trades: int) -> None:
    match = DASH if kpis.match_rate_pct is None else f"{kpis.match_rate_pct:.1f}%"
    age = DASH if kpis.oldest_open_days is None else f"{kpis.oldest_open_days}"
    st.markdown(
        '<div class="kpi-grid">'
        + kpi_card("Match rate", match, f"{total_trades:,} unique trades")
        + kpi_card("Open breaks", f"{kpis.open_breaks:,}", f"of {len(breaks):,} total")
        + kpi_card("Open notional exposure", metrics.format_currency(kpis.open_notional), "USD, open breaks")
        + kpi_card("Oldest open break", f"{age} days" if age != DASH else DASH, "vs. latest settlement date")
        + "</div>",
        unsafe_allow_html=True,
    )
    counts = metrics.status_counts(breaks)
    st.markdown(
        '<div class="card" style="margin-top:.75rem"><span class="card-title">Investigation status</span> &nbsp; '
        + " &nbsp;·&nbsp; ".join(f"{name}: <b>{n}</b>" for name, n in counts.items()) + "</div>",
        unsafe_allow_html=True,
    )
    if breaks.empty:
        st.info("No breaks found with the current tolerances.")
        return
    left, right = st.columns(2)
    with left:
        st.markdown("### Breaks by severity")
        st.plotly_chart(charts.severity_donut(breaks), use_container_width=True, config={"displayModeBar": False})
    with right:
        st.markdown("### Breaks by type")
        st.plotly_chart(charts.breaks_by_type_bar(breaks), use_container_width=True, config={"displayModeBar": False})
    st.markdown("### Breaks per settlement day")
    st.plotly_chart(charts.daily_breaks_chart(breaks), use_container_width=True, config={"displayModeBar": False})


TABLE_COLUMNS: dict[str, str] = {
    "trade_id": "Trade ID", "severity": "Severity", "break_type": "Break type", "status": "Status",
    "symbol": "Symbol", "notional": "Notional (USD)",
    "broker_quantity": "Qty (Broker)", "ledger_quantity": "Qty (Ledger)",
    "broker_price": "Price (Broker)", "ledger_price": "Price (Ledger)",
    "broker_settlement_date": "Settles (Broker)", "ledger_settlement_date": "Settles (Ledger)",
    "broker_counterparty": "Counterparty (Broker)", "ledger_counterparty": "Counterparty (Ledger)",
}


def _severity_style(value: str) -> str:
    color = t.SEVERITY_COLORS.get(value)
    return "" if color is None else f"color: {color}; background-color: {t.tint(color, '24')}; font-weight: 600;"


def styled_table(df: pd.DataFrame):
    """Pandas Styler: formatted numbers/dates, em dash for nulls, coloured severity."""
    view = df[list(TABLE_COLUMNS)].copy()
    view["break_type"] = view["break_type"].map(t.BREAK_TYPE_LABELS)
    formats = {
        "notional": "${:,.0f}", "broker_quantity": "{:,.0f}", "ledger_quantity": "{:,.0f}",
        "broker_price": "${:,.2f}", "ledger_price": "${:,.2f}",
        "broker_settlement_date": "{:%Y-%m-%d}", "ledger_settlement_date": "{:%Y-%m-%d}",
    }
    styler = view.style.format(formats, na_rep=DASH)
    apply_cells = getattr(styler, "map", None) or styler.applymap  # pandas >= 2.1 renamed applymap
    return apply_cells(_severity_style, subset=["severity"])


def tab_breaks(breaks: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.2, 1])
    severities = c1.multiselect("Severity", list(t.SEVERITY_ORDER), default=list(t.SEVERITY_ORDER))
    label_to_type = {label: key for key, label in t.BREAK_TYPE_LABELS.items()}
    type_labels = c2.multiselect("Break type", list(label_to_type), default=list(label_to_type))
    types = [label_to_type[label] for label in type_labels]
    search = c4.text_input("Trade ID contains", placeholder="e.g. T00119")
    view = breaks[breaks["severity"].isin(severities) & breaks["break_type"].isin(types)]
    if not breaks.empty:
        lo, hi = breaks["break_date"].min().date(), breaks["break_date"].max().date()
        picked = c3.date_input("Settlement date range", (lo, hi), min_value=lo, max_value=hi)
        if isinstance(picked, (tuple, list)) and len(picked) == 2:
            view = view[view["break_date"].between(pd.Timestamp(picked[0]), pd.Timestamp(picked[1]))]
    if search.strip():
        view = view[view["trade_id"].str.contains(search.strip(), case=False, regex=False)]

    st.caption(f"Showing {len(view):,} of {len(breaks):,} breaks")
    config = {col: st.column_config.Column(label) for col, label in TABLE_COLUMNS.items()}
    st.dataframe(styled_table(view), column_config=config, hide_index=True, use_container_width=True)

    export = view[list(TABLE_COLUMNS) + ["severity_reason"]].rename(columns={**TABLE_COLUMNS, "severity_reason": "Severity rationale"})
    st.download_button("Download filtered breaks (CSV)", export.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_breaks.csv", mime="text/csv")


def _comparison_rows(row: pd.Series) -> list[tuple[str, str, str, bool]]:
    fields = set(filter(None, str(row["differing_fields"]).split(",")))
    missing = row["break_type"].startswith("missing")
    money_differs = bool({"quantity", "price"} & fields) or missing
    return [
        ("Quantity", fmt_qty(row["broker_quantity"]), fmt_qty(row["ledger_quantity"]), "quantity" in fields or missing),
        ("Price", fmt_price(row["broker_price"]), fmt_price(row["ledger_price"]), "price" in fields or missing),
        ("Notional", metrics.format_currency(row["broker_notional"]), metrics.format_currency(row["ledger_notional"]), money_differs),
        ("Settlement date", fmt_date(row["broker_settlement_date"]), fmt_date(row["ledger_settlement_date"]), "settlement_date" in fields or missing),
        ("Counterparty", fmt_text(row["broker_counterparty"]), fmt_text(row["ledger_counterparty"]), "counterparty" in fields or missing),
    ]


def comparison_card(row: pd.Series) -> str:
    body = "".join(
        f'<tr class="{"diff" if diff else ""}"><td class="field">{name}</td><td>{b}</td><td>{l}</td></tr>'
        for name, b, l, diff in _comparison_rows(row)
    )
    return (f'<div class="card"><div class="card-title">{escape(row["trade_id"])} · {escape(str(row["symbol"]))}</div>'
            f'<table class="cmp"><tr><th>Field</th><th>Broker</th><th>Ledger</th></tr>{body}</table></div>')


def tab_investigate(breaks: pd.DataFrame) -> None:
    if breaks.empty:
        st.info("Nothing to investigate: no breaks with the current tolerances.")
        return
    trade_id = st.selectbox("Trade ID", breaks["trade_id"].tolist())
    row = breaks[breaks["trade_id"] == trade_id].iloc[0]
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown(comparison_card(row), unsafe_allow_html=True)
    with right:
        st.markdown(
            f'<div class="card"><div class="card-title">Assessment</div>'
            f'<div>{severity_badge(row["severity"])} &nbsp; <b>{t.BREAK_TYPE_LABELS[row["break_type"]]}</b></div>'
            f'<div style="margin-top:.6rem;color:{t.MUTED}"><b style="color:{t.NAVY}">Why this severity:</b> '
            f'{escape(row["severity_reason"])}</div></div>',
            unsafe_allow_html=True,
        )
        current = st.session_state.statuses.get(trade_id, metrics.DEFAULT_STATUS)
        st.selectbox("Status", metrics.STATUSES, index=metrics.STATUSES.index(current),
                     key=f"status_{trade_id}", on_change=_save_status, args=(trade_id,))
        st.text_area("Notes", value=st.session_state.notes.get(trade_id, ""), key=f"note_{trade_id}",
                     on_change=_save_note, args=(trade_id,), height=110,
                     placeholder="Add investigation notes (kept for this session only)")


def tab_rules(cfg: engine.ReconConfig) -> None:
    st.markdown(
        f"""<div class="rules">

### Matching key
Broker and ledger records are paired on **`trade_id`**. A trade found on one side only is a *missing* break. For trades found on both sides, four fields are compared: **quantity, price, settlement date and counterparty**. Symbol and trade date are carried for context but are not compared.

### Break types
<table>
<tr><th>Break type</th><th>Raised when</th></tr>
<tr><td>Quantity mismatch</td><td>Quantities differ by more than the quantity tolerance (now <b>{cfg.quantity_tolerance:g}</b> units).</td></tr>
<tr><td>Price mismatch</td><td>Prices differ by more than the price tolerance (now <b>{cfg.price_tolerance_bps:g} bps</b> of the ledger price).</td></tr>
<tr><td>Settlement date mismatch</td><td>Settlement dates differ by more than the date tolerance (now <b>{cfg.settlement_tolerance_days}</b> calendar day(s)).</td></tr>
<tr><td>Counterparty mismatch</td><td>Counterparty names differ (ignoring case and surrounding spaces).</td></tr>
<tr><td>Missing in broker</td><td>The ledger has the trade; the broker file does not.</td></tr>
<tr><td>Missing in ledger</td><td>The broker file has the trade; the ledger does not.</td></tr>
</table>

If one trade differs on several fields, it is reported once, as the type of its most severe difference (ties go to quantity, then price, date, counterparty). All differing fields are highlighted on the Investigate tab.

### How severity is assigned
Rules are applied top to bottom; the first that matches wins.
<table>
<tr><th>#</th><th>Rule</th><th>Severity</th></tr>
<tr><td>1</td><td>Trade is missing on either side</td><td>{severity_badge("HIGH")}</td></tr>
<tr><td>2</td><td>Notional (quantity × broker price) is at least <b>${cfg.high_notional_threshold:,.0f}</b>, for any break type</td><td>{severity_badge("HIGH")}</td></tr>
<tr><td>3</td><td>Quantity difference above the minor limit (<b>{cfg.minor_quantity:g}</b> units), price difference above the minor limit (<b>{cfg.minor_price_bps:g} bps</b>), or any counterparty mismatch</td><td>{severity_badge("MEDIUM")}</td></tr>
<tr><td>4</td><td>Settlement date differences, and quantity or price differences within the minor limits</td><td>{severity_badge("LOW")}</td></tr>
</table>

### Tolerances
Tolerances decide **whether** a difference is a break; they are set in the sidebar. A difference *equal* to the tolerance is not a break. The notional threshold and minor limits decide **how severe** a break is; they are fixed defaults in <code>ReconConfig</code>.

### Data handling
Duplicate <code>trade_id</code>s are collapsed (first row kept) and rows without a <code>trade_id</code> are ignored; both are reported in the sidebar. Unparseable numbers or dates become missing values, so a missing value against a real one is a break. "Oldest open break" is measured from the break's settlement date to the latest settlement date in the data (not today's date), so the sample stays meaningful. Notional is shown in USD; all sample data is synthetic.

</div>""",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    render_header()
    dataset, cfg = sidebar_controls()
    if dataset is None:
        st.info("Upload both a broker and a ledger CSV in the sidebar, or switch on **Use sample data**.")
        return

    breaks = engine.reconcile(dataset.broker, dataset.ledger, cfg)
    init_state(breaks)
    breaks = metrics.attach_status(breaks, st.session_state.statuses)
    total_trades = engine.count_unique_trades(dataset.broker, dataset.ledger)
    kpis = metrics.compute_kpis(breaks, total_trades, metrics.latest_settlement(dataset.broker, dataset.ledger))

    overview, breaks_tab, investigate, rules = st.tabs(["Overview", "Breaks", "Investigate", "Rules & Method"])
    with overview:
        tab_overview(breaks, kpis, total_trades)
    with breaks_tab:
        tab_breaks(breaks)
    with investigate:
        tab_investigate(breaks)
    with rules:
        tab_rules(cfg)


main()
