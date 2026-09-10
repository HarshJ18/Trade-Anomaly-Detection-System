import sqlite3
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule

DB_NAME = 'trades_monitoring.db'
OUTPUT_EXCEL = 'Trade_Anomaly_Alerts.xlsx'

def create_excel_alert_report(db_path=DB_NAME, output_file=OUTPUT_EXCEL):
    conn = sqlite3.connect(db_path)
    df_all = pd.read_sql_query("SELECT * FROM trades_analyzed ORDER BY ExecutionTime DESC", conn)
    conn.close()

    if df_all.empty:
        raise ValueError("No data found in trades_analyzed table.")

    df_alerts = df_all[df_all['RiskTier'].isin(['CRITICAL', 'HIGH', 'MEDIUM'])].copy()

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styles & Palettes
    navy_header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    accent_header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
    
    kpi_card_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
    critical_fill = PatternFill(start_color="FADBD8", end_color="FADBD8", fill_type="solid") # Soft Light Red
    high_fill = PatternFill(start_color="FDEBD0", end_color="FDEBD0", fill_type="solid")     # Soft Light Orange
    medium_fill = PatternFill(start_color="FCF3CF", end_color="FCF3CF", fill_type="solid")   # Soft Light Yellow
    
    font_title = Font(name="Segoe UI", size=16, bold=True, color="1B365D")
    font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="555555")
    font_section = Font(name="Segoe UI", size=12, bold=True, color="1B365D")
    font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    font_kpi_label = Font(name="Segoe UI", size=9, bold=True, color="7F8C8D")
    font_kpi_val = Font(name="Segoe UI", size=16, bold=True, color="1B365D")

    thin_border = Border(
        left=Side(style='thin', color='D0D7DE'),
        right=Side(style='thin', color='D0D7DE'),
        top=Side(style='thin', color='D0D7DE'),
        bottom=Side(style='thin', color='D0D7DE')
    )

    # -------------------------------------------------------------------------
    # SHEET 1: Executive Dashboard
    # -------------------------------------------------------------------------
    ws_dash = wb.create_sheet(title="Executive Dashboard")
    ws_dash.views.sheetView[0].showGridLines = True

    ws_dash["A1"] = "FINANCIAL TRADE LIFECYCLE MONITORING - EXECUTIVE DASHBOARD"
    ws_dash["A1"].font = font_title
    ws_dash["A2"] = "Real-time Operations Risk Analytics & Anomaly Detection Summary"
    ws_dash["A2"].font = font_subtitle

    # KPI Cards Setup
    kpis = [
        ("TOTAL TRADES MONITORED", len(df_all), "A4", "B5", "#,##0"),
        ("CRITICAL ANOMALIES", len(df_all[df_all['RiskTier'] == 'CRITICAL']), "D4", "E5", "#,##0"),
        ("HIGH RISK ALERTS", len(df_all[df_all['RiskTier'] == 'HIGH']), "G4", "H5", "#,##0"),
        ("TOTAL RISK NOTIONAL ($)", df_alerts['NotionalValue'].sum(), "J4", "K5", "$#,##0")
    ]

    for label, val, top_left, bot_right, num_fmt in kpis:
        c_top = ws_dash[top_left[0] + top_left[1]]
        c_bot = ws_dash[top_left[0] + str(int(top_left[1])+1)]
        
        c_top.value = label
        c_top.font = font_kpi_label
        c_top.alignment = Alignment(horizontal="center", vertical="center")
        
        c_bot.value = val
        c_bot.font = font_kpi_val
        c_bot.number_format = num_fmt
        c_bot.alignment = Alignment(horizontal="center", vertical="center")

    # Desk Breakdown Table
    ws_dash["A8"] = "Anomaly Summary by Desk"
    ws_dash["A8"].font = font_section

    headers_desk = ["Desk", "Total Trades", "Critical", "High", "Medium", "Anomaly Rate %", "Total Notional ($)"]
    for col_idx, h in enumerate(headers_desk, 1):
        cell = ws_dash.cell(row=9, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = navy_header_fill
        cell.alignment = Alignment(horizontal="center")

    desk_summary = df_all.groupby('Desk').agg(
        TotalTrades=('TradeID', 'count'),
        Critical=('RiskTier', lambda x: (x == 'CRITICAL').sum()),
        High=('RiskTier', lambda x: (x == 'HIGH').sum()),
        Medium=('RiskTier', lambda x: (x == 'MEDIUM').sum()),
        TotalNotional=('NotionalValue', 'sum')
    ).reset_index()

    for row_idx, row in desk_summary.iterrows():
        r = 10 + row_idx
        ws_dash.cell(row=r, column=1, value=row['Desk']).alignment = Alignment(horizontal="left")
        ws_dash.cell(row=r, column=2, value=int(row['TotalTrades'])).number_format = "#,##0"
        ws_dash.cell(row=r, column=3, value=int(row['Critical'])).number_format = "#,##0"
        ws_dash.cell(row=r, column=4, value=int(row['High'])).number_format = "#,##0"
        ws_dash.cell(row=r, column=5, value=int(row['Medium'])).number_format = "#,##0"
        
        anom_rate = (row['Critical'] + row['High'] + row['Medium']) / max(1, row['TotalTrades'])
        ws_dash.cell(row=r, column=6, value=anom_rate).number_format = "0.0%"
        ws_dash.cell(row=r, column=7, value=float(row['TotalNotional'])).number_format = "$#,##0"

        for c in range(1, 8):
            ws_dash.cell(row=r, column=c).border = thin_border

    # Counterparty Exposure Table
    ws_dash["A16"] = "Top 5 Counterparties by Anomaly Frequency"
    ws_dash["A16"].font = font_section

    headers_cp = ["Counterparty", "Total Trades", "Flagged Anomalies", "Max 1H Trade Burst", "Total Notional Exposure ($)"]
    for col_idx, h in enumerate(headers_cp, 1):
        cell = ws_dash.cell(row=17, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = navy_header_fill
        cell.alignment = Alignment(horizontal="center")

    cp_summary = df_all.groupby('Counterparty').agg(
        TotalTrades=('TradeID', 'count'),
        Anomalies=('IsAnomaly', 'sum'),
        Max1HBurst=('CP_1H_TradeCount', 'max'),
        TotalNotional=('NotionalValue', 'sum')
    ).reset_index().sort_values(by='Anomalies', ascending=False).head(5)

    for row_idx, row in cp_summary.iterrows():
        r = 18 + row_idx
        ws_dash.cell(row=r, column=1, value=row['Counterparty'])
        ws_dash.cell(row=r, column=2, value=int(row['TotalTrades'])).number_format = "#,##0"
        ws_dash.cell(row=r, column=3, value=int(row['Anomalies'])).number_format = "#,##0"
        ws_dash.cell(row=r, column=4, value=int(row['Max1HBurst'])).number_format = "#,##0"
        ws_dash.cell(row=r, column=5, value=float(row['TotalNotional'])).number_format = "$#,##0"

        for c in range(1, 6):
            ws_dash.cell(row=r, column=c).border = thin_border

    # -------------------------------------------------------------------------
    # SHEET 2: Critical & High Alerts
    # -------------------------------------------------------------------------
    ws_alerts = wb.create_sheet(title="Critical & High Alerts")
    ws_alerts.views.sheetView[0].showGridLines = True

    ws_alerts["A1"] = "PRIORITIZED ANOMALY ALERTS TABLE"
    ws_alerts["A1"].font = font_title
    ws_alerts["A2"] = "Filtered operational risk alerts requiring trader / middle-office sign-off"
    ws_alerts["A2"].font = font_subtitle

    # VBA Macro Instruction Banner
    ws_alerts["A4"] = "VBA MACRO ACTIONS: Run 'AcknowledgeTrade' to sign off on selected row | Run 'ExportAuditLog' to generate audit CSV"
    ws_alerts["A4"].font = Font(name="Segoe UI", size=9, bold=True, color="9C0006")
    ws_alerts["A4"].fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    headers_alerts = [
        "TradeID", "ExecutionTime", "Quantity", "Price", "Counterparty",
        "Instrument", "TradeSide", "Trader", "Desk", "NotionalValue",
        "RiskTier", "PrimaryAnomalyReason", "RiskScore", "QtyZScore", "PriceDevPct",
        "CP_1H_Trades", "TimeDiffSec", "SizeAnom", "PriceAnom", "ConcAnom", "SpeedAnom",
        "Trader Sign-Off Status", "Sign-Off Timestamp"
    ]

    for col_idx, h in enumerate(headers_alerts, 1):
        cell = ws_alerts.cell(row=7, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = navy_header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row_idx, row in df_alerts.iterrows():
        r = 8 + row_idx
        ws_alerts.cell(row=r, column=1, value=row['TradeID'])
        ws_alerts.cell(row=r, column=2, value=str(row['ExecutionTime']))
        ws_alerts.cell(row=r, column=3, value=float(row['Quantity'])).number_format = "#,##0.00"
        ws_alerts.cell(row=r, column=4, value=float(row['Price'])).number_format = "$#,##0.0000" if row['Desk']=='FX' else "$#,##0.00"
        ws_alerts.cell(row=r, column=5, value=row['Counterparty'])
        ws_alerts.cell(row=r, column=6, value=row['Instrument'])
        ws_alerts.cell(row=r, column=7, value=row['TradeSide'])
        ws_alerts.cell(row=r, column=8, value=row['Trader'])
        ws_alerts.cell(row=r, column=9, value=row['Desk'])
        ws_alerts.cell(row=r, column=10, value=float(row['NotionalValue'])).number_format = "$#,##0"
        
        tier_cell = ws_alerts.cell(row=r, column=11, value=row['RiskTier'])
        tier_cell.alignment = Alignment(horizontal="center")
        if row['RiskTier'] == 'CRITICAL':
            tier_cell.fill = critical_fill
            tier_cell.font = Font(name="Segoe UI", bold=True, color="9C0006")
        elif row['RiskTier'] == 'HIGH':
            tier_cell.fill = high_fill
            tier_cell.font = Font(name="Segoe UI", bold=True, color="9C6500")
        else:
            tier_cell.fill = medium_fill

        ws_alerts.cell(row=r, column=12, value=row['PrimaryAnomalyReason'])
        ws_alerts.cell(row=r, column=13, value=float(row['AnomalyRiskScore'])).number_format = "0.000"
        ws_alerts.cell(row=r, column=14, value=float(row['QtyZScore'])).number_format = "+0.0;-0.0;0.0"
        ws_alerts.cell(row=r, column=15, value=float(row['PriceDevPct']) / 100.0).number_format = "+0.0%;-0.0%;0.0%"
        ws_alerts.cell(row=r, column=16, value=int(row['CP_1H_TradeCount']))
        ws_alerts.cell(row=r, column=17, value=float(row['TimeDiffSeconds'])).number_format = "0.0"
        
        ws_alerts.cell(row=r, column=18, value=int(row['IsSizeAnomaly']))
        ws_alerts.cell(row=r, column=19, value=int(row['IsPriceAnomaly']))
        ws_alerts.cell(row=r, column=20, value=int(row['IsConcentrationAnomaly']))
        ws_alerts.cell(row=r, column=21, value=int(row['IsSpeedAnomaly']))

        ws_alerts.cell(row=r, column=22, value="PENDING REVIEW").alignment = Alignment(horizontal="center")
        ws_alerts.cell(row=r, column=23, value="").alignment = Alignment(horizontal="center")

        for c in range(1, 24):
            ws_alerts.cell(row=r, column=c).border = thin_border

    # -------------------------------------------------------------------------
    # SHEET 3: All Analyzed Trades
    # -------------------------------------------------------------------------
    ws_full = wb.create_sheet(title="All Analyzed Trades")
    ws_full.views.sheetView[0].showGridLines = True

    ws_full["A1"] = "FULL TRADE AUDIT LOG & ML FEATURES"
    ws_full["A1"].font = font_title

    headers_full = list(df_all.columns)
    for col_idx, h in enumerate(headers_full, 1):
        cell = ws_full.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = accent_header_fill
        cell.alignment = Alignment(horizontal="center")

    for row_idx, row in df_all.iterrows():
        r = 4 + row_idx
        for col_idx, val in enumerate(row, 1):
            cell = ws_full.cell(row=r, column=col_idx, value=val)
            cell.border = thin_border

    # Auto-fit column widths across all sheets
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(output_file)
    print(f"[OK] Created Excel Alert Report: '{output_file}' with 3 styled sheets.")
    return output_file

if __name__ == '__main__':
    create_excel_alert_report()
