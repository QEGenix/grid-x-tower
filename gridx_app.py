import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Grid-x 2.0 India (FnO)", layout="wide")

def format_indian_ticker(symbol):
    symbol = symbol.upper().strip()
    # Special handling for common indices
    indices = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "FINNIFTY": "NIFTY_FIN_SERVICE.NS"}
    if symbol in indices:
        return indices[symbol]
    if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        return f"{symbol}.NS"
    return symbol

def get_strike_suggestion(current_price, pcr, iv_mean):
    """Suggests OTM strikes based on market sentiment."""
    # Common Nifty/Stock strike step sizes
    step = 50 if current_price > 10000 else 100 if current_price > 20000 else 5
    atm_strike = round(current_price / step) * step
    
    if pcr > 1.1: # Bullish setup
        suggestion = {
            "Action": "BULLISH (Sell Put / Buy Call)",
            "Call Strike": atm_strike + step,
            "Put Strike": atm_strike - step
        }
    elif pcr < 0.9: # Bearish setup
        suggestion = {
            "Action": "BEARISH (Sell Call / Buy Put)",
            "Call Strike": atm_strike + step,
            "Put Strike": atm_strike - step
        }
    else:
        suggestion = {"Action": "NEUTRAL (Rangebound Grid)", "Call Strike": atm_strike + step, "Put Strike": atm_strike - step}
    return suggestion

# --- UI ARCHITECTURE ---
st.title("🇮🇳 Agentic Control Tower: India FnO")
st.markdown("---")

# Sidebar - Target Inputs
with st.sidebar:
    st.header("🎯 Target Parameters")
    raw_symbol = st.text_input("Enter NSE Ticker", "NIFTY")
    ticker = format_indian_ticker(raw_symbol)
    lookback = st.selectbox("Lookback Period", ["1d", "5d", "1mo"])
    run_mission = st.button("🚀 INITIALIZE SCAN")

if run_mission:
    try:
        # 1. DATA ACQUISITION
        stock_obj = yf.Ticker(ticker)
        hist = stock_obj.history(period="5d")
        current_price = hist['Close'].iloc[-1]
        
        # 2. OPTION CHAIN SENSORS
        expiries = stock_obj.options
        if expiries:
            nearest_expiry = expiries[0]
            chain = stock_obj.option_chain(nearest_expiry)
            
            # PCR Calculation (Open Interest based)
            total_call_oi = chain.calls['openInterest'].sum()
            total_put_oi = chain.puts['openInterest'].sum()
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0
            
            # IV Radar
            avg_iv = chain.calls['impliedVolatility'].mean() * 100
            
            # Strike Suggestion Logic
            plan = get_strike_suggestion(current_price, pcr, avg_iv)
            
            # --- DASHBOARD RENDERING ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("LTP", f"₹{current_price:,.2f}")
            m2.metric("PCR (OI)", f"{pcr:.2f}")
            m3.metric("Avg IV", f"{avg_iv:.1f}%")
            m4.metric("Expiry", nearest_expiry)
            
            # TACTICAL GRID
            st.subheader("🛠️ Tactical Strike Plan")
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"**Strategy:** {plan['Action']}")
                st.success(f"**Target Call Strike:** {plan['Call Strike']}")
            with col_b:
                st.warning(f"**Target Put Strike:** {plan['Put Strike']}")
                
            # HEATMAP TABLE
            st.subheader("🔥 Option Chain Pulse (Calls)")
            st.dataframe(chain.calls[['strike', 'lastPrice', 'change', 'openInterest', 'impliedVolatility']].head(10), use_container_width=True)
            
        else:
            st.error("No Option Data available for this ticker. Ensure it is an FnO-listed stock.")
            
    except Exception as e:
        st.error(f"Mission Failed: {str(e)}")

st.markdown("---")
st.caption("Data source: Yahoo Finance India. Delays of 15 mins may apply during live market hours.")