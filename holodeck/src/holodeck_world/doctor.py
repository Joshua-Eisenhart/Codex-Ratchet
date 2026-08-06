from __future__ import annotations

import importlib.metadata
import importlib.util
import json
from pathlib import Path
from typing import Any


PRODUCT_ROOT = Path(__file__).resolve().parents[2]


def _import_visible(import_name: str) -> bool:
    try:
        return importlib.util.find_spec(import_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def report() -> dict[str, Any]:
    registry_path = PRODUCT_ROOT / "registry" / "world-model-tools.v9.json"
    source_index_path = PRODUCT_ROOT / "registry" / "source-index.v9.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    source_index = json.loads(source_index_path.read_text(encoding="utf-8"))
    rows = []
    for declared in registry["tools"]:
        distribution = declared["id"].split(".", 1)[1]
        try:
            version = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            version = None
        rows.append({**declared, "live_import_visible": _import_visible(declared["import"]), "live_version": version})
    repo_root = PRODUCT_ROOT.parent
    sources = [{**row, "exists": (repo_root / row["path"]).exists()} for row in source_index["sources"]]
    return {
        "schema": "codex-ratchet.holodeck-doctor.v9",
        "product_version": "0.1.0.dev1",
        "tool_rows": rows,
        "candidate_sources": sources,
        "qit_bridge_state": "blocked_pending_independent_qit_engine_reality_gate",
        "claim_ceiling": "product_scaffold_and_live_tool_visibility_only"
    }
