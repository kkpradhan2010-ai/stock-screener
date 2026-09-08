import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Owl AI Quant Screener Pro", layout="wide", page_icon="🦉")

st.markdown("<h1 style='text-align: center;'>🦉 Owl AI Quant Screener (150 F&O Pro)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Hard Volume Gate | VWAP Filter | Nifty Alignment | Dynamic ATR Targets</p>", unsafe_allow_html=True)

# 150 सबसे लिक्विड F&O स्टॉक्स
STOCKS_150 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "INFY.NS",
    "ITC.NS", "SBIN.NS", "LICI.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS",
    "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS", "KOTAKBANK.NS", "TATAMOTORS.NS",
    "AXISBANK.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "TITAN.NS", "COALINDIA.NS",
    "BAJAJFINSV.NS", "TATASTEEL.NS", "M&M.NS", "ULTRACEMCO.NS", "ASIANPAINT.NS", "SIEMENS.NS",
    "JSWSTEEL.NS", "GRASIM.NS", "TECHM.NS", "HINDALCO.NS", "WIPRO.NS", "NESTLEIND.NS",
    "DLF.NS", "VEDL.NS", "HAL.NS", "BEL.NS", "ZOMATO.NS", "TRENT.NS", "TATAPOWER.NS",
    "IOC.NS", "PFC.NS", "RECLTD.NS", "JIOFIN.NS", "CANBK.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS",
    "EICHERMOT.NS", "BPCL.NS", "GAIL.NS", "BANKBARODA.NS", "PNB.NS", "INDUSINDBK.NS",
    "AMBUJACEM.NS", "DIVISLAB.NS", "CIPLA.NS", "DRREDDY.NS", "APOLLOHOSP.NS", "HEROMOTOCO.NS",
    "HAVELLS.NS", "DABUR.NS", "PIDILITIND.NS", "VOLTAS.NS", "POLYCAB.NS", "PERSISTENT.NS",
    "COFORGE.NS", "MPHASIS.NS", "DIXON.NS", "AUROPHARMA.NS", "LUPIN.NS", "FEDERALBNK.NS",
    "IDFCFIRSTB.NS", "TVSMOTOR.NS", "ASHOKLEY.NS", "CUMMINSIND.NS", "BHARATFORG.NS", "COLPAL.NS",
    "GODREJCP.NS", "BERGEPAINT.NS", "INDIGO.NS", "MOTHERSON.NS", "TORNTPHARM.NS", "ZYDUSLIFE.NS",
    "ABB.NS", "BOSCHLTD.NS", "MUTHOOTFIN.NS", "SBILIFE.NS", "HDFCLIFE.NS", "ICICIPRULI.NS",
    "LICHSGFIN.NS", "MANAPPURAM.NS", "PAGEIND.NS", "BATAINDIA.NS", "JUBLFOOD.NS", "TATACOMM.NS",
    "CONCOR.NS", "ACC.NS", "DALBHARAT.NS", "JKCEMENT.NS", "DEEPAKNTR.NS", "AARTIIND.NS",
    "SRF.NS", "NAVINFLUOR.NS", "ATUL.NS", "PIIND.NS", "UPL.NS", "COROMANDEL.NS",
    "BALKRISIND.NS", "MRF.NS", "APOLLOTYRE.NS", "ESCORTS.NS", "NATIONALUM.NS", "HINDCOPPER.NS",
    "NMDC.NS", "SAIL.NS", "JINDALSTEL.NS", "GMRINFRA.NS", "OBEROIRLTY.NS", "GODREJPROP.NS",
    "PRESTIGE.NS", "LTIM.NS", "OFSS.NS", "LTTS.NS", "TATAELXSI.NS", "KPITTECH.NS",
    "PETRONET.NS", "IGL.NS", "MGL.NS", "GUJGASLTD.NS", "BANDHANBNK.NS", "AUBANK.NS",
    "RBLBANK.NS", "BSOFT.NS", "EXIDEIND.NS", "GLENMARK.NS", "BIOCON.NS", "METROPOLIS.NS",
    "LALPATHLAB.NS", "SYNGENE.NS", "PEL.NS", "SUNTV.NS", "PVRINOX.NS", "INDIAMART.NS"
]

# साइडबार सेटिंग्स
st.sidebar.header("🎯 क्वांट सेटिंग्स")
threshold = st.sidebar.slider("न्यूनतम स्कोर थ्रेशोल्ड (%)", 60, 90, 75, 5)
min_vol_gate = st.sidebar.slider("हार्ड वॉल्यूम गेट (Min Vol Spike)", 1.1, 2.5, 1.3, 0.1)

def get_nifty_trend():
    try:
        nifty = yf.download("^NSEI", period="5d", interval="15m", progress=False)
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        close = nifty['Close']
        ema20 = close.ewm(span=20).mean().iloc[-1]
        current = close.iloc[-1]
        pct = round(((current - close.iloc[-2]) / close.iloc[-2]) * 100, 2)
        trend = "BULLISH" if current > ema20 else "BEARISH"
        return trend, pct
    except:
        return "NEUTRAL", 0.0

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean().iloc[-1]

