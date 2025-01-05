import pandas as pd
import os
from pathlib import Path

# 直接設置數據目錄路徑
DATA_DIR = str(Path(__file__).parent / '09_app_multipage' / 'data') if '__file__' in globals() else str(Path.cwd() / '09_app_multipage' / 'data')

# 載入 Excel 文件
file_path = Path(DATA_DIR) / 'CVD_20250104.xlsx'
excel_file = pd.ExcelFile(file_path)

# 定義 AKT 和 Jusung 的欄位
akt_columns = [ 
    'CHAMBERID', 'GLASSID', 'TSTAMP', 'TOOLID', 'RECIPEID', 'OPERATION', 'PRODUCT', 'step_name', 
    'CHAMBER_CODE', 'Sample_Time', 'pressure', 'load_pwr_mon', 'rflt_pwr_mon', 'vpp', 'vdc', 
    'N2_Flow', 'NH3_Flow', 'SIH4_Flow', 'H2_Flow', 'PH3_Flow', 'Ar_Flow', 'NF3_Flow', 'N2O_Flow', 
    'ΔTime', 'N2_total_Flow', 'NH3_total_Flow', 'SIH4_total_Flow', 'H2_total_Flow', 'PH3_total_Flow', 
    'Ar_total_Flow', 'NF3_total_Flow', 'N2O_total_Flow', 'pressure_std_90s', 'SIN' 
] 
 
jusung_columns = [ 
    'CHAMBERID', 'GLASSID', 'TSTAMP', 'TOOLID', 'RECIPEID', 'OPERATION', 'PRODUCT', 'step_name', 'EVENTID', 'TRACEID', 
    'CHAMBER_CODE', 'Sample_Time', 'CVG01_Drv_ReadPressre_torr', 'PrssCtrl_Drv_ReadPressure_torr', 
    'PrssCtrl_Drv_SetPoint', 'PrssCtrl_Drv_ReadPosition_P', 'Chuck_ActProcPosn_mil', 
    'RFMatcher_Drv_ActTunePosn_P', 'RFMatcher_Drv_ActLoadPosn_P', 'RFGen_Drv_PowerSet_watt', 
    'RFGen_Drv_ActForwardPwr_watt', 'RFGen_Drv_ActBackwardPwr_watt', 'RFMatcher_Drv_ActVdc_V', 
    'RFMatcher_Drv_ActVpp_V', 'RFMatcher_Drv_ActIpp_A', 'N2_1_FlowAct_sccm', 'NF3_FlowAct_sccm', 
    'Ar_FlowAct_sccm', 'SiH4_FlowAct_sccm', 'PH3_H2_FlowAct_sccm', 'H2_FlowAct_sccm', 
    'NH3_FlowAct_sccm', 'N2_2_FlowAct_sccm', 'ChuckHtr_Cntl_IN1_ActTemp_C', 
    'ChuckHtr_Cntl_IN2_ActTemp_C', 'RPSC_BackwardPwr_watt', 'ΔTime', 'N2_1_total_sccm', 
    'NF3_total_Flow', 'Ar_total_Flow', 'SIH4_total_Flow', 'PH3_total_Flow', 'H2_total_Flow', 
    'NH3_total_Flow', 'N2_2_total_sccm', 'N2_total_Flow', 'pressure', 'SIN' 
]
# 將工作表分類為 AKT（非「2ACXDD00」）和 Jusung（包含「2ACXDD00」）
akt_sheets = [sheet for sheet in excel_file.sheet_names if "2ACXDD00" not in sheet]
jusung_sheets = [sheet for sheet in excel_file.sheet_names if "2ACXDD00" in sheet]

# 合併 AKT 數據
akt_data_frames = []
for sheet in akt_sheets:
    try:
        df = pd.read_excel(file_path, sheet_name=sheet)[akt_columns]
        akt_data_frames.append(df)
    except KeyError as e:
        print(f"Missing columns in AKT sheet {sheet}: {e}")
if akt_data_frames:
    akt_data_combined = pd.concat(akt_data_frames, ignore_index=True)
else:
    akt_data_combined = pd.DataFrame()
    print("No valid data for AKT sheets.")

# 合併 Jusung 數據
jusung_data_frames = []
for sheet in jusung_sheets:
    try:
        df = pd.read_excel(file_path, sheet_name=sheet)[jusung_columns]
        jusung_data_frames.append(df)
    except KeyError as e:
        print(f"Missing columns in Jusung sheet {sheet}: {e}")
if jusung_data_frames:
    jusung_data_combined = pd.concat(jusung_data_frames, ignore_index=True)
else:
    jusung_data_combined = pd.DataFrame()
    print("No valid data for Jusung sheets.")

# 修改輸出路徑
output_path = Path(DATA_DIR) / 'Combined_AKT_and_Jusung.xlsx'
with pd.ExcelWriter(output_path) as writer:
    akt_data_combined.to_excel(writer, sheet_name="AKT_Data", index=False)
    jusung_data_combined.to_excel(writer, sheet_name="Jusung_Data", index=False)

print(f"結果已保存到 {output_path}")



import pandas as pd

# 載入合併文件
file_path = Path(DATA_DIR) / 'Combined_AKT_and_Jusung.xlsx'

# 讀取 AKT_Data 和 Jusung_Data
akt_data = pd.read_excel(file_path, sheet_name="AKT_Data")
jusung_data = pd.read_excel(file_path, sheet_name="Jusung_Data")

# 找出兩個表中相同的欄位
common_columns = list(set(akt_data.columns).intersection(set(jusung_data.columns)))
print(f"Common Columns: {common_columns}")

# 提取 Jusung_Data 中的相同欄位數據
jusung_common_data = jusung_data[common_columns]

# 將 Jusung_Data 中的相同數據追加到 AKT_Data
updated_akt_data = pd.concat([akt_data, jusung_common_data], ignore_index=True)
merged_data = pd.concat([akt_data, jusung_common_data], ignore_index=True)
# 保存結果到新文件
output_path = r"D:\curso\streamlit\09_app_multipage\data\Updated_AKT_Data.xlsx"
with pd.ExcelWriter(output_path) as writer:
    updated_akt_data.to_excel(writer, sheet_name="AKT_Data", index=False)
    jusung_data.to_excel(writer, sheet_name="Jusung_Data", index=False)  # 保留原 Jusung_Data 工作表

# 修改輸出路徑
output_path = Path(DATA_DIR) / 'Updated_AKT_Data.xlsx'
with pd.ExcelWriter(output_path) as writer:
    updated_akt_data.to_excel(writer, sheet_name="AKT_Data", index=False)
    jusung_data.to_excel(writer, sheet_name="Jusung_Data", index=False)

# 保存合併結果到 CSV 文件
output_csv_path = Path(DATA_DIR) / 'Merged_Data.csv'
merged_data.to_csv(output_csv_path, index=False)

print(f"更新後的 AKT_Data 已保存到 {output_path}")