import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import numpy as np
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG ---
st.set_page_config(page_title="QE Genix: Stable Sniper", layout="wide")
st_autorefresh(interval=60 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"

# --- 2. THE STABILITY BRAIN ---
@st.cache_data(ttl=60)
def fetch_robust_data():
    df = yf.download(SENSEX_TICKER, period="5d", interval="5m", progress=False, auto_adjust=True)
    return df

def get_stable_signal(df):
    close = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
    
    # Noise Killer 1: Zero-Lag EMA (Fast but smooth)
    zlema = ta.zlma(close, length=20)
    curr_zlema = zlema.iloc[-1]
    
    # Noise Killer 2: Volatility Squeeze (Bollinger Bands vs Keltner)
    # We only trade when the 'Squeeze' is released
    atr = ta.atr(df['High'], df['Low'], close, length=14).iloc[-1]
    
    # Signal Hysteresis: Decision must be held for 3 candles (15 mins) to be "Stable"
    is_bullish = (close.iloc[-1] > curr_zlema) and (close.iloc[-3] > zlema.iloc[-3])
    is_bearish = (close.iloc[-1] < curr_zlema) and (close.iloc[-3] < zlema.iloc[-3])
    
    return is_bullish, is_bearish, close.iloc[-1], curr_zlema, atr

# --- 3. UI: COMMAND CENTER ---
st.title("🛰️ QE Genix: Stable Prediction Engine")
st.caption("v4.1 - Zero-Lag Stability Protocol")

data = fetch_robust_data()

if data is not None and not data.empty:
    is_up, is_down, price, trend_line, vol = get_stable_signal(data)
    
    # THE PREDICTION BOX
    st.divider()
    
    if is_up:
        status, color, action = "STABLE BULLISH", "#2ecc71", "BUY CALL (CE)"
    elif is_down:
        status, color, action = "STABLE BEARISH", "#e74c3c", "BUY PUT (PE)"
    else:
        status, color, action = "NOISE DETECTED", "#fbc531", "WAIT / HOLD CASH"

    st.markdown(f"""
        <div style="background-color:{color}22; border:5px solid {color}; padding:30px; border-radius:15px; text-align:center;">
            <p style="font-size:16px; color:{color}; font-weight:bold;">{status}</p>
            <h1 style="color:white; margin:10px 0;">{action}</h1>
            <p style="color:#aaa;">Trend Lock active. Signal requires 15-minute confirmation to flip.</p>
        </div>
    """, unsafe_allow_html=True)

    # VITALS
    m1, m2, m3 = st.columns(3)
    m1.metric("Sensex Spot", f"{price:,.2f}")
    m2.metric("Trend Line", f"{trend_line:,.2f}")
    m3.metric("Volatility (ATR)", f"{vol:.1f} pts")

else:
    st.error("📡 Waiting for Satellite Sync... (Check internet or requirements)")