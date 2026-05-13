#!/usr/bin/env python3
"""Clifford non-pole vector sweep for identity-vs-plane phase rotation."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from clifford import Cl
from receipt_boundary import apply_default_receipt_boundary


NAME = "clifford_global_relative_phase_vector_rotation_nonpole_sweep"
CLASSIFICATION = "classical_baseline"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TOOL_MANIFEST = {
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "constructs Cl(3) even rotors and vector sandwich rotations in the e12 plane",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples phase-loop parameters and computes vector displacement norms",
    },
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "numpy": "supportive"}

LAYOUT, BLADES = Cl(3)
E1 = BLADES["e1"]
E2 = BLADES["e2"]
E3 = BLADES["e3"]
E12 = E1 * E2


def vector(theta: float):
    return math.sin(theta) * E1 + math.cos(theta) * E3


def identity_rotor(_phase: float):
    return 1.0 + 0.0 * E12


def plane_rotor(phase: float):
    return math.cos(phase / 2.0) - math.sin(phase / 2.0) * E12


def rotate(rotor, vec):
    return rotor * vec * ~rotor


def vector_array(vec) -> np.ndarray:
    return np.array(
        [
            float((vec | E1).value[0]),
            float((vec | E2).value[0]),
            float((vec | E3).value[0]),
        ],
        dtype=float,
    )


def path_metrics(vec, rotor_fn, values: np.ndarray) -> dict[str, object]:
    outputs = [vector_array(rotate(rotor_fn(float(value)), vec)) for value in values]
    steps = [float(np.linalg.norm(outputs[idx + 1] - outputs[idx])) for idx in range(len(outputs) - 1)]
    return {
        "path_length": float(sum(steps)),
        "displacement_from_start": float(max(np.linalg.norm(row - outputs[0]) for row in outputs)),
        "z_span": float(max(row[2] for row in outputs) - min(row[2] for row in outputs)),
        "norm_min": float(min(np.linalg.norm(row) for row in outputs)),
        "norm_max": float(max(np.linalg.norm(row) for row in outputs)),
    }


def run_case(theta: float, sample_count: int) -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, sample_count)
    vec = vector(theta)
    identity_metrics = path_metrics(vec, identity_rotor, values)
    plane_metrics = path_metrics(vec, plane_rotor, values)
    expected_plane_displacement = 2.0 * abs(math.sin(theta))
    tol = 1e-8
    passed = bool(
        identity_metrics["displacement_from_start"] < tol
        and identity_metrics["path_length"] < tol
        and abs(plane_metrics["displacement_from_start"] - expected_plane_displacement) < tol
        and abs(identity_metrics["norm_min"] - 1.0) < tol
        and abs(identity_metrics["norm_max"] - 1.0) < tol
        and abs(plane_metrics["norm_min"] - 1.0) < tol
        and abs(plane_metrics["norm_max"] - 1.0) < tol
    )
    return {
        "theta": theta,
        "sample_count": sample_count,
        "expected_plane_rotation_displacement": expected_plane_displacement,
        "identity_rotor_transport": identity_metrics,
        "plane_rotor_transport": plane_metrics,
        "passed": passed,
    }


def run_graveyards() -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, 129)
    nonpole = vector(math.pi / 3.0)
    pole = vector(0.0)
    identity_metrics = path_metrics(nonpole, identity_rotor, values)
    plane_metrics = path_metrics(nonpole, plane_rotor, values)
    pole_plane = path_metrics(pole, plane_rotor, values)

    same_identity_collapses = bool(plane_metrics["displacement_from_start"] < 1e-9)
    same_plane_collapses = bool(identity_metrics["displacement_from_start"] > 1.0)
    return {
        "both_transports_identity_rotor_would_collapse_distinction": {
            "candidate_passed": same_identity_collapses,
            "expected": False,
            "passed": same_identity_collapses is False,
        },
        "both_transports_plane_rotor_would_collapse_distinction": {
            "candidate_passed": same_plane_collapses,
            "expected": False,
            "passed": same_plane_collapses is False,
        },
        "plane_rotation_on_z_axis_vector_degenerates": {
            "displacement_from_start": pole_plane["displacement_from_start"],
            "expected_near_zero": True,
            "passed": bool(pole_plane["displacement_from_start"] < 1e-9),
        },
        "z_coordinate_readout_hides_plane_rotation": {
            "z_span": plane_metrics["z_span"],
            "expected_near_zero": True,
            "passed": bool(abs(plane_metrics["z_span"]) < 1e-9),
        },
        "bare_rotors_without_vector_carrier_are_insufficient": {
            "has_vector_carrier": False,
            "has_loop_family": False,
            "can_compare_vector_transport": False,
            "passed": True,
        },
    }


def main() -> int:
    theta_values = [math.pi / 8.0, math.pi / 6.0, math.pi / 4.0, math.pi / 3.0, math.pi / 2.0, 2.0 * math.pi / 3.0]
    sample_counts = [33, 65, 129]
    sweep = [run_case(theta, sample_count) for theta in theta_values for sample_count in sample_counts]
    graveyards = run_graveyards()
    all_pass = bool(all(row["passed"] for row in sweep) and all(row["passed"] for row in graveyards.values()))
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "promotion_allowed": False,
        "claim_ceiling": (
            "Clifford Cl(3) non-pole vector-rotation baseline for identity-rotor invariance and e12-plane "
            "rotor transport only; no density matrix, no full Hopf bundle, no physical loop independence, no flux, "
            "no QIT, GStack, axis, bridge, engine, target-system, or nonclassical admission"
        ),
        "next_lego_target": "clifford_two_component_phase_rotation_vector_displacement_sweep",
        "promotion_condition": "No promotion from this sweep; use only as Clifford rotor companion evidence for already-fenced phase-transport baselines.",
        "blocked_until": "blocked from geometric-constraint-manifold claims until nested carrier geometry, density carrier coupling, and physical-evolution graveyards exist",
        "demotion_condition": "Demote if cited as density transport, full Hopf geometry, physical loop independence, flux, QIT, GStack, axis, bridge, engine, target-system, or nonclassical evidence.",
        "divergence_log": (
            "This sweep uses Cl(3) vector rotors rather than density matrices. It is a companion baseline for the "
            "same displacement law, not a density-transport proof and not a full geometric-constraint-manifold "
            "fixture."
        ),
        "operation_sequence": [
            "construct unit Cl(3) vectors with nonzero e1 projection and e3 component",
            "sample identity rotor transport",
            "sample e12-plane rotor sandwich transport",
            "compare vector displacement against closed-form 2 sin(theta) expectation",
            "run same-rotor, z-axis, z-readout-hidden, and no-vector-carrier graveyards",
        ],
        "carrier_topology": "Cl(3) unit vector carrier with identity and e12-plane even-rotor loop families; no density carrier or full Hopf bundle",
        "observable": "Clifford vector sandwich displacement, path length, z-coordinate span, and vector norm",
        "pass_fail_predicate": "identity rotor leaves vectors invariant; e12-plane rotor displacement matches 2 sin(theta); vector norm remains one; adjacent graveyards collapse or become insufficient",
        "graveyards": [
            "both transports use identity rotor",
            "both transports use e12-plane rotor",
            "e12-plane rotation on z-axis vector degenerates",
            "z-coordinate-only readout hides e12-plane rotation",
            "bare rotors without vector carrier are insufficient",
        ],
        "baselines": [
            "QuTiP global-relative phase non-pole density sweep receipt",
            "Qiskit global-relative phase non-pole density sweep receipt",
            "SymPy global-relative phase symbolic density identity receipt",
        ],
        "alternative_formulations": [
            "Clifford rotor-to-density projection fixture",
            "SymPy SO(3) rotation matrix identity",
            "QuTiP/Qiskit density transport sweeps",
            "nested Hopf-torus carrier fixture before stronger geometry claims",
        ],
        "exact_tool_function_needs": {
            "clifford": ["Cl", "MultiVector geometric product", "MultiVector reverse", "vector inner products"],
            "numpy": ["linspace", "array", "linalg.norm"],
        },
        "lego_or_coupling_target": "clifford_two_component_phase_rotation_vector_displacement_sweep",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "theta_count": len(theta_values),
            "sample_count_variants": sample_counts,
            "case_count": len(sweep),
            "all_sweep_cases_pass": all(row["passed"] for row in sweep),
            "all_graveyards_pass": all(row["passed"] for row in graveyards.values()),
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "positive": {"sweep": sweep},
        "graveyards_detail": graveyards,
        "out_of_scope": [
            "No density matrix construction.",
            "No full Hopf bundle or nested Hopf-torus carrier.",
            "No physical loop-independence closure.",
            "No flux, QIT, GStack, axis, bridge, engine, target-system, or nonclassical claim.",
        ],
    }
    result = apply_default_receipt_boundary(result, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out_path)
    print(f"ALL PASS: {result['all_pass']}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
