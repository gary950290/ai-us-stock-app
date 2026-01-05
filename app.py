import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import json

# -----------------------------
# 初始化快取
# -----------------------------
if "ai_cache" not in st.session_state:
    st.session_state.ai_cache = {}

AI_SLEEP = 1
AI_CACHE_HOURS = 24

# -----------------------------
# 呼叫 Gemini / Claude
# -----------------------------
def ai_analyze(symbol, info, model):
    prompt = f"""
    你是美股分析師，分析股票 {symbol}。
    股票資訊：
    股價: {info.get('price',0)}
    市值: {info.get('market_cap',0)}
    請生成 JSON：
    {{
      "score": 0-100,
      "reason": ["列出 3~5 條分析理由"],
      "risk": ["列出 3~5 條潛在風險"]
    }}
    """
    # 在這裡放實際 model.generate_content 呼叫
    # 回傳 JSON
    # 以下示範假資料，實際請替換成真實呼叫
    score = round(50 + hash(symbol) % 50, 2)
    reason = [f"{symbol} 真實分析理由 {i}" for i in range(1,4)]
    risk = [f"{symbol} 真實風險 {i}" for i in range(1,4)]
    time.sleep(AI_SLEEP)
    return {"symbol": symbol, "score": score, "reason": reason, "risk": risk}

# -----------------------------
# 快取管理
# -----------------------------
def get_ai_result(symbol, info, model):
    cached = st.session_state.ai_cache.get(symbol)
    if cached and datetime.now() - cached["time"] < timedelta(hours=AI_CACHE_HOURS):
        return cached["data"], True
    result = ai_analyze(symbol, info, model)
    st.session_state.ai_cache[symbol] = {"data": result, "time": datetime.now()}
    return result, False

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("📊 AI 美股產業分析系統")

# 單支股票
st.subheader("單支股票分析")
symbol_input = st.text_input("輸入股票代碼", "AAPL")
if st.button("分析單支股票"):
    info = {"price": 100, "market_cap": 1e11}
    result, from_cache = get_ai_result(symbol_input, info, model="Gemini")
    if from_cache:
        st.info("使用快取結果")
    st.json(result)

# 一鍵產業分析
st.subheader("一鍵分析產業股票")
industry_symbols = st.text_area("輸入產業股票代碼，用逗號分隔", "AAPL,MSFT,GOOGL").replace(" ","").split(",")
if st.button("分析整個產業"):
    all_results = []
    progress = st.progress(0)
    total = len(industry_symbols)
    for i, sym in enumerate(industry_symbols):
        info = {"price": 100, "market_cap": 1e11}
        result, _ = get_ai_result(sym, info, model="Gemini")
        all_results.append(result)
        progress.progress((i+1)/total)
    df = pd.DataFrame(all_results)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    df = df.sort_values(by="score", ascending=False)
    st.subheader("產業股票排名（依分數排序）")
    st.dataframe(df.reset_index(drop=True))
