import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import feedparser
import concurrent.futures

# ==========================================
# PAGE CONFIG & CLEAN STYLING
# ==========================================
st.set_page_config(page_title="AlphaQuant Core 7-Layer", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    .main-title { text-align: center; font-weight: 800; color: #0F172A; margin-bottom: 2px; }
    .sub-title { text-align: center; font-size: 13px; color: #64748B; margin-bottom: 20px; }
    .metric-box { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🎯 ALPHA-QUANT 7-LAYER SYSTEM</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Market Regime | News Audit | Relative Strength | 15m ORB | VWAP | Dynamic ATR</p>", unsafe_allow_html=True)

# ==========================================
# HIGH-LIQUIDITY F&O UNIVERSE (TOP 60)
# ==========================================
FO_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS",
    "ITC.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TATAMOTORS.NS", "KOTAKBANK.NS", "AXISBANK.NS", "NTPC.NS", "ONGC.NS", "TITAN.NS", "ADANIENT.NS",
    "POWERGRID.NS", "TATASTEEL.NS", "M&M.NS", "JSWSTEEL.NS", "ADANIPORTS.NS", "ASIANPAINT.NS",
    "DLF.NS", "BEL.NS", "HAL.NS", "ZOMATO.NS", "VEDL.NS", "GRASIM.NS", "TECHM.NS", "HINDALCO.NS",
    "INDUSINDBK.NS", "CIPLA.NS", "TRENT.NS", "EICHERMOT.NS", "WIPRO.NS", "SHRIRAMFIN.NS",
    "HEROMOTOCO.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "BPCL.NS", "BAJAJ-AUTO.NS",
    "CHOLAFIN.NS", "POLYCAB.NS", "PIDILITIND.NS", "GAIL.NS", "PFC.NS", "RECLTD.NS", "JINDALSTEL.NS",
    "HAVELLS.NS", "CANBK.NS", "LUPIN.NS", "BANKBARODA.NS", "PERSISTENT.NS", "COFORGE.NS"
]

# ==========================================
# RULE 1: LIVE FINANCIAL NEWS AUDIT
# ==========================================
RISK_TERMS = ["raid", "fraud", "ed", "cbi", "sebi", "resigns", "default", "probe", "penalty", "downgrade", "scam", "loss"]

@st.cache_data(ttl=900)
def get_flagged_news():
    flagged = set()
    rss_feeds = [
        "https://www.moneycontrol.com/rss/MCtopnews.xml",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    ]
    for url in rss_feeds:
        try:
            feed = feedparser.parse(url)
            for item in feed.entries[:25]:
                title = item.title.lower()
                if any(k in title for k in RISK_TERMS):
                    for sym in FO_UNIVERSE:
                        clean_name = sym.replace(".NS", "").lower()
                        if clean_name in title:
                            flagged.add(sym)
        except Exception:
            continue
    return flagged

# ==========================================
# RULE 2: NIFTY 50 REGIME LOCK
# ==========================================
def get_nifty_bias():
    try:
        nifty = yf.download("^NSEI", period="2d", interval="15m", progress=False)
        if nifty.empty or len(nifty) < 2:
            return "NORMAL", 0.0, False
            
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
            
        open_price = float(nifty['Open'].iloc[0])
        last_price = float(nifty['Close'].iloc[-1])
        change_pct = ((last_price - open_price) / open_price) * 100
        
        orb_high = float(nifty['High'].iloc[0])
        orb_low = float(nifty['Low'].iloc[0])
        
        is_choppy = (orb_low <= last_price <= orb_high)
        
        if last_price > orb_high and change_pct > 0.1:
            bias = "TRENDING BULLISH"
        elif last_price < orb_low and change_pct < -0.1:
            bias = "TRENDING BEARISH"
        else:
            bias = "SIDEWAYS / CHOPPY"
            is_choppy = True
            
        return bias, change_pct, is_choppy
    except Exception:
        return "UNKNOWN", 0.0, False

# ==========================================
# RULES 3, 4, 5, 6: QUANT EXECUTION ENGINE
# ==========================================
def screen_stock(ticker, nifty_ret, blacklist):
    if ticker in blacklist:
        return None
        
    try:
        df = yf.download(ticker, period="2d", interval="15m", progress=False)
        if df.empty or len(df) < 4:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        ltp = float(df['Close'].iloc[-1])
        vol_curr = float(df['Volume'].iloc[-1])
        vol_avg = float(df['Volume'].rolling(6).mean().iloc[-1])
        
        if vol_curr < (1.3 * vol_avg) or vol_curr == 0:
            return None
            
        orb_h = float(df['High'].iloc[0])
        orb_l = float(df['Low'].iloc[0])
        
        df['Typical'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['VP'] = df['Typical'] * df['Volume']
        vwap = float(df['VP'].cumsum().iloc[-1] / df['Volume'].cumsum().iloc[-1])
        
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(abs(df['High'] - df['Close'].shift(1)), abs(df['Low'] - df['Close'].shift(1)))
        )
        atr = float(df['TR'].rolling(6).mean().iloc[-1])
        if np.isnan(atr) or atr <= 0:
            atr = ltp * 0.007

        stock_ret = ((ltp - df['Open'].iloc[0]) / df['Open'].iloc[0]) * 100
        rs = stock_ret - nifty_ret
        
        action = None
        sl, t1, t2 = 0.0, 0.0, 0.0
        
        if ltp > orb_h and ltp > vwap and rs > 0.75:
            action = "STRONG BUY"
            sl = round(ltp - (1.2 * atr), 2)
            t1 = round(ltp + (1.5 * atr), 2)
            t2 = round(ltp + (2.5 * atr), 2)
            rank_score = rs * (vol_curr / vol_avg)
            
        elif ltp < orb_l and ltp < vwap and rs < -0.75:
            action = "STRONG SHORT"
            sl = round(ltp + (1.2 * atr), 2)
            t1 = round(ltp - (1.5 * atr), 2)
            t2 = round(ltp - (2.5 * atr), 2)
            rank_score = abs(rs) * (vol_curr / vol_avg)
        else:
            return None
            
        return {
            "Symbol": ticker.replace(".NS", ""),
            "Action": action,
            "LTP": round(ltp, 2),
            "VWAP": round(vwap, 2),
            "Breakout Level": round(orb_h if "BUY" in action else orb_l, 2),
            "RS Score": f"{round(rs, 2)}%",
            "Stop Loss": sl,
            "Target 1 (1.5x)": t1,
            "Target 2 (2.5x)": t2,
            "Rank": round(rank_score, 2)
        }
    except Exception:
        return None

# ==========================================
# UI DASHBOARD & CONTROLS
# ==========================================
nifty_state, n_ret, is_sideways = get_nifty_bias()
flagged_news = get_flagged_news()

c1, c2, c3 = st.columns(3)
c1.markdown(f"<div class='metric-box'><b>NIFTY REGIME</b><br><span style='color:{'#16A34A' if 'BULL' in nifty_state else '#DC2626' if 'BEAR' in nifty_state else '#D97706'}; font-weight:bold;'>{nifty_state} ({round(n_ret, 2)}%)</span></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='metric-box'><b>NEWS BLACKLIST</b><br><span style='color:#2563EB; font-weight:bold;'>{len(flagged_news)} Stocks Excluded</span></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='metric-box'><b>RULE FILTER</b><br><span style='color:#16A34A; font-weight:bold;'>Strict 7-Layer Active</span></div>", unsafe_allow_html=True)

st.write("")

if is_sideways:
    st.warning("⚠️ **मार्केट साइडवेज़ है:** Nifty 50 अपनी पहली 15-मिनट रेंज में फंसा है। ऐसे में ब्रेकआउट फेल होने का रिस्क अधिक रहता है। केवल सर्वोच्च रैंक वाले सेटअप पर ही विचार करें।")

if st.button("🔍 Scan Quality Trades (Top 1-2 Only)", use_container_width=True):
    with st.spinner("7-लेयर कड़े फिल्टर चल रहे हैं..."):
        candidates = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(screen_stock, s, n_ret, flagged_news) for s in FO_UNIVERSE]
            for f in concurrent.futures.as_completed(futures):
                res = f.result()
                if res:
                    candidates.append(res)
                    
        if not candidates:
            st.info("🛡️ **आज कोई भी स्टॉक सभी 7 कड़े पैमानों पर 100% खरा नहीं उतरा।** (शून्य ट्रेड लेना गलत ट्रेड में नुकसान करने से बेहतर है)।")
        else:
            df_res = pd.DataFrame(candidates)
            
            buys = df_res[df_res['Action'] == "STRONG BUY"].sort_values(by="Rank", ascending=False).head(2)
            shorts = df_res[df_res['Action'] == "STRONG SHORT"].sort_values(by="Rank", ascending=False).head(2)
            
            if not buys.empty:
                st.success("### 🟢 TOP CONFIRMED BUY")
                st.dataframe(buys[['Symbol', 'LTP', 'VWAP', 'Breakout Level', 'RS Score', 'Stop Loss', 'Target 1 (1.5x)', 'Target 2 (2.5x)']], use_container_width=True)
                
            if not shorts.empty:
                st.error("### 🔴 TOP CONFIRMED SHORT")
                st.dataframe(shorts[['Symbol', 'LTP', 'VWAP', 'Breakout Level', 'RS Score', 'Stop Loss', 'Target 1 (1.5x)', 'Target 2 (2.5x)']], use_container_width=True)

st.divider()
st.caption("Alpha-Quant Engine | Capital Protection First | Target 1 आने पर 50% प्रॉफिट बुक करें और SL कॉस्ट पर लाएँ।")
