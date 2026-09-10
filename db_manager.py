import sqlite3
import pandas as pd
import os

DB_NAME = 'trades_monitoring.db'

def initialize_database(csv_path='trades_raw.csv', db_path=DB_NAME):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input CSV file '{csv_path}' not found. Generate mock data first.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Read and apply schema
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()

    # Load raw trades CSV into database
    df_raw = pd.read_csv(csv_path)
    df_raw.to_sql('trades_raw', conn, if_exists='append', index=False)
    conn.commit()
    print(f"[OK] Loaded {len(df_raw)} records into 'trades_raw' table.")

    # Read and execute feature engineering SQL script
    with open('feature_engineering.sql', 'r') as f:
        fe_sql = f.read()
    cursor.executescript(fe_sql)
    conn.commit()

    # Verify features table count
    cursor.execute("SELECT COUNT(*) FROM trades_features")
    count = cursor.fetchone()[0]
    print(f"[OK] Feature engineering complete. Populated {count} records into 'trades_features' table.")

    conn.close()
    return db_path

if __name__ == '__main__':
    initialize_database()
