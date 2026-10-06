import pandas as pd

from src.transformation.silver import (
    process_market_data,
)


def test_ohlc_relationships():

    df = pd.DataFrame(
        {
            "open": [100],
            "high": [105],
            "low": [98],
            "close": [103],
        }
    )

    assert (
        df["high"].iloc[0]
        >= df["open"].iloc[0]
    )

    assert (
        df["high"].iloc[0]
        >= df["close"].iloc[0]
    )

    assert (
        df["low"].iloc[0]
        <= df["open"].iloc[0]
    )


def test_invalid_ohlc():

    df = pd.DataFrame(
        {
            "open": [100],
            "high": [95],
            "low": [98],
            "close": [103],
        }
    )

    invalid = (
        (df["high"] < df["open"])
        | (df["high"] < df["close"])
    )

    assert invalid.iloc[0]