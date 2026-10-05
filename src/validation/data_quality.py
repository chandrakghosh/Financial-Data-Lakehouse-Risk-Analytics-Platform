import pandas as pd


def check_empty(df: pd.DataFrame):

    return {
        "is_empty": df.empty,
        "record_count": len(df),
    }


def check_nulls(df: pd.DataFrame):

    counts = df.isna().sum()

    return {
        column: int(count)
        for column, count in counts.items()
        if count > 0
    }


def check_duplicates(
    df: pd.DataFrame,
    keys: list[str],
):

    duplicate_count = df.duplicated(
        subset=keys
    ).sum()

    return {
        "keys": keys,
        "duplicate_count": int(
            duplicate_count
        ),
    }


def check_negative_values(
    df: pd.DataFrame,
    columns: list[str],
):

    results = {}

    for column in columns:

        if column not in df.columns:
            continue

        count = (
            df[column] < 0
        ).sum()

        results[column] = int(count)

    return results


def generate_quality_report(
    df: pd.DataFrame,
    duplicate_keys: list[str] | None = None,
    numeric_columns: list[str] | None = None,
):

    report = {}

    report["row_count"] = len(df)
    report["column_count"] = len(df.columns)

    report["nulls"] = check_nulls(df)

    if duplicate_keys:

        report["duplicates"] = check_duplicates(
            df,
            duplicate_keys,
        )

    if numeric_columns:

        report["negative_values"] = (
            check_negative_values(
                df,
                numeric_columns,
            )
        )

    return report