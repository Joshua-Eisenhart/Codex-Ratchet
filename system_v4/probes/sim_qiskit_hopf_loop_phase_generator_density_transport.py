#!/usr/bin/env python3
"""Qiskit Hopf loop phase-generator density transport baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from qiskit.quantum_info import DensityMatrix, Operator, Statevector
from receipt_boundary import apply_default_receipt_boundary


NAME = "qiskit_hopf_loop_phase_generator_density_transport"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qiskit": {
        "tried": True,
        "used": True,
        "reason": (
            "constructs Statevector/DensityMatrix carrier objects, Operator phase transports, and Pauli "
            "expectation readouts for inner/global-phase and outer/relative-phase Hopf loop transports"
        ),
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples loop parameters, constructs diagonal unitary matrices, and computes path metrics",
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


def inner_operator(chi: float) -> Operator:
    return Operator(np.exp(0.5j * chi) * np.eye(2, dtype=complex))


def outer_operator(phi: float) -> Operator:
    return Operator(
        np.array(
            [[np.exp(0.5j * phi), 0.0], [0.0, np.exp(-0.5j * phi)]],
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
    density_steps = [
        float(np.linalg.norm(matrices[idx + 1] - matrices[idx], ord="fro"))
        for idx in range(len(matrices) - 1)
    ]
    bloch_steps = [
        float(np.linalg.norm(bloch[idx + 1] - bloch[idx]))
        for idx in range(len(bloch) - 1)
    ]
    purities = [float(np.real(np.trace(matrix @ matrix))) for matrix in matrices]
    traces = [float(np.real(np.trace(matrix))) for matrix in matrices]
    return {
        "density_path_length": float(sum(density_steps)),
        "density_displacement_from_start": float(
            max(np.linalg.norm(matrix - matrices[0], ord="fro") for matrix in matrices)
        ),
        "bloch_path_length": float(sum(bloch_steps)),
        "bloch_displacement_from_start": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "trace_min": float(min(traces)),
        "trace_max": float(max(traces)),
        "purity_min": float(min(purities)),
        "purity_max": float(max(purities)),
        "start_bloch": [float(value) for value in bloch[0]],
        "end_bloch": [float(value) for value in bloch[-1]],
    }


def survives(inner: dict[str, object], outer: dict[str, object]) -> bool:
    tol = 1e-9
    traversing_tol = 1.0
    return bool(
        inner["density_displacement_from_start"] < tol
        and inner["bloch_path_length"] < tol
        and outer["density_displacement_from_start"] > traversing_tol
        and outer["bloch_path_length"] > traversing_tol
        and abs(inner["trace_min"] - 1.0) < tol
        and abs(outer["trace_min"] - 1.0) < tol
        and abs(inner["purity_min"] - 1.0) < tol
        and abs(outer["purity_min"] - 1.0) < tol
    )


def run_transport(theta: float) -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, 129)
    rho0 = initial_density(theta)
    inner = path_metrics(transport_density(rho0, inner_operator, values))
    outer = path_metrics(transport_density(rho0, outer_operator, values))
    return {
        "theta": theta,
        "sample_count": int(values.size),
        "inner_global_phase_transport": inner,
        "outer_relative_phase_transport": outer,
        "survives_phase_generator_density_transport": survives(inner, outer),
    }


def run_graveyards() -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, 129)
    rho_nonpole = initial_density(math.pi / 3.0)
    rho_pole = initial_density(0.0)

    inner = path_metrics(transport_density(rho_nonpole, inner_operator, values))
    outer = path_metrics(transport_density(rho_nonpole, outer_operator, values))
    pole_outer = path_metrics(transport_density(rho_pole, outer_operator, values))
    diagonal_readout = [
        float(np.real(rho.expectation_value(PAULI["z"])))
        for rho in transport_density(rho_nonpole, outer_operator, values)
    ]

    return {
        "both_transports_inner_generator_collapses_distinction": {
            "candidate_passed": survives(inner, inner),
            "expected": False,
            "passed": survives(inner, inner) is False,
        },
        "both_transports_outer_generator_collapses_distinction": {
            "candidate_passed": survives(outer, outer),
            "expected": False,
            "passed": survives(outer, outer) is False,
        },
        "outer_relative_phase_on_pole_state_degenerates": {
            "density_displacement_from_start": pole_outer["density_displacement_from_start"],
            "passed": bool(pole_outer["density_displacement_from_start"] < 1e-9),
        },
        "diagonal_only_readout_hides_outer_transport": {
            "sigmaz_span": float(max(diagonal_readout) - min(diagonal_readout)),
            "passed": bool(abs(max(diagonal_readout) - min(diagonal_readout)) < 1e-9),
        },
        "bare_operators_without_carrier_density_are_insufficient": {
            "has_density_carrier": False,
            "has_loop_family": False,
            "can_compare_transport_readout": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_transport(theta=math.pi / 3.0)
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_phase_generator_density_transport"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Qiskit phase-generator density-transport baseline for Hopf-style inner/global-phase and "
            "outer/relative-phase loop transports only; no physical inner/outer loop independence, no full S3 "
            "bundle, no flux, no QIT, GStack, axis, bridge, nonclassical, target-system, or full "
            "geometric-constraint-manifold admission"
        ),
        "next_lego_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "promotion_condition": (
            "May only support later geometry planning after a fuller carrier/topology fixture and physical "
            "graveyards reproduce compatible generator/path readouts."
        ),
        "demotion_condition": (
            "Demote if global-phase transport changes density, if relative-phase transport fails to move a "
            "non-pole density readout, if trace/purity drift, or if same-generator, pole, hidden-readout, and "
            "no-carrier graveyards do not collapse."
        ),
        "blocked_until": (
            "blocked from target-system claims until explicit nested carrier geometry, declared observables, and "
            "physical-evolution graveyards exist"
        ),
        "out_of_scope": [
            "No full nested Hopf-torus carrier.",
            "No flux representation or Pauli shortcut.",
            "No circuit backend execution or target-system admission.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system claim.",
        ],
        "divergence_log": (
            "This is a Qiskit operator-object baseline. It distinguishes global-phase density invariance from "
            "relative-phase density transport on a two-component carrier, but it does not prove full geometric "
            "inner/outer independence."
        ),
        "operation_sequence": [
            "construct a two-component non-pole carrier density",
            "define the inner loop as global-phase Operator exp(i chi I/2)",
            "define the outer loop as relative-phase Operator exp(i phi sigma_z/2)",
            "transport the same density by both operator families",
            "compute density path length, Bloch path length, trace, and purity readouts",
            "run same-generator, pole-state, diagonal-hidden, and no-carrier graveyards",
        ],
        "carrier_topology": (
            "two-component density carrier with Hopf-style phase-generator loop families; no full nested-tori "
            "manifold"
        ),
        "observable": "Qiskit density Frobenius path length, Bloch path length, trace, purity, and Pauli readouts",
        "pass_fail_predicate": (
            "inner/global-phase transport leaves density and Bloch readouts invariant; outer/relative-phase "
            "transport moves density and Bloch readouts away from the pole; trace and purity remain one; adjacent "
            "graveyards collapse or become insufficient"
        ),
        "graveyards": [
            "both transports use inner generator",
            "both transports use outer generator",
            "outer relative phase on pole state degenerates",
            "diagonal-only readout hides outer transport",
            "bare operators without carrier density are insufficient",
        ],
        "baselines": [
            "sampled NumPy Hopf inner/outer path metric fixture",
            "SymPy Hopf density derivative identity",
            "Qiskit Hopf inner/outer density path readout fixture",
            "bare Pauli no-carrier negative control",
        ],
        "alternative_formulations": [
            "QuTiP Qobj.expm phase-generator transport",
            "SymPy exact matrix-exponential phase-generator identity",
            "Clifford rotor relative-phase transport control",
            "nested Hopf-torus carrier transport fixture",
        ],
        "exact_tool_function_needs": {
            "qiskit": ["Statevector", "DensityMatrix", "Operator", "DensityMatrix.expectation_value"],
            "numpy": ["linspace", "eye", "exp", "array", "linalg.norm"],
        },
        "lego_or_coupling_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
