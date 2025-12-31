import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Master Tower", layout="wide")
st_autorefresh(interval=120 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE (Refined for Multi-Index Safety) ---
@st.cache_data(ttl=120)
def fetch_tower_data(ticker_sym):
    try:
        # We fetch the ticker and VIX together to save API calls
        tickers = f"{ticker_sym} ^INDIAVIX"
        data = yf.download(tickers, period="1d", interval="1m", progress=False, auto_adjust=True)
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
target_input = st.sidebar.text_input("Asset Symbol", "TCS").upper().strip()

# Mapping for Indian Indices
mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    all_data = fetch_tower_data(ticker_sym)

    if all_data is None or all_data.empty:
        st.error(f"⚠️ Symbol '{target_input}' Not Found or Yahoo Rate Limited.")
    else:
        # --- ROBUST DATA EXTRACTION ---
        # This part handles both Single-Index and Multi-Index data formats
        try:
            if isinstance(all_data.columns, pd.MultiIndex):
                closes = all_data['Close'][ticker_sym].dropna()
                volumes = all_data['Volume'][ticker_sym].dropna()
                vix_series = all_data['Close']['^INDIAVIX'].dropna()
            else:
                closes = all_data['Close'].dropna()
                volumes = all_data['Volume'].dropna()
                vix_series = pd.Series([15.0]) # Fallback for VIX
            
            curr_p = float(closes.iloc[-1])
            vwap = float((closes * volumes).sum() / volumes.sum())
            current_rsi = float(calculate_rsi(closes).iloc[-1])
            vix = float(vix_series.iloc[-1]) if not vix_series.empty else 15.0
            
            # Logic: Signal & Strike
            buffer = vwap * 0.001 
            is_bullish = curr_p > (vwap + buffer) and 45 < current_rsi < 65
            is_bearish = curr_p < (vwap - buffer) and 35 < current_rsi < 55
            
            interval = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
            atm_strike = int(round(curr_p / interval) * interval)
            
            # Bonus: Capital Calculation (Approximate Margin)
            lot_size = 50 if "NSEI" in ticker_sym else (15 if "NSEBANK" in ticker_sym else 100)
            approx_margin = (curr_p * lot_size) * 0.10 # Assuming 10% for Option Selling/Futures

            st.title(f"🛰️ Grid-x 2.0: {target_input}")

            if is_bullish:
                action, color = f"🟢 BUY {atm_strike} CE", "green"
                reasons = [f"Price above VWAP (Fair: ₹{vwap:.2f})", f"RSI strength at {current_rsi:.1f}", f"Est. Margin for 1 Lot: ₹{approx_margin:,.0f}"]
            elif is_bearish:
                action, color = f"🔴 BUY {atm_strike} PE", "red"
                reasons = [f"Price below VWAP (Fair: ₹{vwap:.2f})", f"RSI weakness at {current_rsi:.1f}", f"Est. Margin for 1 Lot: ₹{approx_margin:,.0f}"]
            else:
                action, color = "🟡 MONITORING / NO TRADE", "orange"
                reasons = ["Price inside VWAP Chop Zone", f"RSI Neutral at {current_rsi:.1f}", "Waiting for directional breakout"]

            st.markdown(f"""<div style="background-color:{color}22; padding:20px; border-radius:12px; border:2px solid {color}; text-align:center;">
                <h1 style="color:{color}; margin:0;">{action}</h1></div>""", unsafe_allow_html=True)

            st.write("")
            st.markdown(f"""
            <div style="background-color:rgba(255,255,255,0.05); padding:15px; border-radius:10px; border-left: 5px solid {color};">
                <h4 style="margin-top:0;">🧠 Agentic Reasoning</h4>
                <ul style="margin-bottom:0;">
                    <li><b>Market State:</b> {reasons[0]}</li>
                    <li><b>Momentum:</b> {reasons[1]}</li>
                    <li><b>Execution:</b> {reasons[2]}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.write("")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Live Price", f"₹{curr_p:.2f}")
            m2.metric("VWAP (Fair)", f"₹{vwap:.2f}", f"{curr_p - vwap:.2f}")
            m3.metric("RSI (14m)", f"{current_rsi:.1f}")
            m4.metric("India VIX", f"{vix:.2f}")

        except Exception as e:
            st.error(f"Data Processing Error: {e}")
            st.info("Yahoo Finance may have returned an incomplete data slice.")

except Exception as e:
    st.info("📡 Scanning Satellite Feed... Please check ticker symbol.")

st.divider()
st.caption(f"Sync: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Architecture")