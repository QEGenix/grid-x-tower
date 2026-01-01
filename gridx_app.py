import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & SETTINGS ---
st.set_page_config(page_title="QE Genix: Capital Guardian", layout="wide")
st_autorefresh(interval=45 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"
PREV_CLOSE = 85220.60  # Fixed for Jan 1, 2026
LOT_SIZE = 10          # Sensex Lot Size

# --- 2. THE HYBRID SATELLITE ---
@st.cache_data(ttl=30)
def fetch_market_state():
    try:
        df = yf.download(SENSEX_TICKER, period="2d", interval="5m", progress=False)
        if df.empty: return None, "Rate Limited"
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        return df, "Live"
    except:
        return None, "Offline"

# --- 3. UI: TOP BAR ---
st.title("🛰️ QE Genix: Sensex Capital Guardian")
data, status = fetch_market_state()

with st.sidebar:
    st.header("🛠️ Tactical Override")
    manual_mode = st.toggle("Enable Manual Bridge", value=(status != "Live"))
    if manual_mode:
        m_price = st.number_input("Broker Price (Spot):", value=85193.0)
        m_trend = st.selectbox("Current Trend:", ["Bullish Momentum", "Bearish Pressure", "Chop"])

# --- 4. ENGINE LOGIC ---
if not manual_mode and data is not None:
    curr_p = float(data['Close'].iloc[-1])
    label = "📡 SATELLITE SYNC"
    # Trend Logic
    zlma = ta.zlma(data['Close'], length=20).iloc[-1]
    is_up = (curr_p > zlma)
    is_down = (curr_p < zlma)
else:
    curr_p = m_price if manual_mode else 85193.0
    label = "🕹️ MANUAL BRIDGE"
    is_up = (m_trend == "Bullish Momentum")
    is_down = (m_trend == "Bearish Pressure")

# --- 5. DASHBOARD ---
st.divider()
color = "#2ecc71" if is_up else ("#e74c3c" if is_down else "#fbc531")
change = curr_p - PREV_CLOSE

col_main, col_metrics = st.columns([2, 1])

with col_main:
    st.markdown(f"""
        <div style="background-color:{color}22; border:4px solid {color}; padding:30px; border-radius:15px; text-align:center;">
            <p style="color:{color}; font-weight:bold;">{label}</p>
            <h1 style="color:white; font-size:45px;">{'BUY CALL (CE)' if is_up else 'BUY PUT (PE)' if is_down else 'WAIT'}</h1>
            <p style="color:#aaa;">Targeting ATM Strike: {int(round(curr_p/100)*100)}</p>
        </div>
    """, unsafe_allow_html=True)

with col_metrics:
    st.metric("Sensex Spot", f"{curr_p:,.2f}", f"{change:,.2f} ({change/PREV_CLOSE:.2%})")
    st.metric("Prev. Close", f"{PREV_CLOSE:,.2f}")

# --- 6. TACTICAL LADDER & PREMIUMS ---
st.subheader("🎯 Strike Ladder & Risk Calculator (Budget: ₹20,000)")
atm = int(round(curr_p / 100) * 100)

# Estimate Premiums (Simplified based on distance from spot)
def est_premium(strike, spot, is_ce):
    intrinsic = max(0, spot - strike) if is_ce else max(0, strike - spot)
    extrinsic = 180 # Average time value for Jan 1 expiry
    return int(intrinsic + extrinsic)

ladder = []
for offset in [-200, 0, 200]:
    strike = atm + offset
    ce_p = est_premium(strike, curr_p, True)
    pe_p = est_premium(strike, curr_p, False)
    
    # Capital Check: Can we afford 1 lot (Premium * Lot Size)?
    can_afford_ce = "✅" if (ce_p * LOT_SIZE) <= 20000 else "❌"
    can_afford_pe = "✅" if (pe_p * LOT_SIZE) <= 20000 else "❌"
    
    ladder.append({
        "Strike": strike,
        "CE Premium (Est)": f"₹{ce_p}",
        "CE Affordable": can_afford_ce,
        "PE Premium (Est)": f"₹{pe_p}",
        "PE Affordable": can_afford_pe
    })

st.table(pd.DataFrame(ladder))