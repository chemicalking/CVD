import streamlit as st
import altair as alt
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib import font_manager

# Page configuration
st.set_page_config(
    page_title="NF3 氣體流量與使用儀表板",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")
alt.themes.enable("dark")
# 設定 Matplotlib 字體
try:
    noto_sans_path = font_manager.findfont("Noto Sans CJK TC")
    custom_font = font_manager.FontProperties(fname=noto_sans_path)
    rcParams['font.sans-serif'] = ['Serif']
except Exception:
    try:
        arial_path = font_manager.findfont("Arial")
        custom_font = font_manager.FontProperties(fname=arial_path)
        rcParams['font.sans-serif'] = ['Serif']
    except Exception:
        rcParams['font.sans-serif'] = ['Serif']
rcParams['axes.unicode_minus'] = False

# 載入資料
data = pd.read_csv(r"D:\curso\streamlit\09_app_multipage\data\Merged_Data.csv")
data['TSTAMP'] = pd.to_datetime(data['TSTAMP'], format='%Y%m%d%H')

# 計算最近 30 天的資料範圍
max_date = data['TSTAMP'].max()
min_date = max_date - pd.Timedelta(days=30)
recent_data = data[(data['TSTAMP'] >= min_date) & (data['TSTAMP'] <= max_date)]

# 計算近 30 日各 CHAMBERID 的生產片數
def calculate_chamberid_stats(recent_data):
    st.header("近 30 日各 CHAMBERID 的生產片數")

    # 計算每個 CHAMBERID 的 GLASSID 數量
    chamberid_glassid_count = recent_data.groupby('CHAMBERID')['GLASSID'].nunique().reset_index()
    chamberid_glassid_count.columns = ['CHAMBERID', 'Unique_GLASSID_Count']

    # 顯示表格
    st.dataframe(chamberid_glassid_count)

# GLASSID 與 PRODUCT 的分析
def analyze_glassid_and_product(recent_data):
    st.header("GLASSID 與 PRODUCT 分析")
    recent_data['GLASSID_prefix'] = recent_data['GLASSID'].astype(str).str[:4]
    recent_data['PRODUCT_prefix'] = recent_data['PRODUCT'].astype(str).str[:4]

    # 過濾匹配 GLASSID 與 PRODUCT 的資料
    filtered_data = recent_data[recent_data['GLASSID_prefix'] == recent_data['PRODUCT_prefix']]

    glassid_count = filtered_data['GLASSID'].nunique()
    st.write(f"GLASSID 與 PRODUCT 前四碼匹配的玻璃片數量: {glassid_count}")

    # 表格顯示
    filtered_data['TSTAMP'] = filtered_data['TSTAMP'].dt.date
    pivot_data = filtered_data.pivot_table(index='CHAMBERID', columns='TSTAMP', values='GLASSID', aggfunc='count').fillna(0)
    pivot_data = pivot_data[sorted(pivot_data.columns, reverse=True)]
    st.dataframe(pivot_data.style.format("{:.0f}"))

    # 新增每日產品 RecipeID 的表格
    product_recipe_data = filtered_data[(filtered_data['PRODUCT_prefix'] != 'Auto_leak_SEA') & (~filtered_data['RECIPEID'].str.startswith('RPSC'))]
    product_recipe_data = product_recipe_data.pivot_table(index='CHAMBERID', columns='TSTAMP', values='RECIPEID', aggfunc=lambda x: ', '.join(set(x))).fillna('')
    product_recipe_data = product_recipe_data[sorted(product_recipe_data.columns, reverse=True)]
    st.subheader("每日產品 RecipeID")
    st.dataframe(product_recipe_data)

# GLASSID 與 RPSC 的分析
def analyze_glassid_and_rpsc(recent_data):
    st.header("GLASSID 與 RPSC 分析")
    recent_data['RECIPEID_prefix'] = recent_data['RECIPEID'].astype(str).str[:4]

    # 過濾匹配 GLASSID 與 RPSC 的資料
    filtered_rpsc_data = recent_data[recent_data['GLASSID_prefix'] == recent_data['RECIPEID_prefix']]

    rpsc_glassid_count = filtered_rpsc_data['GLASSID'].nunique()
    st.write(f"GLASSID 與 RECIPEID 前四碼匹配的玻璃片數量 (RPSC Count): {rpsc_glassid_count}")

    # 表格顯示日期由左往右越久
    filtered_rpsc_data['TSTAMP'] = filtered_rpsc_data['TSTAMP'].dt.date
    pivot_data = filtered_rpsc_data.pivot_table(index='CHAMBERID', columns='TSTAMP', values='GLASSID', aggfunc='count').fillna(0)
    pivot_data = pivot_data[sorted(pivot_data.columns, reverse=True)]
    st.dataframe(pivot_data.style.format("{:.0f}"))

    # 新增每日 RPSC RecipeID 的表格
    rpsc_name_data = filtered_rpsc_data[filtered_rpsc_data['RECIPEID'] != 'Auto_leak_SEA']
    rpsc_name_data = rpsc_name_data.pivot_table(index='CHAMBERID', columns='TSTAMP', values='RECIPEID', aggfunc=lambda x: ', '.join(set(x))).fillna('')
    rpsc_name_data = rpsc_name_data[sorted(rpsc_name_data.columns, reverse=True)]
    st.subheader("每日 RPSC RecipeID")
    st.dataframe(rpsc_name_data)

# 主邏輯
def main():
    st.title("NF3 氣體流量與使用儀表板")

    # 計算近 30 日各 CHAMBERID 的生產片數
    calculate_chamberid_stats(recent_data)

    # GLASSID 與 PRODUCT 分析
    analyze_glassid_and_product(recent_data)

    # GLASSID 與 RPSC 分析
    analyze_glassid_and_rpsc(recent_data)

if __name__ == "__main__":
    main()
