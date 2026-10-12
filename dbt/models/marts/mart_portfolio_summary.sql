-- Foto actual del portafolio simulado: valor, peso, rendimiento por posición.
with last_day as (
    select * from {{ ref('fct_portfolio_daily') }}
    qualify trade_date = max(trade_date) over ()
)

select
    portfolio_id,
    ticker,
    trade_date,
    shares,
    close,
    market_value,
    cost_basis,
    unrealized_pnl,
    cumulative_dividends,
    {{ safe_divide('unrealized_pnl + cumulative_dividends', 'cost_basis') }} as total_return_pct,
    {{ safe_divide('market_value', 'sum(market_value) over (partition by portfolio_id)') }} as weight
from last_day
