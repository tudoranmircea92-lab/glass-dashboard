import hashlib
import io
import math
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
import plotly.express as px

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.ensemble import IsolationForest
    _SKLEARN_OK = True
except Exception:
    _SKLEARN_OK = False

def _k(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:12]

def _none_if_na(x: Any) -> Optional[str]:
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    if isinstance(x, str):
        s = x.strip()
        if s == "" or s.lower() == "none" or s == "None":
            return None
    return x

def _prepare_grouping_cols_for_plot(dff: pd.DataFrame, cols: List[Optional[str]]) -> pd.DataFrame:
    for c in cols:
        if c and c in dff.columns:
            s = dff[c]
            try:
                dff[c] = s.astype("string").fillna("NA").astype(str)
            except Exception:
                dff[c] = s.fillna("NA").astype(str)
    return dff

def _safe_numeric_cols(df: pd.DataFrame) -> List[str]:
    return df.select_dtypes(include="number").columns.tolist()

def _safe_cat_cols(df: pd.DataFrame) -> List[str]:
    cols = []
    for c in df.columns:
        try:
            if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_bool_dtype(df[c]) or pd.api.types.is_categorical_dtype(df[c]):
                cols.append(c)
        except Exception:
            pass
    return cols

def _subheader_safe(title: str):
    # Streamlit compatibility: avoid optional args that may not exist in older versions
    try:
        st.subheader(title, anchor=False)  # type: ignore[arg-type]
    except Exception:
        st.subheader(title)

def _render_title(panel: Dict[str, Any], tab_key: str):
    title = panel.get("title")
    if title:
        _subheader_safe(str(title))

