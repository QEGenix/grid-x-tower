import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. SYSTEM INITIALIZATION ---
st.set_page_config(page_title="Grid-x 2.0 Control Tower", layout="wide")
st_autorefresh(interval=60 * 1000, key="gridx_heartbeat")

# --- 2. INTELLIGENCE ENGINES ---

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    # Avoid division by zero
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def run_monte_carlo(current_price, vol, horizon_mins=60):
    min_vol = vol / np.sqrt(252 * 375) 
    simulations = 100
    all_paths = []
    for _ in range(simulations):
        returns = np.random.normal(0, min_vol, horizon_mins)
        price_path = current_price * (1 + returns).cumprod()
        all_paths.append(price_path[-1])
    return np.percentile(all_paths, [10, 50, 90])

def resolve_ticker(user_input):
    mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN", "VIX": "^INDIAVIX"}
    val = user_input.upper().strip()
    return mapping.get(val, f"{val}.NS" if "^" not in val and "." not in val else val)

# --- 3. SIDEBAR: THE SAFETY PILOT ---
st.sidebar.title("🛡️ Safety Pilot")
capital = st.sidebar.number_input("Total Capital (₹)", 50000, step=5000)
risk_limit = st.sidebar.slider("Risk Per Trade (%)", 0.5, 2.0, 1.0) / 100
target_input = st.sidebar.text_input("Asset Symbol", "TCS")

st.sidebar.divider()
st.sidebar.subheader("📋 Pre-Flight Checklist")
check_news = st.sidebar.checkbox("I checked for major earnings/news.")
check_mood = st.sidebar.checkbox("I am trading without emotional pressure.")

# --- 4. DATA AGGREGATION ---
try:
    ticker_sym = resolve_ticker(target_input)
    # auto_adjust=True and actions=False helps simplify the returned dataframe
    df_live = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
    df_hist = yf.download(ticker_sym, period="5d", interval="5m", progress=False, auto_adjust=True)
    vix_df = yf.download("^INDIAVIX", period="1d", interval="1m", progress=False, auto_adjust=True)
    
    if not df_live.empty:
        # CRITICAL FIX: Ensure we extract single scalar values from pandas series
        curr_p = float(df_live['Close'].iloc[-1])
        prev_close = float(df_hist['Close'].iloc[-1])
        gap_pct = float(((curr_p - prev_close) / prev_close) * 100)
        
        # VWAP & RSI
        vwap = float((df_live['Close'] * df_live['Volume']).sum() / df_live['Volume'].sum())
        rsi_series = calculate_rsi(df_hist['Close'])
        current_rsi = float(rsi_series.iloc[-1])
        
        # VIX Fear Level
        current_vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 15.0
        vol_scalar = 1.5 if current_vix > 18 else (0.8 if current_vix < 12 else 1.0)
        
        # Roadmap Logic
        hi = float(df_live['High'].max())
        lo = float(df_live['Low'].min())
        pivot = (hi + lo + curr_p) / 3
        s1, r1 = (2 * pivot) - hi, (2 * pivot) - lo
        
        # Monte Carlo 60-Min Forecast
        vol_5d = float(df_hist['Close'].pct_change().std() * np.sqrt(252 * 75))
        low_60, mid_60, high_60 = run_monte_carlo(curr_p, vol_5d * vol_scalar)

        # --- 5. AGENTIC COGNITION (Truth Value Fixes Applied) ---
        # We ensure these are simple Booleans (True/False)
        is_bullish = bool(curr_p > vwap and curr_p > pivot and current_rsi < 70)
        is_gap_trap = bool(gap_pct > 2.0)
        
        # --- 6. VISUAL DASHBOARD ---
        st.title(f"🛰️ Grid-x 2.0 Control Tower")
        
        if is_gap_trap:
            st.error(f"### 🛑 GAP TRAP: Price jumped {gap_pct:.1f}% - Entry Forbidden.")
            color = "red"
            status = "DANGER"
        elif is_bullish:
            st.success(f"### 🟢 BULLISH REGIME: Price > VWAP & Pivot. Entry Valid.")
            color = "green"
            status = "BUY"
        else:
            st.warning("### 🟡 MONITORING: Neutral zone or RSI Overextended.")
            color = "orange"
            status = "WAIT"

        # Key Metric Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("Safe Entry (S1)", f"₹{s1:.2f}")
        m3.metric("RSI (14m)", f"{current_rsi:.1f}")
        m4.metric("India VIX", f"{current_vix:.2f}")

        # The Action Card
        risk_per_share = abs(curr_p - s1) if curr_p > s1 else curr_p * 0.01
        qty = int((capital * risk_limit) / risk_per_share) if risk_per_share > 0 else 0
        
        st.markdown(f"""
        <div style="padding:20px; border-radius:10px; border: 3px solid {color}; background-color: rgba(255,255,255,0.05);">
            <h3 style="margin-top:0;">🤖 Agentic Execution Plan</h3>
            <b>Verdict:</b> {status} | <b>Quantity:</b> {qty} Shares<br>
            <b>Target (R1):</b> ₹{r1:.2f} | <b>Stop Loss:</b> ₹{s1:.2f}<br>
            <b>AI Prediction (60m):</b> ₹{low_60:.2f} to ₹{high_60:.2f}
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📈 Real-Time Momentum")
        st.line_chart(df_live['Close'])

    else:
        st.info("📡 Feed Pending... Ensure ticker is correct and market is open.")

except Exception as e:
    # This captures the error and displays it if something still breaks
    st.error(f"Tower Logic Error: {e}")
    st.info("Tip: If error persists, try a different symbol like 'RELIANCE' or 'TCS'.")

st.caption(f"Heartbeat: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Architecture")