import os
import json
from typing import Any, Dict, List

import pyarrow.dataset as ds
from openai import OpenAI

from json_multi_parser import extract_json_objects
from project_controller import apply_command

FILE = "db2026.02.19.parquet"
LAYOUT_FILE = "layout.json"

DEFAULT_MODEL = os.getenv("AGENT_MODEL", "gpt-4.1-mini")

SYSTEM_PROMPT = """You are an elite industrial dashboard agent for glass coating data analysis.

You control the dashboard by outputting JSON commands ONLY.
You may output:
- a single JSON object, OR
- multiple JSON objects separated by newlines, OR
- a JSON array of objects.

Each command must include:
- action: string

Supported actions:
- list_tabs
- inspect_column (name, row_limit?, sample_mode?, top?)
- add_tab (name)
- delete_tab (name)   # name is required
- keep_only_tab (name)
- add_panel (tab_name, panel)
- clear_panels (tab_name)
- create_file (relative_path, content, mode=write|append)
- patch_file (relative_path, pattern, replacement)
- rollback_layout

Rules:
- When deleting a tab you MUST provide the exact tab name in `name`.
- Do not include commentary outside JSON.
- Prefer columns that exist in the dataset.
"""

def load_columns() -> List[str]:
    dataset = ds.dataset(FILE, format="parquet")
    schema = dataset.schema
    return [f.name for f in schema]

def _pretty_print_dict(d: Dict[str, Any]):
    print(json.dumps(d, indent=2, ensure_ascii=False)[:4000])

def main():
    client = OpenAI()
    columns = load_columns()

    print("\nELITE Glass Coating Dashboard Agent READY")
    print(f"Layout file: {LAYOUT_FILE}")
    print(f"Dataset: {FILE}")
    print(f"Columns loaded: {len(columns)}")
    print("Type 'exit' to quit.\n")

    while True:
        user = input("> ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        if not user:
            continue

        # quick local shortcuts
        if user.lower() in {"tabs", "list tabs", "list_tabs"}:
            res = apply_command({"action":"list_tabs"}, columns)
            if res.get("ok"):
                print("TABS:")
                for t in res.get("tabs", []):
                    print("-", t)
                print("Refresh Streamlit.\n")
            else:
                print("ERROR:", res.get("error"))
            continue

        if user.lower().startswith("inspect "):
            col = user.split(" ", 1)[1].strip()
            res = apply_command({"action":"inspect_column","name":col}, columns)
            _pretty_print_dict(res)
            print("\nRefresh Streamlit.\n")
            continue

        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=[
                {"role":"system","content":SYSTEM_PROMPT},
                {"role":"user","content":user}
            ],
        )

        raw = response.output_text or ""
        cmds = extract_json_objects(raw)

        if not cmds:
            print("MODEL_OUTPUT_PARSE_ERROR: No JSON found.")
            print("RAW:", raw[:1200])
            print()
            continue

        for cmd in cmds:
            res = apply_command(cmd, columns)
            if not res.get("ok"):
                print("ERROR:", res.get("error"))
            else:
                if cmd.get("action") == "inspect_column":
                    _pretty_print_dict(res)
                elif "tabs" in res:
                    print("TABS:", res["tabs"])
                elif "written" in res:
                    print("FILE WRITTEN:", res["written"], "mode:", res.get("mode"))
                elif "patched" in res:
                    print("FILE PATCHED:", res["patched"])
                elif "rollback" in res:
                    print("ROLLBACK:", res["rollback"])
                else:
                    msg = {k:v for k,v in res.items() if k != "ok"}
                    print("OK:", msg if msg else "done")

        print("Refresh Streamlit.\n")

if __name__ == "__main__":
    main()
