import os
import tempfile

import pandas as pd
import plotly.express as px
import streamlit as st

from recon_engine import reconcile_trades


st.set_page_config(page_title="Trade Settlement Reconciliation Tool", layout="wide")
st.title("Trade Settlement Reconciliation Tool")
st.write(
    "Upload a broker trade file and an internal ledger file, or use the sample data, to identify reconciliation breaks and severity levels in real time."
)

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
    color_discrete_map={"HIGH": "red", "MEDIUM": "orange", "LOW": "green"},
    labels={"count": "Number of breaks"},
)
st.plotly_chart(fig_severity, use_container_width=True)

st.markdown("### Breaks by type")
fig_type = px.bar(
    break_type_counts,
    x="break_type",
    y="count",
    labels={"count": "Number of breaks", "break_type": "Break type"},
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
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("### Break details")
severity_filter = st.multiselect(
    "Filter by severity", options=breaks["severity"].unique().tolist(), default=breaks["severity"].unique().tolist()
)

display_df = breaks[breaks["severity"].isin(severity_filter)].copy()
display_df = display_df.sort_values(["severity", "break_type"])

st.dataframe(display_df)
