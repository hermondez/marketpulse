-- Análisis (no se materializa): ver cuántos días el RSI simple está en zona extrema.
select ticker, count_if(rsi_14 >= 70) as dias_rsi_alto, count_if(rsi_14 <= 30) as dias_rsi_bajo
from {{ ref('fct_daily_metrics') }}
group by ticker
