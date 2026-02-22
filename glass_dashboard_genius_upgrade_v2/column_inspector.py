from __future__ import annotations
from typing import Any, Dict, Optional
import pandas as pd
import pyarrow.dataset as ds

FILE = "db2026.02.19.parquet"

def inspect_column(col: str, row_limit: int = 100000, sample_mode: str = "head", top: int = 20) -> Dict[str, Any]:
    dataset = ds.dataset(FILE, format="parquet")
    if col not in dataset.schema.names:
        return {"ok": False, "error": f"Column not found: {col}"}

    # Load only that column (fast + memory safe)
    table = dataset.to_table(columns=[col])
    s = table.to_pandas()[col]

    n_total = int(len(s))
    if row_limit and n_total > row_limit:
        if sample_mode == "random":
            s = s.sample(n=row_limit, random_state=42)
        else:
            s = s.head(row_limit)

    out: Dict[str, Any] = {"ok": True, "column": col, "dtype": str(s.dtype), "rows_sampled": int(len(s))}
    out["missing"] = int(pd.isna(s).sum())
    out["missing_pct"] = float(out["missing"] / max(1, len(s)))

    # Try numeric stats
    if pd.api.types.is_numeric_dtype(s):
        sn = pd.to_numeric(s, errors="coerce")
        out["numeric"] = {
            "min": float(sn.min()) if sn.notna().any() else None,
            "max": float(sn.max()) if sn.notna().any() else None,
            "mean": float(sn.mean()) if sn.notna().any() else None,
            "std": float(sn.std()) if sn.notna().any() else None,
        }
        qs = sn.quantile([0.01,0.05,0.25,0.5,0.75,0.95,0.99]).to_dict()
        out["quantiles"] = {str(k): (float(v) if pd.notna(v) else None) for k, v in qs.items()}
    else:
        # categorical-ish
        try:
            ss = s.astype("string").fillna("NA").astype(str)
        except Exception:
            ss = s.fillna("NA").astype(str)
        vc = ss.value_counts(dropna=False).head(top)
        out["top_values"] = [{"value": str(idx), "count": int(cnt)} for idx, cnt in vc.items()]
        out["unique_estimate"] = int(ss.nunique(dropna=False))

    # samples
    samp = s.dropna().head(10).tolist()
    out["samples"] = [str(x) for x in samp]
    return out
