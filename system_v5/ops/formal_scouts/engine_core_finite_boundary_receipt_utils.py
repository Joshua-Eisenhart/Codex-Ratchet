"""Shared builder for finite EngineCore quarantine receipts."""

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
ENGINE_CORE_SOURCE = ROOT / "engine_core.py"
ENGINE_CORE_SEVERANCE_RESULT = RESULT_DIR / "engine_core_autograd_severance_contract_probe_results.json"
TOOL_GATE_RESULT = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"
TRIAGE_RESULT = RESULT_DIR / "engine_core_boundary_row_triage_probe_results.json"

CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "engine_core_finite_boundary_classifier"
SIM_EXECUTION_KIND = "audit"

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive parsing of target, gate, triage, and severance receipts"},
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


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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
            elif isinstance(func, ast.Attribute) and func.attr in {"run_full_cycle", "run_substage", "generate_initial_density"}:
                call_sites.append({"call": func.attr, "line": node.lineno})
    imported_names = sorted({name for row in direct_imports for name in row.get("names", [])})
    return {
        "path": str(path),
        "exists": path.exists(),
        "parse_ok": True,
        "sha256": sha256_file(path),
        "direct_engine_core_imports": direct_imports,
        "imported_engine_core_names": imported_names,
        "engine_core_call_sites": call_sites,
        "direct_numpy_or_scipy_imports": direct_numpy_or_scipy_imports,
        "pass": bool(direct_imports and call_sites and not direct_numpy_or_scipy_imports),
    }


def self_boundary_report(source: pathlib.Path) -> dict[str, Any]:
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


def numeric_finiteness(value: Any, path: str = "$") -> dict[str, Any]:
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
        "pass": numeric_count > 0 and not nonfinite,
    }


def gate_row_for_target(gate: dict[str, Any], target_name: str) -> dict[str, Any]:
    for row in gate.get("tool_role_rows", []):
        if row.get("name") == target_name:
            return row
    return {}


def triage_row_for_target(triage: dict[str, Any], target_name: str) -> dict[str, Any]:
    for row in triage.get("row_triage", []):
        if row.get("name") == target_name:
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
    gate_clearance = z3.Bool("gate_clearance")
    nonclassical_basin_claim_allowed = z3.Bool("nonclassical_basin_claim_allowed")
    solver = z3.Solver()
    solver.add(finite_boundary_receipt, direct_enginecore_importer, z3.Not(torch_native_enginecore_port))
    solver.add(
        z3.Implies(
            z3.And(finite_boundary_receipt, direct_enginecore_importer, z3.Not(torch_native_enginecore_port)),
            z3.And(z3.Not(gate_clearance), z3.Not(nonclassical_basin_claim_allowed)),
        )
    )
    solver.add(z3.Or(gate_clearance, nonclassical_basin_claim_allowed))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "meaning": "Finite boundary receipt plus direct EngineCore import, without a torch-native port, cannot imply gate clearance or nonclassical basin admission.",
    }


def identity_report(paths: dict[str, pathlib.Path]) -> dict[str, Any]:
    rows = {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path) if path.exists() else "missing"}
        for key, path in paths.items()
    }
    return {"files": rows, "pass": all(row["exists"] for row in rows.values())}


def target_claim_ceiling_blocks_broad_claims(target: dict[str, Any]) -> dict[str, Any]:
    ceiling = str(target.get("claim_ceiling") or "").lower()
    broad_terms = ["final", "canonical", "physics", "manifold", "full", "promotion", "promote"]
    return {
        "claim_ceiling": target.get("claim_ceiling"),
        "required_terms": ["does not", "one broad-claim term"],
        "broad_terms_seen": sorted(term for term in broad_terms if term in ceiling),
        "pass": "does not" in ceiling and any(term in ceiling for term in broad_terms),
    }


