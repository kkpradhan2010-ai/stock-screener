import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import concurrent.futures
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# 1. UI CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="AlphaQuant 11-Layer Institutional Engine",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 26px; font-weight: 800; text-align: center; color: #0F172A; margin-bottom: 2px; }
    .sub-header { font-size: 12px; font-weight: 600; text-align: center; color: #64748B; margin-bottom: 20px; text-transform: uppercase; }
    .metric-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; text-align: center; }
    .metric-title { font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 4px; }
    .metric-val-bull { font-size: 15px; font-weight: 800; color: #16A34A; }
    .metric-val-bear { font-size: 15px; font-weight: 800; color: #DC2626; }
    .metric-val-neu { font-size: 15px; font-weight: 800; color: #2563EB; }
    .short-alert { background-color: #FEF2F2; border-left: 5px solid #DC2626; padding: 12px 16px; border-radius: 6px; font-size: 15px; font-weight: 800; color: #991B1B; margin: 15px 0 10px 0; }
    .buy-alert { background-color: #F0FDF4; border-left: 5px solid #16A34A; padding: 12px 16px; border-radius: 6px; font-size: 15px; font-weight: 800; color: #166534; margin: 15px 0 10px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚡ ALPHA-QUANT 11-LAYER INSTITUTIONAL ENGINE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Regime | 150 F&O Universe | Daily EMA | 15m ORB | Volume | VWAP | Relative Strength | Anti-Trap | Dynamic ATR</div>', unsafe_allow_html=True)

# ==========================================
# 2. 150 HIGH-LIQUID F&O UNIVERSE
# ==========================================
INSTITUTIONAL_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "SBIN.NS", "BHARTIARTL.NS", "TECHM.NS", "LT.NS", "TATASTEEL.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "MARUTI.NS", "TATAMOTORS.NS", "BAJFINANCE.NS",
    "HINDUNILVR.NS", "ITC.NS", "SUNPHARMA.NS", "WIPRO.NS", "HCLTECH.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "ASIANPAINT.NS", "BAJAJ-AUTO.NS", "BAJAJFINSV.NS",
    "BPCL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DIVISLAB.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS",
    "HINDALCO.NS", "INDUSINDBK.NS", "JSWSTEEL.NS", "M&M.NS", "NESTLEIND.NS",
    "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "SBILIFE.NS", "SHREECEM.NS",
    "TATACONSUM.NS", "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "APOLLOHOSP.NS",
    "AARTIIND.NS", "ABB.NS", "ABCAPITAL.NS", "ABFRL.NS", "ACC.NS",
    "AMBUJACEM.NS", "ASHOKLEY.NS", "ASTRAL.NS", "AUBANK.NS", "AUROPHARMA.NS",
    "BALKRISIND.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS",
    "BERGEPAINT.NS", "BHARATFORG.NS", "BHEL.NS", "BIOCON.NS", "BOSCHLTD.NS",
    "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "COFORGE.NS",
    "COLPAL.NS", "CONCOR.NS", "COROMANDEL.NS", "CROMPTON.NS", "CUB.NS",
    "CUMMINSIND.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS",
    "DIXON.NS", "DLF.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS",
    "GAIL.NS", "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS",
    "GODREJPROP.NS", "GRANULES.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS",
    "HINDCOPPER.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDEA.NS", "IDFCFIRSTB.NS",
    "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS",
    "INDIGO.NS", "INDUSTOWER.NS", "INTELLECT.NS", "IPCALAB.NS", "JINDALSTEL.NS",
    "JKCEMENT.NS", "JSL.NS", "JUBLFOOD.NS", "L&TFH.NS", "LALPATHLAB.NS",
    "LAURUSLABS.NS", "LICHSGFIN.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS",
    "MANAPPURAM.NS", "MARICO.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS",
    "MFSL.NS", "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS",
    "MUTHOOTFIN.NS", "NATIONALUM.NS", "NAUKRI.NS", "NAVINFLUOR.NS", "NMDC.NS",
    "OBEROIRLTY.NS", "OFSS.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS",
    "PETRONET.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS", "PNB.NS"
]

# ==========================================
# 3. NIFTY MACRO REGIME ENGINE
# ==========================================
@st.cache_data(ttl=60)
def get_nifty_regime():
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="5d", interval="5m")
        if len(hist) >= 10:
            daily_hist = nifty.history(period="5d")
            prev_close = daily_hist['Close'].iloc[-2]
            curr_price = hist['Close'].iloc[-1]
            pct_chg = ((curr_price - prev_close) / prev_close) * 100
            hist['EMA20'] = hist['Close'].ewm(span=20, adjust=False).mean()
            last_ema = hist['EMA20'].iloc[-1]
            if pct_chg > 0.15 and curr_price > last_ema:
                return "TRENDING BULLISH", pct_chg, "BULLISH"
            elif pct_chg < -0.15 and curr_price < last_ema:
                return "TRENDING BEARISH", pct_chg, "BEARISH"
            else:
                return "SIDEWAYS / NEUTRAL", pct_chg, "SIDEWAYS"
    except Exception:
        pass
    return "NEUTRAL", 0.00, "SIDEWAYS"

regime_title, nifty_pct, macro_bias = get_nifty_regime()

m1, m2, m3, m4 = st.columns(4)
with m1:
    vclass = "metric-val-bull" if nifty_pct > 0.15 else ("metric-val-bear" if nifty_pct < -0.15 else "metric-val-neu")
    st.markdown(f'<div class="metric-card"><div class="metric-title">NIFTY REGIME</div><div class="{vclass}">{regime_title} ({nifty_pct:+.2f}%)</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">SCAN UNIVERSE</div><div class="metric-val-neu">{len(INSTITUTIONAL_UNIVERSE)} F&O Stocks</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><div class="metric-title">CONFIRMATION FILTER</div><div class="metric-val-bull">Score 70+ Cutoff</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-card"><div class="metric-title">OUTPUT CONSTRAINT</div><div class="metric-val-bull">Strict Top 1-2</div></div>', unsafe_allow_html=True)

st.write("")

# ==========================================
# 4. HIGH-CONVICTION QUANT ENGINE
# ==========================================
def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

def process_single_stock(ticker, market_regime, n_pct):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1d", interval="5m")
        if df.empty or len(df) < 12:
            return None

        df_daily = stock.history(period="30d", interval="1d")
        if len(df_daily) < 20:
            return None
        
        prev_day_close = df_daily['Close'].iloc[-2]
        daily_ema20 = df_daily['Close'].ewm(span=20, adjust=False).mean().iloc[-1]

        typical = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (typical * df['Volume']).cumsum() / df['Volume'].cumsum()
        
        orb_high = round(df['High'].iloc[:3].max(), 2)
        orb_low = round(df['Low'].iloc[:3].min(), 2)
        
        last = df.iloc[-1]
        ltp = round(last['Close'], 2)
        vwap = round(last['VWAP'], 2)
        day_low = round(df['Low'].min(), 2)
        day_high = round(df['High'].max(), 2)
        
        stock_pct = ((ltp - prev_day_close) / prev_day_close) * 100
        rel_strength = round(stock_pct - n_pct, 2)
        
        avg_vol = df['Volume'].rolling(10).mean().iloc[-1]
        vol_surge = round(last['Volume'] / avg_vol, 2) if avg_vol > 0 else 1.0
        
        atr = calculate_atr(df, 14)
        if pd.isna(atr) or atr == 0:
            atr = ltp * 0.005
            
        bounce_from_low = ((ltp - day_low) / day_low) * 100 if day_low > 0 else 0
        pullback_from_high = ((day_high - ltp) / day_high) * 100 if day_high > 0 else 0
        clean_sym = ticker.replace(".NS", "")

        # हार्ड वॉल्यूम फ़िल्टर: कम से कम 1.3x वॉल्यूम जरूरी
        if vol_surge < 1.3:
            return None

        # ----------------- SHORT SETUP (STRICT ZERO-TRAP) -----------------
        if market_regime != "BULLISH":
            if (ltp < vwap) and (ltp <= orb_low) and (bounce_from_low <= 0.40):
                if last['Close'] <= last['Open']:  # Red confirmation
                    score = 0
                    if rel_strength < -1.0: score += 30
                    elif rel_strength < -0.5: score += 20
                    if vol_surge >= 2.5: score += 25
                    elif vol_surge >= 1.8: score += 15
                    if ((vwap - ltp) / vwap) * 100 >= 0.5: score += 20
                    if ltp < daily_ema20: score += 15
                    if bounce_from_low <= 0.15: score += 10
                    
                    # 70+ स्कोर कटऑफ (केवल अल्ट्रा-हाई प्रोबेबिलिटी)
                    if score >= 70:
                        sl = round(max(vwap, ltp + (1.2 * atr)), 2)
                        risk = sl - ltp
                        t1 = round(ltp - (1.5 * risk), 2)
                        t2 = round(ltp - (2.5 * risk), 2)
                        return {
                            "Signal": "SHORT",
                            "Symbol": clean_sym,
                            "Score": f"{score}/100",
                            "LTP": ltp,
                            "VWAP": vwap,
                            "Breakout": orb_low,
                            "SL": sl,
                            "Target 1": t1,
                            "Target 2": t2,
                            "Vol Surge": f"{vol_surge}x",
                            "raw_score": score
                        }

        # ----------------- BUY SETUP (STRICT ZERO-TRAP) -----------------
        if market_regime != "BEARISH":
            if (ltp > vwap) and (ltp >= orb_high) and (pullback_from_high <= 0.40):
                if last['Close'] >= last['Open']:  # Green confirmation
                    score = 0
                    if rel_strength > 1.0: score += 30
                    elif rel_strength > 0.5: score += 20
                    if vol_surge >= 2.5: score += 25
                    elif vol_surge >= 1.8: score += 15
                    if ((ltp - vwap) / vwap) * 100 >= 0.5: score += 20
                    if ltp > daily_ema20: score += 15
                    if pullback_from_high <= 0.15: score += 10
                    
                    # 70+ स्कोर कटऑफ
                    if score >= 70:
                        sl = round(min(vwap, ltp - (1.2 * atr)), 2)
                        risk = ltp - sl
                        t1 = round(ltp + (1.5 * risk), 2)
                        t2 = round(ltp + (2.5 * risk), 2)
                        return {
                            "Signal": "BUY",
                            "Symbol": clean_sym,
                            "Score": f"{score}/100",
                            "LTP": ltp,
                            "VWAP": vwap,
                            "Breakout": orb_high,
                            "SL": sl,
                            "Target 1": t1,
                            "Target 2": t2,
                            "Vol Surge": f"{vol_surge}x",
                            "raw_score": score
                        }
    except Exception:
        return None
    return None

# ==========================================
# 5. PARALLEL EXECUTION PIPELINE
# ==========================================
if st.button("⚡ Scan 150 Institutional F&O Stocks (High Probability)", use_container_width=True, type="primary"):
    with st.spinner("Scanning 150 F&O stocks with 11-Layer Institutional Pipeline..."):
        trades = []
        # Multi-threading for high-speed scanning of 150 stocks
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_single_stock, sym, macro_bias, nifty_pct) for sym in INSTITUTIONAL_UNIVERSE]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    trades.append(res)
        
        shorts = sorted([t for t in trades if t['Signal'] == "SHORT"], key=lambda x: x['raw_score'], reverse=True)[:2]
        buys = sorted([t for t in trades if t['Signal'] == "BUY"], key=lambda x: x['raw_score'], reverse=True)[:2]

        if macro_bias == "BULLISH":
            st.info("🛡️ **Safety Layer Active:** Nifty का ट्रेंड **BULLISH** है। शॉर्ट ट्रैप से बचाने के लिए 150 स्टॉक्स में से सभी Sell सिग्नल्स सख्त रूप से ब्लॉक हैं।")
        elif shorts:
            st.markdown('<div class="short-alert">🔴 TOP 1-2 INSTITUTIONAL SHORT (70+ SCORE CONFIRMED)</div>', unsafe_allow_html=True)
            df_s = pd.DataFrame(shorts).drop(columns=['Signal', 'raw_score'])
            st.dataframe(df_s, use_container_width=True, hide_index=True)
            st.caption("AlphaQuant Engine | Target 1 पर 50% प्रॉफिट बुक करें और SL कॉस्ट पर ट्रेल करें।")
        else:
            st.write("150 स्टॉक्स में से कोई शॉर्ट ट्रेड 70+ स्कोर क्राइटेरिया मैच नहीं हुई (No Low-Probability Trades)।")

        if buys:
            st.markdown('<div class="buy-alert">🟢 TOP 1-2 INSTITUTIONAL BUY (70+ SCORE CONFIRMED)</div>', unsafe_allow_html=True)
            df_b = pd.DataFrame(buys).drop(columns=['Signal', 'raw_score'])
            st.dataframe(df_b, use_container_width=True, hide_index=True)
            st.caption("AlphaQuant Engine | Target 1 पर 50% प्रॉफिट बुक करें और SL कॉस्ट पर ट्रेल करें।")
        elif macro_bias != "BULLISH":
            st.write("150 स्टॉक्स में से कोई बाय ट्रेड 70+ स्कोर क्राइटेरिया मैच नहीं हुई।")

st.markdown("---")
st.caption("AlphaQuant 11-Layer Institutional Engine | Strict 150 F&O High-Conviction Model")
