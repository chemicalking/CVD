import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import os
import warnings
from datetime import datetime

# Streamlit 設定
st.set_page_config(page_title="NF3 分析儀表板", page_icon=":bar_chart:", layout="wide")

st.title(":bar_chart: NF3 氣體使用與製程分析儀表板")

# 上傳文件
uploaded_file = st.file_uploader("上傳數據文件", type=["csv"])

if uploaded_file is not None:
    # 載入數據
    df = pd.read_csv(uploaded_file, encoding='utf-8')
else:
    os.chdir(r"D:\curso\streamlit\09_app_multipage\data")
    df = pd.read_csv("Merged_Data.csv", encoding='utf-8')

    # 從 RECIPEID 提取 LAYER 信息
    def extract_layer(recipe_id):
        if pd.isna(recipe_id):
            return 'Unknown'
        recipe_id = str(recipe_id).upper()
        if 'BP' in recipe_id:
            return 'BP'
        elif 'PFA' in recipe_id:
            return 'PFA'
        elif 'AS' in recipe_id:
            return 'AS'
        else:
            return 'OTHER'

    # 添加 LAYER 列
    df['LAYER'] = df['RECIPEID'].apply(extract_layer)

    # 自定義時間轉換函數
    def convert_timestamp(ts):
        try:
            ts = str(ts)
            if len(ts) >= 10:  # 確保字符串長度足夠
                year = ts[:4]
                month = ts[4:6]
                day = ts[6:8]
                hour = ts[8:10] if len(ts) >= 10 else "00"
                return f"{year}/{month}/{day} {hour}:00"
            return None
        except:
            return None

    # 轉換 TSTAMP 格式
    df['TSTAMP'] = df['TSTAMP'].apply(convert_timestamp)
    df['TSTAMP'] = pd.to_datetime(df['TSTAMP'], format='%Y/%m/%d %H:%M', errors='coerce')
    
    # 過濾 step_name 為 CLN1、CLN2、CLN3 的數據
    filtered_df = df[df['step_name'].isin(['CLN1', 'CLN2', 'CLN3'])].copy()
    
    # 添加每日日期欄位
    filtered_df['Date'] = filtered_df['TSTAMP'].dt.date

    # **1. Hierarchical TreeMap**
    st.subheader("Hierarchical view of NF3 Usage (Layer ->OPERATION-> SIN -> CHAMBERID)")
    
    # 按日期、LAYER、RECIPEID、CHAMBERID 匯總 NF3_total_Flow
    tree_data = filtered_df.groupby(['Date','LAYER', 'OPERATION', 'SIN', 'CHAMBERID'], as_index=False)['NF3_total_Flow'].sum()
    fig3 = px.treemap(tree_data, 
                      path=['OPERATION','LAYER',  'SIN', 'CHAMBERID'], 
                      values='NF3_total_Flow', 
                      color='CHAMBERID', 
                      hover_data=['NF3_total_Flow'])
    fig3.update_layout(width=800, height=650)
    fig3.update_traces(textinfo="label+value")
    st.plotly_chart(fig3, use_container_width=True)

    # **2. Pie Charts - 機台與製程分析**
    st.subheader("Pie Charts: Daily NF3 Usage Analysis")

    # 每日機台層級分析
    chamber_daily = filtered_df.groupby(['Date', 'CHAMBERID'], as_index=False)['NF3_total_Flow'].sum()
    
    # 將日期轉換為字符串用於顯示
    date_options = [(date, date.strftime('%Y/%m/%d')) for date in sorted(chamber_daily['Date'].unique())]
    selected_date_str = st.selectbox("選擇日期進行分析", 
                                   options=[date[1] for date in date_options],
                                   format_func=lambda x: x)
    
    # 將選擇的日期字符串轉換回原始日期對象
    daily_date = [date[0] for date in date_options if date[1] == selected_date_str][0]
    
    chamber_daily_filtered = chamber_daily[chamber_daily['Date'] == daily_date]
    recipe_daily = filtered_df.groupby(['Date', 'LAYER'], as_index=False)['NF3_total_Flow'].sum()
    recipe_daily_filtered = recipe_daily[recipe_daily['Date'] == daily_date]

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Chamber-wise NF3 Usage")
        fig = px.pie(chamber_daily_filtered, values='NF3_total_Flow', names='CHAMBERID', template='plotly_dark',
                     title=f"機台層級每日 NF3 使用分析 ({selected_date_str})")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Recipe-wise NF3 Usage")
        fig = px.pie(recipe_daily_filtered, values='NF3_total_Flow', names='LAYER', template='gridon',
                     title=f"製程層級每日 NF3 使用分析 ({selected_date_str})")
        st.plotly_chart(fig, use_container_width=True)
