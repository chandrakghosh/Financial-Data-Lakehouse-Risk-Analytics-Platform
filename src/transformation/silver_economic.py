from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_PATH = PROJECT_ROOT / "data" / "bronze"
SILVER_PATH = PROJECT_ROOT / "data" / "silver"


FRED_SERIES = [
    "DFF",
    "DGS10",
    "VIXCLS",
    "CPIAUCSL",
    "UNRATE",
]


def process_economic_data():

    frames = []

    for series_id in FRED_SERIES:

        bronze_file = (
            BRONZE_PATH
            / "economic"
            / f"{series_id}.parquet"
        )

        if not bronze_file.exists():

            raise FileNotFoundError(
                f"Missing Bronze file: "
                f"{bronze_file}"
            )

        df = pd.read_parquet(
            bronze_file
        )

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce",
        ).dt.normalize()

        df["series_id"] = (
            df["series_id"]
            .astype("string")
            .str.upper()
            .str.strip()
        )

        df["value"] = pd.to_numeric(
            df["value"],
            errors="coerce",
        )

        frames.append(df)

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    # -----------------------------------------------------
    # Date validation
    # -----------------------------------------------------

    combined["invalid_date_flag"] = (
        combined["date"].isna()
    )

    # -----------------------------------------------------
    # Missing observation handling
    # -----------------------------------------------------

    combined["missing_value_flag"] = (
        combined["value"].isna()
    )

    # -----------------------------------------------------
    # Duplicate detection
    # -----------------------------------------------------

    combined["duplicate_flag"] = (
        combined.duplicated(
            subset=["date", "series_id"],
            keep=False,
        )
    )

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    combined = combined.sort_values(
        ["series_id", "date"]
    ).reset_index(drop=True)

    # -----------------------------------------------------
    # Remove unusable records
    # -----------------------------------------------------

    clean_df = combined[
        ~combined["invalid_date_flag"]
    ].copy()

    clean_df = clean_df.drop_duplicates(
        subset=["date", "series_id"],
        keep="last",
    )

    # -----------------------------------------------------
    # Add change metrics
    # -----------------------------------------------------

    clean_df["absolute_change"] = (
        clean_df.groupby("series_id")["value"]
        .diff()
    )

    clean_df["percentage_change"] = (
        clean_df.groupby("series_id")["value"]
        .pct_change()
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    output_file = (
        SILVER_PATH
        / "economic"
        / "economic_indicators.parquet"
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    clean_df.to_parquet(
        output_file,
        index=False,
    )

    print(
        f"Economic Silver dataset created: "
        f"{output_file}"
    )

    print(
        f"Rows: {len(clean_df):,}"
    )

    return clean_df


if __name__ == "__main__":
    process_economic_data()