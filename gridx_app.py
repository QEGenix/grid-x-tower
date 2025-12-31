import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_autorefresh import st_autorefresh
import datetime

# --- 1. SYSTEM PULSE ---
st_autorefresh(interval=60 * 1000, key="gridx_pulse")
st.set_page_config(page_title="Grid-x Decision Engine", layout="wide")

# --- 2. THE SMART MAPPER ---
def resolve_ticker(user_input):
    mapping = {
        "NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN",
        "FINNIFTY": "NIFTY_FIN_SERVICE.NS", "MIDCAP": "^NSEMDCP50"
    }
    val = user_input.upper().strip()
    if val in mapping: return mapping[val]
    if val.startswith("^") or "." in val: return val
    return f"{val}.NS"

# --- 3. PREDICTION & SIGNAL LOGIC ---
def get_trade_signals(price, pivot, s1, r1):
    """Generates Buy/Sell logic based on current price position."""
    if price > r1:
        return "🔴 SELL / OVERBOUGHT", "Price is above Resistance. High risk of reversal. Book profits."
    elif price < s1:
        return "🟢 BUY / OVERSOLD", "Price is at Support. High probability of bounce. Enter Long."
    elif price > pivot:
        return "🟡 HOLD / BULLISH", "Strong momentum. Stay in trade, but don't enter fresh here."
    else:
        return "⚪ WAIT / BEARISH", "Price is below Pivot. Wait for a clear reversal signal."

# --- 4. THE CONTROL TOWER UI ---
st.title("🛰️ Grid-x 2.0: Decision Engine")
target_input = st.sidebar.text_input("Enter Symbol (e.g. NIFTY, TCS, ^BSESN)", "NIFTY")
ticker_sym = resolve_ticker(target_input)

try:
    # Fetching 2 days to get a reliable 'yesterday' close and 'today' open
    data = yf.download(ticker_sym, period="2d", interval="1m", progress=False)
    
    if not data.empty:
        curr_price = data['Close'].iloc[-1]
        day_high = data['High'].max()
        day_low = data['Low'].min()
        
        # Calculate Tactical Levels
        pivot = (day_high + day_low + curr_price) / 3
        r1 = (2 * pivot) - day_low
        s1 = (2 * pivot) - day_high
        
        # 🏯 P&L WAR ROOM
        m1, m2, m3 = st.columns(3)
        m1.metric(f"LIVE: {target_input}", f"₹{curr_price:.2f}")
        
        # ⚡ LIVE PREDICTION SIGNAL
        signal, advice = get_trade_signals(curr_price, pivot, s1, r1)
        m2.metric("CURRENT SIGNAL", signal)
        m3.metric("PIVOT LEVEL", f"₹{pivot:.2f}")

        st.info(f"💡 **Agent Advice:** {advice}")

        # 📊 TACTICAL EXECUTION GRID (Stocks)
        st.subheader("🎯 Tactical Execution (Equity/Cash)")
        exec_df = pd.DataFrame({
            "Action Type": ["Entry Zone (Buy)", "Exit Zone (Target)", "Hard Stop Loss"],
            "Price": [f"₹{s1:.2f}", f"₹{r1:.2f}", f"₹{s1 * 0.995:.2f}"],
            "Logic": ["Near Daily Support", "Near Daily Resistance", "0.5% below Support"]
        })
        st.table(exec_df)

        # 💎 OPTIONS STRATEGY GRID
        st.subheader("💎 Agentic Options Strategy (Next 60 Mins)")
        atm = round(curr_price / 50) * 50 if "NIFTY" in ticker_sym else round(curr_price / 100) * 100
        
        opt_logic = "BULLISH" if curr_price > pivot else "BEARISH"
        rec_strike = f"{atm + 50} CE" if opt_logic == "BULLISH" else f"{atm - 50} PE"
        
        st.write(f"**Market Sentiment:** {opt_logic} | **Recommended Action:** Buy {rec_strike}")

    else:
        st.error(f"📡 Link Failed: '{ticker_sym}' not found. Please verify the ticker.")

except Exception as e:
    st.error(f"System Error: {e}")

st.caption(f"Last Pulse: {datetime.datetime.now().strftime('%H:%M:%S')}")