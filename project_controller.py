import os
from typing import Any, Dict, List, Optional

from layout_manager import load_layout, save_layout, backup_layout, rollback_last

LAYOUT_FILE = "layout.json"
ALLOWED_WRITE_EXT = {".py", ".json", ".md", ".txt", ".yml", ".yaml"}

def _safe_relpath(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("relative_path is required.")
    path = path.strip().replace('\\', '/')
    if path.startswith('/') or path.startswith('~'):
        raise ValueError("Absolute paths are not allowed.")
    if '..' in path.split('/'):
        raise ValueError("Path traversal '..' is not allowed.")
    return path

def _write_file(relative_path: str, content: str) -> str:
    rp = _safe_relpath(relative_path)
    ext = os.path.splitext(rp)[1].lower()
    if ext not in ALLOWED_WRITE_EXT:
        raise ValueError(f"Extension not allowed: {ext}. Allowed: {sorted(ALLOWED_WRITE_EXT)}")
    full = os.path.abspath(rp)
    proj = os.path.abspath('.')
    if not full.startswith(proj):
        raise ValueError("Write path is outside project directory.")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    return rp

def list_tabs(layout: Dict[str, Any]) -> List[str]:
    return [t.get('name') for t in layout.get('tabs', []) if isinstance(t, dict) and isinstance(t.get('name'), str)]

def _find_tab(layout: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    for t in layout.get('tabs', []):
        if isinstance(t, dict) and t.get('name') == name:
            return t
    return None

def apply_command(cmd: Dict[str, Any], columns: List[str]) -> Dict[str, Any]:
    if not isinstance(cmd, dict):
        return {"ok": False, "error": "Command must be an object."}
    action = cmd.get('action')
    if not isinstance(action, str) or not action:
        return {"ok": False, "error": "Missing action."}

    if action == "list_tabs":
        layout = load_layout(LAYOUT_FILE)
        return {"ok": True, "tabs": list_tabs(layout)}

    if action == "create_file":
        rp = cmd.get("relative_path")
        content = cmd.get("content", "")
        if not isinstance(rp, str):
            return {"ok": False, "error": "create_file requires relative_path (string)."}
        if not isinstance(content, str):
            return {"ok": False, "error": "create_file requires content (string)."}
        try:
            path = _write_file(rp, content)
            return {"ok": True, "written": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if action == "rollback_layout":
        rb = rollback_last(LAYOUT_FILE)
        return {"ok": True, "rollback": rb}

    # Layout modifications => backup first
    backup_layout(LAYOUT_FILE)
    layout = load_layout(LAYOUT_FILE)

    if action == "add_tab":
        name = cmd.get("name")
        if not isinstance(name, str) or not name.strip():
            return {"ok": False, "error": "add_tab requires name."}
        name = name.strip()
        if _find_tab(layout, name):
            return {"ok": True, "message": "Tab already exists.", "tab": name}
        layout["tabs"].append({"name": name, "filters": [], "panels": []})
        save_layout(layout, LAYOUT_FILE)
        return {"ok": True, "added_tab": name}

    if action == "delete_tab":
        name = cmd.get("name")
        if not isinstance(name, str) or not name.strip():
            return {"ok": False, "error": "delete_tab requires name."}
        name = name.strip()
        layout["tabs"] = [t for t in layout.get("tabs", []) if not (isinstance(t, dict) and t.get("name") == name)]
        save_layout(layout, LAYOUT_FILE)
        return {"ok": True, "deleted_tab": name}

    if action == "keep_only_tab":
        name = cmd.get("name")
        if not isinstance(name, str) or not name.strip():
            return {"ok": False, "error": "keep_only_tab requires name."}
        name = name.strip()
        t = _find_tab(layout, name)
        if not t:
            return {"ok": False, "error": f"Tab not found: {name}"}
        layout["tabs"] = [t]
        save_layout(layout, LAYOUT_FILE)
        return {"ok": True, "kept_only": name}

    if action == "clear_panels":
        tab_name = cmd.get("tab_name")
        if not isinstance(tab_name, str) or not tab_name.strip():
            return {"ok": False, "error": "clear_panels requires tab_name."}
        tab_name = tab_name.strip()
        t = _find_tab(layout, tab_name)
        if not t:
            return {"ok": False, "error": f"Tab not found: {tab_name}"}
        t["panels"] = []
        save_layout(layout, LAYOUT_FILE)
        return {"ok": True, "cleared_panels": tab_name}

    if action == "add_panel":
        tab_name = cmd.get("tab_name")
        panel = cmd.get("panel")
        if not isinstance(tab_name, str) or not tab_name.strip():
            return {"ok": False, "error": "add_panel requires tab_name."}
        if not isinstance(panel, dict):
            return {"ok": False, "error": "add_panel requires panel object."}
        tab_name = tab_name.strip()
        t = _find_tab(layout, tab_name)
        if not t:
            t = {"name": tab_name, "filters": [], "panels": []}
            layout["tabs"].append(t)

        ptype = panel.get("type")
        if not isinstance(ptype, str) or not ptype.strip():
            return {"ok": False, "error": "panel.type is required."}
        panel["type"] = ptype.strip()

        def _check_col(c):
            return (c in columns) if isinstance(c, str) else True

        for key in ["x","y","col","date","group","facet_row","facet_col","color"]:
            if key in panel and isinstance(panel[key], str) and panel[key] and not _check_col(panel[key]):
                return {"ok": False, "error": f"Unknown column for {key}: {panel[key]}"}

        if "metrics" in panel and isinstance(panel["metrics"], list):
            bad = [m for m in panel["metrics"] if isinstance(m, str) and m not in columns]
            if bad:
                return {"ok": False, "error": f"Unknown metric columns: {bad[:8]}{'...' if len(bad)>8 else ''}"}

        t.setdefault("panels", [])
        t["panels"].append(panel)
        save_layout(layout, LAYOUT_FILE)
        return {"ok": True, "added_panel": panel.get("title", panel["type"]), "tab": tab_name}

    return {"ok": False, "error": f"Unknown action: {action}"}
