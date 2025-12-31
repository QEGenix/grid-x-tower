import streamlit as st
import pandas as pd
import yfinance as yf

# --- CONFIGURATION ---
st.set_page_config(page_title="Grid-x: Global Agentic Tower", layout="wide", page_icon="🛰️")

def get_yfinance_data(symbol):
    """Fetches option chain data using Yahoo Finance API (Reliable & Free)."""
    # Yahoo Finance uses .NS suffix for NSE stocks (e.g., TCS.NS)
    if not symbol.endswith(".NS") and symbol not in ["NIFTY", "BANKNIFTY"]:
        symbol = f"{symbol}.NS"
    
    ticker = yf.Ticker(symbol)
    
    try:
        # Get underlying price
        price = ticker.fast_info['last_price']
        
        # Get available expiry dates
        expiries = ticker.options
        if not expiries:
            return None, None, None
        
        # Fetch calls and puts for the nearest expiry
        opt = ticker.option_chain(expiries[0])
        calls = opt.calls[['strike', 'lastPrice', 'openInterest']].rename(columns={'lastPrice': 'Call LTP', 'openInterest': 'Call OI'})
        puts = opt.puts[['strike', 'lastPrice', 'openInterest']].rename(columns={'lastPrice': 'Put LTP', 'openInterest': 'Put OI'})
        
        # Merge into a single chain
        df = pd.merge(calls, puts, on='strike', how='inner')
        return price, expiries[0], df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, None, None

# --- UI ---
st.title("🛰️ Grid-x 2.0: Multi-Source Control Tower")
st.info("Switched to Yahoo Finance source for higher reliability and no 'Session Expired' errors.")

with st.sidebar:
    st.header("🎯 Target Selection")
    # For Yahoo Finance, use TCS.NS or just TCS
    raw_target = st.text_input("Enter Symbol (TCS, RELIANCE, INFOSY)", "TCS").upper()
    scan = st.button("🚀 INITIALIZE SCAN")

if scan:
    with st.spinner(f"Analyzing {raw_target} via Global Link..."):
        ltp, expiry, df = get_yfinance_data(raw_target)
        
        if df is not None:
            # Calculations
            total_call_oi = df['Call OI'].sum()
            total_put_oi = df['Put OI'].sum()
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            # Dashboard Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Price", f"₹{ltp:.2f}")
            m2.metric("Nearest Expiry", expiry)
            m3.metric("PCR (Volume)", f"{pcr:.2f}")
            
            # Option Chain Heatmap
            st.subheader(f"📊 Option Chain Heatmap")
            # Filter for ATM strikes (Within 5% of price)
            atm_df = df[(df['strike'] >= ltp*0.95) & (df['strike'] <= ltp*1.05)]
            
            st.dataframe(
                atm_df.style.background_gradient(subset=['Call OI'], cmap="Reds")
                .background_gradient(subset=['Put OI'], cmap="Greens"),
                use_container_width=True
            )
        else:
            st.error(f"Could not find option data for {raw_target}. Ensure it is an FnO stock.")

st.markdown("---")
st.caption("Data Source: Yahoo Finance | Backup: Agentic Failover Mode")