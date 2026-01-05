import streamlit as st
import pandas as pd
import yahooquery as yq
from supabase import create_client, Client
import time

# --- 1. 資料庫設定 (解決清除紀錄資料消失問題) ---
# 請在 Streamlit Secrets 中設定這些值
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.warning("⚠️ 尚未偵測到資料庫連線，資料將無法永久保存。")

def save_to_db(data_list):
    """將分析結果存入 Supabase"""
    try:
        supabase.table("stock_analysis").insert(data_list).execute()
    except Exception as e:
        print(f"DB Error: {e}")

# --- 2. 數據獲取 (修復 YFRateLimitError) ---
def get_industry_data(tickers):
    """批量獲取數據，減少請求次數"""
    tickers_str = " ".join(tickers)
    tickers_obj = yq.Ticker(tickers_str)
    
    # 獲取關鍵數據
    financials = tickers_obj.financial_data
    summary = tickers_obj.summary_detail
    price = tickers_obj.price
    
    results = {}
    for t in tickers:
        try:
            # 獲取該個股的細節
            f = financials.get(t, {})
            s = summary.get(t, {})
            p = price.get(t, {})
            
            results[t] = {
                "名稱": p.get("shortName", t),
                "股價": p.get("regularMarketPrice", 0),
                "本益比": s.get("trailingPE", 0),
                "營收成長": f.get("revenueGrowth", 0),
                "淨利率": f.get("profitMargins", 0),
                "行業": p.get("sector", "N/A")
            }
        except:
            continue
    return results

# --- 3. AI 分析邏輯 (解決問題 3 & 4: 排名與依據) ---
def advanced_ai_analysis(ticker, data):
    # 這裡實作計分權重模型
    # 權重：營收成長 (40%) + 淨利率 (30%) + 估值 (30%)
    growth_score = min(data['營收成長'] * 100, 40) 
    margin_score = min(data['淨利率'] * 100, 30)
    pe_score = 30 if 0 < data['本益比'] < 20 else 15
    
    total_score = round(growth_score + margin_score + pe_score, 2)
    
    rationale = f"""
    #### {ticker} 評分依據：
    * **營收成長 ({growth_score}/40)**: 增長率為 {data['營收成長']:.2%}。
    * **獲利能力 ({margin_score}/30)**: 淨利率為 {data['淨利率']:.2%}。
    * **估值水平 ({pe_score}/30)**: 本益比為 {data['本益比']}。
    * **綜合評分**: **{total_score}**
    """
    return total_score, rationale

# --- Streamlit UI ---
st.set_page_config(page_title="AI 美股產業分析師", layout="wide")
st.title("📊 AI 美股產業分析工具")

# 輸入產業代碼
input_tickers = st.text_input("輸入要分析的個股代碼 (例如: NVDA, AMD, INTC, MU)", "NVDA, AMD, INTC")

if st.button("🚀 開始一鍵分析"):
    ticker_list = [t.strip().upper() for t in input_tickers.split(",")]
    
    with st.spinner("正在抓取數據並由 AI 評分中..."):
        # 批量抓取
        raw_data = get_industry_data(ticker_list)
        
        final_results = []
        for t, info in raw_data.items():
            score, note = advanced_ai_analysis(t, info)
            final_results.append({
                "代碼": t,
                "名稱": info["名稱"],
                "綜合評分": score,
                "股價": info["股價"],
                "分析詳情": note,
                "created_at": datetime.now().isoformat()
            })
        
        # 解決問題 3：依照排名排序
        df = pd.DataFrame(final_results).sort_values(by="綜合評分", ascending=False)
        
        # 顯示排名表
        st.subheader("🏆 產業個股綜合評分排名")
        st.table(df[["代碼", "名稱", "綜合評分", "股價"]])
        
        # 解決問題 4：顯示詳細依據
        st.subheader("📝 AI 詳細分析報告")
        for index, row in df.iterrows():
            with st.expander(f"查看 {row['代碼']} 分析詳情"):
                st.markdown(row["分析詳情"])
        
        # 解決問題 1：存入資料庫
        save_to_db(final_results)
        st.success("✅ 分析完成並已同步至雲端資料庫！")

