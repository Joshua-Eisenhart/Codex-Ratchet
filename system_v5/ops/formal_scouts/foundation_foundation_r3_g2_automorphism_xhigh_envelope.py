#!/usr/bin/env python3
"""Composite envelope for foundation_r3_g2_automorphism_xhigh.

The envelope reads completed Julia, JAX, and PyTorch leg receipts after the
legs have run. It does not recompute the engine legs or promote the rung.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r3_g2_automorphism_xhigh"
OBJECT_ID = "foundation_r3_g2_automorphism_xhigh_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r3_g2_automorphism_xhigh_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r3_g2_automorphism_xhigh_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_pytorch_results.json"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive envelope assembly from completed engine receipts; not part of the algebra claim path",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic path binding for source and result receipts",
    },
}

TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], *, result_path: Path, values: dict[str, Any]) -> dict[str, Any]:
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
        "values": values,
    }


def dim_values(payload: dict[str, Any]) -> dict[str, int]:
    summary = payload["summary"]
    return {
        "R": int(summary["dim_der_R"]),
        "C": int(summary["dim_der_C"]),
        "H": int(summary["dim_der_H"]),
        "O": int(summary["dim_der_O"]),
    }


def max_dim_divergence(values: dict[str, dict[str, int]]) -> float:
    diffs = []
    for key in ["R", "C", "H", "O"]:
        rows = [row[key] for row in values.values()]
        diffs.append(float(max(rows) - min(rows)))
    return max(diffs)


def all_fences_ok(*payloads: dict[str, Any]) -> bool:
    return all(
        payload["classification"] == "scratch_diagnostic"
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["reads_peer_result"] is False
        for payload in payloads
    )


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = {
        **dim_values(julia),
        "O_rank": int(julia["summary"]["O_rank"]),
        "O_forced_commutative_derivation_dim": int(julia["summary"]["O_forced_commutative_derivation_dim"]),
        "O_h_embedded_derivation_dim": int(julia["summary"]["O_h_embedded_derivation_dim"]),
    }
    jax_values = {
        **dim_values(jax),
        "O_rank": int(jax["summary"]["O_rank"]),
        "O_forced_commutative_derivation_dim": int(jax["summary"]["O_forced_commutative_derivation_dim"]),
        "O_h_embedded_derivation_dim": int(jax["summary"]["O_h_embedded_derivation_dim"]),
    }
    pytorch_values = {
        **dim_values(pytorch),
        "O_rank": int(pytorch["summary"]["O_rank"]),
        "O_forced_commutative_derivation_dim": int(pytorch["summary"]["O_forced_commutative_derivation_dim"]),
        "O_h_embedded_derivation_dim": int(pytorch["summary"]["O_h_embedded_derivation_dim"]),
        "jacrev_alpha_0_5": float(pytorch["summary"]["jacrev_alpha_0_5"]),
        "energy_alpha_1": float(pytorch["summary"]["energy_alpha_1"]),
    }
    engine_values = {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values}
    expected = {"R": 0, "C": 0, "H": 3, "O": 14}
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]

    negative = {
        "ladder_changes_R_C_H_O": dim_values(julia) == dim_values(jax) == dim_values(pytorch) == expected,
        "drop_derivation_constraint_O_dim_64_vs_14": bool(
            julia["negative_control_flip"]["drop_derivation_constraint_O_dim_64_vs_14"]
            and jax["negative_control_flip"]["drop_derivation_constraint_O_dim_64_vs_14"]
            and pytorch["negative_control_flip"]["drop_derivation_constraint_O_dim_64_vs_14"]
        ),
        "forced_commutative_O_dim_changes": bool(
            julia["negative_control_flip"]["forced_commutative_O_dim_changes"]
            and jax["negative_control_flip"]["forced_commutative_O_dim_changes"]
            and pytorch["negative_control_flip"]["forced_commutative_O_dim_changes"]
        ),
        "forced_commutative_O_derivation_dim": julia_values["O_forced_commutative_derivation_dim"],
        "h_embedded_associative_control_dim_changes": bool(
            julia["negative_control_flip"]["h_embedded_associative_control_dim_changes"]
            and jax["negative_control_flip"]["h_embedded_associative_control_dim_changes"]
            and pytorch["negative_control_flip"]["h_embedded_associative_control_dim_changes"]
        ),
        "h_embedded_associative_control_derivation_dim": julia_values["O_h_embedded_derivation_dim"],
        "z3_O_erase_flip_unsat_to_sat": bool(jax["negative_control_flip"]["z3_O_erase_flip"]),
        "cvc5_O_erase_flip_unsat_to_sat": bool(jax["negative_control_flip"]["cvc5_O_erase_flip"]),
        "torch_func_jacrev_independent_sensitivity": bool(pytorch["negative_control_flip"]["torch_func_jacrev_independent_sensitivity"]),
    }
    div = max_dim_divergence({name: dim_values(payload) for name, payload in {"julia": julia, "jax": jax, "pytorch": pytorch}.items()})
    fences_ok = all_fences_ok(julia, jax, pytorch)
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and div == 0.0
        and fences_ok
        and all(value for value in negative.values() if isinstance(value, bool))
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch foundation R3 G2 automorphism rung only: Der(R/C/H/O) "
            "dimension ladder from computed multiplication-preservation constraints. "
            "No promotion, no formal admission, no SU(3)/SM/color claim."
        ),
        "all_pass": all_pass,
        "M": {
            "name": "derivation_automorphism_probe",
            "explicit_probe_family": ["for every ordered basis pair (e_a,e_b) and output coordinate c: D(e_a e_b)_c - (D(e_a)e_b + e_aD(e_b))_c"],
            "finite_probe_counts": jax["M"]["finite_probe_counts"],
            "measurement_map": "M_A(D)=A_A vec(D), where A_A is the computed derivation constraint matrix from structure constants",
        },
        "C": {
            "trace_eq_1": bool(julia["C"]["trace_eq_1"] and jax["C"]["trace_eq_1"] and pytorch["C"]["trace_eq_1"]),
            "psd": bool(julia["C"]["psd"] and jax["C"]["psd"] and pytorch["C"]["psd"]),
            "hermitian": bool(julia["C"]["hermitian"] and jax["C"]["hermitian"] and pytorch["C"]["hermitian"]),
            "normalization": "basis probes are unit-normalized; auxiliary rho=I/dim guard is trace-one/PSD/Hermitian but does not determine the rung result",
            "rung_specific_constraint": "octonion/quaternion/etc multiplication preservation: D(xy)=D(x)y+xD(y) for every basis pair",
        },
        "S_mod_M": {
            "definition": "S=End_R(A), D ~_M D' iff M_A(D-D')=0; the symmetry class is ker(M_A)=Der(A)",
            "class_dimensions": dim_values(julia),
            "quotient_ranks": jax["S_mod_M"]["quotient_ranks"],
            "interpretation": "computed symmetry dimensions are Der(R)=0, Der(C)=0, Der(H)=3, Der(O)=14; the O kernel is the g2 derivation algebra dimension only.",
        },
        "derivation_dimension_ladder": dim_values(julia),
        "negative_control_flip": negative,
        "engines": {
            "julia": engine_record(julia, result_path=JULIA_RESULT, values=julia_values),
            "jax": engine_record(jax, result_path=JAX_RESULT, values=jax_values),
            "pytorch": engine_record(pytorch, result_path=PYTORCH_RESULT, values=pytorch_values),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["z3"]["negative_control_verdict"],
                "H_dimension_not_expected_verdict": jax["crossover_proofs"]["z3"]["H_dimension_not_expected_verdict"],
                "claim": jax["crossover_proofs"]["z3"]["claim"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["cvc5"]["negative_control_verdict"],
                "H_dimension_not_expected_verdict": jax["crossover_proofs"]["cvc5"]["H_dimension_not_expected_verdict"],
                "claim": jax["crossover_proofs"]["cvc5"]["claim"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["O"]["dimension_not_expected_status"],
                "negative_control_verdict": julia["julia_z3"]["O"]["drop_derivation_constraints_dimension_not_expected_status"],
                "H_dimension_not_expected_verdict": julia["julia_z3"]["H"]["dimension_not_expected_status"],
            },
        },
        "claim_path_tools": [
            "CliffordAlgebras",
            "Z3",
            "jax",
            "jax.numpy",
            "z3",
            "cvc5",
            "torch",
            "torch.func",
        ],
        "control_only_tools": ["json", "pathlib", "LinearAlgebra"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": div,
            "notes": [
                "Julia is authoritative for the ladder because CliffordAlgebras verifies H and the Cayley-Dickson table feeds exact rank/Z3 checks.",
                "JAX supplies z3+cvc5 structural proof over computed derivation constraints.",
                "PyTorch supplies torch.func.jacrev sensitivity under structure change, not exact algebra authority.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    dims = result["derivation_dimension_ladder"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R3_G2_AUTOMORPHISM_XHIGH_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"dims={dims['R']}/{dims['C']}/{dims['H']}/{dims['O']} "
        f"forced_comm_dim={result['negative_control_flip']['forced_commutative_O_derivation_dim']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
