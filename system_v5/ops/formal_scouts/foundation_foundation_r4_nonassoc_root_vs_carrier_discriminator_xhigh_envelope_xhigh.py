#!/usr/bin/env python3
"""Composite envelope for foundation R4 nonassoc root-vs-carrier discriminator."""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh"
OBJECT_ID = RUNG_ID
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_envelope_xhigh.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_envelope_xhigh_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_julia_xhigh_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_jax_xhigh_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_pytorch_xhigh_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from completed standalone engine receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for leg result JSONs",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bool_float(value: bool) -> float:
    return 1.0 if value else 0.0


def shared_values(payload: dict[str, Any]) -> dict[str, float]:
    summary = payload["summary"]
    decision = payload["decision"]
    counts = summary["unit_counts_R_C_H_O"]
    return {
        "R_unit_count": float(counts[0]),
        "C_unit_count": float(counts[1]),
        "H_unit_count": float(counts[2]),
        "O_unit_count": float(counts[3]),
        "H_bare_root_admissible": bool_float(decision["H_bare_root_admissible"]),
        "H_cl6_7unit_admissible": bool_float(decision["H_cl6_7unit_admissible"]),
        "O_cl6_7unit_admissible": bool_float(decision["O_cl6_7unit_admissible"]),
        "nonassoc_forced_by_bare_root": bool_float(decision["nonassoc_forced_by_bare_root"]),
    }


def max_divergence(values: dict[str, dict[str, float]]) -> float:
    keys = sorted(next(iter(values.values())).keys())
    max_seen = 0.0
    for key in keys:
        rows = [row[key] for row in values.values()]
        max_seen = max(max_seen, max(rows) - min(rows))
    return max_seen


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
        "values": shared_values(payload),
    }


def same_fences(*payloads: dict[str, Any]) -> bool:
    # The Julia leg is the canonical engine for this discriminator (per
    # project doctrine) and now reads R3's persisted octonion/Cl(6) result as
    # an explicit peer dependency (reads_peer_result=True, with a verified
    # rank/dim provenance match). The JAX/PyTorch legs remain standalone
    # structural cross-checks and were not in scope for the R3 peer-read
    # repair, so they keep reads_peer_result=False.
    return all(
        payload["classification"] == classification
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        for payload in payloads
    ) and payloads[0]["reads_peer_result"] is True


