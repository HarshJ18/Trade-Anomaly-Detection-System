import sqlite3
import pandas as pd

DB_NAME = 'trades_monitoring.db'
OUTPUT_TABLEAU_CSV = 'tableau_trade_analytics.csv'

def export_tableau_dataset(db_path=DB_NAME, output_file=OUTPUT_TABLEAU_CSV):
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        TradeID,
        ExecutionTime,
        DATE(ExecutionTime) AS ExecutionDate,
        TIME(ExecutionTime) AS ExecutionTimeOnly,
        STRFTIME('%H', ExecutionTime) AS ExecutionHour,
        Quantity,
        Price,
        Counterparty,
        Instrument,
        TradeSide,
        Trader,
        Desk,
        ExecutionVenue,
        InjectedAnomalyType,
        NotionalValue,
        QtyZScore,
        PriceDevPct,
        CP_1H_TradeCount,
        CP_1H_NotionalVolume,
        TimeDiffSeconds,
        IsolationForestScore,
        IsAnomaly,
        AnomalyRiskScore,
        RiskTier,
        PrimaryAnomalyReason,
        IsSizeAnomaly,
        IsPriceAnomaly,
        IsConcentrationAnomaly,
        IsSpeedAnomaly,
        CASE 
            WHEN RiskTier = 'CRITICAL' THEN 4
            WHEN RiskTier = 'HIGH' THEN 3
            WHEN RiskTier = 'MEDIUM' THEN 2
            ELSE 1
        END AS RiskTierRank
    FROM trades_analyzed
    ORDER BY ExecutionTime ASC
    """
    
    df_tab = pd.read_sql_query(query, conn)
    conn.close()
    
    df_tab.to_csv(output_file, index=False)
    print(f"[OK] Exported Tableau analytical dataset to '{output_file}' ({len(df_tab)} records).")
    return output_file

if __name__ == '__main__':
    export_tableau_dataset()
