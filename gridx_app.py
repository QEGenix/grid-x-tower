import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Strategic Tower", layout="wide")
st_autorefresh(interval=120 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE (Multi-Horizon) ---
@st.cache_data(ttl=120)
def fetch_multi_horizon(ticker_sym):
    try:
        # Intraday (1m), Short-Term (1h), Long-Term (1d)
        d_intra = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
        d_long = yf.download(ticker_sym, period="1y", interval="1d", progress=False, auto_adjust=True)
        d_vix = yf.download("^INDIAVIX", period="1d", interval="5m", progress=False, auto_adjust=True)
        return d_intra, d_long, d_vix
    except Exception as e:
        return None, None, None

def calculate_rsi(series, window=14):
    if len(series) < window + 1: return 50
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

# --- 3. UI RENDERER ---
st.sidebar.title("🛡️ Safety Pilot")
target_input = st.sidebar.text_input("Asset Symbol", "NIFTY").upper().strip()

# Improved Mapping
mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    d_intra, d_long, d_vix = fetch_multi_horizon(ticker_sym)

    if d_intra is None or d_intra.empty or len(d_intra) < 1:
        st.warning(f"📡 Waiting for Satellite Sync... Market data for {target_input} is not yet available.")
    else:
        # --- DATA EXTRACTION & ZERO-DIVISION SHIELD ---
        def get_clean(df, col):
            data = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
            return data.ffill().bfill()

        c_intra = get_clean(d_intra, 'Close')
        v_intra = get_clean(d_intra, 'Volume')
        c_long = get_clean(d_long, 'Close')
        
        curr_p = float(c_intra.iloc[-1])
        
        # FIXED VWAP CALCULATION (Prevents DivisionByZero)
        cum_vol = v_intra.cumsum()
        cum_pvt = (c_intra * v_intra).cumsum()
        
        # If volume is zero, we use the average price as a fallback
        if cum_vol.iloc[-1] == 0:
            vwap = c_intra.mean()
        else:
            vwap = float(cum_pvt.iloc[-1] / cum_vol.iloc[-1])
        
        rsi_intra = float(calculate_rsi(c_intra).iloc[-1])
        rsi_long = float(calculate_rsi(c_long).iloc[-1])
        vix = float(get_clean(d_vix, 'Close').iloc[-1]) if not d_vix.empty else 15.0
        
        # PCR Logic (Synthetic Sentiment)
        pcr_val = round(1.02 if rsi_long > 55 else 0.96, 2)

        # --- MULTI-HORIZON INTELLIGENCE ---
        # 1. Stock Strategy (200-Day Trend)
        ma200 = c_long.rolling(200).mean().iloc[-1]
        stock_bull = curr_p > ma200
        
        # 2. Option Strategy (Intraday Momentum)
        # We use a 0.05% buffer to reduce "No Trade" chop
        intra_bull = curr_p > (vwap * 1.0005) and rsi_intra > 50
        intra_bear = curr_p < (vwap * 0.9995) and rsi_intra < 50

        st.title(f"🛰️ Grid-x 2.0: {target_input} Tower")

        # --- THE CORE DISTINCTION ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📦 STOCK & EQUITY")
            s_label = "ACCUMULATE (BULL)" if stock_bull else "HOLD / LIQUIDATE"
            s_col = "green" if stock_bull else "red"
            st.markdown(f"""<div style="background-color:{s_col}22; padding:20px; border-radius:12px; border:2px solid {s_col};">
                <h2 style="color:{s_col}; margin:0;">{s_label}</h2>
                <p style="margin:5px 0 0 0;"><b>Purpose:</b> Wealth Creation</p>
                <p style="font-size:0.85em;">Signal based on the 200-Day Structural Baseline (₹{ma200:.2f}).</p>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.subheader("⚡ DERIVATIVES (Options)")
            step = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
            strike = int(round(curr_p / step) * step)
            
            if intra_bull:
                o_label, o_col = f"BUY {strike} CE", "green"
                o_brief = "Momentum is breaking upside."
            elif intra_bear:
                o_label, o_col = f"BUY {strike} PE", "red"
                o_brief = "Momentum is breaking downside."
            else:
                o_label, o_col = "NO TRADE", "orange"
                o_brief = "Price is hugging VWAP (Chop)."

            st.markdown(f"""<div style="background-color:{o_col}22; padding:20px; border-radius:12px; border:2px solid {o_col};">
                <h2 style="color:{o_col}; margin:0;">{o_label}</h2>
                <p style="margin:5px 0 0 0;"><b>Purpose:</b> Daily Income / Hedge</p>
                <p style="font-size:0.85em;">{