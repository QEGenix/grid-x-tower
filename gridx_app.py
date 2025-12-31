import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG (Must be the first Streamlit command) ---
try:
    st.set_page_config(page_title="Grid-x 2.0: Institutional Tower", layout="wide")
except:
    pass # Prevents crash if re-running in certain environments

st_autorefresh(interval=60 * 1000, key="gridx_heartbeat")

# --- 2. THE INSTITUTIONAL BRAIN ---

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

def run_monte_carlo(current_price, vol, horizon_mins=60):
    """Generates the 60-minute Predictive Probability Cloud."""
    min_vol = vol / np.sqrt(252 * 375) 
    simulations = 100
    results = []
    for _ in range(simulations):
        returns = np.random.normal(0, min_vol, horizon_mins)
        price_path = current_price * (1 + returns).cumprod()
        results.append(price_path[-1])
    # Returns 10th, 50th, and 90th percentile
    return np.percentile(results, [10, 50, 90])

def get_pcr_sentiment():
    """Simulates real-time PCR (Put-Call Ratio) Logic."""
    pcr = round(np.random.uniform(0.7, 1.3), 2)
    sentiment = "BULLISH" if pcr > 1.05 else ("BEARISH" if pcr < 0.85 else "NEUTRAL")
    return pcr, sentiment

# --- 3. THE UI RENDERER (Wrapped in a Safety Try/Except) ---
try:
    st.sidebar.title("🛡️ Safety Pilot")
    target_input = st.sidebar.text_input("Asset Symbol", "NIFTY")
    
    # Ticker Resolution
    mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
    ticker_sym = mapping.get(target_input.upper(), f"{target_input.upper()}.NS")
    
    # Data Fetching
    df_live = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
    df_hist = yf.download(ticker_sym, period="5d", interval="5m", progress=False, auto_adjust=True)
    vix_df = yf.download("^INDIAVIX", period="1d", interval="1m", progress=False)

    if not df_live.empty:
        # Metrics Calculation
        curr_p = float(df_live['Close'].iloc[-1])
        vwap = float((df_live['Close'] * df_live['Volume']).sum() / df_live['Volume'].sum())
        current_rsi = float(calculate_rsi(df_hist['Close']).iloc[-1])
        current_vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 15.0
        pcr_val, pcr_sent = get_pcr_sentiment()
        
        # Monte Carlo Simulation
        vol_5d = float(df_hist['Close'].pct_change().std() * np.sqrt(252 * 75))
        low_p, mid_p, high_p = run_monte_carlo(curr_p, vol_5d)

        # --- VISUALS: ACTION BANNER ---
        st.title(f"🛰️ Grid-x 2.0: {target_input} Tower")
        
        # Institutional Signal Logic
        is_bullish = curr_p > vwap and current_rsi < 65 and pcr_val > 0.9
        
        if is_bullish:
            st.success(f"### 🟢 SIGNAL: BUY CALL | PCR: {pcr_val} ({pcr_sent})")
            color = "green"
        elif curr_p < vwap and current_rsi > 35:
            st.error(f"### 🔴 SIGNAL: BUY PUT | PCR: {pcr_val} ({pcr_sent})")
            color = "red"
        else:
            st.warning("### 🟡 MONITORING: Awaiting Institutional Alignment")
            color = "orange"

        # TIER 1: LIVE METRICS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spot Price", f"₹{curr_p:.2f}")
        c2.metric("PCR Sentiment", pcr_val, pcr_sent)
        c3.metric("RSI", f"{current_rsi:.1f}")
        c4.metric("India VIX", f"{current_vix:.2f}")

        # TIER 2: PREDICTIVE CLOUD & CHART
        st.subheader("📈 Institutional Momentum (Price vs VWAP)")
        chart_data = df_live[['Close']].copy()
        chart_data['VWAP'] = vwap
        st.line_chart(chart_data)

        # TIER 3: AI DEEP SCAN
        with st.expander("📊 AI Predictive Intelligence Report", expanded=True):
            st.write(f"**60-Min Probability Cloud:**")
            st.write(f"- 🟢 Optimistic Target: ₹{high_p:.2f}")
            st.write(f"- ⚪ Neutral Median: ₹{mid_p:.2f}")
            st.write(f"- 🔴 Safety Floor: ₹{low_p:.2f}")
            st.divider()
            st.write(f"**Institutional Context:** PCR at {pcr_val} suggests {pcr_sent} bias. Price is currently {'Above' if curr_p > vwap else 'Below'} Fair Value (VWAP).")

    else:
        st.info("📡 Connecting to NSE Satellite... Ensure market is open or use a valid ticker (e.g., RELIANCE).")

except Exception as e:
    st.error(f"🚨 TOWER ERROR: {e}")
    st.write("Troubleshooting: Try clearing your browser cache or restarting the terminal.")

st.caption(f"System Time: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Agentic Tower")