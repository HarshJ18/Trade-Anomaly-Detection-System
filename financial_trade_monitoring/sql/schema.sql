-- Schema for Financial Trade Monitoring System

DROP TABLE IF EXISTS trades_raw;
DROP TABLE IF EXISTS trades_features;
DROP TABLE IF EXISTS trades_analyzed;

CREATE TABLE trades_raw (
    TradeID TEXT PRIMARY KEY,
    ExecutionTime TEXT NOT NULL,
    Quantity REAL NOT NULL,
    Price REAL NOT NULL,
    Counterparty TEXT NOT NULL,
    Instrument TEXT NOT NULL,
    TradeSide TEXT NOT NULL,
    Trader TEXT NOT NULL,
    Desk TEXT NOT NULL,
    ExecutionVenue TEXT NOT NULL,
    InjectedAnomalyType TEXT
);

CREATE TABLE trades_features (
    TradeID TEXT PRIMARY KEY,
    ExecutionTime TEXT NOT NULL,
    Quantity REAL NOT NULL,
    Price REAL NOT NULL,
    Counterparty TEXT NOT NULL,
    Instrument TEXT NOT NULL,
    TradeSide TEXT NOT NULL,
    Trader TEXT NOT NULL,
    Desk TEXT NOT NULL,
    ExecutionVenue TEXT NOT NULL,
    InjectedAnomalyType TEXT,
    NotionalValue REAL,
    AvgInstrumentQty REAL,
    StdDevInstrumentQty REAL,
    QtyZScore REAL,
    AvgInstrumentPrice REAL,
    PriceDevPct REAL,
    CP_1H_TradeCount INTEGER,
    CP_1H_NotionalVolume REAL,
    TimeDiffSeconds REAL
);

CREATE TABLE trades_analyzed (
    TradeID TEXT PRIMARY KEY,
    ExecutionTime TEXT NOT NULL,
    Quantity REAL NOT NULL,
    Price REAL NOT NULL,
    Counterparty TEXT NOT NULL,
    Instrument TEXT NOT NULL,
    TradeSide TEXT NOT NULL,
    Trader TEXT NOT NULL,
    Desk TEXT NOT NULL,
    ExecutionVenue TEXT NOT NULL,
    InjectedAnomalyType TEXT,
    NotionalValue REAL,
    QtyZScore REAL,
    PriceDevPct REAL,
    CP_1H_TradeCount INTEGER,
    CP_1H_NotionalVolume REAL,
    TimeDiffSeconds REAL,
    IsolationForestScore REAL,
    IsAnomaly INTEGER,
    AnomalyRiskScore REAL,
    RiskTier TEXT,
    PrimaryAnomalyReason TEXT,
    IsSizeAnomaly INTEGER,
    IsPriceAnomaly INTEGER,
    IsConcentrationAnomaly INTEGER,
    IsSpeedAnomaly INTEGER,
    ProcessedTimestamp TEXT
);
