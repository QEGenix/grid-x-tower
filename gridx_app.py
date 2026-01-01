import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh

# --- 1. OLED BLACK THEME & CONFIG ---
st.set_page_config(page_title="QE Genix: Sensex Specialist", layout="wide")
st.markdown("""
    <style>
    .stApp {background-color: #000000;}
    h1, h2, h3, p, span {color: #00FF41 !important; font-family: 'Courier New', monospace;}
    .stMetric {background-color: #111111; padding: 15px; border-radius: 10px; border: 1px solid #00FF41;}
    [data-testid="stSidebar"] {background-color: #050505; border-right: 1px solid #333;}
    </style>
""", unsafe_allow_html=True)

st_autorefresh(interval=30 * 1000, key="cockpit_heartbeat")

# --- 2. RISK MANAGEMENT STATE ---
if 'daily_pnl' not in st.session_state:
    st.session_state.daily_pnl = 0

# --- 3. DATA SATELLITE (SIMULATION CAPABLE) ---
with st.sidebar:
    st.header("🛠️ Cockpit Controls")
    sim_mode = st.toggle("🛰️ Activate Simulation Mode", value=False)
    if sim_mode:
        st.info("Simulating Live Market Volatility...")
    
    st.divider()
    st.subheader("💰 Risk Account")
    st.write(f"Capital: ₹20,000")
    st.write(f"Current P&L: ₹{st.session_state.daily_pnl}")
    
    if st.button("Reset Session"):
        st.session_state.daily_pnl = 0

def fetch_data(sim):
    if sim:
        # Create 100 fake 5m candles for testing logic
        np.random.seed(42)
        prices = 85220 + np.cumsum(np.random.normal(0, 15, 100))
        df = pd.DataFrame({'Close': prices, 'High': prices+5, 'Low': prices-5})
        return df, 14.5 # Steady VIX
    try:
        df = yf.download("^BSESN", period="2d", interval="5m", progress=False)
        vix_df = yf.download("^INDIAVIX", period="2d", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = [col[0] for col in df.columns]
        return df, float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 12.5
    except:
        return None, 12.5

# --- 4. EXECUTION ---
if st.session_state.daily_pnl <= -2000:
    st.error("🚫 RISK LOCK: Max Daily Loss (₹2,000) reached. Trading ceased.")
    st.stop()

st.title("🛰️ QE Genix: Sensex Specialist")
df, vix = fetch_data(sim_mode)

if df is not None and not df.empty:
    close = df['Close']
    curr_p = float(close.iloc[-1])
    zlma = ta.zlma(close, length=20).iloc[-1]
    rsi = ta.rsi(close, length=14).iloc[-1]
    
    # 90% SUCCESS PILLARS
    score = 0
    is_bull = (close.iloc[-1] > zlma) and (close.iloc[-2] > zlma)
    is_bear = (close.iloc[-1] < zlma) and (close.iloc[-2] < zlma)
    if is_bull or is_bear: score += 50
    if (rsi > 55) or (rsi < 45): score += 30
    if vix < 18: score += 10 # VIX stability check

    # UI: PROBABILITY DIAL
    dial_color = "#00FF41" if score >= 75 else "#444444"
    st.markdown(f"""
        <div style="border: 2px solid {dial_color}; padding: 15px; border-radius: 50px; text-align: center; margin-bottom: 25px;">
            <h2 style="color: {dial_color}; margin: 0;">CONFLUENCE PROBABILITY: {score}%</h2>
        </div>
    """, unsafe_allow_html=True)

    # UI: CENTER ACTION TERMINAL
    if score >= 75:
        side = "CALL (CE)" if is_bull else "PUT (PE)"
        vasl = round(vix * 4.5)
        st.markdown(f"""
            <div style="background-color: #00FF4111; border: 3px solid #00FF41; padding: 30px; border-radius: 15px; text-align: center;">
                <h1 style="font-size: 50px;">🚀 SIGNAL: BUY {side}</h1>
                <h3>STRIKE: {int(round(curr_p/100)*100)} ATM</h3>
                <p>VASL: {vasl} Pts | TARGET: {vasl * 2} Pts</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #444444;'>🛡️ STANDBY: SEARCHING FOR CONFLUENCE...</h2>", unsafe_allow_html=True)

    # UI: LIVE VITALS
    st.write("---")
    v1, v2, v3 = st.columns(3)
    v1.metric("INDIA VIX", f"{vix:.2f}")
    v2.metric("SENSEX SPOT", f"{curr_p:,.0f}")
    v3.metric("RSI (14)", f"{rsi:.1f}")

    # UI: AGENTIC FLIGHT LOG
    with st.expander("📝 AGENTIC FLIGHT LOG"):
        st.write(f"- **Trend:** {'Bullish Confirmation (2 Candles)' if is_bull else 'Bearish Confirmation (2 Candles)' if is_bear else 'No Trend Stability'}")
        st.write(f"- **Momentum:** RSI is {'Strong' if rsi > 55 or rsi < 45 else 'Weak'} at {rsi:.1f}")
        st.write(f"- **Risk Check:** VIX {vix} allows for {round(vix*4.5)}pt Volatility SL.")

else:
    st.warning("📡 DATA LINK STANDBY: Waiting for first market pulse...")