# Glass Coating Dashboard — Genius Upgrade v2 (Agent + Streamlit)

This is an **overlay ZIP** for your project in `~/proiecte/dashboard`.

## What’s new vs v1
### Agent
- New action: `inspect_column` (e.g. `has_color`) — returns dtype, missing, value counts / numeric stats.
- More resilient parsing of multi-command outputs.
- Safer layout rollback (won’t crash when no backups exist).
- Keeps file writing safe (`create_file`) but now also supports **append** + **patch** operations.

### Streamlit / Visualizations
- Adds filter: **has_color** (so you can include 0 and 1).
- Adds panels:
  - `column_explorer` (search columns, dtype, missing %, unique, samples)
  - `value_counts` (bar chart for categorical/binary like `has_color`)
  - `missingness` (top missing columns)
  - `scatter_matrix` (safe, limited dimensions)
  - `export` (download filtered dataset as CSV)
- Title rendering is Streamlit-version-safe (no unsupported args).

## Install
```bash
cd ~/proiecte/dashboard
unzip -o glass_dashboard_genius_upgrade_v2.zip -d ~/proiecte/dashboard
```

## Run (2 panes)
```bash
chmod +x start_tmux.sh
./start_tmux.sh
```

Backups: `.backups/layout/`

## Quick test (has_color=0 visible)
Open Streamlit → Overview → **Has Color (0/1)** filter → select both `0` and `1`.
