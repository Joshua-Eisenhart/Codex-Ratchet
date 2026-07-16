#!/usr/bin/env python3
"""Adversarial audit of the installed L5--L8 entropic geometry.

This instrument does not promote a manifold layer.  It asks which mathematical
identities really survive on the supplied two-qubit Schmidt family, which
named presentations are only aliases there, and exactly where the claimed
entropy/geometry identity stops carrying the phase geometry.

No target formula is used as a fitted predictor.  Every equality below is an
analytic identity checked numerically on a finite grid, and every conclusion
is restricted to that grid and the installed quantum-information family.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT = HERE / "entropic_geometry_audit_results.json"


def binary_entropy_nats_from_r(r: float) -> float:
    p = 0.5 * (1.0 + r)
    q = 1.0 - p
    terms = [-(x * math.log(x)) for x in (p, q) if x > 0.0]
    return float(sum(terms))


def invert_entropy_nats(value: float, iterations: int = 90) -> float:
    """Invert H_2((1+r)/2) on the monotone branch r in [0, 1]."""
    lo, hi = 0.0, 1.0
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        # Entropy decreases as r increases.
        if binary_entropy_nats_from_r(mid) > value:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def mc_bkm(x: float, y: float) -> float:
    if abs(x - y) < 1e-13:
        return 1.0 / x
    return (math.log(x) - math.log(y)) / (x - y)


def mc_sld(x: float, y: float) -> float:
    return 2.0 / (x + y)


def mc_wigner_yanase(x: float, y: float) -> float:
    return 4.0 / (math.sqrt(x) + math.sqrt(y)) ** 2


def mc_rld(x: float, y: float) -> float:
    return (x + y) / (2.0 * x * y)


METRICS: dict[str, Callable[[float, float], float]] = {
    "BKM": mc_bkm,
    "SLD_Bures": mc_sld,
    "Wigner_Yanase": mc_wigner_yanase,
    "RLD_maximal": mc_rld,
}


def monotone_metric_diagonal(
    eigenvalues: np.ndarray,
    tangent: np.ndarray,
    coefficient: Callable[[float, float], float],
) -> float:
    total = 0.0
    for i, left in enumerate(eigenvalues):
        for j, right in enumerate(eigenvalues):
            total += coefficient(float(left), float(right)) * abs(tangent[i, j]) ** 2
    return float(total)


def psi(eta: float, phi: float) -> np.ndarray:
    return np.array([math.cos(eta) * np.exp(1j * phi), math.sin(eta)], dtype=complex)


def dpsi_eta(eta: float, phi: float) -> np.ndarray:
    return np.array([-math.sin(eta) * np.exp(1j * phi), math.cos(eta)], dtype=complex)


def dpsi_phi(eta: float, phi: float) -> np.ndarray:
    return np.array([1j * math.cos(eta) * np.exp(1j * phi), 0.0], dtype=complex)


def qgt_component(state: np.ndarray, left: np.ndarray, right: np.ndarray) -> complex:
    return np.vdot(left, right) - np.vdot(left, state) * np.vdot(state, right)


def link(left: np.ndarray, right: np.ndarray) -> complex:
    overlap = np.vdot(left, right)
    return overlap / abs(overlap) if abs(overlap) > 1e-14 else 1.0 + 0.0j


def lattice_chern(section: Callable[[float, float], np.ndarray], orient: int, ne: int = 60, np_: int = 60) -> float:
    etas = np.linspace(1e-3, math.pi / 2.0 - 1e-3, ne)
    phis = np.linspace(0.0, 2.0 * math.pi, np_, endpoint=False)
    flux = 0.0
    for i in range(ne - 1):
        for j in range(np_):
            jp = (j + 1) % np_
            a, b = ((j, jp) if orient > 0 else (jp, j))
            p00 = section(float(etas[i]), float(phis[a]))
            p10 = section(float(etas[i]), float(phis[b]))
            p11 = section(float(etas[i + 1]), float(phis[b]))
            p01 = section(float(etas[i + 1]), float(phis[a]))
            plaquette = link(p00, p10) * link(p10, p11) * link(p11, p01) * link(p01, p00)
            flux += float(np.angle(plaquette))
    return flux / (2.0 * math.pi)


def main() -> int:
    # L5: every installed scalar readout is invertible to the same Schmidt radius.
    radii = np.linspace(0.0, 1.0, 257)
    purity = 0.5 * (1.0 + radii**2)
    negativity = 0.5 * np.sqrt(np.maximum(0.0, 1.0 - radii**2))
    entropy = np.array([binary_entropy_nats_from_r(float(r)) for r in radii])
    inv_purity = np.sqrt(np.maximum(0.0, 2.0 * purity - 1.0))
    inv_negativity = np.sqrt(np.maximum(0.0, 1.0 - 4.0 * negativity**2))
    inv_entropy = np.array([invert_entropy_nats(float(s)) for s in entropy])
    l5_inverse_errors = {
        "purity_to_radius": float(np.max(np.abs(inv_purity - radii))),
        "negativity_to_radius": float(np.max(np.abs(inv_negativity - radii))),
        "entropy_to_radius": float(np.max(np.abs(inv_entropy - radii))),
    }
    l5_alias_equivalence = max(l5_inverse_errors.values()) < 1e-10

    # The authored product->Bell direction has a live entropy slope in the open interval.
    etas = np.linspace(1e-3, math.pi / 4.0 - 1e-3, 257)
    entropy_slopes = np.sin(2.0 * etas) * np.log((np.cos(etas) ** 2) / (np.sin(etas) ** 2))
    authored_path_gradient_positive = bool(np.all(entropy_slopes > 0.0))

    # L6: normalized Petz monotone metrics coincide on commuting radial tangents.
    radial_diffs: dict[str, float] = {name: 0.0 for name in METRICS if name != "BKM"}
    transverse_values: dict[str, list[float]] = {name: [] for name in METRICS}
    bkm_eta_values: list[float] = []
    for r in np.linspace(0.05, 0.95, 37):
        lam = np.array([0.5 * (1.0 + r), 0.5 * (1.0 - r)])
        radial = np.diag([0.5, -0.5]).astype(complex)  # d rho / d r
        transverse = np.array([[0.0, 0.5], [0.5, 0.0]], dtype=complex)
        values = {
            name: monotone_metric_diagonal(lam, radial, coefficient)
            for name, coefficient in METRICS.items()
        }
        expected = 1.0 / (1.0 - r * r)
        if abs(values["BKM"] - expected) > 1e-11:
            raise AssertionError("BKM radial formula disagrees with 1/(1-r^2)")
        for name in radial_diffs:
            radial_diffs[name] = max(radial_diffs[name], abs(values[name] - values["BKM"]))
        for name, coefficient in METRICS.items():
            transverse_values[name].append(monotone_metric_diagonal(lam, transverse, coefficient))
        eta = 0.5 * math.acos(float(r))
        dr_deta = -2.0 * math.sin(2.0 * eta)
        bkm_eta_values.append(values["BKM"] * dr_deta * dr_deta)
    radial_metric_alias = max(radial_diffs.values()) < 1e-11
    transverse_spread = max(
        max(values) - min(values)
        for values in zip(*(transverse_values[name] for name in METRICS))
    )
    transverse_metrics_distinguishable = transverse_spread > 1e-3
    bkm_eta_constant = max(abs(value - 4.0) for value in bkm_eta_values) < 1e-10

    # L6->L7 bridge: radial metric agrees, phase direction does not descend to the marginal.
    bridge_rows = []
    max_eta_qfi_error = 0.0
    max_phi_qfi_error = 0.0
    max_curvature_error = 0.0
    for eta in np.linspace(0.08, math.pi / 4.0 - 0.08, 19):
        phi = 0.37
        state = psi(float(eta), phi)
        de = dpsi_eta(float(eta), phi)
        dp = dpsi_phi(float(eta), phi)
        q_eta_eta = qgt_component(state, de, de)
        q_phi_phi = qgt_component(state, dp, dp)
        q_eta_phi = qgt_component(state, de, dp)
        qfi_eta = 4.0 * float(np.real(q_eta_eta))
        qfi_phi = 4.0 * float(np.real(q_phi_phi))
        berry_curvature = -2.0 * float(np.imag(q_eta_phi))
        expected_qfi_phi = math.sin(2.0 * eta) ** 2
        expected_curvature = math.sin(2.0 * eta)
        max_eta_qfi_error = max(max_eta_qfi_error, abs(qfi_eta - 4.0))
        max_phi_qfi_error = max(max_phi_qfi_error, abs(qfi_phi - expected_qfi_phi))
        max_curvature_error = max(max_curvature_error, abs(abs(berry_curvature) - expected_curvature))
        bridge_rows.append(
            {
                "eta": float(eta),
                "marginal_bkm_eta_eta": 4.0,
                "marginal_bkm_phi_phi": 0.0,
                "global_qfi_eta_eta": qfi_eta,
                "global_qfi_phi_phi": qfi_phi,
                "berry_curvature_eta_phi": berry_curvature,
            }
        )
    radial_bridge_agrees = max_eta_qfi_error < 1e-11
    phase_bridge_obstruction = all(row["global_qfi_phi_phi"] > 0.0 for row in bridge_rows)

    # L8: execute the trivial-section control instead of hardcoding zero.
    nontrivial = lambda eta, phi: psi(eta, phi)
    constant_state = np.array([1.0, 0.0], dtype=complex)
    trivial = lambda eta, phi: constant_state
    chern_plus = lattice_chern(nontrivial, +1)
    chern_minus = lattice_chern(nontrivial, -1)
    chern_trivial = lattice_chern(trivial, +1)
    l8_control_executed = abs(chern_trivial) < 1e-12
    l8_orientation_flip = abs(chern_plus + chern_minus) < 1e-10 and chern_plus * chern_minus < 0.0

    # Directly inspect known source-level anti-evidence rather than trusting verdict prose.
    l3_source = (ROOT / "sims_and_scripts" / "manifold_L3_spinor_hopf_sim.py").read_text(encoding="utf-8")
    l6_source = (ROOT / "sims_and_scripts" / "manifold_L6_shell_metric_bkm_connection_sim.py").read_text(encoding="utf-8")
    l8_source = (ROOT / "sims_and_scripts" / "manifold_L8_global_bundle_chern_quantization_sim.py").read_text(encoding="utf-8")
    source_audit = {
        "L3_contains_and_True_control": "and True" in l3_source,
        "L6_stale_curvature_claim_in_scope_or_output": "metric on the shell family + curvature" in l6_source,
        "L8_trivial_control_hardcoded": "c_trivial=0.0" in l8_source,
    }

    result = {
        "schema_version": "entropic-geometry-adversarial-audit/1.0",
        "classification": "executed_formal_fixture_audit",
        "promotion_allowed": False,
        "root": "constrained_distinguishability",
        "L5_operational_equivalence": {
            "relation": {
                "schmidt_spectrum": "lambda_+=(1+r)/2, lambda_-=(1-r)/2",
                "entropy_nats": "H(r)=-sum lambda log(lambda)",
                "purity": "P(r)=(1+r^2)/2",
                "negativity": "N(r)=sqrt(1-r^2)/2",
                "installed_flux": "DeltaPhi=-pi(r_i-r_j)",
            },
            "max_inverse_errors": l5_inverse_errors,
            "all_scalar_presentations_mutually_invertible_on_branch": l5_alias_equivalence,
            "nested_shell_name_adds_no_tested_behavior": l5_alias_equivalence,
            "authored_product_to_Bell_entropy_gradient_positive_interior": authored_path_gradient_positive,
            "drive_caveat": "A slope exists on the authored path, but the fixture supplies no prior unmet obligation that selects this direction; slope alone is not a Ratchet tooth.",
        },
        "L6_metric_family": {
            "radial_formula": "g_rr=1/(1-r^2), g_eta_eta=4 for r=cos(2 eta)",
            "max_radial_differences_from_BKM": radial_diffs,
            "all_normalized_monotone_metrics_alias_on_commuting_radial_tangent": radial_metric_alias,
            "bkm_eta_eta_constant_at_4": bkm_eta_constant,
            "transverse_metric_family_spread": transverse_spread,
            "transverse_direction_distinguishes_metric_families": transverse_metrics_distinguishable,
            "adjudication": "BKM Hessian identity survives, but BKM specificity is not earned by the installed radial shell; SLD/Bures, Wigner-Yanase, and RLD are behaviorally identical there.",
        },
        "L6_to_L7_bridge": {
            "identity": "global QFI_eta_eta = marginal BKM_eta_eta = 4",
            "obstruction": "marginal rho_A is phi-independent, so marginal BKM_phi_phi=0 while global QFI_phi_phi=sin^2(2 eta)>0 and Berry curvature is nonzero",
            "max_qfi_eta_error": max_eta_qfi_error,
            "max_qfi_phi_error": max_phi_qfi_error,
            "max_berry_curvature_abs_error": max_curvature_error,
            "radial_bridge_agrees": radial_bridge_agrees,
            "phase_bridge_obstruction_fires": phase_bridge_obstruction,
            "rows": bridge_rows,
            "adjudication": "The supplied entropy geometry and Berry geometry agree on the radial direction only. The current marginal entropy object cannot carry the phase direction required by L7; the claimed full coidentity is not established.",
        },
        "L8_control_reexecution": {
            "chern_plus": chern_plus,
            "chern_minus": chern_minus,
            "chern_trivial_computed": chern_trivial,
            "trivial_control_pass": l8_control_executed,
            "orientation_flip_pass": l8_orientation_flip,
            "adjudication": "Chern arithmetic for the chosen section survives. Orientation reversal alone does not identify a physical Weyl chirality or engine type; that bridge remains unimplemented.",
        },
        "source_audit": source_audit,
        "earned_from_this_audit": [
            "Within the installed pure two-qubit Schmidt branch, radius, Schmidt spectrum, purity, negativity, entropy, and the stated flux difference are mutually translatable scalar presentations.",
            "All tested normalized monotone quantum metrics coincide on the commuting radial tangent, so the installed shell cannot select BKM uniquely.",
            "The radial BKM/QFI bridge is exact, but the marginal phase direction is zero while global QFI and Berry curvature are nonzero; the full L6-to-L7 entropy-geometry identity is obstructed.",
            "The nontrivial and trivial Chern integrations were both executed; the chosen section has winding and the constant section does not.",
        ],
        "not_earned": [
            "nested-shell geometry as the unique or minimal L5 object",
            "BKM as the uniquely forced L6 metric",
            "L7 Berry phase as already contained in the L6 marginal entropy geometry",
            "Chern orientation sign as physical Weyl chirality or engine type",
            "any scientific manifold layer",
        ],
        "scientific_manifold_layers_admitted": 0,
        "status": "AUDIT_COMPLETE__NEGATIVES_AND_LOCAL_IDENTITIES_EARNED__MANIFOLD_UNADMITTED",
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    assert l5_alias_equivalence
    assert authored_path_gradient_positive
    assert radial_metric_alias and bkm_eta_constant and transverse_metrics_distinguishable
    assert radial_bridge_agrees and phase_bridge_obstruction
    assert l8_control_executed and l8_orientation_flip
    print("PASS entropic_geometry_adversarial_audit")
    print(f"L5 scalar inverse max error: {max(l5_inverse_errors.values()):.3e}")
    print(f"L6 radial metric-family max spread from BKM: {max(radial_diffs.values()):.3e}")
    print(f"L6->L7 phase obstruction: marginal g_phi_phi=0, global QFI_phi_phi>0 ({phase_bridge_obstruction})")
    print(f"L8 computed Chern: {chern_plus:+.6f}, reversed {chern_minus:+.6f}, trivial {chern_trivial:+.6f}")
    print("scientific manifold layers admitted: 0")
    print(f"receipt: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
