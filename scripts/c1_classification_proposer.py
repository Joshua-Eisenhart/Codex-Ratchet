#!/usr/bin/env python3
"""Propose C1 classifications without editing sim source files."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import adaptive_controller
import lint_sim_contract


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "system_v5/ops/c1_classification_proposals.json"


def has_classification(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text())
    except Exception:
        return False
    assigns = lint_sim_contract._module_level_assignments(tree)  # noqa: SLF001 - reuse repo linter parser.
    return "classification" in assigns or "CLASSIFICATION" in assigns


def proposal_for(path: Path) -> dict[str, Any]:
    text = path.read_text(errors="replace")
    runner_class = adaptive_controller.runner_class_for(path, text)
    depth = {}
    manifest = {}
    try:
        tree = ast.parse(text)
        assigns = lint_sim_contract._module_level_assignments(tree)  # noqa: SLF001
        depth = assigns.get("TOOL_INTEGRATION_DEPTH") if isinstance(assigns.get("TOOL_INTEGRATION_DEPTH"), dict) else {}
        manifest = assigns.get("TOOL_MANIFEST") if isinstance(assigns.get("TOOL_MANIFEST"), dict) else {}
    except Exception:
        pass
    load_bearing = sorted(str(tool) for tool, level in depth.items() if level == "load_bearing")
    if runner_class == "classical" and not load_bearing:
        proposed = "classical_baseline"
        confidence = "medium"
        rationale = "runner_class classical and no load-bearing tools detected"
    elif runner_class in {"nonclassical", "bridge"} or load_bearing:
        proposed = "canonical"
        confidence = "review_required"
        rationale = "nonclassical/bridge runner class or load-bearing tool evidence"
    else:
        proposed = "needs_owner_review"
        confidence = "low"
        rationale = "runner class unknown and no static classification"
    return {
        "sim": str(path.relative_to(ROOT)),
        "runner_class": runner_class,
        "runner_class_reason": adaptive_controller.runner_class_reason(path, text),
        "proposed_classification": proposed,
        "confidence": confidence,
        "rationale": rationale,
        "load_bearing_tools": load_bearing,
        "manifest_tools": sorted(str(tool) for tool in manifest),
    }


def main() -> int:
    sims = sorted(path for path in adaptive_controller.PROBES.glob("sim_*.py") if path.is_file() and " 2" not in path.name)
    proposals = [proposal_for(path) for path in sims if not has_classification(path)]
    report = {
        "schema": "c1_classification_proposals_v1",
        "mode": "dry_run_no_source_edits",
        "proposal_count": len(proposals),
        "counts": {
            key: sum(1 for row in proposals if row["proposed_classification"] == key)
            for key in sorted({row["proposed_classification"] for row in proposals})
        },
        "proposals": proposals,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"proposal_count": len(proposals), "counts": report["counts"], "path": str(OUT_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
