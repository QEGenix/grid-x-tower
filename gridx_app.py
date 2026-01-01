import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG ---
st.set_page_config(page_title="QE Genix: Apex Sniper", layout="wide")
st_autorefresh(interval=30 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"

# --- 2. APEX DATA SATELLITE ---
def fetch_apex_data():
    try:
        # Standard 2026 User-Agent
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        session = requests.Session()
        session.headers.update(headers)
        
        # We fetch 2 days to ensure indicator continuity
        df = yf.download(SENSEX_TICKER, period="2d", interval="5m", progress=False, session=session)
        
        if df.empty: return None
        
        # CRITICAL FIX: Flatten Multi-Index columns (the '2026 ghost' error)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        return df
    except Exception as e:
        return None

# --- 3. UI: COMMAND CENTER ---
st.title("🛰️ QE Genix: Apex Prediction Engine")
st.caption("v4.4 - Multi-Index Hardened | Jan 1, 2026 Live Status")

data = fetch_apex_data()

if data is not None:
    # DATA PROCESSING
    close = data['Close']
    curr_p = float(close.iloc[-1])
    
    # INDICATORS (Zero-Lag + RSI)
    zlma = ta.zlma(close, length=20)
    rsi = ta.rsi(close, length=14).iloc[-1]
    
    # TREND CONFIRMATION (Sticky Logic)
    # Must be above trend for 2 candles (10 mins) to prevent flipping
    is_up = (close.iloc[-1] > zlma.iloc[-1]) and (close.iloc[-2] > zlma.iloc[-2]) and (rsi > 52)
    is_down = (close.iloc[-1] < zlma.iloc[-1]) and (close.iloc[-2] < zlma.iloc[-2]) and (rsi < 48)

    # ACTION BOX
    st.divider()
    if is_up:
        sig, color, side = "STRONG BUY", "#2ecc71", "CALL (CE)"
    elif is_down:
        sig, color, side = "STRONG SELL", "#e74c3c", "PUT (PE)"
    else:
        sig, color, side = "NEUTRAL / HOLD", "#fbc531", "CASH"

    st.markdown(f"""
        <div style="background-color:{color}22; border:5px solid {color}; padding:40px; border-radius:15px; text-align:center;">
            <p style="color:{color}; font-weight:bold; letter-spacing:2px;">DIRECTIONAL BIAS</p>
            <h1 style="color:white; font-size:55px; margin:10px 0;">{sig}: {side}</h1>
            <p style="color:#aaa;">Confirmed on 5m Trend-Lock Protocol</p>
        </div>
    """, unsafe_allow_html=True)

    # TRADE TICKET
    atm = int(round(curr_p / 100) * 100)
    col1, col2, col3 = st.columns(3)
    col1.metric("Sensex Spot", f"{curr_p:,.2f}")
    col2.metric("Target Strike", f"{atm}")
    col3.metric("RSI Momentum", f"{rsi:.1f}")
    
else:
    st.error("📡 Satellite Link Interrupted.")
    st.info("Yahoo Finance is blocking the session. Trying to bypass...")