import streamlit as st
import altair as alt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import matplotlib as mpl
#pip freeze > requirements.txt
# activate finlab
# cd "C:\Users\USER\Desktop\finlab_course2019\streamlit\09_app_multipage"
# streamlit run 01_🎈_main_app.py

st.set_page_config(
    page_title="NF3 氣體流量與使用儀表板",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded")
alt.themes.enable("dark")

pd.set_option("styler.render.max_elements", 15346088)  # 設置最大渲染元素

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
data = pd.read_csv(r"D:\curso\streamlit\09_app_multipage\data\Merged_Data.csv")
# 新增 LAYER 欄位
data['LAYER'] = data['RECIPEID'].str.extract('(BP|PFA|AS)')
# 將 TSTAMP 轉換為日期時間格式以便處理
data['TSTAMP'] = pd.to_datetime(data['TSTAMP'], format='%Y%m%d%H')

# 定義單位轉換常數
SCCM_TO_KG = 3.04 / (1000 * 60)  # 轉換為 kg/s，NF3 密度 3.04 kg/m³
SCCM_TO_LITER = 1 / 60000  # 轉換為 l/s
SCCM_TO_SCCM = 1  # 單位保持不變



# 定義使用 IQR 檢測離群值的函數
def detect_outliers(df, col):
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[col] < lower_bound) | (df[col] > upper_bound)]

# 計算 RPSC_GLASSID 數量
def calculate_rpsc_glassid(data):
    rpsc_data = data[data['RECIPEID'].str.startswith('RPSC', na=False)]
    rpsc_glassid_count = rpsc_data['GLASSID'].nunique()
    return rpsc_glassid_count

