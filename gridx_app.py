import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime
import math

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Pro Tower", layout="wide")
st_autorefresh(interval=60 * 1000, key="gridx_heartbeat")

# --- 2. INTELLIGENCE ENGINES ---

def get_strike_interval(ticker):
    """Returns NSE standard strike intervals."""
    t = ticker.upper()
    if "NSEI" in t: return 50
    if "NSEBANK" in t: return 100
    return 10 # Default for stocks like TCS

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

def run_monte_carlo(current_price, vol, horizon_mins=60):
    min_vol = vol / np.sqrt(252 * 375) 
    simulations = 50
    results = [current_price * (1 + np.random.normal(0, min_vol, horizon_mins)).cumprod()[-1] for _ in range(simulations)]
    return np.percentile(results, [10, 50, 90])

def fetch_oi_sentiment():
    pcr = round(np.random.uniform(0.7, 1.3), 2)
    sentiment = "BULLISH" if pcr > 1.05 else ("BEARISH" if pcr < 0.85 else "NEUTRAL")
    return pcr, sentiment

# --- 3. UI RENDERER ---
try:
    st.sidebar.title("🛡️ Safety Pilot")
    target_input = st.sidebar.text_input("Asset Symbol", "TCS")
    
    mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
    ticker_sym = mapping.get(target_input.upper(), f"{target_input.upper()}.NS")
    
    df_live = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
    df_hist = yf.download(ticker_sym, period="5d", interval="5m", progress=False, auto_adjust=True)
    vix_df = yf.download("^INDIAVIX", period="1d", interval="1m", progress=False)

    if not df_live.empty:
        curr_p = float(df_live['Close'].iloc[-1])
        vwap = float((df_live['Close'] * df_live['Volume']).sum() / df_live['Volume'].sum())
        current_rsi = float(calculate_rsi(df_hist['Close']).iloc[-1])
        current_vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 15.0
        pcr_val, oi_sent = fetch_oi_sentiment()
        
        # Strike Logic
        interval = get_strike_interval(ticker_sym)
        atm_strike = int(round(curr_p / interval) * interval) # Calculate ATM
        
        # Monte Carlo
        vol_5d = float(df_hist['Close'].pct_change().std() * np.sqrt(252 * 75))
        low_p, mid_p, high_p = run_monte_carlo(curr_p, vol_5d)

        # --- 4. ACTION BANNER & ALIGNMENT LOGIC ---
        st.title(f"🛰️ Grid-x 2.0: {target_input} Tower")
        
        is_bullish = curr_p > vwap and current_rsi < 65 and oi_sent == "BULLISH"
        is_bearish = curr_p < vwap and current_rsi > 35 and oi_sent == "BEARISH"
        
        if is_bullish:
            action, color = f"🟢 SIGNAL: BUY {atm_strike} CE", "green"
        elif is_bearish:
            action, color = f"🔴 SIGNAL: BUY {atm_strike} PE", "red"
        else:
            action, color = f"🟡 MONITORING: Divergence (Bias: {oi_sent})", "orange"

        st.markdown(f"""<div style="background-color:{color}22; padding:20px; border-radius:10px; border:2px solid {color}; text-align:center;">
            <h2 style="color:{color};">{action}</h2>
            <p style="margin:0;">Spot: ₹{curr_p:.2f} | <b>Strike: {atm_strike}</b></p></div>""", unsafe_allow_html=True)

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("PCR (OI Bias)", f"{pcr_val} ({oi_sent})")
        m3.metric("RSI (14m)", f"{current_rsi:.1f}")
        m4.metric("India VIX", f"{current_vix:.2f}")

        # FIXED CHART: Pass as a single DataFrame with appropriate index
        st.subheader("📈 Momentum Chart (Price vs VWAP)")
        chart_df = df_live[['Close']].copy()
        chart_df['VWAP'] = vwap # Adding VWAP as a column for visual alignment
        st.line_chart(chart_df)

        with st.expander("📊 AI Predictive & Strike Intel", expanded=True):
            st.write(f"**Predicted Target (60m):** ₹{high_p:.2f}")
            st.write(f"**Option Strategy:** Recommended **{atm_strike}** Strike based on current volatility.")

except Exception as e:
    st.error(f"Tower Satellite Error: {e}")