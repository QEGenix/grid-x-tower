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

# --- 2. DATA SATELLITE WITH SAFETY CHECK ---
def get_market_data():
    try:
        # Increase period to '5d' to ensure we have data if today is a holiday
        df = yf.download("^BSESN", period="5d", interval="5m", progress=False)
        vix_df = yf.download("^INDIAVIX", period="5d", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 12.5
        return df, vix
    except Exception as e:
        return None, 12.5

# --- 3. EXECUTION ENGINE ---
st.title("🛰️ QE Genix: Sensex Specialist")
df, vix = get_market_data()

# SAFETY GUARD: Check if dataframe is empty before indexing
if df is not None and not df.empty:
    close = df['Close']
    curr_p = float(close.iloc[-1]) # Now safe because we checked not df.empty
    zlma = ta.zlma(close, length=20).iloc[-1]
    rsi = ta.rsi(close, length=14).iloc[-1]
    
    # ... [Rest of your Probability Logic from v5.1] ...
    score = 0
    is_bull = (close.iloc[-1] > zlma) and (len(close) > 1 and close.iloc[-2] > zlma)
    is_bear = (close.iloc[-1] < zlma) and (len(close) > 1 and close.iloc[-2] < zlma)
    if is_bull or is_bear: score += 50
    if (rsi > 55) or (rsi < 45): score += 30
    if vix < 16: score += 10

    # UI: PROBABILITY DIAL
    dial_color = "#00FF41" if score >= 75 else "#444444"
    st.markdown(f'<div style="border: 2px solid {dial_color}; padding: 15px; border-radius: 50px; text-align: center;">'
                f'<h2 style="color: {dial_color};">CONFLUENCE PROBABILITY: {score}%</h2></div>', unsafe_allow_html=True)

    # UI: VITALS
    st.write("---")
    v1, v2, v3 = st.columns(3)
    v1.metric("INDIA VIX", f"{vix:.2f}")
    v2.metric("SENSEX SPOT", f"{curr_p:,.0f}")
    v3.metric("RSI (14)", f"{rsi:.1f}")

else:
    # This message appears instead of the IndexError crash
    st.warning("📡 DATA LINK STANDBY: Market data is currently unavailable.")
    st.info("Since today is January 1st, the market is closed or the API is refreshing. The dashboard will automatically update once the first 5m candle is detected.")