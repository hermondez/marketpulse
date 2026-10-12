{#
  Tabla de hechos principal: una fila por ticker y día con todas las métricas.
  Se reconstruye completa (table): son pocos miles de filas y las métricas de
  ventana NO acotada (retorno acumulado, máximo histórico, drawdown) necesitan
  toda la historia. Si creciera mucho, ver alternativas en docs/dbt_modeling.md.
#}
with ind as (
    select * from {{ ref('int_prices_indicators') }}
),

running as (
    select
        *,
        first_value(adj_close) over (partition by ticker order by trade_date) as first_adj_close,
        max(adj_close) over (partition by ticker order by trade_date
                             rows between unbounded preceding and current row) as running_max
    from ind
),

dd as (
    select
        *,
        {{ safe_divide('adj_close', 'first_adj_close') }} - 1 as cumulative_return,
        {{ safe_divide('adj_close', 'running_max') }} - 1     as drawdown
    from running
)

select
    ticker,
    trade_date,
    close,
    adj_close,
    prev_adj_close,
    volume,
    daily_return,
    cumulative_return,
    sma_50,
    sma_200,
    prev_sma_200,
    rsi_14,
    volatility_20d,
    volatility_252d,
    drawdown,
    min(drawdown) over (partition by ticker order by trade_date
                        rows between unbounded preceding and current row) as max_drawdown,
    high_52w,
    low_52w,
    {{ safe_divide('close', 'high_52w') }} - 1 as pct_from_52w_high,
    {{ safe_divide('close', 'low_52w') }} - 1  as pct_from_52w_low,
    n_obs_52w >= 252 as has_full_52w
from dd
