import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. THE PERCEPTION PULSE ---
# Keeps the tower alive and scanning every 60 seconds
st_autorefresh(interval=60 * 1000, key="gridx_pulse")

# --- 2. CONFIGURATION & COGNITION ---
st.set_page_config(page_title="Grid-x 2.0 Tower", layout="wide", page_icon="🛰️")

def calculate_synthetic_greeks(S, K, T, r, sigma):
    """Synthetic Engine for confidence intervals."""
    if T <= 0: return 0, 0
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    delta = norm.cdf(d1)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    return round(delta, 2), round(gamma, 5)

# --- 3. THE CONTROL TOWER UI ---
st.title("🛰️ Grid-x 2.0: Agentic Control Tower")
st.caption(f"Status: **Monitoring Live** | Last Sync: {datetime.datetime.now().strftime('%H:%M:%S')}")

with st.sidebar:
    st.header("🎯 Mission Parameters")
    target = st.text_input("NSE Symbol (e.g., TCS, RELIANCE)", "TCS").upper()
    st.divider()
    st.info("Agentic Logic: Auto-refreshing every 60s. Calculating Synthetic Greeks for Decision Support.")

# --- 4. DATA INGESTION ---
ticker_sym = f"{target}.NS"
ticker = yf.Ticker(ticker_sym)

try:
    # Capturing 1-minute interval data for live momentum
    hist = ticker.history(period="1d", interval="1m")
    
    if not hist.empty:
        price = hist['Close'].iloc[-1]
        day_open = hist['Open'].iloc[0]
        vola = hist['Close'].pct_change().std() * np.sqrt(252 * 375) # Real-time vol proxy
        
        # 🏯 P&L WAR ROOM (Top Metrics)
        m1, m2, m3 = st.columns(3)
        m1.metric("Live Spot", f"₹{price:.2f}", f"{price - day_open:.2f}")
        m2.metric("Intraday Vol", f"{vola:.2f}%")
        
        # COGNITION: REGIME DETECTION
        pivot = (hist['High'].max() + hist['Low'].min() + price) / 3
        bias = "BULLISH (Long Grid)" if price > pivot else "BEARISH (Hedged Short)"
        m3.metric("Agentic Bias", bias)

        # 📊 PREDICTIVE ACTION GRID
        st.subheader("🔮 Predictive Analytics Grid (7-Day Expiry Simulation)")
        
        # Generate strikes around spot
        strikes = [round(price * (1 + x), -1) for x in [-0.02, -0.01, 0, 0.01, 0.02]]
        grid_data = []
        for k in strikes:
            d, g = calculate_synthetic_greeks(price, k, 7/365, 0.07, 0.20)
            grid_data.append({
                "Strike": k, 
                "Delta (Prob)": d, 
                "Gamma (Accel)": g,
                "Action": "BUY/SUPPORT" if k < price else "SELL/RESIST"
            })
        
        st.table(pd.DataFrame(grid_data))

        # ⚡ EXECUTION PATH
        st.subheader("⚡ Strategy Execution Logic")
        col_exec1, col_exec2 = st.columns(2)
        with col_exec1:
            st.success(f"**Target Exit (R1):** ₹{hist['High'].max():.2f}")
        with col_exec2:
            st.error(f"**Safety Exit (S1):** ₹{hist['Low'].min():.2f}")
            
    else:
        st.warning("Establishing Satellite Link... Please wait for market data.")
        
except Exception as e:
    st.error(f"Connection Lost: {e}")

st.divider()
st.caption("Grid-x 2.0: Predictive Market Architecture | Using Synthetic Perception for Restricted APIs")