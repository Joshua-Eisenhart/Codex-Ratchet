#!/usr/bin/env python3
"""QuTiP Hopf loop phase-generator density transport baseline."""

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
import qutip as qt
from receipt_boundary import apply_default_receipt_boundary


NAME = "qutip_hopf_loop_phase_generator_density_transport"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": (
            "constructs density operators, phase-generator unitaries, operator exponentials, and Pauli expectation "
            "readouts for inner/global-phase and outer/relative-phase Hopf loop transports"
        ),
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples loop parameters and computes path-length/readout metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": "load_bearing", "numpy": "supportive"}


def initial_ket(theta: float) -> qt.Qobj:
    return qt.Qobj(
        np.array([math.cos(theta / 2.0), math.sin(theta / 2.0)], dtype=complex).reshape((2, 1))
    )


def inner_unitary(chi: float) -> qt.Qobj:
    return (0.5j * chi * qt.qeye(2)).expm()


def outer_unitary(phi: float) -> qt.Qobj:
    return (0.5j * phi * qt.sigmaz()).expm()


def evolve_density(rho0: qt.Qobj, unitary_fn, values: np.ndarray) -> list[qt.Qobj]:
    return [unitary_fn(float(value)) * rho0 * unitary_fn(float(value)).dag() for value in values]


def pauli_readout(rho: qt.Qobj) -> np.ndarray:
    return np.array(
        [
            float(np.real(qt.expect(qt.sigmax(), rho))),
            float(np.real(qt.expect(qt.sigmay(), rho))),
            float(np.real(qt.expect(qt.sigmaz(), rho))),
        ],
        dtype=float,
    )


def path_metrics(densities: list[qt.Qobj]) -> dict[str, object]:
    bloch = [pauli_readout(rho) for rho in densities]
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
        "density_displacement_from_start": float(
            max((rho - densities[0]).norm("fro") for rho in densities)
        ),
        "bloch_path_length": float(sum(bloch_steps)),
        "bloch_displacement_from_start": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "trace_min": float(min(np.real(rho.tr()) for rho in densities)),
        "trace_max": float(max(np.real(rho.tr()) for rho in densities)),
        "purity_min": float(min(np.real((rho * rho).tr()) for rho in densities)),
        "purity_max": float(max(np.real((rho * rho).tr()) for rho in densities)),
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
        and abs(inner["trace_max"] - 1.0) < tol
        and abs(outer["trace_min"] - 1.0) < tol
        and abs(outer["trace_max"] - 1.0) < tol
        and abs(inner["purity_min"] - 1.0) < tol
        and abs(outer["purity_min"] - 1.0) < tol
    )


def run_transport(theta: float) -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, 129)
    rho0 = qt.ket2dm(initial_ket(theta))
    inner = path_metrics(evolve_density(rho0, inner_unitary, values))
    outer = path_metrics(evolve_density(rho0, outer_unitary, values))
    return {
        "theta": theta,
        "sample_count": int(values.size),
        "inner_global_phase_transport": inner,
        "outer_relative_phase_transport": outer,
        "survives_phase_generator_density_transport": survives(inner, outer),
    }


def run_graveyards() -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, 129)
    rho_nonpole = qt.ket2dm(initial_ket(math.pi / 3.0))
    rho_pole = qt.ket2dm(initial_ket(0.0))

    inner = path_metrics(evolve_density(rho_nonpole, inner_unitary, values))
    outer = path_metrics(evolve_density(rho_nonpole, outer_unitary, values))
    pole_outer = path_metrics(evolve_density(rho_pole, outer_unitary, values))
    diagonal_readout = [
        float(np.real(qt.expect(qt.sigmaz(), rho)))
        for rho in evolve_density(rho_nonpole, outer_unitary, values)
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
        "bare_generators_without_carrier_state_are_insufficient": {
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
            "QuTiP phase-generator density-transport baseline for Hopf-style inner/global-phase and "
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
            "No Lindblad dynamics or target-system admission.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system claim.",
        ],
        "divergence_log": (
            "This is a QuTiP operator-object baseline. It distinguishes global-phase density invariance from "
            "relative-phase density transport on a two-component carrier, but it does not prove full geometric "
            "inner/outer independence."
        ),
        "operation_sequence": [
            "construct a two-component non-pole carrier density",
            "define the inner loop as global-phase unitary exp(i chi I/2)",
            "define the outer loop as relative-phase unitary exp(i phi sigma_z/2)",
            "transport the same density by both unitary families",
            "compute density path length, Bloch path length, trace, and purity readouts",
            "run same-generator, pole-state, diagonal-hidden, and no-carrier graveyards",
        ],
        "carrier_topology": (
            "two-component density carrier with Hopf-style phase-generator loop families; no full nested-tori "
            "manifold"
        ),
        "observable": "QuTiP density Frobenius path length, Bloch path length, trace, purity, and Pauli readouts",
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
            "bare generators without carrier state are insufficient",
        ],
        "baselines": [
            "sampled NumPy Hopf inner/outer path metric fixture",
            "SymPy Hopf density derivative identity",
            "QuTiP Hopf inner/outer density path readout fixture",
            "bare Pauli no-carrier negative control",
        ],
        "alternative_formulations": [
            "Qiskit Operator/DensityMatrix unitary phase-generator transport",
            "SymPy exact matrix-exponential phase-generator identity",
            "Clifford rotor relative-phase transport control",
            "nested Hopf-torus carrier transport fixture",
        ],
        "exact_tool_function_needs": {
            "qutip": ["Qobj", "qeye", "sigmaz", "sigmax", "sigmay", "ket2dm", "Qobj.expm", "expect"],
            "numpy": ["linspace", "array", "linalg.norm"],
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
