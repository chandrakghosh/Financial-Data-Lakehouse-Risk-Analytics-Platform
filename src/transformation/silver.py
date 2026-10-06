from pathlib import Path
import json

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_PATH = PROJECT_ROOT / "data" / "bronze"
SILVER_PATH = PROJECT_ROOT / "data" / "silver"


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def ensure_directory(path: Path):
    """Create directory if it does not exist."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def save_quality_report(
    report: dict,
    output_path: Path,
):
    """Save quality report as JSON."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            default=str,
        )


# ---------------------------------------------------------
# Market data
# ---------------------------------------------------------

def process_market_data():

    bronze_file = (
        BRONZE_PATH
        / "market"
        / "market_prices.parquet"
    )

    silver_file = (
        SILVER_PATH
        / "market"
        / "market_prices.parquet"
    )

    quality_file = (
        SILVER_PATH
        / "quality"
        / "market_quality_report.json"
    )

    if not bronze_file.exists():

        raise FileNotFoundError(
            f"Bronze market file not found: {bronze_file}"
        )

    df = pd.read_parquet(bronze_file)

    original_row_count = len(df)

    # -----------------------------------------------------
    # 1. Standardize column names
    # -----------------------------------------------------

    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    # -----------------------------------------------------
    # 2. Standardize date
    # -----------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    ).dt.normalize()

    # -----------------------------------------------------
    # 3. Standardize ticker
    # -----------------------------------------------------

    df["ticker"] = (
        df["ticker"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # -----------------------------------------------------
    # 4. Standardize numeric columns
    # -----------------------------------------------------

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
        "dividends",
        "stock_splits",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # -----------------------------------------------------
    # 5. Detect invalid dates
    # -----------------------------------------------------

    df["invalid_date_flag"] = (
        df["date"].isna()
    )

    # -----------------------------------------------------
    # 6. Detect duplicate date/ticker records
    # -----------------------------------------------------

    df["duplicate_flag"] = (
        df.duplicated(
            subset=["date", "ticker"],
            keep=False,
        )
    )

    duplicate_count = int(
        df["duplicate_flag"].sum()
    )

    # -----------------------------------------------------
    # 7. Detect missing essential values
    # -----------------------------------------------------

    essential_columns = [
        "date",
        "ticker",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
    ]

    df["missing_essential_data_flag"] = (
        df[essential_columns]
        .isna()
        .any(axis=1)
    )

    # -----------------------------------------------------
    # 8. Validate positive prices
    # -----------------------------------------------------

    price_columns = [
        "open",
        "high",
        "low",
        "close",
        "adj_close",
    ]

    df["invalid_price_flag"] = (
        df[price_columns] <= 0
    ).any(axis=1)

    # -----------------------------------------------------
    # 9. Validate OHLC relationships
    # -----------------------------------------------------

    df["invalid_ohlc_flag"] = (
        (df["high"] < df["open"])
        | (df["high"] < df["close"])
        | (df["high"] < df["low"])
        | (df["low"] > df["open"])
        | (df["low"] > df["close"])
        | (df["low"] > df["high"])
    )

    # -----------------------------------------------------
    # 10. Validate volume
    # -----------------------------------------------------

    df["invalid_volume_flag"] = (
        df["volume"] < 0
    )

    # -----------------------------------------------------
    # 11. Validate corporate-action fields
    # -----------------------------------------------------

    df["invalid_dividend_flag"] = (
        df["dividends"] < 0
    )

    df["invalid_split_flag"] = (
        df["stock_splits"] < 0
    )

    # -----------------------------------------------------
    # 12. Overall quality flag
    # -----------------------------------------------------

    quality_flags = [
        "invalid_date_flag",
        "duplicate_flag",
        "missing_essential_data_flag",
        "invalid_price_flag",
        "invalid_ohlc_flag",
        "invalid_volume_flag",
        "invalid_dividend_flag",
        "invalid_split_flag",
    ]

    df["quality_issue_flag"] = (
        df[quality_flags]
        .any(axis=1)
    )

    # -----------------------------------------------------
    # 13. Quality status
    # -----------------------------------------------------

    df["quality_status"] = np.where(
        df["quality_issue_flag"],
        "REVIEW",
        "VALID",
    )

    # -----------------------------------------------------
    # 14. Sort data
    # -----------------------------------------------------

    df = df.sort_values(
        ["ticker", "date"]
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # 15. Market calendar gap detection
    # -----------------------------------------------------

    df["previous_date"] = (
        df.groupby("ticker")["date"]
        .shift(1)
    )

    df["calendar_gap_days"] = (
        df["date"] - df["previous_date"]
    ).dt.days

    # A gap larger than 3 calendar days is flagged.
    # This captures weekends + holidays without
    # treating normal weekends as missing data.

    df["unusual_calendar_gap_flag"] = (
        df["calendar_gap_days"] > 3
    )

    # -----------------------------------------------------
    # 16. Calculate returns
    # -----------------------------------------------------

    df["daily_return"] = (
        df.groupby("ticker")["adj_close"]
        .pct_change()
    )

    # Log return is useful for statistical analysis.

    df["log_return"] = (
        np.log(
            df["adj_close"]
            / df.groupby("ticker")["adj_close"].shift(1)
        )
    )

    # -----------------------------------------------------
    # 17. Remove unusable records
    # -----------------------------------------------------

    invalid_for_analysis = (
        df["invalid_date_flag"]
        | df["missing_essential_data_flag"]
        | df["invalid_price_flag"]
        | df["invalid_ohlc_flag"]
        | df["invalid_volume_flag"]
    )

    clean_df = df[
        ~invalid_for_analysis
    ].copy()

    # Remove duplicate records after flagging them.
    # Keep the last occurrence deterministically.

    clean_df = clean_df.drop_duplicates(
        subset=["date", "ticker"],
        keep="last",
    )

    # -----------------------------------------------------
    # 18. Drop helper column
    # -----------------------------------------------------

    clean_df = clean_df.drop(
        columns=[
            "previous_date",
        ],
        errors="ignore",
    )

    # -----------------------------------------------------
    # 19. Save Silver dataset
    # -----------------------------------------------------

    ensure_directory(silver_file)

    clean_df.to_parquet(
        silver_file,
        index=False,
    )

    # -----------------------------------------------------
    # 20. Build quality report
    # -----------------------------------------------------

    report = {
        "dataset": "market_prices",
        "source_layer": "bronze",
        "target_layer": "silver",
        "original_row_count": original_row_count,
        "silver_row_count": len(clean_df),
        "rows_removed": (
            original_row_count
            - len(clean_df)
        ),
        "duplicate_rows_flagged": duplicate_count,
        "invalid_date_count": int(
            df["invalid_date_flag"].sum()
        ),
        "missing_essential_data_count": int(
            df["missing_essential_data_flag"].sum()
        ),
        "invalid_price_count": int(
            df["invalid_price_flag"].sum()
        ),
        "invalid_ohlc_count": int(
            df["invalid_ohlc_flag"].sum()
        ),
        "invalid_volume_count": int(
            df["invalid_volume_flag"].sum()
        ),
        "unusual_calendar_gap_count": int(
            df["unusual_calendar_gap_flag"].sum()
        ),
        "silver_file": str(
            silver_file
        ),
    }

    save_quality_report(
        report,
        quality_file,
    )

    print(
        f"Market Silver dataset created: "
        f"{silver_file}"
    )

    print(
        f"Rows: {original_row_count:,} → "
        f"{len(clean_df):,}"
    )

    return clean_df