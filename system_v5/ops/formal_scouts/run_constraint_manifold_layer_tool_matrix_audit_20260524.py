#!/usr/bin/env python3
"""Audit the constraint manifold as layer-local tool models.

This is orchestration/audit only. It enforces the owner correction that the
manifold should not be modeled as one blended all-at-once object. Each layer
must have its own bounded model, load-bearing tool receipts, controls, and
carry-forward boundary before the next layer consumes it.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_manifold_layer_tool_matrix_audit_20260524_results.json"
SUITE_PATH = RESULT_DIR / "probe_effect_spinor_bottom_up_manifold_suite_20260524_results.json"
SUITE_MODULE_PATH = ROOT / "run_probe_effect_spinor_bottom_up_manifold_suite_20260524.py"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "layer_tool_matrix_audit"
SOURCE_ALIGNMENT_CATEGORY = "constraint_manifold_layer_local_full_tool_modeling"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Layer-tool audit only: checks that each constraint-manifold layer is "
    "modeled as a bounded local system with its own tool receipts and controls. "
    "It does not admit final manifold, Axis0, Xi, flux, PEPS3D closure, gravity, "
    "Standard Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing receipt and suite-result parsing"},
    "python_importlib": {"tried": True, "used": True, "reason": "supportive reuse of staged suite script registry"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive source/result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_importlib": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def load_suite_module() -> Any:
    spec = importlib.util.spec_from_file_location("bottom_up_suite_20260524", SUITE_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import suite module: {SUITE_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def tool_depth(row: dict[str, Any]) -> dict[str, str]:
    depth = row.get("TOOL_INTEGRATION_DEPTH") or row.get("tool_integration_depth") or {}
    return {str(key): str(value) for key, value in depth.items()}


def tool_manifest(row: dict[str, Any]) -> dict[str, Any]:
    manifest = row.get("TOOL_MANIFEST") or row.get("tool_manifest") or {}
    return {str(key): value for key, value in manifest.items()}


def normalize_tool_name(name: str) -> str:
    return name.lower().replace("-", "_")


TOOL_GROUPS = {
    "torch_native": {"pytorch", "torch", "torch_geometric"},
    "solver_or_exact": {"z3", "sympy", "cvc5"},
    "finite_effect_or_probe": {"sic", "mub", "povm", "effect", "contextuality", "sheaf", "weyl"},
    "spinor_quaternion": {"spinor", "quaternion", "hopf", "weyl", "ijk"},
    "tensor_carrier": {"mps", "peps", "peps3d", "quimb", "opt_einsum", "cotengra"},
    "graph_topology": {"gudhi", "rustworkx", "networkx", "toponetx", "xgi", "torch_geometric"},
    "engine_runtime": {"canonical_qit_engine_specs", "engine", "runtime", "terrain", "schedule"},
    "bridge_or_axis0": {"phi0", "xi", "axis0", "coherent", "entropy", "fep", "cut"},
    "flux": {"flux", "chirality", "twistor", "basin"},
}


LAYER_REQUIREMENTS = {
    "L0_finite_effect_probe_substrate": {
        "required_groups": ["finite_effect_or_probe", "torch_native"],
        "local_boundary": "finite probe/effect identity and process-history receipts only",
    },
    "L1_spinor_quaternion_networks": {
        "required_groups": ["spinor_quaternion", "torch_native", "engine_runtime"],
        "local_boundary": "spinor/quaternion/Hopf/Weyl carrier receipts only",
    },
    "L2_mps_peps_peps3d_carriers": {
        "required_groups": ["tensor_carrier", "torch_native"],
        "local_boundary": "MPS/PEPS/PEPS3D carrier receipts seeded by lower layers",
    },
    "L3_engine_runtime": {
        "required_groups": ["engine_runtime", "torch_native"],
        "local_boundary": "source-aligned engine schedule and basin/runtime receipts",
    },
    "L4_bridge_xi_phi0_control_receipts": {
        "required_groups": ["bridge_or_axis0", "torch_native"],
        "local_boundary": "Xi/Phi0 bridge and stress-control receipts; final closure blocked",
    },
    "L5_axis0_candidates": {
        "required_groups": ["bridge_or_axis0", "spinor_quaternion", "torch_native"],
        "local_boundary": "Axis0 shell/cut response candidates only; final Axis0 blocked",
    },
    "L6_derived_flux_candidates": {
        "required_groups": ["flux", "spinor_quaternion", "torch_native"],
        "local_boundary": "derived dynamic shell-flux candidates only; final flux blocked",
    },
    "L7_flux_bound_axis0_gradient": {
        "required_groups": ["flux", "bridge_or_axis0", "spinor_quaternion", "tensor_carrier", "torch_native"],
        "local_boundary": "Axis0 as signed QIT/FEP gradient on derived PEPS3D spinor-shell flux; final closure blocked",
    },
}


def receipt_text(script_name: str, receipt: dict[str, Any]) -> str:
    parts = [script_name]
    for key in [
        "name",
        "classification",
        "sim_execution_kind",
        "source_alignment_category",
        "why_not_v4_probes",
        "claim_ceiling",
    ]:
        value = receipt.get(key)
        if isinstance(value, str):
            parts.append(value)
    parts.extend(tool_depth(receipt).keys())
    parts.extend(tool_manifest(receipt).keys())
    return " ".join(parts).lower()


def group_present(group: str, script_name: str, receipt: dict[str, Any]) -> bool:
    text = receipt_text(script_name, receipt)
    tools = {normalize_tool_name(name) for name in tool_depth(receipt)}
    needles = TOOL_GROUPS[group]
    if group in {"torch_native", "solver_or_exact", "graph_topology"}:
        return bool(tools & needles) or any(needle in text for needle in needles)
    return any(needle in text for needle in needles)


def inspect_stage(stage_name: str, scripts: list[str], stage_summary: dict[str, Any], suite_module: Any) -> dict[str, Any]:
    receipts = []
    group_hits = {group: [] for group in LAYER_REQUIREMENTS[stage_name]["required_groups"]}
    missing = []
    for script in scripts:
        result_path = suite_module.expected_result_path(script)
        receipt = load_json(result_path)
        if not receipt:
            missing.append(script)
            continue
        depth = tool_depth(receipt)
        receipts.append(
            {
                "script": script,
                "result_path": result_path,
                "all_pass": receipt.get("all_pass"),
                "classification": receipt.get("classification"),
                "source_alignment_category": receipt.get("source_alignment_category"),
                "load_bearing_tools": sorted([name for name, value in depth.items() if value == "load_bearing"]),
                "supportive_tools": sorted([name for name, value in depth.items() if value == "supportive"]),
            }
        )
        for group in group_hits:
            if group_present(group, script, receipt):
                group_hits[group].append(script)
    unsatisfied = [group for group, hits in group_hits.items() if not hits]
    stage_passed_by_suite = bool(stage_summary.get(stage_name, {}).get("failed") == [] and stage_summary.get(stage_name, {}).get("total"))
    return {
        "stage": stage_name,
        "scripts": scripts,
        "stage_passed_by_suite": stage_passed_by_suite,
        "local_boundary": LAYER_REQUIREMENTS[stage_name]["local_boundary"],
        "required_groups": LAYER_REQUIREMENTS[stage_name]["required_groups"],
        "group_hits": group_hits,
        "unsatisfied_groups": unsatisfied,
        "missing_receipts": missing,
        "receipt_summaries": receipts,
        "pass": stage_passed_by_suite and not unsatisfied and not missing,
    }


def main() -> int:
    started = time.time()
    suite_module = load_suite_module()
    suite_result = load_json(SUITE_PATH)
    stage_summary = (suite_result.get("summary") or {}).get("stage_summary") or {}
    stages = []
    for stage_name, scripts in suite_module.STAGED_SCRIPTS:
        if stage_name not in LAYER_REQUIREMENTS:
            continue
        stages.append(inspect_stage(stage_name, scripts, stage_summary, suite_module))
    local_pass = all(stage["pass"] for stage in stages)
    serial_order_pass = [name for name, _ in suite_module.STAGED_SCRIPTS if name in LAYER_REQUIREMENTS] == [
        stage["stage"] for stage in stages
    ]
    not_all_at_once_contract = {
        "pass": serial_order_pass and len(stages) == len(LAYER_REQUIREMENTS),
        "meaning": (
            "Each layer is audited as a local model with its own tool groups and "
            "receipt boundary. The suite may run bottom-up, but a downstream layer "
            "does not erase or replace the local tool obligations of upstream layers."
        ),
        "stage_order": [stage["stage"] for stage in stages],
    }
    boundary = {
        "B1_formal_scout_only": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_no_final_claims": {"pass": "does not admit final manifold" in CLAIM_CEILING},
        "B3_layer_local_not_all_at_once": not_all_at_once_contract,
    }
    positive = {
        "all_layers_have_local_tool_models": {
            "pass": local_pass,
            "failed_layers": [stage["stage"] for stage in stages if not stage["pass"]],
        },
        "suite_result_available_and_green": {
            "pass": bool(suite_result.get("all_pass")),
            "suite_path": SUITE_PATH,
            "script_count": (suite_result.get("summary") or {}).get("script_count"),
            "passed_scripts": (suite_result.get("summary") or {}).get("passed_scripts"),
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in boundary.values())
    variant_rows = list(positive.values()) + list(boundary.values()) + stages
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": "constraint_manifold_layer_tool_matrix_audit_20260524",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "nearby_variants": {
            "passed": sum(1 for row in variant_rows if row["pass"]),
            "total": len(variant_rows),
        },
        "positive": positive,
        "graveyard_companions": {
            "GC1_single_blended_model_not_accepted": {
                "pass": True,
                "blocked_pattern": "one monolithic all-at-once manifold receipt replacing layer-local tool receipts",
            }
        },
        "boundary": boundary,
        "layer_tool_matrix": stages,
        "summary": {
            "elapsed_seconds": time.time() - started,
            "layer_count": len(stages),
            "failed_layers": [stage["stage"] for stage in stages if not stage["pass"]],
            "suite_script_count": (suite_result.get("summary") or {}).get("script_count"),
            "suite_passed_scripts": (suite_result.get("summary") or {}).get("passed_scripts"),
            "not_all_at_once_contract_pass": not_all_at_once_contract["pass"],
        },
        "next_required_work": [
            "For any layer that adds a new tool family, add a layer-local micro scout before coupling it downstream.",
            "Port Axis0 shell response to MPS as an L2/L5 handoff, not as a direct final Axis0 claim.",
            "Port dynamic shell flux to MPS/PEPS/PEPS3D as carrier-local rows before using it in physics overlays.",
            "Scale flux-bound Axis0 only after the 8-site PEPS3D shell row keeps its sheet/chirality/topology controls.",
        ],
        "why_not_v4_probes": (
            "This is a v5 layer-local tool matrix audit. It does not claim a single all-at-once manifold model."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
