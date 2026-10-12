-- Test singular: el máximo del día nunca puede ser menor que el mínimo ni que el cierre.
select *
from {{ ref('stg_prices_daily') }}
where high < low or close > high * 1.0001 or close < low * 0.9999
