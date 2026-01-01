import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time
import random
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG ---
st.set_page_config(page_title="QE Genix: Stealth Sniper", layout="wide")
# Slowing down the heartbeat to 90 seconds to avoid being banned again
st_autorefresh(interval=90 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"

# --- 2. STEALTH DATA SATELLITE ---
def fetch_stealth_data():
    # List of various browsers to rotate identity
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    ]
    
    try:
        # Create a new session for every fetch to clear cookies
        session = yf.utils.get_tld_auth_handler().get_session()
        session.headers.update({'User-Agent': random.choice(agents)})
        
        # Adding a small random sleep to mimic human behavior
        time.sleep(random.uniform(1, 3))
        
        df = yf.download(SENSEX_TICKER, period="5d", interval="5m", progress=False, session=session)
        
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        return df
    except Exception:
        return None

# --- 3. UI: COMMAND CENTER ---
st.title("🛰️ QE Genix: Stealth Sniper v4.5")
st.caption("Status: Rate-Limit Avoidance Active | Interval: 90s")

data = fetch_stealth_data()

if data is not None:
    close = data['Close']
    curr_p = float(close.iloc[-1])
    
    # STICKY LOGIC (The "Decision Lock")
    zlma = ta.zlma(close, length=20)
    rsi = ta.rsi(close, length=14).iloc[-1]
    
    # Must hold for 2 candles (10 mins) + RSI Confirmation
    is_up = (close.iloc[-1] > zlma.iloc[-1]) and (close.iloc[-2] > zlma.iloc[-2]) and (rsi > 55)
    is_down = (close.iloc[-1] < zlma.iloc[-1]) and (close.iloc[-2] < zlma.iloc[-2]) and (rsi < 45)

    st.divider()
    if is_up:
        sig, color = "STRONG BUY (CE)", "#2ecc71"
    elif is_down:
        sig, color = "STRONG SELL (PE)", "#e74c3c"
    else:
        sig, color = "NEUTRAL (WAIT)", "#fbc531"

    st.markdown(f"""
        <div style="background-color:{color}22; border:5px solid {color}; padding:40px; border-radius:15px; text-align:center;">
            <h1 style="color:white; font-size:50px;">{sig}</h1>
            <p style="color:#aaa;">Target: SENSEX {int(round(curr_p/100)*100)} Strike</p>
        </div>
    """, unsafe_allow_html=True)

    # VITALS
    col1, col2 = st.columns(2)
    col1.metric("Sensex Spot", f"{curr_p:,.2f}")
    col2.metric("RSI Momentum", f"{rsi:.1f}")

else:
    st.error("🛑 SATELLITE BLOCKED: Yahoo Finance is still rate-limiting your IP.")
    st.info("Wait 5-10 minutes without refreshing. The engine will auto-reconnect once the block expires.")