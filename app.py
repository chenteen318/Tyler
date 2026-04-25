import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import twstock
import calendar
from datetime import date, timedelta

DEFAULT_STOCKS = [
    ("奕力-KY",  "3532.TW"),
    ("台聚",      "1310.TW"),
    ("中鼎",      "9933.TW"),
    ("乙盛-KY",  "5243.TW"),
    ("台郡",      "6269.TW"),
    ("中環",      "2323.TW"),
    ("仁寶",      "2324.TW"),
    ("漢磊",      "6168.TW"),
]


def _prev_months(n=3):
    today = date.today()
    result = []
    for i in range(n, 0, -1):
        month = (today.month - i - 1) % 12 + 1
        year = today.year + (today.month - i - 1) // 12
        last_day = calendar.monthrange(year, month)[1]
        end = date(year, month, last_day) + timedelta(days=1)  # exclusive end for yfinance
        result.append((
            f"{year}-{month:02d}-01",
            end.strftime("%Y-%m-%d"),
            f"{year}年{month}月",
        ))
    return result


MONTHS = _prev_months()

# ── Design tokens ─────────────────────────────────────
BG        = "#ffffff"
CARD      = "#f8fafc"
CARD2     = "#f1f5f9"
BORDER    = "#e2e8f0"
BLUE      = "#2563eb"
GREEN     = "#16a34a"
RED       = "#dc2626"
TEXT      = "#0f172a"
MUTED     = "#64748b"
CHART_BG  = "#ffffff"
GRID      = "#f1f5f9"

DESIGN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #ffffff !important;
    color: #0f172a !important;
    font-family: 'Inter', sans-serif !important;
}
.block-container {
    padding: 1.5rem 2rem 3rem !important;
    max-width: 1400px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #f8fafc !important;
    border-right: 1px solid #e2e8f0 !important;
}
[data-testid="stSidebar"] * { color: #0f172a !important; }
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background-color: #ffffff !important;
    border-color: #e2e8f0 !important;
}

/* ── Title ── */
h1 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.9rem !important;
    background: linear-gradient(90deg, #2563eb, #16a34a) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin-bottom: 0.25rem !important;
}
h2 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    color: #334155 !important;
    letter-spacing: 0.02em !important;
}
h3 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    color: #2563eb !important;
    border-left: 3px solid #2563eb;
    padding-left: 0.6rem !important;
    margin: 1.2rem 0 0.6rem !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #e2e8f0 !important;
    gap: 0.25rem !important;
}
[data-testid="stTabs"] button[role="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.2s !important;
}
[data-testid="stTabs"] button[role="tab"]:hover { color: #0f172a !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #2563eb !important;
    border-bottom: 2px solid #2563eb !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    position: relative !important;
    overflow: hidden !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #2563eb, #16a34a);
}
[data-testid="stMetricLabel"] p {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 500 !important;
    color: #2563eb !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #ffffff !important;
    color: #2563eb !important;
    border: 1px solid #2563eb !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.45rem 1.2rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #eff6ff !important;
    border-color: #1d4ed8 !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.15) !important;
}

/* ── Selectbox / Multiselect ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background-color: #ffffff !important;
    border-color: #e2e8f0 !important;
    border-radius: 8px !important;
    color: #0f172a !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label {
    color: #64748b !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    margin-bottom: 1rem !important;
}
[data-testid="stExpander"] summary {
    color: #64748b !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    border: 1px solid #e2e8f0 !important;
}
[data-testid="stDataFrame"] th {
    background-color: #f8fafc !important;
    color: #64748b !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    border-bottom: 1px solid #e2e8f0 !important;
}
[data-testid="stDataFrame"] td {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    color: #334155 !important;
    border-bottom: 1px solid #f1f5f9 !important;
}

/* ── Divider ── */
hr { border-color: #e2e8f0 !important; margin: 1.5rem 0 !important; }

/* ── Info box ── */
[data-testid="stAlert"] {
    background-color: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    color: #64748b !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #2563eb !important; }

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
    color: #94a3b8 !important;
    font-size: 0.75rem !important;
}

/* ── Sidebar header ── */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    -webkit-text-fill-color: #2563eb !important;
    color: #2563eb !important;
    border: none !important;
    padding-left: 0 !important;
}

