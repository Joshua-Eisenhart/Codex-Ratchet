#!/usr/bin/env python3
"""Envelope for bloch_root_admissibility_discriminator_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "bloch_root_admissibility_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from engine receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hash receipt"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive", "hashlib": "supportive"}
COMMON_VALUE_KEYS = [
    "t2_commuting_dim",
    "t2_noncommuting_dim",
    "t4_norm_law_violation",
    "t5_nonassoc_count",
    "t5_fano_zero_count",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_leg(engine: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{SIM_ID}_{engine}_results.json"
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "reads_peer_result": payload["reads_peer_result"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "pin_sha256": payload["pin_sha256"],
        "values": payload["values"],
        "all_pass": payload["all_pass"],
    }


def divergence(legs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    max_div = 0.0
    max_key = None
    for key in COMMON_VALUE_KEYS:
        values = {engine: float(payload["values"][key]) for engine, payload in legs.items()}
        diff = max(values.values()) - min(values.values())
        rows.append({"key": key, "values": values, "max_abs_diff": diff})
        if diff > max_div:
            max_div = diff
            max_key = key
    return {
        "julia_authoritative": True,
        "engine_values": {engine: payload["values"] for engine, payload in legs.items()},
        "max_divergence": max_div,
        "max_divergence_key": max_key,
        "comparison": {"common_observable_count": len(COMMON_VALUE_KEYS), "rows": rows, "within_tolerance": max_div <= 1.0e-8},
    }


def proof_flip_ok(proof: dict[str, Any]) -> bool:
    return (
        proof["verdict"] == "unsat"
        and proof["P1_sedenion_norm_violation_eq_zero"] == "unsat"
        and proof["P1_octonion_zero_control"] == "sat"
        and proof["P2_noncommuting_rank_leq_2"] == "unsat"
        and proof["P2_commuting_rank_leq_2_control"] == "sat"
        and proof["asserted_precomputed_boolean"] is False
    )


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    legs = {engine: load_leg(engine) for engine in ("julia", "jax", "pytorch")}
    jax_tests = legs["jax"]["tests"]
    julia_tests = legs["julia"]["tests"]
    pytorch_tests = legs["pytorch"]["tests"]

    pin_ok = len({payload["pin_sha256"] for payload in legs.values()}) == 1
    ceiling_ok = all(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in legs.values()
    )
    source_sha_ok = all(bool(payload.get("source_sha256")) for payload in legs.values())

    t1_ok = (
        jax_tests["T1"]["converges_on_sample"]
        and jax_tests["T1"]["control_non_refining_repeated_probes"]["does_not_converge"]
        and all(row["quotient_cardinality_finite"] for row in jax_tests["T1"]["refinement_ladder"])
        and all(row["monotone_nonincreasing_from_previous"] for row in jax_tests["T1"]["refinement_ladder"])
    )
    t2_ok = (
        jax_tests["T2"]["commuting_sigma_z_binned"]["affine_dimension"] == 1
        and jax_tests["T2"]["commuting_sigma_z_binned"]["extreme_points"] == 2
        and jax_tests["T2"]["noncommuting_full_pauli_family"]["affine_dimension"] == 3
        and jax_tests["T2"]["noncommuting_full_pauli_family"]["boundary_sphericity"]["all_norms_leq_1"]
        and jax_tests["T2"]["control_commuting_only_additions"]["never_raises_dimension_above_interval"]
        and pytorch_tests["T2"]["torch_svd_affine_dimensions"]["commuting_sigma_z_binned"] == 1
        and pytorch_tests["T2"]["torch_svd_affine_dimensions"]["noncommuting_full_pauli"] == 3
        and pytorch_tests["T2"]["torch_func_jacobian_ranks"]["full_pauli_probe_map"] == 3
        and pytorch_tests["T2"]["torch_func_jacobian_ranks"]["commuting_probe_map_with_duplicate_bins"] == 1
    )
    t3_ok = (
        jax_tests["T3"]["base_dimensions"] == [1, 2, 4, 8]
        and jax_tests["T3"]["fiber_dimensions"] == [0, 1, 3, 7]
        and julia_tests["T3"]["base_dimensions"] == [1, 2, 4, 8]
        and julia_tests["T3"]["fiber_dimensions"] == [0, 1, 3, 7]
        and pytorch_tests["T3"]["base_dimensions"] == [1, 2, 4, 8]
        and pytorch_tests["T3"]["fiber_dimensions"] == [0, 1, 3, 7]
        and jax_tests["T3"]["label_shuffle_control"]["invariant"]
        and jax_tests["T3"]["orientation_flip_control"]["invariant"]
    )
    t4_ok = (
        jax_tests["T4"]["designed_failure_fired"]
        and jax_tests["T4"]["norm_law_violation_magnitude"] > 0.5
        and jax_tests["T4"]["image_leaves_S16"]["max_abs_norm_minus_1"] > 0.5
        and jax_tests["T4"]["fiber_constancy_break"]["max_deviation"] > 0.1
        and jax_tests["T4"]["sedenion_rung_passed"] is False
        and jax_tests["T4"]["kill_condition_met"] is False
        and julia_tests["T4"]["designed_failure_fired"]
        and pytorch_tests["T4"]["norm_law_violation_magnitude"] > 0.5
    )
    t5_ok = (
        jax_tests["T5"]["two_generated_sets"]["all_zero"]
        and jax_tests["T5"]["nonassociating_triples"] == 168
        and jax_tests["T5"]["fano_line_ordered_triples_zero"] == 42
        and jax_tests["T5"]["label_shuffle_control"]["invariant"]
        and jax_tests["T5"]["orientation_flip_control"]["invariant"]
        and julia_tests["T5"]["two_generated_sets"]["all_zero"]
        and julia_tests["T5"]["nonassociating_triples"] == 168
        and julia_tests["T5"]["fano_line_ordered_triples_zero"] == 42
    )
    z3 = legs["jax"]["crossover_proofs"]["z3"]
    cvc5 = legs["jax"]["crossover_proofs"]["cvc5"]
    proof_ok = proof_flip_ok(z3) and proof_flip_ok(cvc5) and legs["julia"]["crossover_proofs"]["julia_z3"]["verdict"] == "unsat"
    div = divergence(legs)
    all_pass = (
        all(payload["all_pass"] for payload in legs.values())
        and pin_ok
        and ceiling_ok
        and source_sha_ok
        and t1_ok
        and t2_ok
        and t3_ok
        and t4_ok
        and t5_ok
        and proof_ok
        and div["comparison"]["within_tolerance"]
    )
    artifact = jax_tests["T3"]["artifact_policy"]
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
            "reads_peer_result": False,
        },
        "claim": "Bloch sphere/ball and division-algebra Hopf ladder are tested as bounded scratch diagnostics under F01/N01/non-associativity; no carrier admission or physics claim.",
        "allowed_claims": [
            "F01 finite quotient refinement approaches S2 on the measured ladder, with non-refining control failing to converge",
            "N01 noncommuting Pauli probes reconstruct affine dimension 3 while commuting probes stay dimension 1",
            "R/C/H/O Hopf ladder gives base dimensions 1/2/4/8 and fiber dimensions 0/1/3/7",
            "sedenion Cayley-Dickson control fails by norm law, image norm, and fiber-constancy witnesses",
            "octonion alternativity preserves two-generated sets while 168 ordered distinct triples remain nonassociating",
        ],
        "must_not_claim": ["canonical carrier admission", "formal admission", "physics", "primitive Bloch sphere under F01"],
        "claim_path_tools": ["Z3", "z3", "cvc5"],
        "smt_value_encoding": "exact_integer_ok_for_current_values; future non-integer witnesses require scaled integers or exact rationals",
        "zero_divisor_convention_translation": jax_tests["T4"]["zero_divisor_convention_translation"],
        "pytorch_role": legs["pytorch"]["pytorch_role"],
        "canon_runtime": {
            "semantic_owner": "julia",
            "artifact_path": artifact["artifact_path"],
            "artifact_sha256": artifact["artifact_sha256"],
            "source_sha256": artifact["artifact_source_sha256"],
            "receipt_path": "system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json",
            "proof_tag": artifact["proof_tag"],
            "proof_pass": artifact["proof_pass"],
            "table_version": artifact["table_version"],
            "bracket_convention": artifact["bracket_convention"],
            "consumer_policy": "compute from exported C tensor with fixed parenthesization; no carrier admission",
        },
        "foreign_runtime_manifest": {
            "julia": {"project": "system_v5/julia_carrier", "packages": legs["julia"]["packages_used"], "role": "canon algebra table and Z3.jl checks"},
            "jax": {"python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3", "packages": legs["jax"]["packages_used"], "role": "sampling sweeps plus z3/cvc5 proofs"},
            "pytorch": {
                "python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
                "packages": legs["pytorch"]["packages_used"],
                "role": legs["pytorch"]["pytorch_role"],
            },
            "tensor_exchange": "none; engines independently read source artifact or compute local finite witnesses",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "engines": {engine: engine_record(payload) for engine, payload in legs.items()},
        "tests": {
            "T1": jax_tests["T1"],
            "T2": {"jax": jax_tests["T2"], "pytorch": pytorch_tests["T2"]},
            "T3": {"jax": jax_tests["T3"], "julia": julia_tests["T3"], "pytorch": pytorch_tests["T3"]},
            "T4": {"jax": jax_tests["T4"], "julia": julia_tests["T4"], "pytorch": pytorch_tests["T4"]},
            "T5": {"jax": jax_tests["T5"], "julia": julia_tests["T5"]},
        },
        "acceptance_checks": {
            "pin_ok": pin_ok,
            "ceiling_ok": ceiling_ok,
            "source_sha_ok": source_sha_ok,
            "T1_ok": t1_ok,
            "T2_ok": t2_ok,
            "T3_ok": t3_ok,
            "T4_ok": t4_ok,
            "T5_ok": t5_ok,
            "proof_ok": proof_ok,
            "divergence_ok": div["comparison"]["within_tolerance"],
            "validator_commands": [
                f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch {RESULT_PATH}",
                f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed {RESULT_PATH}",
            ],
        },
        "crossover_proofs": {"z3": z3, "cvc5": cvc5, "julia_z3": legs["julia"]["crossover_proofs"]["julia_z3"]},
        "divergence": div,
        "values": legs["jax"]["values"],
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
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "BLOCH_ROOT_ADMISSIBILITY_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"T1={result['acceptance_checks']['T1_ok']} "
        f"T2={result['acceptance_checks']['T2_ok']} "
        f"T3={result['acceptance_checks']['T3_ok']} "
        f"T4={result['acceptance_checks']['T4_ok']} "
        f"T5={result['acceptance_checks']['T5_ok']} "
        f"proof={result['acceptance_checks']['proof_ok']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
