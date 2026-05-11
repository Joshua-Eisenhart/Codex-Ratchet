#!/usr/bin/env python3
"""Propose C4 divergence-log repairs without editing sim source files."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import adaptive_controller
import lint_sim_contract


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "system_v5/ops/c4_divergence_log_proposals.json"


def assignment_snapshot(path: Path) -> dict[str, Any]:
    try:
        tree = ast.parse(path.read_text())
        return lint_sim_contract._module_level_assignments(tree)  # noqa: SLF001
    except Exception:
        return {}


def proposal_for(path: Path, rule: str) -> dict[str, Any]:
    assigns = assignment_snapshot(path)
    runner_class = adaptive_controller.runner_class_for(path)
    proposed = (
        "Add a non-empty divergence_log explaining the classical baseline contrast, "
        "or reclassify through the C1 proposal surface if this is not a classical baseline."
    )
    return {
        "sim": str(path.relative_to(ROOT)),
        "rule": rule,
        "classification": assigns.get("classification"),
        "runner_class": runner_class,
        "current_divergence_log": assigns.get("divergence_log", None),
        "proposed_action": proposed,
        "mode": "dry_run_no_source_edits",
    }


def main() -> int:
    proposals = []
    for path in sorted(adaptive_controller.PROBES.glob("sim_*.py")):
        if not path.is_file() or " 2" in path.name:
            continue
        for violation in lint_sim_contract.lint_sim(path):
            if violation["rule"] in {"C4_divergence_log_missing", "C4_divergence_log_empty"}:
                proposals.append(proposal_for(path, violation["rule"]))
                break
    report = {
        "schema": "c4_divergence_log_proposals_v1",
        "mode": "dry_run_no_source_edits",
        "proposal_count": len(proposals),
        "rules": {
            rule: sum(1 for row in proposals if row["rule"] == rule)
            for rule in sorted({row["rule"] for row in proposals})
        },
        "proposals": proposals,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"proposal_count": len(proposals), "rules": report["rules"], "path": str(OUT_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
