import streamlit as st
import pandas as pd
import plotly.express as px
from matplotlib import rcParams
from matplotlib import font_manager
import matplotlib.pyplot as plt
import altair as alt
import plotly.figure_factory as ff

# Page configuration
st.set_page_config(
    page_title="NF3 Gas Flow Analysis",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")
alt.themes.enable("dark")

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 確保字體可用
def setup_chinese_font():
    try:
        # 嘗試使用正黑體
        font_path = 'C:/Windows/Fonts/msjh.ttc'  # 正黑體路徑
        font_prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    except:
        try:
            # 嘗試使用微軟雅黑
            font_path = 'C:/Windows/Fonts/msyh.ttc'  # 微軟雅黑路徑
            font_prop = font_manager.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
        except:
            # 如果都失敗，使用系統默認中文字體
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']

setup_chinese_font()

# 載入資料
data = pd.read_csv(r"D:\curso\streamlit\09_app_multipage\data\Merged_Data.csv", encoding='utf-8', sep=',')

# 將所有流量數據四捨五入到小數點後兩位
flow_columns = ['NF3_total_Flow', 'Daily_Flow_sccm', 'Daily_Flow_kg', 'Daily_Flow_l']
for col in flow_columns:
    if col in data.columns:
        data[col] = data[col].round(2)

# 打印列名
st.write("DataFrame 列名：", data.columns.tolist())

data['LAYER'] = data['RECIPEID'].str.extract('(BP|PFA|AS)')

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
data['TSTAMP'] = data['TSTAMP'].apply(convert_timestamp)
data['TSTAMP'] = pd.to_datetime(data['TSTAMP'], format='%Y/%m/%d %H:%M', errors='coerce')

# 過濾 step_name 為 CLN1、CLN2、CLN3 的數據
filtered_data = data[data['step_name'].isin(['CLN1', 'CLN2', 'CLN3'])].copy()

# 添加每日日期欄位
filtered_data['Date'] = filtered_data['TSTAMP'].dt.date

# 定義單位轉換常數
SCCM_TO_KG = 3.04 / (1000 * 60)
SCCM_TO_LITER = 1 / 60000
SCCM_TO_SCCM = 1

# TreeMap 可視化
def visualize_treemap(data):
    st.subheader("Hierarchical view of NF3 Usage (Layer -> RECIPEID -> CHAMBERID)")
    
    tree_data = filtered_data.groupby(['Date','LAYER', 'RECIPEID', 'CHAMBERID'], as_index=False)['NF3_total_Flow'].sum()
    tree_data['NF3_total_Flow'] = tree_data['NF3_total_Flow'].round(2)
    
    fig3 = px.treemap(tree_data, 
                      path=['LAYER', 'RECIPEID', 'CHAMBERID'], 
                      values='NF3_total_Flow', 
                      color='CHAMBERID', 
                      hover_data=['NF3_total_Flow'])
    fig3.update_layout(width=800, height=650)
    fig3.update_traces(textinfo="label+value")
    st.plotly_chart(fig3, use_container_width=True)

# 計算每日 NF3 用量與單片玻璃耗氣量
def analyze_layer_chamberid(data):
    st.header("LAYER 與 CHAMBERID 分析")

    # 過濾近 30 日資料
    max_date = data['TSTAMP'].max()
    min_date = max_date - pd.Timedelta(days=30)
    recent_data = data[(data['TSTAMP'] >= min_date) & (data['TSTAMP'] <= max_date)]

    # 每日 NF3 用量計算
    daily_flow = recent_data.groupby(['LAYER', 'CHAMBERID', recent_data['TSTAMP'].dt.date])['NF3_total_Flow'].sum().reset_index()
    daily_flow['NF3_total_Flow'] = daily_flow['NF3_total_Flow'].round(2)
    daily_flow['Daily_Flow_sccm'] = (daily_flow['NF3_total_Flow'] * SCCM_TO_SCCM).round(2)
    daily_flow['Daily_Flow_kg'] = (daily_flow['NF3_total_Flow'] * SCCM_TO_KG).round(2)
    daily_flow['Daily_Flow_l'] = (daily_flow['NF3_total_Flow'] * SCCM_TO_LITER).round(2)

    # 顯示每日 NF3 用量
    st.subheader("每日 NF3 用量")
    st.dataframe(daily_flow.style.format({
        "NF3_total_Flow": "{:.2f}",
        "Daily_Flow_sccm": "{:.2f}", 
        "Daily_Flow_kg": "{:.2f}", 
        "Daily_Flow_l": "{:.2f}"
    }))

    # 單片玻璃耗氣量
    glassid_count = recent_data.groupby(['CHAMBERID', 'LAYER', recent_data['TSTAMP'].dt.date])['GLASSID'].nunique().reset_index()
    glassid_count = glassid_count.rename(columns={'GLASSID': 'Glass_Count'})
    glass_flow = pd.merge(daily_flow, glassid_count, on=['CHAMBERID', 'LAYER', 'TSTAMP'], how='left')
    glass_flow['Flow_per_Glass_sccm'] = (glass_flow['Daily_Flow_sccm'] / glass_flow['Glass_Count']).round(2)
    glass_flow['Flow_per_Glass_kg'] = (glass_flow['Daily_Flow_kg'] / glass_flow['Glass_Count']).round(2)
    glass_flow['Flow_per_Glass_l'] = (glass_flow['Daily_Flow_l'] / glass_flow['Glass_Count']).round(2)

    st.subheader("單片玻璃耗氣量")
    st.dataframe(glass_flow.style.format({
        "NF3_total_Flow": "{:.2f}",
        "Daily_Flow_sccm": "{:.2f}", 
        "Daily_Flow_kg": "{:.2f}", 
        "Daily_Flow_l": "{:.2f}",
        "Flow_per_Glass_sccm": "{:.2f}", 
        "Flow_per_Glass_kg": "{:.2f}", 
        "Flow_per_Glass_l": "{:.2f}"
    }))

# 單次 RPSC 耗氣量分析
def analyze_rpsc_usage(data):
    st.header("單次 RPSC 耗氣量分析")

    # 過濾近 30 日資料
    max_date = data['TSTAMP'].max()
    min_date = max_date - pd.Timedelta(days=30)
    recent_data = data[(data['TSTAMP'] >= min_date) & (data['TSTAMP'] <= max_date)]

    # 過濾 RPSC 資料
    rpsc_data = recent_data[recent_data['RECIPEID'].str.startswith('RPSC')]

    # 單次 RPSC 耗氣量計算
    rpsc_daily_flow = rpsc_data.groupby(['CHAMBERID', rpsc_data['TSTAMP'].dt.date])['NF3_total_Flow'].sum().reset_index()
    rpsc_daily_flow['NF3_total_Flow'] = rpsc_daily_flow['NF3_total_Flow'].round(2)
    rpsc_daily_flow['Daily_Flow_sccm'] = (rpsc_daily_flow['NF3_total_Flow'] * SCCM_TO_SCCM).round(2)
    rpsc_daily_flow['Daily_Flow_kg'] = (rpsc_daily_flow['NF3_total_Flow'] * SCCM_TO_KG).round(2)
    rpsc_daily_flow['Daily_Flow_l'] = (rpsc_daily_flow['NF3_total_Flow'] * SCCM_TO_LITER).round(2)

    rpsc_glassid_count = rpsc_data.groupby(['CHAMBERID', rpsc_data['TSTAMP'].dt.date])['GLASSID'].nunique().reset_index()
    rpsc_glassid_count = rpsc_glassid_count.rename(columns={'GLASSID': 'RPSC_Glass_Count'})

    rpsc_usage = pd.merge(rpsc_daily_flow, rpsc_glassid_count, on=['CHAMBERID', 'TSTAMP'], how='left')
    rpsc_usage['Flow_per_RPSC_sccm'] = (rpsc_usage['Daily_Flow_sccm'] / rpsc_usage['RPSC_Glass_Count']).round(2)
    rpsc_usage['Flow_per_RPSC_kg'] = (rpsc_usage['Daily_Flow_kg'] / rpsc_usage['RPSC_Glass_Count']).round(2)
    rpsc_usage['Flow_per_RPSC_l'] = (rpsc_usage['Daily_Flow_l'] / rpsc_usage['RPSC_Glass_Count']).round(2)

    st.subheader("單次 RPSC 耗氣量")
    st.dataframe(rpsc_usage.style.format({
        "NF3_total_Flow": "{:.2f}",
        "Daily_Flow_sccm": "{:.2f}", 
        "Daily_Flow_kg": "{:.2f}", 
        "Daily_Flow_l": "{:.2f}",
        "Flow_per_RPSC_sccm": "{:.2f}", 
        "Flow_per_RPSC_kg": "{:.2f}", 
        "Flow_per_RPSC_l": "{:.2f}"
    }))

# Streamlit 應用程式主邏輯
def main():
    st.title("NF3 氣體流量與使用分析儀表板")

    # TreeMap 可視化
    visualize_treemap(data)

    # LAYER 與 CHAMBERID 分析
    analyze_layer_chamberid(data)

    # 單次 RPSC 耗氣量分析
    analyze_rpsc_usage(data)

if __name__ == "__main__":
    main()

