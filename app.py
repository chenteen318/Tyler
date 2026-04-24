import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import twstock

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

MONTHS = [
    ("2025-12-01", "2025-12-31", "2025年12月"),
    ("2026-01-01", "2026-01-31", "2026年1月"),
    ("2026-02-01", "2026-02-28", "2026年2月"),
]

HEADER_BLUE  = "#4472C4"
HEADER_GREEN = "#70AD47"

MOBILE_CSS = """
<style>
/* ── 手機版：欄位自動堆疊 ── */
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.5rem !important;
    }
    [data-testid="column"] {
        min-width: 100% !important;
        width: 100% !important;
        flex: 1 1 100% !important;
    }

    /* 標題縮小 */
    h1 { font-size: 1.4rem !important; line-height: 1.3 !important; }
    h2 { font-size: 1.1rem !important; }
    h3 { font-size: 1rem !important; }

    /* Metric 卡片排成一排 */
    [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
        flex-wrap: nowrap !important;
    }
    [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"])
        [data-testid="column"] {
        min-width: 30% !important;
        width: 33% !important;
        flex: 1 1 30% !important;
    }
    [data-testid="stMetricValue"] { font-size: 1rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.7rem !important; }

    /* Dataframe 水平捲動 */
    [data-testid="stDataFrame"] > div {
        overflow-x: auto !important;
    }

    /* 減少頁面左右 padding */
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-top: 1rem !important;
    }

    /* Tab 標籤字型 */
    [data-testid="stTab"] p { font-size: 0.85rem !important; }

    /* 側邊欄提示 */
    section[data-testid="stSidebar"] { min-width: 280px !important; }
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
        suffix = suffix_map.get(info.market)
        if suffix and info.name:
            results.append((info.name, f"{code}{suffix}"))
    results.sort(key=lambda x: x[1])
    return results if results else DEFAULT_STOCKS


@st.cache_data(ttl=3600)
def fetch(ticker, start, end):
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        return None
    df = df[["High", "Low", "Close"]].copy()
    df.index = pd.to_datetime(df.index)
    df.columns = ["最高價", "最低價", "收盤價"]
    df["差值"] = df["最高價"] - df["最低價"]
    df.index = df.index.strftime("%Y-%m-%d")
    df.index.name = "日期"
    return df.round(2)


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


def color_scale(val, col_data, low_color, high_color):
    if pd.isna(val):
        return ""
    mn, mx = col_data.min(), col_data.max()
    ratio = (val - mn) / (mx - mn) if mx != mn else 0.5
    r1, g1, b1 = int(low_color[0:2], 16), int(low_color[2:4], 16), int(low_color[4:6], 16)
    r2, g2, b2 = int(high_color[0:2], 16), int(high_color[2:4], 16), int(high_color[4:6], 16)
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)
    return f"background-color: #{r:02x}{g:02x}{b:02x}"


def make_bar_chart(chart_df, col_avg):
    fig = go.Figure(go.Bar(
        x=chart_df["股票名稱"],
        y=chart_df[col_avg],
        marker_color=HEADER_BLUE,
        text=chart_df[col_avg].round(4),
        textposition="outside",
    ))
    fig.update_layout(
        yaxis_title="差值平均", xaxis_title="",
        height=320,
        margin=dict(t=30, b=10, l=10, r=10),
        font=dict(size=12),
    )
    return fig


def make_line_chart(df, diffs, avg_d):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=diffs,
        mode="lines+markers", name="差值",
        line=dict(color=HEADER_BLUE, width=2),
        marker=dict(size=5),
    ))
    fig.add_hline(
        y=avg_d, line_dash="dash", line_color=HEADER_GREEN,
        annotation_text=f"平均 {avg_d:.4f}",
        annotation_font_size=11,
    )
    fig.update_layout(
        height=280,
        yaxis_title="差值",
        xaxis_title="",
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis_tickangle=-45,
        font=dict(size=11),
    )
    return fig


# ── 頁面設定 ──────────────────────────────────────────
st.set_page_config(page_title="多股差值分析", layout="wide", initial_sidebar_state="auto")
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# ── 載入台股清單 ───────────────────────────────────────
all_stocks = load_tw_stock_list()
option_labels  = [f"{name} ({code})" for name, code in all_stocks]
label_to_tuple = {f"{name} ({code})": (name, code) for name, code in all_stocks}
code_to_label  = {code: f"{name} ({code})" for name, code in all_stocks}
default_labels = [code_to_label.get(code, f"{name} ({code})") for name, code in DEFAULT_STOCKS]

# ── 重設 session state ───────────────────────────────
if "selected_labels" not in st.session_state:
    st.session_state.selected_labels = default_labels


def render_stock_selector(key_suffix):
    """Render multiselect + reset; sync via session_state."""
    selected = st.multiselect(
        "搜尋並選擇股票（輸入名稱或代號）",
        options=option_labels,
        default=st.session_state.selected_labels,
        placeholder="例：台積電 或 2330",
        key=f"multiselect_{key_suffix}",
    )
    st.session_state.selected_labels = selected

    if st.button("重設為預設清單", use_container_width=True, key=f"reset_{key_suffix}"):
        st.session_state.selected_labels = default_labels
        st.rerun()

    st.caption(f"資料庫共 {len(all_stocks):,} 支台股")


# ── 側邊欄（桌面） ────────────────────────────────────
with st.sidebar:
    st.header("📋 自選股")
    render_stock_selector("sidebar")

STOCKS = [label_to_tuple[lbl] for lbl in st.session_state.selected_labels if lbl in label_to_tuple]

# ── 主畫面標題 ────────────────────────────────────────
st.title("多股高低價差值分析")

# ── 手機版：自選股展開區（桌面自動折疊） ──────────────
with st.expander("📋 管理自選股（手機版）", expanded=False):
    render_stock_selector("mobile")
    STOCKS = [label_to_tuple[lbl] for lbl in st.session_state.selected_labels if lbl in label_to_tuple]

# ── Tabs ──────────────────────────────────────────────
tab_summary, tab_detail = st.tabs(["📊 總覽", "📈 各股明細"])

# ── 總覽頁 ────────────────────────────────────────────
with tab_summary:
    if not STOCKS:
        st.info("請搜尋並選擇股票（上方展開區或左側側邊欄）")
    else:
        st.subheader(f"各股月份差值統計（共 {len(STOCKS)} 支）")

        with st.spinner("下載資料中…"):
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
            for col in avg_cols:
                if col in df.columns:
                    styles[col] = df[col].apply(
                        lambda v: color_scale(v, df[col].dropna(), "dce6f4", "1f4e79")
                    )
            for col in std_cols:
                if col in df.columns:
                    styles[col] = df[col].apply(
                        lambda v: color_scale(v, df[col].dropna(), "fce4e4", "7b0000")
                    )
            return styles

        styled = summary_df.style.apply(apply_colors, axis=None).format(
            "{:.4f}", subset=avg_cols + std_cols, na_rep="—"
        )
        st.dataframe(styled, use_container_width=True, height=min(100 + len(STOCKS) * 35, 480))

        st.divider()
        st.subheader("差值平均比較圖")
        month_choice = st.selectbox("選擇月份", [m[2] for m in MONTHS], key="summary_month")
        col_avg = f"{month_choice} 平均"
        chart_df = summary_df[[col_avg]].dropna().reset_index()
        st.plotly_chart(
            make_bar_chart(chart_df, col_avg),
            use_container_width=True,
            config={"responsive": True},
        )


# ── 各股明細頁 ─────────────────────────────────────────
with tab_detail:
    if not STOCKS:
        st.info("請搜尋並選擇股票（上方展開區或左側側邊欄）")
    else:
        # 選股票 + 月份（手機會自動堆疊）
        sel_col1, sel_col2 = st.columns([1, 1])
        with sel_col1:
            stock_name = st.selectbox("選擇股票", [s[0] for s in STOCKS])
        ticker = dict(STOCKS)[stock_name]
        with sel_col2:
            month_filter = st.selectbox(
                "選擇月份", ["全部"] + [m[2] for m in MONTHS], key="detail_month"
            )

        months_to_show = (
            MONTHS if month_filter == "全部"
            else [m for m in MONTHS if m[2] == month_filter]
        )

        for start, end, label in months_to_show:
            st.subheader(f"{label}　{stock_name}（{ticker}）")
            with st.spinner(f"下載 {label}…"):
                df = fetch(ticker, start, end)

            if df is None or df.empty:
                st.info("此月份無資料")
                continue

            diffs = df["差值"].astype(float)
            avg_d = diffs.mean()
            std_d = diffs.std(ddof=1)

            # 指標列（3 欄，手機保持一排）
            m1, m2, m3 = st.columns(3)
            m1.metric("交易日數", len(df))
            m2.metric("差值平均", f"{avg_d:.4f}")
            m3.metric("差值標準差", f"{std_d:.4f}")

            # 圖表（手機：上下；桌面：左右）
            left, right = st.columns([2, 3])

            diff_col = diffs.dropna()
            def color_diff(val, _col=diff_col):
                if pd.isna(val):
                    return ""
                ratio = (
                    (val - _col.min()) / (_col.max() - _col.min())
                    if _col.max() != _col.min() else 0.5
                )
                r = int(0xff + (0xd7 - 0xff) * ratio)
                g = int(0xff * (1 - ratio))
                return f"background-color: #{r:02x}{g:02x}00"

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
                    config={"responsive": True},
                )

            st.divider()
