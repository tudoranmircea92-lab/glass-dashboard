# Glass Coating Dashboard — Genius Upgrade (Agent + Streamlit)

Drop-in upgrade for your existing project in `~/proiecte/dashboard`.

## Highlights
### Agent (agent_elite.py)
- Parses **single or multiple JSON commands** (newline JSON, JSON list, etc.).
- Strong validation (e.g., `delete_tab` always needs `name`).
- **Auto-backup** for `layout.json` before any change + safe rollback.
- Can **create/update files** (`.py`, `.json`, `.md`) inside the project safely.
- Your prompt "populate all tabs..." can produce many commands; agent applies all.

### Streamlit (app.py + panels.py + data_loader.py)
- Correct date parsing for `data` as **MM/DD/YYYY HH:MM** (+ fallback).
- Sidebar **Row limit** + sampling mode (head/random) for speed.
- Plotly fixes: avoids `boolean value of NA is ambiguous` for group/color/facets.
- Streamlit compatibility fixes: stable unique keys; no `key=` on headings.

## Install
From `~/proiecte/dashboard`:
```bash
unzip -o glass_dashboard_genius_upgrade.zip -d ~/proiecte/dashboard
```

## Run in 2 panes (tmux)
```bash
chmod +x start_tmux.sh
./start_tmux.sh
```

Backups are stored in `.backups/layout/`.
