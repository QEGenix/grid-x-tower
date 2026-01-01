import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="QE Genix: Command Center", layout="wide")
st_autorefresh(interval=45 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"

# --- 2. THE BULLETPROOF DATA SATELLITE ---
def fetch_robust_data():
    try:
        # Spoofing headers to prevent Yahoo Finance 403/Empty Data errors
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Use period='2d' to ensure we have enough data for indicators on a fresh trading day
        df = yf.download(SENSEX_TICKER, period="2d", interval="5m", progress=False, session=session)
        
        if df.empty or len(df) < 5:
            return None
            
        # Standardizing multi-index columns if they exist
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except Exception as e:
        st.sidebar.error(f"Satellite Error: {e}")
        return None

# --- 3. THE DECISION ENGINE ---
def get_decision(df):
    close = df['Close']
    # Zero-Lag EMA for sticky trend detection
    zlma = ta.zlma(close, length=20)
    # RSI for momentum confirmation
    rsi = ta.rsi(close, length=14)
    
    curr_p = close.iloc[-1]
    curr_zlma = zlma.iloc[-1]
    curr_rsi = rsi.iloc[-1]
    
    # DECISION LOGIC (Sticky: Needs 2-candle confirmation)
    is_bullish = (close.iloc[-1] > curr_zlma) and (close.iloc[-2] > zlma.iloc[-2]) and (curr_rsi > 50)
    is_bearish = (close.iloc[-1] < curr_zlma) and (close.iloc[-2] < zlma.iloc[-2]) and (curr_rsi < 50)
    
    if is_bullish: return "STRONG BUY (CE)", "#2ecc71"
    if is_bearish: return "STRONG SELL (PE)", "#e74c3c"
    return "NEUTRAL / WAIT", "#fbc531"

# --- 4. UI: COCKPIT ---
st.title("🛰️ QE Genix: Stable Prediction Engine")
st.caption("v4.2 - Multi-Path Satellite Sync (2026 Optimized)")

data = fetch_robust_data()

if data is not None:
    signal, signal_color = get_decision(data)
    price = data['Close'].iloc[-1]
    
    # LADDER CALCULATIONS
    atm = int(round(price / 100) * 100)
    
    st.divider()
    
    # BIG ACTION BOX
    st.markdown(f"""
        <div style="background-color:{signal_color}22; border:5px solid {signal_color}; padding:40px; border-radius:20px; text-align:center;">
            <p style="color:{signal_color}; font-weight:bold; letter-spacing:2px;">SATELLITE DECISION</p>
            <h1 style="color:white; font-size:60px; margin:10px 0;">{signal}</h1>
            <p style="color:#aaa;">Target Strike: SENSEX {atm}</p>
        </div>
    """, unsafe_allow_html=True)

    # VITALS
    col1, col2, col3 = st.columns(3)
    col1.metric("Sensex Spot", f"{price:,.2f}")
    col2.metric("Target Strike (ATM)", f"{atm}")
    col3.metric("Trend Strength", "High" if abs(data['Close'].iloc[-1] - data['Close'].iloc[-10]) > 50 else "Low")

else:
    st.warning("📡 Satellite Pulse Weak. Attempting to reconnect via Spoofed Handshake...")
    st.info("The Indian market is OPEN today (Jan 1, 2026), but data providers are lagging. Please wait for the auto-refresh.")