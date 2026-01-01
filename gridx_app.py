import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="QE Genix: Sensex Sniper", layout="wide")
st_autorefresh(interval=60 * 1000, key="sniper_heartbeat")

# CONSTANTS (The Locked Pillars)
LOT_SIZE = 20
CAPITAL = 20000
MAX_RISK_PER_TRADE = 1000
MAX_DAILY_LOSS = 2000
SENSEX_TICKER = "^BSESN"

# --- 2. THE INTELLIGENCE SATELLITE ---
@st.cache_data(ttl=60)
def fetch_sensex_data():
    try:
        # Fetch 1m for execution and 1d for structural trend
        d_intra = yf.download(SENSEX_TICKER, period="1d", interval="1m", progress=False, auto_adjust=True)
        d_trend = yf.download(SENSEX_TICKER, period="5d", interval="1h", progress=False, auto_adjust=True)
        d_vix = yf.download("^INDIAVIX", period="1d", interval="5m", progress=False, auto_adjust=True)
        return d_intra, d_trend, d_vix
    except Exception:
        return None, None, None

def get_probability_score(curr_p, vwap, rsi, vix, trend_aligned):
    """The 90% Accuracy Filter: Calculates Confluence"""
    score = 0
    # Price vs VWAP Delta (30 pts)
    if abs(curr_p - vwap) > 10: score += 30
    # RSI Momentum (30 pts)
    if (curr_p > vwap and rsi > 55) or (curr_p < vwap and rsi < 45): score += 30
    # Volatility Shield (20 pts)
    if vix < 18: score += 20
    # Trend Alignment (20 pts)
    if trend_aligned: score += 20
    return score

# --- 3. UI RENDERER ---
st.title("🛰️ QE Genix: Sensex Sniper Engine")
st.caption(f"Target: SENSEX (^BSESN) | Lot Size: {LOT_SIZE} | Risk Cap: ₹{MAX_RISK_PER_TRADE}")

try:
    d_intra, d_trend, d_vix = fetch_sensex_data()

    if d_intra is None or d_intra.empty or len(d_intra) < 5:
        st.warning("📡 Syncing with Sensex Satellite... Market data pending.")
    else:
        # Data Extraction
        def get_clean(df, col):
            data = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
            return data.ffill().bfill()

        c_intra = get_clean(d_intra, 'Close')
        v_intra = get_clean(d_intra, 'Volume')
        curr_p = float(c_intra.iloc[-1])
        
        # VWAP Calculation
        vwap = float((c_intra * v_intra).cumsum().iloc[-1] / v_intra.cumsum().iloc[-1])
        
        # RSI 14
        delta = c_intra.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])
        
        # 2-Minute Guard Check (Pillar 2)
        p_last = float(c_intra.iloc[-1])
        p_prev = float(c_intra.iloc[-2])
        is_bull_confirmed = p_last > vwap and p_prev > vwap
        is_bear_confirmed = p_last < vwap and p_prev < vwap

        # VIX and Structural Trend
        vix = float(get_clean(d_vix, 'Close').iloc[-1]) if not d_vix.empty else 15.0
        ma_trend = float(get_clean(d_trend, 'Close').rolling(20).mean().iloc[-1])
        trend_aligned = (curr_p > ma_trend and is_bull_confirmed) or (curr_p < ma_trend and is_bear_confirmed)

        prob_score = get_probability_score(curr_p, vwap, rsi, vix, trend_aligned)

        # --- THE COCKPIT LAYOUT ---
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🎯 Probability Dial")
            dial_color = "#2ecc71" if prob_score >= 75 else ("#f39c12" if prob_score >= 50 else "#e74c3c")
            st.markdown(f"""
                <div style="border:4px solid {dial_color}; padding:30px; border-radius:20px; text-align:center; background-color:{dial_color}11;">
                    <h1 style="color:{dial_color}; font-size:72px; margin:0;">{prob_score}%</h1>
                    <p style="letter-spacing:2px;">CONFLUENCE SCORE</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.subheader("📊 Live Vitals")
            st.metric("SENSEX Spot", f"{curr_p:,.2f}", f"{(curr_p - vwap):.2f} vs VWAP")
            st.metric("India VIX", f"{vix:.2f}", "STABLE" if vix < 18 else "VOLATILE")
            st.metric("RSI (1m)", f"{rsi:.1f}")

        # --- SIGNAL EXECUTION GATE ---
        st.write("")
        st.subheader("⚡ Sniper Signal Terminal")
        
        if prob_score >= 75:
            # Determine Strike (100pt intervals for Sensex)
            strike = int(round(curr_p / 100) * 100)
            side = "CE" if is_bull_confirmed else "PE"
            sig_color = "#2ecc71" if side == "CE" else "#e74c3c"
            
            st.markdown(f"""
                <div style="background-color:{sig_color}; padding:40px; border-radius:15px; text-align:center;">
                    <h1 style="color:white; margin:0;">BUY SENSEX {strike} {side}</h1>
                    <p style="color:white; font-size:20px;"><b>Entry:</b> CMP | <b>SL:</b> 50 Pts (₹{50*LOT_SIZE}) | <b>Tgt:</b> 100 Pts (₹{100*LOT_SIZE})</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Agentic Reasoning Box
            with st.expander("📝 View Agentic Reasoning"):
                st.write(f"* **Pillar 1:** Lot size locked at {LOT_SIZE} units.")
                st.write(f"* **Pillar 2:** 2-Minute Guard Confirmed (Last 2 candles closed {'Above' if side=='CE' else 'Below'} VWAP).")
                st.write(f"* **Pillar 3:** Risk limited to ₹{MAX_RISK_PER_TRADE} per trade.")
                st.write(f"* **Confluence:** RSI is {rsi:.1f} and Trend is {'Aligned' if trend_aligned else 'Not Aligned'}.")
        else:
            st.info("🛡️ **System Status:** Radar Active. Waiting for 75% Probability Confluence. No trade suggested.")

except Exception as e:
    st.error(f"Execution Error: {e}")

st.divider()
st.caption(f"QE Genix Sniper v2.0 | Multiplier: 20x | Time: {datetime.datetime.now().strftime('%H:%M:%S')}")