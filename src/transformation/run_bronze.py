from src.transformation.bronze import (
    process_market_data,
    process_fred_data,
)


FRED_SERIES = [
    "DFF",
    "DGS10",
    "VIXCLS",
    "CPIAUCSL",
    "UNRATE",
]


def main():

    print("=" * 60)
    print("BRONZE LAYER PROCESSING")
    print("=" * 60)

    print("\nProcessing market data...")

    process_market_data()

    print("\nProcessing economic data...")

    for series_id in FRED_SERIES:
        process_fred_data(series_id)

    print("\nBronze processing completed.")


if __name__ == "__main__":
    main()