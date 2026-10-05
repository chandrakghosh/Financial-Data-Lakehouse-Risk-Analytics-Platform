from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PATH = PROJECT_ROOT / "data" / "raw"
BRONZE_PATH = PROJECT_ROOT / "data" / "bronze"


def get_ingestion_timestamp():
    """Return current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def calculate_file_metadata(file_path: Path):
    """Collect basic source-file metadata."""

    stat = file_path.stat()

    return {
        "source_file": file_path.name,
        "source_path": str(file_path),
        "file_size_bytes": stat.st_size,
        "file_modified_timestamp": datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
    }


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: set[str],
):
    """Check whether required columns exist."""

    missing_columns = required_columns - set(df.columns)

    return sorted(missing_columns)


def check_duplicates(
    df: pd.DataFrame,
    subset: list[str],
):
    """Count duplicate records."""

    return int(
        df.duplicated(subset=subset).sum()
    )


def check_nulls(df: pd.DataFrame):
    """Return null counts for every column."""

    null_counts = df.isna().sum()

    return {
        column: int(count)
        for column, count in null_counts.items()
        if count > 0
    }


def write_metadata(
    metadata: dict,
    output_path: Path,
):
    """Write ingestion metadata as JSON."""

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
            metadata,
            file,
            indent=4,
        )


def process_market_data():
    """Process raw Yahoo Finance data into Bronze."""

    source_file = (
        RAW_PATH
        / "market"
        / "market_prices.csv"
    )

    bronze_file = (
        BRONZE_PATH
        / "market"
        / "market_prices.parquet"
    )

    metadata_file = (
        BRONZE_PATH
        / "metadata"
        / "market_prices_metadata.json"
    )

    if not source_file.exists():
        raise FileNotFoundError(
            f"Raw market file not found: {source_file}"
        )

    ingestion_timestamp = get_ingestion_timestamp()

    df = pd.read_csv(source_file)

    required_columns = {
        "date",
        "ticker",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
    }

    missing_columns = validate_required_columns(
        df,
        required_columns,
    )

    if missing_columns:
        raise ValueError(
            f"Market dataset is missing required columns: "
            f"{missing_columns}"
        )

    duplicate_count = check_duplicates(
        df,
        ["date", "ticker"],
    )

    null_counts = check_nulls(df)

    # Standardize date
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    # Standardize numeric columns
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

    # Standardize ticker
    df["ticker"] = (
        df["ticker"]
        .astype("string")
        .str.upper()
        .str.strip()
    )

    # Add ingestion metadata
    df["ingestion_timestamp"] = ingestion_timestamp
    df["source_system"] = "Yahoo Finance"

    # Create Bronze directory
    bronze_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Write Bronze Parquet
    df.to_parquet(
        bronze_file,
        index=False,
    )

    metadata = {
        "dataset": "market_prices",
        "layer": "bronze",
        "source_system": "Yahoo Finance",
        "ingestion_timestamp": ingestion_timestamp,
        "record_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "missing_required_columns": missing_columns,
        "duplicate_records": duplicate_count,
        "null_counts": null_counts,
        "source_metadata": calculate_file_metadata(
            source_file
        ),
        "bronze_file": str(bronze_file),
    }

    write_metadata(
        metadata,
        metadata_file,
    )

    print(
        f"Bronze market dataset created: "
        f"{bronze_file}"
    )


def process_fred_data(series_id: str):
    """Process a raw FRED dataset into Bronze."""

    source_file = (
        RAW_PATH
        / "economic"
        / f"{series_id}.csv"
    )

    bronze_file = (
        BRONZE_PATH
        / "economic"
        / f"{series_id}.parquet"
    )

    metadata_file = (
        BRONZE_PATH
        / "metadata"
        / f"{series_id}_metadata.json"
    )

    if not source_file.exists():
        raise FileNotFoundError(
            f"FRED file not found: {source_file}"
        )

    ingestion_timestamp = get_ingestion_timestamp()

    df = pd.read_csv(source_file)

    required_columns = {
        "date",
        "series_id",
        "value",
    }

    missing_columns = validate_required_columns(
        df,
        required_columns,
    )

    if missing_columns:
        raise ValueError(
            f"FRED dataset {series_id} is missing "
            f"required columns: {missing_columns}"
        )

    # Standardize date
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    # Standardize value
    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    # Standardize series ID
    df["series_id"] = (
        df["series_id"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    duplicate_count = check_duplicates(
        df,
        ["date", "series_id"],
    )

    null_counts = check_nulls(df)

    # Add ingestion metadata
    df["ingestion_timestamp"] = ingestion_timestamp
    df["source_system"] = "FRED"

    # Create Bronze directory
    bronze_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Write Bronze Parquet
    df.to_parquet(
        bronze_file,
        index=False,
    )

    metadata = {
        "dataset": series_id,
        "layer": "bronze",
        "source_system": "FRED",
        "ingestion_timestamp": ingestion_timestamp,
        "record_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "missing_required_columns": missing_columns,
        "duplicate_records": duplicate_count,
        "null_counts": null_counts,
        "source_metadata": calculate_file_metadata(
            source_file
        ),
        "bronze_file": str(bronze_file),
    }

    write_metadata(
        metadata,
        metadata_file,
    )

    print(
        f"Bronze FRED dataset created: "
        f"{bronze_file}"
    )