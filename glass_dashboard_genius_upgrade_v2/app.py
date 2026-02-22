import pandas as pd
import streamlit as st

from data_loader import load_df
from layout_manager import load_layout
from panels import PANEL_REGISTRY, panel_plasma_stability

try:
    from plasma_engine import calculate_plasma_stability
except Exception:
    calculate_plasma_stability = None

st.set_page_config(page_title="Glass Coating Industrial Dashboard", layout="wide")

@st.cache_data(show_spinner=False)
def _load(row_limit: int, sample_mode: str) -> pd.DataFrame:
    return load_df(row_limit=row_limit, sample_mode=sample_mode)

layout = load_layout()
sidebar_cfg = layout.get("sidebar", {}) if isinstance(layout.get("sidebar", {}), dict) else {}

row_default = int(sidebar_cfg.get("row_limit_default", 5000) or 5000)
row_max = int(sidebar_cfg.get("row_limit_max", 50000) or 50000)
sample_mode_default = sidebar_cfg.get("sample_mode_default", "head")

st.sidebar.title("Data Controls")
row_limit = st.sidebar.number_input("Rows to load", min_value=500, max_value=row_max, value=min(row_default, row_max), step=500)
sample_mode = st.sidebar.selectbox("Sampling", ["head", "random"], index=(1 if sample_mode_default=="random" else 0))

df = _load(int(row_limit), sample_mode)
st.sidebar.caption(f"Loaded rows: {len(df)}")
st.sidebar.caption(f"Columns: {len(df.columns)}")

# Ensure datetime type for date filtering + charts
if "data" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["data"]):
    df["data"] = pd.to_datetime(df["data"], errors="coerce", infer_datetime_format=True, dayfirst=False)

tabs = layout.get("tabs", [])
safe_tabs = []
for t in tabs:
    if isinstance(t, dict) and isinstance(t.get("name"), str) and t["name"].strip():
        safe_tabs.append({
            "name": t["name"].strip(),
            "filters": t.get("filters", []) if isinstance(t.get("filters", []), list) else [],
            "panels": t.get("panels", []) if isinstance(t.get("panels", []), list) else [],
        })
if not safe_tabs:
    safe_tabs = [{"name":"Overview","filters":[],"panels":[]}]
tab_objs = st.tabs([t["name"] for t in safe_tabs])

def _apply_filters(df_in: pd.DataFrame, filters: list, tab_key: str) -> pd.DataFrame:
    dff = df_in

    if "product" in filters and "product" in dff.columns:
        products = sorted(dff["product"].dropna().astype(str).unique().tolist())
        sel = st.selectbox("Filter by product", ["All"] + products, key=f"{tab_key}:product")
        if sel != "All":
            dff = dff[dff["product"].astype(str) == sel]

    if "has_color" in filters and "has_color" in dff.columns:
        vals = dff["has_color"].dropna().unique().tolist()
        try:
            vals_sorted = sorted(vals)
        except Exception:
            vals_sorted = sorted([str(v) for v in vals])
        default = vals_sorted
        chosen = st.multiselect("Has Color (0/1)", vals_sorted, default=default, key=f"{tab_key}:has_color")
        if chosen:
            dff = dff[dff["has_color"].isin(chosen)]

    if "date" in filters and "data" in dff.columns and pd.api.types.is_datetime64_any_dtype(dff["data"]):
        min_date = dff["data"].min()
        max_date = dff["data"].max()
        if not pd.isna(min_date) and not pd.isna(max_date):
            start, end = st.date_input("Filter by date", value=(min_date.date(), max_date.date()), key=f"{tab_key}:date")
            start_ts = pd.to_datetime(start)
            end_ts = pd.to_datetime(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            dff = dff[dff["data"].between(start_ts, end_ts)]

    return dff

for tab, tab_ui in zip(safe_tabs, tab_objs):
    with tab_ui:
        tab_key = f"tab:{tab['name']}"
        st.header(tab["name"])
        filtered = _apply_filters(df, tab.get("filters", []), tab_key)
        st.caption(f"Rows after filter: {len(filtered)}")

        for i, panel in enumerate(tab.get("panels", [])):
            if not isinstance(panel, dict):
                continue
            ptype = panel.get("type")
            if not isinstance(ptype, str) or not ptype:
                continue
            pkey = f"{tab_key}:panel:{i}:{ptype}:{panel.get('title','')}"

            if ptype == "plasma_stability":
                panel_plasma_stability(filtered, panel, pkey, calculate_plasma_stability)
                continue

            fn = PANEL_REGISTRY.get(ptype)
            if fn is None:
                st.warning(f"Unknown panel type: {ptype}")
                continue

            try:
                fn(filtered, panel, pkey)
            except Exception as e:
                st.error(f"Panel '{ptype}' crashed: {e}")
                with st.expander("Debug panel spec"):
                    st.json(panel)
