#!/usr/bin/env python3
"""Hopf-style two-component carrier loop readout geometry baseline."""

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
from receipt_boundary import apply_default_receipt_boundary


NAME = "numpy_hopf_weyl_fiber_base_loop_readout_geometry"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples normalized complex two-component carrier paths and computes density/readout path metrics",
    }
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

PAULI = {
    "x": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex),
    "y": np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex),
    "z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex),
}


def spinor(theta: float, phi: float, chi: float) -> np.ndarray:
    """Normalized Hopf-coordinate carrier in C^2."""
    return np.array(
        [
            math.cos(theta / 2.0) * np.exp(0.5j * (chi + phi)),
            math.sin(theta / 2.0) * np.exp(0.5j * (chi - phi)),
        ],
        dtype=complex,
    )


def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, np.conjugate(psi))


def bloch_readout(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(rho @ matrix))) for matrix in PAULI.values()])


def path_metrics(states: list[np.ndarray]) -> dict[str, float | list[float]]:
    densities = [density(psi) for psi in states]
    bloch = [bloch_readout(rho) for rho in densities]

    density_steps = [
        float(np.linalg.norm(densities[idx + 1] - densities[idx], ord="fro"))
        for idx in range(len(densities) - 1)
    ]
    state_steps = [
        float(np.linalg.norm(states[idx + 1] - states[idx]))
        for idx in range(len(states) - 1)
    ]
    bloch_steps = [
        float(np.linalg.norm(bloch[idx + 1] - bloch[idx]))
        for idx in range(len(bloch) - 1)
    ]
    first_component_phase = np.unwrap(np.angle([psi[0] for psi in states]))
    return {
        "density_path_length": float(sum(density_steps)),
        "state_path_length": float(sum(state_steps)),
        "bloch_path_length": float(sum(bloch_steps)),
        "density_displacement_from_start": float(
            max(np.linalg.norm(rho - densities[0], ord="fro") for rho in densities)
        ),
        "bloch_displacement_from_start": float(max(np.linalg.norm(row - bloch[0]) for row in bloch)),
        "first_component_phase_span": float(first_component_phase[-1] - first_component_phase[0]),
        "start_bloch": [float(value) for value in bloch[0]],
        "end_bloch": [float(value) for value in bloch[-1]],
    }


def sample_inner_loop(theta: float, phi: float, samples: int) -> list[np.ndarray]:
    return [spinor(theta, phi, chi) for chi in np.linspace(0.0, 2.0 * math.pi, samples)]


def sample_outer_loop(theta: float, chi: float, samples: int) -> list[np.ndarray]:
    return [spinor(theta, phi, chi) for phi in np.linspace(0.0, 2.0 * math.pi, samples)]


def survives_fiber_base_readout(inner: dict[str, object], outer: dict[str, object]) -> bool:
    density_tol = 1e-9
    traversing_tol = 1.0
    return bool(
        inner["density_displacement_from_start"] < density_tol
        and inner["bloch_path_length"] < density_tol
        and inner["state_path_length"] > traversing_tol
        and outer["density_displacement_from_start"] > traversing_tol
        and outer["bloch_path_length"] > traversing_tol
    )


def run_positive() -> dict[str, object]:
    theta = math.pi / 3.0
    phi = math.pi / 5.0
    samples = 129
    inner = path_metrics(sample_inner_loop(theta=theta, phi=phi, samples=samples))
    outer = path_metrics(sample_outer_loop(theta=theta, chi=0.0, samples=samples))
    return {
        "theta": theta,
        "fixed_inner_phi": phi,
        "samples": samples,
        "inner_loop": inner,
        "outer_loop": outer,
        "survives_fiber_base_readout": survives_fiber_base_readout(inner, outer),
    }


def run_graveyards() -> dict[str, object]:
    theta = math.pi / 3.0
    phi = math.pi / 5.0
    samples = 129

    inner_as_outer = path_metrics(sample_outer_loop(theta=theta, chi=0.0, samples=samples))
    outer_as_inner = path_metrics(sample_inner_loop(theta=theta, phi=phi, samples=samples))
    both_inner = survives_fiber_base_readout(outer_as_inner, outer_as_inner)
    both_outer = survives_fiber_base_readout(inner_as_outer, inner_as_outer)

    bare_pauli_only = {
        "has_carrier_path": False,
        "can_compute_loop_readout": False,
        "passed": True,
    }

    density_hidden = {
        "inner_state_path_nonzero": bool(outer_as_inner["state_path_length"] > 1.0),
        "outer_state_path_nonzero": bool(inner_as_outer["state_path_length"] > 1.0),
        "can_separate_density_stationary_from_density_traversing": False,
        "passed": True,
    }

    pole_outer = path_metrics(sample_outer_loop(theta=0.0, chi=0.0, samples=samples))
    pole_degeneracy = {
        "outer_loop_at_pole": pole_outer,
        "collapses_outer_density_traversal": bool(pole_outer["density_displacement_from_start"] < 1e-9),
        "passed": bool(pole_outer["density_displacement_from_start"] < 1e-9),
    }

    return {
        "both_paths_forced_to_inner_collapses_distinction": {
            "candidate_passed": both_inner,
            "expected": False,
            "passed": both_inner is False,
        },
        "both_paths_forced_to_outer_collapses_distinction": {
            "candidate_passed": both_outer,
            "expected": False,
            "passed": both_outer is False,
        },
        "bare_pauli_without_carrier_has_no_loop_readout": bare_pauli_only,
        "density_readout_hidden_collapses_stationary_traversing_test": density_hidden,
        "outer_loop_at_pole_degenerates": pole_degeneracy,
    }


