import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_trades(n_trades=1000, output_file='trades_raw.csv'):
    # Set seed for reproducibility
    np.random.seed(42)

    # Parameters
    instruments = ['AAPL', 'MSFT', 'GOOGL', 'EURUSD', 'GBPUSD', 'JPYUSD']
    counterparties = ['JPMorgan Chase', 'Goldman Sachs', 'Citigroup', 'UBS', 'Bank of America', 'Morgan Stanley']
    traders = ['John Smith', 'Jane Doe', 'Alice Johnson', 'Bob Wilson']
    venues = ['NYSE', 'NASDAQ', 'CBOE', 'CME']

    spot_prices = {
        'AAPL': 150.0,
        'MSFT': 420.0,
        'GOOGL': 180.0,
        'EURUSD': 1.1000,
        'GBPUSD': 1.2700,
        'JPYUSD': 0.0067
    }

    trades = []
    current_time = datetime(2026, 7, 22, 9, 30, 0)

    for i in range(n_trades):
        trade_id = f"T{i+1:04d}"
        
        # Pick instrument
        instrument = np.random.choice(instruments)
        spot_price = spot_prices[instrument]
        desk = 'Equities' if instrument in ['AAPL', 'MSFT', 'GOOGL'] else 'FX'
        trader = np.random.choice(traders)

        # Baseline parameters
        if desk == 'Equities':
            normal_qty = float(np.clip(np.random.normal(250, 75), 50, 500))
            normal_price = float(spot_price * np.random.normal(1.0, 0.008))
        else:  # FX
            normal_qty = float(np.clip(np.random.normal(2.5e6, 7.5e5), 1e6, 5e6))
            normal_price = float(spot_price * np.random.normal(1.0, 0.003))

        # Determine anomaly status (10% anomalies overall)
        is_anomaly = np.random.rand() < 0.10
        anomaly_type = 'None'

        if is_anomaly:
            # Anomaly distribution: size (5%), price (2%), concentration (2%), speed (1%) -> normalized probabilities
            anomaly_type = np.random.choice(
                ['size', 'price', 'concentration', 'speed'],
                p=[0.50, 0.20, 0.20, 0.10]
            )

            if anomaly_type == 'size':
                quantity = normal_qty * np.random.uniform(5.0, 10.0)
                price = normal_price
                counterparty = np.random.choice(counterparties)
                current_time += timedelta(seconds=int(np.random.randint(30, 120)))

            elif anomaly_type == 'price':
                quantity = normal_qty
                # Price 10-15% away from spot
                price_shift = np.random.uniform(0.10, 0.15)
                direction = -1.0 if np.random.rand() > 0.5 else 1.0
                price = spot_price * (1.0 + direction * price_shift)
                counterparty = np.random.choice(counterparties)
                current_time += timedelta(seconds=int(np.random.randint(30, 120)))

            elif anomaly_type == 'concentration':
                quantity = normal_qty
                price = normal_price
                counterparty = 'JPMorgan Chase'  # Force high concentration counterparty
                current_time += timedelta(seconds=int(np.random.randint(15, 45)))

            elif anomaly_type == 'speed':
                quantity = normal_qty
                price = normal_price
                counterparty = np.random.choice(counterparties)
                # Rapid execution 2-3 seconds apart
                current_time += timedelta(seconds=int(np.random.randint(1, 4)))

        else:
            quantity = normal_qty
            price = normal_price
            counterparty = np.random.choice(counterparties)
            current_time += timedelta(seconds=int(np.random.randint(30, 120)))

        trades.append({
            'TradeID': trade_id,
            'ExecutionTime': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Quantity': round(quantity, 2),
            'Price': round(price, 4),
            'Counterparty': counterparty,
            'Instrument': instrument,
            'TradeSide': np.random.choice(['BUY', 'SELL']),
            'Trader': trader,
            'Desk': desk,
            'ExecutionVenue': np.random.choice(venues),
            'InjectedAnomalyType': anomaly_type
        })

    df_trades = pd.DataFrame(trades)
    df_trades.to_csv(output_file, index=False)
    
    anomalies_count = len(df_trades[df_trades['InjectedAnomalyType'] != 'None'])
    print(f"[OK] Generated {len(df_trades)} trades in {output_file}")
    print(f"  - Normal trades: {len(df_trades) - anomalies_count}")
    print(f"  - Injected Anomalies: {anomalies_count}")
    print(df_trades['InjectedAnomalyType'].value_counts())
    return df_trades

if __name__ == '__main__':
    generate_mock_trades()
