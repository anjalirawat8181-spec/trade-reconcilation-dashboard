# Settlement Reconciliation Workbench

![tests](https://github.com/anjalirawat8181-spec/trade-reconcilation-dashboard/actions/workflows/tests.yml/badge.svg)

A Streamlit workbench that reconciles broker trade confirmations against an internal ledger, flags breaks (quantity, price, settlement date, counterparty, missing trades), assigns each a documented severity, and lets an analyst triage them. The reconciliation engine is a pure, typed, unit-tested Python module with no UI dependencies; the Streamlit app is a thin layer on top. All data is synthetic.

**Live app:** _add your Streamlit Community Cloud URL here_

## Screenshots

| Overview | Breaks |
|---|---|
| _screenshot placeholder_ | _screenshot placeholder_ |

| Investigate | Rules & Method |
|---|---|
| _screenshot placeholder_ | _screenshot placeholder_ |

## Features

- **Overview:** KPI cards (match rate, open breaks, open notional exposure, oldest open break), breaks by severity (donut) and by type (bar), and daily breaks with a 7-day moving average.
- **Breaks:** filter by severity, break type, date range and trade ID; formatted table with severity badges; CSV export of the filtered view.
- **Investigate:** side-by-side Broker vs Ledger card with differing fields highlighted, the severity and why it was assigned, plus a status (Open / Investigating / Resolved) and notes per break. Statuses feed the Overview.
- **Rules & Method:** the matching key, break types, severity rules and tolerances in plain English, reflecting the live sidebar settings.
- **Sidebar:** sample-data toggle, broker/ledger CSV upload with schema validation and clear errors, and tolerance controls (price in bps, settlement days, quantity).

## Break types and severity

Trades are matched on `trade_id`. Fields compared for trades present on both sides: quantity, price, settlement date, counterparty.

| Break type | Raised when |
|---|---|
| `quantity_mismatch` | quantity differs by more than the quantity tolerance |
| `price_mismatch` | price differs by more than the price tolerance (bps of ledger price) |
| `settlement_date_mismatch` | settlement dates differ by more than the day tolerance |
| `counterparty_mismatch` | counterparty differs (case/whitespace-insensitive) |
| `missing_in_broker` | in the ledger only |
| `missing_in_ledger` | in the broker file only |

Severity (first matching rule wins; thresholds live in `ReconConfig`):

| Severity | Rule |
|---|---|
| **HIGH** | trade missing on either side, **or** notional (quantity × price) ≥ ₹10,00,000 for any break |
| **MEDIUM** | notional (quantity × price) ≥ ₹1,00,000, **or** quantity diff > 5 units, price diff > 25 bps, or any counterparty mismatch |
| **LOW** | settlement date differences, and quantity/price differences within the minor limits above |

A trade that differs on several fields is reported once, with the type of its most severe difference.

## Architecture

```
app.py            Streamlit UI only: sidebar, tabs, session state
recon_engine.py   Pure engine: clean/validate DataFrames -> breaks DataFrame (ReconConfig dataclass)
metrics.py        Pure KPI maths and status helpers
charts.py         Plotly figure builders (DataFrame in, Figure out)
theme.py          Palette and label constants (single source of truth)
styles.py         Injected CSS built from theme.py
generate_data.py  Seeded synthetic data generator
tests/            pytest suite for the engine and metrics
```

`recon_engine.py` and `metrics.py` never import Streamlit, so they are testable and reusable. Palette values are defined in `theme.py` and mirrored in `.streamlit/config.toml`.

## Run locally

Python 3.10 (see `runtime.txt`).

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

Regenerate the sample data (deterministic, seed 42): `python generate_data.py`

## Run tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

GitHub Actions runs the same suite on every push (`.github/workflows/tests.yml`).

## Limitations / future work

- **Synthetic data only.** Counterparties and trades are generated; the sample break rate (~3%) is designed, not observed.
- **No persistence.** Statuses and notes live in `st.session_state` and are lost on refresh; there is no audit trail or multi-user workflow.
- **Simplified matching.** One record per `trade_id`; no partial fills, many-to-one matching, fuzzy keys, or symbol/price-currency checks. Duplicate IDs are collapsed (first row kept), not reported as breaks.
- **Single currency.** Notional is assumed to be INR; no FX or business-day calendar for date tolerances (calendar days).
- **Fixed severity thresholds.** Tolerances are adjustable in the UI; the notional thresholds and minor limits are only configurable in code.
- Future work: persistent case management, role-based access, scheduled runs, additional break types and a database-backed history.
