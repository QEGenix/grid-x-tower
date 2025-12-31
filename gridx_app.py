import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime
import math

# --- 1. SYSTEM INITIALIZATION ---
st.set_page_config(page_title="Grid-x 2.0 Pro: Pilot HUD", layout="wide")
st_autorefresh(interval=60 * 1000, key="gridx_heartbeat")

# --- 2. INTELLIGENCE ENGINES ---

def get_strike_interval(ticker):
    """Returns the NSE standard strike interval for different assets."""
    ticker = ticker.upper()
    if "NSEI" in ticker: return 50    # Nifty 50
    if "NSEBANK" in ticker: return 100 # Bank Nifty
    if "BSESN" in ticker: return 100   # Sensex
    return 10  # Default for stocks (can be refined per stock price)

def calculate_atm_strike(price, interval):
    """Rounds the current price to the nearest NSE strike."""
    return int(round(price / interval) * interval)

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

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
target_input = st.sidebar.text_input("Asset Symbol", "NIFTY")

# --- 4. DATA AGGREGATION ---
try:
    ticker_sym = resolve_ticker(target_input)
    df_live = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
    df_hist = yf.download(ticker_sym, period="5d", interval="5m", progress=False, auto_adjust=True)
    vix_df = yf.download("^INDIAVIX", period="1d", interval="1m", progress=False, auto_adjust=True)
    
    if not df_live.empty:
        curr_p = float(df_live['Close'].iloc[-1])
        prev_close = float(df_hist['Close'].iloc[-1])
        gap_pct = float(((curr_p - prev_close) / prev_close) * 100)
        
        # Indicators
        vwap = float((df_live['Close'] * df_live['Volume']).sum() / df_live['Volume'].sum())
        current_rsi = float(calculate_rsi(df_hist['Close']).iloc[-1])
        current_vix = float(vix_df['Close'].iloc[-1]) if not vix_df.empty else 15.0
        
        # Strike Logic
        interval = get_strike_interval(ticker_sym)
        atm_strike = calculate_atm_strike(curr_p, interval)
        
        # Monte Carlo
        vol_5d = float(df_hist['Close'].pct_change().std() * np.sqrt(252 * 75))
        low_60, mid_60, high_60 = run_monte_carlo(curr_p, vol_5d)

        # --- 5. AGENTIC DECISION ENGINE ---
        is_bullish = curr_p > vwap and current_rsi < 65
        is_bearish = curr_p < vwap and current_rsi > 35
        
        if gap_pct > 1.5:
            action, color, icon = "GAP TRAP (WAIT)", "#FFA500", "⚠️"
            order_type = "NONE"
        elif is_bullish:
            action, color, icon = f"BUY {atm_strike} CE", "#00FF00", "🚀"
            order_type = "CALL"
        elif is_bearish:
            action, color, icon = f"BUY {atm_strike} PE", "#FF4B4B", "📉"
            order_type = "PUT"
        else:
            action, color, icon = "WAIT / NEUTRAL", "#808080", "⏳"
            order_type = "NONE"

        # --- 6. VISUAL DASHBOARD ---
        st.markdown(f"""
            <div style="background-color:{color}22; padding:30px; border-radius:15px; border:2px solid {color}; text-align:center;">
                <h1 style="color:{color}; margin:0;">{icon} {action}</h1>
                <p style="font-size:1.2rem; margin:10px 0;">Spot: ₹{curr_p:.2f} | Strike: <b>{atm_strike}</b></p>
            </div>
        """, unsafe_allow_html=True)

        st.write("")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("RSI (14m)", f"{current_rsi:.1f}")
        m3.metric("ATM Strike", atm_strike)
        m4.metric("VIX", f"{current_vix:.2f}")

        # Execution Logic Card
        st.markdown(f"""
        <div style="padding:20px; border-radius:10px; background-color: rgba(255,255,255,0.05); border-left: 5px solid {color};">
            <h3>📝 Trade Execution Plan</h3>
            <b>Strategy:</b> {order_type} Intraday | <b>Instrument:</b> {target_input} {atm_strike}<br>
            <b>AI Forecast (60m):</b> Likely range between ₹{low_60:.2f} and ₹{high_60:.2f}<br>
            <b>Risk Rule:</b> Exit if price drops below ₹{curr_p * 0.995:.2f} (0.5% Stop Loss)
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📊 Momentum Pulse")
        st.line_chart(df_live['Close'])

    else:
        st.info("📡 Connection Pending... Check if ticker exists and market is open.")

except Exception as e:
    st.error(f"Tower Logic Error: {e}")

st.caption(f"Last Pulse: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Pro")