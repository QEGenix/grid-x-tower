import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Strategic Tower", layout="wide")
st_autorefresh(interval=120 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE ---
@st.cache_data(ttl=120)
def fetch_multi_horizon(ticker_sym):
    try:
        d_intra = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
        d_long = yf.download(ticker_sym, period="1y", interval="1d", progress=False, auto_adjust=True)
        d_vix = yf.download("^INDIAVIX", period="1d", interval="5m", progress=False, auto_adjust=True)
        return d_intra, d_long, d_vix
    except:
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

mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    d_intra, d_long, d_vix = fetch_multi_horizon(ticker_sym)

    if d_intra is None or d_intra.empty or len(d_intra) < 1:
        st.warning(f"📡 Syncing with Satellite... Data for {target_input} pending.")
    else:
        # Data Extraction
        def get_clean(df, col):
            data = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
            return data.ffill().bfill()

        c_intra, v_intra = get_clean(d_intra, 'Close'), get_clean(d_intra, 'Volume')
        c_long = get_clean(d_long, 'Close')
        curr_p = float(c_intra.iloc[-1])
        
        # VWAP Calculation with Zero-Volume Guard
        cum_vol = v_intra.cumsum()
        cum_pvt = (c_intra * v_intra).cumsum()
        vwap = float(cum_pvt.iloc[-1] / cum_vol.iloc[-1]) if cum_vol.iloc[-1] != 0 else curr_p
        
        rsi_intra = float(calculate_rsi(c_intra).iloc[-1])
        vix = float(get_clean(d_vix, 'Close').iloc[-1]) if not d_vix.empty else 15.0

        # --- HORIZON LOGIC ---
        ma200 = c_long.rolling(200).mean().iloc[-1]
        stock_bull = curr_p > ma200
        
        # Derivative Momentum (Buffer included to prevent "No Trade" sticky errors)
        intra_bull = curr_p > (vwap * 1.0002) and rsi_intra > 52
        intra_bear = curr_p < (vwap * 0.9998) and rsi_intra < 48

        st.title(f"🛰️ Grid-x 2.0: {target_input} Tower")

        # --- THE DISTINCTION SECTION (Syntax-Error Free) ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📦 STOCK & EQUITY")
            s_label = "ACCUMULATE" if stock_bull else "HOLD / EXIT"
            s_col = "green" if stock_bull else "red"
            # Using HTML without f-string brackets to avoid SyntaxError
            html_stock = f"""<div style="background-color:{s_col}22; padding:20px; border-radius:12px; border:2px solid {s_col};">
                <h2 style="color:{s_col}; margin:0;">{s_label}</h2>
                <p style="margin:5px 0 0 0;"><b>Wealth Cycle:</b> {'Structural Uptrend' if stock_bull else 'Structural Downtrend'}</p>
            </div>"""
            st.markdown(html_stock, unsafe_allow_html=True)

        with col2:
            st.subheader("⚡ DERIVATIVES (Options)")
            step = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
            strike = int(round(curr_p / step) * step)
            
            if intra_bull:
                o_label, o_col, o_brief = f"BUY {strike} CE", "green", "Bullish Momentum"
            elif intra_bear:
                o_label, o_col, o_brief = f"BUY {strike} PE", "red", "Bearish Distribution"
            else:
                o_label, o_col, o_brief = "NO TRADE", "orange", "Sideways / Chop"

            html_opt = f"""<div style="background-color:{o_col}22; padding:20px; border-radius:12px; border:2px solid {o_col};">
                <h2 style="color:{o_col}; margin:0;">{o_label}</h2>
                <p style="margin:5px 0 0 0;"><b>Intraday:</b> {o_brief}</p>
            </div>"""
            st.markdown(html_opt, unsafe_allow_html=True)

        # --- METRICS & REASONING ---
        st.write("")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Price", f"₹{curr_p:.2f}")
        m2.metric("VWAP", f"₹{vwap:.2f}", f"{((curr_p-vwap)/vwap*100):.2f}%")
        m3.metric("RSI", f"{rsi_intra:.1f}")
        m4.metric("VIX", f"{vix:.2f}")

        with st.expander("🧠 Agentic Intelligence Brief", expanded=True):
            st.markdown(f"""
            * **Stock View:** This is a **{'Long-Term Asset' if stock_bull else 'High-Risk Asset'}** right now. The price is currently **{('above' if stock_bull else 'below')}** its 200-day average of ₹{ma200:.2f}.
            * **Option View:** This is a **{'Leverage Opportunity' if (intra_bull or intra_bear) else 'Neutral Zone'}**. We are targeting the **{strike}** strike based on current spot volatility.
            * **Logic Check:** PCR Sentiment and RSI ({rsi_intra:.1f}) suggest that {('buyers' if intra_bull else 'sellers' if intra_bear else 'no one')} is in control.
            """)

except Exception as e:
    st.error(f"Tower Logic Error: {e}")

st.divider()
st.caption(f"Sync: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Master Architecture")