import streamlit as st
import altair as alt
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.dates as mdates
from matplotlib import font_manager

# Page configuration
st.set_page_config(
    page_title="NF3 氣體流量與使用儀表板",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded")
alt.themes.enable("dark")
# 設定 Matplotlib 字體
try:
    noto_sans_path = font_manager.findfont("Noto Sans CJK TC")
    custom_font = font_manager.FontProperties(fname=noto_sans_path)
    rcParams['font.sans-serif'] = ['Noto Sans CJK TC']
except Exception:
    try:
        arial_path = font_manager.findfont("Arial")
        custom_font = font_manager.FontProperties(fname=arial_path)
        rcParams['font.sans-serif'] = ['Arial']
    except Exception:
        rcParams['font.sans-serif'] = ['sans-serif']
rcParams['axes.unicode_minus'] = False

# 載入資料
data = pd.read_csv(r"D:\curso\streamlit\09_app_multipage\data\Merged_Data.csv")
data['TSTAMP'] = pd.to_datetime(data['TSTAMP'], format='%Y%m%d%H')
# 新增 LAYER 欄位
data['LAYER'] = data['RECIPEID'].str.extract('(BP|PFA|AS)')
# 定義單位轉換常數
SCCM_TO_KG = 3.04 / (1000 * 60)
SCCM_TO_LITER = 1 / 60000
SCCM_TO_SCCM = 1

# 異常值檢測函數
def detect_outliers_and_negatives(data, column):
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in the dataset.")
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = data[(data[column] < lower_bound) | (data[column] > upper_bound) | (data[column] < 0)]
    return outliers

# 每日流量比例計算
def calculate_daily_flow_ratio(data, filter_col):
    if 'NF3_total_Flow' not in data.columns:
        raise ValueError("Column 'NF3_total_Flow' not found in the dataset.")
    data['TSTAMP'] = pd.to_datetime(data['TSTAMP'])  # 確保 TSTAMP 是日期時間格式
    grouped = data.groupby([data['TSTAMP'].dt.date, filter_col])['NF3_total_Flow'].sum().reset_index()
    total_flow = grouped.groupby('TSTAMP')['NF3_total_Flow'].transform('sum')
    grouped['Flow_Ratio'] = grouped['NF3_total_Flow'] / total_flow
    return grouped

# 可視化比例
def visualize_flow_ratio(flow_ratio_data, filter_col):
    st.subheader(f"每日流量比例依據 {filter_col}")
    pivot_data = flow_ratio_data.pivot(index='TSTAMP', columns=filter_col, values='Flow_Ratio').fillna(0)
    pivot_data = pivot_data.sort_index(ascending=True)

    recent_days = pivot_data.index[:3]
    top_5_highlights = {day: pivot_data.loc[day].nlargest(5).index.tolist() for day in recent_days}

    def highlight_columns(data):
        styles = pd.DataFrame('', index=data.index, columns=data.columns)
        for day, top_cols in top_5_highlights.items():
            for col in top_cols:
                styles.loc[day, col] = 'background-color: yellow'
        return styles

    st.dataframe(pivot_data.style.apply(highlight_columns, axis=None).format("{:.2%}"))

    fig, ax = plt.subplots(figsize=(12, 8))
    pivot_data.plot(kind='bar', stacked=True, ax=ax, colormap='viridis')
    ax.set_title(f"每日流量比例依據 {filter_col}")
    ax.set_xlabel("日期")
    ax.set_ylabel("流量比例")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

# 調整表格顯示格式
def format_table_for_display(data):
    recent_30_days = data.tail(30).copy()
    recent_30_days['TSTAMP'] = pd.to_datetime(recent_30_days['TSTAMP'])
    recent_30_days.sort_values('TSTAMP', ascending=False, inplace=True)
    recent_30_days = recent_30_days.set_index('TSTAMP').T
    recent_30_days.columns = [f"{col}_{i}" if list(recent_30_days.columns).count(col) > 1 else str(col) for i, col in enumerate(recent_30_days.columns)]
    return recent_30_days

# Streamlit 應用程式主邏輯
def main():
    st.title("NF3 氣體流量與使用儀表板")

    st.sidebar.header("篩選選項")
    flow_unit = st.sidebar.radio("單位:", ("kg/s", "l/s", "sccm"))
    filter_options = ["CHAMBERID", "TOOLID", "RECIPEID", "OPERATION", "SIN", "LAYER"]

    unit_conversion = SCCM_TO_KG if flow_unit == "kg/s" else SCCM_TO_LITER if flow_unit == "l/s" else SCCM_TO_SCCM

    for selected_filter in filter_options:
        st.subheader(f"{selected_filter} 的分析")
        flow_ratio_data = calculate_daily_flow_ratio(data, selected_filter)

        outliers = detect_outliers_and_negatives(flow_ratio_data, 'NF3_total_Flow')
        if not outliers.empty:
            st.subheader(f"{selected_filter} 中的異常值")
            st.dataframe(outliers)

        valid_data = flow_ratio_data[~flow_ratio_data.index.isin(outliers.index)]
        visualize_flow_ratio(valid_data, selected_filter)

        # 顯示格式化表格
        st.subheader(f"最近 30 天的 {selected_filter} 流量數據")
        formatted_table = format_table_for_display(valid_data)
        st.dataframe(formatted_table)

if __name__ == "__main__":
    main()
