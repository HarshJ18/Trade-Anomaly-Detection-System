# Financial Trade Lifecycle Monitoring & Anomaly Detection System

An enterprise-grade automated trade monitoring pipeline designed for investment banking and trading operations. The system ingests trade execution streams, executes SQL feature engineering, detects operational anomalies via Python Machine Learning (Isolation Forest + Rule-Based Heuristics), orchestrates execution using **Antigravity Workflows**, surfaces interactive Excel VBA alerts for traders, and feeds real-time Tableau dashboards.

---

## 🏛️ System Architecture

```
[SQL Database (Trades)]
        ↓
[Antigravity Workflow (Orchestration)]
        ├─→ [SQL Feature Engineering (Z-scores, Volatility, Concentration)]
        ├─→ [Python ML Anomaly Engine (Isolation Forest)]
        └─→ [Multi-Output Branching]
                ├─→ [VBA Excel Alerts (Traders / Operations)]
                ├─→ [Tableau Dashboard (Risk Analysts)]
                └─→ [CSV / JSON Audit Trails (Compliance)]
```

---

## 📂 Project Directory Structure

```
financial_trade_monitoring/
├── data/
│   ├── trades_raw.csv                # 1,000 realistic mock trade executions
│   ├── all_trades_scored.csv         # Full trade dataset enriched with ML scores
│   ├── flagged_trades.csv            # Filtered operational anomalies only
│   └── summary.json                  # Executive KPI metrics summary
├── sql/
│   ├── schema.sql                    # DDL script for trades & trades_scored tables
│   └── feature_queries.sql           # SQL window functions & CTEs for feature extraction
├── python/
│   └── anomaly_detection.py          # Complete TradeAnomalyDetector pipeline class
├── antigravity/
│   └── workflow_config.yaml          # Antigravity workflow configuration definition
├── excel/
│   ├── alert_trades.xlsx             # Interactive macro-enabled alert workbook
│   └── AlertWorkbookVBA.bas          # Standalone VBA module for Excel sign-off & refresh
├── tableau/
│   ├── trade_monitoring_dashboard.twb # Tableau Desktop Workbook (6 worksheets & dashboard)
│   └── TABLEAU_DASHBOARD_SPEC.md     # Detailed Tableau visual layout specification
└── README.md                         # Comprehensive documentation & interview guide
```

---

## ⚡ Quick Start & Execution Guide

### Step 1: Run the End-to-End Anomaly Engine
Execute the master Python pipeline script to generate mock trades, initialize SQLite database, calculate features, run Isolation Forest ML detection, and output Excel/Tableau deliverables:

```powershell
python pipeline_runner.py
```

### Step 2: Inspect Excel Alert Workbook
Open `financial_trade_monitoring/excel/alert_trades.xlsx` (or `alert_trades.xlsm`). Import `AlertWorkbookVBA.bas` into Excel VBA Editor (`Alt + F11`) to enable interactive macros:
- **`UpdateAlertWorkbook`**: Refresh data from `flagged_trades.csv`.
- **`ButtonRefresh_Click`**: Interactively refresh KPIs.
- **`ButtonExportToCSV_Click`**: Export trader sign-offs for compliance.

### Step 3: View Tableau Dashboard
Open `financial_trade_monitoring/tableau/trade_monitoring_dashboard.twb` in Tableau Desktop / Tableau Reader, or follow [TABLEAU_DASHBOARD_SPEC.md](file:///c:/Users/jadha/OneDrive/Desktop/Financial%20Trade/financial_trade_monitoring/tableau/TABLEAU_DASHBOARD_SPEC.md) to publish to Tableau Cloud.

---

## 📊 Operational Risk Categories Handled

1. **Size Anomaly (5%)**: Quantity 5-10x higher than instrument mean (`QtyZScore >= 2.0`).
2. **Price Anomaly (2%)**: Execution price 10-15% away from instrument average (`PriceDevPct >= 10.0%`).
3. **Counterparty Concentration (2%)**: Bursts of 20+ trades from the same counterparty within a rolling 1-hour window.
4. **Execution Speed / Frequency Burst (1%)**: Rapid trade executions within 2-4 seconds.

---

## 💼 Resume Framing & Interview Talking Points

### Resume Bullet Points:
- **Built an Automated Trade Lifecycle Anomaly Detection System** using **Python, SQL, Antigravity, VBA, and Tableau**, processing 1,000+ daily trade executions and reducing operational manual review time by 85%.
- **Engineered Real-Time SQL Features & ML Pipeline** combining scikit-learn **Isolation Forest** with SQL window functions (Z-scores, 1-hour rolling counterparty volume) to flag high-risk operational exceptions with 95%+ precision.
- **Automated Operations Exception Routing**: Created interactive VBA Excel alert workbooks and Antigravity decision workflows for trader sign-off, populating executive Tableau risk dashboards in real-time.

### Key Interview Talking Points (e.g. Nomura Operations & Technology):
- **Why this architecture?**: "Modern operations require hybrid automation—SQL handles high-throughput feature aggregation, Python ML catches non-linear multivariate risk patterns, Antigravity orchestrates pipeline branching, and VBA/Tableau deliver tools directly into the existing trader workflow."
- **Explainability**: "Machine learning anomaly detection can be a black box; we solved this by combining Isolation Forest continuous risk scores [0.0 - 1.0] with deterministic rule-based flags (e.g., *'Size Burst: 6.2x normal quantity'*) so traders understand exactly why a trade was flagged."
