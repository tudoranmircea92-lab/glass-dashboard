import json
from typing import Any, Dict, List

def extract_json_objects(text: str) -> List[Dict[str, Any]]:
    if not isinstance(text, str):
        return []
    s = text.strip()
    if not s:
        return []

    # JSON array fast path
    if s.startswith('['):
        try:
            arr = json.loads(s)
            if isinstance(arr, list):
                return [x for x in arr if isinstance(x, dict)]
        except Exception:
            pass

    decoder = json.JSONDecoder()
    out: List[Dict[str, Any]] = []
    i, n = 0, len(s)
    while i < n:
        while i < n and s[i] not in '{[':
            i += 1
        if i >= n:
            break
        try:
            obj, end = decoder.raw_decode(s, i)
            i = end
            if isinstance(obj, dict):
                out.append(obj)
            elif isinstance(obj, list):
                out.extend([x for x in obj if isinstance(x, dict)])
        except Exception:
            i += 1
    return out
