import streamlit as st
import yfinance as yf
from groq import Groq
import pandas as pd

# 1. MARKET PERCEPTION
def get_market_data(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="1d", interval="5m")
    # Fetch news headlines for sentiment
    news = stock.news[:5] 
    headlines = [n['title'] for n in news]
    return df, headlines

# 2. COGNITIVE STRATEGY (The Brain)
def analyze_with_groq(price, headlines):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    context = ". ".join(headlines)
    prompt = f"Price: {price}. News: {context}. Act as a Grid Trading Pilot. Should we Expand, Contract, or Pause the grid? Explain why."
    
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat.choices[0].message.content

# 3. INTERFACE (The Control Tower)
st.title("🛰️ Grid-x 2.0: Sentiment Signal Engine")
symbol = st.sidebar.text_input("Ticker Symbol", "NVDA")

if st.sidebar.button("🛰️ RUN PRE-MARKET ANALYSIS"):
    df, news = get_market_data(symbol)
    last_price = df['Close'].iloc[-1]
    
    st.metric(f"Current {symbol} Price", f"${last_price:.2f}")
    st.line_chart(df['Close'])
    
    with st.expander("📰 Latest Headlines"):
        for n in news: st.write(f"- {n}")
        
    with st.status("🤖 Agent Thinking..."):
        signal = analyze_with_groq(last_price, news)
        st.subheader("Pilot Strategy Recommendation")
        st.info(signal)
