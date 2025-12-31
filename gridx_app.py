import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Master Tower", layout="wide")

# Respecting Yahoo's limits with a 2-minute heartbeat
st_autorefresh(interval=120 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE (Cached) ---
@st.cache_data(ttl=120)
def fetch_tower_data(ticker_sym):
    """Batches requests to prevent RateLimitError."""
    try:
        tickers = [ticker_sym, "^INDIAVIX"]
        # Fetching 1m data for precise VWAP and RSI
        data = yf.download(tickers, period="1d", interval="1m", progress=False, auto_adjust=True, multi_level_index=False)
        return data
    except Exception as e:
        return None

# --- 3. INTELLIGENCE ENGINES ---
def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

# --- 4. UI RENDERER ---
try:
    st.sidebar.title("🛡️ Safety Pilot")
    target_input = st.sidebar.text_input("Asset Symbol", "TCS").upper()
    
    mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
    ticker_sym = mapping.get(target_input, f"{target_input}.NS")
    
    all_data = fetch_tower_data(ticker_sym)

    if all_data is not None and not all_data.empty:
        # Data Extraction
        closes = all_data['Close'][ticker_sym].dropna()
        volumes = all_data['Volume'][ticker_sym].dropna()
        vix_series = all_data['Close']['^INDIAVIX'].dropna()
        
        curr_p = float(closes.iloc[-1])
        current_vix = float(vix_series.iloc[-1])
        current_rsi = float(calculate_rsi(closes).iloc[-1])
        
        # Pillar: VWAP Calculation (Price * Vol / Total Vol)
        vwap = float((closes * volumes).sum() / volumes.sum())
        
        # Strike Logic
        interval = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
        atm_strike = int(round(curr_p / interval) * interval)
        
        st.title(f"🛰️ Grid-x 2.0: {target_input} Tower")

        # --- ACTION BANNER ---
        pcr_val = 1.08 # Placeholder for real OI
        is_bullish = curr_p > vwap and current_rsi < 65
        
        if is_bullish:
            action, color = f"🟢 SIGNAL: BUY {atm_strike} CE", "green"
        elif curr_p < vwap and current_rsi > 35:
            action, color = f"🔴 SIGNAL: BUY {atm_strike} PE", "red"
        else:
            action, color = "🟡 MONITORING: Divergence", "orange"

        st.markdown(f"""<div style="background-color:{color}22; padding:25px; border-radius:12px; border:2px solid {color}; text-align:center;">
            <h1 style="color:{color}; margin:0;">{action}</h1>
            <p style="font-size:1.2rem; margin-top:5px;">Spot: ₹{curr_p:.2f} | Strike: <b>{atm_strike}</b></p></div>""", unsafe_allow_html=True)

        st.write("")
        
        # --- THE UPDATED GRID (With VWAP) ---
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("VWAP (Fair)", f"₹{vwap:.2f}", delta=f"{curr_p - vwap:.2f}")
        m3.metric("PCR (Bias)", f"{pcr_val}", "BULLISH")
        m4.metric("RSI (14m)", f"{current_rsi:.1f}")
        m5.metric("India VIX", f"{current_vix:.2f}")

        # Charts and Analysis
        st.subheader("📊 Momentum & Fair Value Pulse")
        plot_df = pd.DataFrame({'Price': closes, 'VWAP': vwap})
        st.line_chart(plot_df)

except Exception as e:
    st.error(f"Tower Logic Error: {e}")

st.caption(f"Data Source: Yahoo Finance (Cached) | Last Sync: {datetime.datetime.now().strftime('%H:%M:%S')}")