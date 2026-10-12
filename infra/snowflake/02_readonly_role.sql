-- =====================================================================
-- Rol de SOLO LECTURA para "Pregunta a tus datos" (Módulo 4).
-- Principio de mínimo privilegio: aunque el validador sqlglot fallara,
-- este rol no puede escribir ni ver RAW/OPS/STAGING.
-- =====================================================================
USE ROLE SECURITYADMIN;

GRANT USAGE ON SCHEMA MARKETPULSE.MARTS TO ROLE MARKETPULSE_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA MARKETPULSE.MARTS TO ROLE MARKETPULSE_READER;
GRANT SELECT ON ALL VIEWS IN SCHEMA MARKETPULSE.MARTS TO ROLE MARKETPULSE_READER;
GRANT SELECT ON FUTURE TABLES IN SCHEMA MARKETPULSE.MARTS TO ROLE MARKETPULSE_READER;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA MARKETPULSE.MARTS TO ROLE MARKETPULSE_READER;
-- Excepción acotada para la página "Salud del pipeline" del dashboard: solo las dos
-- tablas de corridas dbt (no ALERTS_LOG). "Pregunta a tus datos" igual NO puede
-- consultarlas: sql_guard solo permite tablas de MARTS.
GRANT USAGE ON SCHEMA MARKETPULSE.OPS TO ROLE MARKETPULSE_READER;
GRANT SELECT ON TABLE MARKETPULSE.OPS.DBT_RUNS TO ROLE MARKETPULSE_READER;
GRANT SELECT ON TABLE MARKETPULSE.OPS.DBT_NODE_RESULTS TO ROLE MARKETPULSE_READER;
-- Nada de RAW, STAGING, INTERMEDIATE, esquemas DEV_/CI_. Nada de INSERT/UPDATE/CREATE.

-- Opcional: permitir Snowflake Cortex (LLM dentro de Snowflake).
-- GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE MARKETPULSE_READER;

-- Usuario dedicado para el dashboard (Streamlit Cloud). NUNCA uses un usuario admin ahí.
-- TYPE = LEGACY_SERVICE permite contraseña en usuarios de servicio (mejor: key-pair).
CREATE USER IF NOT EXISTS MARKETPULSE_ASK PASSWORD = 'CAMBIAR_ESTO' TYPE = LEGACY_SERVICE
  DEFAULT_ROLE = MARKETPULSE_READER DEFAULT_WAREHOUSE = MARKETPULSE_WH
  DEFAULT_SECONDARY_ROLES = ();
GRANT ROLE MARKETPULSE_READER TO USER MARKETPULSE_ASK;

-- Límites de costo/tiempo: ninguna consulta de este usuario dura más de 30 s.
ALTER USER MARKETPULSE_ASK SET STATEMENT_TIMEOUT_IN_SECONDS = 30;

-- Monitor de recursos opcional para acotar el gasto mensual del warehouse.
-- USE ROLE ACCOUNTADMIN;
-- CREATE RESOURCE MONITOR MARKETPULSE_RM WITH CREDIT_QUOTA = 5
--   TRIGGERS ON 80 PERCENT DO NOTIFY ON 100 PERCENT DO SUSPEND;
-- ALTER WAREHOUSE MARKETPULSE_WH SET RESOURCE_MONITOR = MARKETPULSE_RM;
