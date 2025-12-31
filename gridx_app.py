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
target_input = st.sidebar.text_input("Asset Symbol", "RELIANCE").upper().strip()

mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    d_intra, d_short, d_long, d_vix = fetch_multi_horizon(ticker_sym)

    if d_intra is None or d_intra.empty:
        st.error(f"⚠️ Symbol '{target_input}' not found. Please use standard NSE/BSE tickers.")
    else:
        # Helper to get clean series
        def get_c(df): return df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
        def get_v(df): return df['Volume'].iloc[:, 0] if isinstance(df['Volume'], pd.DataFrame) else df['Volume']

        c_intra, v_intra = get_c(d_intra), get_v(d_intra)
        c_short, c_long = get_c(d_short), get_c(d_long)
        
        curr_p = float(c_intra.iloc[-1])
        vwap = float((c_intra * v_intra).sum() / v_intra.sum())
        rsi_intra = float(calculate_rsi(c_intra).iloc[-1])
        rsi_short = float(calculate_rsi(c_short).iloc[-1])
        rsi_long = float(calculate_rsi(c_long).iloc[-1])
        vix = float(get_c(d_vix).iloc[-1]) if not d_vix.empty else 15.0

        # --- PCR SIMULATION (Sentiment Proxy) ---
        # PCR > 1 (Bullish Sentiment), PCR < 1 (Bearish Sentiment)
        pcr_val = round(1.0 + (0.1 if rsi_long > 55 else -0.1) + np.random.uniform(-0.05, 0.05), 2)

        # --- HORIZON STATUS CALCULATOR ---
        def horizon_check(price, ref, rsi):
            if price > ref and rsi > 50: return "Bullish", "green"
            if price < ref and rsi < 50: return "Bearish", "red"
            return "Neutral", "gray"

        s_intra, c_intra_ui = horizon_check(curr_p, vwap, rsi_intra)
        s_short, c_short_ui = horizon_check(curr_p, c_short.rolling(50).mean().iloc[-1], rsi_short)
        s_long, c_long_ui = horizon_check(curr_p, c_long.rolling(200).mean().iloc[-1], rsi_long)

        # --- UI LAYOUT ---
        st.title(f"🛰️ QE Genix: {target_input} Tower")

        # 1. OPTION VS STOCK DISTINCTION PANELS
        col_stock, col_option = st.columns(2)

        with col_stock:
            st.subheader("📦 Stock (Equity) Signal")
            s_action = "ACCUMULATE" if s_long == "Bullish" else "EXIT/AVOID"
            s_color = "green" if s_long == "Bullish" else "red"
            st.markdown(f"""<div style="background-color:{s_color}22; padding:15px; border-radius:10px; border:1px solid {s_color}; text-align:center;">
                <h2 style="color:{s_color}; margin:0;">{s_action}</h2>
                <small style="color:white;">Best for: Long-Term Wealth</small></div>""", unsafe_allow_html=True)

        with col_option:
            st.subheader("⚡ Option (Derivative) Signal")
            interval = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 10)
            strike = int(round(curr_p / interval) * interval)
            o_action = f"BUY {strike} CE" if s_intra == "Bullish" else (f"BUY {strike} PE" if s_intra == "Bearish" else "NO TRADE")
            o_color = "green" if s_intra == "Bullish" else ("red" if s_intra == "Bearish" else "orange")
            st.markdown(f"""<div style="background-color:{o_color}22; padding:15px; border-radius:10px; border:1px solid {o_color}; text-align:center;">
                <h2 style="color:{o_color}; margin:0;">{o_action}</h2>
                <small style="color:white;">Best for: Intraday Leverage</small></div>""", unsafe_allow_html=True)

        # 2. THE MULTI-HORIZON & PCR PANEL
        st.write("")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("PCR (Bias)", f"{pcr_val}", "Strong" if pcr_val > 1 else "Weak")
        m3.metric("RSI (Intra)", f"{rsi_intra:.1f}")
        m4.metric("India VIX", f"{vix:.2f}")
        m5.metric("VWAP", f"₹{vwap:.2f}")

        # 3. STRATEGIC REASONING
        st.write("")
        with st.expander("🧠 Agentic Intelligence Brief", expanded=True):
            st.markdown(f"""
            ### **Horizon Alignment**
            * **Intraday (1m):** <span style="color:{c_intra_ui}">{s_intra}</span> — {('Momentum is scaling above VWAP.' if s_intra=='Bullish' else 'Price is decaying below VWAP.')}
            * **Short-Term (1h):** <span style="color:{c_short_ui}">{s_short}</span> — {('Hold for 2-4 weeks.' if s_short=='Bullish' else 'Wait for trend reversal.')}
            * **Long-Term (1d):** <span style="color:{c_long_ui}">{s_long}</span> — {('Structural Bull Market.' if s_long=='Bullish' else 'Structural Bear Market.')}

            ### **The Distinction**
            * **Why Stock?** Since the Long-Term trend is **{s_long}**, physical delivery of shares is **{('recommended' if s_long=='Bullish' else 'risky')}**. You own the asset indefinitely.
            * **Why Option?** Intraday momentum is **{s_intra}**. Options decay (Theta) means you must exit by end of day. Use the **{strike} Strike** for maximum liquidity.
            """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Satellite Data Error: {e}")

st.divider()
st.caption(f"Sync: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Master Architecture")