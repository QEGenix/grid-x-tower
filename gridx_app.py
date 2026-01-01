import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. OLED BLACK THEME & CONFIG ---
st.set_page_config(page_title="QE Genix: Sensex Specialist", layout="wide")
st.markdown("<style>body {background-color: #000000; color: #00FF41;}</style>", unsafe_allow_html=True)
st_autorefresh(interval=60 * 1000, key="cockpit_heartbeat")

# CONSTANTS
CAPITAL = 20000
MAX_DAILY_LOSS = 2000
LOT_SIZE = 10

# --- 2. DATA SATELLITE (Refined for Jan 1, 2026) ---
def get_cockpit_data():
    try:
        df = yf.download("^BSESN", period="2d", interval="5m", progress=False)
        vix = yf.download("^INDIAVIX", period="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        return df, float(vix['Close'].iloc[-1]) if not vix.empty else 12.0
    except: return None, 12.0

# --- 3. THE PROBABILITY ENGINE ---
def calculate_probability(df, vix):
    close = df['Close']
    zlma = ta.zlma(close, length=20)
    rsi = ta.rsi(close, length=14).iloc[-1]
    
    score = 0
    # Pillar 1: Trend Confirmation (2 Consecutive candles)
    if (close.iloc[-1] > zlma.iloc[-1]) and (close.iloc[-2] > zlma.iloc[-2]): score += 40
    elif (close.iloc[-1] < zlma.iloc[-1]) and (close.iloc[-2] < zlma.iloc[-2]): score += 40
    
    # Pillar 2: Momentum (RSI)
    if rsi > 60 or rsi < 40: score += 30
    
    # Pillar 3: Volatility (VIX Cooling/Stable)
    if vix < 18: score += 30
    
    return score, rsi, zlma.iloc[-1]

# --- 4. THE COCKPIT UI ---
st.title("🛰️ QE Genix: Sensex Specialist")
df, vix_val = get_cockpit_data()

if df is not None:
    prob, rsi_val, trend_line = calculate_probability(df, vix_val)
    curr_p = float(df['Close'].iloc[-1])
    
    # TOP BAR: PROBABILITY DIAL
    dial_color = "#00FF41" if prob >= 75 else "#555555" # Neon Green vs Gray
    st.markdown(f"""
        <div style="border: 2px solid {dial_color}; padding: 20px; border-radius: 50px; text-align: center;">
            <h2 style="color: {dial_color};">CONFLUENCE PROBABILITY: {prob}%</h2>
        </div>
    """, unsafe_allow_html=True)

    # CENTER STAGE: ACTION TERMINAL
    st.divider()
    if prob >= 75:
        side = "CALL (CE)" if curr_p > trend_line else "PUT (PE)"
        # VASL (Volatility Adjusted Stop Loss)
        vasl_points = round(vix_val * 4) # Logic: Higher VIX = Wider SL
        
        st.markdown(f"""
            <div style="background-color: #00FF4122; border: 5px solid #00FF41; padding: 40px; border-radius: 20px;">
                <h1 style="color: #00FF41; text-align: center;">🚀 SIGNAL: BUY {side}</h1>
                <h3 style="color: white; text-align: center;">SENSEX {int(round(curr_p/100)*100)} ATM</h3>
                <p style="text-align: center;">SL: {vasl_points} Pts | TGT: {vasl_points * 2} Pts</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background-color: #222222; border: 5px solid #555555; padding: 40px; border-radius: 20px; text-align: center;">
                <h1 style="color: #555555;">🛡️ SYSTEM: SEARCHING...</h1>
                <p>Waiting for 75% Probability Confluence</p>
            </div>
        """, unsafe_allow_html=True)

    # BOTTOM GRID: LIVE VITALS
    st.divider()
    v1, v2, v3 =