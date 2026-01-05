import streamlit as st
import yfinance as yf
import google.generativeai as genai
import json
import time

st.set_page_config(page_title="AI 美股分析系統", layout="wide")
st.title("🤖 AI 美股分析系統（穩定版）")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

AI_SLEEP = 3

@st.cache_data(ttl=3600)
def get_stock_fast_info(symbol):
    ticker = yf.Ticker(symbol)
    fi = ticker.fast_info
    return {
        "last_price": fi.get("last_price"),
        "market_cap": fi.get("market_cap"),
        "volume": fi.get("volume"),
    }

def ai_analyze(symbol, info):
    prompt = f"""
你是投資分析師，請分析 {symbol}

股價: {info.get("last_price")}
市值: {info.get("market_cap")}

請輸出 JSON：
{{
 "score": 0-100,
 "reason": ["原因1", "原因2"],
 "risk": ["風險1"]
}}
"""
    res = model.generate_content(prompt)
    time.sleep(AI_SLEEP)
    return json.loads(res.text)

symbol = st.text_input("股票代碼", "AAPL")

if st.button("AI 分析"):
    info = get_stock_fast_info(symbol)
    result = ai_analyze(symbol, info)
    st.json(result)
