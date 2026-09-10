import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DB_NAME = 'trades_monitoring.db'

def run_anomaly_detection(db_path=DB_NAME, contamination=0.10):
    conn = sqlite3.connect(db_path)
    
    # Load features from database
    query = "SELECT * FROM trades_features"
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        raise ValueError("No data found in trades_features table.")

    # Prepare features for ML model
    # We take absolute values of Z-scores & Price deviations and log of time deltas for robust ML scaling
    df['AbsQtyZScore'] = df['QtyZScore'].abs()
    df['AbsPriceDevPct'] = df['PriceDevPct'].abs()
    df['LogNotional'] = np.log1p(df['NotionalValue'])
    df['LogCPVolume'] = np.log1p(df['CP_1H_NotionalVolume'])
    
    feature_cols = [
        'AbsQtyZScore',
        'AbsPriceDevPct',
        'CP_1H_TradeCount',
        'LogNotional',
        'LogCPVolume',
        'TimeDiffSeconds'
    ]

    X = df[feature_cols].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=42,
        max_samples='auto'
    )
    
    # Fit & predict anomaly (-1 for anomaly, 1 for normal)
    iso_preds = iso_forest.fit_predict(X_scaled)
    # Decision function: lower values mean more anomalous
    raw_scores = iso_forest.decision_function(X_scaled)

    # Convert raw scores to normalized Anomaly Risk Score [0.0 - 1.0] (higher = more anomalous)
    min_score, max_score = raw_scores.min(), raw_scores.max()
    normalized_risk_scores = 1.0 - ((raw_scores - min_score) / (max_score - min_score + 1e-6))
    normalized_risk_scores = np.round(normalized_risk_scores, 4)

    df['IsolationForestScore'] = raw_scores
    df['AnomalyRiskScore'] = normalized_risk_scores
    df['ML_IsAnomaly'] = (iso_preds == -1).astype(int)

    # Apply Rule-Based Heuristic Classifiers for Explainability
    df['IsSizeAnomaly'] = ((df['AbsQtyZScore'] >= 3.0) | (df['Quantity'] >= 4.0 * df['AvgInstrumentQty'])).astype(int)
    df['IsPriceAnomaly'] = (df['AbsPriceDevPct'] >= 8.0).astype(int)
    df['IsConcentrationAnomaly'] = (df['CP_1H_TradeCount'] >= 15).astype(int)
    df['IsSpeedAnomaly'] = (df['TimeDiffSeconds'] <= 4.0).astype(int)

    # Combined anomaly flag (ML flag or any heuristic flag)
    df['IsAnomaly'] = (
        (df['ML_IsAnomaly'] == 1) | 
        (df['IsSizeAnomaly'] == 1) | 
        (df['IsPriceAnomaly'] == 1) | 
        (df['IsConcentrationAnomaly'] == 1) | 
        (df['IsSpeedAnomaly'] == 1)
    ).astype(int)

    # Determine Primary Anomaly Reason and Risk Tier
    reasons = []
    risk_tiers = []

    for idx, row in df.iterrows():
        row_reasons = []
        if row['IsSizeAnomaly'] == 1:
            row_reasons.append(f"Size Burst (Z: {row['QtyZScore']:.1f})")
        if row['IsPriceAnomaly'] == 1:
            row_reasons.append(f"Price Swing ({row['PriceDevPct']:+.1f}%)")
        if row['IsConcentrationAnomaly'] == 1:
            row_reasons.append(f"Counterparty Spike ({row['CP_1H_TradeCount']} trades/hr)")
        if row['IsSpeedAnomaly'] == 1:
            row_reasons.append(f"Rapid Interval ({row['TimeDiffSeconds']:.1f}s)")
        
        if not row_reasons and row['ML_IsAnomaly'] == 1:
            row_reasons.append("Multivariate Isolation Forest Pattern")

        primary_reason = " / ".join(row_reasons) if row_reasons else "Normal Execution"
        reasons.append(primary_reason)

        # Risk Tiers
        score = row['AnomalyRiskScore']
        flags_count = row['IsSizeAnomaly'] + row['IsPriceAnomaly'] + row['IsConcentrationAnomaly'] + row['IsSpeedAnomaly']
        
        if flags_count >= 2 or score >= 0.75:
            tier = 'CRITICAL'
        elif flags_count == 1 or score >= 0.60:
            tier = 'HIGH'
        elif score >= 0.45:
            tier = 'MEDIUM'
        else:
            tier = 'LOW'
            
        risk_tiers.append(tier)

    df['PrimaryAnomalyReason'] = reasons
    df['RiskTier'] = risk_tiers
    df['ProcessedTimestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Columns to save to database and export
    output_cols = [
        'TradeID', 'ExecutionTime', 'Quantity', 'Price', 'Counterparty',
        'Instrument', 'TradeSide', 'Trader', 'Desk', 'ExecutionVenue',
        'InjectedAnomalyType', 'NotionalValue', 'QtyZScore', 'PriceDevPct',
        'CP_1H_TradeCount', 'CP_1H_NotionalVolume', 'TimeDiffSeconds',
        'IsolationForestScore', 'IsAnomaly', 'AnomalyRiskScore', 'RiskTier',
        'PrimaryAnomalyReason', 'IsSizeAnomaly', 'IsPriceAnomaly',
        'IsConcentrationAnomaly', 'IsSpeedAnomaly', 'ProcessedTimestamp'
    ]

    df_output = df[output_cols]

    # Save to SQLite database
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trades_analyzed")
    df_output.to_sql('trades_analyzed', conn, if_exists='append', index=False)
    conn.commit()
    print(f"[OK] Saved {len(df_output)} analyzed trades to database table 'trades_analyzed'.")

    # Export full analyzed dataset to CSV
    df_output.to_csv('trades_analyzed.csv', index=False)
    print("[OK] Exported 'trades_analyzed.csv'.")

    # Export alerts CSV (Critical, High, Medium Risk Tiers)
    df_alerts = df_output[df_output['RiskTier'].isin(['CRITICAL', 'HIGH', 'MEDIUM'])].sort_values(
        by=['AnomalyRiskScore', 'ExecutionTime'], ascending=[False, False]
    )
    df_alerts.to_csv('anomaly_alerts.csv', index=False)
    print(f"[OK] Exported {len(df_alerts)} prioritized alerts to 'anomaly_alerts.csv'.")

    # Print summary statistics
    print("\n--- ML Anomaly Detection Summary ---")
    print(f"Total Trades Evaluated: {len(df_output)}")
    print(f"Anomalies Flagged: {df_output['IsAnomaly'].sum()} ({df_output['IsAnomaly'].mean()*100:.1f}%)")
    print("\nRisk Tier Breakdown:")
    print(df_output['RiskTier'].value_counts())

    conn.close()
    return df_output

if __name__ == '__main__':
    run_anomaly_detection()
