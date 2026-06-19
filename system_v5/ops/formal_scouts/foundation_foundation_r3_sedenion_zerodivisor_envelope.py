#!/usr/bin/env python3
"""Composite envelope for the sedenion zero-divisor foundation rung."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_sedenion_zerodivisor"
OBJECT_ID = "foundation_foundation_r3_sedenion_zerodivisor_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_sedenion_zerodivisor_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r3_sedenion_zerodivisor_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
    }


def max_divergence(julia: dict[str, Any], jax: dict[str, Any]) -> float:
    pairs = [
        (
            julia["octonion"]["zero_divisor_probe"]["zero_product_pair_count"],
            jax["octonion"]["zero_divisor_probe"]["zero_product_pair_count"],
        ),
        (
            julia["octonion"]["fixed_control"]["product_normsq"],
            jax["octonion"]["fixed_control"]["product_normsq"],
        ),
        (
            julia["sedenion"]["concrete_witness"]["product_normsq"],
            jax["sedenion"]["concrete_witness"]["product_normsq"],
        ),
        (
            julia["sedenion"]["concrete_witness"]["norm_multiplicativity_defect"],
            jax["sedenion"]["concrete_witness"]["norm_multiplicativity_defect"],
        ),
        (
            julia["octonion"]["norm_multiplicativity"]["nonzero_coeff_count"],
            jax["octonion"]["norm_multiplicativity"]["nonzero_coeff_count"],
        ),
        (
            julia["sedenion"]["norm_multiplicativity"]["nonzero_coeff_count"],
            jax["sedenion"]["norm_multiplicativity"]["nonzero_coeff_count"],
        ),
    ]
    return max(abs(float(a) - float(b)) for a, b in pairs)


def main() -> int:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    z3_s = jax["smt"]["z3"]["sedenion_witness"]["verdict"]
    cvc5_s = jax["smt"]["cvc5"]["sedenion_witness"]["verdict"]
    z3_o = jax["smt"]["z3"]["octonion_control"]["verdict"]
    cvc5_o = jax["smt"]["cvc5"]["octonion_control"]["verdict"]
    divergence_value = max_divergence(julia, jax)
    all_pass = (
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_s == cvc5_s == "sat"
        and z3_o == cvc5_o == "unsat"
        and jax["negative_control"]["drop_product_zero_probe_for_O"]["flips"] is True
        and jax["negative_control"]["erase_O_structure_constants"]["flips"] is True
        and divergence_value == 0.0
    )
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch diagnostic foundation rung only: O/S Cayley-Dickson zero-divisor boundary under explicit finite M. No promotion, no formal admission, no bridge or axis-level claim.",
        "M": julia["M"],
        "C": julia["C"],
        "S_quotient_under_M": julia["S_quotient_under_M"],
        "substantive_values": {
            "concrete_sedenion_zero_divisor": julia["sedenion"]["concrete_witness"],
            "octonion_fixed_control": julia["octonion"]["fixed_control"],
            "octonion_zero_divisor_count_under_M": julia["octonion"]["zero_divisor_probe"]["zero_product_pair_count"],
            "octonion_norm_multiplicativity_identity_holds": julia["octonion"]["norm_multiplicativity"]["identity_holds"],
            "sedenion_norm_multiplicativity_identity_holds": julia["sedenion"]["norm_multiplicativity"]["identity_holds"],
            "sedenion_norm_defect_nonzero_coeff_count": julia["sedenion"]["norm_multiplicativity"]["nonzero_coeff_count"],
        },
        "negative_control_flip_result": {
            "S_vs_O_solver_flip": jax["negative_control"]["S_vs_O_solver_flip"],
            "drop_product_zero_probe_for_O": jax["negative_control"]["drop_product_zero_probe_for_O"],
            "erase_O_structure_constants": jax["negative_control"]["erase_O_structure_constants"],
            "pytorch_defect_flip": pytorch["negative_control"]["O_to_S_defect_flip"],
        },
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT),
            "jax": engine_record(jax, JAX_RESULT),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_s,
                "claim": "Bound S witness components have zero product when product is derived inside solver from computed S table constants",
                "product_derived_in_solver": True,
                "octonion_control_verdict": z3_o,
                "drop_product_zero_probe_for_O_verdict": jax["smt"]["z3"]["octonion_drop_product_probe"]["verdict"],
                "erase_O_structure_constants_verdict": jax["smt"]["z3"]["octonion_zero_structure"]["verdict"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_s,
                "claim": "Bound S witness components have zero product when product is derived inside solver from computed S table constants",
                "product_derived_in_solver": True,
                "octonion_control_verdict": cvc5_o,
                "drop_product_zero_probe_for_O_verdict": jax["smt"]["cvc5"]["octonion_drop_product_probe"]["verdict"],
                "erase_O_structure_constants_verdict": jax["smt"]["cvc5"]["octonion_zero_structure"]["verdict"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["smt"]["Z3"]["sedenion_witness_verdict"],
                "product_derived_in_solver": True,
                "octonion_control_verdict": julia["smt"]["Z3"]["octonion_control_verdict"],
            },
        },
        "claim_path_tools": ["CliffordAlgebras", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": {
                    "O_zero_divisor_count": julia["octonion"]["zero_divisor_probe"]["zero_product_pair_count"],
                    "O_control_product_normsq": julia["octonion"]["fixed_control"]["product_normsq"],
                    "S_witness_product_normsq": julia["sedenion"]["concrete_witness"]["product_normsq"],
                    "S_witness_norm_defect": julia["sedenion"]["concrete_witness"]["norm_multiplicativity_defect"],
                    "O_norm_defect_coeff_count": julia["octonion"]["norm_multiplicativity"]["nonzero_coeff_count"],
                    "S_norm_defect_coeff_count": julia["sedenion"]["norm_multiplicativity"]["nonzero_coeff_count"],
                },
                "jax": {
                    "O_zero_divisor_count": jax["octonion"]["zero_divisor_probe"]["zero_product_pair_count"],
                    "O_control_product_normsq": jax["octonion"]["fixed_control"]["product_normsq"],
                    "S_witness_product_normsq": jax["sedenion"]["concrete_witness"]["product_normsq"],
                    "S_witness_norm_defect": jax["sedenion"]["concrete_witness"]["norm_multiplicativity_defect"],
                    "O_norm_defect_coeff_count": jax["octonion"]["norm_multiplicativity"]["nonzero_coeff_count"],
                    "S_norm_defect_coeff_count": jax["sedenion"]["norm_multiplicativity"]["nonzero_coeff_count"],
                },
                "pytorch": {
                    "S_witness_product_normsq": pytorch["sedenion_witness"]["product_normsq"],
                    "S_witness_norm_defect": pytorch["sedenion_witness"]["norm_multiplicativity_defect"],
                    "jacrev_defect_gradient": pytorch["sedenion_witness"]["jacrev_defect_gradient"],
                    "O_control_product_normsq": pytorch["octonion_control"]["product_normsq"],
                    "O_control_norm_defect": pytorch["octonion_control"]["norm_multiplicativity_defect"],
                },
            },
            "max_divergence": divergence_value,
        },
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent engine receipts"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"S_witness={payload['substantive_values']['concrete_sedenion_zero_divisor']['claim']} "
        f"S_product_normsq={payload['substantive_values']['concrete_sedenion_zero_divisor']['product_normsq']} "
        f"O_product_normsq={payload['substantive_values']['octonion_fixed_control']['product_normsq']} "
        f"z3_S={z3_s} cvc5_S={cvc5_s} "
        f"z3_O={z3_o} cvc5_O={cvc5_o} "
        f"max_divergence={divergence_value}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
