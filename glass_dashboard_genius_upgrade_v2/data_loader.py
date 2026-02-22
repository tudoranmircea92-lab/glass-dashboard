import pandas as pd
import pyarrow.dataset as ds

FILE = "db2026.02.19.parquet"

def _parse_datetime_series(s: pd.Series, colname: str) -> pd.Series:
    # Example shown: 1/8/2026 3:35 -> MM/DD/YYYY HH:MM
    if colname == "data":
        out = pd.to_datetime(s, errors="coerce", format="%m/%d/%Y %H:%M")
        if out.isna().mean() > 0.05:
            out2 = pd.to_datetime(s, errors="coerce", infer_datetime_format=True, dayfirst=False)
            out = out.fillna(out2)
        return out
    if colname == "file_ts":
        out = pd.to_datetime(s, errors="coerce", infer_datetime_format=True, dayfirst=False)
        return out
    return pd.to_datetime(s, errors="coerce", infer_datetime_format=True, dayfirst=False)

def load_df(row_limit: int | None = None, sample_mode: str = "head") -> pd.DataFrame:
    table = ds.dataset(FILE, format="parquet").to_table()
    df = table.to_pandas()

    for col in ["data", "file_ts"]:
        if col in df.columns:
            df[col] = _parse_datetime_series(df[col], col)

    if row_limit is not None and row_limit > 0 and len(df) > row_limit:
        if sample_mode == "random":
            df = df.sample(n=row_limit, random_state=42)
        else:
            df = df.head(row_limit)

    return df
