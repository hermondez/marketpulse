-- Staging: tipado, nombres limpios y deduplicación defensiva. Sin lógica de negocio.
select
    upper(ticker)                 as ticker,
    trade_date::date              as trade_date,
    open::float                   as open,
    high::float                   as high,
    low::float                    as low,
    close::float                  as close,
    coalesce(adj_close, close)::float as adj_close,
    volume::number(38, 0)         as volume,
    source,
    ingested_at
from {{ source('raw', 'prices_daily') }}
where close > 0
qualify row_number() over (partition by upper(ticker), trade_date order by ingested_at desc) = 1
