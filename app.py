import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="NSE Live Connection Test", layout="wide")
st.title("🛰️ NSE Official Live Data & OI Pipeline Test")
st.caption("यह टेस्ट सीधे NSE के आधिकारिक सर्वर से लाइव F&O डेटा और Open Interest (OI) खींचता है।")

def test_nse_connection():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com/"
    }
    
    try:
        # स्टेप 1: NSE होमपेज से कुकीज लेना
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        time.sleep(1)
        
        # स्टेप 2: लाइव F&O डेटा एंडपॉइंट को कॉल करना
        url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20FO"
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            raw_stocks = data.get('data', [])
            
            parsed_list = []
            for item in raw_stocks:
                if item.get('priority') == 0:
                    parsed_list.append({
                        "Symbol": item.get('symbol'),
                        "LTP": item.get('lastPrice'),
                        "Day Change %": item.get('pChange'),
                        "Day High": item.get('dayHigh'),
                        "Day Low": item.get('dayLow'),
                        "Total Traded Vol": item.get('totalTradedVolume'),
                        "Open Interest (OI)": item.get('openInterest', 'N/A'),
                        "OI Change %": item.get('pchangeinOpenInterest', 'N/A')
                    })
            return True, pd.DataFrame(parsed_list), None
        else:
            return False, None, f"HTTP Error: {response.status_code}"
            
    except Exception as e:
        return False, None, str(e)

if st.button("🔌 Test NSE Live Pipeline Now", use_container_width=True):
    with st.spinner("NSE सर्वर से संपर्क हो रहा है और लाइव डेटा खींचा जा रहा है..."):
        success, df_data, err_msg = test_nse_connection()
        
        if success and df_data is not None and not df_data.empty:
            st.success(f"✅ कनेक्शन 100% सफल! कुल {len(df_data)} F&O स्टॉक्स का डेटा और रियल OI प्राप्त हुआ।")
            st.dataframe(df_data.head(15), use_container_width=True)
        else:
            st.error("❌ NSE सर्वर ने कनेक्शन स्वीकार नहीं किया।")
            st.code(err_msg)
