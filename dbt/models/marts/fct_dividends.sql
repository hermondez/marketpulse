-- Incremental simple (append+merge) de dividendos.
{{
  config(materialized='incremental', unique_key=['ticker', 'ex_date'], incremental_strategy='merge')
}}
select ticker, ex_date, dividend_per_share, source
from {{ ref('stg_dividends') }}
where {{ incremental_lookback_filter('ex_date', 60) }}
