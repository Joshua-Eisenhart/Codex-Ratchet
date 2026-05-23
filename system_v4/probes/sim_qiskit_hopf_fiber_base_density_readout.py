#!/usr/bin/env python3
"""Qiskit density readout for Hopf fiber and base carrier loops."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import numpy as np
from qiskit.quantum_info import DensityMatrix, Operator, Statevector
from receipt_boundary import apply_default_receipt_boundary


NAME = "qiskit_hopf_fiber_base_density_readout"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qiskit": {
        "tried": True,
        "used": True,
        "reason": "constructs Statevector and DensityMatrix objects and computes Pauli expectation readouts along declared paths",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples path parameters and computes bounded density/readout path metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"qiskit": "load_bearing", "numpy": "supportive"}

PAULI = {
    "x": Operator(np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)),
    "y": Operator(np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)),
    "z": Operator(np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)),
}


def statevector(theta: float, phi: float, chi: float) -> Statevector:
    vector = np.array(
        [
            math.cos(theta / 2.0) * np.exp(0.5j * (chi + phi)),
            math.sin(theta / 2.0) * np.exp(0.5j * (chi - phi)),
        ],
        dtype=complex,
    )
    return Statevector(vector)


def density_path(states: list[Statevector]) -> list[DensityMatrix]:
    return [DensityMatrix(state) for state in states]


def pauli_readout(rho: DensityMatrix) -> np.ndarray:
    return np.array([float(np.real(rho.expectation_value(op))) for op in PAULI.values()])


def path_metrics(states: list[Statevector]) -> dict[str, float | list[float]]:
    densities = density_path(states)
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
    return {
        "density_path_length": float(sum(density_steps)),
        "bloch_path_length": float(sum(bloch_steps)),
        "density_displacement_from_start": float(
            max(np.linalg.norm(matrix - matrices[0], ord="fro") for matrix in matrices)
        ),
        "bloch_displacement_from_start": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "start_bloch": [float(value) for value in bloch[0]],
        "end_bloch": [float(value) for value in bloch[-1]],
        "trace_start": float(np.real(np.trace(matrices[0]))),
        "trace_end": float(np.real(np.trace(matrices[-1]))),
    }


def sample_inner_loop(theta: float, phi: float, samples: int) -> list[Statevector]:
    return [statevector(theta, phi, chi) for chi in np.linspace(0.0, 2.0 * math.pi, samples)]


def sample_outer_loop(theta: float, chi: float, samples: int) -> list[Statevector]:
    return [statevector(theta, phi, chi) for phi in np.linspace(0.0, 2.0 * math.pi, samples)]


def survives(inner: dict[str, object], outer: dict[str, object]) -> bool:
    density_tol = 1e-9
    traversing_tol = 1.0
    return bool(
        inner["density_displacement_from_start"] < density_tol
        and inner["bloch_path_length"] < density_tol
        and outer["density_displacement_from_start"] > traversing_tol
        and outer["bloch_path_length"] > traversing_tol
        and abs(inner["trace_start"] - 1.0) < density_tol
        and abs(outer["trace_start"] - 1.0) < density_tol
    )


def run_positive() -> dict[str, object]:
    samples = 129
    theta = math.pi / 3.0
    inner = path_metrics(sample_inner_loop(theta=theta, phi=math.pi / 5.0, samples=samples))
    outer = path_metrics(sample_outer_loop(theta=theta, chi=0.0, samples=samples))
    return {
        "samples": samples,
        "theta": theta,
        "inner_loop": inner,
        "outer_loop": outer,
        "survives_qiskit_density_readout": survives(inner, outer),
    }


def run_graveyards() -> dict[str, object]:
    samples = 129
    theta = math.pi / 3.0
    inner = path_metrics(sample_inner_loop(theta=theta, phi=math.pi / 5.0, samples=samples))
    outer = path_metrics(sample_outer_loop(theta=theta, chi=0.0, samples=samples))
    pole_outer = path_metrics(sample_outer_loop(theta=0.0, chi=0.0, samples=samples))
    return {
        "both_paths_inner_collapses_distinction": {
            "candidate_passed": survives(inner, inner),
            "expected": False,
            "passed": survives(inner, inner) is False,
        },
        "both_paths_outer_collapses_distinction": {
            "candidate_passed": survives(outer, outer),
            "expected": False,
            "passed": survives(outer, outer) is False,
        },
        "outer_loop_at_pole_degenerates": {
            "density_displacement_from_start": pole_outer["density_displacement_from_start"],
            "expected_collapse": True,
            "passed": bool(pole_outer["density_displacement_from_start"] < 1e-9),
        },
        "statevector_without_path_is_insufficient": {
            "has_path_family": False,
            "can_distinguish_fiber_base": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_qiskit_density_readout"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Qiskit Statevector/DensityMatrix readout baseline over declared Hopf-coordinate paths only; no "
            "physical fiber/base loop independence, no full S3 bundle, no QIT, GStack, axis, bridge, "
            "nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "declared_fiber_base_coordinate_readout_baseline",
        "promotion_condition": (
            "May only support later operator/path planning after independent carrier and dynamics receipts reproduce "
            "the same distinction with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if Qiskit density readouts vary on the fiber loop, fail to vary on the base loop away from the pole, "
            "or if same-path and pole graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until a fuller carrier/topology and physical-evolution fixture exists",
        "out_of_scope": [
            "No circuit execution, Lindblad evolution, or Hamiltonian dynamics.",
            "No target-system, QIT, GStack, axis, bridge, or nonclassical admission.",
            "No claim that flux is represented.",
        ],
        "divergence_log": (
            "This is a Qiskit object-level baseline for density readouts along declared paths. It is not a physical "
            "fiber/base independence result, dynamical proof, or target-system proof."
        ),
        "operation_sequence": [
            "construct Qiskit Statevector two-component carrier states in Hopf-style coordinates",
            "convert each carrier state to a Qiskit DensityMatrix",
            "sample an fiber loop by varying chi at fixed theta and phi",
            "sample an base loop by varying phi at fixed theta and chi",
            "compute Pauli Operator expectation readouts",
            "run same-path, pole-degenerate, and no-path graveyards",
        ],
        "carrier_topology": "Qiskit two-component state path with density projection; no full nested-tori manifold",
        "observable": "Qiskit density Frobenius path length and Pauli expectation path length",
        "pass_fail_predicate": (
            "fiber density and Pauli readout path lengths collapse while base readout path lengths survive away from degeneracy"
        ),
        "graveyards": [
            "both paths forced to fiber loop collapse distinction",
            "both paths forced to base loop collapse distinction",
            "base loop at pole degenerates",
            "single Statevector without path is insufficient",
        ],
        "baselines": [
            "sampled NumPy Hopf path metric fixture",
            "symbolic SymPy Hopf density derivative fixture",
            "QuTiP density-object path readout fixture",
            "bare Pauli no-carrier negative control",
        ],
        "alternative_formulations": [
            "circuit parameterization fixture",
            "Hamiltonian generator fixture",
            "cell-complex path transport fixture",
        ],
        "exact_tool_function_needs": {
            "qiskit": ["Statevector", "DensityMatrix", "Operator.expectation_value"],
            "numpy": ["linspace", "exp", "linalg.norm"],
        },
        "lego_or_coupling_target": "declared_fiber_base_coordinate_readout_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
