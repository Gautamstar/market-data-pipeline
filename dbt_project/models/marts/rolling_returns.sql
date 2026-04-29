with base as (
    select * from {{ ref('stg_prices') }}
)

select
    ticker,
    date,
    close,
    -- rolling returns
    (close - lag(close, 1)  over w) / nullif(lag(close, 1)  over w, 0) as return_1d,
    (close - lag(close, 5)  over w) / nullif(lag(close, 5)  over w, 0) as return_1w,
    (close - lag(close, 21) over w) / nullif(lag(close, 21) over w, 0) as return_1m,
    (close - lag(close, 63) over w) / nullif(lag(close, 63) over w, 0) as return_3m,
    (close - lag(close, 126) over w) / nullif(lag(close, 126) over w, 0) as return_6m,
    (close - lag(close, 252) over w) / nullif(lag(close, 252) over w, 0) as return_1y,
    -- rolling volatility (annualized)
    stddev(
        (close - lag(close, 1) over w) / nullif(lag(close, 1) over w, 0)
    ) over (
        partition by ticker order by date
        rows between 21 preceding and current row
    ) * sqrt(252) as vol_21d_annualized
from base
window w as (partition by ticker order by date)
