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


def emitted_classification_conflicts(path: Path, classification: object) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(path.read_text())
    except Exception:
        return []
    conflicts: list[dict[str, Any]] = []
    assigns = assignment_snapshot(path)
    upper = assigns.get("CLASSIFICATION")
    if upper is not None and upper != classification:
        conflicts.append(
            {
                "line": None,
                "kind": "module_classification_shadow",
                "emitted": upper,
            }
        )
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and key.value == "classification"):
                continue
            if isinstance(value, ast.Constant) and value.value != classification:
                conflicts.append(
                    {
                        "line": node.lineno,
                        "kind": "result_literal_classification",
                        "emitted": value.value,
                    }
                )
            elif isinstance(value, ast.Name) and value.id == "CLASSIFICATION" and upper != classification:
                conflicts.append(
                    {
                        "line": node.lineno,
                        "kind": "result_classification_name",
                        "emitted": upper,
                    }
                )
    return conflicts


def proposal_for(path: Path, rule: str, violations: list[dict[str, Any]]) -> dict[str, Any]:
    assigns = assignment_snapshot(path)
    runner_class = adaptive_controller.runner_class_for(path)
    classification = assigns.get("classification", assigns.get("CLASSIFICATION"))
    classification_conflicts = emitted_classification_conflicts(path, classification)
    all_rules = sorted({str(violation["rule"]) for violation in violations})
    c4_only = set(all_rules) <= {"C4_divergence_log_missing", "C4_divergence_log_empty"}
    if runner_class == "classical" and c4_only and not classification_conflicts:
        proposal_kind = "simple_classical_divergence_log"
        proposed = (
            "Add a non-empty divergence_log explaining the classical baseline contrast."
        )
    else:
        proposal_kind = "classification_or_stage_review_required"
        proposed = (
            "Do not add divergence_log as a simple C4 fix; review classification, "
            "runner class, and any stage-gate claim before editing source metadata."
        )
    return {
        "sim": str(path.relative_to(ROOT)),
        "rule": rule,
        "classification": classification,
        "runner_class": runner_class,
        "all_rules": all_rules,
        "current_divergence_log": assigns.get("divergence_log", None),
        "classification_conflicts": classification_conflicts,
        "proposal_kind": proposal_kind,
        "proposed_action": proposed,
        "mode": "dry_run_no_source_edits",
    }


def main() -> int:
    proposals = []
    for path in sorted(adaptive_controller.PROBES.glob("sim_*.py")):
        if not path.is_file() or " 2" in path.name:
            continue
        violations = lint_sim_contract.lint_sim(path)
        for violation in violations:
            if violation["rule"] in {"C4_divergence_log_missing", "C4_divergence_log_empty"}:
                proposals.append(proposal_for(path, violation["rule"], violations))
                break
    report = {
        "schema": "c4_divergence_log_proposals_v1",
        "mode": "dry_run_no_source_edits",
        "proposal_count": len(proposals),
        "rules": {
            rule: sum(1 for row in proposals if row["rule"] == rule)
            for rule in sorted({row["rule"] for row in proposals})
        },
        "proposal_kinds": {
            kind: sum(1 for row in proposals if row["proposal_kind"] == kind)
            for kind in sorted({row["proposal_kind"] for row in proposals})
        },
        "runner_classes": {
            runner_class: sum(1 for row in proposals if row["runner_class"] == runner_class)
            for runner_class in sorted({row["runner_class"] for row in proposals})
        },
        "proposals": proposals,
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"proposal_count": len(proposals), "rules": report["rules"], "path": str(OUT_PATH.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
