import os
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

TICKERS = [
    # S&P 500 sector ETFs
    "SPY", "QQQ", "IWM",
    # Tech
    "AAPL", "MSFT", "GOOGL", "NVDA", "META",
    # Finance
    "JPM", "GS", "BAC", "V", "MA",
    # Energy
    "XOM", "CVX",
    # Healthcare
    "JNJ", "UNH",
]

def get_engine():
    url = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(url)


def fetch_and_load(tickers: list[str], period: str = "1y"):
    engine = get_engine()
    raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)

    # yfinance returns MultiIndex columns when multiple tickers requested
    records = []
    for ticker in tickers:
        try:
            df = raw.xs(ticker, axis=1, level=1).copy()
        except KeyError:
            print(f"No data for {ticker}, skipping")
            continue

        df = df.reset_index().rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })
        df["ticker"] = ticker
        df = df[["ticker", "date", "open", "high", "low", "close", "volume"]]
        df = df.dropna(subset=["close"])
        records.append(df)

    if not records:
        print("No data fetched.")
        return

    combined = pd.concat(records, ignore_index=True)

    with engine.begin() as conn:
        for _, row in combined.iterrows():
            conn.execute(
                text("""
                    INSERT INTO raw.prices (ticker, date, open, high, low, close, volume)
                    VALUES (:ticker, :date, :open, :high, :low, :close, :volume)
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        open   = EXCLUDED.open,
                        high   = EXCLUDED.high,
                        low    = EXCLUDED.low,
                        close  = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        loaded_at = NOW()
                """),
                row.to_dict(),
            )

    print(f"Loaded {len(combined)} rows for {len(records)} tickers.")


if __name__ == "__main__":
    fetch_and_load(TICKERS)
