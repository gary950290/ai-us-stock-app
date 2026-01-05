import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# -----------------------------
# 初始化快取
# -----------------------------
if "ai_cache" not in st.session_state:
    st.session_state.ai_cache = {}

# -----------------------------
# 模擬 AI 分析函式
# -----------------------------
def ai_analyze(symbol, info, model):
    """
    呼叫 Gemini 或 Claude LLM 生成分析結果
    回傳格式：
    {
        "symbol": symbol,
        "score": 0-100,
        "reason": ["原因1"],
        "risk": ["風險1"]
    }
    """
    try:
        # model.generate_content 或你實際呼叫 Gemini/Claude 的程式碼
        # 這裡示範用假資料
        score = round(50 + hash(symbol)%50, 2)
        return {"symbol": symbol, "score": score, "reason":["AI 分析結果"], "risk":[]}
    except:
        # fallback
        return {"symbol": symbol, "score": 50, "reason":["AI 無法回傳，使用暫定分數"], "risk":[]}

# -----------------------------
# 快取處理
# -----------------------------
def get_ai_result(symbol, info, model, cache_hours=24):
    cached = st.session_state.ai_cache.get(symbol)
    if cached and datetime.now() - cached["time"] < timedelta(hours=cache_hours):
        return cached["data"], True
    result = ai_analyze(symbol, info, model)
    st.session_state.ai_cache[symbol] = {"data": result, "time": datetime.now()}
    return result, False

# -----------------------------
# UI: 單支分析
# -----------------------------
st.subheader("單支股票分析")
symbol_input = st.text_input("輸入股票代碼", "AAPL")

if st.button("分析單支股票"):
    info = {"price": 100, "market_cap": 1e11}  # 你可改成從 Gemini/Claude 抓股價
    result, from_cache = get_ai_result(symbol_input, info, model="Gemini")
    if from_cache:
        st.info("使用快取結果")
    st.json(result)

# -----------------------------
# UI: 一鍵產業分析
# -----------------------------
st.subheader("一鍵分析產業股票")
industry_symbols = st.text_area("輸入產業股票代碼，用逗號分隔", "AAPL,MSFT,GOOGL").replace(" ", "").split(",")

if st.button("分析整個產業"):
    all_results = []
    progress = st.progress(0)
    for i, sym in enumerate(industry_symbols):
        info = {"price": 100, "market_cap": 1e11}
        result, _ = get_ai_result(sym, info, model="Gemini")
        all_results.append(result)
        progress.progress((i+1)/len(industry_symbols))
    
    df = pd.DataFrame(all_results)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)
    df = df.sort_values(by="score", ascending=False)
    st.dataframe(df.reset_index(drop=True))
