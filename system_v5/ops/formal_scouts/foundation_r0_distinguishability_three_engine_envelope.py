#!/usr/bin/env python3
"""Composite envelope for the strict three-engine foundation_r0_distinguishability rung."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_distinguishability_three_engine_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_r0_distinguishability_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_distinguishability_jax_smt_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_distinguishability_pytorch_grad_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from the already-run engine receipts; not part of the mathematical claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for source and result receipts",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(
    payload: dict[str, Any],
    *,
    result_path: Path,
    values: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "source_sha256": payload.get("source_sha256"),
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": values,
    }


def max_numeric_divergence(left: dict[str, Any], right: dict[str, Any], keys: list[str]) -> float:
    return max(abs(float(left[key]) - float(right[key])) for key in keys)


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = {
        "n_classes_Z": julia["summary"]["n_classes_Z"],
        "n_classes_ZX": julia["summary"]["n_classes_ZX"],
        "Z_equal": julia["summary"]["Z_equal"],
        "X_different": julia["summary"]["X_different"],
    }
    jax_values = {
        "n_classes_Z": jax["summary"]["n_classes_Z"],
        "n_classes_ZX": jax["summary"]["n_classes_ZX"],
        "Z_equal": jax["summary"]["Z_equal"],
        "X_different": jax["summary"]["X_different"],
        "z3_M1_Z": jax["summary"]["z3_M1_Z"],
        "z3_M2_ZX": jax["summary"]["z3_M2_ZX"],
        "cvc5_M1_Z": jax["summary"]["cvc5_M1_Z"],
        "cvc5_M2_ZX": jax["summary"]["cvc5_M2_ZX"],
        "z3_separator_M1_Z": jax["summary"]["z3_separator_M1_Z"],
        "z3_separator_M2_ZX": jax["summary"]["z3_separator_M2_ZX"],
        "cvc5_separator_M1_Z": jax["summary"]["cvc5_separator_M1_Z"],
        "cvc5_separator_M2_ZX": jax["summary"]["cvc5_separator_M2_ZX"],
    }
    pytorch_values = {
        "D_Z": pytorch["summary"]["D_Z"],
        "D_ZX": pytorch["summary"]["D_ZX"],
        "jacrev_grad_D_Z": pytorch["summary"]["jacrev_grad_D_Z"],
        "jacrev_grad_D_ZX": pytorch["summary"]["jacrev_grad_D_ZX"],
    }

    z3_unsat = jax["smt"]["z3"]["relation_M2_ZX"]["verdict"]
    cvc5_unsat = jax["smt"]["cvc5"]["relation_M2_ZX"]["verdict"]
    z3_drop = jax["smt"]["z3"]["relation_M1_Z"]["verdict"]
    cvc5_drop = jax["smt"]["cvc5"]["relation_M1_Z"]["verdict"]
    z3_sep_sat = jax["smt"]["z3"]["separator_M2_ZX"]["verdict"]
    cvc5_sep_sat = jax["smt"]["cvc5"]["separator_M2_ZX"]["verdict"]
    z3_sep_drop = jax["smt"]["z3"]["separator_M1_Z"]["verdict"]
    cvc5_sep_drop = jax["smt"]["cvc5"]["separator_M1_Z"]["verdict"]
    max_divergence = max_numeric_divergence(julia_values, jax_values, ["n_classes_Z", "n_classes_ZX"])
    all_pass = (
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_unsat == cvc5_unsat == "unsat"
        and z3_drop == cvc5_drop == "sat"
        and z3_sep_sat == cvc5_sep_sat == "sat"
        and z3_sep_drop == cvc5_sep_drop == "unsat"
        and max_divergence == 0.0
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": "foundation_r0_distinguishability_three_engine_envelope",
        "rung_id": "foundation_r0_distinguishability",
        "classification": CLASSIFICATION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch foundation rung only: probe-relative identity on a finite one-qubit "
            "state set under M1={Z} versus M2={Z,X}. No promotion, no formal admission, "
            "no other foundation rung, no geometry/carrier/physics claim."
        ),
        "all_pass": all_pass,
        "M": {
            "M1": ["Z"],
            "M2": ["Z", "X"],
            "explicit_probe_family": "Pauli projective measurement effects with Born-probability signatures",
        },
        "C": {
            "trace_one": True,
            "psd": True,
            "hermitian": True,
            "povm_normalization": True,
            "rung_specific_constraint": (
                "distinct witness states share solver-derived Z traces, differ on solver-derived X traces, "
                "and the relation/separator queries bind only matrix entries"
            ),
        },
        "S_mod_M": {
            "definition": "finite quotient of one-qubit candidate states by equality of all Born vectors in the selected probe family",
            "M1_Z_class_count": julia_values["n_classes_Z"],
            "M2_ZX_class_count": julia_values["n_classes_ZX"],
            "M1_Z_classes": julia["S_mod_M"]["M1_Z"]["classes"],
            "M2_ZX_classes": julia["S_mod_M"]["M2_ZX"]["classes"],
        },
        "witness_pair": julia["witness_pair"],
        "negative_control_flip": {
            "drop_X_control": (
                "M2={Z,X} makes the separator query SAT and the relation query UNSAT; "
                "erasing X gives M1={Z}, separator UNSAT and relation SAT"
            ),
            "n_classes_Z": julia_values["n_classes_Z"],
            "n_classes_ZX": julia_values["n_classes_ZX"],
            "class_count_refines": julia_values["n_classes_Z"] < julia_values["n_classes_ZX"],
            "z3_relation_M1_Z": z3_drop,
            "z3_relation_M2_ZX": z3_unsat,
            "cvc5_relation_M1_Z": cvc5_drop,
            "cvc5_relation_M2_ZX": cvc5_unsat,
            "z3_separator_M1_Z": z3_sep_drop,
            "z3_separator_M2_ZX": z3_sep_sat,
            "cvc5_separator_M1_Z": cvc5_sep_drop,
            "cvc5_separator_M2_ZX": cvc5_sep_sat,
            "solver_derived_X_probabilities": jax["negative_control_flip"]["solver_derived_X_probabilities"],
            "solver_derived_bound_entry_probabilities": jax["negative_control_flip"]["solver_derived_bound_entry_probabilities"],
            "derivation_source": jax["smt"]["z3"]["relation_M2_ZX"]["metadata"]["born_derivation"],
            "pytorch_grad_D_Z": pytorch_values["jacrev_grad_D_Z"],
            "pytorch_grad_D_ZX": pytorch_values["jacrev_grad_D_ZX"],
        },
        "engines": {
            "julia": engine_record(julia, result_path=JULIA_RESULT, values=julia_values),
            "jax": engine_record(jax, result_path=JAX_RESULT, values=jax_values),
            "pytorch": engine_record(pytorch, result_path=PYTORCH_RESULT, values=pytorch_values),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_sep_sat,
                "version": jax["smt"]["z3"]["version"],
                "claim": "Solver-derived Tr(M_k rho) terms over bound matrix entries produce an active M2={Z,X} separator",
                "negative_control_verdict": z3_sep_drop,
                "dual_relation_verdict": z3_unsat,
                "dual_relation_negative_control_verdict": z3_drop,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_sep_sat,
                "version": jax["smt"]["cvc5"]["version"],
                "claim": "Solver-derived Tr(M_k rho) terms over bound matrix entries produce an active M2={Z,X} separator",
                "negative_control_verdict": cvc5_sep_drop,
                "dual_relation_verdict": cvc5_unsat,
                "dual_relation_negative_control_verdict": cvc5_drop,
            },
        },
        "claim_path_tools": ["QuantumOptics", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": julia_values,
                "jax": jax_values,
                "pytorch": pytorch_values,
            },
            "max_divergence": max_divergence,
            "notes": [
                "Julia is authoritative for the finite quotient counts and witness Born statistics.",
                "JAX contributes dual-SMT relation and separator flips derived from bound matrix entries.",
                "PyTorch contributes a distinct torch.func.jacrev sensitivity check for the coherence parameter.",
            ],
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
        "THREE_ENGINE_FOUNDATION_R0_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"n_classes_Z={result['negative_control_flip']['n_classes_Z']} "
        f"n_classes_ZX={result['negative_control_flip']['n_classes_ZX']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"drop_X_z3={result['negative_control_flip']['z3_relation_M1_Z']} "
        f"drop_X_cvc5={result['negative_control_flip']['cvc5_relation_M1_Z']} "
        f"separator_drop_X_z3={result['negative_control_flip']['z3_separator_M1_Z']} "
        f"separator_drop_X_cvc5={result['negative_control_flip']['cvc5_separator_M1_Z']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
