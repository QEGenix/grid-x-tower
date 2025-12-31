import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Grid-x: NSE Agentic Tower", layout="wide", page_icon="🛰️")

class NSEAgent:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def refresh_session(self):
        """Forcefully establish a fresh NSE session by hitting the main landing pages."""
        try:
            # Step 1: Hit main site
            self.session.get("https://www.nseindia.com", timeout=10)
            time.sleep(1)
            # Step 2: Hit option chain landing page to trigger specific cookies
            self.session.get("https://www.nseindia.com/option-chain", timeout=10)
            return True
        except:
            return False

    def fetch_option_chain(self, symbol):
        symbol = symbol.upper().strip()
        indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        
        # Decide endpoint
        if symbol in indices:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        else:
            url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
        
        # Try fetching with automatic retry on 401
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code in [401, 403]:
                self.refresh_session()
                time.sleep(1)
                response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

# --- CORE LOGIC: MAX PAIN ---
def calculate_max_pain(df):
    if df.empty: return 0
    strikes = df['Strike'].tolist()
    losses = []
    for s in strikes:
        call_loss = df[df['Strike'] < s].apply(lambda x: (s - x['Strike']) * x['Call OI'], axis=1).sum()
        put_loss = df[df['Strike'] > s].apply(lambda x: (x['Strike'] - s) * x['Put OI'], axis=1).sum()
        losses.append(call_loss + put_loss)
    return strikes[losses.index(min(losses))]

# --- DASHBOARD UI ---
st.title("🛰️ Grid-x 2.0: Agentic Control Tower")

if 'agent' not in st.session_state:
    st.session_state.agent = NSEAgent()

with st.sidebar:
    st.header("🎯 Mission Parameters")
    target = st.text_input("Enter Symbol (TCS, RELIANCE, NIFTY)", "TCS")
    scan = st.button("🚀 INITIALIZE SCAN")

if scan:
    with st.spinner(f"Connecting to Agentic Tower for {target}..."):
        # Force a refresh before every fresh scan to prevent 'Session Expired'
        st.session_state.agent.refresh_session()
        data = st.session_state.agent.fetch_option_chain(target)
        
        if data and 'records' in data:
            ltp = data['records'].get('underlyingValue', 0)
            expiry_dates = data['records'].get('expiryDates', [])
            
            if not expiry_dates:
                st.error("No active contracts found for this symbol.")
            else:
                expiry = expiry_dates[0]
                raw_data = data['records'].get('data', [])
                
                rows = []
                for item in raw_data:
                    if item.get('expiryDate') == expiry:
                        ce = item.get('CE', {})
                        pe = item.get('PE', {})
                        rows.append({
                            "Strike": item.get('strikePrice'),
                            "Call OI": ce.get('openInterest', 0),
                            "Put OI": pe.get('openInterest', 0),
                            "Call Price": ce.get('lastPrice', 0),
                            "Put Price": pe.get('lastPrice', 0)
                        })
                
                df = pd.DataFrame(rows).sort_values("Strike")
                
                # Metrics
                max_pain = calculate_max_pain(df)
                pcr = df['Put OI'].sum() / df['Call OI'].sum() if df['Call OI'].sum() > 0 else 0

                c1, c2, c3 = st.columns(3)
                c1.metric("Underlying Price", f"₹{ltp}")
                c2.metric("Max Pain", f"₹{max_pain}")
                c3.metric("PCR", f"{pcr:.2f}")

                st.subheader(f"🔥 Option Chain Analysis: {expiry}")
                # Show strikes near the current price (ATM +/- 5%)
                atm_range = df[(df['Strike'] >= ltp*0.95) & (df['Strike'] <= ltp*1.05)]
                st.dataframe(atm_range.style.background_gradient(subset=['Call OI', 'Put OI'], cmap="YlOrRd"), use_container_width=True)
        else:
            st.error(f"🔴 Mission Failed: Session expired or '{target}' not in FnO. Please try clicking the button again.")

st.markdown("---")
st.caption("Data: NSE Real-time API | Mode: Free Tier Agentic Deployment")