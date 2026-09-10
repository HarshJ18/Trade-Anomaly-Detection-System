# Trade Anomaly Detection System

> **An end-to-end risk monitoring and ML-powered trade surveillance pipeline for automated anomaly detection and settlement oversight.**

---

## Overview

In modern financial markets, high-volume trade executions expose financial institutions to operational, market, and counterparty risks. Traditional rule-based surveillance systems often fail to capture subtle multi-dimensional risk patterns or generate excessive false positives that overwhelm risk operations teams.

The **Trade Anomaly Detection System** provides an automated, end-to-end trade monitoring solution designed for risk management and settlement oversight. By combining SQL-driven statistical feature engineering with an unsupervised Python Machine Learning pipeline (Isolation Forest), the system flags anomalous executions, classifies risk severity, automates enterprise alerting via Antigravity workflow orchestration and VBA-enabled Excel workbooks, and delivers interactive analytics via Tableau dashboards.

---

## Key Features

- **SQL Feature Engineering:** Computes statistical baseline metrics including quantity Z-scores, price deviation percentages, rolling 1-hour counterparty trade counts, notional volumes, and inter-trade time deltas.
- **Unsupervised ML Anomaly Scoring:** Employs Scikit-learn's Isolation Forest algorithm to detect multi-variable trade anomalies without relying on historical labels.
- **Explainable Severity Classification:** Categorizes flagged trades into Low, Medium, and High risk tiers using normalized risk scores $[0.0 - 1.0]$ coupled with heuristic reason codes (e.g., Size Burst, Price Swing, Counterparty Spike, Rapid Interval).
- **Threshold Calibration:** Calibrates detection sensitivity against historical trade distributions to optimize the trade-off between detection rates and operational false-positive fatigue.
- **Automated Workflow Orchestration & Alerting:** Utilizes Antigravity orchestration for conditional branching, generating color-coded VBA Excel alert workbooks and operational notifications.
- **Interactive Stakeholder Dashboards:** Delivers Tableau analytical extracts and visualization specifications for executive KPI tracking, risk heatmaps, and granular trade drill-downs.

---

## Architecture & Workflow

The pipeline executes through a 7-stage automated lifecycle from raw trade execution ingestion to stakeholder dashboard reporting:

```text
+----------------------+
|   Raw Trade Data     | (CSV / Database Ingestion)
+----------+-----------+
           |
           v
+----------------------+
|  SQL Feature Engine  | (Z-Scores, Price Dev %, Rolling CP Counts, Time Deltas)
+----------+-----------+
           |
           v
+----------------------+
| Isolation Forest ML  | (Multivariate Anomaly Probability & Normalization)
+----------+-----------+
           |
           v
+----------------------+
| Severity & Heuristics| (Low / Medium / High Risk Tiers + Explainable Reason Codes)
+----------+-----------+
           |
           v
+----------------------+
| Antigravity Engine   | (Conditional Decision Branching & Operational Workflow)
+----------+-----------+
           |
    +------+------+
    |             |
    v             v
+-------+     +-------+
|  VBA  |     |Tableau|
| Excel |     | Cloud |
+-------+     +-------+
```

### Pipeline Flow Steps
1. **Data Ingestion:** Ingests raw execution logs containing trade attributes (Quantity, Price, Counterparty, Instrument, Desk, Trader).
2. **Feature Engineering:** Executes SQL queries (`feature_engineering.sql`) to calculate statistical baseline metrics and rolling counterparty concentrations.
3. **ML Scoring:** Standardizes features and fits an Isolation Forest model (`anomaly_detector.py`) to generate continuous risk scores.
4. **Severity Classification:** Assigns risk tiers (Low/Medium/High) and generates human-readable risk reason codes.
5. **Orchestration & Decision Branching:** Antigravity engine evaluates anomaly flags (`antigravity_workflow.yaml`) and routes alerts based on severity.
6. **Excel Alert Workbook Generation:** Generates styled, macro-enabled Excel reports (`alert_trades.xlsx`) with conditional formatting via VBA modules (`vba_modules/`).
7. **Tableau Integration:** Exports cleaned analytical datasets (`tableau_trade_analytics.csv`) and specs for Tableau dashboard consumption.

---

## Tech Stack

| Component | Tool / Technology | Role in Project |
| :--- | :--- | :--- |
| **Database & Transformations** | SQL (SQLite / PostgreSQL) | In-database feature engineering, statistical window functions, time deltas |
| **Core Programming** | Python 3.x | End-to-end pipeline execution, data manipulation, file handling |
| **Data Processing & Analytics**| Pandas, NumPy | Data cleaning, matrix operations, statistical transformations |
| **Machine Learning** | Scikit-learn (Isolation Forest) | Unsupervised multivariate anomaly scoring and standardization |
| **Reporting & Formatting** | VBA / OpenPyXL / XlsxWriter | Automated generation of styled Excel alert workbooks with macros |
| **Orchestration & Automation** | Antigravity Platform | Workflow DAG, conditional decision branching, task automation |
| **Business Intelligence** | Tableau Desktop / Cloud | Stakeholder analytics, KPI dashboards, interactive drill-down views |

---

## How It Works

