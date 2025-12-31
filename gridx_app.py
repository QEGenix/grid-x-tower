import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. CORE SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x 2.0: Clarity Tower", layout="wide")
st_autorefresh(interval=120 * 1000, key="gridx_heartbeat")

# --- 2. DATA SATELLITE ---
@st.cache_data(ttl=120)
def fetch_tower_data(ticker_sym):
    try:
        data_stock = yf.download(ticker_sym, period="1d", interval="1m", progress=False, auto_adjust=True)
        data_vix = yf.download("^INDIAVIX", period="1d", interval="1m", progress=False, auto_adjust=True)
        return data_stock, data_vix
    except:
        return None, None

def calculate_rsi(series, window=14):
    if len(series) < window: return 50
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)

# --- 3. UI RENDERER ---
st.sidebar.title("🛡️ Safety Pilot")
target_input = st.sidebar.text_input("Asset Symbol", "PNB").upper().strip()

mapping = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN"}
ticker_sym = mapping.get(target_input, f"{target_input}.NS")

try:
    stock_raw, vix_raw = fetch_tower_data(ticker_sym)

    if stock_raw is None or stock_raw.empty or len(stock_raw) < 2:
        st.warning(f"📡 Scanning Satellite for '{target_input}'...")
    else:
        closes = stock_raw['Close'].iloc[:, 0] if isinstance(stock_raw['Close'], pd.DataFrame) else stock_raw['Close']
        volumes = stock_raw['Volume'].iloc[:, 0] if isinstance(stock_raw['Volume'], pd.DataFrame) else stock_raw['Volume']
        
        curr_p = float(closes.iloc[-1])
        vwap = float((closes * volumes).sum() / volumes.sum())
        current_rsi = float(calculate_rsi(closes).iloc[-1])
        
        # Fixed VIX extraction
        vix = 15.0
        if vix_raw is not None and not vix_raw.empty:
            vix_closes = vix_raw['Close'].iloc[:, 0] if isinstance(vix_raw['Close'], pd.DataFrame) else vix_raw['Close']
            if len(vix_closes) > 0: vix = float(vix_closes.iloc[-1])

        # --- REFINED SIGNAL LOGIC ---
        diff_pct = ((curr_p - vwap) / vwap) * 100
        
        # Bullish: Price > VWAP + Buffer AND RSI is strengthening
        is_bullish = diff_pct > 0.15 and 50 < current_rsi < 70
        # Bearish: Price < VWAP - Buffer AND RSI is weakening
        is_bearish = diff_pct < -0.15 and 30 < current_rsi < 50
        
        interval = 50 if "NSEI" in ticker_sym else (100 if "NSEBANK" in ticker_sym else 5 if curr_p < 200 else 10)
        atm_strike = int(round(curr_p / interval) * interval)

        st.title(f"🛰️ Grid-x 2.0: {target_input} Tower")

        # --- DYNAMIC SIGNAL BANNER (CLARITY FIX) ---
        if is_bullish:
            header_label = "🟢 BULLISH TREND DETECTED"
            action_instr = f"Action: BUY {atm_strike} CALL (CE)"
            color = "green"
            m_state = f"Upside Breakout: Price is trading {diff_pct:.2f}% above institutional average."
            m_trend = f"Momentum: RSI at {current_rsi:.1f} confirms aggressive buying interest."
            m_exec = f"Execution: Enter {atm_strike} CE. Target next resistance levels."
        elif is_bearish:
            header_label = "🔴 BEARISH TREND DETECTED"
            action_instr = f"Action: BUY {atm_strike} PUT (PE)"
            color = "red"
            m_state = f"Downward Breakdown: Price has dropped {abs(diff_pct):.2f}% below VWAP."
            m_trend = f"Momentum: RSI at {current_rsi:.1f} shows heavy selling (Distribution)."
            m_exec = f"Execution: Enter {atm_strike} PE to profit from the falling price."
        else:
            header_label = "🟡 NEUTRAL / CONFLICT"
            action_instr = "Action: NO TRADE (Wait for Breakout)"
            color = "orange"
            m_state = f"Market State: Price is stuck in a tight range ({diff_pct:.2f}% from VWAP)."
            m_trend = f"Momentum: RSI at {current_rsi:.1f} is neutral. No clear winner yet."
            m_exec = "Execution: Awaiting price to clear the 'No-Trade' chop zone."

        # Display the Header and Instruction clearly
        st.markdown(f"""
            <div style="background-color:{color}22; padding:20px; border-radius:12px; border:2px solid {color}; text-align:center;">
                <h2 style="color:{color}; margin:0;">{header_label}</h2>
                <h1 style="color:{color}; margin:10px 0;">{action_instr}</h1>
            </div>
        """, unsafe_allow_html=True)

        # --- AGENTIC INTELLIGENCE BRIEF ---
        st.write("")
        st.markdown(f"""
        <div style="background-color:rgba(255,255,255,0.05); padding:20px; border-radius:10px; border-left: 8px solid {color};">
            <h4 style="margin-top:0; color:{color};">🧠 Agentic Intelligence Brief</h4>
            <p style="margin-bottom:8px;"><b>1. Price Action:</b> {m_state}</p>
            <p style="margin-bottom:8px;"><b>2. Strength Analysis:</b> {m_trend}</p>
            <p style="margin-bottom:0;"><b>3. Pilot Instruction:</b> {m_exec}</p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Price", f"₹{curr_p:.2f}")
        m2.metric("VWAP (Fair)", f"₹{vwap:.2f}", f"{diff_pct:.2f}%")
        m3.metric("RSI (14m)", f"{current_rsi:.1f}")
        m4.metric("India VIX", f"{vix:.2f}")

except Exception as e:
    st.info("📡 Scanning Satellite Feed... Please check ticker symbol.")

st.divider()
st.caption(f"Sync: {datetime.datetime.now().strftime('%H:%M:%S')} | QE Genix Architecture")