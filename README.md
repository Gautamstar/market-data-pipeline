# Market Data Pipeline

End-to-end data engineering project ingesting daily equity market data, transforming it with dbt, orchestrating with Prefect, and serving insights via a Streamlit dashboard.

## Architecture

```
yfinance API → Python ingestion → PostgreSQL (raw)
                                        ↓
                                   dbt models
                                        ↓
                              PostgreSQL (marts)
                                        ↓
                            Streamlit dashboard
                              (Prefect schedules daily)
```

## Features

- **Ingestion**: Pulls daily OHLCV data for S&P 500 stocks and sector ETFs via `yfinance`
- **Storage**: Raw and transformed data in PostgreSQL with upsert logic
- **Transformations** (dbt):
  - `stg_prices` — cleaned staging view
  - `technical_indicators` — SMA 20/50/200, Bollinger Bands, RSI 14
  - `rolling_returns` — 1d/1w/1m/3m/6m/1y returns + annualized volatility
- **Orchestration**: Prefect flow runs ingest → dbt run → dbt test daily
- **Dashboard**: Streamlit app with candlestick charts, technical indicators, and a momentum screener

## Setup

### 1. Install dependencies

```bash
cd market-data-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Postgres credentials
```

### 3. Initialize the database

```bash
psql -U postgres -c "CREATE DATABASE market_data;"
psql -U postgres -d market_data -f sql/init_schema.sql
```

### 4. Run first ingestion

```bash
python -m ingestion.fetch_prices
```

### 5. Run dbt models

```bash
cd dbt_project
dbt run --profiles-dir . --project-dir .
dbt test --profiles-dir . --project-dir .
```

### 6. Launch dashboard

```bash
streamlit run dashboard/app.py
```

### 7. Schedule with Prefect

```bash
python orchestration/pipeline_flow.py
```

## Project Structure

```
market-data-pipeline/
├── ingestion/          # yfinance data fetching + Postgres loader
├── dbt_project/        # dbt models (staging + marts)
├── orchestration/      # Prefect flow
├── dashboard/          # Streamlit app
├── sql/                # Schema initialization
├── requirements.txt
└── .env.example
```
