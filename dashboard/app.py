import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Market Intelligence Dashboard", layout="wide")


@st.cache_resource
def get_engine():
    url = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(url)


@st.cache_data(ttl=3600)
def load_indicators(ticker: str) -> pd.DataFrame:
    query = text("""
        SELECT * FROM marts.technical_indicators
        WHERE ticker = :ticker
        ORDER BY date
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn, params={"ticker": ticker})


@st.cache_data(ttl=3600)
def load_momentum_screener() -> pd.DataFrame:
    query = text("""
        SELECT
            ticker,
            date,
            close,
            return_1d,
            return_1w,
            return_1m,
            return_3m,
            vol_21d_annualized
        FROM marts.rolling_returns
        WHERE date = (SELECT MAX(date) FROM marts.rolling_returns)
        ORDER BY return_1m DESC NULLS LAST
    """)
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=3600)
def load_all_tickers() -> list[str]:
    query = text("SELECT DISTINCT ticker FROM raw.prices ORDER BY ticker")
    with get_engine().connect() as conn:
        return pd.read_sql(query, conn)["ticker"].tolist()


# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("Market Intelligence")
page = st.sidebar.radio("View", ["Price Chart", "Momentum Screener"])

tickers = load_all_tickers()

# ── Price Chart ───────────────────────────────────────────────────────────────
if page == "Price Chart":
    ticker = st.sidebar.selectbox("Ticker", tickers, index=0)
    df = load_indicators(ticker)

    st.title(f"{ticker} — Technical Analysis")

    col1, col2, col3, col4 = st.columns(4)
    latest = df.iloc[-1]
    col1.metric("Close", f"${latest['close']:.2f}")
    col2.metric("RSI (14)", f"{latest['rsi_14']:.1f}" if pd.notna(latest["rsi_14"]) else "—")
    col3.metric("SMA 50", f"${latest['sma_50']:.2f}" if pd.notna(latest["sma_50"]) else "—")
    col4.metric("Daily Return", f"{latest['daily_return']*100:.2f}%" if pd.notna(latest["daily_return"]) else "—")

    # Candlestick + Bollinger Bands
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="OHLC"
    ))
    fig.add_trace(go.Scatter(x=df["date"], y=df["sma_20"], name="SMA 20", line=dict(color="orange", width=1)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["sma_50"], name="SMA 50", line=dict(color="blue", width=1)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["bb_upper"], name="BB Upper",
                             line=dict(color="gray", dash="dash", width=1)))
    fig.add_trace(go.Scatter(x=df["date"], y=df["bb_lower"], name="BB Lower",
                             line=dict(color="gray", dash="dash", width=1),
                             fill="tonexty", fillcolor="rgba(128,128,128,0.05)"))
    fig.update_layout(xaxis_rangeslider_visible=False, height=500)
    st.plotly_chart(fig, use_container_width=True)

    # RSI chart
    st.subheader("RSI (14)")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df["date"], y=df["rsi_14"], name="RSI", line=dict(color="purple")))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig_rsi.update_layout(height=250, yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig_rsi, use_container_width=True)

# ── Momentum Screener ─────────────────────────────────────────────────────────
elif page == "Momentum Screener":
    st.title("Momentum Screener")
    st.caption("Latest trading day — sorted by 1-month return")

    df = load_momentum_screener()

    def pct(val):
        if pd.isna(val):
            return "—"
        color = "green" if val >= 0 else "red"
        return f'<span style="color:{color}">{val*100:.2f}%</span>'

    df_display = df.copy()
    for col in ["return_1d", "return_1w", "return_1m", "return_3m"]:
        df_display[col] = df_display[col].apply(pct)
    df_display["close"] = df_display["close"].apply(lambda v: f"${v:.2f}")
    df_display["vol_21d_annualized"] = df_display["vol_21d_annualized"].apply(
        lambda v: f"{v*100:.1f}%" if pd.notna(v) else "—"
    )
    df_display.columns = ["Ticker", "Date", "Price", "1D", "1W", "1M", "3M", "Vol (21d)"]

    st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