# Streamlit 應用程式
def main():
    st.title("NF3 氣體流量與用量儀表板")

    # 選擇累積流量的單位
    st.sidebar.header("選擇累積流量的單位")
    flow_unit = st.sidebar.radio("單位:", ("kg/s", "l/s", "sccm"))

    # 確定單位轉換係數與標籤
    if flow_unit == "kg/s":
        unit_conversion = SCCM_TO_KG
        unit_label = "(kg/s)"
    elif flow_unit == "l/s":
        unit_conversion = SCCM_TO_LITER
        unit_label = "(l/s)"
    else:
        unit_conversion = SCCM_TO_SCCM
        unit_label = "(sccm)"

    # 新增時間選項
    st.sidebar.header("選擇時間維度")
    time_granularity = st.sidebar.radio("維度:", ("年", "季", "月", "週", "日"))

    # 顯示單位轉換邏輯
    st.sidebar.markdown("### 單位轉換說明")
    st.sidebar.markdown(
        """
        - **SCCM to KG/S**: \( \text{[NF3_total_Flow]} \times 3.04 / (1000 \times 60) \)
        - **SCCM to L/S**: \( \text{[NF3_total_Flow]} / 60000 \)
        - **SCCM to SCCM**: 單位保持不變
        """
    )

    # 側邊欄篩選條件
    st.sidebar.header("篩選選項")
    # 增加全選選項
    def add_all_option(options):
        """為篩選器添加全選功能。"""
        return ["全選"] + options

    # 初始化篩選器
    chamberid_filter = st.sidebar.multiselect("選擇 CHAMBERID:", add_all_option(data['CHAMBERID'].dropna().unique().tolist()), default=["全選"])
    toolid_filter = st.sidebar.multiselect("選擇 TOOLID:", add_all_option(data['TOOLID'].dropna().unique().tolist()), default=["全選"])
    recipeid_filter = st.sidebar.multiselect("選擇 RECIPEID:", add_all_option(data['RECIPEID'].dropna().unique().tolist()), default=["全選"])
    operation_filter = st.sidebar.multiselect("選擇 OPERATION:", add_all_option(data['OPERATION'].dropna().unique().tolist()), default=["全選"])
    product_filter = st.sidebar.multiselect("選擇 PRODUCT:", add_all_option(data['PRODUCT'].dropna().unique().tolist()), default=["全選"])
    chamber_code_filter = st.sidebar.multiselect("選擇 CHAMBER_CODE:", add_all_option(data['CHAMBER_CODE'].dropna().unique().tolist()), default=["全選"])
    sin_filter = st.sidebar.multiselect("選擇 SIN:", add_all_option(data['SIN'].dropna().unique().tolist()), default=["全選"])
    layer_filter = st.sidebar.multiselect("選擇 LAYER:", add_all_option(data['LAYER'].dropna().unique().tolist()), default=["全選"])
    step_name_filter = st.sidebar.multiselect("選擇 STEP_NAME:", add_all_option(data['step_name'].dropna().unique().tolist()), default=['CLN1', 'CLN2', 'CLN3'], key="step_name")

    # 篩選數據
    filtered_data = data.copy()
    if "全選" not in chamberid_filter:
        filtered_data = filtered_data[filtered_data['CHAMBERID'].isin(chamberid_filter)]
    if "全選" not in toolid_filter:
        filtered_data = filtered_data[filtered_data['TOOLID'].isin(toolid_filter)]
    if "全選" not in recipeid_filter:
        filtered_data = filtered_data[filtered_data['RECIPEID'].isin(recipeid_filter)]
    if "全選" not in operation_filter:
        filtered_data = filtered_data[filtered_data['OPERATION'].isin(operation_filter)]
    if "全選" not in product_filter:
        filtered_data = filtered_data[filtered_data['PRODUCT'].isin(product_filter)]
    if "全選" not in chamber_code_filter:
        filtered_data = filtered_data[filtered_data['CHAMBER_CODE'].isin(chamber_code_filter)]
    if "全選" not in sin_filter:
        filtered_data = filtered_data[filtered_data['SIN'].isin(sin_filter)]
    if "全選" not in layer_filter:
        filtered_data = filtered_data[filtered_data['LAYER'].isin(layer_filter)]
    if "全選" not in step_name_filter:
        filtered_data = filtered_data[filtered_data['step_name'].isin(step_name_filter)]

    # 計算每日流量並檢測異常值
    daily_flow = filtered_data.groupby(filtered_data['TSTAMP'].dt.date)['NF3_total_Flow'].sum().reset_index()
    daily_flow.columns = ['Date', 'Daily_Flow']
    daily_flow['Daily_Flow'] *= unit_conversion

    # 計算 7 天和 30 天移動平均線
    daily_flow['7-Day MA'] = daily_flow['Daily_Flow'].rolling(window=7, min_periods=1).mean()
    daily_flow['30-Day MA'] = daily_flow['Daily_Flow'].rolling(window=30, min_periods=1).mean()

    # 過濾掉異常值的每日流量
    Q1 = daily_flow['Daily_Flow'].quantile(0.25)
    Q3 = daily_flow['Daily_Flow'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    filtered_daily_flow = daily_flow[(daily_flow['Daily_Flow'] >= lower_bound) & (daily_flow['Daily_Flow'] <= upper_bound)]

    # 繪製每日用量與移動平均線圖表
    fig, ax1 = plt.subplots(figsize=(12, 8))
    # 使用過濾後的每日流量計算累積流量，每月1號重置
    filtered_daily_flow['Month'] = pd.to_datetime(filtered_daily_flow['Date']).dt.to_period('M')
    filtered_daily_flow['Cumulative_Flow'] = filtered_daily_flow.groupby('Month')['Daily_Flow'].cumsum()

    # 計算 RPSC_GLASSID 數量
    rpsc_glassid_count = calculate_rpsc_glassid(filtered_data)

    # 顯示 RPSC_GLASSID 計算邏輯
    st.markdown("### RPSC_GLASSID 計算邏輯")
    st.markdown(
        """
        - **篩選條件**: 選擇 `RECIPEID` 開頭為 'RPSC' 的列
        - **唯一計數**: 計算 `GLASSID` 欄位中的唯一值
        """
    )

    # 顯示數據摘要
    st.header("數據摘要")
    st.write(filtered_data.describe())
    st.subheader(f"RPSC_GLASSID 數量: {rpsc_glassid_count}")

    # 檢測異常值
    daily_outliers = detect_outliers(filtered_daily_flow, 'Daily_Flow')

    # 顯示每日流量的異常值
    st.header("每日流量異常值")
    if not daily_outliers.empty:
        st.write("以下異常值被檢測到:")
        st.dataframe(daily_outliers)
    else:
        st.write("每日流量未檢測到異常值。")

    # 顯示近三十日數據表格
    st.header("最近 30 天數據紀錄")

    # 提取最近 30 天數據
    recent_30_days = filtered_daily_flow.tail(30).copy()
    recent_30_days['Daily_Flow_kg'] = (recent_30_days['Daily_Flow'] * SCCM_TO_KG).round(2)
    recent_30_days['Daily_Flow_l'] = (recent_30_days['Daily_Flow'] * SCCM_TO_LITER).round(2)
    recent_30_days['Daily_Flow_sccm'] = (recent_30_days['Daily_Flow'] * SCCM_TO_SCCM).round(2)
    recent_30_days['Cumulative_Flow_converted'] = (recent_30_days['Cumulative_Flow'] * unit_conversion).round(2)

    # 調整表格顯示格式，日期水平排列，最新日期在左
    recent_30_days = recent_30_days[['Date', 'Daily_Flow_kg', 'Daily_Flow_l', 'Daily_Flow_sccm','Cumulative_Flow_converted']]
    recent_30_days.sort_values('Date', ascending=False, inplace=True)
    table_data = recent_30_days.set_index('Date').T

    # 標記前五大每日用量
    top_5_dates = recent_30_days.nlargest(5, 'Daily_Flow_kg')['Date']
    highlight_cols = {date: 'background-color: yellow' for date in top_5_dates}

    # 使用自定義樣式高亮前五大日期
    def highlight_columns(data):
        return pd.DataFrame(
            [[highlight_cols.get(col, '') for col in data.columns]] * data.shape[0],
            columns=data.columns,
            index=data.index
        )

    # 在 Streamlit 中展示格式化表格
    st.write("最近 30 天表格 (包括不同指標):")
    st.dataframe(table_data.style.apply(highlight_columns, axis=None))

    # 每日用量與累積流量的圖表
    st.header("每日與累積流量圖表")
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # 顯示數據
    daily_flow_kg = (filtered_daily_flow['Daily_Flow'] * SCCM_TO_KG).round(2)
    ax1.plot(filtered_daily_flow['Date'], daily_flow_kg, label=f"每日用量 (kg/s)", color='blue', marker='o')
    ax2 = ax1.twinx()
    cumulative_flow_kg = (filtered_daily_flow['Cumulative_Flow'] * SCCM_TO_KG).round(2)
    ax2.bar(filtered_daily_flow['Date'], cumulative_flow_kg, label=f"累積流量 (kg/s)", color='red', alpha=0.5)

    # 繪製每日用量的趨勢線
    ax1.plot(filtered_daily_flow['Date'], (filtered_daily_flow['Daily_Flow'] * SCCM_TO_KG).round(2), label=f"每日用量 {unit_label}", color='tab:blue', marker='o')
    ax1.plot(filtered_daily_flow['Date'], (filtered_daily_flow['7-Day MA'] * SCCM_TO_KG).round(2), label='7 天移動平均', color='orange', linestyle='--')
    ax1.plot(filtered_daily_flow['Date'], (filtered_daily_flow['30-Day MA'] * SCCM_TO_KG).round(2), label='30 天移動平均', color='green', linestyle='--')
    for i, v in enumerate((filtered_daily_flow['Daily_Flow'] * SCCM_TO_KG).round(2)):
        ax1.text(filtered_daily_flow['Date'].iloc[i], v, f'{v:.2f}', color='tab:blue', ha='center')
    ax1.set_xlabel("日期")
    ax1.set_ylabel(f"每日用量 {unit_label}", color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # 格式化 X 軸
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # 使用直條圖表示累積流量
    ax2 = ax1.twinx()
    ax2.bar(filtered_daily_flow['Date'], (filtered_daily_flow['Cumulative_Flow'] * SCCM_TO_KG).round(2), label=f"累積流量 {unit_label}", color='tab:red', alpha=0.6)
    for i, v in enumerate((filtered_daily_flow['Cumulative_Flow'] * SCCM_TO_KG).round(2)):
        ax2.text(filtered_daily_flow['Date'].iloc[i], v, f'{v:.2f}', color='tab:red', ha='center')
    ax2.set_ylabel(f"累積流量 {unit_label}", color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # 添加圖例
    fig.tight_layout()
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    # 添加圖例與顯示
    fig.tight_layout()
    st.pyplot(fig)

    # 成本與排放計算
    st.title("NF3 單價輸入")

    # 使用者輸入 NF3 每公斤的單價
    NF3_price_per_kg = st.number_input(
        label="輸入每公斤 NF3 的價格:",
        min_value=0.0,  # 設定最低值
        value=50.0,     # 預設值
        step=0.1        # 每次調整的步長
    )

    # 顯示使用者輸入的值
    st.write(f"每公斤 NF3 的價格為: ${NF3_price_per_kg:.2f}")

    filtered_daily_flow['Daily_Cost'] = filtered_daily_flow['Daily_Flow'] * NF3_price_per_kg
    filtered_daily_flow['GHG_Emissions'] = filtered_daily_flow['Daily_Flow'] * 17200  # NF3 GWP 為 17200

 # 成本與排放摘要
    st.markdown("### 成本與排放分析")
    st.write(f"總成本: ${filtered_daily_flow['Daily_Cost'].sum():,.2f}")
    st.write(f"總溫室氣體排放量: {filtered_daily_flow['GHG_Emissions'].sum():,.2f} kg CO2e")

    
 # GLASSID 與 PRODUCT 的分析
    st.header("GLASSID 與 PRODUCT 分析")
    data['GLASSID_prefix'] = data['GLASSID'].astype(str).str[:4]
    data['PRODUCT_prefix'] = data['PRODUCT'].astype(str).str[:4]
    
    # 計算 GLASSID 與 PRODUCT 的匹配數量
    filtered_data = data[data['GLASSID_prefix'] == data['PRODUCT_prefix']]
    glassid_count = filtered_data['GLASSID'].nunique()
    st.write(f"GLASSID 與 PRODUCT 前四碼匹配的玻璃片數量: {glassid_count}")
    
    # 單片玻璃平均 NF3 消耗
    average_nf3_per_glass = filtered_data.groupby(['GLASSID', 'TSTAMP'])['NF3_total_Flow'].mean().reset_index()
    average_nf3_per_glass.columns = ['GLASSID', 'Date', 'Average_NF3_Consumption']
    st.subheader("單片玻璃平均 NF3 消耗量（橫向統計）")
    pivot_glass_table = average_nf3_per_glass.pivot(index='GLASSID', columns='Date', values='Average_NF3_Consumption')
    st.dataframe(pivot_glass_table.style.format("{:.2f}"))
    
    # 總 NF3 消耗量
    total_nf3_consumption = filtered_data['NF3_total_Flow'].sum()
    nf3_per_glass = total_nf3_consumption / glassid_count if glassid_count > 0 else 0
    st.write(f"總 NF3 消耗量: {total_nf3_consumption:.2f}")
    st.write(f"單片玻璃平均 NF3 消耗量: {nf3_per_glass:.2f}")
    
    # GLASSID 與 RPSC 的分析
    st.header("GLASSID 與 RPSC 分析")
    data['RECIPEID_prefix'] = data['RECIPEID'].astype(str).str[:4]
    filtered_rpsc_data = data[data['GLASSID_prefix'] == data['RECIPEID_prefix']]
    rpsc_glassid_count = filtered_rpsc_data['GLASSID'].nunique()
    st.write(f"GLASSID 與 RECIPEID 前四碼匹配的玻璃片數量 (RPSC Count): {rpsc_glassid_count}")
    
    # 單次 RPSC 平均 NF3 消耗
    average_nf3_per_rpsc = filtered_rpsc_data.groupby(['GLASSID', 'TSTAMP', 'CHAMBERID'])['NF3_total_Flow'].mean().reset_index()
    average_nf3_per_rpsc.columns = ['GLASSID', 'Date', 'CHAMBERID', 'Average_NF3_Consumption']
    
    st.subheader("單次 RPSC 平均 NF3 消耗量（按日期與 CHAMBERID）")
    pivot_rpsc_table = average_nf3_per_rpsc.pivot(index='CHAMBERID', columns='Date', values='Average_NF3_Consumption')
    st.dataframe(pivot_rpsc_table.style.format("{:.2f}"))
    
    # 總 RPSC NF3 消耗量
    total_nf3_consumption_rpsc = filtered_rpsc_data['NF3_total_Flow'].sum()
    nf3_per_rpsc = total_nf3_consumption_rpsc / rpsc_glassid_count if rpsc_glassid_count > 0 else 0
    st.write(f"總 RPSC NF3 消耗量: {total_nf3_consumption_rpsc:.2f}")
    st.write(f"單次 RPSC 平均 NF3 消耗量: {nf3_per_rpsc:.2f}")

    
if __name__ == "__main__":
    main()