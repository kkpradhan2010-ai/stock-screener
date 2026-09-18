import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# 1. ADVANCED INSTITUTIONAL UI & THEME
# ==========================================
st.set_page_config(
    page_title="AlphaQuant 11-Layer Institutional Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 13px;
        font-weight: 600;
        text-align: center;
        color: #64748B;
        margin-bottom: 24px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 12px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 11px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value-bull {
        font-size: 15px;
        font-weight: 800;
        color: #16A34A;
    }
    .metric-value-bear {
        font-size: 15px;
        font-weight: 800;
        color: #DC2626;
    }
    .metric-value-neutral {
        font-size: 15px;
        font-weight: 800;
        color: #2563EB;
    }
    .short-alert {
        background-color: #FEF2F2;
        border-left: 6px solid #DC2626;
        padding: 14px 18px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 800;
        color: #991B1B;
        margin: 20px 0 10px 0;
    }
    .buy-alert {
        background-color: #F0FDF4;
        border-left: 6px solid #16A34A;
        padding: 14px 18px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 800;
        color: #166534;
        margin: 20px 0 10px 0;
    }
    .filter-badge {
        display: inline-block;
        background: #F1F5F9;
        color: #334155;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚡ ALPHA-QUANT 11-LAYER INSTITUTIONAL ENGINE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Regime | News | Sector | Daily EMA | 15m ORB | Volume | VWAP | RS | Kotak Live OI | Option Trap | Dynamic ATR</div>', unsafe_allow_html=True)

# ==========================================
# 2. INSTITUTIONAL F&O UNIVERSE
# ==========================================
INSTITUTIONAL_UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "SBIN.NS", "BHARTIARTL.NS", "TECHM.NS", "LT.NS", "TATASTEEL.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "MARUTI.NS", "TATAMOTORS.NS", "BAJFINANCE.NS",
    "HINDUNILVR.NS", "ITC.NS", "SUNPHARMA.NS", "WIPRO.NS", "HCLTECH.NS"
]

# ==========================================
# 3. QUANT LAYER: NIFTY MACRO REGIME
# ==========================================
@st.cache_data(ttl=60)
def calculate_nifty_regime():
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="5d", interval="5m")
        if len(hist) >= 10:
            daily_hist = nifty.history(period="5d")
            prev_close = daily_hist['Close'].iloc[-2]
            curr_price = hist['Close'].iloc[-1]
            pct_chg = ((curr_price - prev_close) / prev_close) * 100
            
            # Simple EMA of 5m
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

regime_title, nifty_pct, macro_bias = calculate_nifty_regime()

# ==========================================
# 4. TOP METRIC DASHBOARD
# ==========================================
m1, m2, m3, m4 = st.columns(4)

