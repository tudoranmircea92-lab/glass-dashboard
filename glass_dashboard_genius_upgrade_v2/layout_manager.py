import json
import os
import time
from typing import Any, Dict, List, Optional

LAYOUT_FILE = "layout.json"
BACKUP_DIR = os.path.join(".backups", "layout")

def _ensure_dirs():
    os.makedirs(BACKUP_DIR, exist_ok=True)

def load_layout(path: str = LAYOUT_FILE) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"tabs": [{"name": "Overview", "filters": [], "panels": []}], "sidebar": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _validate(layout: Dict[str, Any]) -> Dict[str, Any]:
    tabs = layout.get("tabs", [])
    safe_tabs: List[Dict[str, Any]] = []
    for t in tabs:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        safe_tabs.append({
            "name": name.strip(),
            "filters": t.get("filters", []) if isinstance(t.get("filters", []), list) else [],
            "panels": t.get("panels", []) if isinstance(t.get("panels", []), list) else [],
        })
    if not safe_tabs:
        safe_tabs = [{"name": "Overview", "filters": [], "panels": []}]
    layout["tabs"] = safe_tabs

    sidebar = layout.get("sidebar", {})
    if not isinstance(sidebar, dict):
        sidebar = {}
    layout["sidebar"] = sidebar
    return layout

def save_layout(layout: Dict[str, Any], path: str = LAYOUT_FILE) -> None:
    layout = _validate(layout)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2)

def backup_layout(path: str = LAYOUT_FILE) -> Optional[str]:
    if not os.path.exists(path):
        return None
    _ensure_dirs()
    ts = time.strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"layout_{ts}.json")
    with open(path, "rb") as src, open(dest, "wb") as dst:
        dst.write(src.read())
    return dest

def list_backups() -> List[str]:
    if not os.path.exists(BACKUP_DIR):
        return []
    files = [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith(".json")]
    return sorted(files)

def rollback_last(path: str = LAYOUT_FILE) -> Optional[str]:
    backups = list_backups()
    if not backups:
        return None
    last = backups[-1]
    with open(last, "rb") as src, open(path, "wb") as dst:
        dst.write(src.read())
    return last