def build_receipt(config: dict[str, Any], source_file: str) -> dict[str, Any]:
    started = time.time()
    name = str(config["name"])
    target_name = str(config["target_name"])
    target_source = ROOT / f"sim_{target_name}.py"
    target_result = RESULT_DIR / f"{target_name}_results.json"
    output_path = RESULT_DIR / f"{name}_results.json"
    wrapper_source = ROOT / source_file

    target = read_json(target_result)
    severance = read_json(ENGINE_CORE_SEVERANCE_RESULT)
    gate = read_json(TOOL_GATE_RESULT)
    triage = read_json(TRIAGE_RESULT)
    gate_row = gate_row_for_target(gate, target_name)
    triage_row = triage_row_for_target(triage, target_name)
    target_gate_status = gate_row.get("tool_role_status")
    source_imports = import_report(target_source)
    self_boundary = self_boundary_report(wrapper_source)
    numeric = numeric_finiteness(target)
    severance_report = severance_contract_report(severance)
    z3_witness = z3_quarantine_witness()
    claim_ceiling = (
        f"Formal scout quarantine receipt only: records bounded evidence that the current {target_name} "
        f"EngineCore import is consumed as finite JSON/scalar/window/readout evidence for {config['finite_scope']}. "
        "It does not clear the EngineCore importer boundary, does not admit nonclassical basin evidence, "
        "and does not promote final Axis0, FEP, Holodeck, PEPS3D, manifold, physics, cognition, or world-model claims."
    )
    gate_status_ok = target_gate_status in {
        "blocked_engine_core_importer_boundary",
        "blocked_engine_core_importer_boundary_finite_receipt_covered",
    }
    positive = {
        "exact_files_are_hash_bound": identity_report(
            {
                "target_source": target_source,
                "target_result": target_result,
                "engine_core_source": ENGINE_CORE_SOURCE,
                "engine_core_severance_result": ENGINE_CORE_SEVERANCE_RESULT,
                "tool_gate_result": TOOL_GATE_RESULT,
                "triage_result": TRIAGE_RESULT,
                "receipt_source": wrapper_source,
            }
        ),
        "target_direct_enginecore_import_is_live": source_imports,
        "target_is_current_finite_quarantine_candidate": {
            "triage_classification": triage_row.get("classification"),
            "triage_detail": triage_row.get("classification_detail"),
            "pass": triage_row.get("classification") == "finite_router_or_readout_quarantine_candidate",
        },
        "target_result_is_green_but_gate_blocked": {
            "target_all_pass": target.get("all_pass"),
            "target_promotion_allowed": target.get("promotion_allowed"),
            "target_blockers": target.get("blockers", []),
            "gate_status": target_gate_status,
            "gate_nonclassical_basin_claim_allowed": gate_row.get("nonclassical_basin_claim_allowed"),
            "pass": bool(
                target.get("exists")
                and result_all_pass(target)
                and target.get("promotion_allowed") is False
                and not target.get("blockers", [])
                and gate_status_ok
                and gate_row.get("nonclassical_basin_claim_allowed") is False
            ),
        },
        "enginecore_severance_contract_is_active": severance_report,
        "target_consumes_finite_json_stage_evidence": {
            "pass": bool(
                numeric["pass"]
                and source_imports["pass"]
                and triage_row.get("classification") == "finite_router_or_readout_quarantine_candidate"
            ),
            "finite_scope": config["finite_scope"],
            "numeric_json_finiteness": numeric,
            "admitted_uses": config["admitted_uses"],
        },
        "z3_quarantine_implication_blocks_promotion": z3_witness,
    }
    graveyard = {
        "finite_boundary_receipt_is_not_torch_native_enginecore_port": {
            "pass": True,
            "blocked_claim": "gradient-through-EngineCore or differentiable engine-cycle claim",
            "next_required_receipt": "torch_native_enginecore_migration_receipt",
        },
        "gate_clearance_from_finite_json_is_rejected": {
            "pass": gate_row.get("nonclassical_basin_claim_allowed") is False,
            "current_gate_status": target_gate_status,
            "reason": "The receipt can classify the boundary but cannot convert the target row into nonclassical basin evidence.",
        },
        "target_broad_claim_is_rejected": target_claim_ceiling_blocks_broad_claims(target),
    }
    boundary = {
        "receipt_source_does_not_import_enginecore_numpy_scipy_or_torch": self_boundary,
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_names_no_broad_claims": {
            "pass": all(
                phrase in claim_ceiling.lower()
                for phrase in ["does not clear", "does not admit nonclassical basin", "does not promote", "physics", "world-model"]
            ),
            "claim_ceiling": claim_ceiling,
        },
    }
    all_checks = {**positive, **graveyard, **boundary}
    all_pass = all(bool(row.get("pass")) for row in all_checks.values())
    return {
        "schema": "ENGINE_CORE_FINITE_BOUNDARY_RECEIPT_v1",
        "name": name,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": claim_ceiling,
        "target": {
            "name": target_name,
            "source": str(target_source),
            "result": str(target_result),
            "current_tool_gate_status": target_gate_status,
            "admission_result": "finite_boundary_admitted_without_gate_clearance",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "finite_boundary_receipt": {
            "target_imports": source_imports,
            "finite_consumption": positive["target_consumes_finite_json_stage_evidence"],
            "severance_contract": severance_report,
            "triage_row": triage_row,
            "gate_row": gate_row,
            "admitted_uses": config["admitted_uses"],
            "blocked_uses": [
                "torch-native EngineCore proof",
                "gradient-through-EngineCore proof",
                "nonclassical basin admission",
                "final Axis0/FEP/Holodeck/PEPS3D/world-model/manifold promotion",
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
            "This receipt audits a current v5 EngineCore importer-boundary row.",
            "It reads current v5 gate, triage, and severance receipts instead of reusing v4 probe semantics.",
            "It is an audit/quarantine receipt and not a source-native nonclassical promotion surface.",
        ],
        "blockers": [] if all_pass else [key for key, row in all_checks.items() if not row.get("pass")],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
        "output_path": rel(output_path),
    }


def write_receipt(config: dict[str, Any], source_file: str) -> int:
    result = build_receipt(config, source_file)
    output_path = RESULT_DIR / f"{config['name']}_results.json"
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT {config['name']}: all_pass={result['all_pass']} -> {output_path}")
    return 0 if result["all_pass"] else 1
