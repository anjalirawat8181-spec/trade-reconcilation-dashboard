"""Custom CSS for the workbench, built from the palette in theme.py."""
from __future__ import annotations

import streamlit as st

import theme as t


def build_css() -> str:
    """Return the full <style> block."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Tinos:wght@400;700&display=swap');

:root {{
  --navy: {t.NAVY}; --mid-navy: {t.MID_NAVY}; --accent: {t.ACCENT}; --tint: {t.TINT};
  --page: {t.PAGE_BG}; --border: {t.BORDER}; --muted: {t.MUTED};
  --high: {t.HIGH}; --medium: {t.MEDIUM}; --low: {t.LOW};
  --radius: {t.RADIUS_PX}px;
  --shadow: none;
  --serif: {t.HEADING_FONT};
  --body-font: {t.FONT_FAMILY};
}}

html, body, [class*="css"], .stApp {{ font-family: var(--body-font); font-size: 16px; line-height: 1.5; }}
.stApp {{ background: var(--page); color: var(--navy); }}
h1, h2, h3, h4 {{ font-family: var(--serif); color: var(--navy); font-weight: 400;
  line-height: 1.1; letter-spacing: -0.02em; }}
h3 {{ font-size: 1.5rem; margin: .4rem 0 .3rem; }}
button, input, select, textarea, [data-baseweb], [data-testid="stDataFrame"], [data-testid="stSidebar"],
[data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"],
[data-testid="stTabs"] {{ font-family: var(--body-font); }}

footer, [data-testid="stFooter"] {{ visibility: hidden; height: 0; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding: 1.2rem 2rem 2rem; max-width: 1400px; }}

.wb-header {{ background: var(--navy); color: #fff; border-radius: var(--radius);
  padding: 1.1rem 1.4rem; display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; box-shadow: var(--shadow); border-left: 4px solid var(--accent); margin-bottom: .6rem; }}
.wb-title {{ font-family: var(--serif); font-size: 2.2rem; font-weight: 400; letter-spacing: -0.02em; line-height: 1.1; }}
.wb-sub {{ color: #B9C7D8; font-size: .86rem; margin-top: .2rem; }}
.wb-badge {{ border: 1px solid var(--accent); color: #D7E3F1; border-radius: 999px;
  padding: .15rem .65rem; font-size: .7rem; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; white-space: nowrap; }}

[data-testid="stSidebar"] {{ background: var(--navy); }}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] [data-testid="stTextInputRoot"],
[data-testid="stSidebar"] [data-testid="stCheckbox"], [data-testid="stSidebar"] [data-testid="stSelectbox"] {{ font-family: var(--body-font); }}
[data-testid="stSidebar"] hr {{ border-color: var(--mid-navy); }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {{ color: #FFFFFF; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stToggle"] {{ color: {t.TINT}; }}

[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="base-input"],
[data-testid="stSidebar"] [data-baseweb="textarea"],
[data-testid="stSidebar"] [data-baseweb="select"] > div {{ background-color: #FFFFFF; }}
[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="textarea"],
[data-testid="stSidebar"] [data-baseweb="select"] > div {{ border: 1px solid #D5DDE6; border-radius: var(--radius); overflow: hidden; }}
[data-testid="stSidebar"] [data-baseweb="base-input"] {{ border: 0; border-radius: 0; }}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] div {{ color: {t.NAVY}; -webkit-text-fill-color: {t.NAVY}; background-color: transparent; }}
[data-testid="stSidebar"] input::placeholder, [data-testid="stSidebar"] textarea::placeholder {{ color: {t.MUTED}; -webkit-text-fill-color: {t.MUTED}; opacity: 1; }}
[data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill: {t.NAVY}; }}

[data-testid="stNumberInput"] > div:has(> [data-baseweb="input"]) {{ background: #FFFFFF; border: 1px solid #D5DDE6;
  border-radius: var(--radius); overflow: hidden; }}
[data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="input"] {{ border: 0; border-radius: 0; }}

[data-testid="stNumberInput"] button {{ background-color: #FFFFFF; color: {t.NAVY}; border: 0;
  border-left: 1px solid #D5DDE6; }}
[data-testid="stNumberInput"] button svg {{ fill: {t.NAVY}; color: {t.NAVY}; }}
[data-testid="stNumberInput"] button:hover:not(:disabled) {{ background-color: {t.TINT}; }}
[data-testid="stNumberInput"] button:disabled {{ background-color: #F3F6FA; opacity: 1; cursor: not-allowed; }}
[data-testid="stNumberInput"] button:disabled svg {{ fill: {t.MUTED}; color: {t.MUTED}; }}
[data-testid="stNumberInput"] input:disabled {{ -webkit-text-fill-color: {t.MUTED}; color: {t.MUTED}; }}

[data-testid="stFileUploader"] {{ background: transparent; }}
[data-testid="stFileUploader"] [data-testid="stWidgetLabel"] {{ background: transparent; }}
[data-testid="stFileUploadDropzone"], [data-testid="stFileUploaderDropzone"] {{
  background: #FFFFFF; border: 1px solid #D5DDE6; border-radius: var(--radius); color: {t.NAVY}; }}
[data-testid="stFileUploadDropzone"]:hover, [data-testid="stFileUploaderDropzone"]:hover {{ border-color: var(--accent); }}
[data-testid="stFileUploadDropzone"] span, [data-testid="stFileUploaderDropzone"] span {{ color: {t.NAVY}; }}
[data-testid="stFileUploadDropzone"] small, [data-testid="stFileUploaderDropzone"] small {{ color: {t.MUTED}; }}
[data-testid="stFileUploadDropzone"] svg, [data-testid="stFileUploaderDropzone"] svg {{ fill: {t.NAVY}; color: {t.NAVY}; }}
[data-testid="stFileUploadDropzone"] button, [data-testid="stFileUploaderDropzone"] button {{
  background: {t.ACCENT}; color: {t.NAVY}; border: 1px solid {t.ACCENT}; border-radius: var(--radius); font-weight: 600; }}
[data-testid="stFileUploadDropzone"] button:hover:not(:disabled), [data-testid="stFileUploaderDropzone"] button:hover:not(:disabled) {{
  background: #6A90BE; border-color: #6A90BE; color: #0D1B2A; }}
[data-testid="stFileUploadDropzone"] button:disabled, [data-testid="stFileUploaderDropzone"] button:disabled {{
  background: #B9C9DC; border-color: #B9C9DC; color: {t.NAVY}; opacity: 1; cursor: not-allowed; }}
[data-testid="stFileUploader"] ul {{ list-style: none; padding: 0; margin: .5rem 0 0; }}
[data-testid="stFileUploader"] li, [data-testid="stFileUploader"] [data-testid="stUploadedFile"] {{
  background: #FFFFFF; border: 1px solid #D5DDE6; border-radius: var(--radius); padding: .3rem .5rem; margin-bottom: .35rem; }}
[data-testid="stFileUploader"] li *, [data-testid="stFileUploader"] [data-testid="stUploadedFile"] * {{ color: {t.NAVY}; }}
[data-testid="stFileUploader"] li small, [data-testid="stFileUploader"] [data-testid="stUploadedFile"] small {{ color: {t.MUTED}; }}
[data-testid="stFileUploader"] li svg {{ fill: {t.NAVY}; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 1.4rem; border-bottom: 1px solid var(--border); }}
.stTabs [data-baseweb="tab"] {{ padding: .5rem .1rem; color: var(--muted); font-weight: 500; font-family: var(--body-font); }}
.stTabs [aria-selected="true"] {{ color: var(--navy); font-weight: 600; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: var(--accent); }}

.kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; }}
@media (max-width: 900px) {{ .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
.kpi {{ background: #fff; border: 1px solid var(--border); border-radius: var(--radius);
  padding: .85rem 1rem; box-shadow: var(--shadow); }}
.kpi-label {{ color: var(--muted); margin-top: .1rem; font-size: .72rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; font-family: var(--body-font); font-variant-numeric: tabular-nums; }}
.kpi-value {{ font-family: var(--serif); color: var(--navy); font-size: 3rem; font-weight: 400; letter-spacing: -0.02em; line-height: 1.1; margin-top: .15rem; font-variant-numeric: tabular-nums; }}
.kpi-note {{ color: var(--muted); font-size: .75rem; margin-top: .1rem; font-family: var(--body-font); }}

.card {{ background: #fff; border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 1rem 1.1rem; }}
.card-title {{ font-family: var(--serif); font-size: 1.25rem; font-weight: 400; line-height: 1.1; color: var(--navy); margin-bottom: .5rem; }}
.badge {{ display: inline-block; border-radius: 999px; padding: .1rem .6rem; font-size: .72rem;
  font-weight: 600; letter-spacing: .04em; }}
.badge-HIGH {{ color: var(--high); background: {t.tint(t.HIGH)}; }}
.badge-MEDIUM {{ color: var(--medium); background: {t.tint(t.MEDIUM, "26")}; }}
.badge-LOW {{ color: #3F6694; background: {t.tint(t.LOW, "2E")}; }}

table.cmp {{ width: 100%; border-collapse: collapse; font-size: .9rem; font-family: var(--body-font); font-variant-numeric: tabular-nums; }}
table.cmp th {{ text-align: left; color: var(--muted); font-size: .72rem; font-weight: 600;
  letter-spacing: .06em; text-transform: uppercase; padding: .4rem .6rem; border-bottom: 1px solid var(--border); }}
table.cmp td {{ padding: .5rem .6rem; border-bottom: 1px solid var(--tint); }}
table.cmp td.field {{ color: var(--muted); width: 28%; }}
table.cmp tr.diff td {{ background: {t.tint(t.HIGH, "14")}; font-weight: 600; }}
table.cmp tr.diff td.field {{ color: var(--high); }}

.rules table {{ border-collapse: collapse; width: 100%; font-size: .9rem; font-family: var(--body-font); }}
.rules th, .rules td {{ border: 1px solid var(--border); padding: .45rem .65rem; text-align: left; vertical-align: top; }}
.rules th {{ background: var(--tint); color: var(--navy); }}

.stDownloadButton button, .stButton button {{ border-radius: var(--radius); border: 1px solid var(--mid-navy);
  background: var(--mid-navy); color: #fff; font-weight: 500; font-family: var(--body-font); }}
.stDownloadButton button:hover, .stButton button:hover {{ background: var(--navy); border-color: var(--navy); color: #fff; }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: var(--radius); font-family: var(--body-font); font-variant-numeric: tabular-nums; }}
[data-testid="stDataFrame"] * {{ font-family: var(--body-font); font-variant-numeric: tabular-nums; }}
a {{ color: var(--accent); }}
</style>
"""


def inject_styles() -> None:
    """Inject the stylesheet into the running Streamlit app."""
    st.markdown(build_css(), unsafe_allow_html=True)
