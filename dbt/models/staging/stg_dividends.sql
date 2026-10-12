select
    upper(ticker)        as ticker,
    ex_date::date        as ex_date,
    amount::float        as dividend_per_share,
    source,
    ingested_at
from {{ source('raw', 'dividends') }}
where amount > 0
qualify row_number() over (partition by upper(ticker), ex_date order by ingested_at desc) = 1
