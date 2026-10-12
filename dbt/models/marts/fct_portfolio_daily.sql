{#
  Valor diario del portafolio SIMULADO. Supuestos (documentados en docs/metrics.md):
  - posiciones fijas desde purchase_date, sin comisiones ni impuestos;
  - market_value con precio de cierre NO ajustado (lo que verías en un broker);
  - dividendos acumulados en efectivo (no reinvertidos).
#}
with h as (
    select * from {{ ref('seed_portfolio_holdings') }}
),

p as (
    select ticker, trade_date, close from {{ ref('stg_prices_daily') }}
),

divs as (
    select
        h.portfolio_id,
        d.ticker,
        d.ex_date,
        d.dividend_per_share * h.shares as dividend_cash
    from {{ ref('fct_dividends') }} d
    join h on h.ticker = d.ticker and d.ex_date > h.purchase_date
)

select
    h.portfolio_id,
    h.ticker,
    p.trade_date,
    h.shares,
    p.close,
    h.shares * p.close                       as market_value,
    h.shares * h.avg_cost                    as cost_basis,
    h.shares * (p.close - h.avg_cost)        as unrealized_pnl,
    coalesce(sum(dv.dividend_cash) over (partition by h.portfolio_id, h.ticker order by p.trade_date
                                          rows between unbounded preceding and current row), 0)
                                             as cumulative_dividends
from h
join p on p.ticker = h.ticker and p.trade_date >= h.purchase_date
left join divs dv on dv.portfolio_id = h.portfolio_id and dv.ticker = h.ticker and dv.ex_date = p.trade_date
