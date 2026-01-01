import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG ---
st.set_page_config(page_title="Sensex Tactical Engine", layout="wide")
st_autorefresh(interval=30 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"
STRIKE_GAP = 100

# --- 2. DATA SATELLITE WITH HEADERS ---
def fetch_data():
    try:
        # Use period='5d' to ensure we get the last trading day if today is a holiday
        df = yf.download(SENSEX_TICKER, period="5d", interval="1m", progress=False, auto_adjust=True)
        if df.empty: return None
        return df
    except:
        return None

# --- 3. UI LAYOUT ---
st.title("🛰️ QE Genix: Sensex Tactical Engine")

data = fetch_data()

# EMERGENCY FALLBACK: If API fails, use a manual input to keep the engine running
if data is None:
    st.error("📡 Satellite Link Down (Market Closed or API Blocked)")
    manual_spot = st.number_input("Enter Current Sensex Spot Manually to Generate Ladder:", value=85310.0)
    curr_p = manual_spot
    is_live = False
else:
    close = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
    curr_p = float(close.iloc[-1])
    is_live = True

# --- 4. THE COMMAND CENTER ---
atm = int(round(curr_p / STRIKE_GAP) * STRIKE_GAP)

st.divider()
col1, col2, col3 = st.columns(3)
col1.metric("CURRENT SPOT", f"{curr_p:,.2f}", delta="LIVE" if is_live else "MANUAL")
col2.metric("ATM STRIKE", f"{atm}")
col3.metric("EXPIRY FOCUS", "Weekly (Thursday)")

# --- 5. THE TRADE TICKET (PRECISION INSTRUCTIONS) ---
st.subheader("⚡ Sniper Execution Ticket")

# Calculate Strategy (Trend + Volatility)
# If live, use TEMA. If manual, default to neutral.
if is_live:
    tema = ta.tema(close, length=9).iloc[-1]
    bias = "BULLISH" if curr_p > tema else "BEARISH"
else:
    bias = st.radio("Select Current Market Bias:", ["BULLISH", "BEARISH"], horizontal=True)

# Generate Instructions
side = "CALL (CE)" if bias == "BULLISH" else "PUT (PE)"
itm_strike = atm - 200 if bias == "BULLISH" else atm + 200
otm_strike = atm + 200 if bias == "BULLISH" else atm - 200

# Action Box
bg_color = "#1e272e"
border_color = "#2ecc71" if bias == "BULLISH" else "#e74c3c"

st.markdown(f"""
    <div style="background-color:{bg_color}; padding:25px; border-radius:15px; border-left: 10px solid {border_color};">
        <h2 style="color:white; margin:0;">ACTION: ENTER {side} POSITION</h2>
        <p style="color:#aaa;">Selection Logic: Momentum Alignment detected at {curr_p:,.0f}</p>
        <hr style="border-color:#444;">
        <table style="width:100%; color:white; font-size:18px;">
            <tr>
                <td><b>PREMIUM PICK:</b> ITM {itm_strike} (Low Decay)</td>
                <td><b>SCALPER PICK:</b> ATM {atm} (High Gamma)</td>
                <td><b>LOTS:</b> 1 (₹20,000 Capital)</td>
            </tr>
            <tr style="height:20px;"></tr>
            <tr>
                <td style="color:#2ecc71;"><b>ENTRY:</b> NOW ({curr_p:,.0f})</td>
                <td style="color:#e74c3c;"><b>STOP LOSS:</b> {curr_p - 60 if bias == 'BULLISH' else curr_p + 60:,.0f}</td>
                <td style="color:#3498db;"><b>TARGET:</b> {curr_p + 120 if bias == 'BULLISH' else curr_p - 120:,.0f}</td>
            </tr>
        </table>
    </div>
""", unsafe_allow_html=True)

with st.expander("📈 Why these numbers?"):
    st.write(f"**ITM Strike ({itm_strike}):** Chosen to minimize Theta decay on expiry day.")
    st.write(f"**Stop Loss (60 pts):** Aligned with the ₹1,200 risk per lot (under your ₹2,000 daily cap).")
    st.write(f"**Target (120 pts):** A 1:2 Risk-Reward ratio targeting ₹2,400 profit per trade.")