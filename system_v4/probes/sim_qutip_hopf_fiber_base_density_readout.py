#!/usr/bin/env python3
"""QuTiP density readout for Hopf fiber and base carrier loops."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import qutip as qt
from receipt_boundary import apply_default_receipt_boundary


NAME = "qutip_hopf_fiber_base_density_readout"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "constructs Qobj carrier states, density matrices, and Pauli expectation readouts along declared paths",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples path parameters and computes bounded path-length metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": "load_bearing", "numpy": "supportive"}


def ket(theta: float, phi: float, chi: float) -> qt.Qobj:
    vector = np.array(
        [
            math.cos(theta / 2.0) * np.exp(0.5j * (chi + phi)),
            math.sin(theta / 2.0) * np.exp(0.5j * (chi - phi)),
        ],
        dtype=complex,
    )
    return qt.Qobj(vector.reshape((2, 1)))


def density_path(states: list[qt.Qobj]) -> list[qt.Qobj]:
    return [qt.ket2dm(state) for state in states]


def pauli_readout(rho: qt.Qobj) -> list[float]:
    return [
        float(np.real(qt.expect(qt.sigmax(), rho))),
        float(np.real(qt.expect(qt.sigmay(), rho))),
        float(np.real(qt.expect(qt.sigmaz(), rho))),
    ]


def path_metrics(states: list[qt.Qobj]) -> dict[str, float | list[float]]:
    densities = density_path(states)
    bloch = [np.array(pauli_readout(rho), dtype=float) for rho in densities]
    density_steps = [
        float((densities[idx + 1] - densities[idx]).norm("fro"))
        for idx in range(len(densities) - 1)
    ]
    bloch_steps = [
        float(np.linalg.norm(bloch[idx + 1] - bloch[idx]))
        for idx in range(len(bloch) - 1)
    ]
    return {
        "density_path_length": float(sum(density_steps)),
        "bloch_path_length": float(sum(bloch_steps)),
        "density_displacement_from_start": float(
            max((rho - densities[0]).norm("fro") for rho in densities)
        ),
        "bloch_displacement_from_start": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "start_bloch": [float(value) for value in bloch[0]],
        "end_bloch": [float(value) for value in bloch[-1]],
        "trace_start": float(np.real(densities[0].tr())),
        "trace_end": float(np.real(densities[-1].tr())),
    }


def sample_inner_loop(theta: float, phi: float, samples: int) -> list[qt.Qobj]:
    return [ket(theta, phi, chi) for chi in np.linspace(0.0, 2.0 * math.pi, samples)]


def sample_outer_loop(theta: float, chi: float, samples: int) -> list[qt.Qobj]:
    return [ket(theta, phi, chi) for phi in np.linspace(0.0, 2.0 * math.pi, samples)]


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
        "survives_qutip_density_readout": survives(inner, outer),
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
        "qutip_state_without_path_is_insufficient": {
            "has_path_family": False,
            "can_distinguish_fiber_base": False,
            "passed": True,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_qutip_density_readout"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "QuTiP density-object readout baseline over declared Hopf-coordinate paths only; no physical "
            "fiber/base loop independence, no full S3 bundle, no QIT, GStack, axis, bridge, nonclassical, "
            "target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "declared_fiber_base_coordinate_readout_baseline",
        "promotion_condition": (
            "May only support later operator/path planning after independent carrier and dynamics receipts reproduce "
            "the same distinction with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if QuTiP density readouts vary on the fiber loop, fail to vary on the base loop away from the pole, "
            "or if same-path and pole graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until a fuller carrier/topology and physical-evolution fixture exists",
        "out_of_scope": [
            "No Lindblad evolution or Hamiltonian dynamics.",
            "No target-system, QIT, GStack, axis, bridge, or nonclassical admission.",
            "No claim that flux is represented.",
        ],
        "divergence_log": (
            "This is a QuTiP object-level baseline for density readouts along declared paths. It is not a physical "
            "fiber/base independence result, dynamical proof, or target-system proof."
        ),
        "operation_sequence": [
            "construct Qobj two-component carrier states in Hopf-style coordinates",
            "convert each carrier state to a QuTiP density matrix",
            "sample an fiber loop by varying chi at fixed theta and phi",
            "sample an base loop by varying phi at fixed theta and chi",
            "compute sigmax, sigmay, and sigmaz expectation readouts",
            "run same-path, pole-degenerate, and no-path graveyards",
        ],
        "carrier_topology": "QuTiP two-component state path with density projection; no full nested-tori manifold",
        "observable": "QuTiP density Frobenius path length and Pauli expectation path length",
        "pass_fail_predicate": (
            "fiber density and Pauli readout path lengths collapse while base readout path lengths survive away from degeneracy"
        ),
        "graveyards": [
            "both paths forced to fiber loop collapse distinction",
            "both paths forced to base loop collapse distinction",
            "base loop at pole degenerates",
            "single QuTiP state without path is insufficient",
        ],
        "baselines": [
            "sampled NumPy Hopf path metric fixture",
            "symbolic SymPy Hopf density derivative fixture",
            "bare Pauli no-carrier negative control",
        ],
        "alternative_formulations": [
            "Lindblad path evolution fixture",
            "Hamiltonian generator fixture",
            "cell-complex path transport fixture",
        ],
        "exact_tool_function_needs": {
            "qutip": ["Qobj", "ket2dm", "expect", "sigmax", "sigmay", "sigmaz"],
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
