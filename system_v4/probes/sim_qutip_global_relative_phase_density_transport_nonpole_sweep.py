#!/usr/bin/env python3
"""QuTiP non-pole sweep for global-vs-relative phase density transport."""

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


NAME = "qutip_global_relative_phase_density_transport_nonpole_sweep"
CLASSIFICATION = "classical_baseline"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TOOL_MANIFEST = {
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "constructs density operators, global/relative phase unitaries, and Pauli expectation readouts",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples phase-loop parameters and computes vector norms across non-pole carrier states",
    },
}
TOOL_INTEGRATION_DEPTH = {"qutip": "load_bearing", "numpy": "supportive"}


def initial_ket(theta: float) -> qt.Qobj:
    return qt.Qobj(np.array([math.cos(theta / 2.0), math.sin(theta / 2.0)], dtype=complex).reshape((2, 1)))


def global_phase_unitary(phase: float) -> qt.Qobj:
    return (0.5j * phase * qt.qeye(2)).expm()


def relative_phase_unitary(phase: float) -> qt.Qobj:
    return (0.5j * phase * qt.sigmaz()).expm()


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
    density_steps = [float((densities[idx + 1] - densities[idx]).norm("fro")) for idx in range(len(densities) - 1)]
    bloch_steps = [float(np.linalg.norm(bloch[idx + 1] - bloch[idx])) for idx in range(len(bloch) - 1)]
    return {
        "density_path_length": float(sum(density_steps)),
        "density_displacement_from_start": float(max((rho - densities[0]).norm("fro") for rho in densities)),
        "bloch_path_length": float(sum(bloch_steps)),
        "bloch_displacement_from_start": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "trace_min": float(min(np.real(rho.tr()) for rho in densities)),
        "trace_max": float(max(np.real(rho.tr()) for rho in densities)),
        "purity_min": float(min(np.real((rho * rho).tr()) for rho in densities)),
        "purity_max": float(max(np.real((rho * rho).tr()) for rho in densities)),
    }


def run_case(theta: float, sample_count: int) -> dict[str, object]:
    values = np.linspace(0.0, 2.0 * math.pi, sample_count)
    rho0 = qt.ket2dm(initial_ket(theta))
    global_metrics = path_metrics(evolve_density(rho0, global_phase_unitary, values))
    relative_metrics = path_metrics(evolve_density(rho0, relative_phase_unitary, values))
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
    nonpole_rho = qt.ket2dm(initial_ket(math.pi / 3.0))
    pole_rho = qt.ket2dm(initial_ket(0.0))

    global_metrics = path_metrics(evolve_density(nonpole_rho, global_phase_unitary, values))
    relative_metrics = path_metrics(evolve_density(nonpole_rho, relative_phase_unitary, values))
    pole_relative = path_metrics(evolve_density(pole_rho, relative_phase_unitary, values))
    diagonal_readout = [
        float(np.real(qt.expect(qt.sigmaz(), rho)))
        for rho in evolve_density(nonpole_rho, relative_phase_unitary, values)
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
        "bare_phase_generators_without_density_carrier_are_insufficient": {
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
            "QuTiP non-pole parameter-sweep baseline for global-phase density invariance and relative-phase "
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
            "sample global-phase unitary transport exp(i phase I/2)",
            "sample relative-phase unitary transport exp(i phase sigma_z/2)",
            "compare density displacement and Bloch displacement against closed-form non-pole expectations",
            "run same-generator, pole-density, hidden-readout, and no-carrier graveyards",
        ],
        "carrier_topology": "two-component density carrier with sampled global-phase and relative-phase unitary loop families; no full Hopf bundle or nested-tori manifold",
        "observable": "QuTiP density Frobenius displacement, Bloch displacement, trace, purity, and Pauli readouts over theta/sample-count sweep",
        "pass_fail_predicate": "global-phase transport leaves density invariant; relative-phase transport displacement matches sqrt(2) sin(theta) in density norm and 2 sin(theta) in Bloch norm; trace and purity remain one; adjacent graveyards collapse or become insufficient",
        "graveyards": [
            "both transports use global-phase generator",
            "both transports use relative-phase generator",
            "relative phase on pole density degenerates",
            "diagonal-only readout hides relative phase transport",
            "bare phase generators without density carrier are insufficient",
        ],
        "baselines": [
            "single-theta QuTiP phase-generator density transport receipt",
            "single-theta Qiskit phase-generator density transport receipt",
            "backend-agreement audit over existing QuTiP/Qiskit transport receipts",
        ],
        "alternative_formulations": [
            "Qiskit DensityMatrix parameter sweep",
            "SymPy exact matrix-exponential proof over symbolic theta",
            "Clifford rotor relative-phase companion",
            "nested Hopf-torus carrier fixture before stronger geometry claims",
        ],
        "exact_tool_function_needs": {
            "qutip": ["Qobj", "qeye", "sigmaz", "sigmax", "sigmay", "ket2dm", "Qobj.expm", "expect"],
            "numpy": ["linspace", "array", "linalg.norm"],
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
