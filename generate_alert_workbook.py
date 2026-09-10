import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import json
import os
from datetime import datetime

def generate_alert_workbook(flagged_csv='trade_monitoring_flagged.csv', summary_json='trade_monitoring_summary.json', output_file='alert_trades.xlsx'):
    wb = openpyxl.Workbook()
    wb.remove(wb.active) # Remove default sheet

    # Colors and Styles
    font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="4682B4", end_color="4682B4", fill_type="solid") # Steel Blue
    
    font_bold = Font(name="Segoe UI", size=10, bold=True)
    font_regular = Font(name="Segoe UI", size=10)
    font_title = Font(name="Segoe UI", size=14, bold=True, color="1B365D")
    
    thin_border = Border(
        left=Side(style='thin', color='D0D7DE'),
        right=Side(style='thin', color='D0D7DE'),
        top=Side(style='thin', color='D0D7DE'),
        bottom=Side(style='thin', color='D0D7DE')
    )

    # -------------------------------------------------------------------------
    # SHEET 1: Summary
    # -------------------------------------------------------------------------
    ws_sum = wb.create_sheet(title="Summary")
    ws_sum.views.sheetView[0].showGridLines = True

    ws_sum["A1"] = "TRADE ANOMALY MONITORING - EXECUTIVE SUMMARY"
    ws_sum["A1"].font = font_title

    headers_summary = ["Metric", "Value", "Status"]
    for col_idx, h in enumerate(headers_summary, 1):
        cell = ws_sum.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    # Load summary data from JSON if available
    summary_data = {}
    if os.path.exists(summary_json):
        with open(summary_json, 'r') as f:
            summary_data = json.load(f)

    flagged_count = summary_data.get('flagged_count', 0)
    high_count = summary_data.get('high_severity', 0)
    med_count = summary_data.get('medium_severity', 0)
    tot_risk = summary_data.get('total_notional_risk', 0.0)

    rows_summary = [
        ("Flagged Trades", f"{flagged_count} trades", "ALERT" if flagged_count > 0 else "NORMAL"),
        ("HIGH Severity", f"{high_count} trades", "HIGH" if high_count > 0 else "OK"),
        ("MEDIUM Severity", f"{med_count} trades", "MEDIUM" if med_count > 0 else "OK"),
        ("Total Risk", tot_risk, "")
    ]

    for idx, (m, v, s) in enumerate(rows_summary, 4):
        c_m = ws_sum.cell(row=idx, column=1, value=m)
        c_v = ws_sum.cell(row=idx, column=2, value=v)
        c_s = ws_sum.cell(row=idx, column=3, value=s)

        c_m.font = font_bold
        c_v.font = font_regular
        c_s.font = font_bold
        c_s.alignment = Alignment(horizontal="center")

        if m == "Total Risk":
            c_v.number_format = "$#,##0.00"

        # Apply Status fills
        if s in ["ALERT", "HIGH"]:
            c_s.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            c_s.font = Font(name="Segoe UI", bold=True, color="9C0006")
        elif s == "MEDIUM":
            c_s.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            c_s.font = Font(name="Segoe UI", bold=True, color="9C6500")

        for col in range(1, 4):
            ws_sum.cell(row=idx, column=col).border = thin_border

    ws_sum.cell(row=9, column=1, value="Last Updated:").font = font_bold
    ws_sum.cell(row=9, column=2, value=datetime.now().strftime('%Y-%m-%d %H:%M:%S')).font = font_regular

    # -------------------------------------------------------------------------
    # SHEET 2: Flagged Trades
    # -------------------------------------------------------------------------
    ws_flagged = wb.create_sheet(title="Flagged Trades")
    ws_flagged.views.sheetView[0].showGridLines = True

    if os.path.exists(flagged_csv):
        df_flagged = pd.read_csv(flagged_csv)
    else:
        df_flagged = pd.DataFrame(columns=[
            'TradeID', 'ExecutionTime', 'Quantity', 'Price', 'Counterparty', 
            'Instrument', 'anomaly_type', 'severity_level', 'anomaly_score'
        ])

    headers_flagged = ['TradeID', 'Time', 'Quantity', 'Price', 'Counterparty', 'Instrument', 'Type', 'Severity', 'Score']
    for col_idx, h in enumerate(headers_flagged, 1):
        cell = ws_flagged.cell(row=1, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center")

    fill_red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    fill_orange = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    fill_yellow = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

    for idx, row in df_flagged.iterrows():
        r = 2 + idx
        ws_flagged.cell(row=r, column=1, value=str(row.get('TradeID', '')))
        ws_flagged.cell(row=r, column=2, value=str(row.get('ExecutionTime', '')))
        ws_flagged.cell(row=r, column=3, value=float(row.get('Quantity', 0))).number_format = "#,##0"
        ws_flagged.cell(row=r, column=4, value=float(row.get('Price', 0))).number_format = "$#,##0.00"
        ws_flagged.cell(row=r, column=5, value=str(row.get('Counterparty', '')))
        ws_flagged.cell(row=r, column=6, value=str(row.get('Instrument', '')))
        ws_flagged.cell(row=r, column=7, value=str(row.get('anomaly_type', 'MULTI_FACTOR')))
        
        sev = str(row.get('severity_level', 'MEDIUM')).upper()
        sev_cell = ws_flagged.cell(row=r, column=8, value=sev)
        sev_cell.alignment = Alignment(horizontal="center")
        
        ws_flagged.cell(row=r, column=9, value=float(row.get('anomaly_score', 0.0))).number_format = "0.00%"

        # Color row based on severity
        if sev == 'HIGH':
            sev_fill = fill_red
        elif sev == 'MEDIUM':
            sev_fill = fill_orange
        else:
            sev_fill = fill_yellow

        for c in range(1, 10):
            cell = ws_flagged.cell(row=r, column=c)
            cell.fill = sev_fill
            cell.border = thin_border

    # -------------------------------------------------------------------------
    # SHEET 3: Settings (Hidden)
    # -------------------------------------------------------------------------
    ws_set = wb.create_sheet(title="Settings")
    ws_set.views.sheetView[0].showGridLines = True
    
    ws_set.cell(row=1, column=1, value="Threshold Parameter").font = font_header
    ws_set.cell(row=1, column=1).fill = fill_header
    ws_set.cell(row=1, column=2, value="Value").font = font_header
    ws_set.cell(row=1, column=2).fill = fill_header

    settings_data = [
        ("Anomaly Threshold", 0.70),
        ("High Severity Threshold", 0.85),
        ("Medium Severity Threshold", 0.70),
        ("Z-Score Cutoff", 2.00),
        ("Price Deviation Cutoff", 0.10),
        ("1-Hour Counterparty Threshold", 20)
    ]

    for idx, (param, val) in enumerate(settings_data, 2):
        ws_set.cell(row=idx, column=1, value=param).font = font_bold
        ws_set.cell(row=idx, column=2, value=val).font = font_regular
        ws_set.cell(row=idx, column=1).border = thin_border
        ws_set.cell(row=idx, column=2).border = thin_border

    # Auto-fit columns
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 14)

    wb.save(output_file)
    print(f"[OK] Generated Excel Alert Workbook '{output_file}' matching Phase 5 specifications.")
    return output_file

if __name__ == '__main__':
    generate_alert_workbook()
