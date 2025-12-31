import streamlit as st
import requests
import pandas as pd
import time

# --- ROBUST NSE SESSION MANAGER ---
class NSEAgent:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.refresh_session()

    def refresh_session(self):
        """Visits the homepage to grab fresh cookies."""
        try:
            self.session.get("https://www.nseindia.com", timeout=10)
        except Exception as e:
            st.error(f"Failed to reach NSE: {e}")

    def fetch_option_chain(self, symbol):
        symbol = symbol.upper().strip()
        indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        
        # Determine the correct API endpoint
        if symbol in indices:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        else:
            url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
        
        try:
            response = self.session.get(url, timeout=10)
            # If session expired (401), refresh once and retry
            if response.status_code == 401:
                self.refresh_session()
                response = self.session.get(url, timeout=10)
                
            if response.status_code == 200:
                return response.json()
            else:
                st.warning(f"NSE returned status code {response.status_code}. The symbol '{symbol}' might not be in FnO.")
                return None
        except Exception as e:
            st.error(f"Data fetch error: {e}")
            return None

# --- UI ARCHITECTURE ---
st.set_page_config(page_title="NSE Agentic Tower", layout="wide")
st.title("🛰️ Agentic Control Tower: NSE Live")

if 'agent' not in st.session_state:
    st.session_state.agent = NSEAgent()

with st.sidebar:
    st.header("🎯 Target Selection")
    target = st.text_input("NSE Symbol (e.g. TCS, RELIANCE, NIFTY)", "TCS")
    if st.button("🚀 INITIALIZE SCAN"):
        st.session_state.scan_active = True

if st.session_state.get('scan_active'):
    with st.spinner(f"Establishing Link for {target}..."):
        data = st.session_state.agent.fetch_option_chain(target)
        
        if data:
            ltp = data['records']['underlyingValue']
            expiry = data['records']['expiryDates'][0]
            
            # --- DASHBOARD ---
            c1, c2 = st.columns(2)
            c1.metric(f"{target} Price", f"₹{ltp:,.2f}")
            c2.metric("Target Expiry", expiry)
            
            # Process Data
            rows = []
            for item in data['records']['data']:
                if item['expiryDate'] == expiry:
                    rows.append({
                        "Strike": item['strikePrice'],
                        "Call OI": item.get('CE', {}).get('openInterest', 0),
                        "Put OI": item.get('PE', {}).get('openInterest', 0),
                        "IV": item.get('CE', {}).get('impliedVolatility', 0)
                    })
            
            df = pd.DataFrame(rows).sort_values("Strike")
            
            # Filter for ATM Strikes (Price +/- 5%)
            buffer = ltp * 0.05
            atm_view = df[(df['Strike'] >= ltp - buffer) & (df['Strike'] <= ltp + buffer)]
            
            st.subheader("🔥 Option Chain Heatmap")
            st.dataframe(atm_view, use_container_width=True)
            
            # Agentic Logic
            pcr = df['Put OI'].sum() / df['Call OI'].sum() if df['Call OI'].sum() > 0 else 0
            st.info(f"**Agentic Insight:** PCR is **{pcr:.2f}**. " + 
                    ("Support is building." if pcr > 1.1 else "Resistance is strong."))
        else:
            st.error(f"Mission Failed. Verify '{target}' is an FnO stock (like TCS, INFY, RELIANCE).")