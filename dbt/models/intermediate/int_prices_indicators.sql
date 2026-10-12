{#
  Indicadores de ventana ACOTADA (SMA, RSI, volatilidad, 52 semanas). Incremental:
  - lee `window_history_days` de historia para que las ventanas tengan datos suficientes,
  - pero solo hace MERGE de los últimos `incremental_lookback_days`.
  Las métricas de ventana NO acotada (retorno acumulado, drawdown) van en el mart.
#}
{{
  config(
    materialized='incremental',
    unique_key=['ticker', 'trade_date'],
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
  )
}}

with base as (
    select *
    from {{ ref('int_prices_returns') }}
    {% if is_incremental() %}
    where trade_date >= (select dateadd(day, -{{ var('window_history_days') }}, max(trade_date)) from {{ this }})
    {% endif %}
),

changes as (
    select
        *,
        greatest(adj_close - prev_adj_close, 0) as gain,
        greatest(prev_adj_close - adj_close, 0) as loss
    from base
),

indicators as (
    select
        ticker,
        trade_date,
        close,
        adj_close,
        prev_adj_close,
        volume,
        daily_return,
        log_return,
        {{ sma('adj_close', 50) }}  as sma_50,
        {{ sma('adj_close', 200) }} as sma_200,
        -- RSI 14 con medias SIMPLES (variante de Cutler). Wilder usa suavizado
        -- exponencial recursivo, difícil en SQL puro: ver docs/metrics.md.
        {{ sma('gain', 14) }} as avg_gain_14,
        {{ sma('loss', 14) }} as avg_loss_14,
        {{ annualized_volatility('daily_return', 20) }}  as volatility_20d,
        {{ annualized_volatility('daily_return', 252) }} as volatility_252d,
        -- 52 semanas ≈ 252 sesiones. Usamos máximos/mínimos intradía.
        max(high) over (partition by ticker order by trade_date rows between 251 preceding and current row) as high_52w,
        min(low)  over (partition by ticker order by trade_date rows between 251 preceding and current row) as low_52w,
        count(*)  over (partition by ticker order by trade_date rows between 251 preceding and current row) as n_obs_52w
    from changes
)

select
    *,
    case
        when avg_loss_14 = 0 and avg_gain_14 > 0 then 100
        when avg_loss_14 is null then null
        else 100 - 100 / (1 + {{ safe_divide('avg_gain_14', 'avg_loss_14') }})
    end as rsi_14,
    lag(sma_200) over (partition by ticker order by trade_date) as prev_sma_200,
    current_timestamp() as dbt_updated_at
from indicators
where {{ incremental_lookback_filter('trade_date') }}
