import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="QE Genix: Trend Predictor", layout="wide")
st_autorefresh(interval=60 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"

# --- 2. MULTI-TIMEFRAME BRAIN ---
def fetch_mtf_data():
    try:
        # Fetch Daily data for the "Anchor" Trend
        d_trend = yf.download(SENSEX_TICKER, period="5d", interval="15m", progress=False, auto_adjust=True)
        # Fetch Intraday data for the "Execution"
        d_live = yf.download(SENSEX_TICKER, period="1d", interval="1m", progress=False, auto_adjust=True)
        return d_trend, d_live
    except:
        return None, None

def get_prediction(d_trend, d_live):
    # ANCHOR: Use 15-minute TEMA to decide Daily Bias
    trend_close = d_trend['Close'].iloc[:,0] if isinstance(d_trend['Close'], pd.DataFrame) else d_trend['Close']
    anchor_tema = ta.tema(trend_close, length=20).iloc[-1]
    last_price = trend_close.iloc[-1]
    
    daily_bias = "BULLISH" if last_price > anchor_tema else "BEARISH"
    
    # TRIGGER: Use 1-minute RSI & TEMA for entry timing
    live_close = d_live['Close'].iloc[:,0] if isinstance(d_live['Close'], pd.DataFrame) else d_live['Close']
    live_tema = ta.tema(live_close, length=9).iloc[-1]
    rsi = ta.rsi(live_close, length=14).iloc[-1]
    
    curr_p = live_close.iloc[-1]
    
    # FILTER: Only signal if Live timing matches Daily Bias
    signal = "HOLD"
    if daily_bias == "BULLISH" and curr_p > live_tema and rsi > 50:
        signal = "STRONG BUY (CE)"
    elif daily_bias == "BEARISH" and curr_p < live_tema and rsi < 50:
        signal = "STRONG SELL (PE)"
        
    return daily_bias, signal, curr_p, rsi

# --- 3. UI DISPLAY ---
st.title("🛰️ QE Genix: Trend Prediction Engine")

d_trend, d_live = fetch_mtf_data()

if d_trend is not None and not d_live.empty:
    bias, signal, price, rsi = get_prediction(d_trend, d_live)
    
    # Top Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("SENSEX SPOT", f"{price:,.2f}")
    c2.markdown(f"**DAILY ANCHOR:** <span style='color:{'#2ecc71' if bias == 'BULLISH' else '#e74c3c'}'>{bias}</span>", unsafe_allow_html=True)
    c3.metric("MOMENTUM (RSI)", f"{rsi:.1f}")

    # THE PREDICTION BOX
    st.divider()
    box_color = "#2ecc71" if "BUY" in signal else ("#e74c3c" if "SELL" in signal else "#fbc531")
    
    st.markdown(f"""
        <div style="background-color:{box_color}22; border:5px solid {box_color}; padding:40px; border-radius:20px; text-align:center;">
            <h1 style="color:{box_color}; margin:0;">{signal}</h1>
            <p style="font-size:18px; color:white;">Strategy: Aligning 15m Trend with 1m Momentum</p>
        </div>
    """, unsafe_allow_html=True)

    if signal == "HOLD":
        st.info("🛡️ **System Logic:** Waiting for 1-minute momentum to align with the 15-minute daily trend. This prevents whipsaws.")
else:
    st.warning("Awaiting Market Pulse...")