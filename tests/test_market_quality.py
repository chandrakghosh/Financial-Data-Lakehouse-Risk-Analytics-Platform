import pandas as pd

from src.validation.data_quality import (
    check_duplicates,
    check_nulls,
)


def test_duplicate_detection():

    df = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-01",
            ],
            "ticker": [
                "AAPL",
                "AAPL",
            ],
        }
    )

    result = check_duplicates(
        df,
        ["date", "ticker"],
    )

    assert result["duplicate_count"] == 1


def test_null_detection():

    df = pd.DataFrame(
        {
            "price": [
                100,
                None,
                105,
            ]
        }
    )

    result = check_nulls(df)

    assert result["price"] == 1