import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

# --- SYSTEM CONFIG ---
st.set_page_config(page_title="Grid-x Agentic Tower", layout="wide", page_icon="🛰️")

def fetch_tower_data(symbol):
    """Hybrid Data Engine: Reliable Price + Option Chain Logic"""
    # Force .NS suffix for Yahoo Finance
    ticker_sym = f"{symbol.upper().strip()}.NS"
    ticker = yf.Ticker(ticker_sym)
    
    try:
        # 1. Reliable Price Feed
        price = ticker.fast_info['last_price']
        
        # 2. Option Chain Fetch
        expiries = ticker.options
        if not expiries:
            return price, None, None
            
        target_expiry = expiries[0]
        chain = ticker.option_chain(target_expiry)
        
        calls = chain.calls[['strike', 'lastPrice', 'openInterest']].rename(columns={'lastPrice': 'CE Price', 'openInterest': 'CE OI'})
        puts = chain.puts[['strike', 'lastPrice', 'openInterest']].rename(columns={'lastPrice': 'PE Price', 'openInterest': 'PE OI'})
        
        df = pd.merge(calls, puts, on='strike', how='inner').fillna(0)
        return price, target_expiry, df
    except:
        return None, None, None

# --- UI ARCHITECTURE ---
st.title("🛰️ Grid-x: Agentic Control Tower")
st.markdown(f"**System Status:** `Active` | **Date:** {datetime.date.today()}")

with st.sidebar:
    st.header("🎯 Mission Parameters")
    target = st.text_input("NSE Symbol (e.g., TCS, RELIANCE, NIFTY)", "TCS").upper()
    scan = st.button("🚀 INITIALIZE SCAN")
    st.divider()
    st.caption("Using Hybrid Data Feed (Yahoo Finance + NSE Bridge)")

if scan:
    with st.spinner(f"Establishing Link to {target}..."):
        price, expiry, df = fetch_tower_data(target)
        
        if price:
            # Layout Row 1: Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric(f"{target} Price", f"₹{price:.2f}")
            
            if df is not None and not df.empty:
                col2.metric("Expiry Date", expiry)
                
                # Logic: Sentiment Analysis (PCR)
                total_ce = df['CE OI'].sum()
                total_pe = df['PE OI'].sum()
                pcr = total_pe / total_ce if total_ce > 0 else 0
                col3.metric("PCR (Sentiment)", f"{pcr:.2f}")
                
                # Strategy Alert
                if pcr > 1.2:
                    st.success("🟢 **Bullish Momentum:** Strong Put writing (Support) detected.")
                elif pcr < 0.8:
                    st.error("🔴 **Bearish Pressure:** Heavy Call writing (Resistance) detected.")
                else:
                    st.warning("🟡 **Neutral/Sideways:** Market participants are balanced.")

                # Layout Row 2: The Heatmap
                st.subheader("🔥 Option Chain Heatmap (ATM ±5%)")
                # Filter for strikes near the spot price
                atm_mask = (df['strike'] >= price * 0.95) & (df['strike'] <= price * 1.05)
                
                # Apply conditional formatting for scannability
                st.dataframe(
                    df[atm_mask].style.background_gradient(subset=['CE OI'], cmap="Reds")
                    .background_gradient(subset=['PE OI'], cmap="Greens"),
                    use_container_width=True
                )
            else:
                st.warning(f"⚠️ Live price found, but the Option Chain for {target} is restricted via API.")
                st.info(f"👉 **[Click here for Live Verified Option Chain for {target}](https://www.niftytrader.in/nse-option-chain/{target.lower()})**")
        else:
            st.error(f"🔴 Mission Failed: Symbol '{target}' not found. Ensure it's a valid NSE stock.")

st.divider()
st.caption("Agentic Tower Architecture: Core Intent Layer (yfinance) | Execution Layer (Streamlit)")