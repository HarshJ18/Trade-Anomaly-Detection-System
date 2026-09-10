-- Feature Engineering Queries for Trade Anomaly Detection

INSERT INTO trades_features (
    TradeID,
    ExecutionTime,
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
    AvgInstrumentQty,
    StdDevInstrumentQty,
    QtyZScore,
    AvgInstrumentPrice,
    PriceDevPct,
    CP_1H_TradeCount,
    CP_1H_NotionalVolume,
    TimeDiffSeconds
)
WITH InstrumentStats AS (
    SELECT 
        Instrument,
        AVG(Quantity) AS AvgQty,
        -- Standard deviation calculation in SQLite: SQRT(AVG(x^2) - AVG(x)^2)
        SQRT(MAX(0.0001, AVG(Quantity * Quantity) - AVG(Quantity) * AVG(Quantity))) AS StdDevQty,
        AVG(Price) AS AvgPrice
    FROM trades_raw
    GROUP BY Instrument
),
TimeDeltas AS (
    SELECT 
        TradeID,
        ExecutionTime,
        JULIANDAY(ExecutionTime) * 86400.0 AS ExecSeconds,
        LAG(JULIANDAY(ExecutionTime) * 86400.0, 1) OVER (
            PARTITION BY Desk ORDER BY ExecutionTime, TradeID
        ) AS PrevExecSeconds
    FROM trades_raw
)
SELECT 
    r.TradeID,
    r.ExecutionTime,
    r.Quantity,
    r.Price,
    r.Counterparty,
    r.Instrument,
    r.TradeSide,
    r.Trader,
    r.Desk,
    r.ExecutionVenue,
    r.InjectedAnomalyType,
    
    -- Notional Value
    (r.Quantity * r.Price) AS NotionalValue,
    
    -- Instrument Baseline Metrics
    s.AvgQty AS AvgInstrumentQty,
    s.StdDevQty AS StdDevInstrumentQty,
    
    -- Quantity Z-Score
    ROUND((r.Quantity - s.AvgQty) / NULLIF(s.StdDevQty, 0), 4) AS QtyZScore,
    
    -- Price Deviation Percentage
    s.AvgPrice AS AvgInstrumentPrice,
    ROUND(((r.Price - s.AvgPrice) / NULLIF(s.AvgPrice, 0)) * 100.0, 4) AS PriceDevPct,
    
    -- Counterparty Rolling 1-Hour Window Metrics
    (
        SELECT COUNT(*) 
        FROM trades_raw sub
        WHERE sub.Counterparty = r.Counterparty
          AND JULIANDAY(sub.ExecutionTime) <= JULIANDAY(r.ExecutionTime)
          AND JULIANDAY(sub.ExecutionTime) >= JULIANDAY(r.ExecutionTime) - (1.0 / 24.0)
    ) AS CP_1H_TradeCount,
    
    (
        SELECT COALESCE(SUM(sub.Quantity * sub.Price), 0.0)
        FROM trades_raw sub
        WHERE sub.Counterparty = r.Counterparty
          AND JULIANDAY(sub.ExecutionTime) <= JULIANDAY(r.ExecutionTime)
          AND JULIANDAY(sub.ExecutionTime) >= JULIANDAY(r.ExecutionTime) - (1.0 / 24.0)
    ) AS CP_1H_NotionalVolume,
    
    -- Time interval between consecutive trades on the same desk (seconds)
    COALESCE(ROUND(td.ExecSeconds - td.PrevExecSeconds, 2), 999.0) AS TimeDiffSeconds

FROM trades_raw r
JOIN InstrumentStats s ON r.Instrument = s.Instrument
JOIN TimeDeltas td ON r.TradeID = td.TradeID;
