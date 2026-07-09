#!/usr/bin/env python3
"""Composite envelope for foundation_r4_mc_profile_v0.

The engine legs compute independently. This controller only reads their
completed result JSONs and binds them into the three-engine envelope contract.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_r4_mc_profile_v0_three_engine_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_mc_profile_v0_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r4_mc_profile_v0_julia_leg_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_jax_leg_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_pytorch_leg_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(
    payload: dict[str, Any],
    result_path: Path,
    packages_used: list[str],
    load_bearing: list[str],
    values: dict[str, Any],
    authority: str,
) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "authority": authority,
        "values": values,
    }


def max_abs_diff(left: dict[str, float], right: dict[str, float], keys: list[str]) -> float:
    return max(abs(left[key] - right[key]) for key in keys)


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = {
        "admitted_cardinality": float(julia["profile"]["admitted_cardinality"]),
        "full_M_class_count": float(julia["profile"]["full_M"]["class_count"]),
        "drop_P_yplus_class_count": float(julia["profile"]["drop_P_yplus"]["class_count"]),
        "force_commuting_cardinality": float(julia["profile"]["force_commuting_with_P_z0_admitted_cardinality"]),
    }
    jax_values = {
        "admitted_cardinality": float(jax["profile"]["admitted_cardinality"]),
        "full_M_class_count": float(jax["profile"]["full_M_class_count"]),
        "drop_P_yplus_class_count": float(jax["profile"]["drop_P_yplus_class_count"]),
        "force_commuting_cardinality": float(jax["profile"]["force_commuting_with_P_z0_admitted_cardinality"]),
    }
    pytorch_values = {
        "boundary_parameter": pytorch["boundary_parameter"],
        "boundary_psd_det_margin": pytorch["rows"][1]["psd_det_margin"],
        "boundary_d_psd_det_margin_dt": pytorch["rows"][1]["d_psd_det_margin_dt"],
        "control_t_0p75_psd_det_margin": pytorch["rows"][3]["psd_det_margin"],
    }
    compare_keys = ["admitted_cardinality", "full_M_class_count", "drop_P_yplus_class_count", "force_commuting_cardinality"]
    max_divergence = max_abs_diff(julia_values, jax_values, compare_keys)
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    engine_payloads = [julia, jax, pytorch]
    engine_fences_ok = all(
        payload["classification"] == "scratch_diagnostic"
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        and payload.get("rung_reclassified_from_r4_to_r2") is True
        and payload["all_pass"] is True
        for payload in engine_payloads
    )
    flip = jax["negative_control_flip"]
    flip_ok = all(row["before"] == "unsat" and row["z3_after"] == "sat" and row["cvc5_after"] == "sat" for row in flip.values())
    all_pass = bool(
        engine_fences_ok
        and max_divergence == 0.0
        and z3_verdict == cvc5_verdict == "unsat"
        and flip_ok
        and julia["profile"]["drop_probe_coarsens_quotient"] is True
        and julia["profile"]["force_commuting_changes_profile"] is True
        and julia["convex_closure"]["all_pairwise_midpoints_admitted"] is True
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Reclassified R2 M(C) profile v0 (not R4) scratch diagnostic only: finite probe-family quotient under explicit density/admissibility constraints on a generic qubit; no octonion/Cl(6) carrier dependency exists. No promotion, no formal admission, no bridge or axis-level claim.",
        "rung_reclassified_from_r4_to_r2": True,
        "rung_reclassification_reason": "All three engine legs profile a generic qubit Bloch-sphere family with zero derivation link to R3's admitted octonion/Cl(6) carrier; per the R4 reopen review, this object is demoted to R2 rather than asserting a fake R3 dependency.",
        "all_pass": all_pass,
        "M_probe_family": julia["M_probe_family"],
        "C_constraints": julia["C_constraints"],
        "quotient_relation": julia["quotient_relation"],
        "mc_profile_summary": {
            "grid_cardinality": julia["profile"]["grid_cardinality"],
            "admitted_cardinality": julia["profile"]["admitted_cardinality"],
            "full_M_class_count": julia["profile"]["full_M"]["class_count"],
            "drop_P_yplus_class_count": julia["profile"]["drop_P_yplus"]["class_count"],
            "drop_probe_coarsens_quotient": julia["profile"]["drop_probe_coarsens_quotient"],
            "force_commuting_with_P_z0_admitted_cardinality": julia["profile"]["force_commuting_with_P_z0_admitted_cardinality"],
            "force_commuting_changes_profile": julia["profile"]["force_commuting_changes_profile"],
            "convex_closure_holds": julia["convex_closure"]["all_pairwise_midpoints_admitted"],
            "convex_midpoint_ordered_pair_count": julia["convex_closure"]["ordered_pair_count"],
        },
        "negative_control_flip": flip,
        "negative_controls": {
            "excluded_unsat_under_C": {
                name: {
                    "z3": jax["controls"][name]["z3_status_under_C"],
                    "cvc5": jax["controls"][name]["cvc5_status_under_C"],
                    "computed_values": jax["controls"][name]["computed_values"],
                }
                for name in ["non_psd_inside_probe_bounds", "trace_not_one", "probe_upper_bound_z0", "probe_prob_gt_1"]
            },
            "drop_constraint_flips": flip,
        },
        "engines": {
            "julia": engine_record(
                julia,
                JULIA_RESULT,
                ["QuantumOptics", "LinearAlgebra", "JSON", "SHA", "Dates"],
                ["QuantumOptics"],
                julia_values,
                "authoritative",
            ),
            "jax": engine_record(
                jax,
                JAX_RESULT,
                ["jax", "jax.numpy", "z3", "cvc5", "json"],
                ["z3", "cvc5"],
                jax_values,
                "structural_smt",
            ),
            "pytorch": engine_record(
                pytorch,
                PYTORCH_RESULT,
                ["torch", "torch.func", "json"],
                ["torch.func"],
                pytorch_values,
                "differentiable_boundary_support",
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "claim": jax["crossover_proofs"]["z3"]["claim"],
                "erase_flip_verdicts": jax["crossover_proofs"]["z3"]["erase_flip_verdicts"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "claim": jax["crossover_proofs"]["cvc5"]["claim"],
                "erase_flip_verdicts": jax["crossover_proofs"]["cvc5"]["erase_flip_verdicts"],
            },
        },
        "claim_path_tools": ["QuantumOptics", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values},
            "max_divergence": max_divergence,
            "notes": [
                "Julia and JAX independently profile the finite M(C) grid and quotient counts.",
                "PyTorch is not a quotient mirror; it supplies torch.func jacrev sensitivity of the PSD boundary family.",
            ],
        },
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive result-envelope assembly from completed engine receipts"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"admitted={result['mc_profile_summary']['admitted_cardinality']} "
        f"classes={result['mc_profile_summary']['full_M_class_count']} "
        f"drop_y_classes={result['mc_profile_summary']['drop_P_yplus_class_count']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
