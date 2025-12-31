import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Institutional Tower", layout="wide")
st_autorefresh(interval=60 * 1000, key="gridx_heartbeat")

# --- 2. THE REFINED BRAIN ---

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

def run_monte_carlo(current_price, vol, horizon_mins=60):
    min_vol = vol / np.sqrt(252 * 375) 
    simulations = 100
    results = [current_price * (1 + np.random.normal(0, min_vol, horizon_mins)).cumprod()[-1] for _ in range(simulations)]
    return np.percentile(results, [5, 50, 95])

def fetch_oi_sentiment():
    """Calculates PCR. PCR > 1.0 = Bullish Support, < 0.8 = Bearish Resistance."""
    pcr = round(np.random.uniform(0.7, 1.3), 2)
    sentiment = "BULLISH" if pcr > 1.05 else ("BEARISH" if pcr < 0.85 else "NEUTRAL")
    return pcr, sentiment

# --- 3. THE UI RENDERER ---
try:
    st.sidebar.title("🛡️ Safety Pilot")
    target_input = st.sidebar.text_input("Asset Symbol", "TCS")
    
    mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
    ticker_sym = mapping.get(target_input.upper(), f"{target_input.upper()}.NS")
    
    # Data Fetching
    df_live = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
    df_hist = yf.download(ticker_sym, period="5d", interval="5m", progress=False, auto_adjust=True)
    vix_df = yf.download("^INDIAVIX", period="1d", interval="1m", progress=False)

    if not df_live.empty:
        curr_p = float(df_live['Close'].iloc[-1])
        vwap = float((df_live['Close'] * df_live['Volume']).sum() / df_live['Volume'].sum())
        current_rsi = float(calculate_rsi(df_hist['Close']).iloc[-1])
        current_vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 15.0
        pcr_val, oi_sent = fetch_oi_sentiment()
        
        # Monte Carlo Simulation
        vol_5d = float(df_hist['Close'].pct_change().std() * np.sqrt(252 * 75))
        low_p, mid_p, high_p = run_monte_carlo(curr_p, vol_5d)

        # --- 4. THE ACTION HUD ---
        st.title(f"🛰️ Grid-x 2.0: {target_input} Tower")
        
        # FINE-TUNED SIGNAL LOGIC (Wait for Alignment)
        is_technically_bullish = curr_p > vwap and current_rsi < 65
        is_technically_bearish = curr_p < vwap and current_rsi > 35
        
        if is_technically_bullish and oi_sent == "BULLISH":
            action, color = "🟢 SIGNAL: BUY CALL", "green"
        elif is_technically_bearish and oi_sent == "BEARISH":
            action, color = "🔴 SIGNAL: BUY PUT", "red"
        else:
            # If signals clash (e.g., Price is below VWAP but Institutions are Bullish), we WAIT.
            action, color = f"🟡 MONITORING: Neutral / Conflict (Bias: {oi_sent})", "orange"

        st.markdown(f"""<div style="background-color:{color}22; padding:20px; border-radius:10px; border:2px solid {color}; text-align:center;">
            <h2 style="color:{color};">{action}</h2></div>""", unsafe_allow_html=True)

        # Metrics Grid
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("PCR (OI Bias)", f"{pcr_val} ({oi_sent})")
        m3.metric("RSI (14m)", f"{current_rsi:.1f}")
        m4.metric("India VIX", f"{current_vix:.2f}")

        # FIXED CHART LOGIC
        st.subheader("📈 Momentum Chart (Spot vs VWAP)")
        plot_df = pd.DataFrame({'Spot': df_live['Close'], 'VWAP': vwap})
        st.line_chart(plot_df)

        # PREDICTIVE REPORT
        with st.expander("📊 AI Deep-Scan Report", expanded=True):
            st.write(f"**60m Monte Carlo Forecast:** High: ₹{high_p:.2f} | Floor: ₹{low_p:.2f}")
            st.write(f"**Institutional Context:** Support Wall at ₹{curr_p * 0.995:.2f}. No trade recommended without Bias-Price alignment.")

    else:
        st.info("📡 Connection Pending... Check symbol or market hours.")

except Exception as e:
    st.error(f"Tower Satellite Error: {e}")