import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import sqlite3
from datetime import datetime
import json
import os

class TradeAnomalyDetector:
    """
    Detects anomalies in trade data using Isolation Forest.
    Combines statistical methods (Z-scores) with ML scoring.
    """
    
    def __init__(self, db_path='trades.db'):
        self.db_path = db_path
        self.anomaly_threshold = 0.7  # Score > 0.7 = anomaly
        self.severity_thresholds = {'HIGH': 0.85, 'MEDIUM': 0.7}
        
    def setup_database_schema(self, csv_path='trades_raw.csv'):
        """Initialize SQLite database schema and load raw trades."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS trades")
        cursor.execute("DROP TABLE IF EXISTS trades_scored")
        
        cursor.execute("""
        CREATE TABLE trades (
            trade_id TEXT PRIMARY KEY,
            execution_time TIMESTAMP NOT NULL,
            quantity FLOAT NOT NULL,
            price FLOAT NOT NULL,
            counterparty TEXT NOT NULL,
            instrument TEXT NOT NULL,
            trade_side TEXT NOT NULL,
            trader TEXT NOT NULL,
            desk TEXT NOT NULL,
            execution_venue TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("""
        CREATE TABLE trades_scored (
            trade_id TEXT PRIMARY KEY,
            execution_time TIMESTAMP NOT NULL,
            quantity FLOAT NOT NULL,
            price FLOAT NOT NULL,
            counterparty TEXT NOT NULL,
            instrument TEXT NOT NULL,
            trade_side TEXT NOT NULL,
            notional_value FLOAT,
            qty_zscore FLOAT,
            price_volatility FLOAT,
            counterparty_frequency INT,
            anomaly_score FLOAT,
            severity_level TEXT,
            anomaly_type TEXT,
            flagged_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        
        if os.path.exists(csv_path):
            df_raw = pd.read_csv(csv_path)
            # Rename columns to match SQL schema lower_snake_case if needed
            df_sql = df_raw.rename(columns={
                'TradeID': 'trade_id',
                'ExecutionTime': 'execution_time',
                'Quantity': 'quantity',
                'Price': 'price',
                'Counterparty': 'counterparty',
                'Instrument': 'instrument',
                'TradeSide': 'trade_side',
                'Trader': 'trader',
                'Desk': 'desk',
                'ExecutionVenue': 'execution_venue'
            })[['trade_id', 'execution_time', 'quantity', 'price', 'counterparty', 'instrument', 'trade_side', 'trader', 'desk', 'execution_venue']]
            
            df_sql.to_sql('trades', conn, if_exists='append', index=False)
            conn.commit()
        
        conn.close()

    def load_trades_from_sql(self):
        """Load trades and calculated features from SQL."""
        query = """
        WITH instrument_stats AS (
            SELECT 
                instrument,
                AVG(quantity) as avg_qty,
                SQRT(MAX(0.0001, AVG(quantity * quantity) - AVG(quantity) * AVG(quantity))) as std_qty,
                AVG(price) as avg_price,
                MAX(price) as max_price,
                MIN(price) as min_price
            FROM trades
            GROUP BY instrument
        ),
        trades_with_features AS (
            SELECT 
                t.trade_id,
                t.execution_time,
                t.quantity,
                t.price,
                t.counterparty,
                t.instrument,
                t.trade_side,
                t.trader,
                t.desk,
                t.execution_venue,
                CASE 
                    WHEN s.std_qty = 0 THEN 0
                    ELSE (t.quantity - s.avg_qty) / s.std_qty
                END as qty_zscore,
                ABS(t.price - s.avg_price) / NULLIF(s.avg_price, 0) as price_dev_pct,
                (SELECT COUNT(*) FROM trades t2 
                 WHERE t2.counterparty = t.counterparty 
                 AND JULIANDAY(t2.execution_time) <= JULIANDAY(t.execution_time)
                 AND JULIANDAY(t2.execution_time) >= JULIANDAY(t.execution_time) - (1.0 / 24.0)
                ) as party_freq_1hr
            FROM trades t
            LEFT JOIN instrument_stats s ON t.instrument = s.instrument
        )
        SELECT * FROM trades_with_features
        ORDER BY execution_time DESC;
        """
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Ensure column names retain PascalCase compatibility for downstream functions
        df = df.rename(columns={
            'trade_id': 'TradeID',
            'execution_time': 'ExecutionTime',
            'quantity': 'Quantity',
            'price': 'Price',
            'counterparty': 'Counterparty',
            'instrument': 'Instrument',
            'trade_side': 'TradeSide',
            'trader': 'Trader',
            'desk': 'Desk',
            'execution_venue': 'ExecutionVenue'
        })
        return df
    
    def load_trades_from_csv(self, csv_path='trades_raw.csv'):
        """Load trades from CSV and engineer features."""
        df = pd.read_csv(csv_path)
        df['ExecutionTime'] = pd.to_datetime(df['ExecutionTime'])
        
        # Quantity Z-score by instrument
        df['qty_zscore'] = df.groupby('Instrument')['Quantity'].transform(
            lambda x: (x - x.mean()) / (x.std() + 1e-8)
        )
        
        # Price deviation % by instrument
        inst_means = df.groupby('Instrument')['Price'].transform('mean')
        df['price_dev_pct'] = (df['Price'] - inst_means).abs() / (inst_means + 1e-8)
        
        # Counterparty frequency (1-hour window count per trade)
        df['party_freq_1hr'] = df.groupby('Counterparty')['Quantity'].transform('count')
        
        return df
    
    def engineer_ml_features(self, df):
        """Create features for ML model."""
        features_df = df.copy()
        
        scaler = StandardScaler()
        feature_cols = ['qty_zscore', 'price_dev_pct', 'party_freq_1hr']
        
        scaled_vals = scaler.fit_transform(
            features_df[[col for col in feature_cols if col in features_df.columns]].fillna(0)
        )
        
        for idx, col in enumerate(feature_cols):
            if col in features_df.columns:
                features_df[f'{col}_scaled'] = scaled_vals[:, idx]
        
        weights = {'qty_zscore': 0.4, 'price_dev_pct': 0.3, 'party_freq_1hr': 0.3}
        features_df['risk_score'] = sum(
            weights.get(col, 0) * features_df[col].abs() 
            for col in feature_cols if col in features_df.columns
        ) / sum(weights.values())
        
        return features_df
    
    def detect_anomalies(self, df):
        """Apply Isolation Forest to detect anomalies."""
        feature_cols = ['qty_zscore', 'price_dev_pct', 'party_freq_1hr']
        X = df[[col for col in feature_cols if col in df.columns]].fillna(0).values
        
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_predictions = iso_forest.fit_predict(X)  # -1 for anomaly, 1 for normal
        anomaly_scores = -iso_forest.score_samples(X)  # Convert score samples
        
        # Normalize scores to 0-1
        anomaly_scores = (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min() + 1e-8)
        
        df['anomaly_score'] = np.round(anomaly_scores, 4)
        df['is_anomaly'] = df['anomaly_score'] > self.anomaly_threshold
        
        # Assign severity
        df['severity_level'] = df['anomaly_score'].apply(self._classify_severity)
        
        # Determine anomaly type
        df['anomaly_type'] = df.apply(self._classify_anomaly_type, axis=1)
        
        # Generate flagged reason
        df['flagged_reason'] = df.apply(self._generate_reason, axis=1)
        
        return df
    
    def _classify_severity(self, score):
        """Classify anomaly severity based on score."""
        if score >= self.severity_thresholds['HIGH']:
            return 'HIGH'
        elif score >= self.severity_thresholds['MEDIUM']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _classify_anomaly_type(self, row):
        """Classify the type of anomaly detected."""
        if not row['is_anomaly']:
            return 'NORMAL'
        
        if abs(row['qty_zscore']) > 2:
            return 'SIZE_ANOMALY'
        elif row['price_dev_pct'] > 0.1:
            return 'PRICE_ANOMALY'
        elif row['party_freq_1hr'] > 20:
            return 'CONCENTRATION'
        else:
            return 'MULTI_FACTOR'
    
    def _generate_reason(self, row):
        """Generate human-readable flagged reason."""
        reasons = []
        
        if abs(row['qty_zscore']) > 2:
            reasons.append(f"{row['qty_zscore']:.2f}x normal quantity for {row['Instrument']}")
        
        if row['price_dev_pct'] > 0.1:
            reasons.append(f"Price {row['price_dev_pct']*100:.1f}% away from average")
        
        if row['party_freq_1hr'] > 20:
            reasons.append(f"{row['Counterparty']} traded {row['party_freq_1hr']} times in 1hr")
        
        if not reasons:
            reasons.append("Multi-factor anomaly (risk score > threshold)")
        
        return "; ".join(reasons)
    
    def save_scored_trades_to_db(self, df):
        """Save scored results to trades_scored SQL table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trades_scored")
        
        df_scored = df.copy()
        df_scored['notional_value'] = df_scored['Quantity'] * df_scored['Price']
        
        db_export = pd.DataFrame({
            'trade_id': df_scored['TradeID'],
            'execution_time': df_scored['ExecutionTime'].astype(str),
            'quantity': df_scored['Quantity'],
            'price': df_scored['Price'],
            'counterparty': df_scored['Counterparty'],
            'instrument': df_scored['Instrument'],
            'trade_side': df_scored['TradeSide'],
            'notional_value': df_scored['notional_value'],
            'qty_zscore': df_scored['qty_zscore'],
            'price_volatility': df_scored['price_dev_pct'],
            'counterparty_frequency': df_scored['party_freq_1hr'],
            'anomaly_score': df_scored['anomaly_score'],
            'severity_level': df_scored['severity_level'],
            'anomaly_type': df_scored['anomaly_type'],
            'flagged_reason': df_scored['flagged_reason'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        db_export.to_sql('trades_scored', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        print(f"  [OK] Saved {len(db_export)} scored trades to table 'trades_scored' in {self.db_path}")

    def run(self, input_source='trades_raw.csv', output_prefix='trade_monitoring'):
        """Execute full pipeline."""
        print("=" * 80)
        print("TRADE ANOMALY DETECTION PIPELINE")
        print("=" * 80)
        
        # Step 0: Ensure DB initialized
        self.setup_database_schema(csv_path=input_source)
        
        # Step 1: Load
        print("\n[1/5] Loading trades...")
        try:
            df = self.load_trades_from_sql()
            print(f"  [OK] Loaded {len(df)} trades from database")
        except Exception as e:
            print(f"  ! SQL load failed ({e}), falling back to CSV")
            df = self.load_trades_from_csv(input_source)
            print(f"  [OK] Loaded {len(df)} trades from CSV")
        
        # Step 2: Engineer features
        print("\n[2/5] Engineering features...")
        df = self.engineer_ml_features(df)
        print(f"  [OK] Calculated Z-scores, volatility, concentration metrics")
        
        # Step 3: Detect anomalies
        print("\n[3/5] Detecting anomalies with Isolation Forest...")
        df = self.detect_anomalies(df)
        anomaly_count = df['is_anomaly'].sum()
        print(f"  [OK] Flagged {anomaly_count} anomalies ({anomaly_count/len(df)*100:.1f}% of trades)")
        
        # Step 4: Save to database & Generate outputs
        print("\n[4/5] Saving scored trades to database & generating outputs...")
        self.save_scored_trades_to_db(df)
        
        # All trades with scores
        all_trades_path = f'{output_prefix}_all_trades.csv'
        df.to_csv(all_trades_path, index=False)
        print(f"  [OK] Exported {all_trades_path}")
        
        # Flagged trades only
        flagged_df = df[df['is_anomaly']].sort_values('anomaly_score', ascending=False)
        flagged_path = f'{output_prefix}_flagged.csv'
        flagged_df.to_csv(flagged_path, index=False)
        print(f"  [OK] Exported {flagged_path}")
        
        # Summary KPIs
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': int(len(df)),
            'flagged_count': int(anomaly_count),
            'flagged_pct': f"{anomaly_count/len(df)*100:.2f}%",
            'high_severity': int(len(df[df['severity_level'] == 'HIGH'])),
            'medium_severity': int(len(df[df['severity_level'] == 'MEDIUM'])),
            'total_notional_risk': float((flagged_df['Quantity'] * flagged_df['Price']).sum())
        }
        
        summary_path = f'{output_prefix}_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"  [OK] Exported {summary_path}")
        
        # Step 5: Report
        print("\n[5/5] Summary Report")
        print(f"  Total Trades Processed: {summary['total_trades']}")
        print(f"  Flagged Anomalies: {summary['flagged_count']} ({summary['flagged_pct']})")
        print(f"    - HIGH Severity: {summary['high_severity']}")
        print(f"    - MEDIUM Severity: {summary['medium_severity']}")
        print(f"  Total Notional Risk (Anomalies): ${summary['total_notional_risk']:,.2f}")
        print("\n" + "=" * 80)
        
        return df, summary

if __name__ == '__main__':
    detector = TradeAnomalyDetector()
    df_scored, summary = detector.run(input_source='trades_raw.csv')
    print("\n[OK] Pipeline complete. Outputs ready for Antigravity orchestration and Tableau.")
