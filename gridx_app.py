import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import pandas_ta as ta
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="QE Genix: Command & Control", layout="wide")
st_autorefresh(interval=30 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"
STRIKE_INTERVAL = 100 # Sensex standard strike gap

# --- 2. DATA SATELLITE ---
@st.cache_data(ttl=20)
def fetch_tactical_data():
    df = yf.download(SENSEX_TICKER, period="1d", interval="1m", progress=False, auto_adjust=True)
    return df

def get_strike_ladder(spot):
    atm = int(round(spot / STRIKE_INTERVAL) * STRIKE_INTERVAL)
    return {
        "ITM_Call": atm - 200, "ATM": atm, "OTM_Call": atm + 200,
        "ITM_Put": atm + 200, "OTM_Put": atm - 200
    }

# --- 3. UI: COMMAND & CONTROL ---
st.title("🛰️ QE Genix: Sensex Tactical Engine")

try:
    data = fetch_tactical_data()
    if not data.empty:
        # DATA Vitals
        curr_p = data['Close'].iloc[-1]
        tema = ta.tema(data['Close'], length=9).iloc[-1]
        rsi = ta.rsi(data['Close'], length=14).iloc[-1]
        atr = ta.atr(data['High'], data['Low'], data['Close'], length=14).iloc[-1]
        
        # LADDER CALCULATION
        ladder = get_strike_ladder(curr_p)
        
        # --- UI ROW 1: THE LADDER ---
        st.subheader("🎯 Strike Selection Ladder")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"**ITM (In-The-Money)**\n\nCall: {ladder['ITM_Call']} | Put: {ladder['ITM_Put']}")
        with c2:
            st.success(f"**ATM (At-The-Money)**\n\nStrike: {ladder['ATM']}")
        with c3:
            st.warning(f"**OTM (Out-Of-The-Money)**\n\nCall: {ladder['OTM_Call']} | Put: {ladder['OTM_Put']}")

        # --- UI ROW 2: TACTICAL EXECUTION ---
        st.divider()
        st.subheader("⚡ Sniper Execution Command")
        
        # STRATEGY LOGIC
        is_bullish = curr_p > tema and rsi > 55
        is_bearish = curr_p < tema and rsi < 45
        
        if is_bullish or is_bearish:
            side = "CALL (CE)" if is_bullish else "PUT (PE)"
            chosen_strike = ladder['ITM_Call'] if is_bullish else ladder['ITM_Put']
            
            st.markdown(f"""
                <div style="background-color:#1e272e; padding:30px; border-radius:15px; border-left: 10px solid {'#2ecc71' if is_bullish else '#e74c3c'};">
                    <h2 style="color:white; margin-bottom:5px;">ACTION: ENTER {side} NOW</h2>
                    <h3 style="color:#d1d8e0;">Strike: SENSEX {chosen_strike}</h3>
                    <hr>
                    <table style="width:100%; color:white; font-size:20px;">
                        <tr>
                            <td><b>ENTRY RANGE:</b> Current Spot ({curr_p:,.2f})</td>
                            <td><b>STOP LOSS:</b> {curr_p - (atr*2) if is_bullish else curr_p + (atr*2):,.2f}</td>
                            <td><b>TARGET:</b> {curr_p + (atr*4) if is_bullish else curr_p - (atr*4):,.2f}</td>
                        </tr>
                    </table>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background-color:#2f3640; padding:30px; border-radius:15px; text-align:center;">
                    <h2 style="color:#fbc531;">HOLD / WAIT</h2>
                    <p style="color:white;">Market is in No-Trade Zone. Signals not aligned.</p>
                </div>
            """, unsafe_allow_html=True)

        # --- UI ROW 3: SATELLITE VITALS ---
        with st.expander("📊 Technical Satellite Vitals (Click to view)"):
            v1, v2, v3 = st.columns(3)
            v1.metric("Current Price", f"{curr_p:,.2f}")
            v2.metric("TEMA (Trend Line)", f"{tema:,.2f}")
            v3.metric("RSI (Momentum)", f"{rsi:.1f}")

except Exception as e:
    st.error(f"Engine Stall: {e}")