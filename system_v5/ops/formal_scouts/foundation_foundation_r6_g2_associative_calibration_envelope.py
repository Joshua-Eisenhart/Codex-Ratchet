#!/usr/bin/env python3
"""Composite envelope for foundation_r6_g2_associative_calibration."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_g2_associative_calibration"
OBJECT_ID = "foundation_r6_g2_associative_calibration_envelope"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r6_g2_associative_calibration_envelope.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r6_g2_associative_calibration_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_pytorch_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from completed engine receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path, values: dict[str, Any]) -> dict[str, Any]:
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


def values(payload: dict[str, Any]) -> dict[str, Any]:
    s = payload["summary"]
    return {
        "calibrated_plane_count": int(s["calibrated_plane_count"]),
        "fano_line_count": int(s["fano_line_count"]),
        "first_fano_phi": float(s["first_fano_phi"]),
        "generic_control_phi": float(s["generic_control_phi"]),
        "erased_first_fano_calibrated_count": int(s["erased_first_fano_calibrated_count"]),
        "forced_commutative_zero_phi_calibrated_count": int(s["forced_commutative_zero_phi_calibrated_count"]),
    }


def max_divergence(engine_values: dict[str, dict[str, Any]]) -> float:
    keys = [
        "calibrated_plane_count",
        "fano_line_count",
        "first_fano_phi",
        "generic_control_phi",
        "erased_first_fano_calibrated_count",
        "forced_commutative_zero_phi_calibrated_count",
    ]
    diffs = []
    for key in keys:
        vals = [float(row[key]) for row in engine_values.values()]
        diffs.append(max(vals) - min(vals))
    return max(diffs)


def fences_ok(*payloads: dict[str, Any]) -> bool:
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
    julia_values = values(julia)
    jax_values = values(jax)
    pytorch_values = values(pytorch)
    engine_values = {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values}
    div = max_divergence(engine_values)
    z3_verdict = jax["crossover_proofs"]["z3"]["verdict"]
    cvc5_verdict = jax["crossover_proofs"]["cvc5"]["verdict"]
    fano_lines = julia["S_mod_M"]["calibrated_planes"]
    negative = {
        "drop_one_fano_probe_count_7_to_6": bool(
            julia["negative_control_flip"]["drop_one_fano_probe_count_7_to_6"]
            and jax["negative_control_flip"]["drop_one_fano_probe_count_7_to_6"]
            and pytorch["negative_control_flip"]["drop_one_fano_probe_count_7_to_6"]
        ),
        "force_commutative_zero_phi_count_7_to_0": bool(
            julia["negative_control_flip"]["force_commutative_zero_phi_count_7_to_0"]
            and jax["negative_control_flip"]["force_commutative_zero_phi_count_7_to_0"]
            and pytorch["negative_control_flip"]["force_commutative_zero_phi_count_7_to_0"]
        ),
        "generic_coordinate_plane_phi_less_than_one": bool(
            julia["negative_control_flip"]["generic_coordinate_plane_phi_less_than_one"]
            and jax["negative_control_flip"]["generic_coordinate_plane_phi_less_than_one"]
            and pytorch["negative_control_flip"]["generic_coordinate_plane_phi_less_than_one"]
        ),
        "z3_erase_flip_unsat_to_sat": bool(jax["negative_control_flip"]["z3_erase_flip_unsat_to_sat"]),
        "cvc5_erase_flip_unsat_to_sat": bool(jax["negative_control_flip"]["cvc5_erase_flip_unsat_to_sat"]),
        "torch_func_jacrev_independent_sensitivity": bool(pytorch["negative_control_flip"]["torch_func_jacrev_independent_sensitivity"]),
    }
    all_pass = bool(
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_verdict == cvc5_verdict == "unsat"
        and div == 0.0
        and fences_ok(julia, jax, pytorch)
        and all(negative.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "controller_reads_engine_results_after_lanes": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": (
            "Scratch foundation R6 G2 associative calibration rung only: finite octonion-derived "
            "associative 3-form phi calibrates the seven coordinate Fano-line associative 3-planes. "
            "No G2-manifold, M-theory, bridge, physics, or promotion claim."
        ),
        "all_pass": all_pass,
        "M": {
            "name": "G2 associative calibration probe family",
            "explicit_probe_family": julia["M"]["explicit_probe_family"],
            "finite_probe_counts": julia["M"]["finite_probe_counts"],
            "measurement_map": "M(P) records phi(P), unit volume, and octonion cross-product closure for each coordinate 3-plane P.",
        },
        "C": {
            "trace_eq_1": bool(julia["C"]["trace_eq_1"] and jax["C"]["trace_eq_1"] and pytorch["C"]["trace_eq_1"]),
            "psd": bool(julia["C"]["psd"] and jax["C"]["psd"] and pytorch["C"]["psd"]),
            "hermitian": bool(julia["C"]["hermitian"] and jax["C"]["hermitian"] and pytorch["C"]["hermitian"]),
            "normalization": "orthonormal imaginary octonion basis; each coordinate 3-plane has unit volume; auxiliary rho guards satisfy trace-one/PSD/Hermitian constraints",
            "rung_specific_constraint": "phi is computed from the Cayley-Dickson octonion table, and calibrated planes must have oriented phi=1 plus cross-product closure",
        },
        "S_mod_M": {
            "definition": "S is the finite set of 35 coordinate 3-planes in Im(O); P ~_M Q iff their calibration/closure probe vector agrees.",
            "calibrated_class": "the seven oriented Fano-line planes with phi=1, equivalently coordinate Im(H) subalgebras closed under octonion cross product",
            "calibrated_class_count": julia_values["calibrated_plane_count"],
            "uncalibrated_class_count": 28,
            "calibrated_planes": fano_lines,
        },
        "calibration": {
            "fano_lines": fano_lines,
            "first_fano_oriented_plane": julia["calibration"]["first_fano_oriented_plane"],
            "first_fano_phi": julia_values["first_fano_phi"],
            "generic_control_plane": julia["calibration"]["generic_control_plane"],
            "generic_control_phi": julia_values["generic_control_phi"],
            "erased_first_fano_calibrated_count": julia_values["erased_first_fano_calibrated_count"],
            "forced_commutative_zero_phi_calibrated_count": julia_values["forced_commutative_zero_phi_calibrated_count"],
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
                "negative_control_verdict": jax["crossover_proofs"]["z3"]["negative_control_verdict"],
                "generic_control_verdict": jax["crossover_proofs"]["z3"]["generic_control_verdict"],
                "claim": jax["crossover_proofs"]["z3"]["claim"],
                "derived_expression": jax["crossover_proofs"]["z3"]["derived_expression"],
                "asserted_precomputed_scalar_literal": False,
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_verdict,
                "negative_control_verdict": jax["crossover_proofs"]["cvc5"]["negative_control_verdict"],
                "generic_control_verdict": jax["crossover_proofs"]["cvc5"]["generic_control_verdict"],
                "claim": jax["crossover_proofs"]["cvc5"]["claim"],
                "derived_expression": jax["crossover_proofs"]["cvc5"]["derived_expression"],
                "asserted_precomputed_scalar_literal": False,
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["julia_z3"]["fano_phi_not_one_status"],
                "negative_control_verdict": julia["julia_z3"]["erased_fano_phi_not_one_status"],
                "generic_control_verdict": julia["julia_z3"]["generic_phi_less_than_one_status"],
                "claim": julia["julia_z3"]["claim"],
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
        "control_only_tools": ["json", "pathlib"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": div,
            "notes": [
                "Julia is authoritative for the octonion-derived phi and calibrated Fano-line list.",
                "JAX supplies dual-SMT in-solver calibration and erase-flip checks.",
                "PyTorch supplies an independent torch.func.jacrev sensitivity check, not a bare mirror.",
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
        "FOUNDATION_R6_G2_ASSOCIATIVE_CALIBRATION_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"calibrated={result['S_mod_M']['calibrated_class_count']} "
        f"max_divergence={result['divergence']['max_divergence']} "
        f"z3={result['crossover_proofs']['z3']['verdict']} "
        f"cvc5={result['crossover_proofs']['cvc5']['verdict']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
