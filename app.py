import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI 美股分析系統", layout="wide")
st.title("🤖 AI 美股分析系統")

symbol = st.text_input("輸入股票代碼", "AAPL")

if st.button("查詢"):
    info = yf.Ticker(symbol).info
    st.json({
        "company": info.get("shortName"),
        "revenueGrowth": info.get("revenueGrowth"),
        "profitMargins": info.get("profitMargins"),
        "roe": info.get("returnOnEquity")
    })
