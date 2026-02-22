import os
import json
from typing import Any, Dict, List

WORKSPACE_DIR = "workspaces"

def create_workspace(name: str, config: Dict[str, Any]) -> str:
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    filename = name.lower().replace(" ", "_") + ".json"
    path = os.path.join(WORKSPACE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"name": name, "workspace": config}, f, indent=2, ensure_ascii=False)
    return path

def load_workspaces() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not os.path.exists(WORKSPACE_DIR):
        return out
    for file in os.listdir(WORKSPACE_DIR):
        if file.endswith(".json"):
            with open(os.path.join(WORKSPACE_DIR, file), "r", encoding="utf-8") as f:
                out.append(json.load(f))
    return out
