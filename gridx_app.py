import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import numpy as np
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & HEARTBEAT ---
st.set_page_config(page_title="QE Genix: Apex Sniper", layout="wide")
st_autorefresh(interval=60 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"

# --- 2. SATELLITE ENGINE WITH FALLBACK ---
def fetch_data_with_fallback():
    try:
        # Attempt stealth fetch
        df = yf.download(SENSEX_TICKER, period="2d", interval="5m", progress=False)
        if df.empty: return None, "Rate Limited"
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        return df, "Live"
    except:
        return None, "Connection Blocked"

# --- 3. UI: COCKPIT ---
st.title("🛰️ QE Genix: Sensex Tactical Engine")
st.caption("v4.6 - Zero-Downtime Hybrid Protocol (Jan 1, 2026)")

data, status = fetch_data_with_fallback()

# --- 4. THE MANUAL TACTICAL BRIDGE ---
with st.sidebar:
    st.header("🛠️ Tactical Override")
    override = st.toggle("Enable Manual Entry", value=(status != "Live"))
    
    if override:
        st.warning("Manual Mode Active: Enter price from broker.")
        manual_price = st.number_input("Current Sensex Spot:", value=85220.0, step=1.0)
        manual_trend = st.selectbox("Current 5m Trend (from chart):", ["Upward", "Downward", "Sideways"])

# --- 5. LOGIC PROCESSING ---
if not override and data is not None:
    # AUTOMATED LOGIC
    close = data['Close']
    curr_p = float(close.iloc[-1])
    zlma = ta.zlma(close, length=20).iloc[-1]
    rsi = ta.rsi(close, length=14).iloc[-1]
    
    is_up = (curr_p > zlma) and (rsi > 52)
    is_down = (curr_p < zlma) and (rsi < 48)
    mode_label = "📡 SATELLITE SYNC"
else:
    # MANUAL LOGIC (Bridge)
    curr_p = manual_price if override else 85220.0
    is_up = (manual_trend == "Upward")
    is_down = (manual_trend == "Downward")
    rsi = 50.0 # Neutral default
    mode_label = "🕹️ MANUAL BRIDGE"

# --- 6. EXECUTION DISPLAY ---
st.divider()

if is_up:
    sig, color, side = "STRONG BUY", "#2ecc71", "CALL (CE)"
elif is_down:
    sig, color, side = "STRONG SELL", "#e74c3c", "PUT (PE)"
else:
    sig, color, side = "NEUTRAL / WAIT", "#fbc531", "CASH"

st.markdown(f"""
    <div style="background-color:{color}22; border:5px solid {color}; padding:40px; border-radius:15px; text-align:center;">
        <p style="color:{color}; font-weight:bold; letter-spacing:2px;">{mode_label}</p>
        <h1 style="color:white; font-size:55px; margin:10px 0;">{sig}: {side}</h1>
        <p style="color:#aaa;">Targeting ATM Strike: {int(round(curr_p/100)*100)}</p>
    </div>
""", unsafe_allow_html=True)

# METRICS
m1, m2, m3 = st.columns(3)
m1.metric("Current Spot", f"{curr_p:,.2f}")
m2.metric("Target Strike", f"{int(round(curr_p/100)*100)}")
m3.metric("System Health", status)