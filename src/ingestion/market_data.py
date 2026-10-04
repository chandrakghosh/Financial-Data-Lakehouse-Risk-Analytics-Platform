from pathlib import Path

import pandas as pd
import yfinance as yf


def download_market_data(
    tickers: list[str],
    start_date: str,
    output_path: str,
) -> pd.DataFrame:

    print(f"Downloading market data for: {', '.join(tickers)}")

    data = yf.download(
        tickers=tickers,
        start=start_date,
        interval="1d",
        auto_adjust=False,
        actions=True,
        group_by="ticker",
        progress=True,
        threads=True,
    )

    if data.empty:
        raise ValueError("No market data was returned.")

    records = []

    for ticker in tickers:

        if ticker not in data.columns.get_level_values(0):
            print(f"Warning: no data returned for {ticker}")
            continue

        ticker_data = data[ticker].copy()

        ticker_data = ticker_data.reset_index()

        ticker_data["Ticker"] = ticker

        records.append(ticker_data)

    if not records:
        raise ValueError("No ticker data could be processed.")

    result = pd.concat(records, ignore_index=True)

    result.columns = [
        str(column).lower().replace(" ", "_")
        for column in result.columns
    ]

    result["date"] = pd.to_datetime(result["date"]).dt.date

    result = result[
        [
            "date",
            "ticker",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume",
            "dividends",
            "stock_splits",
        ]
    ]

    result = result.sort_values(
        ["ticker", "date"]
    ).reset_index(drop=True)

    output_file = Path(output_path)
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        output_file,
        index=False,
    )

    print(
        f"Saved {len(result):,} market records "
        f"to {output_file}"
    )

    return result