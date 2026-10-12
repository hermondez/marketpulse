-- Test singular: cada posición simulada debe tener precios cargados (ticker en la watchlist).
select h.ticker
from {{ ref('seed_portfolio_holdings') }} h
left join {{ ref('dim_ticker') }} d on d.ticker = h.ticker
where d.ticker is null
