import streamlit as st
import yfinance as yf
import pandas as pd
import google.generativeai as genai
import json
import time
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded
from datetime import datetime, timedelta

# =====================
# Streamlit 頁面設定
# =====================
st.set_page_config(page_title="AI 美股產業分析", layout="wide")
st.title("🤖 AI 美股產業分析系統（穩定版）")

# =====================
# Gemini API 設定
# =====================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

AI_SLEEP = 2       # 每次呼叫 AI 等待秒數
AI_CACHE_HOURS = 24

# =====================
# 保底結果函式
# =====================
def fallback_ai_result(symbol):
    return {
        "symbol": symbol,
        "score": None,
        "reason": ["AI 暫時無法提供分析（Free API 限制或網路問題）"],
        "risk": []
    }

# =====================
# Yahoo Finance 快取
# =====================
@st.cache_data(ttl=3600)
def get_stock_fast_info(symbol):
    ticker = yf.Ticker(symbol)
    fi = ticker.fast_info
    # 轉成乾淨 dict
    return {
        "symbol": symbol,
        "last_price": fi.get("last_price"),
        "market_cap": fi.get("market_cap"),
        "volume": fi.get("volume")
    }

# =====================
# AI 分析函式（保護版）
# =====================
def ai_analyze(symbol, info):
    prompt = f"""
你是美股投資分析師，請分析 {symbol}

股價: {info.get('last_price')}
市值: {info.get('market_cap')}

請只輸出 JSON：
{{
 "score": 0-100,
 "reason": ["原因1", "原因2"],
 "risk": ["風險1"]
}}
"""
    try:
        res = model.generate_content(prompt, request_options={"timeout": 15})
        time.sleep(AI_SLEEP)
        text = res.text.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except (ResourceExhausted, DeadlineExceeded):
        return fallback_ai_result(symbol)
    except Exception:
        return fallback_ai_result(symbol)

# =====================
# Session 快取 AI 結果，避免重複呼叫
# =====================
if "ai_cache" not in st.session_state:
    st.session_state.ai_cache = {}

def get_ai_result(symbol, info):
    cached = st.session_state.ai_cache.get(symbol)
    if cached and datetime.now() - cached["time"] < timedelta(hours=AI_CACHE_HOURS):
        return cached["data"], True
    else:
        result = ai_analyze(symbol, info)
        st.session_state.ai_cache[symbol] = {"data": result, "time": datetime.now()}
        return result, False

# =====================
# UI：單一股票分析
# =====================
st.subheader("單支股票分析")
symbol_input = st.text_input("輸入股票代碼", "AAPL")

if st.button("分析單支股票"):
    info = get_stock_fast_info(symbol_input)
    result, from_cache = get_ai_result(symbol_input, info)
    if from_cache:
        st.info("使用快取結果（未重新呼叫 AI）")
    st.json(result)

# =====================
# UI：一鍵產業分析
# =====================
st.subheader("一鍵分析產業股票")
# 預設產業股票池，可自行修改
industry_symbols = st.text_area(
    "輸入產業股票代碼，用逗號分隔",
    "AAPL,MSFT,GOOGL,AMZN,NVDA"
).replace(" ", "").split(",")

if st.button("分析整個產業"):
    all_results = []
    progress = st.progress(0)
    total = len(industry_symbols)

    for i, sym in enumerate(industry_symbols):
        info = get_stock_fast_info(sym)
        result, _ = get_ai_result(sym, info)
        all_results.append(result)
        progress.progress((i + 1) / total)

    # 排名
    df = pd.DataFrame(all_results)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df.sort_values(by="score", ascending=False)
    st.subheader("產業股票排名（依 AI 分數）")
    st.dataframe(df.reset_index(drop=True))
