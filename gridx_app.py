import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import numpy as np
from pykalman import KalmanFilter
from streamlit_autorefresh import st_autorefresh

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="QE Genix: State-Space Sniper", layout="wide")
st_autorefresh(interval=60 * 1000, key="sniper_heartbeat")

SENSEX_TICKER = "^BSESN"

# --- 2. NOISE-REDUCTION BRAIN ---
def apply_kalman_filter(data):
    """Uses a State-Space model to find the 'True' price under the noise."""
    kf = KalmanFilter(transition_matrices=[1], 
                      observation_matrices=[1], 
                      initial_state_mean=data[0], 
                      initial_state_covariance=1, 
                      observation_covariance=10, # High value = ignore more noise
                      transition_covariance=0.01)
    state_means, _ = kf.filter(data)
    return state_means.flatten()

@st.cache_data(ttl=60)
def fetch_tactical_data():
    # Fetch 5 days of 5-minute data for stability
    df = yf.download(SENSEX_TICKER, period="5d", interval="5m", progress=False, auto_adjust=True)
    return df

# --- 3. THE DECISION LOGIC ---
st.title("🛰️ QE Genix: Regime-Switching Sniper")

data = fetch_tactical_data()

if data is not None and not data.empty:
    close = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
    
    # 1. Kalman Smoothing (The 'True' Trend)
    smoothed_price = apply_kalman_filter(close.values)
    current_true_p = smoothed_price[-1]
    prev_true_p = smoothed_price[-10] # Lookback 50 mins
    
    # 2. Volatility Buffer (ATR)
    atr = ta.atr(data['High'], data['Low'], close, length=14).iloc[-1]
    buffer = atr * 1.5 
    
    # 3. Decision State (Hysteresis)
    # The decision ONLY changes if current price breaks the 'True' trend + Buffer
    is_stable_up = (current_true_p > prev_true_p) and (close.iloc[-1] > current_true_p - buffer)
    is_stable_down = (current_true_p < prev_true_p) and (close.iloc[-1] < current_true_p + buffer)
    
    # --- UI RENDERING ---
    st.divider()
    
    # REGIME INDICATOR
    if is_stable_up:
        regime = "BULLISH ACCUMULATION"
        color = "#2ecc71"
        action = "BUY CALL (CE) & HOLD"
    elif is_stable_down:
        regime = "BEARISH DISTRIBUTION"
        color = "#e74c3c"
        action = "BUY PUT (PE) & HOLD"
    else:
        regime = "CHOPPY / NO TRADE"
        color = "#fbc531"
        action = "STAY IN CASH"

    # Tactical Command Box
    st.markdown(f"""
        <div style="background-color:{color}22; border:5px solid {color}; padding:30px; border-radius:15px; text-align:center;">
            <p style="font-size:18px; color:{color}; font-weight:bold; text-transform:uppercase;">Current Market State: {regime}</p>
            <h1 style="color:white; margin:10px 0;">{action}</h1>
            <p style="color:#aaa;">State locked based on 50-minute Kalman Stability Analysis</p>
        </div>
    """, unsafe_allow_html=True)

    # Vitals
    m1, m2, m3 = st.columns(3)
    m1.metric("Sensex Spot", f"{close.iloc[-1]:,.2f}")
    m2.metric("True Trend (Filtered)", f"{current_true_p:,.2f}")
    m3.metric("Noise Buffer (ATR)", f"± {buffer:.1f} pts")

else:
    st.warning("Satellite Connection Initializing...")