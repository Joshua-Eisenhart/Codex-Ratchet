#!/usr/bin/env python3
"""Three-engine envelope for R1 N01 noncommutation ordered quotient.

The controller reads completed lane JSON only after the Julia, JAX, and
PyTorch lanes have each computed locally.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_three_engine_foundation_r1_n01_noncommutation_order_quotient_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/three_engine_foundation_r1_n01_noncommutation_order_quotient_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/foundation_r1_n01_noncommutation_order_quotient_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r1_n01_noncommutation_order_quotient_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r1_n01_noncommutation_order_quotient_pytorch_results.json"

OBJECT_ID = "foundation_r1_n01_noncommutation_order_quotient_v1"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
TOL = 1.0e-9

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly after each engine result already exists; not a math claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic binding to the three completed engine receipt paths",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_object_signature(payload: dict[str, Any]) -> dict[str, Any]:
    finite = payload["finite_object"]
    return {
        "hilbert_dimension": finite["hilbert_dimension"],
        "state_ids": finite["state_ids"],
        "probe_ids": finite["probe_ids"],
        "ordered_histories": finite["ordered_histories"],
        "outcome_labels": finite["outcome_labels"],
        "named_positive_witness": finite["named_positive_witness"],
    }


def same_finite_object(*payloads: dict[str, Any]) -> bool:
    signatures = [finite_object_signature(payload) for payload in payloads]
    return all(signature == signatures[0] for signature in signatures[1:])


def same_classifications(*payloads: dict[str, Any]) -> bool:
    keys = [
        ("noncommuting", "classification"),
        ("commuting_control", "classification"),
    ]
    for section, key in keys:
        values = [payload[section][key] for payload in payloads]
        if any(value != values[0] for value in values[1:]):
            return False
    return True


def same_quotient_counts(*payloads: dict[str, Any]) -> bool:
    pairs = [
        (
            payload["quotient"]["noncommuting"]["class_count"],
            payload["quotient"]["commuting_control"]["class_count"],
        )
        for payload in payloads
    ]
    return all(pair == pairs[0] for pair in pairs[1:])


def max_abs(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def engine_record(
    *,
    payload: dict[str, Any],
    result_path: Path,
    packages_used: list[str],
    load_bearing: list[str],
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
        "values": {
            "noncommuting_commutator_norm": payload["noncommuting"]["commutator_norm"],
            "noncommuting_order_gap": payload["noncommuting"]["order_gap"],
            "noncommuting_order_gap_max": payload["noncommuting"]["order_gap_max"],
            "commuting_control_commutator_norm": payload["commuting_control"]["commutator_norm"],
            "commuting_control_order_gap": payload["commuting_control"]["order_gap"],
            "commuting_control_order_gap_max": payload["commuting_control"]["order_gap_max"],
            "noncommuting_quotient_class_count": payload["quotient"]["noncommuting"]["class_count"],
            "commuting_control_quotient_class_count": payload["quotient"]["commuting_control"]["class_count"],
        },
    }


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = [julia, jax, pytorch]

    engine_values = {
        payload["engine"]: {
            "noncommuting_commutator_norm": float(payload["noncommuting"]["commutator_norm"]),
            "noncommuting_order_gap": float(payload["noncommuting"]["order_gap"]),
            "noncommuting_order_gap_max": float(payload["noncommuting"]["order_gap_max"]),
            "commuting_control_commutator_norm": float(payload["commuting_control"]["commutator_norm"]),
            "commuting_control_order_gap": float(payload["commuting_control"]["order_gap"]),
            "commuting_control_order_gap_max": float(payload["commuting_control"]["order_gap_max"]),
            "noncommuting_quotient_class_count": float(payload["quotient"]["noncommuting"]["class_count"]),
            "commuting_control_quotient_class_count": float(payload["quotient"]["commuting_control"]["class_count"]),
        }
        for payload in payloads
    }
    divergence_components = []
    for key in next(iter(engine_values.values())).keys():
        divergence_components.append(max_abs([values[key] for values in engine_values.values()]))
    max_divergence = max(divergence_components)

    z3_main = jax["finite_certificates"]["z3"]["main_status"]
    cvc5_main = jax["finite_certificates"]["cvc5"]["main_status"]
    z3_bad = jax["finite_certificates"]["z3"]["negative_control_status"]
    cvc5_bad = jax["finite_certificates"]["cvc5"]["negative_control_status"]
    julia_z3 = julia["finite_certificates"]["z3"]["verdict"]

    same_object = same_finite_object(*payloads)
    class_match = same_classifications(*payloads)
    quotient_count_match = same_quotient_counts(*payloads)
    engine_peer_reads_false = all(payload["reads_peer_result"] is False for payload in payloads)
    engine_fences_ok = all(
        payload["classification"] == "scratch_diagnostic"
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        for payload in payloads
    )
    lanes_all_pass = all(payload["all_pass"] is True for payload in payloads)
    negative_controls_pass = all(
        all(row["pass"] is True for row in payload["negative_controls"].values())
        for payload in payloads
    )
    all_pass = bool(
        lanes_all_pass
        and same_object
        and class_match
        and quotient_count_match
        and engine_peer_reads_false
        and engine_fences_ok
        and negative_controls_pass
        and max_divergence <= TOL
        and z3_main == cvc5_main == "sat"
        and z3_bad == cvc5_bad == "unsat"
        and julia_z3 == "sat"
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "mode": "all_three_full_sims",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "controller_reads_engine_results_after_lanes": True,
        "engine_lane_reads_peer_result_all_false": engine_peer_reads_false,
        "claim_ceiling": "R1 N01 scratch diagnostic envelope only: finite one-qubit projective-probe ordered-history quotient. Not full M(C), not R0/R1-F01/R2, not formal admission, not canonical, not bridge, not axis, and not physics/gravity/entropy-master evidence.",
        "all_pass": all_pass,
        "finite_object": finite_object_signature(julia),
        "same_finite_object": same_object,
        "same_order_gap_control_classifications": class_match,
        "same_quotient_counts": quotient_count_match,
        "engines": {
            "julia": engine_record(
                payload=julia,
                result_path=JULIA_RESULT,
                packages_used=["QuantumOptics", "Z3", "Symbolics", "LinearAlgebra", "JSON", "Dates"],
                load_bearing=["QuantumOptics", "Z3"],
                authority="reference",
            ),
            "jax": engine_record(
                payload=jax,
                result_path=JAX_RESULT,
                packages_used=["jax", "jax.numpy", "qutip", "z3", "cvc5", "sympy", "numpy", "json"],
                load_bearing=["qutip", "z3", "cvc5", "sympy"],
                authority="rich_mirror",
            ),
            "pytorch": engine_record(
                payload=pytorch,
                result_path=PYTORCH_RESULT,
                packages_used=["torch", "torch.func", "sympy", "json"],
                load_bearing=["torch.func", "sympy"],
                authority="third_substrate_support",
            ),
        },
        "engine_contract": {
            "julia": {"status": "ran", "authority": "reference", "load_bearing_packages": ["QuantumOptics", "Z3"], "result_path": str(JULIA_RESULT), "reads_peer_result": julia["reads_peer_result"]},
            "jax": {"status": "ran", "authority": "rich_mirror", "load_bearing_packages": ["qutip", "z3", "cvc5", "sympy"], "result_path": str(JAX_RESULT), "reads_peer_result": jax["reads_peer_result"]},
            "pytorch": {"status": "ran", "authority": "third_substrate_support", "load_bearing_packages": ["torch", "torch.func", "sympy"], "result_path": str(PYTORCH_RESULT), "reads_peer_result": pytorch["reads_peer_result"]},
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_main,
                "negative_control_verdict": z3_bad,
                "claim": "Exact finite ket0 order-gap certificate: TV(Z_then_X, X_then_Z)=1/2 and contradictory zero-gap condition is unsat.",
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_main,
                "negative_control_verdict": cvc5_bad,
                "claim": "Independent exact finite ket0 order-gap certificate matching z3.",
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3,
                "negative_control_verdict": julia["finite_certificates"]["z3"]["negative_control_verdict"],
            },
        },
        "claim_path_tools": ["QuantumOptics", "Z3", "qutip", "z3", "cvc5", "sympy", "torch", "torch.func"],
        "control_only_tools": ["numpy"],
        "package_observables": {
            "QuantumOptics": julia["package_observables"]["QuantumOptics"],
            "Z3": julia["package_observables"]["Z3"],
            "qutip": jax["package_observables"]["qutip"],
            "z3": jax["package_observables"]["z3"],
            "cvc5": jax["package_observables"]["cvc5"],
            "sympy": jax["package_observables"]["sympy"],
            "torch": pytorch["package_observables"]["torch"],
            "torch.func": pytorch["package_observables"]["torch.func"],
        },
        "ordered_histories": {
            "outcome_order": julia["class_signatures"]["outcome_order"],
            "witness_ket0": julia["ordered_histories"]["witness_ket0"],
            "engine_witnesses": {
                "julia": julia["ordered_histories"]["witness_ket0"],
                "jax": jax["ordered_histories"]["witness_ket0"],
                "pytorch": pytorch["ordered_histories"]["witness_ket0"],
            },
        },
        "quotient": {
            "definition": julia["quotient"]["definition"],
            "noncommuting": julia["quotient"]["noncommuting"],
            "commuting_control": julia["quotient"]["commuting_control"],
            "strict_refinement_observed": julia["quotient"]["strict_refinement_observed"],
        },
        "class_signatures": julia["class_signatures"],
        "noncommuting": {
            "probe_pair": "Z,X",
            "commutator_norm": engine_values["julia"]["noncommuting_commutator_norm"],
            "order_gap": engine_values["julia"]["noncommuting_order_gap"],
            "order_gap_max": engine_values["julia"]["noncommuting_order_gap_max"],
            "classification": julia["noncommuting"]["classification"],
            "witness_state_id": "ket0",
        },
        "commuting_control": {
            "probe_pair": "Z,Z_duplicate",
            "commutator_norm": engine_values["julia"]["commuting_control_commutator_norm"],
            "order_gap": engine_values["julia"]["commuting_control_order_gap"],
            "order_gap_max": engine_values["julia"]["commuting_control_order_gap_max"],
            "classification": julia["commuting_control"]["classification"],
        },
        "negative_controls": {
            "engine_controls_pass": negative_controls_pass,
            "commuting_duplicate_Z_has_zero_order_gap_all_states": julia["negative_controls"]["commuting_duplicate_Z_has_zero_order_gap_all_states"],
            "noncommuting_ZX_has_nonzero_commutator": julia["negative_controls"]["noncommuting_ZX_has_nonzero_commutator"],
            "finite_witness_ket0_has_nonzero_order_gap": julia["negative_controls"]["finite_witness_ket0_has_nonzero_order_gap"],
            "noncommuting_quotient_refines_commuting_control": julia["negative_controls"]["noncommuting_quotient_refines_commuting_control"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max_divergence,
            "structural_disagreements": [] if max_divergence <= TOL and same_object and class_match else ["engine mismatch detected"],
            "interpretation": "Agreement is bounded to this finite R1 N01 scratch object; divergence would block any broader use.",
        },
        "verification": {
            "lanes_all_pass": lanes_all_pass,
            "same_finite_object": same_object,
            "same_order_gap_control_classifications": class_match,
            "same_quotient_counts": quotient_count_match,
            "engine_lane_reads_peer_result_all_false": engine_peer_reads_false,
            "engine_fences_ok": engine_fences_ok,
            "negative_controls_pass": negative_controls_pass,
            "max_divergence_within_tol": max_divergence <= TOL,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"same_finite_object={str(result['same_finite_object']).lower()} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"noncommuting_order_gap={result['noncommuting']['order_gap']} "
        f"commuting_control_order_gap={result['commuting_control']['order_gap']} "
        f"noncommuting_classes={result['quotient']['noncommuting']['class_count']} "
        f"commuting_control_classes={result['quotient']['commuting_control']['class_count']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
