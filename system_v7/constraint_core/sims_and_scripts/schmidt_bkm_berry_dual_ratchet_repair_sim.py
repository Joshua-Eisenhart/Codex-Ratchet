#!/usr/bin/env python3
"""Bounded repair of the external Schmidt/BKM/Berry manifold claims.

This scratch diagnostic keeps only the finite mathematics that can be
recomputed on a two-qubit Schmidt family,

    |Psi(eta, phi)> = cos(eta) exp(i phi) |00> + sin(eta) |11>.

It tests three connected but distinct objects:

* the reduced-state radius/entropy family;
* the BKM metric obtained as the Hessian of Umegaki relative entropy; and
* the Berry connection on the phase-carrying global pure-state family.

The separation matters.  The reduced state forgets phi, so Berry holonomy is
not a function of the marginal radius alone.  In the natural Schmidt
coordinate the BKM line element is constant, so finite-difference spacing in
the radius coordinate is not evidence of intrinsic curvature.  Finally, the
Berry rectangle gives -pi (r_i-r_j) for the orientation used here, not the
external packet's asserted +2 pi (r_i-r_j) normalization.

Classification: scratch diagnostic.  Passing gates support only these finite
identities and controls.  They do not establish nested tori, a global bundle,
Chern quantization, a manifold spine, terrain forcing, Axis0, engine
admission, or physics.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any

import sympy as sp
import torch


HERE = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = SOURCE_PATH.with_name(f"{SOURCE_PATH.stem}_results.json")

SIM_ID = "schmidt_bkm_berry_dual_ratchet_repair_sim"
classification = "scratch_diagnostic"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
promotion_allowed = False
formal_admission_allowed = False

CLAIM_CEILING = (
    "Scratch diagnostic only: finite two-qubit Schmidt marginal, BKM/Umegaki "
    "Hessian, CPTP contraction, nonpositive-map control, and Berry-connection "
    "identities. No nested-torus, manifold-spine, terrain, Axis0, engine, "
    "admission, or physics claim."
)

BLOCKED_CONSUMERS = [
    "nested_tori",
    "manifold_spine",
    "global_bundle",
    "chern_quantization",
    "terrain_forcing",
    "Axis0",
    "engine_admission",
    "formal_admission",
    "physics",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex128 Schmidt states and partial traces, "
            "torch.func.hessian Umegaki metric, torch.linalg.eigh BKM metric, "
            "CPTP/nonpositive controls, and discrete Berry transport"
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing exact derivation of g_eta_eta=4, Berry curvature, "
            "rectangle flux, and the -1/2 normalization ratio"
        ),
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive hashing, timestamps, paths, runtime metadata, and JSON serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "python_stdlib": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-10
HESSIAN_TOL = 2.0e-9
TRANSPORT_TOL = 2.0e-6


def scalar(value: float) -> torch.Tensor:
    return torch.tensor(value, dtype=DTYPE)


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(row) for key, row in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(row) for row in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return jsonable(value.detach().cpu().item())
        return jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, sp.Basic):
        return str(value)
    return value


def schmidt_state(eta: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    phase = torch.exp(1j * phi.to(CDTYPE))
    zero = torch.zeros((), dtype=CDTYPE)
    return torch.stack(
        [
            torch.cos(eta).to(CDTYPE) * phase,
            zero,
            zero,
            torch.sin(eta).to(CDTYPE),
        ]
    )


def density(state: torch.Tensor) -> torch.Tensor:
    return state[:, None] @ torch.conj(state[None, :])


def marginal_a(state: torch.Tensor) -> torch.Tensor:
    coefficient_matrix = state.reshape(2, 2)
    return coefficient_matrix @ torch.conj(coefficient_matrix).T


def schmidt_probabilities(eta: torch.Tensor) -> torch.Tensor:
    return torch.stack([torch.cos(eta) ** 2, torch.sin(eta) ** 2])


def marginal_tangent_eta(eta: torch.Tensor) -> torch.Tensor:
    tangent = torch.sin(2.0 * eta)
    return torch.diag(torch.stack([-tangent, tangent])).to(CDTYPE)


def entropy_from_probabilities(probabilities: torch.Tensor) -> torch.Tensor:
    positive = probabilities[probabilities > 0.0]
    return -torch.sum(positive * torch.log(positive))


def relative_entropy_diagonal(candidate: torch.Tensor, reference: torch.Tensor) -> torch.Tensor:
    return torch.sum(candidate * (torch.log(candidate) - torch.log(reference)))


def umegaki_hessian_at_eta(eta_value: float) -> float:
    eta = scalar(eta_value)
    reference = schmidt_probabilities(eta)

    def shifted_relative_entropy(delta: torch.Tensor) -> torch.Tensor:
        candidate = schmidt_probabilities(eta + delta)
        return relative_entropy_diagonal(candidate, reference)

    hessian = torch.func.hessian(shifted_relative_entropy)(scalar(0.0))
    return float(hessian.item())


def bkm_metric(rho: torch.Tensor, tangent: torch.Tensor) -> float:
    """Finite full-rank BKM metric in the eigenbasis of rho."""
    eigenvalues, eigenvectors = torch.linalg.eigh(0.5 * (rho + torch.conj(rho).T))
    if float(torch.min(eigenvalues).item()) <= 0.0:
        raise ValueError("BKM metric requires a full-rank density matrix")
    tangent_eigenbasis = torch.conj(eigenvectors).T @ tangent @ eigenvectors
    total = torch.zeros((), dtype=DTYPE)
    for i in range(eigenvalues.numel()):
        for j in range(eigenvalues.numel()):
            left = eigenvalues[i]
            right = eigenvalues[j]
            if abs(float((left - right).item())) <= 1.0e-12:
                coefficient = 1.0 / left
            else:
                coefficient = (torch.log(left) - torch.log(right)) / (left - right)
            total = total + coefficient * torch.abs(tangent_eigenbasis[i, j]) ** 2
    return float(torch.real(total).item())


def marginal_radius_entropy_gate() -> dict[str, Any]:
    eta_values = [0.12, 0.25, 0.40, 0.60, math.pi / 4.0]
    rows = []
    for eta_value in eta_values:
        eta = scalar(eta_value)
        state = schmidt_state(eta, scalar(0.37))
        rho_a = marginal_a(state)
        probabilities = torch.real(torch.diag(rho_a))
        expected = schmidt_probabilities(eta)
        expected_rho = torch.diag(expected).to(CDTYPE)
        radius = abs(float((probabilities[0] - probabilities[1]).item()))
        expected_radius = abs(math.cos(2.0 * eta_value))
        entropy = float(entropy_from_probabilities(probabilities).item())
        rows.append(
            {
                "eta": eta_value,
                "probabilities": probabilities,
                "partial_trace_max_abs_error": float(torch.max(torch.abs(rho_a - expected_rho)).item()),
                "radius": radius,
                "expected_abs_cos_2eta": expected_radius,
                "entropy_nats": entropy,
            }
        )
    radius_strictly_decreases = all(rows[i + 1]["radius"] < rows[i]["radius"] for i in range(len(rows) - 1))
    entropy_strictly_increases = all(
        rows[i + 1]["entropy_nats"] > rows[i]["entropy_nats"] for i in range(len(rows) - 1)
    )
    max_trace_error = max(row["partial_trace_max_abs_error"] for row in rows)
    max_radius_error = max(abs(row["radius"] - row["expected_abs_cos_2eta"]) for row in rows)
    passed = bool(
        radius_strictly_decreases
        and entropy_strictly_increases
        and max_trace_error <= TOL
        and max_radius_error <= TOL
    )
    return {
        "domain": "0 < eta <= pi/4",
        "rows": rows,
        "radius_strictly_decreases": radius_strictly_decreases,
        "entropy_strictly_increases": entropy_strictly_increases,
        "max_partial_trace_error": max_trace_error,
        "max_radius_identity_error": max_radius_error,
        "pass": passed,
        "tool_calls": ["torch complex128 state construction", "torch partial trace", "torch entropy"],
    }


def exact_symbolic_gate() -> dict[str, Any]:
    eta, eta_i, eta_j = sp.symbols("eta eta_i eta_j", real=True)
    p0 = sp.cos(eta) ** 2
    p1 = sp.sin(eta) ** 2
    radius = sp.cos(2 * eta)
    radius_derivative = sp.trigsimp(sp.diff(radius, eta))
    entropy = -p0 * sp.log(p0) - p1 * sp.log(p1)
    entropy_derivative = sp.trigsimp(sp.expand_log(sp.diff(entropy, eta), force=True))
    expected_entropy_derivative = 2 * (sp.log(sp.cos(eta)) - sp.log(sp.sin(eta))) * sp.sin(2 * eta)
    g_eta = sp.trigsimp(sp.diff(p0, eta) ** 2 / p0 + sp.diff(p1, eta) ** 2 / p1)
    berry_connection_phi = -sp.cos(eta) ** 2
    berry_curvature_eta_phi = sp.trigsimp(sp.diff(berry_connection_phi, eta))
    delta_r = sp.cos(2 * eta_i) - sp.cos(2 * eta_j)
    oriented_surface_flux = sp.trigsimp(
        2 * sp.pi * sp.integrate(berry_curvature_eta_phi, (eta, eta_i, eta_j))
    )
    oriented_rectangle_holonomy = -oriented_surface_flux
    external_l5_flux = 2 * sp.pi * delta_r
    normalization_ratio = sp.trigsimp(oriented_rectangle_holonomy / external_l5_flux)
    transformed_radius_metric = 1 / (1 - sp.symbols("r", real=True) ** 2)
    passed = bool(
        radius_derivative == -2 * sp.sin(2 * eta)
        and sp.trigsimp(sp.expand_log(entropy_derivative - expected_entropy_derivative, force=True)) == 0
        and g_eta == 4
        and berry_curvature_eta_phi == sp.sin(2 * eta)
        and sp.trigsimp(oriented_surface_flux - sp.pi * delta_r) == 0
        and normalization_ratio == -sp.Rational(1, 2)
    )
    return {
        "domain": "0 < eta < pi/4",
        "signed_radius": radius,
        "signed_radius_derivative": radius_derivative,
        "signed_radius_derivative_sign_on_domain": "negative because sin(2*eta)>0",
        "entropy_nats": entropy,
        "entropy_derivative": entropy_derivative,
        "entropy_derivative_sign_on_domain": (
            "positive because sin(2*eta)>0 and log(cos(eta))-log(sin(eta))>0"
        ),
        "bkm_metric_eta_eta": g_eta,
        "bkm_metric_radius_radius": transformed_radius_metric,
        "berry_connection_A_phi": berry_connection_phi,
        "berry_curvature_F_eta_phi": berry_curvature_eta_phi,
        "surface_flux_orientation_deta_wedge_dphi": oriented_surface_flux,
        "rectangle_holonomy_orientation_phi_plus_eta_plus_phi_minus_eta_minus": oriented_rectangle_holonomy,
        "delta_signed_radius": delta_r,
        "external_L5_asserted_flux": external_l5_flux,
        "rectangle_to_external_L5_ratio": normalization_ratio,
        "interpretation": (
            "The BKM line element is flat in eta but coordinate-dependent in r. "
            "The Berry rectangle is -pi*delta_r for the declared path orientation; "
            "it does not derive the external +2*pi*delta_r normalization."
        ),
        "pass": passed,
        "tool_calls": ["sympy.diff", "sympy.integrate", "sympy.trigsimp"],
    }


def bkm_hessian_and_coordinate_gate() -> dict[str, Any]:
    eta_values = [0.15, 0.27, 0.41, 0.59, math.pi / 4.0]
    rows = []
    for eta_value in eta_values:
        eta = scalar(eta_value)
        probabilities = schmidt_probabilities(eta)
        rho = torch.diag(probabilities).to(CDTYPE)
        tangent = marginal_tangent_eta(eta)
        hessian = umegaki_hessian_at_eta(eta_value)
        spectral_metric = bkm_metric(rho, tangent)
        radius = math.cos(2.0 * eta_value)
        radius_metric = 1.0 / (1.0 - radius * radius)
        dr_deta = -2.0 * math.sin(2.0 * eta_value)
        pulled_back_metric = radius_metric * dr_deta * dr_deta
        rows.append(
            {
                "eta": eta_value,
                "signed_radius": radius,
                "torch_func_hessian_D_rho_eta_plus_delta_parallel_rho_eta": hessian,
                "spectral_bkm_metric": spectral_metric,
                "radius_coordinate_metric": radius_metric,
                "radius_metric_pulled_back_to_eta": pulled_back_metric,
            }
        )
    max_hessian_error = max(abs(row["torch_func_hessian_D_rho_eta_plus_delta_parallel_rho_eta"] - 4.0) for row in rows)
    max_spectral_error = max(abs(row["spectral_bkm_metric"] - 4.0) for row in rows)
    max_pullback_error = max(abs(row["radius_metric_pulled_back_to_eta"] - 4.0) for row in rows)
    passed = bool(
        max_hessian_error <= HESSIAN_TOL
        and max_spectral_error <= HESSIAN_TOL
        and max_pullback_error <= HESSIAN_TOL
    )
    return {
        "rows": rows,
        "max_hessian_error_from_4": max_hessian_error,
        "max_spectral_bkm_error_from_4": max_spectral_error,
        "max_coordinate_pullback_error_from_4": max_pullback_error,
        "one_dimensional_curvature_claim": "rejected; the metric is exactly constant in eta",
        "pass": passed,
        "tool_calls": ["torch.func.hessian", "torch.linalg.eigh"],
    }


def channel_controls_gate() -> dict[str, Any]:
    depolarizing_strength = 0.35
    depolarizing_rows = []
    identity = torch.eye(2, dtype=CDTYPE)
    for eta_value in [0.20, 0.40, 0.60]:
        eta = scalar(eta_value)
        rho = torch.diag(schmidt_probabilities(eta)).to(CDTYPE)
        tangent = marginal_tangent_eta(eta)
        before = bkm_metric(rho, tangent)
        rho_after = (1.0 - depolarizing_strength) * rho + depolarizing_strength * identity / 2.0
        tangent_after = (1.0 - depolarizing_strength) * tangent
        after = bkm_metric(rho_after, tangent_after)
        depolarizing_rows.append(
            {
                "eta": eta_value,
                "before": before,
                "after": after,
                "ratio": after / before,
                "contracts": after < before - 1.0e-10,
            }
        )

    theta = scalar(0.37)
    unitary = torch.stack(
        [
            torch.stack([torch.cos(theta), -torch.sin(theta)]),
            torch.stack([torch.sin(theta), torch.cos(theta)]),
        ]
    ).to(CDTYPE)
    eta = scalar(0.43)
    rho = torch.diag(schmidt_probabilities(eta)).to(CDTYPE)
    tangent = marginal_tangent_eta(eta)
    unitary_before = bkm_metric(rho, tangent)
    unitary_after = bkm_metric(unitary @ rho @ torch.conj(unitary).T, unitary @ tangent @ torch.conj(unitary).T)

    amplifier = 1.25
    eta_amplifier = scalar(0.65)
    rho_amplifier = torch.diag(schmidt_probabilities(eta_amplifier)).to(CDTYPE)
    tangent_amplifier = marginal_tangent_eta(eta_amplifier)
    amplified_rho = identity / 2.0 + amplifier * (rho_amplifier - identity / 2.0)
    amplified_tangent = amplifier * tangent_amplifier
    amplifier_before = bkm_metric(rho_amplifier, tangent_amplifier)
    amplifier_after = bkm_metric(amplified_rho, amplified_tangent)
    pure_state = torch.diag(torch.tensor([1.0, 0.0], dtype=DTYPE)).to(CDTYPE)
    amplified_pure_state = identity / 2.0 + amplifier * (pure_state - identity / 2.0)
    amplified_pure_min_eigenvalue = float(torch.min(torch.linalg.eigvalsh(amplified_pure_state)).item())

    depolarizing_pass = all(row["contracts"] for row in depolarizing_rows)
    unitary_pass = abs(unitary_after - unitary_before) <= 1.0e-10
    amplifier_control_pass = bool(
        float(torch.min(torch.linalg.eigvalsh(amplified_rho)).item()) > 0.0
        and amplifier_after > amplifier_before + 1.0e-10
        and amplified_pure_min_eigenvalue < 0.0
    )
    return {
        "cptp_depolarizing": {
            "strength": depolarizing_strength,
            "rows": depolarizing_rows,
            "all_contract": depolarizing_pass,
        },
        "unitary_isometry": {
            "before": unitary_before,
            "after": unitary_after,
            "absolute_difference": abs(unitary_after - unitary_before),
            "pass": unitary_pass,
        },
        "nonpositive_amplifier_control": {
            "amplifier": amplifier,
            "interior_state_remains_full_rank": bool(
                float(torch.min(torch.linalg.eigvalsh(amplified_rho)).item()) > 0.0
            ),
            "metric_before": amplifier_before,
            "metric_after": amplifier_after,
            "metric_increases": amplifier_after > amplifier_before + 1.0e-10,
            "pure_state_output_min_eigenvalue": amplified_pure_min_eigenvalue,
            "map_is_not_positive_on_full_state_space": amplified_pure_min_eigenvalue < 0.0,
            "pass": amplifier_control_pass,
        },
        "pass": bool(depolarizing_pass and unitary_pass and amplifier_control_pass),
        "tool_calls": ["torch.linalg.eigh", "torch complex128 channel pushforwards"],
    }


def berry_loop(eta_value: float, sample_count: int = 4096) -> float:
    eta = scalar(eta_value)
    total = torch.zeros((), dtype=DTYPE)
    states = [
        schmidt_state(eta, scalar(2.0 * math.pi * index / sample_count))
        for index in range(sample_count)
    ]
    for index, state in enumerate(states):
        next_state = states[(index + 1) % sample_count]
        total = total - torch.angle(torch.vdot(state, next_state))
    return float(total.item())


def berry_phase_family_gate() -> dict[str, Any]:
    eta_values = [math.pi / 8.0, math.pi / 6.0, math.pi / 4.0]
    loop_rows = []
    for eta_value in eta_values:
        observed = berry_loop(eta_value)
        analytic = -2.0 * math.pi * math.cos(eta_value) ** 2
        loop_rows.append(
            {
                "eta": eta_value,
                "discrete_holonomy": observed,
                "analytic_holonomy": analytic,
                "absolute_error": abs(observed - analytic),
            }
        )

    eta_i = math.pi / 8.0
    eta_j = math.pi / 6.0
    radius_delta = math.cos(2.0 * eta_i) - math.cos(2.0 * eta_j)
    rectangle_holonomy = berry_loop(eta_i) - berry_loop(eta_j)
    analytic_rectangle = -math.pi * radius_delta
    external_l5_assertion = 2.0 * math.pi * radius_delta
    observed_ratio = rectangle_holonomy / external_l5_assertion

    eta = scalar(0.41)
    state_phi_a = schmidt_state(eta, scalar(0.20))
    state_phi_b = schmidt_state(eta, scalar(1.40))
    marginal_phase_distance = float(
        torch.linalg.vector_norm(marginal_a(state_phi_a) - marginal_a(state_phi_b)).item()
    )
    global_density_phase_distance = float(
        torch.linalg.vector_norm(density(state_phi_a) - density(state_phi_b)).item()
    )

    max_loop_error = max(row["absolute_error"] for row in loop_rows)
    rectangle_error = abs(rectangle_holonomy - analytic_rectangle)
    transport_pass = bool(max_loop_error <= TRANSPORT_TOL and rectangle_error <= TRANSPORT_TOL)
    phase_location_pass = bool(marginal_phase_distance <= TOL and global_density_phase_distance > 1.0e-3)
    normalization_rejected = bool(abs(observed_ratio + 0.5) <= 2.0e-6)
    return {
        "global_state_family": "cos(eta) exp(i phi)|00> + sin(eta)|11>",
        "loop_rows": loop_rows,
        "max_loop_error": max_loop_error,
        "rectangle": {
            "path_orientation": "phi+, eta+, phi-, eta-",
            "eta_i": eta_i,
            "eta_j": eta_j,
            "signed_radius_delta": radius_delta,
            "discrete_holonomy": rectangle_holonomy,
            "analytic_minus_pi_delta_r": analytic_rectangle,
            "absolute_error": rectangle_error,
            "external_L5_plus_2pi_delta_r": external_l5_assertion,
            "observed_to_external_ratio": observed_ratio,
            "external_normalization_rejected": normalization_rejected,
        },
        "phase_location_control": {
            "marginal_distance_across_phi": marginal_phase_distance,
            "global_density_distance_across_phi": global_density_phase_distance,
            "marginal_erases_phi_while_global_state_retains_it": phase_location_pass,
        },
        "single_loop_pure_gauge_claim": (
            "rejected; closed-loop Berry phase is gauge invariant modulo 2*pi, "
            "although a chosen connection potential is gauge dependent"
        ),
        "pass": bool(transport_pass and phase_location_pass and normalization_rejected),
        "tool_calls": ["torch.vdot", "torch.angle", "torch partial trace"],
    }


def boundary_gate() -> dict[str, Any]:
    pure_eta = scalar(0.0)
    mixed_eta = scalar(math.pi / 4.0)
    pure_rho = torch.diag(schmidt_probabilities(pure_eta)).to(CDTYPE)
    mixed_rho = torch.diag(schmidt_probabilities(mixed_eta)).to(CDTYPE)
    pure_min_eigenvalue = float(torch.min(torch.linalg.eigvalsh(pure_rho)).item())
    mixed_min_eigenvalue = float(torch.min(torch.linalg.eigvalsh(mixed_rho)).item())
    pure_bkm_rejected = False
    try:
        bkm_metric(pure_rho, marginal_tangent_eta(pure_eta))
    except ValueError:
        pure_bkm_rejected = True
    mixed_metric = bkm_metric(mixed_rho, marginal_tangent_eta(mixed_eta))
    passed = bool(
        pure_min_eigenvalue == 0.0
        and pure_bkm_rejected
        and abs(mixed_min_eigenvalue - 0.5) <= TOL
        and abs(mixed_metric - 4.0) <= HESSIAN_TOL
    )
    return {
        "eta_zero_pure_marginal": {
            "min_eigenvalue": pure_min_eigenvalue,
            "finite_full_rank_BKM_rejected": pure_bkm_rejected,
            "note": "The eta-coordinate metric has an interior limit, but the matrix BKM formula is support-singular at the pure boundary.",
        },
        "eta_pi_over_4_maximally_mixed_marginal": {
            "min_eigenvalue": mixed_min_eigenvalue,
            "BKM_metric_eta_eta": mixed_metric,
        },
        "pass": passed,
    }


def main() -> dict[str, Any]:
    gates = {
        "marginal_radius_entropy": marginal_radius_entropy_gate(),
        "exact_symbolic_identities": exact_symbolic_gate(),
        "bkm_hessian_and_coordinate_flatness": bkm_hessian_and_coordinate_gate(),
        "channel_controls": channel_controls_gate(),
        "berry_phase_family": berry_phase_family_gate(),
        "support_boundaries": boundary_gate(),
    }
    all_pass = all(bool(gate["pass"]) for gate in gates.values())
    source_sha256 = hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()
    result = {
        "schema": "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "claim_ceiling": CLAIM_CEILING,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "source": {
            "path": str(SOURCE_PATH),
            "sha256": source_sha256,
        },
        "runtime": {
            "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "python": platform.python_version(),
            "pytorch": torch.__version__,
            "sympy": sp.__version__,
            "command": f"{platform.python_implementation()} {SOURCE_PATH}",
            "deterministic": True,
            "random_seed": None,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "gates": gates,
        "external_claim_disposition": {
            "finite_schmidt_radius_entropy_family": "survives with explicit domain",
            "BKM_hessian_identity": "survives on full-rank two-level marginals",
            "one_dimensional_intrinsic_curvature": "rejected by constant eta-coordinate metric",
            "CPTP_metric_contraction": "survives for the tested depolarizing family",
            "Berry_curvature_on_global_phase_family": "survives as a bounded two-parameter calculation",
            "external_L5_flux_normalization": "rejected; signed ratio is -1/2 for the declared orientation",
            "single_shell_holonomy_is_pure_gauge": "rejected",
            "nested_tori_or_manifold_spine": "not tested",
        },
        "allowed_claims": [
            "The two-qubit Schmidt marginal has radius |cos(2 eta)| and entropy increasing toward eta=pi/4.",
            "For full-rank interior marginals, the Umegaki Hessian and spectral BKM metric both give g_eta_eta=4.",
            "The tested depolarizing CPTP map contracts the BKM metric and a unitary change of basis preserves it.",
            "A nonpositive Bloch amplifier increases the metric on a valid interior witness and fails positivity on a pure-state control.",
            "The global Schmidt phase family has Berry curvature sin(2 eta), while its one-qubit marginal erases phi.",
            "For the declared rectangle orientation, Berry holonomy is -pi delta_r, not the packet's +2 pi delta_r.",
        ],
        "verdict": "PASS_BOUNDED_REPAIR" if all_pass else "FAIL_BOUNDED_REPAIR",
        "all_gates_pass": bool(all_pass),
    }
    RESULT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "sim_id": SIM_ID,
                "verdict": result["verdict"],
                "all_gates_pass": all_pass,
                "result_path": str(RESULT_PATH),
                "source_sha256": source_sha256,
                "external_L5_flux_status": result["external_claim_disposition"]["external_L5_flux_normalization"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not all_pass:
        raise SystemExit(1)
    return result


if __name__ == "__main__":
    main()
