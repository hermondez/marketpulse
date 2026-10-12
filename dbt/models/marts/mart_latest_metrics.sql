-- Última fila por ticker: alimenta alertas de Telegram y la portada del dashboard.
select
    f.*,
    d.name,
    d.asset_type
from {{ ref('fct_daily_metrics') }} f
join {{ ref('dim_ticker') }} d using (ticker)
where f.trade_date = (select max(trade_date) from {{ ref('fct_daily_metrics') }})
