#!/usr/bin/env python3
"""Composite envelope for pg32_sedenion_incidence."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "pg32_sedenion_incidence"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULTS_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULTS_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULTS_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULTS_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULTS_DIR / f"{SIM_ID}_pytorch_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from independent engine receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload.get("source_sha256"),
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": payload.get("packages_used", []),
        "aligned_packages_load_bearing": payload.get("aligned_packages_load_bearing", []),
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "all_pass": payload.get("all_pass"),
        "values": payload.get("shared_scalars", {}),
    }


def scalar_divergence(payloads: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], float]:
    engine_values = {name: payload.get("shared_scalars", {}) for name, payload in payloads.items()}
    common = set.intersection(*(set(values) for values in engine_values.values()))
    spreads: dict[str, Any] = {}
    max_spread = 0.0
    for key in sorted(common):
        values = {name: float(engine_values[name][key]) for name in sorted(engine_values)}
        spread = max(values.values()) - min(values.values())
        max_spread = max(max_spread, spread)
        spreads[key] = {"values": values, "spread": spread, "within_tolerance": spread == 0.0}
    return {"engine_values": engine_values, "scalar_spreads": spreads}, max_spread


def first_non_alt_witness(planes: dict[str, Any]) -> dict[str, Any] | None:
    for row in planes.get("records", []):
        if row.get("classification") != "genuine_octonion_subalgebra":
            return {"plane": row.get("plane"), "witness": row.get("witness")}
    return None


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = {"julia": julia, "jax": jax, "pytorch": pytorch}
    div, max_divergence = scalar_divergence(payloads)

    z3_unsat = jax["smt"]["z3"]["claimed_non_line_unsat"]["verdict"]
    cvc5_unsat = jax["smt"]["cvc5"]["claimed_non_line_unsat"]["verdict"]
    julia_z3_unsat = julia["smt"]["julia_z3"]["claimed_non_line_unsat"]["verdict"]
    z3_zero = jax["smt"]["z3"]["zero_product"]["verdict"]
    cvc5_zero = jax["smt"]["cvc5"]["zero_product"]["verdict"]
    julia_zero = julia["smt"]["julia_z3"]["zero_product"]["verdict"]

    line_count = julia["shared_scalars"]["line_count"]
    pair_axiom_ok = bool(julia["shared_scalars"]["pair_axiom_ok"])
    genuine_planes = julia["shared_scalars"]["genuine_octonion_plane_count"]
    non_alt_planes = julia["shared_scalars"]["non_alternative_plane_count"]
    zero_pair_count = julia["shared_scalars"]["ordered_zero_divisor_pair_count"]
    component_count = julia["shared_scalars"]["zero_divisor_component_count"]

    all_pass = (
        all(payload.get("all_pass") is True for payload in payloads.values())
        and line_count == 35
        and pair_axiom_ok
        and genuine_planes == 8
        and non_alt_planes == 7
        and zero_pair_count == 84
        and component_count == 7
        and max_divergence == 0.0
        and z3_unsat == cvc5_unsat == julia_z3_unsat == "unsat"
        and z3_zero == cvc5_zero == julia_zero == "sat"
        and all(payload.get("reads_peer_result") is False for payload in payloads.values())
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": f"{SIM_ID}_envelope",
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "scratch diagnostic: sedenion structure-constant incidence, plane alternativity split, and two-term zero-divisor graph only; no canonical promotion",
        "all_pass": all_pass,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "lanes": ["julia", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "pytorch_local", "controller_comparison"],
        },
        "construction": julia["construction"],
        "headline": {
            "line_count": line_count,
            "pair_axiom_ok": pair_axiom_ok,
            "plane_classification_split": {
                "genuine_octonion_subalgebra": genuine_planes,
                "closed_non_alternative_sedenion_plane": non_alt_planes,
                "first_failure_witness": first_non_alt_witness(julia["planes"]),
            },
            "zero_divisors": {
                "ordered_pair_count_for_x=e_a+e_b_y=e_c+e_d": zero_pair_count,
                "component_count": component_count,
                "component_sizes": julia["zero_divisors"]["component_sizes"],
                "examples": julia["zero_divisors"]["examples"][:8],
            },
            "controls": {
                "octonion_restriction": julia["controls"]["octonion_restriction"],
                "signed_entry_scramble": julia["controls"]["signed_entry_scramble"],
            },
            "smt_verdicts": {
                "z3_claimed_non_line_line_closure": z3_unsat,
                "cvc5_claimed_non_line_line_closure": cvc5_unsat,
                "julia_z3_claimed_non_line_line_closure": julia_z3_unsat,
                "z3_zero_product": z3_zero,
                "cvc5_zero_product": cvc5_zero,
                "julia_z3_zero_product": julia_zero,
            },
        },
        "incidence": julia["incidence"],
        "planes": julia["planes"],
        "zero_divisors": julia["zero_divisors"],
        "controls": julia["controls"],
        "smt": {"julia": julia["smt"], "jax": jax["smt"]},
        "pytorch_graph_check": {
            "zero_divisors": {
                "ordered_pair_count": pytorch["zero_divisors"]["ordered_zero_divisor_pair_count"],
                "component_count": pytorch["zero_divisors"]["component_count"],
                "component_sizes": pytorch["zero_divisors"]["component_sizes"],
            },
            "torch_func_zero_witness": pytorch["torch_func_zero_witness"],
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
                "verdict": z3_unsat,
                "claim": "Bound C[*][1][2] structure constants cannot close the claimed non-line {1,2,4}; line-closure assertion is UNSAT",
                "line_sat_control": jax["smt"]["z3"]["claimed_line_sat"]["verdict"],
                "line_negation_unsat": jax["smt"]["z3"]["claimed_line_negation_unsat"]["verdict"],
                "non_line_negation_sat": jax["smt"]["z3"]["claimed_non_line_negation_sat"]["verdict"],
                "zero_product_verdict": z3_zero,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_unsat,
                "claim": "Independent cvc5 mirror of the same bound non-line line-closure UNSAT check",
                "line_sat_control": jax["smt"]["cvc5"]["claimed_line_sat"]["verdict"],
                "line_negation_unsat": jax["smt"]["cvc5"]["claimed_line_negation_unsat"]["verdict"],
                "non_line_negation_sat": jax["smt"]["cvc5"]["claimed_non_line_negation_sat"]["verdict"],
                "zero_product_verdict": cvc5_zero,
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia_z3_unsat,
                "claim": "Z3.jl repeats the same bound non-line line-closure UNSAT check and zero-product SAT derivation",
                "zero_product_verdict": julia_zero,
            },
        },
        "divergence": {
            "julia_authoritative": True,
            "comparison_rule": "same-named integer shared scalars across Julia/JAX/PyTorch receipts",
            "engine_values": div["engine_values"],
            "scalar_spreads": div["scalar_spreads"],
            "max_divergence": max_divergence,
        },
        "claim_path_tools": ["Z3", "z3", "cvc5", "jax", "jax.numpy", "torch", "torch.func"],
        "control_only_tools": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ENVELOPE_DONE "
        f"all_pass={str(payload['all_pass']).lower()} "
        f"lines={payload['headline']['line_count']} "
        f"pair_axiom={payload['headline']['pair_axiom_ok']} "
        f"planes={payload['headline']['plane_classification_split']['genuine_octonion_subalgebra']}/"
        f"{payload['headline']['plane_classification_split']['closed_non_alternative_sedenion_plane']} "
        f"zero_pairs={payload['headline']['zero_divisors']['ordered_pair_count_for_x=e_a+e_b_y=e_c+e_d']} "
        f"components={payload['headline']['zero_divisors']['component_count']} "
        f"smt_z3={payload['headline']['smt_verdicts']['z3_claimed_non_line_line_closure']} "
        f"smt_cvc5={payload['headline']['smt_verdicts']['cvc5_claimed_non_line_line_closure']}"
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
