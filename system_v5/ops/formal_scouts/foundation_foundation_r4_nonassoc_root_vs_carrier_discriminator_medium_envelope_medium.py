#!/usr/bin/env python3
"""Composite envelope for the R4 nonassoc root/carrier discriminator rung."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_medium"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_envelope_medium.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_envelope_medium_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_julia_medium_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_jax_medium_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_pytorch_medium_results.json"


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
        "values": payload["values"],
    }


def max_divergence(julia_values: dict[str, Any], jax_values: dict[str, Any]) -> float:
    diffs = []
    for key in ("R", "C", "H", "O"):
        diffs.append(abs(float(julia_values["unit_counts"][key]) - float(jax_values["unit_counts"][key])))
    return max(diffs)


def main() -> int:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    z3_verdict = jax["smt_structural_proof"]["z3"]["H_Cl6_7_unit"]["verdict"]
    cvc5_verdict = jax["smt_structural_proof"]["cvc5"]["H_Cl6_7_unit"]["verdict"]
    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and z3_verdict == cvc5_verdict == "unsat"
        and jax["smt_structural_proof"]["z3"]["H_bare_root"]["verdict"] == "sat"
        and jax["smt_structural_proof"]["z3"]["O_Cl6_7_unit"]["verdict"] == "sat"
        and julia["decision"]["verdict"] == jax["decision"]["verdict"] == "INSTALLED_NOT_FORCED"
    )
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": RUNG_ID,
        "classification": "scratch_diagnostic",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch diagnostic foundation rung only: non-associativity is not promoted as forced by the bare root.",
        "all_pass": all_pass,
        "M": {
            "finite_probe_family": "coordinate probes on finite carrier basis plus Z/X noncommutation probe; Cl6 control adds seven pairwise anticommuting imaginary-unit probes",
            "H_bare_M": julia["M"]["finite_probe_family"],
        },
        "C": {
            "bare_root_constraints": ["finite carrier", "unital normalized basis", "noncommuting Z/X analog", "well-defined coordinate-probe quotient"],
            "installed_constraint": ">=7 mutually anticommuting imaginary units / Cl(6) / 3-qubit Weyl floor",
            "state_constraints_note": "trace=1, PSD, and Hermiticity are state-rung constraints; this carrier rung records the corresponding unit/star/normalization carrier constraints instead of claiming a density matrix.",
        },
        "S_quotient_under_M": {
            "relation": "a ~_M b iff all finite probes agree",
            "H_bare_root": "admitted; coordinate quotient rank 4",
            "H_with_installed_Cl6_constraint": "excluded",
            "O_with_installed_Cl6_constraint": "admitted",
        },
        "negative_control": {
            "H_bare_root_admissible": julia["negative_control"]["bare_root_admits_H"],
            "H_excluded_only_after_Cl6_constraint": julia["negative_control"]["add_Cl6_7_unit_constraint_excludes_H"],
            "O_admitted_by_Cl6_constraint": julia["negative_control"]["add_Cl6_7_unit_constraint_admits_O"],
            "z3_H_bare_to_Cl6_flip": jax["negative_control"]["erase_flip"]["sat_to_unsat"],
            "cvc5_H_bare_to_Cl6_flip": jax["smt_structural_proof"]["cvc5"]["H_bare_root"]["verdict"] == "sat" and cvc5_verdict == "unsat",
            "pytorch_H8_to_O_penalty_flip": pytorch["negative_control"]["flips"],
        },
        "decision": {
            "forced_by_bare_root": False,
            "installed_by_constraint": ">=7 mutually anticommuting imaginary units / Cl(6) / 3-qubit Weyl floor",
            "verdict": "INSTALLED_NOT_FORCED",
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
                "verdict": z3_verdict,
                "claim": "H cannot satisfy the installed >=7 mutually anticommuting imaginary-unit / Cl(6) constraint",
                "positive_control_H_bare_root_verdict": jax["smt_structural_proof"]["z3"]["H_bare_root"]["verdict"],
                "positive_control_O_Cl6_verdict": jax["smt_structural_proof"]["z3"]["O_Cl6_7_unit"]["verdict"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "claim": "H cannot satisfy the installed >=7 mutually anticommuting imaginary-unit / Cl(6) constraint",
                "positive_control_H_bare_root_verdict": jax["smt_structural_proof"]["cvc5"]["H_bare_root"]["verdict"],
                "positive_control_O_Cl6_verdict": jax["smt_structural_proof"]["cvc5"]["O_Cl6_7_unit"]["verdict"],
            },
        },
        "claim_path_tools": ["CliffordAlgebras", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia["values"],
                "jax": jax["values"],
                "pytorch": pytorch["values"],
            },
            "max_divergence": max_divergence(julia["values"], jax["values"]),
        },
        "TOOL_MANIFEST": {
            "CliffordAlgebras": {"tried": True, "used": True, "reason": "Julia authoritative finite carrier algebra reference and Cl(0,2)/Cl(0,6) dimensions"},
            "z3": {"tried": True, "used": True, "reason": "JAX leg load-bearing SMT derivation of H bare SAT and H Cl6 UNSAT from product coefficients"},
            "cvc5": {"tried": True, "used": True, "reason": "independent SMT agreement with z3 over the same derived product-coefficient constraints"},
            "torch.func": {"tried": True, "used": True, "reason": "differentiable sensitivity check for the H8-to-O Cl6 penalty flip"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "CliffordAlgebras": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch.func": "load_bearing",
        },
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(f"SCOUT_DONE all_pass={all_pass} counts={result['divergence']['engine_values']['julia']['unit_counts']} z3={z3_verdict} cvc5={cvc5_verdict} max_divergence={result['divergence']['max_divergence']}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