### 1. Isolation Forest Scoring Approach
The Isolation Forest algorithm isolates trade anomalies by randomly selecting a feature and splitting values between the minimum and maximum of that feature. Because anomalous trades (e.g., extreme order size, abnormal execution speed, or sudden price spikes) differ significantly from normal market patterns, they require fewer random partition splits to isolate:

- **Path Length & Decision Function:** Shorter average path lengths in isolation trees correlate directly with higher anomaly scores.
- **Normalization:** Raw decision scores are transformed into a continuous scale $[0.0 - 1.0]$, where values closer to $1.0$ indicate high anomaly confidence.
- **Multivariate Feature Input:** Evaluates combined vector space across:
  $$\text{Feature Set} = \{\text{AbsQtyZScore}, \text{AbsPriceDevPct}, \text{CP\_1H\_TradeCount}, \text{LogNotional}, \text{LogCPVolume}, \text{TimeDiffSeconds}\}$$

### 2. Threshold Calibration & Sensitivity Trade-Off
A key challenge in trade surveillance is tuning model parameters to balance **detection sensitivity** (catching genuine operational or fraud risks) against **false-positive rate** (preventing alert fatigue for compliance officers).

```text
  High Sensitivity / Low Threshold           Balanced Calibration           Low Sensitivity / High Threshold
[ High Recall | High False Positives ] <---> [ Optimized Target: ~[X]% ] <---> [ Low Recall | Low False Positives ]
```

- **Contamination Hyperparameter:** The contamination parameter is calibrated against historical baseline trade data (e.g., setting target contamination at `[X]%`).
- **Hybrid Heuristic Coupling:** To ensure no critical edge case is missed, unsupervised ML scores are combined with rule-based heuristic boundaries (e.g., Quantity Z-Score $\ge 3.0$ or Price Deviation $\ge 8.0\%$).
- **Risk Tiering Logic:**
  - **High Risk (Score $\ge 0.75$ or Multiple Heuristics):** Immediate escalation to operations/risk lead.
  - **Medium Risk ($0.55 \le \text{Score} < 0.75$):** Flagged for daily review queue.
  - **Low Risk ($\text{Score} < 0.55$):** Passed to baseline audit log.

---

## Setup / Installation

### Prerequisites
- Python 3.9+ installed
- SQLite (or equivalent SQL database engine)
- Microsoft Excel (for VBA macro execution)
- Tableau Desktop or Tableau Public (optional, for viewing dashboards)

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HarshJ18/Trade-Anomaly-Detection-System.git
   cd Trade-Anomaly-Detection-System
   ```

2. **Create and activate a virtual environment:**
   - **On macOS/Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **On Windows:**
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

*(Note: Create a `requirements.txt` file containing `pandas`, `numpy`, `scikit-learn`, `openpyxl`, `xlsxwriter`, `pyyaml` if installing manually.)*

---

## Usage

### Running the End-to-End Surveillance Pipeline

To run the complete data generation, feature engineering, ML scoring, Excel alerting, and Tableau extract export pipeline:

```bash
python pipeline_runner.py
```

### Running Individual Pipeline Components

- **Generate Synthetic Trade Ingestion Data:**
  ```bash
  python generate_mock_data.py
  ```

- **Run ML Anomaly Detection Engine:**
  ```bash
  python anomaly_detector.py
  ```

- **Generate VBA-Enabled Excel Alert Workbooks:**
  ```bash
  python generate_excel_alerts.py
  ```

- **Export Tableau Analytical Dataset:**
  ```bash
  python tableau_export.py
  ```

---

## Sample Output & Screenshots

> *Placeholder: Add screenshots of your Tableau Dashboard and formatted Excel alert workbooks here.*

| Sample Excel Alert Report | Tableau Trade Analytics Dashboard |
| :---: | :---: |
| `![Excel Alert Workbook](docs/screenshots/excel_alert_sample.png)` <br> *Color-coded trade anomaly alert workbook with VBA macro support* | `![Tableau Dashboard](docs/screenshots/tableau_dashboard_sample.png)` <br> *Interactive Tableau dashboard showcasing anomaly KPIs and desk distribution* |

### Summary Output File Example (`outputs/summary.json`)
```json
{
  "total_trades_analyzed": "[X]",
  "anomalies_flagged": "[X]",
  "anomaly_rate_pct": "[X]%",
  "high_risk_count": "[X]",
  "medium_risk_count": "[X]",
  "low_risk_count": "[X]"
}
```

---

## Future Improvements

- [ ] **Real-Time Streaming Detection:** Integrate Apache Kafka or WebSockets to stream incoming trade messages and perform low-latency scoring.
- [ ] **Expanded Risk Feature Store:** Engineer additional risk signals such as off-market hours execution flags, trader-level behavioral drift, and multi-leg strategy variations.
- [ ] **Automated Model Retraining Pipeline:** Implement scheduled model evaluation and drift detection to auto-retrain the Isolation Forest model on fresh market data.
- [ ] **LLM-Based Alert Summarization:** Integrate generative AI prompts into Antigravity workflows to write natural-language compliance explanations for flagged trades.

---

## Author / Contact

**Harsh Joshi**
- **GitHub:** [@HarshJ18](https://github.com/HarshJ18)
- **LinkedIn:** [Harsh Joshi](https://linkedin.com/in/your-linkedin-handle)
- **Email:** `[your-email@domain.com]`

---
*Feel free to star ⭐ this repository if you find it useful or insightful!*
