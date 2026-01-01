import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from streamlit_autorefresh import st_autorefresh

# --- 1. SAFE BOOT CONFIG ---
st.set_page_config(page_title="QE Genix: Command & Control", layout="wide")
st_autorefresh(interval=30 * 1000, key="sniper_heartbeat")

# CONSTANTS
SENSEX_TICKER = "^BSESN"
STRIKE_INTERVAL = 100

st.title("🛰️ QE Genix: Sensex Tactical Engine")
st.divider()

# --- 2. DATA SATELLITE (WITH ERROR HANDLING) ---
def fetch_data_safely():
    try:
        # Added a timeout to prevent the 'stuck' blank screen
        df = yf.download(SENSEX_TICKER, period="1d", interval="1m", progress=False, auto_adjust=True, timeout=10)
        if df.empty:
            return None, "No data returned from Yahoo Finance."
        return df, None
    except Exception as e:
        return None, str(e)

# --- 3. THE COMMAND CENTER ---
data, error = fetch_data_safely()

if error:
    st.error(f"📡 Satellite Connection Failed: {error}")
    st.info("Check your internet connection or try restarting the app.")
elif data is not None:
    # DATA PROCESSING
    close = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
    curr_p = float(close.iloc[-1])
    
    # CALCULATE LADDER
    atm = int(round(curr_p / STRIKE_INTERVAL) * STRIKE_INTERVAL)
    
    # UI: TACTICAL TILES
    col1, col2, col3 = st.columns(3)
    col1.metric("SENSEX SPOT", f"{curr_p:,.2f}")
    col2.metric("ATM STRIKE", f"{atm}")
    col3.metric("MARKET STATUS", "🟢 OPEN" if datetime.datetime.now().hour < 16 else "🔴 CLOSED")

    # TRADE PLANNER
    st.subheader("⚡ Strategic Instructions")
    
    # Simplified Logic for Immediate Signal
    tema = ta.tema(close, length=9).iloc[-1]
    if curr_p > tema:
        st.success(f"🚀 **ACTION:** BUY SENSEX {atm} CALL (CE)")
        st.write(f"**Target:** {curr_p + 100:,.2f} | **SL:** {curr_p - 50:,.2f}")
    else:
        st.error(f"📉 **ACTION:** BUY SENSEX {atm} PUT (PE)")
        st.write(f"**Target:** {curr_p - 100:,.2f} | **SL:** {curr_p + 50:,.2f}")

else:
    st.warning("⏳ Initializing Satellite... Waiting for first data pulse.")