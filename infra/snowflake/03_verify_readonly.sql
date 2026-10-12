-- Prueba manual del rol de solo lectura. Las sentencias marcadas con ❌ DEBEN fallar.
USE ROLE MARKETPULSE_READER;
USE WAREHOUSE MARKETPULSE_WH;
SELECT COUNT(*) FROM MARKETPULSE.MARTS.FCT_DAILY_METRICS;       -- ✅ funciona
SELECT COUNT(*) FROM MARKETPULSE.RAW.PRICES_DAILY;               -- ❌ no autorizado
DELETE FROM MARKETPULSE.MARTS.DIM_TICKER;                        -- ❌ no autorizado
CREATE TABLE MARKETPULSE.MARTS.HACK AS SELECT 1 AS X;            -- ❌ no autorizado
