import pandas as pd


def check_market_data(df: pd.DataFrame):

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

    missing_columns = (
        required_columns - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError(
            "Market dataset is empty."
        )

    duplicate_count = df.duplicated(
        subset=["date", "ticker"]
    ).sum()

    print(
        f"Duplicate date/ticker records: "
        f"{duplicate_count:,}"
    )

    invalid_prices = (
        (df["open"] <= 0)
        | (df["high"] <= 0)
        | (df["low"] <= 0)
        | (df["close"] <= 0)
    ).sum()

    print(
        f"Invalid price records: "
        f"{invalid_prices:,}"
    )

    print(
        f"Null values:\n"
        f"{df.isna().sum()}"
    )