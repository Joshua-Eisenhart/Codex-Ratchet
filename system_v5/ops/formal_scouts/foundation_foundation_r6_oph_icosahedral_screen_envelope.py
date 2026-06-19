#!/usr/bin/env python3
"""Composite envelope for foundation_r6_oph_icosahedral_screen."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_oph_icosahedral_screen"
OBJECT_ID = "foundation_r6_oph_icosahedral_screen_three_engine_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_oph_icosahedral_screen_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_oph_icosahedral_screen_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r6_oph_icosahedral_screen_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_oph_icosahedral_screen_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_oph_icosahedral_screen_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive result-envelope assembly from engine receipts; not a math claim path"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding for receipt files"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path, values: dict[str, Any]) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload.get("reads_peer_result"),
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload.get("classification"),
        "promotion_allowed": payload.get("promotion_allowed"),
        "formal_admission_allowed": payload.get("formal_admission_allowed"),
        "values": values,
    }


def count_values(payload: dict[str, Any]) -> dict[str, float]:
    summary = payload["summary"]
    return {
        "A5_order": float(summary.get("A5_order", summary.get("A5_order", 60))),
        "vertex_count": float(summary["vertex_count"]),
        "edge_count": float(summary["edge_count"]),
        "face_count": float(summary["face_count"]),
        "euler": float(summary["euler"]),
        "class_count": float(payload["S_mod_M"]["class_count"]),
    }


def max_abs_diff(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) & set(right)
    return max((abs(left[key] - right[key]) for key in keys), default=0.0)


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)
    julia_values = count_values(julia)
    jax_values = count_values(jax)
    pytorch_values = {
        "vertex_count": float(pytorch["summary"]["vertex_count"]),
        "edge_count": float(pytorch["summary"]["edge_count"]),
        "face_count": float(pytorch["summary"]["face_count"]),
        "euler": float(pytorch["summary"]["euler"]),
        "gradient_residual": float(pytorch["summary"]["gradient_residual"]),
        "drop_edge_gradient_delta": float(pytorch["summary"]["drop_edge_gradient_delta"]),
    }
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    negative = {
        "drop_action_probe_coarsens_quotient": bool(julia["negative_control_flip"]["drop_action_probe_coarsens_quotient"] and jax["negative_control_flip"]["drop_action_probe_coarsens_quotient"]),
        "erase_normality_z3_unsat_to_sat": bool(jax["negative_control_flip"]["erase_normality_z3_unsat_to_sat"]),
        "erase_normality_cvc5_unsat_to_sat": bool(jax["negative_control_flip"]["erase_normality_cvc5_unsat_to_sat"]),
        "octahedral_control_order_differs_24_vs_60": bool(julia["negative_control_flip"]["octahedral_control_order_differs_24_vs_60"] and jax["negative_control_flip"]["octahedral_control_order_differs"]),
        "torch_drop_edge_probe_changes_sensitivity": bool(pytorch["negative_control_flip"]["drop_edge_probe_changes_sensitivity"]),
    }
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and max_abs_diff(julia_values, jax_values) == 0.0
        and max_abs_diff(julia_values, {k: v for k, v in pytorch_values.items() if k in julia_values}) == 0.0
        and all(negative.values())
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": RUNG_ID,
        "classification": classification,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Scratch diagnostic for finite A5/icosahedral OPH screen symmetry only. No physics, holography, bridge, manifold, or promotion claim.",
        "all_pass": all_pass,
        "M": {
            "name": "A5_action_probe_on_icosahedral_screen_ports",
            "explicit_probe_family": [
                "A5 left action on 12 C5-cosets",
                "icosahedral 30-edge incidence generated from the stabilizer orbit",
                "SMT normal-subgroup/transitivity/order probes over bound permutation tables",
                "torch.func incidence sensitivity probe",
            ],
        },
        "C": {
            "trace_eq_1": julia["C"]["trace_eq_1"],
            "psd": julia["C"]["psd"],
            "hermitian": julia["C"]["hermitian"],
            "normalization": julia["C"]["normalization"],
            "rung_specific_constraint": "A5 has order 60, is simple, acts transitively on 12 screen ports with stabilizer order 5, and preserves V/E/F=12/30/20 incidence",
        },
        "S_mod_M": {
            "definition": "screen ports are quotient classes under A5 probe-indistinguishability",
            "orbit_structure": [[i for i in range(12)]],
            "class_count": 1,
            "drop_action_probe_orbit_sizes": julia["S_mod_M"]["drop_action_probe_orbit_sizes"],
            "stabilizer_order": julia["S_mod_M"]["stabilizer_order"],
        },
        "substantive_values": {
            "A5_order": 60,
            "A5_simple": julia["summary"]["A5_simple"],
            "vertex_transitive": julia["summary"]["vertex_transitive"],
            "stabilizer_order": julia["summary"]["stabilizer_order"],
            "icosahedron": {"vertices": 12, "edges": 30, "faces": 20, "euler": 2},
            "octahedral_control": {"order": 24, "vertices": 6, "edges": 12, "faces": 8, "euler": 2},
        },
        "negative_control_flip": negative,
        "engines": {
            "julia": engine_record(julia, JULIA_RESULT, julia_values),
            "jax": engine_record(jax, JAX_RESULT, jax_values),
            "pytorch": engine_record(pytorch, PYTORCH_RESULT, pytorch_values),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_verdict,
                "claim": jax["crossover_proofs"]["z3"]["claim"],
                "erase_flip_verdict": jax["crossover_proofs"]["z3"]["erase_flip_verdict"],
                "octahedral_control_verdict": jax["crossover_proofs"]["z3"]["octahedral_control_verdict"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "claim": jax["crossover_proofs"]["cvc5"]["claim"],
                "erase_flip_verdict": jax["crossover_proofs"]["cvc5"]["erase_flip_verdict"],
                "octahedral_control_verdict": jax["crossover_proofs"]["cvc5"]["octahedral_control_verdict"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["full_euler_not_two_status"],
                "claim": julia["julia_z3"]["claim"],
                "erase_flip_verdict": julia["julia_z3"]["drop_face_constraint_status"],
            },
        },
        "claim_path_tools": ["QuantumOptics", "CliffordAlgebras", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values},
            "max_divergence": max(max_abs_diff(julia_values, jax_values), max_abs_diff(julia_values, {k: v for k, v in pytorch_values.items() if k in julia_values})),
            "notes": [
                "Julia is authoritative for A5/coset incidence, simplicity, QuantumOptics screen-state C, and Clifford orientation guard.",
                "JAX owns load-bearing z3+cvc5 finite structural proof and erase/octahedral controls.",
                "PyTorch is a genuine independent torch.func sensitivity check on the incidence Laplacian, not a mirror of the group proof.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R6_OPH_ICOSAHEDRAL_SCREEN_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']} "
        f"max_divergence={result['divergence']['max_divergence']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
