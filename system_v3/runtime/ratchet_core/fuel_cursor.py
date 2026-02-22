import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import json
import os


def fuel_cursor_path(run_dir):
    return os.path.join(run_dir, "fuel_cursor.json")


def load_fuel_cursor(run_dir):
    path = fuel_cursor_path(run_dir)
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return int(data.get("offset", 0))
    except Exception:
        return 0


def save_fuel_cursor(run_dir, offset):
    path = fuel_cursor_path(run_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"offset": int(offset)}, f, sort_keys=True, separators=(",", ":"))
