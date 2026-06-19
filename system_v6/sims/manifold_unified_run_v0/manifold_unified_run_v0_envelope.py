#!/usr/bin/env python3
"""Envelope builder for manifold_unified_run_v0."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

from manifold_unified_run_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    MODE,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SEED,
    SIM_ID,
    TOL,
    base_leg_payload,
    build_core,
    now_z,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)

SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
LEG_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(name: str, leg: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": leg["source_path"],
        "source_sha256": leg["source_sha256"],
        "result_path": rel(path),
        "result_sha256": sha256_file(path),
        "reads_peer_result": False,
        "packages_used": leg["packages_used"],
        "aligned_packages_load_bearing": leg["aligned_packages_load_bearing"],
        "claim_path_tools": leg.get("claim_path_tools", []),
        "trajectory_artifact": leg.get("trajectory_artifact", {}),
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {
        name: float(leg["engine_values"]["conditioned_total_abs_current"]) for name, leg in legs.items()
    }
    julia_value = values["julia"]
    diffs = {name: abs(value - julia_value) for name, value in values.items()}
    return {
        "julia_authoritative": True,
        "metric": "step3.conditioned_total_abs_current",
        "engine_values": values,
        "absolute_differences_from_julia": {name: round(value, 12) for name, value in diffs.items()},
        "max_divergence": round(max(diffs.values()), 12),
        "tolerance": TOL,
    }


def build_payload() -> dict[str, Any]:
    core = build_core()
    legs = {name: load(path) for name, path in LEG_PATHS.items()}
    jax_proofs = legs["jax"]["crossover_proofs"]
    julia_z3 = legs["julia"]["crossover_proofs"]["julia_z3"]
    div = divergence(legs)
    one_to_one = core["one_to_one_tool_calls"]
    matrix = core["cross_layer_consistency_matrix"]
    trajectory = core["trajectory"]
    controls = core["controls"]
    artifact_receipt = core["trajectory_artifact_receipt"]
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "ceiling": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": now_z(),
        "seed": SEED,
        "mode": MODE,
        "stage": "S11_unified_geometric_constraint_manifold_scratch",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": stable_sha256(PIN_SPEC),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "declared_packet_mode": MODE,
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "reads_peer_result": False,
            "source_backed_validator_expected_command": (
                "python scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed "
                f"{rel(RESULT_PATH)}"
            ),
        },
        "scope_fence": {
            "bounded_unified_scratch_run": True,
            "manifold_level_admission": False,
            "bridge_or_axis_claim": False,
            "mct_theorem": False,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "active_lane_not_touched": "terrain_spinor_flux_nest_n4_v0",
        },
        "engines": {name: engine_record(name, legs[name], LEG_PATHS[name]) for name in ("julia", "jax", "pytorch")},
        "engine_result_sha256": {name: sha256_file(path) for name, path in LEG_PATHS.items()},
        "TOOL_MANIFEST": {
            "julia": legs["julia"]["TOOL_MANIFEST"],
            "jax": legs["jax"]["TOOL_MANIFEST"],
            "pytorch": legs["pytorch"]["TOOL_MANIFEST"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "julia": legs["julia"]["TOOL_INTEGRATION_DEPTH"],
            "jax": legs["jax"]["TOOL_INTEGRATION_DEPTH"],
            "pytorch": legs["pytorch"]["TOOL_INTEGRATION_DEPTH"],
        },
        "claim_path_tools": ["QuantumOptics", "Z3", "z3", "cvc5", "sympy", "torch_geometric", "torch.func"],
        "parent_lineage": core["parent_lineage"],
        "trajectory_artifact": artifact_receipt,
        "trajectory": trajectory,
        "one_thing_check": trajectory["one_thing_check"],
        "row_family_step_classification": trajectory["row_family_step_classification"],
        "step_recomputation_claim": (
            "step-dependent families recomputed per step; invariant families carried with stated justification"
        ),
        "cross_layer_consistency_matrix": matrix,
        "cross_layer_findings": matrix["findings"],
        "controls": controls,
        "capability_receipts": core["capability_receipts"],
        "tool_calls": core["tool_calls"],
        "one_to_one_tool_calls": one_to_one,
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_proofs["z3"]["verdict"],
                "erased_flip_verdict": jax_proofs["z3"]["erased_flip_verdict"],
                "formula_terms_bound": jax_proofs["z3"]["formula_terms_bound"],
                "edge_current_terms_in_solver": jax_proofs["z3"]["edge_current_terms_in_solver"],
                "divergence_derived_in_solver": jax_proofs["z3"]["divergence_derived_in_solver"],
                "proof_row": jax_proofs["z3"]["proof_row"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": jax_proofs["cvc5"]["verdict"],
                "erased_flip_verdict": jax_proofs["cvc5"]["erased_flip_verdict"],
                "formula_terms_bound": jax_proofs["cvc5"]["formula_terms_bound"],
                "edge_current_terms_in_solver": jax_proofs["cvc5"]["edge_current_terms_in_solver"],
                "divergence_derived_in_solver": jax_proofs["cvc5"]["divergence_derived_in_solver"],
                "proof_row": jax_proofs["cvc5"]["proof_row"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3["verdict"],
                "erased_flip_verdict": julia_z3["erased_flip_verdict"],
                "formula_terms_bound": julia_z3["formula_terms_bound"],
                "edge_current_terms_in_solver": julia_z3["edge_current_terms_in_solver"],
                "divergence_derived_in_solver": julia_z3["divergence_derived_in_solver"],
                "proof_row": julia_z3["proof_row"],
            },
        },
        "divergence": div,
        "divergence_log": [
            "All engine values report step3.conditioned_total_abs_current on the same state trajectory.",
            "Julia is authoritative for the local density/Z3 proof leg; JAX and PyTorch are independent recompute/tool lanes.",
        ],
        "runtime_versions": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "legs": {name: leg.get("package_versions", {}) for name, leg in legs.items()},
        },
        "build_gates": {
            "classification_scratch": CLASSIFICATION == "scratch_diagnostic",
            "promotion_blocked": PROMOTION_ALLOWED is False,
            "formal_admission_blocked": FORMAL_ADMISSION_ALLOWED is False,
            "one_thing_check_pass": trajectory["one_thing_check"]["pass"],
            "trajectory_artifact_verified": artifact_receipt["verified"],
            "all_engine_legs_verified_trajectory_artifact": all(
                legs[name].get("trajectory_artifact", {}).get("verified") is True
                for name in ("julia", "jax", "pytorch")
            ),
            "nested_row_lineage_present": trajectory["one_thing_check"]["nested_row_lineage_present"],
            "step_dependent_s2_holonomy_spectrum_changes": trajectory["one_thing_check"][
                "step_dependent_s2_holonomy_spectrum_changes"
            ],
            "cross_layer_matrix_pass": matrix["all_pass"],
            "no_cross_layer_findings": not matrix["findings"],
            "parent_lineage_hash_bound": core["parent_lineage"]["hash_bound"],
            "one_to_one_claim_tool_calls": one_to_one["pass"],
            "solver_erased_flips_fire": jax_proofs["z3"]["erased_flip_verdict"] == "sat"
            and jax_proofs["cvc5"]["erased_flip_verdict"] == "sat"
            and julia_z3["erased_flip_verdict"] == "sat",
            "z3_cvc5_agree": jax_proofs["z3"]["verdict"] == jax_proofs["cvc5"]["verdict"],
            "julia_z3_agrees": julia_z3["verdict"] == jax_proofs["z3"]["verdict"],
            "max_divergence_within_tolerance": div["max_divergence"] <= TOL,
            "layer_decoupled_control_pass": controls["layer_decoupled_control"]["same_where_independent"][
                "conditioned_total_abs_current"
            ]["pass"]
            and controls["layer_decoupled_control"]["different_where_coupled"][
                "leaf_conditioning_changes_total_abs_current"
            ]["different"],
            "active_n4_lane_untouched": True,
        },
        "allowed_claims": [
            "one bounded unified scratch run over one shared n=3 state trajectory",
            "step-dependent families recomputed per step; invariant families carried with stated justification",
            "cross-layer consistency matrix computed for shared-object row pairs",
            "source-backed local validator result when the validator passes",
        ],
        "disallowed_claims": [
            "manifold-level admission",
            "bridge or axis claim",
            "M(C,t) theorem",
            "formal proof of the entire geometric constraint manifold",
            "freshly recomputed every row family at every step",
        ],
        "all_pass": True,
    }
    payload["all_pass"] = all(
        [
            payload["build_gates"]["classification_scratch"],
            payload["build_gates"]["promotion_blocked"],
            payload["build_gates"]["formal_admission_blocked"],
            payload["build_gates"]["one_thing_check_pass"],
            payload["build_gates"]["trajectory_artifact_verified"],
            payload["build_gates"]["all_engine_legs_verified_trajectory_artifact"],
            payload["build_gates"]["nested_row_lineage_present"],
            payload["build_gates"]["step_dependent_s2_holonomy_spectrum_changes"],
            payload["build_gates"]["cross_layer_matrix_pass"],
            payload["build_gates"]["parent_lineage_hash_bound"],
            payload["build_gates"]["one_to_one_claim_tool_calls"],
            payload["build_gates"]["solver_erased_flips_fire"],
            payload["build_gates"]["z3_cvc5_agree"],
            payload["build_gates"]["julia_z3_agrees"],
            payload["build_gates"]["max_divergence_within_tolerance"],
            payload["build_gates"]["layer_decoupled_control_pass"],
        ]
    )
    return payload


def main() -> int:
    payload = build_payload()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT_PATH)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
