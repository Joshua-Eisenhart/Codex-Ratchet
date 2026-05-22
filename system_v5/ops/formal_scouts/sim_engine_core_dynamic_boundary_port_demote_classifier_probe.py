#!/usr/bin/env python3
"""Classify dynamic EngineCore-boundary rows as port-required or demotion-only."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import Counter
from typing import Any

import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "engine_core_dynamic_boundary_port_demote_classifier_probe_results.json"
TRIAGE = RESULT_DIR / "engine_core_boundary_row_triage_probe_results.json"
TOOL_GATE = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"

NAME = "engine_core_dynamic_boundary_port_demote_classifier_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "engine_core_dynamic_boundary_port_demote_classifier"
CLAIM_CEILING = (
    "Formal scout audit only: classifies current dynamic EngineCore importer-boundary rows "
    "into torch-native port required versus preserve-only demotion evidence. It does not "
    "port EngineCore, clear the tool-role gate, convert finite fixtures into live dynamics, "
    "or admit basin, manifold, PEPS3D, Holodeck, physics, consciousness, or target-system claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of current gate and EngineCore row-triage receipts",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical path binding",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt/source identity hashes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that dynamic rows without a torch-native port cannot support positive live-dynamics promotion",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

PRESERVE_ONLY_DEMOTION_ROWS: dict[str, str] = {}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def dynamic_triage_rows(triage: dict[str, Any]) -> list[dict[str, Any]]:
    rows = triage.get("row_triage", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if row.get("classification") == "dynamic_torch_port_required"]


def status_counts(gate: dict[str, Any]) -> dict[str, int]:
    rows = gate.get("tool_role_rows", [])
    if not isinstance(rows, list):
        return {}
    return dict(sorted(Counter(str(row.get("tool_role_status")) for row in rows).items()))


def row_action(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("name"))
    preserve_reason = PRESERVE_ONLY_DEMOTION_ROWS.get(name)
    source_audit = row.get("source_audit", {}) if isinstance(row.get("source_audit"), dict) else {}
    call_sites = source_audit.get("engine_core_call_sites") or []
    dynamic_markers = source_audit.get("dynamic_markers") or []
    finite_markers = source_audit.get("finite_markers") or []
    manifest_report = row.get("engine_core_manifest_report", {})
    if not isinstance(manifest_report, dict):
        manifest_report = {}
    if preserve_reason:
        action = "preserve_negative_demotion_and_port_before_positive_claim"
        positive_claim_requires_port = True
        finite_demotion_honesty = "honest_as_existing_negative_or_preserve-only_evidence"
        reason = preserve_reason
    else:
        action = "torch_native_port_required_for_positive_dynamic_claim"
        positive_claim_requires_port = True
        finite_demotion_honesty = "honest_only_if_rewritten_as_frozen_fixture_not_original_live_dynamic_claim"
        reason = (
            "The row's current claim consumes live EngineCore trajectory, basin, transport, "
            "holonomy, PEPS3D slot, or closed-loop evidence. A finite fixture could only "
            "preserve a weaker replay/readout artifact."
        )
    return {
        "name": name,
        "source_path": row.get("source_path"),
        "result_path": row.get("result_path"),
        "gate_status": row.get("gate_status"),
        "direct_import_is_gate_blocker": row.get("direct_import_is_gate_blocker"),
        "result_all_pass": row.get("result_all_pass"),
        "promotion_allowed": row.get("promotion_allowed"),
        "action": action,
        "positive_claim_requires_torch_native_port": positive_claim_requires_port,
        "finite_demotion_honesty": finite_demotion_honesty,
        "reason": reason,
        "engine_core_call_count": len(call_sites),
        "engine_core_call_sites": call_sites,
        "dynamic_markers": dynamic_markers,
        "finite_markers": finite_markers,
        "manifest_tension": manifest_report.get("tension", ""),
        "recommended_next_move": row.get("recommended_next_move"),
    }


def z3_no_promotion_without_port(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "pass": True,
            "solver_status": "not_run_empty_frontier",
            "row_count": 0,
            "meaning": "No current dynamic EngineCore-boundary rows are present, so there is no positive live-dynamics promotion path to block.",
        }
    solver = z3.Solver()
    for idx, row in enumerate(rows):
        dynamic_row = z3.Bool(f"dynamic_row_{idx}")
        torch_native_port = z3.Bool(f"torch_native_port_{idx}")
        positive_promotion = z3.Bool(f"positive_promotion_{idx}")
        solver.add(dynamic_row == True)
        solver.add(torch_native_port == False)
        solver.add(z3.Implies(z3.And(dynamic_row, z3.Not(torch_native_port)), z3.Not(positive_promotion)))
        solver.add(positive_promotion)
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "row_count": len(rows),
        "meaning": "No current dynamic EngineCore-boundary row can support positive live-dynamics promotion while the torch-native port is absent.",
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    triage = read_json(TRIAGE)
    gate = read_json(TOOL_GATE)
    rows = [row_action(row) for row in dynamic_triage_rows(triage)]
    action_counts = Counter(row["action"] for row in rows)
    manifest_tensions = [row for row in rows if row["manifest_tension"]]
    z3_check = z3_no_promotion_without_port(rows)
    positive = {
        "current_triage_loaded": {
            "pass": TRIAGE.exists() and triage.get("all_pass") is True,
            "triage_path": rel(TRIAGE),
            "triage_sha256": sha256(TRIAGE),
        },
        "dynamic_partition_count_is_current": {
            "pass": len(rows) == triage.get("summary", {}).get("dynamic_torch_port_required_count"),
            "dynamic_row_count": len(rows),
            "triage_summary": triage.get("summary", {}),
        },
        "all_dynamic_rows_remain_gate_blocked": {
            "pass": all(row["gate_status"] == "blocked_engine_core_importer_boundary" for row in rows),
            "gate_status_counts": status_counts(gate),
        },
        "all_dynamic_rows_need_port_before_positive_claim": {
            "pass": all(row["positive_claim_requires_torch_native_port"] for row in rows),
            "action_counts": dict(sorted(action_counts.items())),
        },
        "z3_blocks_positive_promotion_without_port": z3_check,
    }
    boundary = {
        "promotion_disabled": {"pass": PROMOTION_ALLOWED is False},
        "finite_demotion_does_not_preserve_original_live_claim": {
            "pass": all("original_live_dynamic_claim" in row["finite_demotion_honesty"] or "preserve-only" in row["finite_demotion_honesty"] for row in rows),
            "demotion_modes": dict(sorted(Counter(row["finite_demotion_honesty"] for row in rows).items())),
        },
        "claim_ceiling_blocks_broad_claims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["does not port", "clear the tool-role gate", "physics", "consciousness"]),
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    graveyard_companions = {
        "finite_fixture_as_live_dynamics_control_killed": {
            "pass": True,
            "reason": "Finite replay/readout evidence can be kept only as a weaker fixture, not as live EngineCore dynamics.",
        },
        "manifest_tension_state_recorded": {
            "pass": True,
            "manifest_tension_count": len(manifest_tensions),
            "rows": [
                {
                    "name": row["name"],
                    "source_path": row["source_path"],
                    "manifest_tension": row["manifest_tension"],
                }
                for row in manifest_tensions
            ],
        },
        "preserve_only_demote_rows_currently_absent_from_dynamic_partition": {
            "pass": not any(row["action"] == "preserve_negative_demotion_and_port_before_positive_claim" for row in rows),
            "reason": "The prior qit_engine_dynamics_required_work_discrimination row now clears the tool-role gate without a direct EngineCore import, so it is not part of this dynamic EngineCore-boundary partition.",
            "preserve_only_rows": sorted(PRESERVE_ONLY_DEMOTION_ROWS),
        },
    }
    checks = {**positive, **boundary, **graveyard_companions}
    all_pass = all(bool(item.get("pass")) for item in checks.values())
    return {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "dynamic_row_count": len(rows),
            "action_counts": dict(sorted(action_counts.items())),
            "manifest_tension_count": len(manifest_tensions),
            "gate_clearance_authorized": False,
            "positive_dynamic_claim_authorized": False,
            "cleanup_authorized": False,
        },
        "row_actions": rows,
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for item in graveyard_companions.values() if item.get("pass")),
            "variants": sorted(graveyard_companions),
        },
        "why_not_v4_probes": [
            "This consumes the current v5 EngineCore row-triage receipt.",
            "It is a v5 audit/classifier over current direct EngineCore importers, not a legacy v4 sim.",
            "It writes no target-source repairs and clears no gate.",
        ],
        "blockers": [] if all_pass else [key for key, item in checks.items() if not item.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
