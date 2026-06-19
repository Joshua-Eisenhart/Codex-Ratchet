#!/usr/bin/env python3
"""Composite envelope for foundation_r4_nonassoc_root_vs_carrier_discriminator_low."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


OBJECT_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_low"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_pytorch_results.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path, packages: list[str], load_bearing: list[str], role: str) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": packages,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "role": role,
        "all_pass": payload["all_pass"],
        "values": payload["summary"],
    }


def max_divergence(julia: dict[str, Any], jax: dict[str, Any]) -> float:
    keys = ["R_unit_count", "C_unit_count", "H_unit_count", "O_unit_count"]
    return max(abs(float(julia["summary"][k]) - float(jax["summary"][k])) for k in keys)


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    z3 = jax["smt"]["z3"]
    cvc5 = jax["smt"]["cvc5"]
    divergence = max_divergence(julia, jax)
    negative = {
        "bare_root_admits_H": julia["negative_control_flip"]["bare_root_admits_H"],
        "H_bare_root_z3": z3["H_bare_root"]["verdict"],
        "H_bare_root_cvc5": cvc5["H_bare_root"]["verdict"],
        "H_cl6_z3": z3["H_cl6"]["verdict"],
        "H_cl6_cvc5": cvc5["H_cl6"]["verdict"],
        "O_cl6_z3": z3["O_cl6"]["verdict"],
        "O_cl6_cvc5": cvc5["O_cl6"]["verdict"],
        "forced_nonassoc_under_bare_root": False,
        "installed_constraint": "Cl(6)/>=7 mutually anticommuting imaginary units / 3-qubit Weyl floor",
        "verdict": "INSTALLED_BY_CL6_7_UNIT_CONSTRAINT_NOT_FORCED_BY_BARE_ROOT",
        "flips": julia["negative_control_flip"]["flips"] and jax["negative_control_flip"]["flips"],
    }
    all_pass = bool(
        julia["all_pass"]
        and jax["all_pass"]
        and pytorch["all_pass"]
        and divergence == 0.0
        and z3["verdict"] == cvc5["verdict"] == "unsat"
        and z3["O_cl6"]["verdict"] == cvc5["O_cl6"]["verdict"] == "sat"
        and z3["H_bare_root"]["verdict"] == cvc5["H_bare_root"]["verdict"] == "sat"
        and negative["flips"]
    )
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "schema": "codex_ratchet.three_engine_sim_result.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine": "envelope_controller",
        "executable": sys.executable,
        "reads_peer_result": False,
        "reads_engine_result_jsons": True,
        "claim_ceiling": "Strict scratch foundation rung only: decides forced-vs-installed non-assoc for bare root vs Cl6/7-unit constraint. No promotion or formal admission.",
        "all_pass": all_pass,
        "M": {
            "explicit_probe_family": [
                "finite carrier dimension",
                "imaginary unit square=-1 predicates",
                "pairwise anticommutator zero predicates derived from multiplication table",
                "finite noncommutator witness [e1,e2]",
                "Cl6/>=7 mutually anticommuting imaginary-unit admissibility flag",
            ],
        },
        "C": {
            "state_constraints": ["trace=1", "PSD", "Hermiticity", "normalization"],
            "bare_root_constraints": ["finite carrier", "noncommutation witness", "well-defined finite M quotient"],
            "installing_constraint": "carrier must have >=7 mutually anticommuting imaginary units / generate Cl(6) / carry 3-qubit Weyl floor",
            "density_constraint_witness": julia["density_constraint_witness"],
        },
        "quotient_summary": julia["quotient"],
        "negative_control_flip": negative,
        "decision": {
            "forced_by_bare_distinguishability_root": False,
            "installed_by_downstream_carrier_constraint": True,
            "plain_verdict": "H is associative and noncommutative and satisfies the bare root; H is excluded only after adding the Cl6/>=7 imaginary-unit constraint. Non-assoc is installed, not forced by the bare root.",
        },
        "unit_counts": julia["unit_counts"],
        "engine_result_paths": {"julia": str(JULIA_RESULT), "jax": str(JAX_RESULT), "pytorch": str(PYTORCH_RESULT)},
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"], ["QuantumOptics", "CliffordAlgebras", "Z3"], "authoritative"),
            "jax": engine_record(jax, JAX_RESULT, ["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"], ["z3", "cvc5"], "dual_smt_structural_proof"),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, ["torch", "torch.func", "json", "hashlib", "pathlib"], ["torch.func"], "differentiable_sensitivity_check"),
        },
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": z3["verdict"], "bare_H_verdict": z3["H_bare_root"]["verdict"], "O_cl6_verdict": z3["O_cl6"]["verdict"]},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5["verdict"], "bare_H_verdict": cvc5["H_bare_root"]["verdict"], "O_cl6_verdict": cvc5["O_cl6"]["verdict"]},
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia["unit_counts"],
                "jax": jax["unit_counts"],
                "pytorch": {
                    "H_relaxed_unit_score": pytorch["summary"]["H_relaxed_unit_score"],
                    "O_relaxed_unit_score": pytorch["summary"]["O_relaxed_unit_score"],
                },
            },
            "max_divergence": divergence,
        },
        "claim_path_tools": ["QuantumOptics", "CliffordAlgebras", "Z3", "z3", "cvc5", "torch.func"],
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive envelope assembly"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"FOUNDATION_R4_NONASSOC_ROOT_VS_CARRIER_DISCRIMINATOR_LOW_ENVELOPE_DONE {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
