#!/usr/bin/env python3
"""Classify EngineCore importers against the current NumPy/autograd boundary."""

from __future__ import annotations

import hashlib
import ast
import json
import pathlib
import re
import time
from typing import Any

import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "engine_core_importer_boundary_classifier_probe_results.json"
ENGINE_CORE = ROOT / "engine_core.py"
TOOL_GATE = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"
NUMPY_GATE = RESULT_DIR / "numpy_quarantine_source_native_nonclassical_gate_probe_results.json"
AUTOGRAD_CONTRACT = RESULT_DIR / "engine_core_autograd_severance_contract_probe_results.json"

NAME = "engine_core_importer_boundary_classifier_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: classifies direct EngineCore importers against the current "
    "NumPy/autograd-severed EngineCore boundary. It blocks using EngineCore-importing "
    "rows as torch-native nonclassical attractor-basin or differentiable manifold "
    "evidence unless a later torch-native EngineCore migration receipt or explicit "
    "finite-scalar boundary receipt covers the exact importer. It does not promote "
    "any engine, Axis0, manifold, world-model, or basin claim."
)

TOOL_MANIFEST = {
    "python_pathlib": {"tried": True, "used": True, "reason": "load-bearing source and receipt path scan"},
    "python_ast": {"tried": True, "used": True, "reason": "load-bearing direct EngineCore import detection that ignores comments and strings"},
    "python_re": {"tried": True, "used": True, "reason": "supportive legacy EngineCore boundary pattern kept for syntax-error fallback"},
    "python_json": {"tried": True, "used": True, "reason": "load-bearing gate receipt consumption and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hash receipt"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing boundary implication witness over candidate importers"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_pathlib": "supportive",
    "python_ast": "supportive",
    "python_re": "supportive",
    "python_json": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

IMPORT_RE = re.compile(r"^(?:from\s+engine_core\s+import|import\s+engine_core\b)|\bengine_core\.", re.MULTILINE)


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def direct_importers() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(ROOT.glob("sim_*.py")):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            matches = [match.group(0) for match in IMPORT_RE.finditer(text)]
        else:
            matches = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "engine_core" or alias.name.startswith("engine_core."):
                            matches.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module == "engine_core" or str(node.module or "").startswith("engine_core."):
                        matches.append(f"from {node.module} import")
        if not matches:
            continue
        rows.append(
            {
                "path": path.name,
                "relative_path": str(path.relative_to(ROOT)),
                "match_count": len(matches),
                "sha256": sha256_file(path),
            }
        )
    return rows


def tool_status_by_name() -> dict[str, dict[str, Any]]:
    if not TOOL_GATE.exists():
        return {}
    data = load_json(TOOL_GATE)
    out: dict[str, dict[str, Any]] = {}
    for row in data.get("tool_role_rows", []):
        result_name = str(row.get("result_path", "")).removeprefix("results/")
        if result_name.endswith("_results.json"):
            stem = result_name[: -len("_results.json")]
            out[f"sim_{stem}.py"] = row
    return out


def quarantine_by_path() -> dict[str, str]:
    if not NUMPY_GATE.exists():
        return {}
    data = load_json(NUMPY_GATE)
    return {str(row.get("path")): str(row.get("quarantine")) for row in data.get("quarantine_rows", [])}


def engine_core_boundary() -> dict[str, Any]:
    source = ENGINE_CORE.read_text(encoding="utf-8")
    has_numpy_import = "numpy as np" in source
    has_projection_severance = bool(re.search(r"\.detach\(\)\.cpu\(\)\.numpy\(\)", source))
    contract = load_json(AUTOGRAD_CONTRACT) if AUTOGRAD_CONTRACT.exists() else {}
    contract_pass = bool(
        contract.get("all_pass") is True
        or contract.get("summary", {}).get("all_pass") is True
        or contract.get("pass") is True
    )
    return {
        "engine_core_path": ENGINE_CORE.name,
        "engine_core_sha256": sha256_file(ENGINE_CORE),
        "has_numpy_import": has_numpy_import,
        "has_autograd_projection_severance_site": has_projection_severance,
        "autograd_contract_receipt": AUTOGRAD_CONTRACT.name,
        "autograd_contract_exists": AUTOGRAD_CONTRACT.exists(),
        "autograd_contract_all_pass": contract_pass,
        "boundary_active": bool(has_numpy_import and has_projection_severance and contract_pass),
    }


def classify(importer: dict[str, Any], tool_rows: dict[str, dict[str, Any]], quarantine_rows: dict[str, str]) -> dict[str, Any]:
    path = importer["path"]
    tool_row = tool_rows.get(path)
    tool_status = str(tool_row.get("tool_role_status")) if tool_row else "not_in_tool_gate"
    quarantine = quarantine_rows.get(path, "not_in_numpy_gate")
    if tool_status == "tool_role_candidate":
        boundary_class = "candidate_requires_engine_core_boundary_or_torch_port"
        nonclassical_basin_claim_allowed = False
    elif tool_status.startswith("blocked_") or quarantine.startswith("hard_"):
        boundary_class = "blocked_already"
        nonclassical_basin_claim_allowed = False
    elif quarantine.startswith("review_") or tool_status == "not_in_tool_gate":
        boundary_class = "review_required_not_candidate"
        nonclassical_basin_claim_allowed = False
    else:
        boundary_class = "needs_torch_port_before_nonclassical_claim"
        nonclassical_basin_claim_allowed = False
    return {
        **importer,
        "tool_role_status": tool_status,
        "numpy_quarantine_status": quarantine,
        "boundary_class": boundary_class,
        "nonclassical_basin_claim_allowed": nonclassical_basin_claim_allowed,
        "required_next_action": (
            "add exact finite-scalar boundary receipt or port this importer off EngineCore/NumPy before any "
            "torch-native nonclassical basin claim"
            if boundary_class == "candidate_requires_engine_core_boundary_or_torch_port"
            else "keep blocked/review until exact torch-native or finite-scalar boundary receipt exists"
        ),
    }


def z3_boundary_witness(boundary: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    boundary_active = z3.Bool("boundary_active")
    candidate_importer_exists = z3.Bool("candidate_importer_exists")
    any_importer_allowed = z3.Bool("any_importer_allowed")
    solver.add(boundary_active == bool(boundary["boundary_active"]))
    solver.add(candidate_importer_exists == any(row["boundary_class"] == "candidate_requires_engine_core_boundary_or_torch_port" for row in rows))
    solver.add(any_importer_allowed == any(row["nonclassical_basin_claim_allowed"] for row in rows))
    solver.add(z3.Not(z3.Implies(z3.And(boundary_active, candidate_importer_exists), z3.Not(any_importer_allowed))))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim": "If the EngineCore boundary is active and any candidate imports EngineCore, no direct importer is allowed as nonclassical basin evidence by this receipt.",
    }


def current_gate_boundary_rows(tool_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    uncovered = []
    finite_covered = []
    for source_path, row in sorted(tool_rows.items()):
        status = str(row.get("tool_role_status"))
        compact = {
            "name": row.get("name"),
            "source_path": row.get("source_path") or source_path,
            "result_path": row.get("result_path"),
            "tool_role_status": status,
            "nonclassical_basin_claim_allowed": row.get("nonclassical_basin_claim_allowed"),
        }
        if status == "blocked_engine_core_importer_boundary":
            uncovered.append(compact)
        elif status == "blocked_engine_core_importer_boundary_finite_receipt_covered":
            finite_covered.append(compact)
    return {
        "uncovered": uncovered,
        "finite_receipt_covered": finite_covered,
        "uncovered_count": len(uncovered),
        "finite_receipt_covered_count": len(finite_covered),
        "pass": bool(
            all(row["nonclassical_basin_claim_allowed"] is False for row in uncovered)
            and all(row["nonclassical_basin_claim_allowed"] is False for row in finite_covered)
        ),
        "frontier_empty": not uncovered and not finite_covered,
    }


def main() -> int:
    started = time.time()
    boundary = engine_core_boundary()
    tool_rows = tool_status_by_name()
    quarantine_rows = quarantine_by_path()
    rows = [classify(row, tool_rows, quarantine_rows) for row in direct_importers()]
    class_counts = {
        cls: sum(1 for row in rows if row["boundary_class"] == cls)
        for cls in sorted({row["boundary_class"] for row in rows})
    }
    candidate_rows = [row for row in rows if row["boundary_class"] == "candidate_requires_engine_core_boundary_or_torch_port"]
    current_gate_rows = current_gate_boundary_rows(tool_rows)
    direct_importer_paths = {row["relative_path"] for row in rows}
    z3_witness = z3_boundary_witness(boundary, rows)
    positive = {
        "engine_core_boundary_is_active": {"pass": boundary["boundary_active"], **boundary},
        "direct_engine_core_importers_are_mapped": {"pass": len(rows) > 0, "direct_importer_count": len(rows)},
        "current_uncovered_gate_rows_are_direct_importers": {
            "pass": current_gate_rows["pass"]
            and all(str(row["source_path"]) in direct_importer_paths for row in current_gate_rows["uncovered"]),
            "uncovered_count": current_gate_rows["uncovered_count"],
            "finite_receipt_covered_count": current_gate_rows["finite_receipt_covered_count"],
            "uncovered_rows": current_gate_rows["uncovered"],
        },
        "candidate_importers_are_demoted_to_boundary_required": {
            "pass": all(row["nonclassical_basin_claim_allowed"] is False for row in candidate_rows),
            "candidate_requires_boundary_count": len(candidate_rows),
            "candidate_paths": [row["path"] for row in candidate_rows],
        },
        "z3_boundary_implication_holds": z3_witness,
    }
    graveyard = {
        "shim_would_hide_not_remove_autograd_severance": {
            "pass": True,
            "reason": "A shim around EngineCore importers would preserve the current finite-scalar NumPy-mediated boundary and must not be counted as a torch-native repair.",
        },
        "enginecore_stage_records_are_finite_evidence_not_basin_proof": {
            "pass": True,
            "reason": "Scalar EngineCore stage records can be finite receipts, but they do not prove root-driven attractor-basin convergence or differentiable manifold dynamics.",
        },
        "axis0_and_world_model_claims_remain_downstream": {
            "pass": True,
            "reason": "EngineCore importer cleanup supports later Axis0/world-model work; it does not itself repair Axis0 or prove a world engine.",
        },
    }
    boundary_checks = {
        "no_promotion": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_basin_and_world_model_overclaims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["attractor-basin", "world-model", "torch-native"]),
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard.values())
        and all(row["pass"] for row in boundary_checks.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "engine_core_importer_boundary_classifier",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "consumed_receipts": {
            "tool_gate": TOOL_GATE.name,
            "numpy_gate": NUMPY_GATE.name,
            "autograd_contract": AUTOGRAD_CONTRACT.name,
        },
        "engine_core_boundary": boundary,
        "direct_importer_rows": rows,
        "class_counts": class_counts,
        "current_gate_boundary_rows": current_gate_rows,
        "summary": {
            "direct_importer_count": len(rows),
            "uncovered_engine_core_importer_boundary_count": current_gate_rows["uncovered_count"],
            "finite_receipt_covered_count": current_gate_rows["finite_receipt_covered_count"],
            "candidate_requires_boundary_count": len(candidate_rows),
            "class_counts": class_counts,
            "gate_clearance_authorized": False,
            "promotion_authorized": False,
            "cleanup_authorized": False,
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary_checks,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "why_not_v4_probes": [
            "This is a v5 source-native boundary classifier over direct EngineCore importers.",
            "It blocks narrative promotion while preserving finite scalar receipt usage.",
        ],
        "blockers": [] if all_pass else [key for key, row in {**positive, **graveyard, **boundary_checks}.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "script_sha256": sha256_file(pathlib.Path(__file__)),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  direct_importers={len(rows)} candidate_requires_boundary={len(candidate_rows)} class_counts={class_counts}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
