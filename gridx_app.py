import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Agentic Tower", layout="wide")
st_autorefresh(interval=120 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE (With Ticker Guard) ---
@st.cache_data(ttl=120)
def fetch_tower_data(ticker_sym):
    try:
        tickers = [ticker_sym, "^INDIAVIX"]
        data = yf.download(tickers, period="1d", interval="1m", progress=False, auto_adjust=True, multi_level_index=False)
        # Check if the dataframe is empty or doesn't contain the requested ticker
        if data.empty or ticker_sym not in data.columns.get_level_values(0) if isinstance(data.columns, pd.MultiIndex) else ticker_sym not in data.columns:
            return None
        return data
    except:
        return None

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

# --- 3. UI RENDERER ---
st.sidebar.title("🛡️ Safety Pilot")
target_input = st.sidebar.text_input("Asset Symbol (e.g. TCS, RELIANCE, NIFTY)", "TCS").upper().strip()

# Resolve mapping for Indian Indices
mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    all_data = fetch_tower_data(ticker_sym)

    # 🛑 Ticker Guard Logic
    if all_data is None or all_data.empty or ticker_sym not in all_data.columns:
        st.error(f"⚠️ Symbol '{target_input}' Not Traded or Invalid.")
        st.info("Tip: For Indian stocks, just type the name (e.g., INFY). For US stocks, use the full ticker (e.g., AAPL).")
    else:
        # Extract Data
        closes = all_data['Close'][ticker_sym].dropna()
        volumes = all_data['Volume'][ticker_sym].dropna()
        vix_series = all_data['Close'].get('^INDIAVIX', pd.Series([15.0]))
        vix = float(vix_series.dropna().iloc[-1]) if not vix_series.empty else 15.0
        
        curr_p = float(closes.iloc[-1])
        vwap = float((closes * volumes).sum() / volumes.sum())
        current_rsi = float(calculate_rsi(closes).iloc[-1])
        
        # --- PILLAR: SIGNAL QUALITY FILTERS ---
        buffer = vwap * 0.001 
        is_bullish = curr_p > (vwap + buffer) and 45 < current_rsi < 65
        is_bearish = curr_p < (vwap - buffer) and 35 < current_rsi < 55
        
        interval = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
        atm_strike = int(round(curr_p / interval) * interval)

        st.title(f"🛰️ Grid-x 2.0: {target_input}")

        # --- DYNAMIC SIGNAL BANNER ---
        if is_bullish:
            action, color, reason_list = f"🟢 BUY {atm_strike} CE", "green", [
                f"Price (₹{curr_p:.2f}) is trending above Institutional Fair Value (VWAP: ₹{vwap:.2f}).",
                f"RSI is at {current_rsi:.1f}, confirming strength without overextension.",
                "Institutional momentum suggests buyers are in control."
            ]
        elif is_bearish:
            action, color, reason_list = f"🔴 BUY {atm_strike} PE", "red", [
                f"Price (₹{curr_p:.2f}) has slipped below the VWAP floor.",
                f"RSI at {current_rsi:.1f} shows bearish pressure building.",
                "Market sentiment favors the downside at this level."
            ]
        else:
            action, color, reason_list = "🟡 MONITORING / NO TRADE", "orange", [
                "Price is currently inside the 'Chop Zone' (too close to VWAP).",
                f"RSI at {current_rsi:.1f} is neutral/weak.",
                "Waiting for price to break away from Fair Value with volume."
            ]

        st.markdown(f"""<div style="background-color:{color}22; padding:20px; border-radius:12px; border:2px solid {color}; text-align:center;">
            <h1 style="color:{color}; margin:0;">{action}</h1></div>""", unsafe_allow_html=True)

        # --- THE REASONING BOX ---
        st.write("")
        st.markdown(f"""
        <div style="background-color:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border-left: 5px solid {color};">
            <h4 style="margin-top:0;">🧠 Agentic Reasoning (How I Predicted This)</h4>
            <ul style="margin-bottom:0; font-size:1.1rem;">
                <li>{reason_list[0]}</li>
                <li>{reason_list[1]}</li>
                <li>{reason_list[2]}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # --- METRIC ROW ---
        st.write("")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("VWAP (Fair)", f"₹{vwap:.2f}", f"{curr_p - vwap:.2f}")
        m3.metric("RSI (14m)", f"{current_rsi:.1f}")
        m4.metric("India VIX", f"{vix:.2f}")

except Exception as e:
    st.info("📡 Scanning Satellite Feed... Please check ticker symbol.")

st.divider()
st.caption(f"Sync: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Architecture")