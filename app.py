import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import time

# 這裡建議串接資料庫如 Supabase，以下先用 Streamlit Cache 模擬
# 如果要解決問題 1，必須在這裡串接資料庫存取 API

def get_stock_data(ticker):
    """抓取個股基本數據"""
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "名稱": info.get("longName", ticker),
        "股價": info.get("currentPrice", 0),
        "本益比": info.get("trailingPE", "N/A"),
        "營收成長": info.get("revenueGrowth", 0)
    }

def ai_analyze_stock(ticker, data):
    """
    解決問題 4：AI 個股分析依據與評分
    """
    # 這裡串接 OpenAI / Gemini API
    # 模擬評分邏輯
    score = 70 + (data['營收成長'] * 100) # 僅為範例
    analysis_rationale = f"""
    ### {ticker} 分析報告
    - **財務面 (40%)**: 營收成長率為 {data['營收成長']:.2%}，表現優異。
    - **技術面 (30%)**: 股價目前為 {data['股價']}，處於區間震盪。
    - **評分標準**: 本系統採計 40% 財務 + 30% 技術 + 30% 市場熱度。
    """
    return round(score, 2), analysis_rationale

st.title("📈 專業美股 AI 產業分析工具")

# 1. 產業個股輸入 (解決問題 2: 一鍵分析)
industry_tickers = st.text_input("輸入產業代碼 (用逗號隔開)", "AAPL,MSFT,GOOGL,AMZN")

if st.button("開始一鍵分析產業個股"):
    tickers_list = [t.strip().upper() for t in industry_tickers.split(",")]
    results = []
    
    progress_bar = st.progress(0)
    for idx, ticker in enumerate(tickers_list):
        with st.status(f"正在分析 {ticker}...", expanded=False):
            data = get_stock_data(ticker)
            score, rationale = ai_analyze_stock(ticker, data)
            results.append({
                "代碼": ticker,
                "名稱": data["名稱"],
                "綜合評分": score,
                "分析依據": rationale,
                "股價": data["股價"]
            })
        progress_bar.progress((idx + 1) / len(tickers_list))

    # 2. 依照排名排序 (解決問題 3)
    df = pd.DataFrame(results)
    df = df.sort_values(by="綜合評分", ascending=False)

    st.subheader("🏆 產業個股綜合排名")
    st.dataframe(df[["代碼", "名稱", "綜合評分", "股價"]], hide_index=True)

    # 3. 顯示詳細分析 (解決問題 4)
    st.divider()
    for res in results:
        with st.expander(f"查看 {res['代碼']} - {res['名稱']} 詳細分析 (得分: {res['綜合評分']})"):
            st.markdown(res["分析依據"])
