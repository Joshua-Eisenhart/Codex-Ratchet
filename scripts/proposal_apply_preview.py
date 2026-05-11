#!/usr/bin/env python3
"""Build a single dry-run preview from generated proposal reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "system_v5/ops"
OUT_PATH = OPS / "proposal_apply_preview.json"


INPUTS = {
    "c1": OPS / "c1_classification_proposals.json",
    "c4": OPS / "c4_divergence_log_proposals.json",
    "c6": OPS / "c6_loadbearing_report.json",
}


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    sections: dict[str, Any] = {}
    action_items = []
    for name, path in INPUTS.items():
        data = load(path)
        if not data:
            sections[name] = {"present": False}
            continue
        rows = data.get("proposals") or data.get("rows") or []
        sections[name] = {
            "present": True,
            "path": str(path.relative_to(ROOT)),
            "row_count": len(rows),
            "sample": rows[:20],
        }
        action_items.append(
            {
                "proposal_family": name,
                "path": str(path.relative_to(ROOT)),
                "row_count": len(rows),
                "next_action": "owner_review_required_before_any_source_edit",
            }
        )
    report = {
        "schema": "proposal_apply_preview_v1",
        "mode": "dry_run_no_source_edits",
        "action_items": action_items,
        "sections": sections,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"path": str(OUT_PATH.relative_to(ROOT)), "action_item_count": len(action_items)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
