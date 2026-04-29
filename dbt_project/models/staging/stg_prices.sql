with source as (
    select * from raw.prices
)

select
    ticker,
    date,
    open,
    high,
    low,
    close,
    volume,
    loaded_at
from source
