import streamlit as st
import requests
import pandas as pd
import time
import math

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(page_title="Grid-x: NSE Agentic Tower", layout="wide", page_icon="🛰️")

# --- CORE LOGIC: NSE SESSION AGENT ---
class NSEAgent:
    def __init__(self):
        # Headers specifically designed to mimic a real Chrome browser
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
        """Visits the NSE homepage to initialize/refresh cookies."""
        try:
            # 1. Hit the homepage to get the initial cookies
            self.session.get("https://www.nseindia.com", timeout=10)
        except Exception as e:
            st.error(f"⚠️ Network Error during handshake: {e}")

    def fetch_option_chain(self, symbol):
        symbol = symbol.upper().strip()
        
        # Logic to distinguish between Indices and Stocks
        indices = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]
        
        if symbol in indices:
            url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        else:
            # For stocks, NSE requires the symbol encoded (though usually standard works)
            url = f"https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"
        
        try:
            response = self.session.get(url, timeout=10)
            
            # If the session expired (401), try one refresh
            if response.status_code == 401:
                self.refresh_session()
                time.sleep(1) # Polite delay
                response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            st.error(f"Data Fetch Error: {e}")
            return None

# --- CORE LOGIC: MAX PAIN CALCULATOR ---
def calculate_max_pain(df):
    """
    Calculates Max Pain: The strike price where option writers 
    (Sellers) lose the least amount of money.
    """
    strikes = df['Strike'].tolist()
    total_loss_per_strike = []
    
    for hypothetical_expiry in strikes:
        total_loss = 0
        for _, row in df.iterrows():
            strike = row['Strike']
            call_oi = row['Call OI']
            put_oi = row['Put OI']
            
            # Loss for Call Writers: If Expiry > Strike
            if hypothetical_expiry > strike:
                total_loss += (hypothetical_expiry - strike) * call_oi
                
            # Loss for Put Writers: If Expiry < Strike
            if hypothetical_expiry < strike:
                total_loss += (strike - hypothetical_expiry) * put_oi
                
        total_loss_per_strike.append(total_loss)
    
    # Find the strike with the minimum total loss
    min_loss_index = total_loss_per_strike.index(min(total_loss_per_strike))
    return strikes[min_loss_index]

# --- UI ARCHITECTURE ---
st.title("🛰️ Grid-x 2.0: Agentic Control Tower (NSE Direct)")
st.markdown("---")

# Initialize the Agent in Session State to keep cookies alive
if 'agent' not in st.session_state:
    st.session_state.agent = NSEAgent()

# SIDEBAR: COMMAND CENTER
with st.sidebar:
    st.header("🎯 Mission Parameters")
    target_symbol = st.text_input("Enter Symbol (e.g. TCS, NIFTY)", "NIFTY")
    
    if st.button("🚀 INITIALIZE SCAN"):
        st.session_state.scan_active = True

# MAIN DASHBOARD RENDERING
if st.session_state.get('scan_active'):
    
    with st.spinner(f"Establishing Secure Link to NSE for {target_symbol}..."):
        data = st.session_state.agent.fetch_option_chain(target_symbol)
        
        if data:
            # 1. PARSE CRITICAL METRICS
            try:
                # Underlying Price (Spot Price)
                ltp = data['records']['underlyingValue']
                # Get the nearest expiry date
                expiry_list = data['records']['expiryDates']
                expiry = expiry_list[0] 
                
                # Process the Raw JSON into a Clean DataFrame
                raw_data = data['records']['data']
                oc_rows = []
                
                for item in raw_rows:
                    if item['expiryDate'] == expiry:
                        strike = item['strikePrice']
                        ce = item.get('CE', {})
                        pe = item.get('PE', {})
                        
                        oc_rows.append({
                            "Strike": strike,
                            "Call OI": ce.get('openInterest', 0),
                            "Call Change": ce.get('changeinOpenInterest', 0),
                            "Call Price": ce.get('lastPrice', 0),
                            "Put OI": pe.get('openInterest', 0),
                            "Put Change": pe.get('changeinOpenInterest', 0),
                            "Put Price": pe.get('lastPrice', 0),
                            "IV (Call)": ce.get('impliedVolatility', 0)
                        })
                
                df = pd.DataFrame(oc_rows).sort_values("Strike")
                
                # Calculate Derived Metrics
                max_pain = calculate_max_pain(df)
                total_ce_oi = df