/* ── Mobile ── */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem 2rem !important; }
    h1 { font-size: 1.4rem !important; }
    h3 { font-size: 0.9rem !important; }

    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.5rem !important; }
    [data-testid="column"] { min-width: 100% !important; flex: 1 1 100% !important; }

    [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) { flex-wrap: nowrap !important; }
    [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) [data-testid="column"] {
        min-width: 30% !important; flex: 1 1 30% !important;
    }
    [data-testid="stMetricValue"] { font-size: 1rem !important; }
    [data-testid="stMetricLabel"] p { font-size: 0.65rem !important; }
    [data-testid="stDataFrame"] > div { overflow-x: auto !important; }
    [data-testid="stTab"] p { font-size: 0.8rem !important; }
}
</style>
"""


@st.cache_data(ttl=86400, show_spinner="載入台股清單…")
def load_tw_stock_list():
    results = []
    suffix_map = {"上市": ".TW", "上櫃": ".TWO"}
    for code, info in twstock.codes.items():
        if not code.isdigit():
            continue
        if code.startswith("00"):
            continue
        suffix = suffix_map.get(info.market)
        if suffix and info.name:
            results.append((info.name, f"{code}{suffix}"))
    results.sort(key=lambda x: x[1])
    return results if results else DEFAULT_STOCKS


@st.cache_data(ttl=3600)
def fetch(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False, timeout=10)
        if df.empty:
            return None
        df = df[["High", "Low", "Close"]].copy()
        df.index = pd.to_datetime(df.index)
        df.columns = ["最高價", "最低價", "收盤價"]
        df["差值"] = df["最高價"] - df["最低價"]
        df.index = df.index.strftime("%Y-%m-%d")
        df.index.name = "日期"
        return df.round(2)
    except Exception:
        return None


def get_monthly_stats(ticker):
    stats = []
    for start, end, label in MONTHS:
        df = fetch(ticker, start, end)
        if df is None or df.empty:
            stats.append((label, None, None))
        else:
            diffs = df["差值"].astype(float)
            stats.append((label, round(diffs.mean(), 4), round(diffs.std(ddof=1), 4)))
    return stats


def color_scale(val, col_data, low_hex, high_hex):
    if pd.isna(val):
        return f"background-color: {CARD}; color: {MUTED}"
    mn, mx = col_data.min(), col_data.max()
    ratio = (val - mn) / (mx - mn) if mx != mn else 0.5
    r1,g1,b1 = int(low_hex[0:2],16), int(low_hex[2:4],16), int(low_hex[4:6],16)
    r2,g2,b2 = int(high_hex[0:2],16), int(high_hex[2:4],16), int(high_hex[4:6],16)
    r = int(r1+(r2-r1)*ratio)
    g = int(g1+(g2-g1)*ratio)
    b = int(b1+(b2-b1)*ratio)
    lum = 0.299*r + 0.587*g + 0.114*b
    fg = "#0f172a" if lum > 140 else "#ffffff"
    return f"background-color: #{r:02x}{g:02x}{b:02x}; color: {fg}"


CHART_LAYOUT = dict(
    paper_bgcolor=CHART_BG,
    plot_bgcolor=CHART_BG,
    font=dict(family="Inter, sans-serif", color=TEXT, size=11),
    xaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=BORDER, tickfont=dict(color=MUTED, size=10)),
    yaxis=dict(gridcolor=GRID, linecolor=BORDER, tickcolor=BORDER, tickfont=dict(family="JetBrains Mono", color=MUTED, size=10)),
    margin=dict(t=20, b=10, l=10, r=10),
    hoverlabel=dict(bgcolor=CARD2, bordercolor=BORDER, font=dict(family="JetBrains Mono", color=TEXT)),
)


MONTH_COLORS = ["#93c5fd", "#3b82f6", "#1e40af"]


def make_grouped_chart(summary_df, col_suffix, y_title):
    fig = go.Figure()
    stocks = summary_df.index.tolist()
    for i, (_, _, label) in enumerate(MONTHS):
        col = f"{label} {col_suffix}"
        vals = summary_df[col].tolist() if col in summary_df.columns else [None] * len(stocks)
        fig.add_trace(go.Bar(
            name=label,
            x=stocks,
            y=vals,
            marker=dict(color=MONTH_COLORS[i], opacity=0.85, line=dict(width=0)),
            text=[f"{v:.4f}" if v is not None and not pd.isna(v) else "—" for v in vals],
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=9, color=TEXT),
            hovertemplate=f"<b>%{{x}}</b><br>{label}<br>{y_title}: %{{y:.4f}}<extra></extra>",
        ))
    fig.update_layout(
        barmode="group",
        height=340,
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11, color=TEXT)),
        **CHART_LAYOUT,
    )
    fig.update_yaxes(title_text=y_title, title_font=dict(color=MUTED, size=11))
    return fig


def make_line_chart(df, diffs, avg_d):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=diffs,
        mode="lines+markers", name="差值",
        line=dict(color=BLUE, width=2),
        marker=dict(size=5, color=BLUE, line=dict(color=BG, width=1)),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.08)",
        hovertemplate="%{x}<br><b>差值: %{y:.4f}</b><extra></extra>",
    ))
    fig.add_hline(
        y=avg_d, line_dash="dot", line_color=GREEN, line_width=1.5,
        annotation_text=f"均值 {avg_d:.4f}",
        annotation_font=dict(color=GREEN, size=11, family="JetBrains Mono"),
        annotation_position="top right",
    )
    fig.update_layout(height=280, xaxis_tickangle=-45, showlegend=False, **CHART_LAYOUT)
    return fig


# ── 頁面設定 ──────────────────────────────────────────
st.set_page_config(
    page_title="台股差值分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto",
)
st.markdown(DESIGN_CSS, unsafe_allow_html=True)

# ── 載入台股清單 ───────────────────────────────────────
all_stocks = load_tw_stock_list()
option_labels  = [f"{name} ({code})" for name, code in all_stocks]
label_to_tuple = {f"{name} ({code})": (name, code) for name, code in all_stocks}

if "selected_labels" not in st.session_state:
    st.session_state.selected_labels = []
if "analysis_started" not in st.session_state:
    st.session_state.analysis_started = False


def render_stock_selector(key_suffix):
    selected = st.multiselect(
        "搜尋並選擇股票",
        options=option_labels,
        default=st.session_state.selected_labels,
        placeholder="輸入名稱或代號，例：台積電 / 2330",
        key=f"multiselect_{key_suffix}",
    )
    st.session_state.selected_labels = selected
    if st.button("✕ 清除選股", use_container_width=True, key=f"reset_{key_suffix}"):
        st.session_state.selected_labels = []
        st.session_state.analysis_started = False
        st.rerun()
    st.caption(f"資料庫 {len(all_stocks):,} 支上市上櫃股票")


# ── 側邊欄 ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 自選股")
    render_stock_selector("sidebar")
    st.markdown("---")
    if st.button("🔍 開始分析", use_container_width=True, key="start_sidebar", type="primary"):
        st.session_state.analysis_started = True
        st.rerun()

STOCKS = [label_to_tuple[lbl] for lbl in st.session_state.selected_labels if lbl in label_to_tuple]

# ── 標題列 ────────────────────────────────────────────
st.markdown("# 台股高低價差值分析")
st.markdown(
    f"<p style='color:{MUTED}; font-size:0.85rem; margin-top:-0.5rem; margin-bottom:1rem;'>"
    f"分析期間：{MONTHS[0][2]} ─ {MONTHS[-1][2]}　｜　自選股 {len(STOCKS)} 支</p>",
    unsafe_allow_html=True,
)

# ── 手機版自選股 ──────────────────────────────────────
with st.expander("📋 管理自選股", expanded=False):
    render_stock_selector("mobile")
    STOCKS = [label_to_tuple[lbl] for lbl in st.session_state.selected_labels if lbl in label_to_tuple]

# ── Tabs ──────────────────────────────────────────────
tab_summary, tab_detail = st.tabs(["📊  總覽", "📈  各股明細"])

# ── 總覽頁 ────────────────────────────────────────────
with tab_summary:
    if not STOCKS:
        st.info("請在側邊欄或上方展開區搜尋並加入股票")
    elif not st.session_state.analysis_started:
        st.info("選好股票後，點擊側邊欄的「🔍 開始分析」以載入資料")
    else:
        st.markdown(f"### 差值統計總表　<span style='color:{MUTED};font-size:0.8rem;font-weight:400'>共 {len(STOCKS)} 支</span>", unsafe_allow_html=True)

        with st.spinner("資料下載中…"):
            rows = []
            for stock_name, ticker in STOCKS:
                row = {"股票名稱": stock_name, "代碼": ticker}
                for label, avg_d, std_d in get_monthly_stats(ticker):
                    row[f"{label} 平均"] = avg_d
                    row[f"{label} 標準差"] = std_d
                rows.append(row)

        summary_df = pd.DataFrame(rows).set_index("股票名稱")
        avg_cols = [c for c in summary_df.columns if "平均" in c]
        std_cols = [c for c in summary_df.columns if "標準差" in c]

        def apply_colors(df):
            styles = pd.DataFrame("", index=df.index, columns=df.columns)
            for col in avg_cols + std_cols:
                if col in df.columns:
                    styles[col] = df[col].apply(
                        lambda v: color_scale(v, df[col].dropna(), "dbeafe", "1e40af")
                    )
            return styles

        styled = (
            summary_df.style
            .apply(apply_colors, axis=None)
            .format("{:.4f}", subset=avg_cols + std_cols, na_rep="—")
            .set_table_styles([{
                "selector": "th",
                "props": [("font-family","Inter"), ("font-size","0.75rem"),
                          ("text-transform","uppercase"), ("letter-spacing","0.05em")]
            }])
        )
        st.dataframe(styled, use_container_width=True, height=min(120 + len(STOCKS) * 35, 500))

        st.divider()
        st.markdown("### 各股差值平均（前三個月）")
        st.plotly_chart(make_grouped_chart(summary_df, "平均", "差值平均"), use_container_width=True, config={"responsive": True, "displayModeBar": False})

        st.markdown("### 各股差值標準差（前三個月）")
        st.plotly_chart(make_grouped_chart(summary_df, "標準差", "差值標準差"), use_container_width=True, config={"responsive": True, "displayModeBar": False})


# ── 各股明細頁 ─────────────────────────────────────────
with tab_detail:
    if not STOCKS:
        st.info("請在側邊欄或上方展開區搜尋並加入股票")
    elif not st.session_state.analysis_started:
        st.info("選好股票後，點擊側邊欄的「🔍 開始分析」以載入資料")
    else:
        sel_col1, sel_col2 = st.columns([1, 1])
        with sel_col1:
            stock_name = st.selectbox("股票", [s[0] for s in STOCKS])
        ticker = dict(STOCKS)[stock_name]
        with sel_col2:
            month_filter = st.selectbox("月份", ["全部"] + [m[2] for m in MONTHS], key="detail_month")

        months_to_show = MONTHS if month_filter == "全部" else [m for m in MONTHS if m[2] == month_filter]

        for start, end, label in months_to_show:
            st.markdown(f"### {label}　{stock_name}　<span style='color:{MUTED};font-size:0.85rem;font-weight:400'>{ticker}</span>", unsafe_allow_html=True)

            with st.spinner(f"載入 {label}…"):
                df = fetch(ticker, start, end)

            if df is None or df.empty:
                st.info("此月份無資料")
                continue

            diffs = df["差值"].astype(float)
            avg_d = diffs.mean()
            std_d = diffs.std(ddof=1)

            m1, m2, m3 = st.columns(3)
            m1.metric("交易日數", f"{len(df)} 天")
            m2.metric("差值平均", f"{avg_d:.4f}")
            m3.metric("差值標準差", f"{std_d:.4f}")

            left, right = st.columns([2, 3])

            diff_col = diffs.dropna()
            def color_diff(val, _col=diff_col):
                if pd.isna(val):
                    return f"background-color:{CARD}; color:{MUTED}"
                ratio = (val-_col.min())/(_col.max()-_col.min()) if _col.max()!=_col.min() else 0.5
                r = int(0xdb + (0x16-0xdb)*ratio)
                g = int(0xea + (0xa3-0xea)*ratio)
                b = int(0xfe + (0x4a-0xfe)*ratio)
                lum = 0.299*r + 0.587*g + 0.114*b
                fg = "#0f172a" if lum > 140 else "#ffffff"
                return f"background-color:#{r:02x}{g:02x}{b:02x}; color:{fg}"

            with left:
                st.dataframe(
                    df.style.map(color_diff, subset=["差值"]).format("{:.2f}"),
                    use_container_width=True,
                    height=280,
                )
            with right:
                st.plotly_chart(
                    make_line_chart(df, diffs, avg_d),
                    use_container_width=True,
                    config={"responsive": True, "displayModeBar": False},
                )

            st.divider()
