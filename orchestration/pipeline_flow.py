import subprocess
from prefect import flow, task
from ingestion.fetch_prices import fetch_and_load, TICKERS


@task(name="ingest-prices", retries=2, retry_delay_seconds=60)
def ingest_prices():
    fetch_and_load(TICKERS)


@task(name="run-dbt-models", retries=1)
def run_dbt():
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", ".", "--project-dir", "."],
        cwd="dbt_project",
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"dbt run failed:\n{result.stderr}")


@task(name="run-dbt-tests")
def test_dbt():
    result = subprocess.run(
        ["dbt", "test", "--profiles-dir", ".", "--project-dir", "."],
        cwd="dbt_project",
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"dbt test failed:\n{result.stderr}")


@flow(name="market-data-pipeline", log_prints=True)
def market_pipeline():
    ingest_prices()
    run_dbt()
    test_dbt()


if __name__ == "__main__":
    market_pipeline()
