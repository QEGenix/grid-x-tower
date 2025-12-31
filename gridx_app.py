import streamlit as st
import requests
import pandas as pd
import time

# --- SESSION & HEADER CONFIGURATION ---
# This mimics a real browser to prevent "401 Unauthorized" errors
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': '*/*',
    'Connection': 'keep-alive'
}

class NSEPortal:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.base_url = "https://www.nseindia.com"
        # Initial visit to get cookies
        try:
            self.session.get(self.base_url, timeout=10)
        except:
            st.error("❌ Could not connect to NSE. Please check your internet.")

    def get_option_chain(self, symbol):
        # Determine if it's an index or a stock scrip
        indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        if symbol.upper() in indices:
            url = f"{self.base_url}/api/option-chain-indices?symbol={symbol.upper()}"
        else:
            url = f"{self.base_url}/api/option-chain-equities?symbol={symbol.upper()}"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except:
            return None

# --- UI ARCHITECTURE ---
st.set_page_config(page_title="Grid-x NSE Tower", layout="wide")
st.title("🇮🇳 Agentic Control Tower: NSE Direct")

# Initialize NSE Session
if 'nse' not in st.session_state:
    st.session_state.nse = NSEPortal()

with st.sidebar:
    st.header("🎯 Mission Parameters")
    target = st.text_input("Enter NSE Symbol (NIFTY / RELIANCE / TCS)", "NIFTY")
    if st.button("🚀 INITIALIZE SCAN"):
        st.session_state.run_scan = True
    else:
        st.session_state.run_scan = False

if st.session_state.get('run_scan'):
    with st.spinner(f"Establishing Secure Link to NSE for {target}..."):
        data = st.session_state.nse.get_option_chain(target)
        
        if data:
            # 1. Perception: Basic Info
            ltp = data['records']['underlyingValue']
            expiry = data['records']['expiryDates'][0] # Nearest Expiry
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Underlying Price", f"₹{ltp:,.2f}")
            m2.metric("Expiry Tracked", expiry)
            m3.metric("Status", "🟢 LIVE")

            # 2. Logic: Process Option Chain
            raw_rows = data['records']['data']
            processed_data = []
            for item in raw_rows:
                if item['expiryDate'] == expiry:
                    strike = item['strikePrice']
                    ce_oi = item.get('CE', {}).get('openInterest', 0)
                    pe_oi = item.get('PE', {}).get('openInterest', 0)
                    
                    processed_data.append({
                        "Strike": strike,
                        "Call OI": ce_oi,
                        "Put OI": pe_oi,
                        "LTP (Call)": item.get('CE', {}).get('lastPrice', 0),
                        "LTP (Put)": item.get('PE', {}).get('lastPrice', 0)
                    })

            df = pd.DataFrame(processed_data).sort_values("Strike")
            
            # 3. Strategy: Call/Put Wall Detection
            st.subheader("🛠️ Tactical Strike Radar")
            # Filter for strikes near the current price
            buffer = 200 if "NIFTY" in target else 50
            near_atm = df[(df['Strike'] >= ltp - buffer) & (df['Strike'] <= ltp + buffer)]
            
            st.table(near_atm)
            
            # 4. Agentic Suggestion
            total_call_oi = df['Call OI'].sum()
            total_put_oi = df['Put OI'].sum()
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            st.info(f"**Agentic Sentiment:** PCR is **{pcr:.2f}**. " + 
                    ("Bullish momentum detected." if pcr > 1 else "Market showing resistance."))
        else:
            st.error(f"🔴 NSE Error: '{target}' may not be in the FnO segment or session expired.")

st.divider()
st.caption("Data provided via secure session handshake with nseindia.com. Use for educational purposes.")