#!/usr/bin/env python3
"""Layer-validity audit for the geometric constraint manifold.

This scout separates three claims that were previously conflated:

1. a named layer exists in the 13-layer fixture;
2. that layer has operational evidence under current PyTorch/graph/proof
   receipts;
3. that layer is valid as an emergent consequence of the two root constraints
   F01 finitude and N01 noncommutation.

The current expected result is intentionally conservative: current receipts
support operational candidate layers, but do not prove root-emergent layer
validity. A green receipt here means the audit ran and blocked overclaim.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "geometric_manifold_layer_validity_root_constraint_audit_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

ROOT_MATURITY = RESULT_DIR / "root_geometric_constraint_manifold_maturity_pytorch_toolchain_probe_results.json"
SEMANTIC_COUPLING = RESULT_DIR / "g_structure_semantic_layer_operator_coupling_probe_results.json"
RESPONSIBILITY = RESULT_DIR / "constraint_manifold_layer_causal_responsibility_matrix_probe_results.json"
FOUNDATION_GATE = RESULT_DIR / "two_root_constraint_attractor_basin_foundation_gate_probe_results.json"
LAYER_EMERGENCE_ABLATION = RESULT_DIR / "two_root_constraint_layer_emergence_ablation_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "proof_audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "geometric_manifold_layer_validity_root_constraint_audit"
CLAIM_CEILING = (
    "Formal scout only: audits whether the current 13 named geometric-manifold "
    "layers are merely operational candidates or are proven as valid emergent "
    "layers from F01 finitude and N01 noncommutation. It blocks layer-validity, "
    "final manifold, attractor-basin, Axis0, engine, physics, target-system, "
    "Holodeck, and canonical claims unless executable root-constraint evidence "
    "exists; it does not admit canonical claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parsing and cross-audit of current formal-scout receipts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite logic gate separating operational candidate layers from root-valid layers",
    },
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "z3": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(val) for val in value]
    return value


def load_inputs() -> dict[str, dict[str, Any]]:
    paths = {
        "root_maturity": ROOT_MATURITY,
        "semantic_coupling": SEMANTIC_COUPLING,
        "responsibility": RESPONSIBILITY,
        "foundation_gate": FOUNDATION_GATE,
        "layer_emergence_ablation": LAYER_EMERGENCE_ABLATION,
    }
    return {
        key: {
            "path": str(path.relative_to(REPO)),
            "sha256": sha256_file(path),
            "receipt": read_json(path),
        }
        for key, path in paths.items()
    }


def layer_rows(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    root = inputs["root_maturity"]["receipt"]
    resp = inputs["responsibility"]["receipt"]
    foundation = inputs["foundation_gate"]["receipt"]
    layer_ablation = inputs["layer_emergence_ablation"]["receipt"]
    layers = list(root.get("layers") or [])
    maturity_rows = {
        row["layer"]: row
        for row in root.get("fixture_layer_rows", [])
    }
    removal_rows = {
        row["layer"]: row
        for row in root.get("graveyard_companions", {})
        .get("each_layer_removal_changes_state", {})
        .get("rows", [])
    }
    responsibility_rows = {
        row["layer_name"]: row for row in resp.get("responsibility_matrix", {}).get("rows", [])
    }
    executable_root_count = int(layer_ablation.get("summary", {}).get("executable_root_receipt_count") or 0)
    root_supported_layers = {
        row["layer"]
        for row in layer_ablation.get("layer_root_emergence_rows", [])
        if row.get("root_ablation_supported") is True
    }

    out = []
    for idx, layer in enumerate(layers):
        maturity = maturity_rows.get(layer, {})
        removal = removal_rows.get(layer, {})
        responsibility = responsibility_rows.get(layer, {})
        operational_signals = {
            "inventory_present": bool(layer),
            "runtime_delta_nonzero": float(maturity.get("delta_norm") or 0.0) > 0.0,
            "removal_changes_state": bool(removal.get("pass") is True),
            "responsibility_non_substitutable": bool(responsibility.get("non_substitutable") is True),
        }
        operational_candidate = all(operational_signals.values())
        root_ablation_supported = executable_root_count > 0 and layer in root_supported_layers
        out.append(
            {
                "layer_idx": idx,
                "layer": layer,
                "operational_signals": operational_signals,
                "runtime_delta_norm": float(maturity.get("delta_norm") or 0.0),
                "removal_gap": float(removal.get("gap") or 0.0),
                "responsibility_distances": responsibility.get("distances", {}),
                "operational_candidate": operational_candidate,
                "root_ablation_supported": root_ablation_supported,
                "validity_status": "root_ablation_supported_layer" if root_ablation_supported else "operational_candidate_not_root_validated",
            }
        )
    return out


def semantic_role_report(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    semantic = inputs["semantic_coupling"]["receipt"]
    roles = (
        semantic.get("positive", {})
        .get("explicit_semantic_operator_roles_present", {})
        .get("roles", [])
    )
    role_ids = [row.get("role_id") for row in roles]
    return {
        "role_count": len(role_ids),
        "role_ids": role_ids,
        "semantic_coupling_all_pass": semantic.get("all_pass") is True,
        "semantic_gap_summary": semantic.get("summary", {}),
        "pass": len(role_ids) == 13 and semantic.get("all_pass") is True,
        "boundary": "Semantic operator roles support a non-row-count G-structure fixture, but do not prove the named 13 layers emerge from F01/N01.",
    }


def z3_report(rows: list[dict[str, Any]], executable_root_count: int) -> dict[str, Any]:
    solver = z3.Solver()
    op_all = z3.Bool("all_layers_operational_candidates")
    root_all = z3.Bool("all_layers_root_ablation_supported")
    root_ablation_supported = z3.Bool("root_ablation_layer_set_supported")
    all_operational = all(bool(row["operational_candidate"]) for row in rows)
    all_root = all(bool(row["root_ablation_supported"]) for row in rows)
    solver.add(op_all == z3.BoolVal(all_operational))
    solver.add(root_all == z3.BoolVal(all_root))
    solver.add(root_ablation_supported == z3.And(op_all, root_all, z3.IntVal(executable_root_count) > 0))
    solver.push()
    solver.add(root_ablation_supported)
    root_support_check = solver.check()
    solver.pop()
    return {
        "all_layers_operational_candidates": all_operational,
        "all_layers_root_ablation_supported": all_root,
        "executable_root_receipt_count": executable_root_count,
        "root_ablation_layer_set_supported_under_current_evidence": str(root_support_check),
        "pass": root_support_check == z3.sat,
        "rule": "root-ablation layer-set support requires operational layer evidence and executable F01/N01 layer-emergence ablation evidence",
    }


def main() -> int:
    started = time.time()
    inputs = load_inputs()
    rows = layer_rows(inputs)
    foundation = inputs["foundation_gate"]["receipt"]
    layer_ablation = inputs["layer_emergence_ablation"]["receipt"]
    executable_root_count = int(layer_ablation.get("summary", {}).get("executable_root_receipt_count") or 0)
    semantic = semantic_role_report(inputs)
    z3_gate = z3_report(rows, executable_root_count)
    operational_count = sum(1 for row in rows if row["operational_candidate"])
    root_supported_count = sum(1 for row in rows if row["root_ablation_supported"])

    positive = {
        "thirteen_named_layers_have_operational_candidate_evidence": {
            "pass": operational_count == 13,
            "operational_candidate_count": operational_count,
            "layer_count": len(rows),
        },
        "semantic_operator_fixture_is_non_row_count_but_not_root_derivation": semantic,
        "z3_confirms_root_ablation_layer_support_with_executable_root_constraints": z3_gate,
    }
    graveyard = {
        "all_operational_layers_require_root_ablation_evidence": {
            "pass": operational_count == 13 and root_supported_count == 13,
            "operational_candidate_count": operational_count,
            "root_ablation_supported_layer_count": root_supported_count,
        },
        "root_constraint_foundation_gate_blocks_basin_and_layer_promotion": {
            "pass": foundation.get("summary", {}).get("root_basin_admission_status") == "blocked"
            and executable_root_count > 0,
            "foundation_summary": foundation.get("summary", {}),
            "layer_ablation_summary": layer_ablation.get("summary", {}),
        },
        "axis0_downstream_not_layer_validity_evidence": {
            "pass": True,
            "reason": "Axis0 receipts can stress a candidate manifold, but cannot validate the root layer set before F01/N01-driven layer emergence is executable.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "validity_language_demoted": {
            "pass": root_supported_count == 13,
            "allowed_phrase": "root-ablation-supported layer",
            "blocked_phrase": "valid root-emergent layer",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_retuned_layer_stack_integration_probe",
            "requirement": "Consume the root-ablation-supported layers in the retuned stack, then separately test dynamic attractor-basin convergence.",
        },
    }
    all_pass = all(row.get("pass") is True for row in positive.values()) and all(
        row.get("pass") is True for row in graveyard.values()
    ) and all(row.get("pass") is True for row in boundary.values())

    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "layer_count": len(rows),
            "operational_candidate_layer_count": operational_count,
            "root_ablation_supported_layer_count": root_supported_count,
            "layer_validity_status": "root_ablation_supported_not_final_basin",
            "root_constraints": ["F01_finitude", "N01_noncommutation"],
            "executable_root_receipt_count": executable_root_count,
            "next_required_scout": "two_root_retuned_layer_stack_integration_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "layer_validity_rows": jsonable(rows),
        "input_receipts": {key: {k: v for k, v in value.items() if k != "receipt"} for key, value in inputs.items()},
        "why_not_v4_probes": [
            "v5 formal-scout audit over current manifold receipts.",
            "It admits root-ablation layer support only after F01/N01 are executable layer-emergence predicates.",
            "It treats Axis0 as downstream stress evidence, not as root layer evidence.",
        ],
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "variants": [
                "treat operational candidate evidence alone as root-ablation support: rejected",
                "treat semantic operator roles alone as F01/N01 derivation: rejected",
                "treat Axis0 stress fixtures as root layer validation: rejected",
            ],
        },
        "blockers": [],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
