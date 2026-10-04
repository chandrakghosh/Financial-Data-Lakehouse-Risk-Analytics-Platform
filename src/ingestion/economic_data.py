import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()


FRED_API_URL = (
    "https://api.stlouisfed.org/fred/series/observations"
)


def download_fred_series(
    series_id: str,
    start_date: str,
    output_path: str,
) -> pd.DataFrame:

    api_key = os.getenv("FRED_API_KEY")

    if not api_key:
        raise ValueError(
            "FRED_API_KEY is missing from the .env file."
        )

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "sort_order": "asc",
    }

    response = requests.get(
        FRED_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    observations = payload.get("observations", [])

    if not observations:
        raise ValueError(
            f"No observations returned for {series_id}"
        )

    data = pd.DataFrame(observations)

    data = data[
        [
            "date",
            "value",
        ]
    ]

    data["date"] = pd.to_datetime(data["date"])

    data["value"] = pd.to_numeric(
        data["value"],
        errors="coerce",
    )

    data["series_id"] = series_id

    data = data[
        [
            "date",
            "series_id",
            "value",
        ]
    ]

    data = data.sort_values("date")

    output_file = Path(output_path)
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        output_file,
        index=False,
    )

    print(
        f"Saved {len(data):,} records "
        f"for {series_id} → {output_file}"
    )

    return data