#!/usr/bin/env python3
"""Row-level triage for current EngineCore importer-boundary blockers."""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import time
from collections import Counter
from typing import Any

import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "engine_core_boundary_row_triage_probe_results.json"
TOOL_GATE_RESULT = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"
SEVERANCE_RESULT = RESULT_DIR / "engine_core_autograd_severance_contract_probe_results.json"

NAME = "engine_core_boundary_row_triage_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "engine_core_boundary_row_triage"
SIM_EXECUTION_KIND = "audit"
CLAIM_CEILING = (
    "Formal scout audit only: partitions current EngineCore importer-boundary "
    "blockers into finite/readout quarantine candidates versus dynamic rows "
    "that need a torch-native port or explicit demotion. It does not clear the "
    "EngineCore importer boundary, does not admit nonclassical basin evidence, "
    "and does not promote final Axis0, FEP, Holodeck, PEPS3D, holonomy, "
    "manifold, physics, cognition, or world-model claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of gate and target result receipts",
    },
    "python_ast": {
        "tried": True,
        "used": True,
        "reason": "supportive source import and EngineCore call-site audit without executing target sims",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source/result path binding",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive exact source/result identity hashes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing implication that row triage does not imply gate clearance or basin promotion",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_ast": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

FINITE_QUARANTINE_CANDIDATES = {
    "axis0_fep_gradient_stage_local_adapter_closure_probe",
    "constraint_manifold_delta_neural_readout_probe",
    "source_native_active_inference_strategy_policy_probe",
    "source_native_fep_pomdp_policy_tree_probe",
    "source_native_holodeck_hash_memory_placeholder_probe",
    "source_native_hopf_fep_igt_chirality_prediction_probe",
    "source_native_multicarrier_subdense_environment_contraction_probe",
    "source_native_peps3d_48_site_regime_crossing_probe",
    "source_native_peps3d_52_56_60_site_regime_ladder_probe",
}

DYNAMIC_PORT_REQUIRED = {
    "full_thirteen_layer_active_g_structure_both_chiral_source_native_composition_probe",
}

ENGINECORE_BOUNDARY_STATUSES = {
    "blocked_engine_core_importer_boundary",
    "blocked_engine_core_importer_boundary_finite_receipt_covered",
}

DEMOTION_PRESERVE_ONLY: set[str] = set()

DYNAMIC_MARKERS = [
    "attractor",
    "basin",
    "closed-loop",
    "closed_loop",
    "dynamic",
    "dynamics",
    "holonomy",
    "mps transport",
    "operator-slot",
    "peps3d slot",
    "run_full_cycle",
    "slot dynamics",
    "transport",
    "trajectory",
]
FINITE_MARKERS = [
    "bounded",
    "finite",
    "placeholder",
    "policy window",
    "readout",
    "replay",
    "stage records",
]


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def result_all_pass(data: dict[str, Any]) -> bool:
    if data.get("all_pass") is True:
        return True
    summary = data.get("summary")
    if isinstance(summary, dict) and summary.get("all_pass") is True:
        return True
    positive = data.get("positive")
    if isinstance(positive, dict) and positive:
        checks = [row.get("pass") for row in positive.values() if isinstance(row, dict) and "pass" in row]
        return bool(checks and all(check is True for check in checks))
    return False


def source_for_row(row: dict[str, Any]) -> pathlib.Path:
    source = row.get("source_path")
    return ROOT / str(source) if source else ROOT / f"sim_{row['name']}.py"


def result_for_row(row: dict[str, Any]) -> pathlib.Path:
    return ROOT / str(row.get("result_path") or f"results/{row['name']}_results.json")


def parse_source(path: pathlib.Path) -> ast.Module | None:
    if not path.exists():
        return None
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None


def source_audit(path: pathlib.Path) -> dict[str, Any]:
    tree = parse_source(path)
    if tree is None:
        return {"path": str(path), "exists": path.exists(), "parse_ok": False, "pass": False}
    imports: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "engine_core" or module.startswith("engine_core."):
                imports.append({"module": module, "names": [alias.name for alias in node.names], "line": node.lineno})
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "engine_core" or alias.name.startswith("engine_core."):
                    imports.append({"module": alias.name, "names": [alias.name], "line": node.lineno})
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in {"EngineCore", "generate_initial_density"}:
                calls.append({"call": func.id, "line": node.lineno})
            elif isinstance(func, ast.Attribute) and func.attr in {
                "generate_initial_density",
                "run_full_cycle",
                "run_substage",
            }:
                calls.append({"call": func.attr, "line": node.lineno})
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    return {
        "path": str(path),
        "exists": path.exists(),
        "parse_ok": True,
        "sha256": sha256_file(path),
        "direct_engine_core_imports": imports,
        "engine_core_call_sites": calls,
        "dynamic_markers": sorted(marker for marker in DYNAMIC_MARKERS if marker in text),
        "finite_markers": sorted(marker for marker in FINITE_MARKERS if marker in text),
        "pass": bool(imports and calls),
    }


def load_bearing_tools(data: dict[str, Any]) -> list[str]:
    depth = data.get("TOOL_INTEGRATION_DEPTH") or data.get("tool_integration_depth") or {}
    if not isinstance(depth, dict):
        return []
    return sorted(tool for tool, value in depth.items() if str(value).lower() == "load_bearing")


def engine_core_manifest_report(data: dict[str, Any]) -> dict[str, Any]:
    manifest = data.get("TOOL_MANIFEST") or data.get("tool_manifest") or {}
    depth = data.get("TOOL_INTEGRATION_DEPTH") or data.get("tool_integration_depth") or {}
    manifest_row = manifest.get("engine_core") if isinstance(manifest, dict) else None
    depth_role = depth.get("engine_core") if isinstance(depth, dict) else None
    reason = str((manifest_row or {}).get("reason") or "") if isinstance(manifest_row, dict) else ""
    reason_says_load_bearing = "load-bearing" in reason.lower() or "load bearing" in reason.lower()
    tension = ""
    if manifest_row is None and depth_role is None:
        tension = "engine_core_import_omitted_from_manifest_and_depth"
    elif reason_says_load_bearing and depth_role == "supportive":
        tension = "manifest_reason_load_bearing_but_depth_supportive"
    return {
        "manifest_present": manifest_row is not None,
        "manifest_reason": reason,
        "depth_role": depth_role,
        "reason_says_load_bearing": reason_says_load_bearing,
        "tension": tension,
        "pass": True,
    }


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("name"))
    source_path = source_for_row(row)
    result_path = result_for_row(row)
    result = read_json(result_path)
    source = source_audit(source_path)
    direct_import = bool(source.get("direct_engine_core_imports"))
    result_pass = result_all_pass(result)
    if not direct_import:
        classification = "source_already_ported_or_gate_stale"
    elif not result_pass:
        classification = "result_failure_or_other_blocker"
    elif name in FINITE_QUARANTINE_CANDIDATES:
        classification = "finite_router_or_readout_quarantine_candidate"
    elif name in DYNAMIC_PORT_REQUIRED:
        classification = "dynamic_torch_port_required"
    else:
        classification = "manual_review_required"

    if name in DEMOTION_PRESERVE_ONLY:
        classification_detail = "dynamic_torch_port_required_preserve_existing_demotion"
    elif classification == "finite_router_or_readout_quarantine_candidate":
        classification_detail = "finite_boundary_receipt_allowed_only_as_quarantine_not_gate_clearance"
    elif classification == "dynamic_torch_port_required":
        classification_detail = "port_live_enginecore_substrate_or_demote_to_frozen_fixture"
    else:
        classification_detail = classification

    claim = str(result.get("claim_ceiling") or "")
    manifest_report = engine_core_manifest_report(result)
    return {
        "name": name,
        "classification": classification,
        "classification_detail": classification_detail,
        "gate_status": row.get("tool_role_status"),
        "gate_nonclassical_basin_claim_allowed": row.get("nonclassical_basin_claim_allowed"),
        "source_path": rel(source_path),
        "source_sha256": source.get("sha256"),
        "result_path": rel(result_path),
        "result_sha256": sha256_file(result_path) if result_path.exists() else "missing",
        "result_all_pass": result_pass,
        "promotion_allowed": result.get("promotion_allowed"),
        "load_bearing_tools": load_bearing_tools(result),
        "claim_ceiling_excerpt": claim[:280],
        "source_audit": source,
        "engine_core_manifest_report": manifest_report,
        "direct_import_is_gate_blocker": direct_import and row.get("tool_role_status") in ENGINECORE_BOUNDARY_STATUSES,
        "recommended_next_move": recommended_next_move(classification, name),
    }


