import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Dual Tower", layout="wide")
st_autorefresh(interval=60 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE ---
@st.cache_data(ttl=60)
def fetch_tower_data(ticker_sym):
    try:
        d_intra = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
        d_long = yf.download(ticker_sym, period="2y", interval="1d", progress=False, auto_adjust=True)
        vix_data = yf.download("^INDIAVIX", period="1d", interval="5m", progress=False, auto_adjust=True)
        return d_intra, d_long, vix_data
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
target_input = st.sidebar.text_input("Asset Symbol", "RELIANCE").upper().strip()

mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    d_intra, d_long, d_vix = fetch_tower_data(ticker_sym)

    if d_intra is None or d_intra.empty or len(d_intra) < 2:
        st.warning(f"📡 Syncing with {target_input} Satellite... Market data pending.")
    else:
        # DATA EXTRACTION
        def get_clean(df, col):
            data = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
            return data.ffill().bfill()

        c_intra, v_intra = get_clean(d_intra, 'Close'), get_clean(d_intra, 'Volume')
        c_long = get_clean(d_long, 'Close')
        curr_p = float(c_intra.iloc[-1])
        
        # VWAP & RSI
        cum_vol = v_intra.cumsum()
        cum_pvt = (c_intra * v_intra).cumsum()
        vwap = float(cum_pvt.iloc[-1] / cum_vol.iloc[-1]) if cum_vol.iloc[-1] != 0 else curr_p
        rsi_intra = float(calculate_rsi(c_intra).iloc[-1])
        ma200 = float(c_long.rolling(200).mean().iloc[-1])

        # VIX Extraction
        vix = 15.0
        if d_vix is not None and not d_vix.empty:
            vix = float(get_clean(d_vix, 'Close').iloc[-1])

        st.title(f"🛰️ QE Genix: {target_input} Dual-Tower Dashboard")
        st.write("")

        # --- THE DUAL PARTITION ---
        left_col, right_col = st.columns(2)

        # --- LEFT SIDE: STOCKS ---
        with left_col:
            st.markdown("### 📦 EQUITY TERMINAL (Cash)")
            s_status = "ACCUMULATE" if curr_p > ma200 else "DISTRIBUTION"
            s_col = "#2ecc71" if curr_p > ma200 else "#e74c3c"
            
            st.markdown(f"""
                <div style="border:2px solid {s_col}; padding:20px; border-radius:12px; background-color:{s_col}15;">
                    <h2 style="color:{s_col}; margin:0;">{s_status}</h2>
                    <p style="margin:10px 0 0 0;"><b>Structure:</b> 200-Day Trend Tracking</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            with st.container():
                st.info(f"**Wealth Brief:** Price is ₹{abs(curr_p - ma200):.2f} {'above' if curr_p > ma200 else 'below'} the 200DMA (₹{ma200:.2f}). This is a **{'Structural Uptrend' if curr_p > ma200 else 'Structural Downtrend'}**.")
            
            # Stock Metrics
            sm1, sm2 = st.columns(2)
            sm1.metric("Live Price", f"₹{curr_p:.2f}")
            sm2.metric("Trendline (200D)", f"₹{ma200:.2f}")

        # --- RIGHT SIDE: OPTIONS ---
        with right_col:
            st.markdown("### ⚡ DERIVATIVE TERMINAL (Options)")
            is_bull = curr_p > vwap and rsi_intra > 50
            is_bear = curr_p < vwap and rsi_intra < 50
            
            o_col = "#2ecc71" if is_bull else ("#e74c3c" if is_bear else "#f39c12")
            step = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
            strike = int(round(curr_p / step) * step)
            o_action = f"BUY {strike} CE" if is_bull else (f"BUY {strike} PE" if is_bear else "NO TRADE")

            st.markdown(f"""
                <div style="border:2px solid {o_col}; padding:20px; border-radius:12px; background-color:{o_col}15;">
                    <h2 style="color:{o_col}; margin:0;">{o_action}</h2>
                    <p style="margin:10px 0 0 0;"><b>Structure:</b> Intraday Momentum Tracking</p>
                </div>
            """, unsafe_allow_html=True)

            st.write("")
            with st.container():
                st.success(f"**Income Brief:** Intraday momentum is **{('Bullish' if is_bull else 'Bearish' if is_bear else 'Neutral')}**. RSI ({rsi_intra:.1f}) and VWAP (₹{vwap:.2f}) suggest {('entry' if (is_bull or is_bear) else 'waiting')} for better volume.")

            # Option Metrics
            om1, om2 = st.columns(2)
            om1.metric("VWAP (Fair)", f"₹{vwap:.2f}", f"{((curr_p-vwap)/vwap*100):.2f}%")
            om2.metric("RSI (1m)", f"{rsi_intra:.1f}")

        # --- FOOTER METRICS (Market Condition) ---
        st.divider()
        f1, f2, f3 = st.columns(3)
        f1.metric("Asset Class", "Index" if "^" in ticker_sym else "Equity")
        f2.metric("India VIX", f"{vix:.2f}", delta="High Vol" if vix > 18 else "Stable", delta_color="inverse")
        f3.metric("Last Heartbeat", datetime.datetime.now().strftime('%H:%M:%S'))

except Exception as e:
    st.error(f"Tower Analysis Error: {e}")

st.caption("QE Genix Architecture | Data provided by Satellite Feed (yFinance)")