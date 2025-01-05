#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os
import warnings

#######################
# Page configuration
st.set_page_config(
    page_title="NF3 氣體流量分析儀表板",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

alt.themes.enable("dark")

#######################
# CSS styling
st.markdown("""
<style>
[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}
</style>
""", unsafe_allow_html=True)

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
df['LAYER'] = df['RECIPEID'].str.extract('(BP|PFA|AS)')

# 定義單位轉換常數和函數
def sccm_to_kg_per_day(flow_sccm):
    """
    將 SCCM 轉換為 kg/day
    SCCM = Standard Cubic Centimeters per Minute
    1. SCCM → m³/min: × (1/1000000)
    2. m³/min → m³/day: ÷ 1440 (24小時 * 60分鐘)
    3. m³ → kg: × 3.04 (NF3 密度在標準狀態下約為 3.04 kg/m³)
    """
    m3_per_min = flow_sccm * (1/1000000)  # SCCM → m³/min
    m3_per_day = m3_per_min / 1440        # m³/min → m³/day
    kg_per_day = m3_per_day * 3.04        # m³ → kg
    return kg_per_day

# 轉換流量單位
df['Daily_Flow_kg'] = df['NF3_total_Flow'].apply(lambda x: sccm_to_kg_per_day(x)).round(2)

#######################
# Sidebar
with st.sidebar:
    st.title('🏂 NF3 氣體流量分析儀表板')
    
    date_list = sorted(df['Date'].unique(), reverse=True)
    selected_date = st.selectbox('選擇日期', date_list)
    df_selected_date = df[df['Date'] == selected_date]

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('選擇顏色主題', color_theme_list)

#######################
# 計算函數

# 計算流量變化
def calculate_flow_changes(df, selected_date):
    # 日變化
    daily_flow = df.groupby('Date')['Daily_Flow_kg'].sum().reset_index()
    daily_flow['Previous_Day'] = daily_flow['Daily_Flow_kg'].shift(1)
    daily_flow['Day_Change'] = ((daily_flow['Daily_Flow_kg'] - daily_flow['Previous_Day']) / daily_flow['Previous_Day'] * 100).round(2)
    
    # 月變化
    daily_flow['Month'] = pd.to_datetime(daily_flow['Date']).dt.to_period('M')
    monthly_flow = daily_flow.groupby('Month')['Daily_Flow_kg'].sum().reset_index()
    monthly_flow['Previous_Month'] = monthly_flow['Daily_Flow_kg'].shift(1)
    monthly_flow['Month_Change'] = ((monthly_flow['Daily_Flow_kg'] - monthly_flow['Previous_Month']) / monthly_flow['Previous_Month'] * 100).round(2)
    
    # 獲取當前數據
    current_day_data = daily_flow[daily_flow['Date'] == selected_date].iloc[0]
    current_month = pd.to_datetime(selected_date).to_period('M')
    current_month_data = monthly_flow[monthly_flow['Month'] == current_month].iloc[0]
    
    return (current_day_data['Daily_Flow_kg'], 
            current_day_data['Day_Change'],
            current_month_data['Daily_Flow_kg'],
            current_month_data['Month_Change'])

# 計算製程分布
def calculate_layer_distribution(df):
    layer_data = df.groupby('LAYER')['Daily_Flow_kg'].sum().reset_index()
    total_flow = layer_data['Daily_Flow_kg'].sum()
    layer_data['Usage_Percentage'] = (layer_data['Daily_Flow_kg'] / total_flow * 100).round(2)
    return layer_data

# 格式化數字
def format_number(num):
    return f'{num:.2f}'


tab1, tab2 = st.tabs(["即時監控", "相關性分析"])

#######################
# Dashboard Main Panel
with tab1:
    col = st.columns((1.2, 4.8, 1.8), gap='medium')
    
    with col[0]:
        # 添加更新時間
        current_time = pd.Timestamp.now().strftime('%Y/%m/%d %H:%M')
        st.markdown(f'''
            <div style="font-size: 12px; color: #888888; margin-bottom: 10px;">
            🔄 更新時間：{current_time}
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('#### 流量變化')
        
        current_flow, day_change, month_flow, month_change = calculate_flow_changes(df, selected_date)
        
        # 獲取當前日期和月份的第一天
        current_date = pd.to_datetime(selected_date)
        current_month_start = current_date.replace(day=1)
        
        # 顯示當日流量
        st.metric(label=f"當日流量 ({current_date.strftime('%Y/%m/%d')})", 
                value=format_number(current_flow), 
                delta=f"{format_number(day_change)}%",
                help="與前一天相比的變化百分比")
                    
        # 顯示當月累積
        st.metric(label=f"當月累積 ({current_month_start.strftime('%Y/%m/%d')}~{current_date.strftime('%Y/%m/%d')})", 
                value=format_number(month_flow), 
                delta=f"{format_number(month_change)}%",
                help="與前一月相比的變化百分比")

        # 添加製程分布餅圖
        st.markdown('#### 製程分布')
        layer_data = calculate_layer_distribution(df_selected_date)
        
        # 添加 OPERATION 分布餅圖
        operation_data = df_selected_date.groupby('OPERATION')['Daily_Flow_kg'].sum().reset_index()
        total_flow_operation = operation_data['Daily_Flow_kg'].sum()
        operation_data['Usage_Percentage'] = (operation_data['Daily_Flow_kg'] / total_flow_operation * 100).round(2)
        
        fig_pie_operation = px.pie(operation_data, 
                         values='Daily_Flow_kg', 
                         names='OPERATION',
                         title="Operation-wise NF3 Usage")
        fig_pie_operation.update_layout(
            template='plotly_dark',
            height=300,
            margin=dict(t=70, b=5, l=10, r=10),
            font=dict(size=14),
            title=dict(
                text="Operation-wise NF3 Usage",
                font=dict(size=16),
                y=0.8
            ),
            showlegend=True,
            legend=dict(
                font=dict(size=12),
                orientation="h",
                yanchor="bottom",
                y=1.1,
                xanchor="center",
                x=0.5,
                traceorder="normal"
            )
        )
        st.plotly_chart(fig_pie_operation, use_container_width=True)

        # Recipe-wise NF3 Usage 餅圖
        fig_pie = px.pie(layer_data, 
                         values='Daily_Flow_kg', 
                         names='LAYER',
                         title="Recipe-wise NF3 Usage")
        fig_pie.update_layout(
            template='plotly_dark',
            height=300,
            margin=dict(t=70, b=5, l=10, r=10),
            font=dict(size=14),
            title=dict(
                text="Recipe-wise NF3 Usage",
                font=dict(size=16),
                y=0.8
            ),
            showlegend=True,
            legend=dict(
                font=dict(size=12),
                orientation="h",
                yanchor="bottom",
                y=1.1,
                xanchor="center",
                x=0.5,
                traceorder="normal"
            )
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # 添加 SIN 分布餅圖
        sin_data = df_selected_date.groupby('SIN')['Daily_Flow_kg'].sum().reset_index()
        total_flow_sin = sin_data['Daily_Flow_kg'].sum()
        sin_data['Usage_Percentage'] = (sin_data['Daily_Flow_kg'] / total_flow_sin * 100).round(2)
        
        fig_pie_sin = px.pie(sin_data, 
                         values='Daily_Flow_kg', 
                         names='SIN',
                         title="SIN-wise NF3 Usage")
        fig_pie_sin.update_layout(
            template='plotly_dark',
            height=300,
            margin=dict(t=70, b=5, l=10, r=10),
            font=dict(size=14),
            title=dict(
                text="SIN-wise NF3 Usage",
                font=dict(size=16),
                y=0.8
            ),
            showlegend=True,
            legend=dict(
                font=dict(size=10),
                yanchor="middle",
                y=1.1,
                xanchor="left",
                x=0.95
            )
        )
        st.plotly_chart(fig_pie_sin, use_container_width=True)



    with col[1]:
        st.markdown('#### 流量趨勢')
        
        # 每日流量趨勢圖
        daily_flow = df.groupby('Date')['Daily_Flow_kg'].sum().reset_index()
        daily_flow['Formatted_Date'] = pd.to_datetime(daily_flow['Date']).dt.strftime('%Y/%m/%d')
        daily_flow['Cumulative_Flow'] = daily_flow['Daily_Flow_kg'].cumsum()
        
        fig = go.Figure()
        
        # 添加每日流量折線圖
        fig.add_trace(go.Scatter(
            x=daily_flow['Formatted_Date'],
            y=daily_flow['Daily_Flow_kg'],
            name='每日流量',
            text=daily_flow['Daily_Flow_kg'].round(2),
            textposition='top center',
            texttemplate='%{text:.2f}',
            mode='lines+markers+text',
            line=dict(width=2),
            marker=dict(size=8)
        ))
        
        # 添加累積流量柱狀圖
        fig.add_trace(go.Bar(
            x=daily_flow['Formatted_Date'],
            y=daily_flow['Cumulative_Flow'],
            name='累積流量',
            yaxis='y2',
            text=daily_flow['Cumulative_Flow'].round(2),
            textposition='outside',
            texttemplate='%{text:.2f}'
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=600,
            margin=dict(t=50, b=50, l=50, r=50),
            font=dict(size=12),
            title=dict(
                text='每日與累積氣體流量趨勢',
                font=dict(size=16)
            ),
            legend=dict(
                font=dict(size=12),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(title='日期', tickangle=45),
            yaxis=dict(
                title='每日流量 (kg/day)',
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)',
                tickformat='.2f'
            ),
            yaxis2=dict(
                title='累積流量 (kg)',
                overlaying='y',
                side='right',
                showgrid=False,
                tickformat='.2f'
            ),
            bargap=0.2
        )
        st.plotly_chart(fig, use_container_width=True)

        # 添加異常數據顯示
        with st.expander("每日流量異常數據", expanded=False):
            # 計算每日總流量
            daily_total = df.groupby('Date')['Daily_Flow_kg'].sum().reset_index()
            daily_total = daily_total.sort_values('Date')
            
            # 計算5日移動平均
            daily_total['5D_Average'] = daily_total['Daily_Flow_kg'].rolling(window=5, min_periods=1).mean()
            
            # 計算異常倍數
            daily_total['Abnormal_Times'] = daily_total['Daily_Flow_kg'] / daily_total['5D_Average']
            
            # 篩選異常數據（當日流量超過5日平均5倍的數據）
            abnormal_dates = daily_total[daily_total['Abnormal_Times'] > 5]['Date']
            
            # 獲取異常日期的詳細數據
            abnormal_data = df[
                (df['Date'].isin(abnormal_dates)) &
                (df['Date'] == selected_date)
            ][['Date', 'TSTAMP', 'CHAMBERID', 'RECIPEID', 'LAYER', 'Daily_Flow_kg']].copy()
            
            if not abnormal_data.empty:
                # 獲取當日的5日平均值
                current_day_avg = daily_total[daily_total['Date'] == selected_date]['5D_Average'].iloc[0]
                current_day_times = daily_total[daily_total['Date'] == selected_date]['Abnormal_Times'].iloc[0]
                
                st.write(f"### 當日異常分析")
                st.write(f"""
                - 當日總流量：{daily_total[daily_total['Date'] == selected_date]['Daily_Flow_kg'].iloc[0]:.2f} kg/day
                - 前5日平均：{current_day_avg:.2f} kg/day
                - 異常倍數：{current_day_times:.1f} 倍
                """)
                
                st.write("### 異常數據明細")
                st.dataframe(
                    abnormal_data,
                    column_config={
                        "Date": "日期",
                        "TSTAMP": "時間戳記",
                        "CHAMBERID": "機台編號",
                        "RECIPEID": "配方編號",
                        "LAYER": "製程層別",
                        "Daily_Flow_kg": st.column_config.NumberColumn(
                            "日流量 (kg/day)",
                            format="%.2f"
                        )
                    },
                    hide_index=True
                )
                
                # 顯示歷史異常記錄
                st.write("### 歷史異常記錄")
                historical_abnormal = daily_total[daily_total['Abnormal_Times'] > 5].sort_values('Date')
                
                st.dataframe(
                    historical_abnormal[['Date', 'Daily_Flow_kg', '5D_Average', 'Abnormal_Times']],
                    column_config={
                        "Date": "日期",
                        "Daily_Flow_kg": st.column_config.NumberColumn(
                            "日流量 (kg/day)",
                            format="%.2f"
                        ),
                        "5D_Average": st.column_config.NumberColumn(
                            "5日平均 (kg/day)",
                            format="%.2f"
                        ),
                        "Abnormal_Times": st.column_config.NumberColumn(
                            "異常倍數",
                            format="%.1f"
                        )
                    },
                    hide_index=True
                )
                
                # 添加下載按鈕
                csv = historical_abnormal.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "下載異常記錄",
                    data=csv,
                    file_name="異常流量記錄.csv",
                    mime="text/csv",
                    help='點擊下載異常流量記錄CSV檔案'
                )
            else:
                st.info("當日流量未超過前5日平均值的5倍")

        # 添加層級樹狀圖
        st.markdown('#### 層級分析')
        tree_data = df_selected_date.groupby(['LAYER', 'OPERATION', 'SIN', 'CHAMBERID'], 
                                           as_index=False)['Daily_Flow_kg'].sum()
        
        fig_tree = px.treemap(tree_data,
                             path=['LAYER', 'OPERATION', 'SIN', 'CHAMBERID'],
                             values='Daily_Flow_kg',
                             title="Hierarchical view of NF3 Usage")
        fig_tree.update_layout(
            template='plotly_dark',
            height=400,
            margin=dict(t=30, b=20, l=20, r=20),
            font=dict(size=16),
            title=dict(
                text="Hierarchical view of NF3 Usage",
                font=dict(size=18)
            )
        )
        fig_tree.update_traces(textinfo="label+value")
        st.plotly_chart(fig_tree, use_container_width=True, key="tree_left")

        

        with col[2]:
            st.markdown('#### 機台排名 (前十大)')
            
            # 機台排名表格（只顯示前十名）
            chamber_ranking = df_selected_date.groupby('CHAMBERID')['Daily_Flow_kg'].sum().reset_index()
            chamber_ranking = chamber_ranking.sort_values('Daily_Flow_kg', ascending=False).head(10)
            
            st.dataframe(chamber_ranking,
                         column_order=("CHAMBERID", "Daily_Flow_kg"),
                         hide_index=True,
                         height=400,
                         width=None,
                         column_config={
                            "CHAMBERID": st.column_config.TextColumn(
                                "機台編號",
                            ),
                            "Daily_Flow_kg": st.column_config.ProgressColumn(
                                "日流量 (kg/day)",
                                format="%.2f",
                                min_value=0,
                                max_value=max(chamber_ranking['Daily_Flow_kg']),
                             )}
                         )
            
            with st.expander('說明', expanded=True):
                st.markdown('''
                    <div style="font-size: 14px; padding: 10px; background-color: rgba(0,0,0,0.2); border-radius: 5px; margin-top: 10px;">
                    <div style="color: #E0E0E0; margin-bottom: 8px; font-size: 16px;">📊 <b>數據說明</b></div>
                    <div style="margin-left: 10px; margin-bottom: 12px;">
                    • 數據來源：半導體製程 NF3 氣體流量監測系統<br>
                    • 更新頻率：每日自動更新
                    </div>
                    
                    <div style="color: #E0E0E0; margin-bottom: 8px; font-size: 16px;">🔄 <b>流量計算邏輯</b></div>
                    <div style="margin-left: 10px; margin-bottom: 12px;">
                    <u>單位換算</u>：<br>
                    • 原始單位：SCCM<br>
                    • 轉換步驟：<br>
                    &nbsp;&nbsp;1. SCCM → m³/min: × (1/1000000)<br>
                    &nbsp;&nbsp;2. m³/min → m³/day: ÷ 1440<br>
                    &nbsp;&nbsp;3. m³ → kg: × 3.04
                    </div>
                    
                    <div style="margin-left: 10px; margin-bottom: 12px;">
                    <u>變化率計算</u>：<br>
                    • 日變化率 = (當日流量 - 前日流量) / 前日流量 × 100%<br>
                    • 月變化率 = (當月累積 - 前月累積) / 前月累積 × 100%
                    </div>
                    
                    <div style="color: #E0E0E0; margin-bottom: 8px; font-size: 16px;">🔍 <b>製程分類</b></div>
                    <div style="margin-left: 10px; margin-bottom: 12px;">
                    • AS：特殊製程層別<br>
                    • BP/PFA：標準製程層別<br>
                    • 佔比 = 特定製程流量 / 總流量 × 100%
                    </div>
                    
                    <div style="color: #E0E0E0; margin-bottom: 8px; font-size: 16px;">📈 <b>機台排名</b></div>
                    <div style="margin-left: 10px;">
                    • 基於當日累積流量<br>
                    • 顯示所有機台的流量排序<br>
                    • 數據每日更新
                    </div>
                    </div>
                    ''', unsafe_allow_html=True)
            
with tab2:
    col_analysis1, col_analysis2 = st.columns([1, 1])
    
    with col_analysis1:
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
            height=550,  # 調整高度
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

    with col_analysis2:
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
                    textfont={"size": 14},
                    hoverongaps=False,
                    showscale=True,
                    colorbar=dict(
                        title=dict(
                            text="相關係數",
                            side="right",
                            font=dict(size=14)
                        ),
                        thickness=15,
                        len=0.5,
                        x=1.05,
                        y=0.5,
                        tickfont=dict(size=12)
                    )
                ))
                
                fig_heatmap.update_layout(
                    template='plotly_dark',
                    height=550,
                    title=dict(
                        text='CLN1 步驟 ΔTime 參數相關係數',
                        font=dict(size=16),
                        x=0.5,
                        y=0.98
                    ),
                    margin=dict(t=30, b=20, l=50, r=50),
                    xaxis=dict(
                        tickangle=45,
                        tickfont=dict(size=12),
                        side='bottom'
                    ),
                    yaxis=dict(
                        tickfont=dict(size=12),
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
        