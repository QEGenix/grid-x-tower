import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Intelligent Tower", layout="wide")
st_autorefresh(interval=120 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE (Enhanced Error Handling) ---
@st.cache_data(ttl=120)
def fetch_tower_data(ticker_sym):
    try:
        # Fetching tickers individually to prevent one failure from killing the whole batch
        data_stock = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
        data_vix = yf.download("^INDIAVIX", period="1d", interval="1m", progress=False, auto_adjust=True)
        return data_stock, data_vix
    except:
        return None, None

def calculate_rsi(series, window=14):
    if len(series) < window: return 50
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

# --- 3. UI RENDERER ---
st.sidebar.title("🛡️ Safety Pilot")
target_input = st.sidebar.text_input("Asset Symbol", "TCS").upper().strip()

mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    stock_raw, vix_raw = fetch_tower_data(ticker_sym)

    # 🛑 Data Integrity Guard (Fixes Out-of-Bounds Error)
    if stock_raw is None or stock_raw.empty or len(stock_raw) < 2:
        st.warning(f"📡 Waiting for Market Data... Symbol '{target_input}' might be inactive or rate-limited.")
    else:
        # Robust Extraction
        closes = stock_raw['Close'].iloc[:, 0] if isinstance(stock_raw['Close'], pd.DataFrame) else stock_raw['Close']
        volumes = stock_raw['Volume'].iloc[:, 0] if isinstance(stock_raw['Volume'], pd.DataFrame) else stock_raw['Volume']
        
        curr_p = float(closes.iloc[-1])
        vwap = float((closes * volumes).sum() / volumes.sum())
        current_rsi = float(calculate_rsi(closes).iloc[-1])
        
        vix = 15.0 # Default
        if vix_raw is not None and not vix_raw.empty:
            vix_closes = vix_raw['Close'].iloc[:, 0] if isinstance(vix_raw['Close'], pd.DataFrame) else vix_raw['Close']
            if len(vix_closes) > 0: vix = float(vix_closes.iloc[-1])

        # --- SIGNAL FILTERS ---
        diff_pct = ((curr_p - vwap) / vwap) * 100
        is_bullish = diff_pct > 0.15 and 45 < current_rsi < 70
        is_bearish = diff_pct < -0.15 and 30 < current_rsi < 55
        
        interval = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
        atm_strike = int(round(curr_p / interval) * interval)

        st.title(f"🛰️ Grid-x 2.0: {target_input}")

        # --- DYNAMIC SIGNAL BANNER ---
        if is_bullish:
            action, color = f"🟢 BUY {atm_strike} CE", "green"
            m_state = f"Aggressive Momentum: Price is ₹{abs(curr_p - vwap):.2f} above Fair Value."
            m_trend = f"RSI at {current_rsi:.1f} indicates strong bullish breakout with room to grow."
            m_exec = f"Volatility (VIX: {vix:.2f}) is stable. High probability for {atm_strike} Strike."
        elif is_bearish:
            action, color = f"🔴 BUY {atm_strike} PE", "red"
            m_state = f"Heavy Distribution: Price has crashed {abs(diff_pct):.2f}% below VWAP."
            m_trend = f"RSI at {current_rsi:.1f} shows bearish dominance is accelerating."
            m_exec = f"Warning: Downward velocity is high. Monitor {atm_strike} Put premiums."
        else:
            action, color = "🟡 MONITORING / NO TRADE", "orange"
            m_state = f"Range-Bound: Price is drifting only {abs(diff_pct):.2f}% from VWAP (Chop Zone)."
            m_trend = f"RSI is neutral ({current_rsi:.1f}), showing no institutional conviction."
            m_exec = "Execution Lock: Awaiting a decisive break above or below the Fair Value line."

        st.markdown(f"""<div style="background-color:{color}22; padding:20px; border-radius:12px; border:2px solid {color}; text-align:center;">
            <h1 style="color:{color}; margin:0;">{action}</h1></div>""", unsafe_allow_html=True)

        # --- IMPROVISED REASONING BOX ---
        st.write("")
        st.markdown(f"""
        <div style="background-color:rgba(255,255,255,0.05); padding:20px; border-radius:10px; border-left: 8px solid {color};">
            <h4 style="margin-top:0; color:{color};">🧠 Agentic Intelligence Brief</h4>
            <p style="margin-bottom:8px;"><b>1. Market State:</b> {m_state}</p>
            <p style="margin-bottom:8px;"><b>2. Momentum Analysis:</b> {m_trend}</p>
            <p style="margin-bottom:0;"><b>3. Strategy Instruction:</b> {m_exec}</p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("VWAP (Fair)", f"₹{vwap:.2f}", f"{diff_pct:.2f}%")
        m3.metric("RSI (14m)", f"{current_rsi:.1f}")
        m4.metric("India VIX", f"{vix:.2f}")

except Exception as e:
    st.info("📡 Scanning Satellite Feed... Ensure ticker symbol is correct.")

st.divider()
st.caption(f"Sync: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Master Tower")