"""Small reusable presentation helpers for the Streamlit dashboard."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape

import plotly.graph_objects as go
import streamlit as st

THEME = {
    "background": "#0B1020",
    "surface": "#121A2B",
    "card": "#182338",
    "teal": "#2DE2C5",
    "cyan": "#38BDF8",
    "violet": "#A78BFA",
    "positive": "#34D399",
    "warning": "#FBBF24",
    "negative": "#FB7185",
    "text": "#F1F5F9",
    "muted": "#94A3B8",
    "grid": "#26334A",
}
KPI_COLORS = (
    THEME["cyan"],
    THEME["warning"],
    THEME["teal"],
    THEME["violet"],
    THEME["positive"],
)
KPI_ICONS = ("↗", "↘", "◈", "%", "#")


def format_inr(value: float | int) -> str:
    """Format an amount in Indian rupee notation, e.g. ₹1,25,000."""
    amount = float(value)
    sign = "-" if amount < 0 else ""
    whole = str(int(abs(amount)))
    if len(whole) > 3:
        last_three = whole[-3:]
        leading = whole[:-3]
        groups: list[str] = []
        while len(leading) > 2:
            groups.insert(0, leading[-2:])
            leading = leading[:-2]
        if leading:
            groups.insert(0, leading)
        whole = ",".join(groups + [last_three])
    decimals = abs(amount) % 1
    fraction = f".{round(decimals * 100):02.0f}" if decimals else ""
    return f"{sign}₹{whole}{fraction}"


def comparison_text(
    current: float, previous: float, *, percentage: bool = True, percentage_points: bool = False
) -> str:
    """Describe a real prior-period comparison, or report it as unavailable."""
    if percentage_points:
        difference = current - previous
        return f"{difference:+.1f} pp vs prior period"
    if previous == 0:
        return "N/A vs prior period"
    difference = current - previous
    if percentage:
        return f"{difference / abs(previous) * 100:+.1f}% vs prior period"
    return f"{difference:+,.0f} vs prior period"


def inject_design_system() -> None:
    """Apply the FinTech palette and responsive, accessible component styles."""
    st.markdown(
        f"""
        <style>
        :root {{
          color-scheme: dark;
          --et-bg: {THEME["background"]};
          --et-surface: {THEME["surface"]};
          --et-card: {THEME["card"]};
          --et-teal: {THEME["teal"]};
          --et-cyan: {THEME["cyan"]};
          --et-violet: {THEME["violet"]};
          --et-positive: {THEME["positive"]};
          --et-warning: {THEME["warning"]};
          --et-negative: {THEME["negative"]};
          --et-text: {THEME["text"]};
          --et-muted: {THEME["muted"]};
          --et-grid: {THEME["grid"]};
        }}
        .stApp {{ background: var(--et-bg); color: var(--et-text); }}
        [data-testid="stHeader"] {{ background: rgba(11,16,32,.92); }}
        [data-testid="stSidebar"] {{
          background: var(--et-surface);
          border-right: 1px solid var(--et-grid);
        }}
        .block-container {{
          max-width: 1540px; padding: 1.65rem clamp(1rem, 3vw, 2.5rem) 3rem;
        }}
        [data-testid="stMetric"] {{
          min-height: 138px; box-sizing: border-box;
          background: var(--et-card); border: 1px solid var(--et-grid);
          border-radius: 14px; padding: 1rem 1.1rem;
          transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
        }}
        [data-testid="stMetric"]:hover {{
          transform: translateY(-2px); border-color: rgba(45,226,197,.5);
          box-shadow: 0 8px 22px rgba(0,0,0,.18);
        }}
        [data-testid="stMetricLabel"] {{ color: var(--et-muted); font-size: .88rem; }}
        [data-testid="stMetricValue"] {{ color: var(--et-text); font-size: clamp(1.3rem, 2vw, 1.8rem); }}
        [data-testid="stMetricDelta"] {{ font-size: .78rem; }}
        .et-kpi-card {{
          min-height:138px; box-sizing:border-box; padding:1rem 1.1rem;
          background:var(--et-card); border:1px solid var(--et-grid);
          border-top:2px solid var(--et-accent); border-radius:14px;
          transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease;
        }}
        .et-kpi-card:hover {{
          transform:translateY(-2px); border-color:var(--et-accent);
          box-shadow:0 8px 22px rgba(0,0,0,.18);
        }}
        .et-kpi-label {{ color:var(--et-muted); font-size:.84rem; font-weight:650; }}
        .et-kpi-value {{ margin:.55rem 0 .4rem; color:var(--et-text); font-size:clamp(1.25rem,2vw,1.8rem); font-weight:700; line-height:1.2; overflow-wrap:anywhere; }}
        .et-kpi-delta {{ color:var(--et-muted); font-size:.75rem; }}
        [data-testid="stTabs"] [role="tablist"] {{
          display:flex; flex-wrap:wrap; align-items:center; gap:.25rem;
          border:0; overflow:visible;
        }}
        [data-testid="stTabs"] [role="tab"] {{
          flex:0 1 auto; min-height:34px; height:34px; padding:0 .4rem;
          border:1px solid var(--et-grid); border-radius:9px;
          background:var(--et-surface); color:var(--et-muted);
          font-size:11.5px; font-weight:700; line-height:1.1; white-space:nowrap;
          transition:transform .14s ease, border-color .14s ease, background .14s ease, box-shadow .14s ease;
        }}
        [data-testid="stTabs"] [role="tab"] [data-testid="stMarkdownContainer"],
        [data-testid="stTabs"] [role="tab"] p {{
          margin:0; font-size:11.5px; font-weight:700; line-height:1.1;
        }}
        [data-testid="stTabs"] [role="tab"]:hover {{
          transform:translateY(-1px); border-color:var(--et-tab-accent);
        }}
        [data-testid="stTabs"] [role="tab"]:focus-visible {{
          outline:2px solid var(--et-tab-accent) !important; outline-offset:2px;
        }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(1) {{ --et-tab-accent:#2DE2C5; color:#2DE2C5; }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(2) {{ --et-tab-accent:#38BDF8; color:#38BDF8; }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(3) {{ --et-tab-accent:#A78BFA; color:#A78BFA; }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(4) {{ --et-tab-accent:#34D399; color:#34D399; }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(5) {{ --et-tab-accent:#60A5FA; color:#60A5FA; }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(6) {{ --et-tab-accent:#FBBF24; color:#FBBF24; }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(7) {{ --et-tab-accent:#FB7185; color:#FB7185; }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(1)[aria-selected="true"] {{ background:rgba(45,226,197,.12); border-color:#2DE2C5; box-shadow:0 0 12px rgba(45,226,197,.16); }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(2)[aria-selected="true"] {{ background:rgba(56,189,248,.12); border-color:#38BDF8; box-shadow:0 0 12px rgba(56,189,248,.16); }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(3)[aria-selected="true"] {{ background:rgba(167,139,250,.12); border-color:#A78BFA; box-shadow:0 0 12px rgba(167,139,250,.16); }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(4)[aria-selected="true"] {{ background:rgba(52,211,153,.12); border-color:#34D399; box-shadow:0 0 12px rgba(52,211,153,.16); }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(5)[aria-selected="true"] {{ background:rgba(96,165,250,.12); border-color:#60A5FA; box-shadow:0 0 12px rgba(96,165,250,.16); }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(6)[aria-selected="true"] {{ background:rgba(251,191,36,.12); border-color:#FBBF24; box-shadow:0 0 12px rgba(251,191,36,.16); }}
        [data-testid="stTabs"] [role="tab"]:nth-of-type(7)[aria-selected="true"] {{ background:rgba(251,113,133,.12); border-color:#FB7185; box-shadow:0 0 12px rgba(251,113,133,.16); }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
          background: var(--et-card); border-color: var(--et-grid); border-radius: 14px;
        }}
        [data-testid="stAlert"] {{ border-radius: 10px; }}
        button:focus-visible, input:focus-visible, [tabindex="0"]:focus-visible {{
          outline: 2px solid var(--et-teal) !important; outline-offset: 2px;
        }}
        .et-hero {{
          display:flex; justify-content:space-between; align-items:center; gap:1rem;
          flex-wrap:wrap; padding:1.35rem 1.5rem; margin:.2rem 0 1.1rem;
          background:var(--et-surface); border:1px solid var(--et-grid); border-radius:16px;
        }}
        .et-brand {{ display:flex; align-items:center; gap:1rem; min-width:min(100%, 300px); }}
        .et-mark {{
          display:grid; place-items:center; width:50px; height:50px; flex:none;
          color:var(--et-teal); background:rgba(45,226,197,.10);
          border:1px solid rgba(45,226,197,.24); border-radius:15px; font-size:1.55rem;
        }}
        .et-title {{ margin:0; color:var(--et-text); font-size:clamp(1.4rem,3vw,2rem); line-height:1.15; }}
        .et-subtitle {{ margin:.35rem 0 0; color:var(--et-muted); font-size:.92rem; }}
        .et-status {{ display:flex; justify-content:flex-end; gap:.5rem; flex-wrap:wrap; align-items:center; }}
        .et-badge {{
          display:inline-flex; align-items:center; gap:.4rem; padding:.38rem .65rem;
          border:1px solid var(--et-grid); border-radius:999px; color:var(--et-text);
          background:var(--et-card); font-size:.72rem; font-weight:700; letter-spacing:.06em;
        }}
        .et-badge-sim {{ color:var(--et-teal); border-color:rgba(45,226,197,.32); }}
        .et-badge-upload {{ color:var(--et-cyan); border-color:rgba(56,189,248,.32); }}
        .et-load-time {{ width:100%; text-align:right; color:var(--et-muted); font-size:.75rem; }}
        .et-status {{ flex-direction:column; align-items:flex-end; }}
        .et-status-badges {{ display:flex; justify-content:flex-end; gap:.5rem; flex-wrap:wrap; }}
        .et-author {{
          display:inline-flex; align-items:center; gap:.42rem; padding:.28rem .58rem .28rem .32rem;
          border:1px solid rgba(45,226,197,.25); border-radius:10px;
          background:linear-gradient(115deg,rgba(45,226,197,.09),rgba(56,189,248,.07));
          color:var(--et-text); font-size:.78rem; font-weight:750; letter-spacing:.01em;
        }}
        .et-author-mark {{
          display:grid; place-items:center; width:22px; height:22px; flex:none;
          border:1px solid rgba(45,226,197,.32); border-radius:7px;
          background:rgba(45,226,197,.12); color:var(--et-teal);
          font-size:.65rem; font-weight:800; letter-spacing:.03em;
        }}
        .et-section-title {{ margin:.1rem 0 .15rem; color:var(--et-text); font-weight:700; font-size:1.22rem; }}
        .et-help {{ color:var(--et-muted); font-size:.82rem; }}
        @media (max-width: 900px) {{
          .block-container {{ padding-top:1rem; }}
          [data-testid="stMetric"] {{ min-height:120px; padding:.8rem; }}
        }}
        @media (max-width: 680px) {{
          .block-container {{ padding-left:.75rem; padding-right:.75rem; }}
          [data-testid="stHorizontalBlock"] {{ flex-wrap:wrap; gap:.55rem; }}
          [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            min-width:min(100%, 220px) !important; flex:1 1 100% !important;
          }}
          [data-testid="stMetric"] {{ min-height:unset; }}
          .et-hero {{ padding:1rem; align-items:flex-start; }}
          .et-brand {{ align-items:flex-start; }}
          .et-status {{ justify-content:flex-start; align-items:flex-start; }}
          .et-status-badges {{ justify-content:flex-start; }}
          .et-load-time {{ text-align:left; }}
          [data-testid="stTabs"] [role="tablist"] {{ gap:.2rem; }}
          [data-testid="stTabs"] [role="tab"] {{ flex:1 1 auto; padding:0 .35rem; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
          *, *::before, *::after {{ scroll-behavior:auto !important; transition:none !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(
    source_label: str,
    *,
    simulated: bool,
    refreshed_at: str,
    session_entry_count: int = 0,
) -> None:
    """Render product identity and truthful data provenance/status."""
    badge_class = "et-badge-sim" if simulated else "et-badge-upload"
    badge_text = "SIMULATED DATA" if simulated else "UPLOADED DATA"
    safe_source = escape(source_label)
    safe_timestamp = escape(refreshed_at)
    session_badge = (
        f'<span class="et-badge">{session_entry_count} session-only entries</span>'
        if session_entry_count
        else ""
    )
    st.markdown(
        f"""
        <section class="et-hero" aria-label="Expense Intelligence dashboard">
          <div class="et-brand">
            <div class="et-mark" aria-hidden="true">◈</div>
            <div>
              <h1 class="et-title">Expense Intelligence</h1>
              <p class="et-subtitle">Personal Finance Analytics &amp; Spending Intelligence</p>
            </div>
          </div>
          <div class="et-status">
            <div class="et-author" aria-label="Dashboard author: Mahesh Bhakre">
              <span class="et-author-mark" aria-hidden="true">MB</span>
              <span>Mahesh Bhakre</span>
            </div>
            <div class="et-status-badges">
              <span class="et-badge {badge_class}">{badge_text}</span>
              <span class="et-badge">● &nbsp;Local analytics · no live bank connection</span>
              <span class="et-badge">{safe_source}</span>
              {session_badge}
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="et-load-time">Last successful data load · {safe_timestamp}</div>',
        unsafe_allow_html=True,
    )


def render_kpis(
    values: Sequence[tuple[str, str, str, str, str]],
) -> None:
    """Render consistent five-column native Streamlit KPI cards.

    Each item is (label, value, delta, help text, accent color).
    """
    columns = st.columns(len(values), gap="small")
    for index, (label, value, delta, help_text, color) in enumerate(values):
        with columns[index]:
            st.markdown(
                f'<article class="et-kpi-card" role="group" aria-label="{escape(label)}: {escape(value)}" '
                f'title="{escape(help_text)}" style="--et-accent:{escape(color)}">'
                f'<div class="et-kpi-label">{KPI_ICONS[index % len(KPI_ICONS)]} &nbsp;{escape(label)}</div>'
                f'<div class="et-kpi-value">{escape(value)}</div>'
                f'<div class="et-kpi-delta">{escape(delta)}</div>'
                "</article>",
                unsafe_allow_html=True,
            )


def style_chart(figure: go.Figure, *, currency_axis: str | None = "y", height: int = 370) -> go.Figure:
    """Apply shared chart typography, surface colors, hover and currency axes."""
    figure.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, sans-serif", "color": THEME["text"], "size": 12},
        margin={"l": 18, "r": 22, "t": 48, "b": 24},
        hoverlabel={"bgcolor": THEME["card"], "bordercolor": THEME["grid"], "font_color": THEME["text"]},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
    )
    figure.update_xaxes(showgrid=False, linecolor=THEME["grid"], automargin=True)
    figure.update_yaxes(showgrid=True, gridcolor=THEME["grid"], zerolinecolor=THEME["grid"], automargin=True)
    if currency_axis == "y":
        figure.update_yaxes(tickprefix="₹", separatethousands=True, tickformat=",.0f")
    elif currency_axis == "x":
        figure.update_xaxes(tickprefix="₹", separatethousands=True, tickformat=",.0f")
    return figure