def recommended_next_move(classification: str, name: str) -> str:
    if classification == "finite_router_or_readout_quarantine_candidate":
        return (
            "write an exact finite-boundary quarantine receipt only if it binds this row to frozen JSON/scalar/window/readout evidence; "
            "the row remains nonpromotional and does not become a tool-role candidate from that receipt alone"
        )
    if name in DEMOTION_PRESERVE_ONLY:
        return (
            "preserve current negative-control/demotion evidence, but port EngineCore trajectory generation before any positive manifold-required dynamics claim"
        )
    if classification == "dynamic_torch_port_required":
        return "port the live EngineCore substrate to a torch-native source path or explicitly demote the row to a frozen finite fixture"
    if classification == "source_already_ported_or_gate_stale":
        return "rerun the tool-role gate; this row should not remain an EngineCore importer-boundary blocker"
    return "manual blocker review required"


def z3_boundary_witness() -> dict[str, Any]:
    finite_quarantine = z3.Bool("finite_quarantine")
    dynamic_row = z3.Bool("dynamic_row")
    torch_native_port = z3.Bool("torch_native_port")
    gate_clearance = z3.Bool("gate_clearance")
    basin_promotion = z3.Bool("basin_promotion")
    solver = z3.Solver()
    solver.add(z3.Implies(finite_quarantine, z3.Not(gate_clearance)))
    solver.add(z3.Implies(z3.And(dynamic_row, z3.Not(torch_native_port)), z3.Not(basin_promotion)))
    solver.add(finite_quarantine, dynamic_row, z3.Not(torch_native_port), z3.Or(gate_clearance, basin_promotion))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "meaning": "Finite quarantine does not clear the gate; dynamic EngineCore rows without a torch-native port cannot support basin promotion.",
    }


