select
    m.ticker,
    m.name,
    m.asset_type,
    m.category,
    min(p.trade_date) as first_trade_date,
    max(p.trade_date) as last_trade_date
from {{ ref('seed_ticker_metadata') }} m
left join {{ ref('stg_prices_daily') }} p on p.ticker = m.ticker
group by 1, 2, 3, 4
