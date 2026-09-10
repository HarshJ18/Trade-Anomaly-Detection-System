import time
import os
import shutil
from datetime import datetime

from generate_mock_data import generate_mock_trades
from db_manager import initialize_database
from anomaly_detection import TradeAnomalyDetector
from anomaly_detector import run_anomaly_detection
from generate_excel_alerts import create_excel_alert_report
from generate_alert_workbook import generate_alert_workbook
from tableau_export import export_tableau_dataset

def run_pipeline():
    start_time = time.time()
    print("==========================================================================")
    print(f"   FINANCIAL TRADE LIFECYCLE MONITORING & ANOMALY DETECTION PIPELINE")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("==========================================================================")

    # Step 1: Data Ingestion / Mock Generation
    print("\n[STEP 1/7] EXTRACT: Generating Mock Trade Execution Data...")
    df_raw = generate_mock_trades(n_trades=1000, output_file='trades_raw.csv')

    # Step 2: Database Setup & Feature Engineering
    print("\n[STEP 2/7] TRANSFORM: Initializing SQLite DBs & Feature Engineering...")
    db_path = initialize_database(csv_path='trades_raw.csv')

    # Step 3: Python ML Anomaly Detection Engine (TradeAnomalyDetector - trades.db)
    print("\n[STEP 3/7] PYTHON ML: Running TradeAnomalyDetector Pipeline...")
    detector = TradeAnomalyDetector(db_path='trades.db')
    detector.run(input_source='trades_raw.csv')

    # Step 4: Multi-Factor Anomaly Scoring Engine (trades_monitoring.db)
    print("\n[STEP 4/7] PYTHON ML: Running Multi-Factor Isolation Forest Engine...")
    df_analyzed = run_anomaly_detection(db_path=db_path, contamination=0.10)

    # Step 5: Excel Alert Workbooks Generation (VBA Integration)
    print("\n[STEP 5/7] EXCEL ALERTS: Generating VBA-Enabled Alert Workbooks...")
    excel_path_1 = create_excel_alert_report()
    excel_path_2 = generate_alert_workbook(
        flagged_csv='trade_monitoring_flagged.csv',
        summary_json='trade_monitoring_summary.json',
        output_file='alert_trades.xlsx'
    )

    # Step 6: Tableau Analytical Extract Preparation
    print("\n[STEP 6/7] TABLEAU EXTRACT: Formatting Data for Tableau Desktop / Cloud...")
    tableau_csv = export_tableau_dataset()

    # Step 7: Export Outputs & Audit Directory Population (Antigravity Step 5)
    print("\n[STEP 7/7] EXPORT & BRANCHING: Copying Deliverables to 'outputs/' Directory...")
    output_dir = 'outputs'
    os.makedirs(output_dir, exist_ok=True)

    shutil.copy('trade_monitoring_flagged.csv', os.path.join(output_dir, 'flagged_trades.csv'))
    shutil.copy('trade_monitoring_all_trades.csv', os.path.join(output_dir, 'all_trades.csv'))
    shutil.copy('trade_monitoring_summary.json', os.path.join(output_dir, 'summary.json'))
    shutil.copy('alert_trades.xlsx', os.path.join(output_dir, 'alert_trades.xlsx'))
    print(f"[OK] Exported files to '{output_dir}/' folder.")

    elapsed = time.time() - start_time
    print("\n==========================================================================")
    print(f"[OK] PIPELINE EXECUTED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print("==========================================================================")
    print("Generated Artifacts & Pipeline Deliverables:")
    print(" 1. Antigravity Workflow Config : antigravity_workflow.yaml")
    print(" 2. Raw Trades Database & CSV    : trades_raw.csv / trades.db / trades_monitoring.db")
    print(" 3. Scored Trades CSV & JSON     : trade_monitoring_all_trades.csv / summary.json")
    print(" 4. Flagged Anomaly CSV Extract  : trade_monitoring_flagged.csv / outputs/flagged_trades.csv")
    print(" 5. Interactive Excel Workbooks  : Trade_Anomaly_Alerts.xlsx / alert_trades.xlsx")
    print(" 6. Tableau Analytical Extract   : tableau_trade_analytics.csv")
    print(" 7. VBA Automation Modules       : vba_modules/AlertWorkbookVBA.bas & AnomalyAlertsModule.bas")
    print(" 8. Tableau Visual Specs Guide   : TABLEAU_DASHBOARD_SPEC.md")
    print("==========================================================================")

if __name__ == '__main__':
    run_pipeline()