def panel_kpis(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    metrics = panel.get("metrics", [])
    if not metrics:
        st.info("No KPI metrics configured.")
        return

    cols = st.columns(min(4, max(1, len(metrics))), gap="small")
    for i, m in enumerate(metrics):
        with cols[i % len(cols)]:
            if m not in df.columns:
                st.metric(label=m, value="—")
                continue
            s = df[m]
            if pd.api.types.is_numeric_dtype(s):
                sn = pd.to_numeric(s, errors="coerce").dropna()
                val = float(sn.mean()) if len(sn) else math.nan
                st.metric(label=m, value=f"{val:.4g}" if math.isfinite(val) else "—")
            else:
                st.metric(label=m, value=str(s.dropna().iloc[0]) if s.dropna().shape[0] else "—")

def panel_distribution(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    col = _none_if_na(panel.get("col"))
    if not col or col not in df.columns:
        st.warning("Distribution panel missing `col` or column not found.")
        return
    if not pd.api.types.is_numeric_dtype(df[col]):
        st.warning(f"{col} is not numeric.")
        return

    bins = st.slider("Bins", 10, 200, 50, key=_k(f"{tab_key}:bins:{col}"))
    fig = px.histogram(df, x=col, nbins=bins, title=None)
    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:hist:{col}:{bins}"))

def panel_value_counts(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    col = _none_if_na(panel.get("col"))
    top = int(panel.get("top", 20) or 20)
    if not col or col not in df.columns:
        st.warning("value_counts panel requires `col`.")
        return
    s = df[col]
    try:
        ss = s.astype("string").fillna("NA").astype(str)
    except Exception:
        ss = s.fillna("NA").astype(str)
    vc = ss.value_counts(dropna=False).head(top).reset_index()
    vc.columns = [col, "count"]
    fig = px.bar(vc, x=col, y="count")
    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:vc:{col}:{top}"))
    st.dataframe(vc, use_container_width=True, key=_k(f"{tab_key}:vc:df:{col}:{top}"))

def panel_missingness(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    top = int(panel.get("top", 30) or 30)
    miss = df.isna().mean().sort_values(ascending=False).head(top)
    out = miss.reset_index()
    out.columns = ["column", "missing_pct"]
    fig = px.bar(out, x="column", y="missing_pct")
    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:miss:fig:{top}"))
    st.dataframe(out, use_container_width=True, key=_k(f"{tab_key}:miss:df:{top}"))

def panel_chart(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    chart_type = panel.get("chart_type", "scatter")
    x = _none_if_na(panel.get("x"))
    y = _none_if_na(panel.get("y"))
    color = _none_if_na(panel.get("color"))
    facet_row = _none_if_na(panel.get("facet_row"))
    facet_col = _none_if_na(panel.get("facet_col"))

    for c in [x, y, color, facet_row, facet_col]:
        if c and c not in df.columns:
            st.warning(f"Column not found: {c}")
            return

    dff = _prepare_grouping_cols_for_plot(df.copy(), [color, facet_row, facet_col])

    if chart_type == "scatter":
        fig = px.scatter(dff, x=x, y=y, color=color, facet_row=facet_row, facet_col=facet_col)
    elif chart_type == "line":
        fig = px.line(dff.sort_values(x) if x else dff, x=x, y=y, color=color)
    elif chart_type == "box":
        fig = px.box(dff, x=x, y=y, color=color)
    elif chart_type == "bar":
        fig = px.bar(dff, x=x, y=y, color=color)
    else:
        st.warning(f"Unsupported chart_type: {chart_type}")
        return

    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:chart:{chart_type}:{x}:{y}:{color}:{facet_row}:{facet_col}"))

def panel_scatter_matrix(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    cols = panel.get("cols", [])
    color = _none_if_na(panel.get("color"))

    if not isinstance(cols, list) or not cols:
        st.warning("scatter_matrix requires `cols` list.")
        return

    cols = [c for c in cols if isinstance(c, str) and c in df.columns][:6]
    if len(cols) < 2:
        st.warning("Select at least 2 columns (max 6).")
        return

    dff = df[cols + ([color] if color and color in df.columns else [])].copy()
    if color and color in dff.columns:
        dff = _prepare_grouping_cols_for_plot(dff, [color])
    fig = px.scatter_matrix(dff, dimensions=cols, color=color if color in dff.columns else None)
    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:sm:{','.join(cols)}:{color}"))

def panel_chart_builder(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)

    numeric_cols = _safe_numeric_cols(df)
    if not numeric_cols:
        st.warning("No numeric columns.")
        return

    all_cols = df.columns.tolist()
    cat_cols = [c for c in all_cols if c not in numeric_cols]

    c1, c2, c3 = st.columns([1, 1, 1], gap="small")
    with c1:
        chart_type = st.selectbox("Chart type", ["scatter", "line", "histogram", "box", "bar"], key=_k(f"{tab_key}:cb:type"))
    with c2:
        x = st.selectbox("X", all_cols, index=0, key=_k(f"{tab_key}:cb:x"))
    with c3:
        y = st.selectbox("Y", numeric_cols, index=0, key=_k(f"{tab_key}:cb:y"))

    c4, c5, c6 = st.columns([1, 1, 1], gap="small")
    with c4:
        color = _none_if_na(st.selectbox("Color (optional)", ["None"] + cat_cols, key=_k(f"{tab_key}:cb:color")))
    with c5:
        facet_col = _none_if_na(st.selectbox("Facet col (optional)", ["None"] + cat_cols, key=_k(f"{tab_key}:cb:facet_col")))
    with c6:
        facet_row = _none_if_na(st.selectbox("Facet row (optional)", ["None"] + cat_cols, key=_k(f"{tab_key}:cb:facet_row")))

    run = st.button("Generate", key=_k(f"{tab_key}:cb:run:{chart_type}:{x}:{y}:{color}:{facet_row}:{facet_col}"))
    if not run:
        st.caption("Pick options then click Generate.")
        return

    dff = _prepare_grouping_cols_for_plot(df.copy(), [color, facet_row, facet_col])

    if chart_type == "scatter":
        fig = px.scatter(dff, x=x, y=y, color=color, facet_row=facet_row, facet_col=facet_col)
    elif chart_type == "line":
        fig = px.line(dff.sort_values(x) if x else dff, x=x, y=y, color=color)
    elif chart_type == "histogram":
        fig = px.histogram(dff, x=x, color=color)
    elif chart_type == "box":
        fig = px.box(dff, x=x, y=y, color=color)
    else:
        fig = px.bar(dff, x=x, y=y, color=color)

    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:cb:fig:{chart_type}:{x}:{y}:{color}:{facet_row}:{facet_col}"))

def panel_groupby(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    group_cols = panel.get("group_cols", [])
    metrics = panel.get("metrics", [])
    agg = panel.get("agg", "mean")

    if not group_cols or not metrics:
        st.warning("Groupby panel needs `group_cols` and `metrics`.")
        return

    for c in group_cols + metrics:
        if c not in df.columns:
            st.warning(f"Column not found: {c}")
            return

    gb = df.groupby(group_cols, dropna=False)[metrics]
    if agg == "mean":
        out = gb.mean(numeric_only=True)
    elif agg == "median":
        out = gb.median(numeric_only=True)
    elif agg == "std":
        out = gb.std(numeric_only=True)
    elif agg == "min":
        out = gb.min()
    elif agg == "max":
        out = gb.max()
    else:
        st.warning(f"Unsupported agg: {agg}")
        return

    out = out.reset_index()
    st.dataframe(out, use_container_width=True, key=_k(f"{tab_key}:groupby:{':'.join(group_cols)}:{agg}"))

def panel_timeseries(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    date_col = _none_if_na(panel.get("date", "data"))
    y = _none_if_na(panel.get("y"))
    group = _none_if_na(panel.get("group"))
    agg = panel.get("agg", "mean")
    rolling = int(panel.get("rolling", 0) or 0)

    for c in [date_col, y, group]:
        if c and c not in df.columns:
            st.warning(f"Column not found: {c}")
            return

    if not date_col or not y:
        st.warning("Timeseries panel requires `date` and `y`.")
        return

    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        st.warning(f"{date_col} is not datetime. Ensure date parsing.")
        return

    dff = df.dropna(subset=[date_col])
    if group:
        g = dff.groupby([pd.Grouper(key=date_col, freq="D"), group], dropna=False)[y]
    else:
        g = dff.groupby(pd.Grouper(key=date_col, freq="D"), dropna=False)[y]

    if agg == "mean":
        out = g.mean(numeric_only=True)
    elif agg == "median":
        out = g.median(numeric_only=True)
    else:
        out = g.mean(numeric_only=True)

    out = out.reset_index()

    if group and group in out.columns:
        try:
            out[group] = out[group].astype("string").fillna("NA").astype(str)
        except Exception:
            out[group] = out[group].fillna("NA").astype(str)

    if rolling and rolling > 1:
        if group:
            out["rolling"] = out.groupby(group)[y].transform(lambda s: s.rolling(rolling, min_periods=1).mean())
            fig = px.line(out.sort_values(date_col), x=date_col, y="rolling", color=group)
        else:
            out["rolling"] = out[y].rolling(rolling, min_periods=1).mean()
            fig = px.line(out.sort_values(date_col), x=date_col, y="rolling")
    else:
        fig = px.line(out.sort_values(date_col), x=date_col, y=y, color=group)

    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:ts:{date_col}:{y}:{group}:{agg}:{rolling}"))

def panel_correlation(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    numeric_cols = _safe_numeric_cols(df)
    if len(numeric_cols) < 2:
        st.warning("Not enough numeric columns for correlation.")
        return

    default_n = min(25, len(numeric_cols))
    sel = st.multiselect("Columns", numeric_cols, default=numeric_cols[:default_n], key=_k(f"{tab_key}:corr:cols"))
    if len(sel) < 2:
        st.info("Select at least 2 columns.")
        return

    corr = df[sel].corr(numeric_only=True)
    fig = px.imshow(corr, text_auto=False, aspect="auto")
    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:corr:fig:{len(sel)}"))

def panel_pca(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    if not _SKLEARN_OK:
        st.info("scikit-learn not installed. Install it to enable PCA.")
        return

    numeric_cols = _safe_numeric_cols(df)
    if len(numeric_cols) < 3:
        st.warning("Need at least 3 numeric columns for PCA.")
        return

    sel = st.multiselect("Numeric columns", numeric_cols, default=numeric_cols[:min(20, len(numeric_cols))], key=_k(f"{tab_key}:pca:cols"))
    if len(sel) < 3:
        st.info("Select at least 3 columns.")
        return

    color = _none_if_na(st.selectbox("Color (optional)", ["None"] + _safe_cat_cols(df), key=_k(f"{tab_key}:pca:color")))

    X = df[sel].copy()
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    pca = PCA(n_components=2, random_state=42)
    Z = pca.fit_transform(Xs)

    out = pd.DataFrame({"PC1": Z[:, 0], "PC2": Z[:, 1]})
    if color and color in df.columns:
        out[color] = df[color].astype("string").fillna("NA").astype(str)

    fig = px.scatter(out, x="PC1", y="PC2", color=color)
    st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:pca:fig:{len(sel)}:{color}"))

    with st.expander("PCA explained variance / loadings", expanded=False):
        st.write({"explained_variance_ratio": pca.explained_variance_ratio_.tolist()})
        loadings = pd.DataFrame(pca.components_.T, index=sel, columns=["PC1_loading", "PC2_loading"])
        st.dataframe(loadings, use_container_width=True, key=_k(f"{tab_key}:pca:loadings:{len(sel)}"))

def panel_anomaly(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    if not _SKLEARN_OK:
        st.info("scikit-learn not installed. Install it to enable Anomaly Detection.")
        return

    numeric_cols = _safe_numeric_cols(df)
    if len(numeric_cols) < 3:
        st.warning("Need at least 3 numeric columns for anomaly detection.")
        return

    sel = st.multiselect("Numeric columns", numeric_cols, default=numeric_cols[:min(25, len(numeric_cols))], key=_k(f"{tab_key}:anom:cols"))
    if len(sel) < 3:
        st.info("Select at least 3 columns.")
        return

    contamination = st.slider("Contamination (expected anomaly fraction)", 0.001, 0.2, 0.02, step=0.001, key=_k(f"{tab_key}:anom:cont"))
    n_show = st.slider("Show top anomalies", 10, 200, 50, key=_k(f"{tab_key}:anom:show"))

    X = df[sel].copy()
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    model = IsolationForest(
        n_estimators=200,
        contamination=float(contamination),
        random_state=42,
        n_jobs=-1
    )
    scores = model.fit_predict(X)
    raw = model.decision_function(X)

    out = df.copy()
    out["_anomaly"] = (scores == -1)
    out["_anomaly_score"] = raw

    top = out.sort_values("_anomaly_score", ascending=True).head(int(n_show))
    st.dataframe(top, use_container_width=True, key=_k(f"{tab_key}:anom:df:{len(sel)}:{contamination}:{n_show}"))

def panel_stats(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    numeric_cols = _safe_numeric_cols(df)
    if not numeric_cols:
        st.warning("No numeric columns.")
        return
    sel = st.multiselect("Columns", numeric_cols, default=numeric_cols[:min(25, len(numeric_cols))], key=_k(f"{tab_key}:stats:cols"))
    if not sel:
        return
    desc = df[sel].describe().T
    st.dataframe(desc, use_container_width=True, key=_k(f"{tab_key}:stats:df:{len(sel)}"))

def panel_column_explorer(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    q = st.text_input("Search column name", value="", key=_k(f"{tab_key}:ce:q"))
    cols = df.columns.tolist()
    if q.strip():
        cols = [c for c in cols if q.lower() in c.lower()]

    max_show = st.slider("Max columns to show", 20, 300, 80, key=_k(f"{tab_key}:ce:max"))
    cols = cols[:max_show]

    rows = []
    for c in cols:
        s = df[c]
        miss = float(s.isna().mean())
        try:
            nun = int(s.nunique(dropna=True))
        except Exception:
            nun = None
        rows.append({
            "column": c,
            "dtype": str(s.dtype),
            "missing_pct": miss,
            "n_unique": nun,
            "sample": str(s.dropna().iloc[0]) if s.dropna().shape[0] else "—"
        })
    out = pd.DataFrame(rows).sort_values("missing_pct", ascending=False)
    st.dataframe(out, use_container_width=True, key=_k(f"{tab_key}:ce:df:{q}:{max_show}"))

def panel_export(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str):
    _render_title(panel, tab_key)
    n = len(df)
    st.caption(f"Rows to export: {n}")
    if n == 0:
        return
    limit = st.number_input("Export rows limit (0 = all)", min_value=0, max_value=max(0, n), value=min(n, 10000), step=1000, key=_k(f"{tab_key}:exp:limit"))
    dff = df if int(limit) == 0 else df.head(int(limit))
    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name="filtered_export.csv", mime="text/csv", key=_k(f"{tab_key}:exp:btn:{len(dff)}"))

def panel_plasma_stability(df: pd.DataFrame, panel: Dict[str, Any], tab_key: str, calculate_plasma_stability):
    _render_title(panel, tab_key)
    if calculate_plasma_stability is None:
        st.error("plasma_engine.calculate_plasma_stability not available.")
        return
    stability = calculate_plasma_stability(df)
    st.caption("Top 10 Most Unstable Cathodes")
    top10 = stability.head(10)
    st.dataframe(top10, use_container_width=True, key=_k(f"{tab_key}:plasma:table"))
    if "cathode" in top10.columns and "stability_index" in top10.columns:
        fig = px.bar(top10, x="cathode", y="stability_index")
        st.plotly_chart(fig, use_container_width=True, key=_k(f"{tab_key}:plasma:bar"))

PANEL_REGISTRY = {
    "kpis": panel_kpis,
    "distribution": panel_distribution,
    "value_counts": panel_value_counts,
    "missingness": panel_missingness,
    "chart": panel_chart,
    "scatter_matrix": panel_scatter_matrix,
    "chart_builder": panel_chart_builder,
    "groupby": panel_groupby,
    "timeseries": panel_timeseries,
    "correlation": panel_correlation,
    "pca": panel_pca,
    "anomaly": panel_anomaly,
    "stats": panel_stats,
    "column_explorer": panel_column_explorer,
    "export": panel_export,
}
