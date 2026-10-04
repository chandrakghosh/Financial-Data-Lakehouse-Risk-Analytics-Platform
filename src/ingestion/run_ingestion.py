from pathlib import Path

import yaml

from market_data import download_market_data
from economic_data import download_fred_series


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config():

    config_path = PROJECT_ROOT / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main():

    config = load_config()

    raw_path = (
        PROJECT_ROOT
        / config["data"]["raw_path"]
    )

    # -------------------------
    # Market data
    # -------------------------

    market_output = (
        raw_path / "market" / "market_prices.csv"
    )

    download_market_data(
        tickers=config["market"]["tickers"],
        start_date=config["market"]["start_date"],
        output_path=str(market_output),
    )

    # -------------------------
    # Economic data
    # -------------------------

    for series_id in config["economic"]["fred_series"]:

        output_file = (
            raw_path
            / "economic"
            / f"{series_id}.csv"
        )

        download_fred_series(
            series_id=series_id,
            start_date=config["economic"]["start_date"],
            output_path=str(output_file),
        )

    print("\nIngestion completed successfully.")


if __name__ == "__main__":
    main()