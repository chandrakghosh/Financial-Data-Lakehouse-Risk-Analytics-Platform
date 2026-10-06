from src.transformation.silver import (
    process_market_data,
)

from src.transformation.silver_economic import (
    process_economic_data,
)


def main():

    print("=" * 60)
    print("SILVER LAYER PROCESSING")
    print("=" * 60)

    print("\nProcessing market data...")

    process_market_data()

    print("\nProcessing economic data...")

    process_economic_data()

    print("\nSilver processing completed.")


if __name__ == "__main__":
    main()