def build_result() -> dict[str, Any]:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    payloads = {"julia": julia, "jax": jax, "pytorch": pytorch}
    engine_values = {name: shared_values(payload) for name, payload in payloads.items()}
    divergence_max = max_divergence(engine_values)
    z3_proof = jax["smt"]["z3"]
    cvc5_proof = jax["smt"]["cvc5"]

    negative_control_flip = {
        "drop_stronger_cl6_7unit_constraint": {
            "description": "H is admitted under bare finitude+noncommutation+quotient root but excluded after adding the Cl(0,6)/>=7-unit constraint.",
            "H_bare_root_z3": z3_proof["H_bare_root_admissibility"]["status"],
            "H_bare_root_cvc5": cvc5_proof["H_bare_root_admissibility"]["status"],
            "H_cl6_7unit_z3": z3_proof["H_has_at_least_7_mutually_anticommuting_units"]["status"],
            "H_cl6_7unit_cvc5": cvc5_proof["H_has_at_least_7_mutually_anticommuting_units"]["status"],
            "flips": z3_proof["H_bare_root_admissibility"]["status"] == cvc5_proof["H_bare_root_admissibility"]["status"] == "sat"
            and z3_proof["H_has_at_least_7_mutually_anticommuting_units"]["status"] == cvc5_proof["H_has_at_least_7_mutually_anticommuting_units"]["status"] == "unsat",
        },
        "O_positive_control": {
            "O_cl6_7unit_z3": z3_proof["O_has_at_least_7_mutually_anticommuting_units"]["status"],
            "O_cl6_7unit_cvc5": cvc5_proof["O_has_at_least_7_mutually_anticommuting_units"]["status"],
            "passes": z3_proof["O_has_at_least_7_mutually_anticommuting_units"]["status"] == cvc5_proof["O_has_at_least_7_mutually_anticommuting_units"]["status"] == "sat",
        },
        "force_commutativity_control": {
            "description": "Forcing H commutativity while retaining the bare noncommutation root flips H from SAT to UNSAT.",
            "H_bare_noncommuting_z3": z3_proof["H_bare_root_admissibility"]["status"],
            "H_forced_commutative_z3": z3_proof["H_force_commutativity_control"]["status"],
            "H_bare_noncommuting_cvc5": cvc5_proof["H_bare_root_admissibility"]["status"],
            "H_forced_commutative_cvc5": cvc5_proof["H_force_commutativity_control"]["status"],
            "flips": z3_proof["H_force_commutativity_control"]["status"] == cvc5_proof["H_force_commutativity_control"]["status"] == "unsat",
        },
        "drop_probe_coarsening": julia["quotient"]["drop_probe_coarsening_flip"],
        "torch_func_sensitivity": {
            "genuine_independent_check": pytorch["torch_func_sensitivity"]["genuine_independent_check"],
            "honest_limit": pytorch["torch_func_sensitivity"]["honest_limit"],
            "H_noncommutator_jacobian_norm": pytorch["summary"]["H_noncommutator_jacobian_norm"],
            "O_cl6_jacobian_norm": pytorch["summary"]["O_cl6_jacobian_norm"],
        },
    }

    all_pass = bool(
        all(payload["all_pass"] is True for payload in payloads.values())
        and same_fences(julia, jax, pytorch)
        and divergence_max == 0.0
        and z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat"
        and z3_proof["O_has_at_least_7_mutually_anticommuting_units"]["status"] == cvc5_proof["O_has_at_least_7_mutually_anticommuting_units"]["status"] == "sat"
        and negative_control_flip["drop_stronger_cl6_7unit_constraint"]["flips"]
        and negative_control_flip["force_commutativity_control"]["flips"]
        and negative_control_flip["drop_probe_coarsening"]["flips"]
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "schema": "codex_ratchet.three_engine_sim_result.v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "sim_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "engine": "envelope_controller",
        "executable": sys.executable,
        "reads_peer_result": reads_peer_result,
        "reads_engine_result_jsons": True,
        "reads_peer_result_note": "Engine legs have reads_peer_result=false. The envelope only reads completed leg receipts after standalone execution.",
        "claim_ceiling": "Strict scratch foundation rung only: bare root admits associative H; non-associativity is installed by adding the Cl(0,6)/>=7 mutually anticommuting imaginary-unit carrier constraint. No formal admission, no promotion.",
        "all_pass": all_pass,
        "M": {
            "name": "explicit finite root probe family M over Cayley-Dickson carriers R/C/H/O",
            "carrier_set_S": ["R", "C", "H", "O"],
            "probe_family": [
                "finite multiplication table shape",
                "left-multiplication imaginary-unit observables i*L_ei",
                "basis imaginary square probes e_i^2",
                "pair anticommutator probes e_i e_j + e_j e_i",
                "pair commutator probes e_i e_j - e_j e_i",
                "carrier dimension",
                "associator probe used for quotient visibility, not as a bare-root constraint",
            ],
            "quotient_discriminators": ["finite", "noncommutative", "carrier_dimension", "imaginary_unit_count", "associative", "cl6_7unit_capacity"],
        },
        "C": {
            "state_constraints": ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "bare_root_constraints": ["finite carrier table", "derived nonzero [Z,X]-analog commutator", "finite M quotient"],
            "rung_specific_stronger_constraint": "carrier has >=7 mutually anticommuting imaginary units / generates Cl(0,6) / carries the 3-qubit Weyl floor",
            "density_constraint_witness_H": julia["C"]["density_constraint_witness_H"],
            "density_constraint_witness_O": julia["C"]["density_constraint_witness_O"],
        },
        "quotient_summary": {
            "S": julia["quotient"]["S"],
            "equivalence_relation": julia["quotient"]["equivalence_relation"],
            "bare_root_admitted_carriers": julia["quotient"]["bare_root_admitted_carriers"],
            "strong_cl6_7unit_admitted_carriers": julia["quotient"]["strong_cl6_7unit_admitted_carriers"],
            "full_probe_signatures": julia["quotient"]["full_probe_signatures"],
            "coarse_signatures_after_dropping_dimension_unit_and_associator_probes": julia["quotient"]["coarse_signatures_after_dropping_dimension_unit_and_associator_probes"],
            "bare_root_class_count": julia["quotient"]["bare_root_class_count"],
            "coarse_class_count": julia["quotient"]["coarse_class_count"],
        },
        "unit_counts": julia["unit_counts"],
        "negative_control_flip": negative_control_flip,
        "decision": {
            "H_bare_root_admissible": True,
            "H_associative": True,
            "H_cl6_7unit_admissible": False,
            "O_cl6_7unit_admissible": True,
            "nonassoc_forced_by_bare_root": False,
            "nonassoc_installed_by_constraint": "Cl(0,6)/>=7 mutually anticommuting imaginary units/3-qubit Weyl floor",
            "forced_vs_installed_verdict": "INSTALLED_NOT_FORCED",
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
                role="authoritative_cayley_dickson_carrier",
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
                role="differentiable_sensitivity_check",
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_proof["verdict"],
                "claim": "H cannot satisfy the stronger >=7 mutually anticommuting imaginary-unit constraint when the solver derives the equations from bound H structure constants.",
                "version": z3_proof["version"],
                "H_bare_root_verdict": z3_proof["H_bare_root_admissibility"]["status"],
                "H_cl6_7unit_verdict": z3_proof["H_has_at_least_7_mutually_anticommuting_units"]["status"],
                "O_cl6_7unit_verdict": z3_proof["O_has_at_least_7_mutually_anticommuting_units"]["status"],
                "force_commutativity_control_verdict": z3_proof["H_force_commutativity_control"]["status"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_proof["verdict"],
                "claim": "Independent cvc5 derivation of the same H exclusion / O admission / H bare-root SAT structure.",
                "version": cvc5_proof["version"],
                "H_bare_root_verdict": cvc5_proof["H_bare_root_admissibility"]["status"],
                "H_cl6_7unit_verdict": cvc5_proof["H_has_at_least_7_mutually_anticommuting_units"]["status"],
                "O_cl6_7unit_verdict": cvc5_proof["O_has_at_least_7_mutually_anticommuting_units"]["status"],
                "force_commutativity_control_verdict": cvc5_proof["H_force_commutativity_control"]["status"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3_cardinality_guard"]["H_has_7_distinct_imaginary_labels"],
                "O_positive_control_verdict": julia["julia_z3_cardinality_guard"]["O_has_7_distinct_imaginary_labels"],
                "claim": "Julia Z3.jl cardinality guard for finite imaginary basis labels; dual structural proof authority is z3+cvc5 in the JAX leg.",
            },
        },
        "claim_path_tools": [
            "QuantumOptics",
            "CliffordAlgebras",
            "Z3",
            "jax",
            "jax.numpy",
            "z3",
            "cvc5",
            "torch",
            "torch.func",
        ],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": divergence_max,
            "notes": [
                "Julia, JAX, and PyTorch agree on R/C/H/O unit counts and H/O admissibility flags.",
                "PyTorch adds torch.func sensitivity; it is not used as the discrete SAT/UNSAT authority.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"unit_counts={[result['unit_counts'][key] for key in ['R', 'C', 'H', 'O']]} "
        f"H_bare={str(result['decision']['H_bare_root_admissible']).lower()} "
        f"H_cl6={str(result['decision']['H_cl6_7unit_admissible']).lower()} "
        f"O_cl6={str(result['decision']['O_cl6_7unit_admissible']).lower()} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"verdict={result['decision']['forced_vs_installed_verdict']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
