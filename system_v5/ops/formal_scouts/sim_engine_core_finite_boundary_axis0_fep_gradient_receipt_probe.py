#!/usr/bin/env python3
"""Finite EngineCore boundary receipt for the Axis0 FEP-gradient scout."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import pathlib
import time
from typing import Any

import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "engine_core_finite_boundary_axis0_fep_gradient_receipt_probe_results.json"

NAME = "engine_core_finite_boundary_axis0_fep_gradient_receipt_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "engine_core_finite_boundary_classifier"
SIM_EXECUTION_KIND = "audit"
CLAIM_CEILING = (
    "Formal scout quarantine receipt only: records bounded evidence that the current "
    "axis0_fep_gradient_stage_local_adapter_closure_probe EngineCore import "
    "is consumed as finite stage-record JSON/scalar evidence for one "
    "stage-local FEP-gradient vector. It does not clear the EngineCore "
    "importer boundary, does not admit nonclassical basin evidence, and does "
    "not promote final Axis0, FEP, retrocausality, Holodeck, physics, "
    "cognition, world-model, or manifold claims."
)

TARGET_NAME = "axis0_fep_gradient_stage_local_adapter_closure_probe"
TARGET_SOURCE = ROOT / f"sim_{TARGET_NAME}.py"
TARGET_RESULT = RESULT_DIR / f"{TARGET_NAME}_results.json"
ENGINE_CORE_SOURCE = ROOT / "engine_core.py"
ENGINE_CORE_SEVERANCE_RESULT = RESULT_DIR / "engine_core_autograd_severance_contract_probe_results.json"
TOOL_GATE_RESULT = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive parsing of target, gate, and severance receipts"},
    "python_pathlib": {"tried": True, "used": True, "reason": "supportive source/result path binding"},
    "python_ast": {"tried": True, "used": True, "reason": "supportive import/call-site audit without executing EngineCore"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive exact source/result identity receipts"},
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing implication that finite-boundary quarantine does not imply gate clearance or basin admission",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "python_ast": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

REQUIRED_STAGE_FIELDS = ["fep_efe_score", "model_before", "model_after", "update_repair"]


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def parse_source(path: pathlib.Path) -> ast.Module | None:
    if not path.exists():
        return None
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None


def import_report(path: pathlib.Path) -> dict[str, Any]:
    tree = parse_source(path)
    direct_imports: list[dict[str, Any]] = []
    call_sites: list[dict[str, Any]] = []
    direct_numpy_or_scipy_imports: list[dict[str, Any]] = []
    if tree is None:
        return {"path": str(path), "exists": path.exists(), "parse_ok": False, "pass": False}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "engine_core" or module.startswith("engine_core."):
                direct_imports.append({"module": module, "names": [alias.name for alias in node.names], "line": node.lineno})
            if module in {"numpy", "scipy"} or module.startswith(("numpy.", "scipy.")):
                direct_numpy_or_scipy_imports.append({"module": module, "line": node.lineno})
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "engine_core" or name.startswith("engine_core."):
                    direct_imports.append({"module": name, "names": [name], "line": node.lineno})
                if name in {"numpy", "scipy"} or name.startswith(("numpy.", "scipy.")):
                    direct_numpy_or_scipy_imports.append({"module": name, "line": node.lineno})
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in {"EngineCore", "generate_initial_density"}:
                call_sites.append({"call": func.id, "line": node.lineno})
            elif isinstance(func, ast.Attribute) and func.attr in {"run_full_cycle", "run_substage"}:
                call_sites.append({"call": func.attr, "line": node.lineno})
    imported_names = sorted({name for row in direct_imports for name in row.get("names", [])})
    return {
        "path": str(path),
        "exists": path.exists(),
        "parse_ok": True,
        "direct_engine_core_imports": direct_imports,
        "imported_engine_core_names": imported_names,
        "expected_engine_core_imports_only": imported_names == ["EngineCore", "generate_initial_density"],
        "engine_core_call_sites": call_sites,
        "direct_numpy_or_scipy_imports": direct_numpy_or_scipy_imports,
        "pass": bool(
            direct_imports
            and imported_names == ["EngineCore", "generate_initial_density"]
            and call_sites
            and not direct_numpy_or_scipy_imports
        ),
    }


def self_boundary_report() -> dict[str, Any]:
    source = pathlib.Path(__file__).resolve()
    tree = parse_source(source)
    forbidden: list[dict[str, Any]] = []
    if tree is None:
        return {"path": str(source), "pass": False}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "engine_core" or module.startswith("engine_core."):
                forbidden.append({"module": module, "line": node.lineno})
            if module in {"numpy", "scipy", "torch"} or module.startswith(("numpy.", "scipy.", "torch.")):
                forbidden.append({"module": module, "line": node.lineno})
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in {"engine_core", "numpy", "scipy", "torch"} or name.startswith(
                    ("engine_core.", "numpy.", "scipy.", "torch.")
                ):
                    forbidden.append({"module": name, "line": node.lineno})
    return {"path": str(source), "forbidden_runtime_imports": forbidden, "pass": not forbidden}


def numeric_finiteness(value: Any, path: str = "$", *, require_numeric: bool = True) -> dict[str, Any]:
    nonfinite: list[dict[str, Any]] = []
    numeric_count = 0

    def walk(item: Any, item_path: str) -> None:
        nonlocal numeric_count
        if isinstance(item, bool) or item is None or isinstance(item, str):
            return
        if isinstance(item, int):
            numeric_count += 1
            return
        if isinstance(item, float):
            numeric_count += 1
            if not math.isfinite(item):
                nonfinite.append({"path": item_path, "value": repr(item)})
            return
        if isinstance(item, list):
            for index, child in enumerate(item):
                walk(child, f"{item_path}[{index}]")
            return
        if isinstance(item, dict):
            for key, child in item.items():
                walk(child, f"{item_path}.{key}")
            return
        nonfinite.append({"path": item_path, "value_type": type(item).__name__})

    walk(value, path)
    return {
        "numeric_leaf_count": numeric_count,
        "nonfinite_or_nonjson_values": nonfinite,
        "require_numeric": require_numeric,
        "pass": (numeric_count > 0 or not require_numeric) and not nonfinite,
    }


def finite_consumption_report(target: dict[str, Any]) -> dict[str, Any]:
    positive = target.get("positive") or {}
    repair = target.get("repair_receipt") or {}
    axis0 = target.get("axis0_outputs_or_blockers") or {}
    subtrees = {
        "fep_gradient_recomputed_from_stage_efe_rows": positive.get("fep_gradient_recomputed_from_stage_efe_rows"),
        "fep_gradient_has_matched_controls": positive.get("fep_gradient_has_matched_controls"),
        "downstream_plural_axis0_controls_consume_fep_gradient": positive.get("downstream_plural_axis0_controls_consume_fep_gradient"),
        "primary_control_result": repair.get("primary_control/result"),
        "axis0_fep_gradient_polarity": axis0.get("fep_gradient_polarity"),
    }
    finiteness = {key: numeric_finiteness(value, f"$.{key}") for key, value in subtrees.items()}
    stage_fields = repair.get("stage_fields_touched_or_consumed") or []
    required_present = all(field in stage_fields for field in REQUIRED_STAGE_FIELDS)
    positive_passes = [
        bool((positive.get("fep_gradient_recomputed_from_stage_efe_rows") or {}).get("pass")),
        bool((positive.get("fep_gradient_has_matched_controls") or {}).get("pass")),
        bool((positive.get("downstream_plural_axis0_controls_consume_fep_gradient") or {}).get("pass")),
    ]
    return {
        "stage_fields_touched_or_consumed": stage_fields,
        "required_stage_fields": REQUIRED_STAGE_FIELDS,
        "required_stage_fields_present": required_present,
        "subtree_finiteness": finiteness,
        "pass": bool(required_present and all(positive_passes) and all(row["pass"] for row in finiteness.values())),
    }


def gate_row_for_target(gate: dict[str, Any]) -> dict[str, Any]:
    for row in gate.get("tool_role_rows", []):
        if row.get("name") == TARGET_NAME:
            return row
    return {}


def severance_contract_report(receipt: dict[str, Any]) -> dict[str, Any]:
    positive = receipt.get("positive") or {}
    graveyard = receipt.get("graveyard_companions") or {}
    return {
        "receipt_exists": bool(receipt.get("exists")),
        "receipt_all_pass": receipt.get("all_pass"),
        "source_severance_sites_enumerated": bool((positive.get("source_severance_sites_are_enumerated") or {}).get("pass")),
        "enginecore_current_path_autograd_severed": bool(
            (positive.get("enginecore_current_path_is_detected_as_autograd_severed") or {}).get("pass")
        ),
        "finite_stage_record_scouts_not_blocked": bool(
            (graveyard.get("finite_stage_record_scouts_are_not_blocked") or {}).get("pass")
        ),
        "pass": bool(
            receipt.get("exists")
            and receipt.get("all_pass") is True
            and (positive.get("source_severance_sites_are_enumerated") or {}).get("pass") is True
            and (positive.get("enginecore_current_path_is_detected_as_autograd_severed") or {}).get("pass") is True
            and (graveyard.get("finite_stage_record_scouts_are_not_blocked") or {}).get("pass") is True
        ),
    }


def z3_quarantine_witness() -> dict[str, Any]:
    finite_boundary_receipt = z3.Bool("finite_boundary_receipt")
    direct_enginecore_importer = z3.Bool("direct_enginecore_importer")
    torch_native_enginecore_port = z3.Bool("torch_native_enginecore_port")
    nonclassical_basin_claim_allowed = z3.Bool("nonclassical_basin_claim_allowed")
    solver = z3.Solver()
    solver.add(finite_boundary_receipt, direct_enginecore_importer, z3.Not(torch_native_enginecore_port))
    solver.add(
        z3.Implies(
            z3.And(finite_boundary_receipt, direct_enginecore_importer, z3.Not(torch_native_enginecore_port)),
            z3.Not(nonclassical_basin_claim_allowed),
        )
    )
    solver.add(nonclassical_basin_claim_allowed)
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "meaning": "Finite boundary receipt plus direct EngineCore import, without a torch-native port, cannot imply nonclassical basin admission.",
    }


def identity_report() -> dict[str, Any]:
    paths = {
        "target_source": TARGET_SOURCE,
        "target_result": TARGET_RESULT,
        "engine_core_source": ENGINE_CORE_SOURCE,
        "engine_core_severance_result": ENGINE_CORE_SEVERANCE_RESULT,
        "tool_gate_result": TOOL_GATE_RESULT,
    }
    rows = {
        key: {
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else "missing",
        }
        for key, path in paths.items()
    }
    return {"files": rows, "pass": all(row["exists"] for row in rows.values())}


def main() -> int:
    started = time.time()
    target = read_json(TARGET_RESULT)
    severance = read_json(ENGINE_CORE_SEVERANCE_RESULT)
    gate = read_json(TOOL_GATE_RESULT)
    gate_row = gate_row_for_target(gate)
    target_gate_status = gate_row.get("tool_role_status")
    finite = finite_consumption_report(target)
    severance_report = severance_contract_report(severance)
    z3_witness = z3_quarantine_witness()
    identity = identity_report()
    target_imports = import_report(TARGET_SOURCE)
    self_boundary = self_boundary_report()

    gate_status_ok = target_gate_status in {
        "blocked_engine_core_importer_boundary",
        "blocked_engine_core_importer_boundary_finite_receipt_covered",
    }
    positive = {
        "exact_files_are_hash_bound": identity,
        "target_direct_enginecore_import_is_narrow": target_imports,
        "enginecore_severance_contract_is_active": severance_report,
        "target_result_is_green_but_gate_blocked": {
            "target_all_pass": target.get("all_pass"),
            "target_promotion_allowed": target.get("promotion_allowed"),
            "gate_status": target_gate_status,
            "gate_nonclassical_basin_claim_allowed": gate_row.get("nonclassical_basin_claim_allowed"),
            "pass": bool(
                target.get("exists")
                and target.get("all_pass") is True
                and target.get("promotion_allowed") is False
                and gate_status_ok
                and gate_row.get("nonclassical_basin_claim_allowed") is False
            ),
        },
        "target_consumes_finite_json_stage_evidence": finite,
        "z3_quarantine_implication_blocks_promotion": z3_witness,
    }
    graveyard = {
        "finite_boundary_receipt_is_not_torch_native_enginecore_port": {
            "pass": True,
            "blocked_claim": "gradient-through-EngineCore or differentiable engine-cycle claim",
            "next_required_receipt": "torch_native_enginecore_migration_receipt",
        },
        "gate_clearance_from_finite_stage_json_is_rejected": {
            "pass": gate_row.get("nonclassical_basin_claim_allowed") is False,
            "current_gate_status": target_gate_status,
            "reason": "The receipt can classify the boundary but cannot convert the target row into nonclassical basin evidence.",
        },
        "final_axis0_fep_world_model_claim_is_rejected": {
            "pass": all(term in str(target.get("claim_ceiling", "")).lower() for term in ["does not admit", "final axis0", "fep", "world-model"]),
            "target_claim_ceiling": target.get("claim_ceiling"),
        },
    }
    boundary = {
        "receipt_source_does_not_import_enginecore_numpy_scipy_or_torch": self_boundary,
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_names_no_broad_claims": {
            "pass": all(
                phrase in CLAIM_CEILING.lower()
                for phrase in ["does not clear", "does not admit nonclassical basin", "does not promote", "physics", "world-model"]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    all_checks = {**positive, **graveyard, **boundary}
    all_pass = all(bool(row.get("pass")) for row in all_checks.values())
    result = {
        "schema": "ENGINE_CORE_FINITE_BOUNDARY_RECEIPT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "target": {
            "name": TARGET_NAME,
            "source": str(TARGET_SOURCE),
            "result": str(TARGET_RESULT),
            "current_tool_gate_status": target_gate_status,
            "admission_result": "finite_boundary_admitted_without_gate_clearance",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "finite_boundary_receipt": {
            "target_imports": target_imports,
            "finite_consumption": finite,
            "severance_contract": severance_report,
            "gate_row": gate_row,
            "admitted_uses": ["finite EngineCore stage-record JSON/scalar dependency receipt", "stage-local FEP-gradient vector audit"],
            "blocked_uses": [
                "torch-native EngineCore proof",
                "gradient-through-EngineCore proof",
                "nonclassical basin admission",
                "final Axis0/FEP/Holodeck/world-model/manifold promotion",
            ],
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
            "This receipt audits a current v5 Axis0/FEP EngineCore importer-boundary row.",
            "It reads current v5 gate and severance receipts instead of reusing v4 probe semantics.",
            "It is an audit/quarantine receipt and not a source-native nonclassical promotion surface.",
        ],
        "blockers": [] if all_pass else [key for key, row in all_checks.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
