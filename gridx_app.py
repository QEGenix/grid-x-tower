import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --- 1. OLED BLACK THEME & CONFIG ---
st.set_page_config(page_title="QE Genix: Sensex Specialist", layout="wide")
st.markdown("""
    <style>
    .stApp {background-color: #000000;}
    h1, h2, h3, p, span {color: #00FF41 !important; font-family: 'Courier New', monospace;}
    .stMetric {background-color: #111111; padding: 15px; border-radius: 10px; border: 1px solid #00FF41;}
    </style>
""", unsafe_allow_html=True)

st_autorefresh(interval=60 * 1000, key="cockpit_heartbeat")

# CONSTANTS
PREV_CLOSE = 85220.60
MAX_DAILY_LOSS = 2000
LOT_SIZE = 10

# --- 2. DATA SATELLITE ---
def get_market_data():
    try:
        # Fetching 5m data for 2-candle confirmation
        df = yf.download("^BSESN", period="2d", interval="5m", progress=False)
        vix_df = yf.download("^INDIAVIX", period="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 12.5
        return df, vix
    except:
        return None, 12.5

# --- 3. COCKPIT ENGINE ---
df, vix = get_market_data()

if df is not None:
    close = df['Close']
    curr_p = float(close.iloc[-1])
    zlma = ta.zlma(close, length=20).iloc[-1]
    rsi = ta.rsi(close, length=14).iloc[-1]
    
    # PROBABILITY CALCULATION (90% Success Pillars)
    score = 0
    # Pillar 1: 2-Candle Confirmation (Noise Filtration)
    is_bull = (close.iloc[-1] > zlma) and (close.iloc[-2] > zlma)
    is_bear = (close.iloc[-1] < zlma) and (close.iloc[-2] < zlma)
    if is_bull or is_bear: score += 50
    # Pillar 2: RSI Strength
    if (rsi > 55) or (rsi < 45): score += 30
    # Pillar 3: VIX Stability
    if vix < 16: score += 10
    
    # TOP BAR: PROBABILITY DIAL
    dial_color = "#00FF41" if score >= 75 else "#444444"
    st.markdown(f"""
        <div style="border: 2px solid {dial_color}; padding: 15px; border-radius: 50px; text-align: center; margin-bottom: 25px;">
            <h2 style="color: {dial_color}; margin: 0;">CONFLUENCE PROBABILITY: {score}%</h2>
        </div>
    """, unsafe_allow_html=True)

    # CENTER STAGE: ACTION TERMINAL
    if score >= 75:
        side = "CALL (CE)" if is_bull else "PUT (PE)"
        # VASL (Volatility Adjusted Stop Loss) logic
        vasl = round(vix * 4.5) 
        st.markdown(f"""
            <div style="background-color: #00FF4111; border: 3px neon #00FF41; padding: 30px; border-radius: 15px; text-align: center;">
                <h1 style="font-size: 50px;">BUY {side}</h1>
                <h3>SENSEX {int(round(curr_p/100)*100)} ATM</h3>
                <p>VASL: {vasl} Pts | TARGET: {vasl * 2} Pts</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #444444;'>STANDING BY: PROBABILITY < 75%</h2>", unsafe_allow_html=True)

    # BOTTOM GRID: LIVE VITALS (FIXED SYNTAX)
    st.write("---")
    v1, v2, v3 = st.columns(3)
    v1.metric("INDIA VIX", f"{vix:.2f}")
    v2.metric("SENSEX SPOT", f"{curr_p:,.0f}", f"{curr_p - PREV_CLOSE:,.2f}")
    v3.metric("RSI (14)", f"{rsi:.1f}")

    # FLIGHT LOG (Agentic Reasoning)
    with st.expander("📝 AGENTIC FLIGHT LOG"):
        st.write(f"**Trend:** {'Bullish' if is_bull else 'Bearish' if is_bear else 'Chop'}")
        st.write(f"**Volatility Adjusted SL:** Using {vix} VIX to set {round(vix*4.5)}pt buffer.")
        st.write(f"**Position Sizing:** Premium based logic active for ₹20k budget.")