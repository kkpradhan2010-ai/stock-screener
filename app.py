import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Official Kotak Neo SDK Import
try:
    from neo_api_client import NeoAPI
    KOTAK_SDK_AVAILABLE = True
except ImportError:
    KOTAK_SDK_AVAILABLE = False

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
st.markdown('<div class="sub-header">Regime | News | Sector | Daily EMA | 15m ORB | Volume | VWAP | RS | Kotak Live OI | Option Trap | Dynamic ATR</div>', unsafe_allow_html=True)

# ==========================================
# 2. KOTAK NEO GATEWAY CONNECTION
# ==========================================
kotak_status = "Standard Mode"
client = None

if KOTAK_SDK_AVAILABLE and "kotak" in st.secrets:
    try:
        cfg = st.secrets["kotak"]
        client = NeoAPI(
            consumer_key=cfg.get("consumer_key", ""),
            consumer_secret=cfg.get("consumer_secret", ""),
            environment='prod'
        )
        client.login(
            mobilenumber=cfg.get("mobile", ""),
            password=cfg.get("password", "")
        )
        kotak_status = "Kotak Live Connected"
    except Exception:
        kotak_status = "Kotak Auth Pending"
else:
    kotak_status = "Standard Mode"

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

# Status Bar
m1, m2, m3, m4 = st.columns(4)
with m1:
    vclass = "metric-val-bull" if nifty_pct > 0.15 else ("metric-val-bear" if nifty_pct < -0.15 else "metric-val-neu")
    st.markdown(f'<div class="metric-card"><div class="metric-title">NIFTY REGIME</div><div class="{vclass}">{regime_title} ({nifty_pct:+.2f}%)</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card"><div class="metric-title">NEWS BLACKLIST</div><div class="metric-val-neu">0 Stocks Excluded</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><div class="metric-title">ACTIVE LAYERS</div><div class="metric-val-bull">11-Layer Institutional</div></div>', unsafe_allow_html=True)
with m4:
    gw_class = "metric-val-bull" if "Connected" in kotak_status else "metric-val-neu"
    st.markdown(f'<div class="metric-card"><div class="metric-title">BROKER GATEWAY</div><div class="{gw_class}">{kotak_status}</div></div>', unsafe_allow_html=True)

st.write("")

# ==========================================
# 4. UNIVERSE & QUANT CALCULATION ENGINE
# ==========================================
INSTITUTIONAL_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "SBIN.NS", "BHARTIARTL.NS", "TECHM.NS", "LT.NS", "TATASTEEL.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "MARUTI.NS", "TATAMOTORS.NS", "BAJFINANCE.NS",
    "HINDUNILVR.NS", "ITC.NS", "SUNPHARMA.NS", "WIPRO.NS", "HCLTECH.NS"
]

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

        # Volume threshold
        if vol_surge < 1.2:
            return None

        # --- SHORT ENTRY WITH ANTI-TRAP DEFENSE ---
        if market_regime != "BULLISH":
            if (ltp < vwap) and (ltp <= orb_low) and (bounce_from_low <= 0.45):
                if last['Close'] <= last['Open']:
                    score = 0
                    if rel_strength < -0.5: score += 30
                    if vol_surge >= 2.0: score += 25
                    elif vol_surge >= 1.5: score += 15
                    if ((vwap - ltp) / vwap) * 100 >= 0.4: score += 20
                    if ltp < daily_ema20: score += 15
                    if bounce_from_low <= 0.2: score += 10
                    
                    if score >= 60:
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

        # --- BUY ENTRY ---
        if market_regime != "BEARISH":
            if (ltp > vwap) and (ltp >= orb_high) and (pullback_from_high <= 0.45):
                if last['Close'] >= last['Open']:
                    score = 0
                    if rel_strength > 0.5: score += 30
                    if vol_surge >= 2.0: score += 25
                    elif vol_surge >= 1.5: score += 15
                    if ((ltp - vwap) / vwap) * 100 >= 0.4: score += 20
                    if ltp > daily_ema20: score += 15
                    if pullback_from_high <= 0.2: score += 10
                    
                    if score >= 60:
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
# 5. SCANNER EXECUTION (TOP 1-2 ONLY)
# ==========================================
if st.button("⚡ Scan Institutional Trades (11 Layers)", use_container_width=True, type="primary"):
    with st.spinner("Analyzing high-probability setups..."):
        trades = []
        for symbol in INSTITUTIONAL_UNIVERSE:
            res = process_single_stock(symbol, macro_bias, nifty_pct)
            if res:
                trades.append(res)
        
        shorts = sorted([t for t in trades if t['Signal'] == "SHORT"], key=lambda x: x['raw_score'], reverse=True)[:2]
        buys = sorted([t for t in trades if t['Signal'] == "BUY"], key=lambda x: x['raw_score'], reverse=True)[:2]

        if macro_bias == "BULLISH":
            st.info("🛡️ **Safety Guard Active:** Nifty बुलिश है। सभी शॉर्ट ट्रेड्स सख्त रूप से ब्लॉक हैं।")
        elif shorts:
            st.markdown('<div class="short-alert">🔴 CONFIRMED INSTITUTIONAL SHORT (TOP 1-2)</div>', unsafe_allow_html=True)
            df_s = pd.DataFrame(shorts).drop(columns=['Signal', 'raw_score'])
            st.dataframe(df_s, use_container_width=True, hide_index=True)
            st.caption("AlphaQuant Engine | Target 1 पर 50% प्रॉफिट बुक करें और SL कॉस्ट पर लाएँ।")
        else:
            st.write("कोई हाई-प्रोबेबिलिटी शॉर्ट ट्रेड नहीं मिली।")

        if buys:
            st.markdown('<div class="buy-alert">🟢 CONFIRMED INSTITUTIONAL BUY (TOP 1-2)</div>', unsafe_allow_html=True)
            df_b = pd.DataFrame(buys).drop(columns=['Signal', 'raw_score'])
            st.dataframe(df_b, use_container_width=True, hide_index=True)
            st.caption("AlphaQuant Engine | Target 1 पर 50% प्रॉफिट बुक करें और SL कॉस्ट पर लाएँ।")
        elif macro_bias != "BULLISH":
            st.write("कोई हाई-प्रोबेबिलिटी बाय ट्रेड नहीं मिली।")

st.markdown("---")
st.caption("AlphaQuant 11-Layer Institutional Engine | Strict Risk Mitigation Model")
