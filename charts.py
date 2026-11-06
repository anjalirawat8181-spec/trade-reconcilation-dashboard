from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import theme as t

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=t.FONT_FAMILY, color=t.NAVY, size=12),
    margin=dict(l=8, r=8, t=8, b=8),
    legend=dict(orientation="h", y=-0.18, x=0, title_text="", font=dict(color=t.MUTED, family=t.FONT_FAMILY)),
    hoverlabel=dict(bgcolor=t.NAVY, font=dict(color="#fff", family=t.FONT_FAMILY), bordercolor=t.NAVY),
    height=320,
)


def _axes(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=t.BORDER, tickfont=dict(color=t.MUTED))
    fig.update_yaxes(showgrid=False, zeroline=False, tickfont=dict(color=t.MUTED))
    return fig


def _empty(message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**_LAYOUT, xaxis_visible=False, yaxis_visible=False)
    fig.add_annotation(text=message, showarrow=False, font=dict(color=t.MUTED, size=13))
    return fig


def severity_donut(breaks: pd.DataFrame) -> go.Figure:
    if breaks.empty:
        return _empty("No breaks")
    counts = breaks["severity"].value_counts().reindex(t.SEVERITY_ORDER).dropna().astype(int)
    fig = go.Figure(go.Pie(
        labels=list(counts.index), values=list(counts.values), hole=0.62, sort=False,
        marker=dict(colors=[t.SEVERITY_COLORS[s] for s in counts.index], line=dict(color="#fff", width=2)),
        textinfo="value", textfont=dict(color="#fff", size=13),
        hovertemplate="<b>%{label}</b><br>%{value} breaks (%{percent})<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT, showlegend=True)
    fig.add_annotation(
        text=f"<b>{int(counts.sum())}</b><br><span style='font-size:11px'>breaks</span>",
        showarrow=False, font=dict(size=28, color=t.NAVY, family=t.HEADING_FONT),
    )
    return fig


def breaks_by_type_bar(breaks: pd.DataFrame) -> go.Figure:
    if breaks.empty:
        return _empty("No breaks")
    table = breaks.pivot_table(index="break_type", columns="severity", values="trade_id",
                               aggfunc="count", fill_value=0)
    table = table.reindex(columns=list(t.SEVERITY_ORDER), fill_value=0)
    table = table.loc[table.sum(axis=1).sort_values(ascending=True).index]
    labels = [t.BREAK_TYPE_LABELS.get(k, k) for k in table.index]
    fig = go.Figure()
    for sev in t.SEVERITY_ORDER:
        fig.add_bar(y=labels, x=table[sev], name=sev, orientation="h", marker_color=t.SEVERITY_COLORS[sev],
                    hovertemplate=f"<b>%{{y}}</b><br>{sev}: %{{x}} breaks<extra></extra>")
    fig.update_layout(**_LAYOUT, barmode="stack", bargap=0.35)
    fig.update_xaxes(title_text="Breaks")
    return _axes(fig)


def daily_breaks_chart(breaks: pd.DataFrame, window: int = 7) -> go.Figure:
    if breaks.empty:
        return _empty("No breaks")
    daily = (breaks.assign(day=breaks["break_date"].dt.normalize())
             .groupby(["day", "severity"]).size().unstack(fill_value=0)
             .reindex(columns=list(t.SEVERITY_ORDER), fill_value=0))
    days = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(days, fill_value=0)
    moving_avg = daily.sum(axis=1).rolling(window, min_periods=1).mean()
    fig = go.Figure()
    for sev in t.SEVERITY_ORDER:
        fig.add_bar(x=daily.index, y=daily[sev], name=sev, marker_color=t.SEVERITY_COLORS[sev],
                    hovertemplate=f"%{{x|%d %b %Y}}<br>{sev}: %{{y}}<extra></extra>")
    fig.add_scatter(x=daily.index, y=moving_avg, name=f"{window}-day average", mode="lines",
                    line=dict(color=t.NAVY, width=2),
                    hovertemplate=f"%{{x|%d %b %Y}}<br>{window}-day avg: %{{y:.2f}}<extra></extra>")
    fig.update_layout(**_LAYOUT, barmode="stack", bargap=0.2)
    fig.update_yaxes(title_text="Breaks per day")
    return _axes(fig)
