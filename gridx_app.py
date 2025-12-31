import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Grid-x: NSE Agentic Tower", layout="wide", page_icon="🛰️")

class NSEAgent:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.nseindia.com/option-chain',
            'Connection': 'keep-alive'
        }
        self.session.headers.update(self.headers)

    def refresh_session(self):
        """Standard NSE handshake to get live cookies."""
        try:
            # Hit the main site first
            self.session.get("https://www.nseindia.com", timeout=10)
            # Hit the option chain page to ensure we have the right tracking cookies
            self.session.get("https://www.nseindia.com/option-chain", timeout=10)
            return True
        except:
            return False

    def fetch_data(self, symbol):
        symbol = symbol.upper().strip()
        is_index = symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}" if is_index else \
              f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
        
        try:
            # First attempt
            response = self.session.get(url, timeout=10)
            
            # If rejected (401/403), refresh and try one last time
            if response.status_code in [401, 403]:
                self.refresh_session()
                time.sleep(1)
                response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

# --- UI LOGIC ---
st.title("🛰️ Agentic Control Tower: NSE Live")

if 'agent' not in st.session_state:
    st.session_state.agent = NSEAgent()

with st.sidebar:
    st.header("🎯 Mission Parameters")
    target = st.text_input("NSE Symbol (TCS, RELIANCE, NIFTY)", "TCS")
    if st.button("🚀 INITIALIZE SCAN"):
        st.session_state.run_scan = True

if st.session_state.get('run_scan'):
    with st.spinner(f"Establishing Secure Link for {target}..."):
        # We refresh the session every time the button is clicked
        st.session_state.agent.refresh_session()
        data = st.session_state.agent.fetch_data(target)
        
        if data and 'records' in data:
            ltp = data['records'].get('underlyingValue', 0)
            expiry = data['records'].get('expiryDates', [None])[0]
            
            if expiry:
                # Process only the nearest expiry
                rows = []
                for item in data['records'].get('data', []):
                    if item.get('expiryDate') == expiry:
                        c, p = item.get('CE', {}), item.get('PE', {})
                        rows.append({
                            "Strike": item.get('strikePrice'),
                            "Call OI": c.get('openInterest', 0),
                            "Put OI": p.get('openInterest', 0),
                            "Call LTP": c.get('lastPrice', 0),
                            "Put LTP": p.get('lastPrice', 0)
                        })
                
                df = pd.DataFrame(rows).sort_values("Strike")
                
                # Visuals
                c1, c2 = st.columns(2)
                c1.metric(f"{target} LTP", f"₹{ltp}")
                c2.metric("Expiry", expiry)
                
                st.subheader(f"🔥 Option Chain: {expiry}")
                # Show strikes near the ATM (At-the-money)
                atm_filter = df[(df['Strike'] >= ltp*0.95) & (df['Strike'] <= ltp*1.05)]
                st.dataframe(atm_filter.style.background_gradient(cmap="RdYlGn", subset=['Put OI']), use_container_width=True)
            else:
                st.error("No active contracts found.")
        else:
            st.error("🔴 Mission Failed: Session rejected by NSE. Try clicking the button again in 10 seconds.")