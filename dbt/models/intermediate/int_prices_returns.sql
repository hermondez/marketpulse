-- Retornos diarios sobre precio AJUSTADO (incluye dividendos y splits).
-- Retorno simple: P_t / P_{t-1} - 1. También el retorno logarítmico (sumable en el tiempo).
select
    ticker,
    trade_date,
    close,
    adj_close,
    high,
    low,
    volume,
    lag(adj_close) over (partition by ticker order by trade_date) as prev_adj_close,
    lag(close) over (partition by ticker order by trade_date) as prev_close,
    {{ safe_divide('adj_close', 'lag(adj_close) over (partition by ticker order by trade_date)') }} - 1
        as daily_return,
    ln({{ safe_divide('adj_close', 'lag(adj_close) over (partition by ticker order by trade_date)') }})
        as log_return
from {{ ref('stg_prices_daily') }}
