import streamlit as st
import yfinance as yf
from groq import Groq
import pandas as pd

# --- SYSTEM INITIALIZATION ---
st.set_page_config(page_title="Grid-x 2.0 India", layout="wide")

def format_indian_ticker(symbol):
    """Ensures the ticker is ready for NSE/BSE sensors."""
    symbol = symbol.upper().strip()
    if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
        # Defaulting to NSE as it has higher liquidity for Options
        return f"{symbol}.NS"
    return symbol

def fetch_indian_options(ticker_symbol):
    """Fetches the Option Chain for Indian FnO stocks."""
    try:
        stock = yf.Ticker(ticker_symbol)
        expiries = stock.options
        if not expiries:
            return None, "No Options found. Ensure the stock is in the FnO list."
        
        # Get the nearest expiry (current month)
        chain = stock.option_chain(expiries[0])
        return chain, expiries[0]
    except Exception as e:
        return None, str(e)

# --- THE PERCEPTION LAYER (GROQ) ---
def get_sentiment_analysis(symbol, headlines):
    if not headlines:
        return 0, "NEUTRAL (No recent news found on Yahoo Finance India)"
    
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    news_block = "\n".join(headlines[:5]) # Top 5 headlines
    
    prompt = f"Analyze these Indian market headlines for {symbol}: {news_block}. Return a score from -1 to 1 and a 10-word summary."
    # ... Groq Chat Completion logic here ...
    return 0.8, "Bullish momentum seen in Indian Bluechips." # Placeholder

# --- UI ARCHITECTURE ---
st.title("🛰️ Agentic Control Tower: India Edition")
st.sidebar.header("Target Selection")

raw_symbol = st.sidebar.text_input("NSE Symbol (e.g., RELIANCE, NIFTY_50)", "RELIANCE")
symbol = format_indian_ticker(raw_symbol)

if st.sidebar.button("🚀 START MISSION"):
    with st.spinner(f"Scanning {symbol}..."):
        # 1. Price Data
        data = yf.download(symbol, period="5d", interval="15m")
        current_price = data['Close'].iloc[-1]
        
        # 2. Options Pulse
        chain, expiry = fetch_indian_options(symbol)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"₹{current_price:,.2f}")
        with col2:
            st.metric("Market", "NSE (India)")
        with col3:
            st.metric("Expiry Tracked", expiry if expiry else "N/A")

        # 3. Sentiment & Grid Strategy
        st.subheader("📊 Tactical Analysis")
        if chain:
            # Show Call vs Put Open Interest (Simplified)
            calls_oi = chain.calls['openInterest'].sum()
            puts_oi = chain.puts['openInterest'].sum()
            pcr = puts_oi / calls_oi if calls_oi > 0 else 0
            
            st.write(f"**Put-Call Ratio (PCR):** {pcr:.2f}")
            if pcr > 1:
                st.success("Target Status: BULLISH (High Put Writing detected)")
            else:
                st.warning("Target Status: CAUTIOUS (Call Resistance ahead)")
            
            # Show the Option Chain Table
            st.dataframe(chain.calls[['strike', 'lastPrice', 'openInterest']].head(5), use_container_width=True)
        else:
            st.info("This ticker is not in the FnO segment. Running Equity-only analysis.")