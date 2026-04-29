with base as (
    select * from {{ ref('stg_prices') }}
),

with_moving_averages as (
    select
        *,
        avg(close) over (
            partition by ticker order by date
            rows between 19 preceding and current row
        ) as sma_20,
        avg(close) over (
            partition by ticker order by date
            rows between 49 preceding and current row
        ) as sma_50,
        avg(close) over (
            partition by ticker order by date
            rows between 199 preceding and current row
        ) as sma_200,
        stddev(close) over (
            partition by ticker order by date
            rows between 19 preceding and current row
        ) as stddev_20
    from base
),

with_bands as (
    select
        *,
        sma_20 + (2 * stddev_20) as bb_upper,
        sma_20 - (2 * stddev_20) as bb_lower,
        -- daily return
        (close - lag(close) over (partition by ticker order by date))
            / nullif(lag(close) over (partition by ticker order by date), 0) as daily_return
    from with_moving_averages
),

with_rsi as (
    select
        *,
        -- RSI gain/loss helpers
        case when daily_return > 0 then daily_return else 0 end as gain,
        case when daily_return < 0 then abs(daily_return) else 0 end as loss
    from with_bands
),

with_avg_gl as (
    select
        *,
        avg(gain) over (
            partition by ticker order by date
            rows between 13 preceding and current row
        ) as avg_gain_14,
        avg(loss) over (
            partition by ticker order by date
            rows between 13 preceding and current row
        ) as avg_loss_14
    from with_rsi
)

select
    ticker,
    date,
    open,
    high,
    low,
    close,
    volume,
    daily_return,
    sma_20,
    sma_50,
    sma_200,
    bb_upper,
    bb_lower,
    round(
        100 - (100 / nullif(1 + avg_gain_14 / nullif(avg_loss_14, 0), 0))
    , 2) as rsi_14
from with_avg_gl
