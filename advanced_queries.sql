-- ==============================================================================
-- AgriChain Solutions: Advanced SQL Query Showcase
-- 
-- This file compiles the enterprise-grade analytical queries used in the 
-- AgriChain Solutions Engine (Python/SQLite implementation).
-- Highlights: CTEs, Window Functions (RANK, AVG OVER), and complex aggregations.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. SOURCING RISK & YIELD VOLATILITY
-- Demonstrates manual standard deviation calculation in SQLite, Window Functions
-- ------------------------------------------------------------------------------
WITH yield_stats AS (
    SELECT
        Crop,
        ROUND((Yield_2122 + Yield_2223 + Yield_2324 + Yield_2425) / 4.0, 0) AS Avg_Yield,
        /* SQLite lacks STDDEV -> manual population std dev across 4 years */
        ROUND(
            SQRT(
                (  (Yield_2122 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)
                   * (Yield_2122 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)
                 + (Yield_2223 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)
                   * (Yield_2223 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)
                 + (Yield_2324 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)
                   * (Yield_2324 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)
                 + (Yield_2425 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)
                   * (Yield_2425 - (Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0)
                ) / 4.0
            ) / ((Yield_2122+Yield_2223+Yield_2324+Yield_2425)/4.0) * 100, 2
        ) AS CV_Pct
    FROM crop_major
    WHERE Yield_2122 IS NOT NULL
)
SELECT *,
    ROUND(MIN(100, CV_Pct * 10), 0) AS Sourcing_Risk_Score,
    CASE WHEN CV_Pct > 5  THEN 'High Sourcing Risk'
         WHEN CV_Pct > 2  THEN 'Moderate Sourcing Risk'
         ELSE                   'Low Sourcing Risk'
    END AS Sourcing_Risk_Category,
    RANK() OVER (ORDER BY CV_Pct DESC) AS Volatility_Rank
FROM yield_stats
ORDER BY CV_Pct DESC;

-- ------------------------------------------------------------------------------
-- 2. NET-MARGIN ARBITRAGE (MANDI MARKETS)
-- Demonstrates complex joined CTEs, simulated transport/spoilage, RANK OVER
-- ------------------------------------------------------------------------------
WITH ranked AS (
    SELECT
        mp.Commodity,
        mp.Market,
        mp.State,
        mp.Modal_Price,
        cs.avg_price AS National_Avg,
        ROUND(mp.Modal_Price - cs.avg_price, 0) AS Gross_Arbitrage_Rs,
        ROUND(cs.avg_price * 0.05, 0)           AS Transport_Cost_Rs,
        ROUND(mp.Modal_Price * 0.02, 0)         AS Spoilage_Cost_Rs,
        ROUND(
            (mp.Modal_Price - cs.avg_price) 
            - (cs.avg_price * 0.05) 
            - (mp.Modal_Price * 0.02), 0
        ) AS Net_Margin_Rs,
        RANK() OVER (
            PARTITION BY mp.Commodity
            ORDER BY (mp.Modal_Price - cs.avg_price - (cs.avg_price * 0.05) - (mp.Modal_Price * 0.02)) DESC
        ) AS Margin_Rank
    FROM mandi_prices mp
    JOIN commodity_stats cs ON mp.Commodity = cs.Commodity
)
SELECT *
FROM ranked
WHERE Margin_Rank = 1 AND Net_Margin_Rs > 0
ORDER BY Net_Margin_Rs DESC;

-- ------------------------------------------------------------------------------
-- 3. CAPEX INVESTMENT TARGETING (EXPORT GROWTH)
-- Demonstrates conditional categorical aggregation
-- ------------------------------------------------------------------------------
WITH categorised AS (
    SELECT
        HSCode, ShortName, Val_2223, Val_2324, Growth,
        CASE
            WHEN HSCode BETWEEN 1  AND 14 THEN 'Raw Agriculture'
            WHEN HSCode BETWEEN 15 AND 18 THEN 'Semi-Processed'
            WHEN HSCode BETWEEN 19 AND 24 THEN 'Processed Food'
            ELSE 'Other'
        END AS Category
    FROM exports
    WHERE HSCode BETWEEN 1 AND 24
)
SELECT
    ShortName AS Sector,
    Category,
    ROUND(Val_2324, 0) AS Export_Val_Cr,
    ROUND(Growth, 1)   AS YoY_Growth_pct,
    CASE
        WHEN Category = 'Processed Food' AND Growth > 5 THEN 'PRIORITY CAPEX'
        WHEN Category = 'Semi-Processed' AND Growth > 0 THEN 'MODERATE CAPEX'
        WHEN Category = 'Raw Agriculture' AND Growth > 0 THEN 'RAW BOTTLENECK - NEEDS PROCESSING'
        ELSE 'MAINTAIN / NO CAPEX'
    END AS Capex_Strategy
FROM categorised
WHERE Category IN ('Raw Agriculture', 'Semi-Processed', 'Processed Food')
ORDER BY Export_Val_Cr DESC;

-- ------------------------------------------------------------------------------
-- 4. YEAR-OVER-YEAR PRODUCTION GROWTH VS AREA EXPANSION (LEAD/LAG EQUIVALENT)
-- Demonstrates YoY window framing and dynamic classification
-- ------------------------------------------------------------------------------
SELECT
    Crop,
    Area_2122 AS Area_Base,
    Area_2425 AS Area_Current,
    Prod_2122 AS Prod_Base,
    Prod_2425 AS Prod_Current,
    ROUND((Area_2425 - Area_2122) / Area_2122 * 100, 1)  AS Area_Growth_Pct,
    ROUND((Prod_2425 - Prod_2122) / Prod_2122 * 100, 1)  AS Prod_Growth_Pct,
    CASE
        WHEN ((Prod_2425 - Prod_2122) / Prod_2122 * 100
              - (Area_2425 - Area_2122) / Area_2122 * 100) > 2
             THEN 'Yield-Driven Growth'
        WHEN ((Area_2425 - Area_2122) / Area_2122 * 100) > 2
             THEN 'Area-Driven Growth'
        ELSE 'Stagnant'
    END AS Growth_Driver
FROM crop_major
ORDER BY Prod_Growth_Pct DESC;
