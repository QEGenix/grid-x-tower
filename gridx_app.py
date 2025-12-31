import streamlit as st
import yfinance as yf
from groq import Groq
import pandas as pd

# --- 1. THE PERCEPTION LAYER (Market & News) ---
def get_market_context(ticker):
    """Fetches real-time price data and news headlines with safety checks."""
    stock = yf.Ticker(ticker)
    # Fetch 1-minute interval data
    df = stock.history(period="1d", interval="1m")
    
    # SAFE NEWS FETCHING
    news_items = stock.news[:5]
    headlines = []
    for item in news_items:
        # Use .get() to avoid KeyError if 'title' is missing
        title = item.get('title')
        if title:
            headlines.append(title)
            
    return df, headlines

def fetch_news_sentiment(ticker, headlines):
    """Asks Groq to analyze headlines and return a sentiment score."""
    if not headlines:
        return 0.0, "No recent news found."

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    headlines_text = "\n".join(headlines)
    
    prompt = f"""
    Analyze the following news headlines for {ticker}:
    {headlines_text}
    
    Provide a sentiment score between -1.0 (Very Bearish) and 1.0 (Very Bullish). 
    Output ONLY the score followed by a one-sentence summary.
    Format: [Score] | [Summary]
    """
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = response.choices[0].message.content
    try:
        score = float(result.split('|')[0].strip().replace('[', '').replace(']', ''))
        summary = result.split('|')[1].strip()
    except:
        score = 0.0
        summary = "Neutral (Could not parse score)"
        
    return score, summary

# --- 2. THE COGNITIVE LAYER (Strategy Brain) ---
def get_agent_strategy(price, sentiment_summary, ticker):
    """Generates the final Grid Trading strategy."""
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    prompt = f"""
    Ticker: {ticker}
    Current Price: ${price:.2f}
    Market Sentiment: {sentiment_summary}
    
    Act as an Expert Grid Trading Agent. 
    1. Should we be Aggressive or Conservative?
    2. Suggest a 'Buy' grid level and a 'Sell' grid level.
    3. Provide a brief 'Risk Warning' based on the sentiment.
    """
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content

# --- 3. THE INTERFACE LAYER (Control Tower UI) ---
st.set_page_config(page_title="Grid-x 2.0 Tower", layout="wide")
st.title("🛰️ Grid-x 2.0: Agentic Control Tower")

# Sidebar for Inputs
st.sidebar.header("Mission Parameters")
symbol = st.sidebar.text_input("Enter Ticker", value="NVDA").upper()

if st.sidebar.button("🚀 START MISSION"):
    with st.status("Initializing Grid-x Sensors...", expanded=True) as status:
        # Step 1: Sense
        df, headlines = get_market_context(symbol)
        last_price = df['Close'].iloc[-1]
        st.write("✅ Market Data Ingested")
        
        # Step 2: Analyze News
        sentiment_score, sentiment_summary = fetch_news_sentiment(symbol, headlines)
        st.write("✅ Sentiment Pulse Captured")
        
        # Step 3: Formulate Strategy
        strategy = get_agent_strategy(last_price, sentiment_summary, symbol)
        st.write("✅ Strategy Optimized")
        status.update(label="Mission Analysis Complete!", state="complete", expanded=False)

    # --- DISPLAY RESULTS ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"📈 {symbol} Price Action")
        st.line_chart(df['Close'])
        
    with col2:
        st.subheader("🤖 Sentiment Pulse")
        if sentiment_score > 0.2:
            st.success(f"BULLISH ({sentiment_score})")
        elif sentiment_score < -0.2:
            st.error(f"BEARISH ({sentiment_score})")
        else:
            st.warning(f"NEUTRAL ({sentiment_score})")
        st.caption(sentiment_summary)

    st.divider()
    st.subheader("🎮 Pilot's Strategic Recommendation")
    st.info(strategy)