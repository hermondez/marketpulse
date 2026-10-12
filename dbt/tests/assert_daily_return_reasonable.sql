-- Test singular: un ETF amplio que se mueve >40 % en un día casi seguro es un error de datos
-- (split no ajustado, precio en otra moneda...). Severidad warn: avisa sin romper el build.
{{ config(severity='warn') }}
select ticker, trade_date, daily_return
from {{ ref('fct_daily_metrics') }}
where abs(daily_return) > 0.40
