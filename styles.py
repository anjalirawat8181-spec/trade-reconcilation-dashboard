"""Custom CSS for the workbench, built from the palette in theme.py."""
from __future__ import annotations

import streamlit as st

import theme as t


def build_css() -> str:
    """Return the full <style> block."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {{
  --navy: {t.NAVY}; --mid-navy: {t.MID_NAVY}; --accent: {t.ACCENT}; --tint: {t.TINT};
  --page: {t.PAGE_BG}; --border: {t.BORDER}; --muted: {t.MUTED};
  --high: {t.HIGH}; --medium: {t.MEDIUM}; --low: {t.LOW};
  --radius: {t.RADIUS_PX}px;
  --shadow: 0 1px 2px rgba(13,27,42,.06), 0 2px 8px rgba(13,27,42,.05);
}}

html, body, [class*="css"], .stApp {{ font-family: {t.FONT_FAMILY}; }}
.stApp {{ background: var(--page); color: var(--navy); }}
h1, h2, h3, h4 {{ color: var(--navy); font-weight: 600; letter-spacing: -0.01em; }}
h3 {{ font-size: 1.05rem; margin: .4rem 0 .2rem; }}

/* layout + chrome */
footer, [data-testid="stFooter"] {{ visibility: hidden; height: 0; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding: 1.2rem 2rem 2rem; max-width: 1400px; }}

/* header band */
.wb-header {{ background: var(--navy); color: #fff; border-radius: var(--radius);
  padding: 1.1rem 1.4rem; display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; box-shadow: var(--shadow); border-left: 4px solid var(--accent); margin-bottom: .6rem; }}
.wb-title {{ font-size: 1.45rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2; }}
.wb-sub {{ color: #B9C7D8; font-size: .86rem; margin-top: .2rem; }}
.wb-badge {{ border: 1px solid var(--accent); color: #D7E3F1; border-radius: 999px;
  padding: .15rem .65rem; font-size: .7rem; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; white-space: nowrap; }}

/* sidebar */
[data-testid="stSidebar"] {{ background: var(--navy); }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color: {t.TINT}; }}
[data-testid="stSidebar"] hr {{ border-color: var(--mid-navy); }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 1.4rem; border-bottom: 1px solid var(--border); }}
.stTabs [data-baseweb="tab"] {{ padding: .5rem .1rem; color: var(--muted); font-weight: 500; }}
.stTabs [aria-selected="true"] {{ color: var(--navy); font-weight: 600; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: var(--accent); }}

/* cards */
.kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; }}
@media (max-width: 900px) {{ .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
.kpi {{ background: #fff; border: 1px solid var(--border); border-radius: var(--radius);
  padding: .85rem 1rem; box-shadow: var(--shadow); }}
.kpi-label {{ color: var(--muted); font-size: .72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; }}
.kpi-value {{ color: var(--navy); font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; margin-top: .15rem; }}
.kpi-note {{ color: var(--muted); font-size: .75rem; margin-top: .1rem; }}

.card {{ background: #fff; border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 1rem 1.1rem; }}
.card-title {{ font-weight: 600; color: var(--navy); margin-bottom: .5rem; }}
.badge {{ display: inline-block; border-radius: 999px; padding: .1rem .6rem; font-size: .72rem;
  font-weight: 600; letter-spacing: .04em; }}
.badge-HIGH {{ color: var(--high); background: {t.tint(t.HIGH)}; }}
.badge-MEDIUM {{ color: var(--medium); background: {t.tint(t.MEDIUM, "26")}; }}
.badge-LOW {{ color: #3F6694; background: {t.tint(t.LOW, "2E")}; }}

table.cmp {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
table.cmp th {{ text-align: left; color: var(--muted); font-size: .72rem; font-weight: 600;
  letter-spacing: .06em; text-transform: uppercase; padding: .4rem .6rem; border-bottom: 1px solid var(--border); }}
table.cmp td {{ padding: .5rem .6rem; border-bottom: 1px solid var(--tint); }}
table.cmp td.field {{ color: var(--muted); width: 28%; }}
table.cmp tr.diff td {{ background: {t.tint(t.HIGH, "14")}; font-weight: 600; }}
table.cmp tr.diff td.field {{ color: var(--high); }}

.rules table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
.rules th, .rules td {{ border: 1px solid var(--border); padding: .45rem .65rem; text-align: left; vertical-align: top; }}
.rules th {{ background: var(--tint); color: var(--navy); }}

/* buttons + tables */
.stDownloadButton button, .stButton button {{ border-radius: var(--radius); border: 1px solid var(--mid-navy);
  background: var(--mid-navy); color: #fff; font-weight: 500; }}
.stDownloadButton button:hover, .stButton button:hover {{ background: var(--navy); border-color: var(--navy); color: #fff; }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: var(--radius); }}
a {{ color: var(--accent); }}
</style>
"""


def inject_styles() -> None:
    """Inject the stylesheet into the running Streamlit app."""
    st.markdown(build_css(), unsafe_allow_html=True)
