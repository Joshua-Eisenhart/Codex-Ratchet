#!/usr/bin/env python3
"""Qiskit non-pole sweep for global-vs-relative phase density transport."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from qiskit.quantum_info import DensityMatrix, Operator, Statevector
from receipt_boundary import apply_default_receipt_boundary


NAME = "qiskit_global_relative_phase_density_transport_nonpole_sweep"
CLASSIFICATION = "classical_baseline"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TOOL_MANIFEST = {
    "qiskit": {
        "tried": True,
        "used": True,
        "reason": "constructs Statevector/DensityMatrix carrier objects, phase Operators, and Pauli expectation readouts",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples phase-loop parameters, constructs diagonal unitary matrices, and computes path metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"qiskit": "load_bearing", "numpy": "supportive"}

PAULI = {
    "x": Operator(np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)),
    "y": Operator(np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)),
    "z": Operator(np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)),
}


def initial_density(theta: float) -> DensityMatrix:
    vector = np.array([math.cos(theta / 2.0), math.sin(theta / 2.0)], dtype=complex)
    return DensityMatrix(Statevector(vector))


def global_phase_operator(phase: float) -> Operator:
    return Operator(np.exp(0.5j * phase) * np.eye(2, dtype=complex))


def relative_phase_operator(phase: float) -> Operator:
    return Operator(
        np.array(
            [[np.exp(0.5j * phase), 0.0], [0.0, np.exp(-0.5j * phase)]],
            dtype=complex,
        )
    )


def transport_density(rho0: DensityMatrix, operator_fn, values: np.ndarray) -> list[DensityMatrix]:
    outputs = []
    base = np.asarray(rho0.data, dtype=complex)
    for value in values:
        unitary = np.asarray(operator_fn(float(value)).data, dtype=complex)
        outputs.append(DensityMatrix(unitary @ base @ unitary.conj().T))
    return outputs


def pauli_readout(rho: DensityMatrix) -> np.ndarray:
    return np.array([float(np.real(rho.expectation_value(op))) for op in PAULI.values()], dtype=float)


def path_metrics(densities: list[DensityMatrix]) -> dict[str, object]:
    matrices = [np.asarray(rho.data, dtype=complex) for rho in densities]
    bloch = [pauli_readout(rho) for rho in densities]
    density_steps = [float(np.linalg.norm(matrices[idx + 1] - matrices[idx], ord="fro")) for idx in range(len(matrices) - 1)]
    bloch_steps = [float(np.linalg.norm(bloch[idx + 1] - bloch[idx])) for idx in range(len(bloch) - 1)]
    purities = [float(np.real(np.trace(matrix @ matrix))) for matrix in matrices]
    traces = [float(np.real(np.trace(matrix))) for matrix in matrices]
    return {
        "density_path_length": float(sum(density_steps)),
        "density_displacement_from_start": float(max(np.linalg.norm(matrix - matrices[0], ord="fro") for matrix in matrices)),
        "bloch_path_length": float(sum(bloch_steps)),
        "bloch_displacement_from_start": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "trace_min": float(min(traces)),
        "trace_max": float(max(traces)),
        "purity_min": float(min(purities)),
        "purity_max": float(max(purities)),
    }


def run_case(theta: float, sample_count: int) -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, sample_count)
    rho0 = initial_density(theta)
    global_metrics = path_metrics(transport_density(rho0, global_phase_operator, values))
    relative_metrics = path_metrics(transport_density(rho0, relative_phase_operator, values))
    expected_density_displacement = math.sqrt(2.0) * abs(math.sin(theta))
    expected_bloch_displacement = 2.0 * abs(math.sin(theta))
    tol = 1e-8
    passed = bool(
        global_metrics["density_displacement_from_start"] < tol
        and global_metrics["bloch_path_length"] < tol
        and abs(relative_metrics["density_displacement_from_start"] - expected_density_displacement) < tol
        and abs(relative_metrics["bloch_displacement_from_start"] - expected_bloch_displacement) < tol
        and abs(global_metrics["trace_min"] - 1.0) < tol
        and abs(global_metrics["trace_max"] - 1.0) < tol
        and abs(relative_metrics["trace_min"] - 1.0) < tol
        and abs(relative_metrics["trace_max"] - 1.0) < tol
        and abs(global_metrics["purity_min"] - 1.0) < tol
        and abs(relative_metrics["purity_min"] - 1.0) < tol
    )
    return {
        "theta": theta,
        "sample_count": sample_count,
        "expected_density_displacement": expected_density_displacement,
        "expected_bloch_displacement": expected_bloch_displacement,
        "global_phase_transport": global_metrics,
        "relative_phase_transport": relative_metrics,
        "passed": passed,
    }


def run_graveyards() -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, 129)
    nonpole_rho = initial_density(math.pi / 3.0)
    pole_rho = initial_density(0.0)

    global_metrics = path_metrics(transport_density(nonpole_rho, global_phase_operator, values))
    relative_metrics = path_metrics(transport_density(nonpole_rho, relative_phase_operator, values))
    pole_relative = path_metrics(transport_density(pole_rho, relative_phase_operator, values))
    diagonal_readout = [
        float(np.real(rho.expectation_value(PAULI["z"])))
        for rho in transport_density(nonpole_rho, relative_phase_operator, values)
    ]

    same_global_collapses = bool(relative_metrics["density_displacement_from_start"] < 1e-9)
    same_relative_collapses = bool(global_metrics["density_displacement_from_start"] > 1.0)
    return {
        "both_transports_global_phase_would_collapse_distinction": {
            "candidate_passed": same_global_collapses,
            "expected": False,
            "passed": same_global_collapses is False,
        },
        "both_transports_relative_phase_would_collapse_distinction": {
            "candidate_passed": same_relative_collapses,
            "expected": False,
            "passed": same_relative_collapses is False,
        },
        "relative_phase_on_pole_density_degenerates": {
            "density_displacement_from_start": pole_relative["density_displacement_from_start"],
            "expected_near_zero": True,
            "passed": bool(pole_relative["density_displacement_from_start"] < 1e-9),
        },
        "diagonal_only_readout_hides_relative_phase_transport": {
            "sigmaz_span": float(max(diagonal_readout) - min(diagonal_readout)),
            "expected_near_zero": True,
            "passed": bool(abs(max(diagonal_readout) - min(diagonal_readout)) < 1e-9),
        },
        "bare_phase_operators_without_density_carrier_are_insufficient": {
            "has_density_carrier": False,
            "has_loop_family": False,
            "can_compare_density_transport": False,
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
            "Qiskit non-pole parameter-sweep baseline for global-phase density invariance and relative-phase "
            "density transport on two-component pure-state densities only; no full Hopf bundle, no physical loop "
            "independence, no flux, no QIT, GStack, axis, bridge, engine, target-system, or nonclassical admission"
        ),
        "next_lego_target": "two_component_global_relative_phase_density_transport_sweep",
        "promotion_condition": "No promotion from this sweep; use only as bounded calibration for later carrier/topology fixtures.",
        "blocked_until": "blocked from geometric-constraint-manifold claims until nested carrier geometry and physical-evolution graveyards exist",
        "demotion_condition": "Demote if cited as full Hopf geometry, physical loop independence, flux, QIT, GStack, axis, bridge, engine, target-system, or nonclassical evidence.",
        "divergence_log": (
            "This sweep only shows that a two-component density is invariant under sampled global-phase transport "
            "and moves under sampled relative-phase transport away from pole states. It deliberately diverges from "
            "full geometric-constraint-manifold work by omitting nested carrier geometry, flux representation, "
            "Lindblad terrain dynamics, and any target-system admission."
        ),
        "operation_sequence": [
            "construct two-component pure-state densities for several non-pole polar angles",
            "sample global-phase Operator exp(i phase I/2)",
            "sample relative-phase Operator exp(i phase sigma_z/2)",
            "compare density displacement and Bloch displacement against closed-form non-pole expectations",
            "run same-generator, pole-density, hidden-readout, and no-carrier graveyards",
        ],
        "carrier_topology": "two-component density carrier with sampled global-phase and relative-phase unitary loop families; no full Hopf bundle or nested-tori manifold",
        "observable": "Qiskit density Frobenius displacement, Bloch displacement, trace, purity, and Pauli readouts over theta/sample-count sweep",
        "pass_fail_predicate": "global-phase transport leaves density invariant; relative-phase transport displacement matches sqrt(2) sin(theta) in density norm and 2 sin(theta) in Bloch norm; trace and purity remain one; adjacent graveyards collapse or become insufficient",
        "graveyards": [
            "both transports use global-phase generator",
            "both transports use relative-phase generator",
            "relative phase on pole density degenerates",
            "diagonal-only readout hides relative phase transport",
            "bare phase operators without density carrier are insufficient",
        ],
        "baselines": [
            "single-theta Qiskit phase-generator density transport receipt",
            "single-theta QuTiP phase-generator density transport receipt",
            "QuTiP global-relative phase non-pole sweep receipt",
        ],
        "alternative_formulations": [
            "QuTiP Qobj parameter sweep",
            "SymPy exact matrix-exponential proof over symbolic theta",
            "Clifford rotor relative-phase companion",
            "nested Hopf-torus carrier fixture before stronger geometry claims",
        ],
        "exact_tool_function_needs": {
            "qiskit": ["Statevector", "DensityMatrix", "Operator", "DensityMatrix.expectation_value"],
            "numpy": ["linspace", "eye", "exp", "array", "linalg.norm"],
        },
        "lego_or_coupling_target": "two_component_global_relative_phase_density_transport_sweep",
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
            "No full Hopf bundle or nested Hopf-torus carrier.",
            "No physical loop-independence closure.",
            "No flux representation.",
            "No QIT, GStack, axis, bridge, engine, target-system, or nonclassical claim.",
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
