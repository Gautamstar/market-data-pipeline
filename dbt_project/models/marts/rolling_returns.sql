with base as (
    select * from {{ ref('stg_prices') }}
),

with_lags as (
    select
        ticker,
        date,
        close,
        lag(close, 1)   over (partition by ticker order by date) as prev_1d,
        lag(close, 5)   over (partition by ticker order by date) as prev_5d,
        lag(close, 21)  over (partition by ticker order by date) as prev_21d,
        lag(close, 63)  over (partition by ticker order by date) as prev_63d,
        lag(close, 126) over (partition by ticker order by date) as prev_126d,
        lag(close, 252) over (partition by ticker order by date) as prev_252d
    from base
),

with_returns as (
    select
        ticker,
        date,
        close,
        (close - prev_1d)   / nullif(prev_1d,   0) as return_1d,
        (close - prev_5d)   / nullif(prev_5d,   0) as return_1w,
        (close - prev_21d)  / nullif(prev_21d,  0) as return_1m,
        (close - prev_63d)  / nullif(prev_63d,  0) as return_3m,
        (close - prev_126d) / nullif(prev_126d, 0) as return_6m,
        (close - prev_252d) / nullif(prev_252d, 0) as return_1y
    from with_lags
)

select
    ticker,
    date,
    close,
    return_1d,
    return_1w,
    return_1m,
    return_3m,
    return_6m,
    return_1y,
    stddev(return_1d) over (
        partition by ticker order by date
        rows between 21 preceding and current row
    ) * sqrt(252) as vol_21d_annualized
from with_returns
