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
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.refresh_session()

    def refresh_session(self):
        """Attempts to establish a session with up to 3 retries."""
        for i in range(3):
            try:
                # Use the main option chain page to get valid cookies
                resp = self.session.get("https://www.nseindia.com/option-chain", timeout=10)
                if resp.status_code == 200:
                    return True
            except:
                time.sleep(1)
        return False

    def fetch_option_chain(self, symbol):
        symbol = symbol.upper().strip()
        indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}" if symbol in indices else f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 401:
                self.refresh_session()
                response = self.session.get(url, timeout=10)
            return response.json() if response.status_code == 200 else None
        except:
            return None

def calculate_max_pain(df):
    if df.empty: return 0
    strikes = df['Strike'].tolist()
    losses = []
    for s in strikes:
        # Sum of (Price Difference * OI) where writers lose money
        call_loss = df[df['Strike'] < s].apply(lambda x: (s - x['Strike']) * x['Call OI'], axis=1).sum()
        put_loss = df[df['Strike'] > s].apply(lambda x: (x['Strike'] - s) * x['Put OI'], axis=1).sum()
        losses.append(call_loss + put_loss)
    return strikes[losses.index(min(losses))]

# --- UI ---
st.title("🛰️ Grid-x 2.0: Agentic Control Tower")

if 'agent' not in st.session_state:
    st.session_state.agent = NSEAgent()

with st.sidebar:
    st.header("🎯 Target Selection")
    target = st.text_input("NSE Symbol", "TCS").upper()
    scan = st.button("🚀 INITIALIZE SCAN")

if scan:
    data = st.session_state.agent.fetch_option_chain(target)
    if data:
        try:
            # Metadata
            ltp = data['records']['underlyingValue']
            expiry = data['records']['expiryDates'][0]
            
            # Extract Rows
            rows = []
            for item in data['records']['data']:
                if item.get('expiryDate') == expiry:
                    c, p = item.get('CE', {}), item.get('PE', {})
                    rows.append({
                        "Strike": item.get('strikePrice'),
                        "Call OI": c.get('openInterest', 0),
                        "Put OI": p.get('openInterest', 0),
                        "LTP": c.get('lastPrice', 0) # Just for display
                    })
            
            df = pd.DataFrame(rows).sort_values("Strike")
            max_pain = calculate_max_pain(df)
            pcr = df['Put OI'].sum() / df['Call OI'].sum() if df['Call OI'].sum() > 0 else 0

            # Dashboard
            m1, m2, m3 = st.columns(3)
            m1.metric("Stock Price", f"₹{ltp}")
            m2.metric("Max Pain", f"₹{max_pain}")
            m3.metric("PCR", f"{pcr:.2f}")

            # Visual Table (ATM focus)
            st.write(f"### Option Chain Heatmap: {expiry}")
            atm_df = df[(df['Strike'] >= ltp*0.97) & (df['Strike'] <= ltp*1.03)]
            st.dataframe(atm_df.style.background_gradient(cmap="Greens", subset=["Put OI"]).background_gradient(cmap="Reds", subset=["Call OI"]), use_container_width=True)
            
        except Exception as e:
            st.error(f"Logic Error: {e}. NSE might have returned a partial data frame.")
    else:
        st.error(f"Mission Failed. '{target}' session expired or not in FnO.")