import pandas as pd

def calculate_plasma_stability(df):

    cathodes = sorted(set(
        col.split(".")[0]
        for col in df.columns
        if col.startswith("c")
    ))

    results = []

    for cathode in cathodes:

        cathode_cols = [
            col for col in df.columns
            if col.startswith(cathode + ".")
        ]

        voltage_cols = [
            col for col in cathode_cols
            if "Voltage" in col
        ]

        current_cols = [
            col for col in cathode_cols
            if "current" in col.lower()
        ]

        arc_cols = [
            col for col in cathode_cols
            if "Arc" in col
        ]

        stability = 0

        if voltage_cols:
            stability += df[voltage_cols].std().mean()

        if current_cols:
            stability += df[current_cols].std().mean()

        if arc_cols:
            stability += df[arc_cols].std().mean()

        results.append({
            "cathode": cathode,
            "stability_index": stability
        })

    result_df = pd.DataFrame(results)

    return result_df.sort_values(
        "stability_index",
        ascending=False
    )

