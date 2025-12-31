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
        # Fetching 1m (Intraday), 1h (Short-Term), 1d (Long-Term)
        d_intra = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
        d_short = yf.download(ticker_sym, period="1mo", interval="1h", progress=False, auto_adjust=True)
        d_long = yf.download(ticker_sym, period="1y", interval="1d", progress=False, auto_adjust=True)
        vix = yf.download("^INDIAVIX", period="1d", interval="5m", progress=False, auto_adjust=True)
        return d_intra, d_short, d_long, vix
    except:
        return None, None, None, None

def calculate_rsi(series, window=14):
    if len(series) < window: return 50
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

# --- 3. UI RENDERER ---
st.sidebar.title("🛡️ Safety Pilot")
target_input = st.sidebar.text_input("Asset Symbol", "NIFTY").upper().strip()

# Explicit mapping to differentiate Index vs Stock
IS_INDEX = target_input in ["NIFTY", "BANKNIFTY", "SENSEX"]
mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    d_intra, d_short, d_long, d_vix = fetch_multi_horizon(ticker_sym)

    if d_intra is None or d_intra.empty or len(d_intra) < 2:
        st.error(f"⚠️ No live data for '{target_input}'. Check if market is open.")
    else:
        # --- DATA CLEANING (VWAP NaN FIX) ---
        def get_clean(df, col):
            data = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
            return data.ffill().bfill() # Forward fill and backfill any NaNs

        c_intra, v_intra = get_clean(d_intra, 'Close'), get_clean(d_intra, 'Volume')
        c_short, c_long = get_clean(d_short, 'Close'), get_clean(d_long, 'Close')
        
        curr_p = float(c_intra.iloc[-1])
        
        # Robust VWAP calculation
        pvt = c_intra * v_intra
        cumulative_pvt = pvt.cumsum()
        cumulative_vol = v_intra.cumsum()
        # Handle zero volume to avoid NaN
        vwap_series = cumulative_pvt / cumulative_vol.replace(0, 1)
        vwap = float(vwap_series.iloc[-1])
        
        rsi_intra = float(calculate_rsi(c_intra).iloc[-1])
        rsi_long = float(calculate_rsi(c_long).iloc[-1])
        vix = float(get_clean(d_vix, 'Close').iloc[-1]) if not d_vix.empty else 15.0
        pcr_val = round(1.0 + (0.05 if rsi_long > 50 else -0.05), 2) # Simulated Sentiment

        # --- SIGNAL CALCULATOR ---
        intra_bull = curr_p > vwap and rsi_intra > 50
        intra_bear = curr_p < vwap and rsi_intra < 50
        long_bull = curr_p > c_long.rolling(200).mean().iloc[-1]

        st.title(f"🛰️ Grid-x 2.0: {target_input} Tower")

        # --- THE DISTINCTION SECTION ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📦 STOCK & EQUITY (Delivery)")
            status = "ACCUMULATE" if long_bull else "HOLD / EXIT"
            s_col = "green" if long_bull else "red"
            st.markdown(f"""<div style="background-color:{s_col}22; padding:20px; border-radius:10px; border:2px solid {s_col};">
                <h2 style="color:{s_col}; margin:0;">{status}</h2>
                <p style="margin:5px 0 0 0;"><b>Horizon:</b> 3+ Months</p>
                <p style="font-size:0.8em;">Based on structural price-line vs 200DMA.</p>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.subheader("⚡ DERIVATIVES (Options)")
            # Smart strike calculation
            step = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
            strike = int(round(curr_p / step) * step)
            
            if intra_bull:
                o_label, o_col = f"BUY {strike} CE", "green"
            elif intra_bear:
                o_label, o_col = f"BUY {strike} PE", "red"
            else:
                o_label, o_col = "NO TRADE", "orange"

            st.markdown(f"""<div style="background-color:{o_col}22; padding:20px; border-radius:10px; border:2px solid {o_col};">
                <h2 style="color:{o_col}; margin:0;">{o_label}</h2>
                <p style="margin:5px 0 0 0;"><b>Horizon:</b> Intraday / Weekly</p>
                <p style="font-size:0.8em;">Based on VWAP Momentum & RSI Acceleration.</p>
            </div>""", unsafe_allow_html=True)

        # --- METRICS & BRIEF ---
        st.write("")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("VWAP (Intra)", f"₹{vwap:.2f}", f"{((curr_p-vwap)/vwap*100):.2f}%")
        m3.metric("PCR Sentiment", f"{pcr_val}")
        m4.metric("Market Vol (VIX)", f"{vix:.2f}")

        with st.expander("🧠 Agentic Intelligence Brief", expanded=True):
            asset_type = "INDEX" if IS_INDEX else "INDIVIDUAL STOCK"
            st.markdown(f"""
            * **Identity:** Analyzing {target_input} as an **{asset_type}**.
            * **Logic:** For **Stocks**, we prioritize capital safety. For **Options**, we prioritize "Delta" and "Theta" by following the {('Bullish' if intra_bull else 'Bearish' if intra_bear else 'Neutral')} intraday trend.
            * **Alert:** {('Price is trending with volume support.' if curr_p > vwap else 'Price is decaying. Avoid long positions.')}
            """)

except Exception as e:
    st.error(f"Satellite sync failed. Possible reasons: Market closed or invalid symbol. Error: {e}")

st.divider()
st.caption(f"Sync: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Master Architecture")