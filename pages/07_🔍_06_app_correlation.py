#######################
# Import libraries
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

#######################
# Page configuration
st.set_page_config(
    page_title="相關性分析",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded")

#######################
# Load data
fl = st.file_uploader(":file_folder: Upload a file",type=(["csv","txt","xlsx","xls"]))
if fl is not None:
    filename = fl.name
    st.write(filename)
    df = pd.read_csv(filename, encoding = "utf-8")
else:
    os.chdir(r"D:\curso\streamlit\09_app_multipage\data")
    df = pd.read_csv("Merged_Data.csv", encoding = "utf-8")

# 自定義時間轉換函數
def convert_timestamp(ts):
    try:
        ts = str(ts)
        if len(ts) >= 10:
            year = ts[:4]
            month = ts[4:6]
            day = ts[6:8]
            hour = ts[8:10] if len(ts) >= 10 else "00"
            return f"{year}/{month}/{day} {hour}:00"
        return None
    except:
        return None

# 數據預處理
df['TSTAMP'] = df['TSTAMP'].apply(convert_timestamp)
df['TSTAMP'] = pd.to_datetime(df['TSTAMP'], format='%Y/%m/%d %H:%M', errors='coerce')
df['Date'] = df['TSTAMP'].dt.date

# 定義單位轉換常數和函數
def sccm_to_kg_per_day(flow_sccm):
    m3_per_min = flow_sccm * (1/1000000)
    m3_per_day = m3_per_min / 1440
    kg_per_day = m3_per_day * 3.04
    return kg_per_day

# 轉換流量單位
df['Daily_Flow_kg'] = df['NF3_total_Flow'].apply(lambda x: sccm_to_kg_per_day(x)).round(2)

#######################
# Sidebar
with st.sidebar:
    st.title('🔍 相關性分析')
    
    date_list = sorted(df['Date'].unique(), reverse=True)
    selected_date = st.selectbox('選擇日期', date_list)
    df_selected_date = df[df['Date'] == selected_date]

#######################
# Main Panel
st.markdown("## 相關性分析")

tab1, tab2 = st.tabs(["基本資訊", "相關性分析"])

with tab1:
    st.markdown("### 基本資訊")
    # 這裡可以放置其他基本資訊的內容

with tab2:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 機台月度用量佔比分析
        st.markdown('#### 機台月度用量佔比分析')
        
        # 計算每月總用量
        df['YearMonth'] = pd.to_datetime(df['Date']).dt.strftime('%Y/%m')
        monthly_total = df.groupby('YearMonth')['Daily_Flow_kg'].sum().reset_index()
        
        # 計算每個機台每月的用量
        chamber_monthly = df.groupby(['YearMonth', 'CHAMBERID'])['Daily_Flow_kg'].sum().reset_index()
        
        # 計算每個機台每月的用量佔比
        chamber_monthly = chamber_monthly.merge(monthly_total, on='YearMonth', suffixes=('', '_total'))
        chamber_monthly['Usage_Percentage'] = (chamber_monthly['Daily_Flow_kg'] / chamber_monthly['Daily_Flow_kg_total'] * 100).round(2)
        
        # 創建樞紐表格式的數據
        pivot_data = chamber_monthly.pivot(index='CHAMBERID', columns='YearMonth', values='Usage_Percentage').fillna(0)
        
        # 創建組合圖表
        fig = go.Figure()
        
        # 添加熱力圖
        fig.add_trace(go.Heatmap(
            z=pivot_data.values,
            x=pivot_data.columns,  # YearMonth
            y=pivot_data.index,    # CHAMBERID
            colorscale='RdBu',
            text=pivot_data.values.round(2),
            texttemplate='%{text:.1f}%',
            textfont={"size": 10},
            hoverongaps=False,
            colorbar=dict(
                title=dict(
                    text="佔比 (%)",
                    side="right",
                    font=dict(size=12)
                ),
                ticksuffix="%",
                thickness=15,
                len=0.5,
                x=1.05,
                y=0.5,
                tickfont=dict(size=10)
            )
        ))
        
        # 添加每月總用量折線圖
        fig.add_trace(go.Scatter(
            x=monthly_total['YearMonth'],
            y=monthly_total['Daily_Flow_kg'],
            name='月總用量',
            yaxis='y2',
            mode='lines+markers+text',
            line=dict(color='yellow', width=2),
            marker=dict(size=8),
            text=monthly_total['Daily_Flow_kg'].round(2),
            textposition='top center',
            texttemplate='%{text:.1f}',
            textfont=dict(size=10)
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=550,
            title=dict(
                text='機台月度 NF3 用量佔比與總量分布',
                font=dict(size=14),
                x=0.5,
                y=0.98
            ),
            margin=dict(t=30, b=20, l=50, r=80),
            xaxis=dict(
                title='年月',
                tickangle=45,
                tickfont=dict(size=10),
                side='bottom'
            ),
            yaxis=dict(
                title='機台編號',
                tickfont=dict(size=10)
            ),
            yaxis2=dict(
                title='月總用量 (kg)',
                overlaying='y',
                side='right',
                showgrid=False,
                tickfont=dict(size=10),
                tickformat='.1f'
            ),
            showlegend=True,
            legend=dict(
                x=1.15,
                y=0.5,
                font=dict(size=10),
                bgcolor='rgba(0,0,0,0.5)'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # CLN1 ΔTime 相關係數分析
        st.markdown('#### CLN1 ΔTime 相關係數分析')
        
        # 篩選符合條件的數據
        cln1_data = df_selected_date[
            (df_selected_date['step_name'] == 'CLN1')
        ].copy()
        
        if not cln1_data.empty:
            # 定義要分析的參數列表
            parameters = ['ΔTime', 'pressure', 'load_pwr', 'rfl_pwr', 'mon_vpp', 'vdc',
                         'N2_Flow', 'NH3_Flow', 'SiH4_Flow', 'H2_Flow', 'PH3_Flow',
                         'Ar_Flow', 'NF3_Flow', 'N2O_Flow']
            
            # 過濾出實際存在的列
            available_columns = [col for col in parameters if col in cln1_data.columns]
            
            if available_columns:
                # 計算相關係數
                corr_matrix = cln1_data[available_columns].corr()
                
                # 創建熱力圖
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmid=0,
                    text=corr_matrix.values.round(2),
                    texttemplate='%{text}',
                    textfont={"size": 10},
                    hoverongaps=False,
                    showscale=True,
                    colorbar=dict(
                        title=dict(
                            text="相關係數",
                            side="right",
                            font=dict(size=12)
                        ),
                        thickness=15,
                        len=0.5,
                        x=1.05,
                        y=0.5,
                        tickfont=dict(size=10)
                    )
                ))
                
                fig_heatmap.update_layout(
                    template='plotly_dark',
                    height=550,
                    title=dict(
                        text='CLN1 步驟 ΔTime 參數相關係數',
                        font=dict(size=14),
                        x=0.5,
                        y=0.98
                    ),
                    margin=dict(t=30, b=20, l=50, r=50),
                    xaxis=dict(
                        tickangle=45,
                        tickfont=dict(size=10),
                        side='bottom'
                    ),
                    yaxis=dict(
                        tickfont=dict(size=10),
                        autorange='reversed'
                    )
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # 添加說明
                with st.expander("相關係數分析說明", expanded=False):
                    st.markdown("""
                    #### 相關係數基本概念
                    - **相關係數範圍**：-1 到 1
                        - 1：完全正相關（當一個變數增加，另一個變數也同比例增加）
                        - 0：無相關（兩個變數之間沒有線性關係）
                        - -1：完全負相關（當一個變數增加，另一個變數同比例減少）
                    
                    #### 顏色說明
                    - **紅色**：正相關（0到1）
                        - 深紅色：強正相關（0.7到1）
                        - 淺紅色：弱正相關（0到0.3）
                    - **白色**：無相關（接近0）
                    - **藍色**：負相關（-1到0）
                        - 深藍色：強負相關（-1到-0.7）
                        - 淺藍色：弱負相關（-0.3到0）
                    
                    #### 參數說明
                    - **ΔTime**：製程時間變化
                    - **pressure**：腔體壓力
                    - **load_pwr**：負載功率
                    - **rfl_pwr**：反射功率
                    - **mon_vpp**：監測電壓
                    - **vdc**：直流偏壓
                    - **各氣體流量**：N2、NH3、SiH4、H2、PH3、Ar、NF3、N2O
                    
                    #### 注意事項
                    - 相關係數只反映線性關係
                    - 相關不等於因果關係
                    - 建議結合實際製程經驗解讀數據
                    """)
            else:
                st.info("數據中沒有可用於相關係數分析的列")
        else:
            st.info("當日無CLN1步驟的數據") 