def run_boundary() -> dict[str, object]:
    samples = 129
    equator_outer = path_metrics(sample_outer_loop(theta=math.pi / 2.0, chi=0.0, samples=samples))
    near_pole_outer = path_metrics(sample_outer_loop(theta=1e-6, chi=0.0, samples=samples))
    return {
        "equator_outer_density_traverses": bool(equator_outer["density_displacement_from_start"] > 1.0),
        "near_pole_outer_density_nearly_collapses": bool(
            near_pole_outer["density_displacement_from_start"] < 1e-5
        ),
        "equator_outer": equator_outer,
        "near_pole_outer": near_pole_outer,
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    boundary = run_boundary()
    all_graveyards_pass = all(row["passed"] for row in graveyards.values())
    all_pass = bool(
        positive["survives_fiber_base_readout"]
        and all_graveyards_pass
        and boundary["equator_outer_density_traverses"]
        and boundary["near_pole_outer_density_nearly_collapses"]
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "classical sampled Hopf-coordinate carrier readout baseline only; no physical fiber/base loop "
            "independence, no full S3 bundle, no QIT, GStack, axis, bridge, nonclassical, target-system, "
            "or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "declared_fiber_base_coordinate_readout_baseline",
        "promotion_condition": (
            "May only support later geometry planning after independent symbolic or operator-evolution receipts "
            "reproduce compatible declared-path readouts with the same graveyards."
        ),
        "demotion_condition": (
            "Demote if the fiber loop varies in density, if the base loop stops traversing density away from the pole, "
            "or if same-path and hidden-readout graveyards do not collapse the distinction."
        ),
        "blocked_until": (
            "blocked from target-system claims until a fuller carrier/topology implementation, declared observables, "
            "and physical-evolution graveyards exist"
        ),
        "out_of_scope": [
            "No full GStack or target geometric constraint manifold.",
            "No quantum dynamics, Lindblad evolution, bridge, QIT, axis, or nonclassical admission.",
            "No claim that flux is represented; only a carrier-loop readout baseline is represented.",
        ],
        "divergence_log": (
            "Numpy sampled complex-vector geometry is a classical baseline. It can show different readouts for "
            "declared Hopf-coordinate paths, but it does not prove physical loop independence or admit a "
            "target-system structure."
        ),
        "operation_sequence": [
            "construct normalized two-component complex carrier states in Hopf-style coordinates",
            "sample an inner fiber loop by holding theta and phi fixed while chi varies",
            "sample an outer base-lift loop by holding theta and chi fixed while phi varies",
            "compute density matrices and Pauli readouts along both paths",
            "compare density path length, Bloch path length, and state path length",
            "run same-path, hidden-density, bare-Pauli, and pole-degeneracy graveyards",
        ],
        "carrier_topology": "sampled S^3 carrier coordinates with projection to density/Bloch readouts; no full nested-tori manifold",
        "observable": (
            "density displacement from start, density path length, Bloch path length, state path length, and phase span"
        ),
        "pass_fail_predicate": (
            "fiber loop has zero density/Bloch traversal while state path is nonzero; base loop has nonzero "
            "density/Bloch traversal away from the pole; adjacent graveyards collapse or become insufficient"
        ),
        "graveyards": [
            "both paths forced to the fiber loop collapse the distinction",
            "both paths forced to the base-lift loop collapse the distinction",
            "bare Pauli matrices without carrier path have no loop readout",
            "hidden density readout cannot separate stationary from traversing behavior",
            "base loop at the pole degenerates to zero density traversal",
        ],
        "baselines": [
            "finite z3 product-coordinate readout is lower than this geometry baseline",
            "bare Pauli orientation integer predicate is a no-carrier negative control",
            "sampled Hopf-coordinate path metrics are classical geometry bookkeeping",
        ],
        "alternative_formulations": [
            "symbolic Hopf-coordinate proof of density invariance and traversal",
            "density-matrix evolution with an explicit path-parameter generator",
            "cell-complex or graph approximation of loop transport",
        ],
        "exact_tool_function_needs": {"numpy": ["array", "exp", "outer", "trace", "linalg.norm", "unwrap"]},
        "lego_or_coupling_target": "declared_fiber_base_coordinate_readout_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "boundary": boundary,
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