def run_screener():
    bullish_list = []
    bearish_list = []
    
    nifty_trend, nifty_change = get_nifty_trend()
    st.info(f"📊 **Nifty 50 ट्रेंड:** `{nifty_trend}` ({nifty_change}%) | फ़िल्टर उसी दिशा में प्राथमिकता देंगे")
    
    progress = st.progress(0)
    status_text = st.empty()
    total = len(STOCKS_150)
    
    for idx, ticker in enumerate(STOCKS_150):
        try:
            status_text.text(f"स्कैनिंग ({idx+1}/{total}): {ticker.replace('.NS', '')}")
            
            # 5 दिन का 15-मिनट इंट्राडे डेटा
            df = yf.download(ticker, period="5d", interval="15m", progress=False)
            if df.empty or len(df) < 25:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            ltp = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            pct_change = round(((ltp - prev_close) / prev_close) * 100, 2)

            # 1. हार्ड वॉल्यूम गेट (Volume Gate)
            current_vol = float(df['Volume'].iloc[-1])
            avg_vol = float(df['Volume'].iloc[-20:-1].mean())
            vol_ratio = round(current_vol / (avg_vol + 1e-9), 2)
            
            if vol_ratio < min_vol_gate:
                continue  # वॉल्यूम कम है तो सीधा रिजेक्ट

            # 2. VWAP कैलकुलेशन
            typical_price = (df['High'] + df['Low'] + df['Close']) / 3
            vwap = (typical_price * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)
            current_vwap = round(float(vwap.iloc[-1]), 2)

            # 3. ATR (डायनामिक टारगेट और SL)
            atr = float(calculate_atr(df, period=14))
            if np.isnan(atr) or atr <= 0:
                atr = ltp * 0.01  # बैकअप 1%

            # 4. Moving Average & RSI
            ema20 = float(df['Close'].ewm(span=20).mean().iloc[-1])
            rsi = float(calculate_rsi(df['Close']).iloc[-1])

            # क्वांट स्कोरिंग इंजन
            bullish_score = 0
            bearish_score = 0

            # वॉल्यूम अंक (अधिकतम 30)
            if vol_ratio >= 1.8:
                bullish_score += 30
                bearish_score += 30
            else:
                bullish_score += 15
                bearish_score += 15

            # VWAP व ट्रेंड अंक (अधिकतम 35)
            if ltp > current_vwap and ltp > ema20:
                bullish_score += 35
            elif ltp < current_vwap and ltp < ema20:
                bearish_score += 35

            # RSI अंक (अधिकतम 20)
            if 55 <= rsi <= 72:
                bullish_score += 20
            elif 28 <= rsi <= 45:
                bearish_score += 20

            # Nifty ट्रेंड सिंक (अधिकतम 15)
            if nifty_trend == "BULLISH":
                bullish_score += 15
            elif nifty_trend == "BEARISH":
                bearish_score += 15

            stock_name = ticker.replace(".NS", "")

            # बुलिश फ़िल्टर (भाव VWAP से ऊपर होना अनिवार्य)
            if bullish_score >= threshold and ltp > current_vwap:
                sl = round(ltp - (1.0 * atr), 2)
                t1 = round(ltp + (1.5 * atr), 2)
                t2 = round(ltp + (2.0 * atr), 2)
                bullish_list.append({
                    "Stock": stock_name,
                    "Score %": f"{bullish_score}%",
                    "LTP (₹)": ltp,
                    "VWAP (₹)": current_vwap,
                    "Vol": f"{vol_ratio}x",
                    "Entry": ltp,
                    "SL (ATR)": sl,
                    "Target 1": t1,
                    "Target 2": t2
                })

            # बेयरिश फ़िल्टर (भाव VWAP से नीचे होना अनिवार्य)
            if bearish_score >= threshold and ltp < current_vwap:
                sl = round(ltp + (1.0 * atr), 2)
                t1 = round(ltp - (1.5 * atr), 2)
                t2 = round(ltp - (2.0 * atr), 2)
                bearish_list.append({
                    "Stock": stock_name,
                    "Score %": f"{bearish_score}%",
                    "LTP (₹)": ltp,
                    "VWAP (₹)": current_vwap,
                    "Vol": f"{vol_ratio}x",
                    "Entry": ltp,
                    "SL (ATR)": sl,
                    "Target 1": t1,
                    "Target 2": t2
                })

        except Exception:
            continue
        finally:
            progress.progress((idx + 1) / total)

    status_text.empty()
    return bullish_list, bearish_list

if st.button("🚀 150 स्टॉक्स स्कैन करें (Run Quant Scanner)"):
    with st.spinner("150 F&O स्टॉक्स, VWAP, Nifty और ATR लेवल्स प्रोसेस हो रहे हैं..."):
        bulls, bears = run_screener()

    st.markdown("### 🟢 TOP 5 QUALIFIED BULLISH (VWAP के ऊपर + हाई वॉल्यूम)")
    if bulls:
        df_bull = pd.DataFrame(bulls).sort_values(by="Vol", ascending=False).head(5)
        st.dataframe(df_bull, use_container_width=True)
    else:
        st.warning("⚠️ कोई बुलिश स्टॉक नहीं मिला (हार्ड वॉल्यूम गेट या VWAP नियम पूरे नहीं हुए)")

    st.markdown("### 🔴 TOP 5 QUALIFIED BEARISH (VWAP के नीचे + भारी बिकवाली)")
    if bears:
        df_bear = pd.DataFrame(bears).sort_values(by="Vol", ascending=False).head(5)
        st.dataframe(df_bear, use_container_width=True)
    else:
        st.warning("⚠️ कोई बेयरिश स्टॉक नहीं मिला (हार्ड वॉल्यूम गेट या VWAP नियम पूरे नहीं हुए)")
