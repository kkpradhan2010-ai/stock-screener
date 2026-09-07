import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from textblob import TextBlob

st.set_page_config(page_title="AI Stock Screener", layout="wide")

st.title("🤖 AI Quant Stock Screener (NSE)")
st.caption("Top 5 Bullish & Top 5 Bearish Probability Engine")

STOCK_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "TATAMOTORS.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS",
    "BAJFINANCE.NS", "TATASTEEL.NS", "ASIANPAINT.NS", "HCLTECH.NS", "NTPC.NS",
    "POWERGRID.NS", "M&M.NS", "ULTRACEMCO.NS", "COALINDIA.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "WIPRO.NS", "BAJAJFINSV.NS", "ONGC.NS", "JSWSTEEL.NS"
]

def calculate_technicals(df):
    if len(df) < 20:
        return None
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
    curr_vol = df['Volume'].iloc[-1]
    vol_ratio = (curr_vol / avg_vol) if avg_vol > 0 else 1.0
    latest_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    pct_change = ((latest_close - prev_close) / prev_close) * 100
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = df['TR'].rolling(window=14).mean().iloc[-1]
    return {
        "price": latest_close,
        "pct_change": pct_change,
        "ema_20": df['EMA_20'].iloc[-1],
        "rsi": df['RSI'].iloc[-1],
        "vol_ratio": vol_ratio,
        "atr": atr if not np.isnan(atr) else (latest_close * 0.01)
    }

def analyze_news_sentiment(ticker_obj):
    try:
        news_items = ticker_obj.news
        if not news_items:
            return 0.0, "Normal"
        polarities = [TextBlob(n.get('title', '')).sentiment.polarity for n in news_items[:3]]
        return np.mean(polarities) if polarities else 0.0, news_items[0].get('title', 'Normal')
    except Exception:
        return 0.0, "Normal"

def score_stock(tech, news_sentiment):
    bull = 0
    bear = 0
    if tech['price'] > tech['ema_20']: bull += 20
    else: bear += 20
    if tech['pct_change'] > 0.5: bull += 10
    elif tech['pct_change'] < -0.5: bear += 10
    if tech['vol_ratio'] >= 1.8:
        if tech['pct_change'] > 0: bull += 25
        else: bear += 25
    elif tech['vol_ratio'] >= 1.2:
        if tech['pct_change'] > 0: bull += 15
        else: bear += 15
    if 55 <= tech['rsi'] <= 72: bull += 25
    elif tech['rsi'] > 72: bull += 10
    elif 28 <= tech['rsi'] <= 45: bear += 25
    elif tech['rsi'] < 28: bear += 10
    if news_sentiment > 0.15: bull += 20
    elif news_sentiment < -0.15: bear += 20
    else:
        bull += 5
        bear += 5
    return round(bull, 1), round(bear, 1)

min_confidence = st.slider("न्यूनतम कॉन्फिडेंस थ्रेशोल्ड (%)", 60, 90, 75, 5)

if st.button("🚀 सभी स्टॉक्स स्कैन करें (Run Scanner)", type="primary"):
    progress = st.progress(0)
    bull_res, bear_res = [], []
    total = len(STOCK_UNIVERSE)
    
    for i, symbol in enumerate(STOCK_UNIVERSE):
        clean_name = symbol.replace(".NS", "")
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo", interval="1d")
            if not hist.empty and len(hist) >= 20:
                tech = calculate_technicals(hist)
                if tech:
                    news_score, headline = analyze_news_sentiment(ticker)
                    bull_p, bear_p = score_stock(tech, news_score)
                    atr, entry = tech['atr'], tech['price']
                    if bull_p >= min_confidence and tech['pct_change'] > 0:
                        bull_res.append({
                            "Stock": clean_name,
                            "Bullish %": f"{bull_p}%",
                            "Score": bull_p,
                            "LTP (₹)": round(entry, 2),
                            "Change %": f"{round(tech['pct_change'], 2)}%",
                            "Vol": f"{round(tech['vol_ratio'], 1)}x",
                            "Entry": round(entry, 2),
                            "SL": round(entry - (1.2 * atr), 2),
                            "Target": round(entry + (2.4 * atr), 2)
                        })
                    elif bear_p >= min_confidence and tech['pct_change'] < 0:
                        bear_res.append({
                            "Stock": clean_name,
                            "Bearish %": f"{bear_p}%",
                            "Score": bear_p,
                            "LTP (₹)": round(entry, 2),
                            "Change %": f"{round(tech['pct_change'], 2)}%",
                            "Vol": f"{round(tech['vol_ratio'], 1)}x",
                            "Entry": round(entry, 2),
                            "SL": round(entry + (1.2 * atr), 2),
                            "Target": round(entry - (2.4 * atr), 2)
                        })
        except Exception:
            pass
        progress.progress((i + 1) / total)
    progress.empty()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🟢 TOP 5 BULLISH STOCKS")
        if bull_res:
            df = pd.DataFrame(bull_res).sort_values("Score", ascending=False).head(5).drop(columns=["Score"])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("⚠️ NO HIGH-CONFIDENCE BULLISH STOCK")
    with c2:
        st.subheader("🔴 TOP 5 BEARISH STOCKS")
        if bear_res:
            df = pd.DataFrame(bear_res).sort_values("Score", ascending=False).head(5).drop(columns=["Score"])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("⚠️ NO HIGH-CONFIDENCE BEARISH STOCK")