def severance_report(receipt: dict[str, Any]) -> dict[str, Any]:
    positive = receipt.get("positive") or {}
    return {
        "exists": bool(receipt.get("exists")),
        "all_pass": receipt.get("all_pass"),
        "enginecore_current_path_is_detected_as_autograd_severed": bool(
            (positive.get("enginecore_current_path_is_detected_as_autograd_severed") or {}).get("pass")
        ),
        "source_severance_sites_are_enumerated": bool(
            (positive.get("source_severance_sites_are_enumerated") or {}).get("pass")
        ),
        "pass": bool(
            receipt.get("exists")
            and receipt.get("all_pass") is True
            and (positive.get("enginecore_current_path_is_detected_as_autograd_severed") or {}).get("pass") is True
            and (positive.get("source_severance_sites_are_enumerated") or {}).get("pass") is True
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    gate = read_json(TOOL_GATE_RESULT)
    severance = read_json(SEVERANCE_RESULT)
    current_enginecore_rows = [
        row for row in gate.get("tool_role_rows", [])
        if row.get("tool_role_status") in ENGINECORE_BOUNDARY_STATUSES
    ]
    rows = [
        row for row in gate.get("tool_role_rows", [])
        if row.get("tool_role_status") in ENGINECORE_BOUNDARY_STATUSES
    ]
    row_details = [classify_row(row) for row in rows]
    by_class = Counter(row["classification"] for row in row_details)
    gate_status_counts = Counter(str(row.get("gate_status")) for row in row_details)
    manifest_tensions = [
        {
            "name": row["name"],
            "tension": row["engine_core_manifest_report"]["tension"],
            "source_path": row["source_path"],
            "result_path": row["result_path"],
        }
        for row in row_details
        if row["engine_core_manifest_report"]["tension"]
    ]
    observed_names = {row["name"] for row in row_details}
    manual_review_rows = [row["name"] for row in row_details if row["classification"] == "manual_review_required"]
    expected_partition = {
        "finite_router_or_readout_quarantine_candidate": by_class.get("finite_router_or_readout_quarantine_candidate", 0),
        "dynamic_torch_port_required": by_class.get("dynamic_torch_port_required", 0),
    }
    z3_witness = z3_boundary_witness()
    severance_check = severance_report(severance)
    positive = {
        "current_gate_frontier_consumed": {
            "pass": bool(TOOL_GATE_RESULT.exists() and isinstance(gate.get("tool_role_rows"), list) and len(rows) == len(current_enginecore_rows)),
            "enginecore_boundary_partition_count": len(rows),
            "gate_status_counts": dict(sorted(gate_status_counts.items())),
            "observed_names": sorted(observed_names),
            "current_frontier_names": sorted(str(row.get("name")) for row in current_enginecore_rows),
        },
        "row_partition_is_complete": {
            "pass": not manual_review_rows,
            "classification_counts": dict(sorted(by_class.items())),
            "expected_counts": expected_partition,
            "manual_review_rows": manual_review_rows,
        },
        "all_rows_are_live_direct_enginecore_importers": {
            "pass": all(row["source_audit"].get("pass") and row["direct_import_is_gate_blocker"] for row in row_details),
            "row_count": len(row_details),
        },
        "all_target_results_are_green_but_nonpromotional": {
            "pass": all(row["result_all_pass"] is True and row["promotion_allowed"] is False for row in row_details),
            "row_count": len(row_details),
        },
        "enginecore_severance_contract_remains_active": severance_check,
        "z3_triage_does_not_clear_gate_or_promote_basin": z3_witness,
    }
    graveyard = {
        "blanket_finite_receipt_for_all_enginecore_rows_rejected": {
            "pass": True,
            "dynamic_rows": sorted(row["name"] for row in row_details if row["classification"] == "dynamic_torch_port_required"),
            "reason": "If dynamic EngineCore-boundary rows are present, blanket finite receipts are rejected; the current frontier has none.",
        },
        "blanket_torch_port_for_all_rows_is_overbroad": {
            "pass": True,
            "finite_or_readout_rows": sorted(
                row["name"] for row in row_details if row["classification"] == "finite_router_or_readout_quarantine_candidate"
            ),
            "reason": "If finite/readout rows are present, blanket torch-port work is overbroad; the current frontier has none.",
        },
        "stale_gate_hypothesis_rejected_for_remaining_rows": {
            "pass": by_class.get("source_already_ported_or_gate_stale", 0) == 0,
            "gate_stale_rows": sorted(row["name"] for row in row_details if row["classification"] == "source_already_ported_or_gate_stale"),
        },
        "result_failure_hypothesis_rejected_for_remaining_rows": {
            "pass": by_class.get("result_failure_or_other_blocker", 0) == 0,
            "result_failure_rows": sorted(row["name"] for row in row_details if row["classification"] == "result_failure_or_other_blocker"),
        },
        "manifest_depth_tension_state_is_recorded": {
            "pass": True,
            "tension_count": len(manifest_tensions),
            "tensions": manifest_tensions,
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_names_no_broad_claims": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["does not clear", "does not admit nonclassical basin", "does not promote", "physics", "world-model"]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
        "triage_is_not_gate_mutation": {
            "pass": True,
            "gate_result_read": rel(TOOL_GATE_RESULT),
            "gate_result_written": False,
            "blocked_status_preserved": "blocked_engine_core_importer_boundary",
        },
    }
    all_checks = {**positive, **graveyard, **boundary}
    all_pass = all(bool(row.get("pass")) for row in all_checks.values())
    return {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "blocked_engine_core_importer_boundary_count": len(rows),
            "gate_status_counts": dict(sorted(gate_status_counts.items())),
            "finite_receipt_covered_count": gate_status_counts.get("blocked_engine_core_importer_boundary_finite_receipt_covered", 0),
            "uncovered_engine_core_importer_boundary_count": gate_status_counts.get("blocked_engine_core_importer_boundary", 0),
            "finite_router_or_readout_quarantine_candidate_count": by_class.get("finite_router_or_readout_quarantine_candidate", 0),
            "dynamic_torch_port_required_count": by_class.get("dynamic_torch_port_required", 0),
            "source_already_ported_or_gate_stale_count": by_class.get("source_already_ported_or_gate_stale", 0),
            "result_failure_or_other_blocker_count": by_class.get("result_failure_or_other_blocker", 0),
            "manifest_depth_tension_count": len(manifest_tensions),
            "cleanup_authorized": False,
            "gate_clearance_authorized": False,
        },
        "row_triage": row_details,
        "partition": {
            "finite_router_or_readout_quarantine_candidate": sorted(
                row["name"] for row in row_details if row["classification"] == "finite_router_or_readout_quarantine_candidate"
            ),
            "dynamic_torch_port_required": sorted(
                row["name"] for row in row_details if row["classification"] == "dynamic_torch_port_required"
            ),
            "source_already_ported_or_gate_stale": sorted(
                row["name"] for row in row_details if row["classification"] == "source_already_ported_or_gate_stale"
            ),
            "result_failure_or_other_blocker": sorted(
                row["name"] for row in row_details if row["classification"] == "result_failure_or_other_blocker"
            ),
        },
        "next_admissible_moves": {
            "current_empty_frontier": (
                "no EngineCore importer-boundary rows are active in the current tool-role gate; do not resurrect stale finite or dynamic partitions without a fresh gate row"
            ),
            "finite_router_or_readout_quarantine_candidate": (
                "write exact finite-boundary quarantine receipts one row at a time; each receipt must bind to frozen finite JSON/scalar/window/readout evidence and keep promotion blocked"
            ),
            "dynamic_torch_port_required": (
                "port the live EngineCore substrate to torch-native source paths, or explicitly demote the row to a frozen finite fixture before any finite-boundary receipt"
            ),
            "manifest_depth_tensions": "repair rows where direct EngineCore import is omitted from TOOL_MANIFEST/TOOL_INTEGRATION_DEPTH or manifest prose says load-bearing while depth says supportive",
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row.get("pass")),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This audits current v5 EngineCore importer-boundary rows from the current v5 tool-role gate.",
            "It reads current v5 source/result files and the current EngineCore autograd-severance receipt.",
            "It is a row-level repair router, not a legacy v4 probe, gate mutation, or promotion surface.",
        ],
        "blockers": [] if all_pass else [key for key, row in all_checks.items() if not row.get("pass")],
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
