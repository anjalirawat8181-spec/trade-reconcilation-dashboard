import os
import tempfile

import pandas as pd
import plotly.express as px
import streamlit as st

from recon_engine import reconcile_trades


st.set_page_config(page_title="Trade Settlement Reconciliation Tool", layout="wide")

# Import Inter from Google Fonts and apply global CSS because Streamlit
# does not provide a native way to load external fonts. We inject a small
# CSS block with `st.markdown(..., unsafe_allow_html=True)` so the font and
# typography rules apply across the app (headers, body, KPI values, charts).
_INTER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --accent: #4da8f7;
    --text: #0f172a;
    --muted: #6b7280;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

/* Title styling: slightly heavier, tightened letter spacing */
h1 {
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
    margin: 0 0 0.25rem 0 !important;
}

/* Body and descriptions lighter weight for contrast */
p, h2, h3 {
    font-weight: 400 !important;
}

/* KPI numbers: larger and bolder to act as anchors */
div[data-testid="metric-container"] .stMetricValue, .stMetric .value {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
}

/* Subtle card/background shading and soft borders */
section.main > div[role="main"] {
    background-color: #ffffff !important;
}

</style>
"""

st.markdown(_INTER_CSS, unsafe_allow_html=True)

# Replace default title with HTML-controlled heading for tighter typography control
st.markdown(
        "<h1 style='font-family: Inter, sans-serif;'>Trade Settlement Reconciliation Tool</h1>",
        unsafe_allow_html=True,
)
st.write(
        "Upload a broker trade file and an internal ledger file, or use the sample data, to identify reconciliation breaks and severity levels in real time."
)

ACCENT_COLOR = "#4da8f7"
HIGH_COLOR = "#dc2626"
MEDIUM_COLOR = "#f59e0b"
LOW_COLOR = "#60a5fa"

use_sample = st.checkbox("Use sample data from this project", value=True)

broker_file = None
ledger_file = None

if use_sample:
    st.success("Using sample files: broker_trades.csv and internal_ledger.csv")
    broker_file = "broker_trades.csv"
    ledger_file = "internal_ledger.csv"
else:
    uploaded_broker = st.file_uploader("Upload broker trade CSV", type="csv", key="broker")
    uploaded_ledger = st.file_uploader("Upload internal ledger CSV", type="csv", key="ledger")
    if uploaded_broker is not None and uploaded_ledger is not None:
        broker_file = uploaded_broker
        ledger_file = uploaded_ledger


def reconcile_uploaded_files(broker_buffer, ledger_buffer):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_broker:
        temp_broker.write(broker_buffer.read())
        broker_path = temp_broker.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_ledger:
        temp_ledger.write(ledger_buffer.read())
        ledger_path = temp_ledger.name

    try:
        return reconcile_trades(broker_path, ledger_path)
    finally:
        os.unlink(broker_path)
        os.unlink(ledger_path)


def load_dataframe(source):
    if isinstance(source, str):
        return pd.read_csv(source, dtype={"trade_id": str})
    return pd.read_csv(source, dtype={"trade_id": str})


if broker_file is None or ledger_file is None:
    st.info("Please upload both CSV files or enable sample data.")
    st.stop()

if not use_sample:
    breaks = reconcile_uploaded_files(broker_file, ledger_file)
    broker_df = load_dataframe(broker_file)
    ledger_df = load_dataframe(ledger_file)
else:
    breaks = reconcile_trades(broker_file, ledger_file)
    broker_df = load_dataframe(broker_file)
    ledger_df = load_dataframe(ledger_file)

all_trade_ids = pd.Index(broker_df["trade_id"]).append(pd.Index(ledger_df["trade_id"]))
total_trades = len(all_trade_ids.unique())
total_breaks = len(breaks)
break_rate = round(total_breaks / max(total_trades, 1) * 100, 1)

col1, col2, col3 = st.columns(3)
col1.metric("Total unique trades", total_trades)
col2.metric("Total breaks detected", total_breaks)
col3.metric("Break rate", f"{break_rate}%")

st.write("")

breaks["break_date"] = pd.to_datetime(
    breaks["broker_settlement_date"].fillna(breaks["ledger_settlement_date"])
)

severity_counts = breaks["severity"].value_counts().reset_index()
severity_counts.columns = ["severity", "count"]

break_type_counts = breaks["break_type"].value_counts().reset_index()
break_type_counts.columns = ["break_type", "count"]

trend_data = (
    breaks.groupby("break_date")
    .size()
    .reset_index(name="count")
    .sort_values("break_date")
)

st.markdown("### Breaks by severity")
fig_severity = px.bar(
    severity_counts,
    x="severity",
    y="count",
    color="severity",
    color_discrete_map={"HIGH": HIGH_COLOR, "MEDIUM": MEDIUM_COLOR, "LOW": LOW_COLOR},
    labels={"count": "Number of breaks"},
)
fig_severity.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#0f172a", family="Inter, sans-serif"),
)
st.plotly_chart(fig_severity, use_container_width=True)

st.markdown("### Breaks by type")
fig_type = px.bar(
    break_type_counts,
    x="break_type",
    y="count",
    color_discrete_sequence=[ACCENT_COLOR],
    labels={"count": "Number of breaks", "break_type": "Break type"},
)
fig_type.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#0f172a", family="Inter, sans-serif"),
)
st.plotly_chart(fig_type, use_container_width=True)

st.markdown("### Trend of breaks over time")
fig_trend = px.line(
    trend_data,
    x="break_date",
    y="count",
    labels={"break_date": "Settlement date", "count": "Break count"},
    markers=True,
)
fig_trend.update_traces(line_color=ACCENT_COLOR)
fig_trend.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#0f172a", family="Inter, sans-serif"),
)
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("### Break details")
severity_filter = st.multiselect(
    "Filter by severity", options=breaks["severity"].unique().tolist(), default=breaks["severity"].unique().tolist()
)

display_df = breaks[breaks["severity"].isin(severity_filter)].copy()
display_df = display_df.sort_values(["severity", "break_type"])

st.dataframe(display_df)