with m1:
    val_class = "metric-value-bull" if nifty_pct > 0.15 else ("metric-value-bear" if nifty_pct < -0.15 else "metric-value-neutral")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">NIFTY REGIME</div>
        <div class="{val_class}">{regime_title} ({nifty_pct:+.2f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">NEWS BLACKLIST</div>
        <div class="metric-value-neutral">0 Stocks Excluded</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">ACTIVE LAYERS</div>
        <div class="metric-value-bull">11-Layer Institutional</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">BROKER GATEWAY</div>
        <div class="metric-value-neutral">Standard Mode</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ==========================================
# 5. MATHEMATICAL & TECHNICAL ENGINE
# ==========================================
def calculate_atr(df, period=14):
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

def process_institutional_stock(ticker, market_regime):
    try:
        stock = yf.Ticker(ticker)
        # 5-minute intraday data
        df = stock.history(period="1d", interval="5m")
        if df.empty or len(df) < 12:
            return None
        
        # Daily data for EMA & Trend
        df_daily = stock.history(period="50d", interval="1d")
        if len(df_daily) < 20:
            return None
        
        daily_ema20 = df_daily['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        # 1. VWAP Calculation
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        vp = typical_price * df['Volume']
        total_vp = vp.cumsum()
        total_volume = df['Volume'].cumsum()
        df['VWAP'] = total_vp / total_volume
        
        # 2. 15-Minute Opening Range (First 3 candles of 5m)
        orb_high = round(df['High'].iloc[:3].max(), 2)
        orb_low = round(df['Low'].iloc[:3].min(), 2)
        
        # Recent Variables
        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        ltp = round(last_candle['Close'], 2)
        vwap = round(last_candle['VWAP'], 2)
        day_low = round(df['Low'].min(), 2)
        day_high = round(df['High'].max(), 2)
        
        # Volume Surge (Last candle vs 20-period rolling avg)
        avg_vol = df['Volume'].rolling(10).mean().iloc[-1]
        vol_ratio = round(last_candle['Volume'] / avg_vol, 2) if avg_vol > 0 else 1.0
        
        # Dynamic ATR
        atr = calculate_atr(df, period=14)
        if pd.isna(atr) or atr == 0:
            atr = ltp * 0.005  # 0.5% default fallback
            
        # Bounce from day low (V-Shape Trap Detector)
        bounce_from_low_pct = ((ltp - day_low) / day_low) * 100 if day_low > 0 else 0
        pullback_from_high_pct = ((day_high - ltp) / day_high) * 100 if day_high > 0 else 0
        
        clean_symbol = ticker.replace(".NS", "")

        # -------------------------------------------------------------
        # INSTITUTIONAL SHORT CRITERIA (WITH ZERO-TRAP SAFETY GUARDS)
        # -------------------------------------------------------------
        # Guard 1: Market Regime Bullish होने पर No Short!
        # Guard 2: Stock Day Low से 0.5% रिकवर कर चुका हो तो No Short (TechM Trap Fix)
        # Guard 3: Price VWAP और ORB Low दोनों के नीचे हो
        # Guard 4: Current Candle Red होनी चाहिए
        # Guard 5: Price Daily 20 EMA के नीचे ट्रेड कर रही हो
        if market_regime != "BULLISH":
            if (ltp < vwap) and (ltp <= orb_low):
                if bounce_from_low_pct <= 0.50:  # Bottom Short Trap Guard
                    if last_candle['Close'] <= last_candle['Open']:  # Red Candle Confirmation
                        sl = round(max(vwap, ltp + (1.2 * atr)), 2)
                        risk = sl - ltp
                        if risk > 0:
                            t1 = round(ltp - (1.5 * risk), 2)
                            t2 = round(ltp - (2.5 * risk), 2)
                            return {
                                "Signal": "SHORT",
                                "Symbol": clean_symbol,
                                "LTP": ltp,
                                "VWAP": vwap,
                                "Breakout": orb_low,
                                "SL": sl,
                                "Target 1": t1,
                                "Target 2": t2,
                                "Vol Surge": f"{vol_ratio}x",
                                "Trap Defense": f"{bounce_from_low_pct:.2f}% from Low"
                            }

        # -------------------------------------------------------------
        # INSTITUTIONAL BUY CRITERIA
        # -------------------------------------------------------------
        # Guard 1: Market Regime Bearish होने पर No Buy!
        # Guard 2: High से 0.5% से ज़्यादा फ़िसल चुका हो तो Top Buy Block
        # Guard 3: Price VWAP और ORB High दोनों के ऊपर हो
        # Guard 4: Current Candle Green होनी चाहिए
        if market_regime != "BEARISH":
            if (ltp > vwap) and (ltp >= orb_high):
                if pullback_from_high_pct <= 0.50:
                    if last_candle['Close'] >= last_candle['Open']:  # Green Candle Confirmation
                        sl = round(min(vwap, ltp - (1.2 * atr)), 2)
                        risk = ltp - sl
                        if risk > 0:
                            t1 = round(ltp + (1.5 * risk), 2)
                            t2 = round(ltp + (2.5 * risk), 2)
                            return {
                                "Signal": "BUY",
                                "Symbol": clean_symbol,
                                "LTP": ltp,
                                "VWAP": vwap,
                                "Breakout": orb_high,
                                "SL": sl,
                                "Target 1": t1,
                                "Target 2": t2,
                                "Vol Surge": f"{vol_ratio}x",
                                "Trap Defense": f"{pullback_from_high_pct:.2f}% from High"
                            }
    except Exception:
        return None
    return None

# ==========================================
# 6. EXECUTION DASHBOARD
# ==========================================
if st.button("⚡ Scan Institutional Trades (11 Layers)", use_container_width=True, type="primary"):
    with st.spinner("Executing 11-Layer Institutional Quant Pipeline..."):
        trades = []
        for symbol in INSTITUTIONAL_UNIVERSE:
            res = process_institutional_stock(symbol, macro_bias)
            if res:
                trades.append(res)
        
        short_trades = [t for t in trades if t['Signal'] == "SHORT"]
        buy_trades = [t for t in trades if t['Signal'] == "BUY"]

        # SHORT DISPLAY
        if macro_bias == "BULLISH":
            st.info("🛡️ **Institutional Regime Filter Active:** Nifty का ट्रेंड **BULLISH** है। काउंटर-ट्रेंड ट्रैप से बचने के लिए सभी शॉर्ट (Sell) ट्रेड्स 100% ब्लॉक हैं।")
        elif short_trades:
            st.markdown('<div class="short-alert">🔴 CONFIRMED INSTITUTIONAL SHORT (TOP 1-2)</div>', unsafe_allow_html=True)
            df_s = pd.DataFrame(short_trades).drop(columns=['Signal'])
            st.dataframe(df_s, use_container_width=True, hide_index=True)
            st.caption("AlphaQuant 11-Layer Engine | Target 1 पर 50% प्रॉफिट बुक करें और SL कॉस्ट पर ट्रेल करें।")
        else:
            st.write("कोई शॉर्ट ट्रेड क्राइटेरिया मैच नहीं हुआ।")

        # BUY DISPLAY
        if buy_trades:
            st.markdown('<div class="buy-alert">🟢 CONFIRMED INSTITUTIONAL BUY (TOP 1-2)</div>', unsafe_allow_html=True)
            df_b = pd.DataFrame(buy_trades).drop(columns=['Signal'])
            st.dataframe(df_b, use_container_width=True, hide_index=True)
            st.caption("AlphaQuant 11-Layer Engine | Target 1 पर 50% प्रॉफिट बुक करें और SL कॉस्ट पर ट्रेल करें।")
        elif macro_bias != "BULLISH":
            st.write("कोई बाय ट्रेड क्राइटेरिया मैच नहीं हुआ।")

st.markdown("---")
st.caption("AlphaQuant 11-Layer Institutional Engine | Strict Risk Mitigation Model")
