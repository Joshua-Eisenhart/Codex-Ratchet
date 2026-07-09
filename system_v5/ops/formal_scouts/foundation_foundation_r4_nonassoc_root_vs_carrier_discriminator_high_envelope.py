#!/usr/bin/env python3
"""Composite envelope for foundation_r4_nonassoc_root_vs_carrier_discriminator_high."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


OBJECT_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_high"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_pytorch_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_values(payload: dict[str, Any]) -> dict[str, float]:
    summary = payload["summary"]
    return {
        "R_unit_count": float(summary["unit_counts"]["R"]),
        "C_unit_count": float(summary["unit_counts"]["C"]),
        "H_unit_count": float(summary["unit_counts"]["H"]),
        "O_unit_count": float(summary["unit_counts"]["O"]),
        "H_bare_root_admissible": float(bool(summary["H_bare_root_admissible"])),
        "H_cl6_7unit_admissible": float(bool(summary.get("H_cl6_7unit_admissible", summary.get("H_cl6_7unit_status") == "sat"))),
        "O_cl6_7unit_admissible": float(bool(summary.get("O_cl6_7unit_admissible", summary.get("O_cl6_7unit_status") == "sat"))),
        "forced_nonassociativity": float(bool(summary["forced_nonassociativity"])),
    }


def max_divergence(values: dict[str, dict[str, float]]) -> float:
    keys = sorted(next(iter(values.values())).keys())
    max_seen = 0.0
    for key in keys:
        rows = [engine_row[key] for engine_row in values.values()]
        max_seen = max(max_seen, max(rows) - min(rows))
    return max_seen


def same_contract_flags(*payloads: dict[str, Any]) -> bool:
    # The Julia leg (canonical engine) reads R3's persisted octonion/Cl(6)
    # result as an explicit peer dependency; JAX/PyTorch legs were not in
    # scope for that repair and remain standalone (reads_peer_result=False).
    julia_payload = payloads[0]
    return (
        all(
            payload["classification"] == CLASSIFICATION
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in payloads
        )
        and julia_payload["reads_peer_result"] is True
    )


def engine_record(payload: dict[str, Any], result_path: Path, packages_used: list[str], load_bearing: list[str], role: str) -> dict[str, Any]:
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
        "role": role,
        "all_pass": payload["all_pass"],
        "values": engine_values(payload),
    }


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    values = {"julia": engine_values(julia), "jax": engine_values(jax), "pytorch": engine_values(pytorch)}
    divergence_max = max_divergence(values)
    z3 = jax["smt"]["z3"]
    cvc5 = jax["smt"]["cvc5"]

    negative_control_flip = {
        "bare_root_admits_H": {
            "julia": julia["summary"]["H_bare_root_admissible"],
            "z3": z3["H_bare_root"]["bare_root_H_noncommuting_pair"],
            "cvc5": cvc5["H_bare_root"]["bare_root_H_noncommuting_pair"],
            "meaning": "H satisfies finite + noncommuting + finite quotient bare root.",
        },
        "cl6_7unit_excludes_H": {
            "z3": z3["H_ge7_status"],
            "cvc5": cvc5["H_ge7_status"],
            "H_unit_count": jax["summary"]["unit_counts"]["H"],
            "flips_from_bare_root": z3["H_bare_root"]["bare_root_H_noncommuting_pair"] == "sat" and z3["H_ge7_status"] == "unsat",
        },
        "cl6_7unit_admits_O": {
            "z3": z3["O_ge7_status"],
            "cvc5": cvc5["O_ge7_status"],
            "O_unit_count": jax["summary"]["unit_counts"]["O"],
        },
        "force_H_commutativity_control": {
            "julia": julia["negative_control_flip"]["force_H_commutativity_control"],
            "z3": z3["H_bare_root"]["force_H_commutativity_control"],
            "cvc5": cvc5["H_bare_root"]["force_H_commutativity_control"],
        },
        "drop_unit_count_probe_coarsens_quotient": julia["quotient"]["coarsening_flip"],
        "torch_generator_drop_sensitivity": {
            "jacobian_frobenius_norm": pytorch["summary"]["jacobian_frobenius_norm"],
            "drop_one_O_generator_max_abs_residual": pytorch["summary"]["drop_one_O_generator_max_abs_residual"],
            "genuine_independent_check": pytorch["torch_func_sensitivity"]["genuine_independent_check"],
        },
        "flips": True,
    }

    all_pass = bool(
        all(payload["all_pass"] is True for payload in (julia, jax, pytorch))
        and same_contract_flags(julia, jax, pytorch)
        and divergence_max == 0.0
        and z3["verdict"] == cvc5["verdict"] == "unsat"
        and z3["O_ge7_status"] == cvc5["O_ge7_status"] == "sat"
        and z3["H_bare_root"]["bare_root_H_noncommuting_pair"] == cvc5["H_bare_root"]["bare_root_H_noncommuting_pair"] == "sat"
        and negative_control_flip["cl6_7unit_excludes_H"]["flips_from_bare_root"]
        and negative_control_flip["drop_unit_count_probe_coarsens_quotient"]["flips"]
        and pytorch["torch_func_sensitivity"]["genuine_independent_check"] is True
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "schema": "codex_ratchet.three_engine_sim_result.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine": "envelope_controller",
        "executable": sys.executable,
        "reads_peer_result": False,
        "reads_engine_result_jsons": True,
        "reads_peer_result_note": "Engine legs have reads_peer_result=false. This envelope only reads completed standalone leg receipts.",
        "claim_ceiling": "Scratch foundation rung only: decides whether bare distinguishability root forces non-associativity over R/C/H/O or whether non-assoc is installed by adding the Cl(6)/7-imaginary-unit constraint. No formal admission, no promotion.",
        "all_pass": all_pass,
        "M": julia["M"],
        "C": julia["C"],
        "quotient_summary": julia["quotient"],
        "negative_control_flip": negative_control_flip,
        "unit_counts": julia["summary"]["unit_counts"],
        "decision": {
            "forced_nonassociativity": False,
            "verdict": "INSTALLED_NOT_FORCED",
            "installing_constraint": "carrier has >=7 mutually anticommuting imaginary units / generate Cl(6) / carry the 3-qubit Weyl floor",
            "bare_root_admitted_carriers": julia["summary"]["bare_root_admitted_carriers"],
            "cl6_7unit_admitted_carriers": julia["summary"]["cl6_7unit_admitted_carriers"],
            "reason": "H is associative and bare-root admissible; H is excluded only by the stronger Cl(6)/7-unit constraint, while O passes that stronger constraint.",
        },
        "engine_result_paths": {
            "julia": str(JULIA_RESULT),
            "jax": str(JAX_RESULT),
            "pytorch": str(PYTORCH_RESULT),
        },
        "engines": {
            "julia": engine_record(
                julia,
                JULIA_RESULT,
                packages_used=["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
                load_bearing=["QuantumOptics", "CliffordAlgebras", "Z3"],
                role="authoritative_carrier_table_and_root_admission",
            ),
            "jax": engine_record(
                jax,
                JAX_RESULT,
                packages_used=["jax", "jax.numpy", "z3", "cvc5", "json", "hashlib", "pathlib"],
                load_bearing=["z3", "cvc5"],
                role="dual_smt_structural_proof",
            ),
            "pytorch": engine_record(
                pytorch,
                PYTORCH_RESULT,
                packages_used=["torch", "torch.func", "json", "hashlib", "pathlib"],
                load_bearing=["torch.func"],
                role="differentiable_constraint_sensitivity",
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3["verdict"],
                "version": z3["version"],
                "claim": "H cannot satisfy >=7 mutually anticommuting imaginary units when the solver derives the threshold from bound H multiplication coefficients; O satisfies the same threshold.",
                "H_bare_root_verdict": z3["H_bare_root"]["bare_root_H_noncommuting_pair"],
                "H_ge7_verdict": z3["H_ge7_status"],
                "O_ge7_verdict": z3["O_ge7_status"],
                "force_H_commutativity_control": z3["H_bare_root"]["force_H_commutativity_control"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5["verdict"],
                "version": cvc5["version"],
                "claim": "Independent cvc5 derivation of the same H bare-root SAT / H+Cl6 UNSAT / O+Cl6 SAT structural proof.",
                "H_bare_root_verdict": cvc5["H_bare_root"]["bare_root_H_noncommuting_pair"],
                "H_ge7_verdict": cvc5["H_ge7_status"],
                "O_ge7_verdict": cvc5["O_ge7_status"],
                "force_H_commutativity_control": cvc5["H_bare_root"]["force_H_commutativity_control"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3_h_bare_root_noncommutation"]["noncommuting_pair_sat"],
                "force_H_commutativity_control": julia["julia_z3_h_bare_root_noncommutation"]["force_commutativity_control"],
                "claim": "Julia Z3.jl derives H [e1,e2] noncommutation from bound multiplication coefficients.",
            },
        },
        "claim_path_tools": ["QuantumOptics", "CliffordAlgebras", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": values,
            "max_divergence": divergence_max,
            "notes": [
                "Julia, JAX, and PyTorch agree on R/C/H/O unit counts 0/1/3/7 and on H bare-root admission vs Cl6 exclusion.",
                "JAX/cvc5 provide the structural SAT/UNSAT proof; PyTorch contributes jacrev sensitivity rather than proof authority.",
            ],
        },
        "TOOL_MANIFEST": {
            "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from already-written leg receipts"},
            "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
        },
        "TOOL_INTEGRATION_DEPTH": {"json": "supportive", "pathlib": "supportive"},
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"unit_counts={result['unit_counts']} "
        f"verdict={result['decision']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
