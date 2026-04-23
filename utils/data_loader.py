import pandas as pd

REQUIRED_COLUMNS = {"timestamp", "orders", "revenue", "channel"}


def load_data(path: str) -> pd.DataFrame:
    # Read CSV file.
    df = pd.read_csv(path)

    # Make sure all expected columns are present.
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Parse timestamp text into datetime values.
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        raise ValueError("Some timestamps could not be parsed. Check your timestamp column.")

    # Parse numeric columns.
    df["orders"] = pd.to_numeric(df["orders"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")

    if df[["orders", "revenue"]].isna().any().any():
        raise ValueError("Some values in orders or revenue are not valid numbers.")

    return df
