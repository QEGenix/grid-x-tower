import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Agentic Tower", layout="wide")
st_autorefresh(interval=120 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE (Cached) ---
@st.cache_data(ttl=120)
def fetch_tower_data(ticker_sym):
    try:
        tickers = [ticker_sym, "^INDIAVIX"]
        data = yf.download(tickers, period="1d", interval="1m", progress=False, auto_adjust=True, multi_level_index=False)
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
try:
    st.sidebar.title("🛡️ Safety Pilot")
    target_input = st.sidebar.text_input("Asset Symbol", "TCS").upper()
    ticker_sym = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}.get(target_input, f"{target_input}.NS")
    
    all_data = fetch_tower_data(ticker_sym)

    if all_data is not None and not all_data.empty:
        closes = all_data['Close'][ticker_sym].dropna()
        volumes = all_data['Volume'][ticker_sym].dropna()
        vix = float(all_data['Close']['^INDIAVIX'].dropna().iloc[-1])
        
        curr_p = float(closes.iloc[-1])
        vwap = float((closes * volumes).sum() / volumes.sum())
        current_rsi = float(calculate_rsi(closes).iloc[-1])
        
        # --- PILLAR: SIGNAL QUALITY FILTERS ---
        # We only Buy if price is significantly above VWAP (0.1% buffer)
        buffer = vwap * 0.001 
        is_bullish = curr_p > (vwap + buffer) and 45 < current_rsi < 65
        is_bearish = curr_p < (vwap - buffer) and 35 < current_rsi < 55
        
        # Strike & Logic
        interval = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
        atm_strike = int(round(curr_p / interval) * interval)

        st.title(f"🛰️ Grid-x 2.0: {target_input}")

        # --- DYNAMIC SIGNAL BANNER ---
        if is_bullish:
            action, color, reason_list = f"🟢 BUY {atm_strike} CE", "green", [
                f"Price (₹{curr_p:.2f}) is trending above the Institutional VWAP (₹{vwap:.2f}).",
                f"RSI is at {current_rsi:.1f}, showing healthy momentum without being overbought.",
                "Institutional Bias (PCR) is supportive of an upside move."
            ]
        elif is_bearish:
            action, color, reason_list = f"🔴 BUY {atm_strike} PE", "red", [
                f"Price (₹{curr_p:.2f}) has broken below the Fair Value Floor (VWAP).",
                f"RSI at {current_rsi:.1f} indicates bearish pressure is increasing.",
                "Market volatility (VIX) and volume suggest further downside risk."
            ]
        else:
            action, color, reason_list = "🟡 MONITORING / NO TRADE", "orange", [
                "Price is too close to the VWAP (Inside the 'No-Trade' chop zone).",
                f"RSI at {current_rsi:.1f} is neutral, suggesting a lack of clear direction.",
                "The system is waiting for institutional volume to confirm the next move."
            ]

        st.markdown(f"""<div style="background-color:{color}22; padding:20px; border-radius:12px; border:2px solid {color}; text-align:center;">
            <h1 style="color:{color}; margin:0;">{action}</h1></div>""", unsafe_allow_html=True)

        # --- THE REASONING BOX ---
        st.write("")
        with st.container():
            st.markdown(f"""
            <div style="background-color:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border-left: 5px solid {color};">
                <h4 style="margin-top:0;">🧠 Agentic Reasoning (How I Predicted This)</h4>
                <ul style="margin-bottom:0;">
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

        st.line_chart(pd.DataFrame({'Price': closes, 'VWAP': vwap}))

except Exception as e:
    st.error(f"Tower Logic Error: {e}")