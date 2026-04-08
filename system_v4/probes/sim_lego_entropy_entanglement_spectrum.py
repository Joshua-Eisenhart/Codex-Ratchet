#!/usr/bin/env python3
"""
PURE LEGO: Entanglement Entropy and Entanglement Spectrum
=========================================================
Pure-math bipartite entropy lego.

Targets:
  - Entanglement entropy for pure bipartite states
  - Entanglement spectrum from Schmidt eigenvalues
  - Negativity and log-negativity
  - Werner-like threshold checks on two-qubit families

Scope note:
  This sim keeps the entropy formulas exact. It omits smooth entropy
  approximations because the request is about the clean extremal and
  bipartite entanglement relations, and any smooth form would require
  an additional regularization convention that is not needed here.
"""

import json
import os
import time

import numpy as np

np.random.seed(42)
EPS = 1e-12

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this lego"},
}


# =====================================================================
# BASIC HELPERS
# =====================================================================

def normalize_rho(rho):
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho)
    return rho / tr


def partial_trace_A(rho):
    """Trace out subsystem A from a 2x2 bipartite state."""
    return np.array(
        [
            [rho[0, 0] + rho[2, 2], rho[0, 1] + rho[2, 3]],
            [rho[1, 0] + rho[3, 2], rho[1, 1] + rho[3, 3]],
        ],
        dtype=complex,
    )


def partial_trace_B(rho):
    """Trace out subsystem B from a 2x2 bipartite state."""
    return np.array(
        [
            [rho[0, 0] + rho[1, 1], rho[0, 2] + rho[1, 3]],
            [rho[2, 0] + rho[3, 1], rho[2, 2] + rho[3, 3]],
        ],
        dtype=complex,
    )


def von_neumann_entropy(rho):
    eigs = np.clip(np.linalg.eigvalsh(normalize_rho(rho)), 0.0, None)
    nz = eigs[eigs > EPS]
    return float(-np.sum(nz * np.log2(nz))) if len(nz) else 0.0


def schmidt_spectrum_from_pure_state(psi):
    """Schmidt eigenvalues for a pure 2x2 bipartite state."""
    psi = np.asarray(psi, dtype=complex).reshape(4)
    mat = psi.reshape(2, 2)
    svals = np.linalg.svd(mat, compute_uv=False)
    spec = np.sort(np.real(svals**2))[::-1]
    return [float(x) for x in spec]


def entanglement_entropy_pure(psi):
    spec = schmidt_spectrum_from_pure_state(psi)
    nz = [x for x in spec if x > EPS]
    return float(-np.sum(np.array(nz) * np.log2(np.array(nz)))) if nz else 0.0


def density_from_pure(psi):
    psi = np.asarray(psi, dtype=complex).reshape(4, 1)
    return normalize_rho(psi @ psi.conj().T)


def negativity(rho):
    rho = normalize_rho(rho)
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def log_negativity(rho):
    rho = normalize_rho(rho)
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(np.log2(max(np.sum(np.abs(evals)), 1.0)))


def werner_state(p):
    """Two-qubit Werner state rho_W(p) = p|Psi-><Psi-| + (1-p)I/4."""
    psi_minus = np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)
    bell = np.outer(psi_minus, psi_minus.conj())
    return normalize_rho(p * bell + (1.0 - p) * np.eye(4, dtype=complex) / 4.0)


def werner_negativity_expected(p):
    return max(0.0, (3.0 * p - 1.0) / 4.0)


def werner_log_negativity_expected(p):
    n = werner_negativity_expected(p)
    return float(np.log2(1.0 + 2.0 * n))


def random_unitary_2(rng):
    z = rng.randn(2, 2) + 1j * rng.randn(2, 2)
    q, r = np.linalg.qr(z)
    phases = np.diag(r)
    phases = phases / np.where(np.abs(phases) < EPS, 1.0, np.abs(phases))
    return q * phases.conj()


def product_state_from_angles(theta_a, phi_a, theta_b, phi_b):
    """|a> ⊗ |b> with Bloch-sphere parameterization."""
    a = np.array([np.cos(theta_a / 2), np.exp(1j * phi_a) * np.sin(theta_a / 2)], dtype=complex)
    b = np.array([np.cos(theta_b / 2), np.exp(1j * phi_b) * np.sin(theta_b / 2)], dtype=complex)
    return np.kron(a, b)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    rng = np.random.RandomState(123)
    results = {}
    t0 = time.time()

    pure_specs = {
        "bell_state": np.array([1.0, 0.0, 0.0, 0.0], dtype=complex),
        "product_state": product_state_from_angles(0.3, 0.2, 1.1, 0.7),
        "partially_entangled": (np.array([0.0, 0.0, 0.0, 0.0], dtype=complex)),
    }
    pure_specs["partially_entangled"] = (
        np.cos(0.35) * np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        + np.sin(0.35) * np.array([0.0, 0.0, 0.0, 1.0], dtype=complex)
    )

    pure_results = {}
    pure_pass = True
    for name, psi in pure_specs.items():
        psi = psi / np.linalg.norm(psi)
        rho = density_from_pure(psi)
        spec = schmidt_spectrum_from_pure_state(psi)
        s_ent = entanglement_entropy_pure(psi)
        rho_A = partial_trace_B(rho)
        rho_B = partial_trace_A(rho)
        spec_A = np.sort(np.real(np.linalg.eigvalsh(rho_A)))[::-1]
        spec_B = np.sort(np.real(np.linalg.eigvalsh(rho_B)))[::-1]
        pure_results[name] = {
            "schmidt_spectrum": spec,
            "reduced_spectrum_A": [float(x) for x in spec_A],
            "reduced_spectrum_B": [float(x) for x in spec_B],
            "entanglement_entropy": s_ent,
            "entropy_from_spectrum": float(-np.sum(np.array([x for x in spec if x > EPS]) * np.log2(np.array([x for x in spec if x > EPS]))))
            if any(x > EPS for x in spec)
            else 0.0,
            "spectrum_matches_reduced_A": bool(np.allclose(spec, spec_A, atol=1e-12)),
            "spectrum_matches_reduced_B": bool(np.allclose(spec, spec_B, atol=1e-12)),
            "entropy_matches_spectrum": bool(np.isclose(
                s_ent,
                (-np.sum(np.array([x for x in spec if x > EPS]) * np.log2(np.array([x for x in spec if x > EPS]))))
                if any(x > EPS for x in spec)
                else 0.0,
                atol=1e-12,
            )),
            "negativity": negativity(rho),
            "log_negativity": log_negativity(rho),
        }
        pure_pass = pure_pass and pure_results[name]["spectrum_matches_reduced_A"] and pure_results[name]["spectrum_matches_reduced_B"] and pure_results[name]["entropy_matches_spectrum"]

    results["pure_state_checks"] = pure_results

    invariance_checks = {}
    for name, psi in pure_specs.items():
        psi = psi / np.linalg.norm(psi)
        rho = density_from_pure(psi)
        uA = random_unitary_2(rng)
        uB = random_unitary_2(rng)
        U = np.kron(uA, uB)
        rho_u = U @ rho @ U.conj().T
        psi_u = np.linalg.eigh(rho_u)[1][:, -1]
        invariance_checks[name] = {
            "entropy_invariant": bool(np.isclose(entanglement_entropy_pure(psi), entanglement_entropy_pure(psi_u), atol=1e-8)),
            "spectrum_invariant": bool(np.allclose(sorted(schmidt_spectrum_from_pure_state(psi), reverse=True), sorted(schmidt_spectrum_from_pure_state(psi_u), reverse=True), atol=1e-8)),
        }
        pure_pass = pure_pass and invariance_checks[name]["entropy_invariant"] and invariance_checks[name]["spectrum_invariant"]
    results["local_unitary_invariance"] = invariance_checks

    pure_state = np.array([np.cos(0.4), 0.0, 0.0, np.sin(0.4)], dtype=complex)
    pure_state = pure_state / np.linalg.norm(pure_state)
    prod_state = product_state_from_angles(0.2, 0.0, 1.0, 1.2)
    bell_state = np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)
    mixed_state = werner_state(0.6)

    positive_monotones = {
        "product_state": {
            "entropy": entanglement_entropy_pure(prod_state),
            "negativity": negativity(density_from_pure(prod_state)),
            "log_negativity": log_negativity(density_from_pure(prod_state)),
        },
        "partially_entangled": {
            "entropy": entanglement_entropy_pure(pure_state),
            "negativity": negativity(density_from_pure(pure_state)),
            "log_negativity": log_negativity(density_from_pure(pure_state)),
        },
        "bell_state": {
            "entropy": entanglement_entropy_pure(bell_state),
            "negativity": negativity(density_from_pure(bell_state)),
            "log_negativity": log_negativity(density_from_pure(bell_state)),
        },
        "werner_p06": {
            "entropy_A": von_neumann_entropy(partial_trace_B(mixed_state)),
            "negativity": negativity(mixed_state),
            "log_negativity": log_negativity(mixed_state),
            "werner_threshold": 1.0 / 3.0,
        },
    }

    results["positive_monotones"] = positive_monotones

    werner_grid = np.linspace(0.0, 1.0, 11)
    werner_trace = []
    for p in werner_grid:
        rho = werner_state(float(p))
        n = negativity(rho)
        ln = log_negativity(rho)
        werner_trace.append({
            "p": float(p),
            "negativity": float(n),
            "log_negativity": float(ln),
            "expected_negativity": float(werner_negativity_expected(float(p))),
            "expected_log_negativity": float(werner_log_negativity_expected(float(p))),
        })

    expected_match = all(
        np.isclose(item["negativity"], item["expected_negativity"], atol=1e-12)
        and np.isclose(item["log_negativity"], item["expected_log_negativity"], atol=1e-12)
        for item in werner_trace
    )
    monotone_non_decreasing = all(
        werner_trace[i + 1]["negativity"] >= werner_trace[i]["negativity"] - 1e-12
        for i in range(len(werner_trace) - 1)
    )

    results["werner_trace"] = werner_trace
    results["werner_pass"] = bool(expected_match and monotone_non_decreasing)
    results["pass"] = bool(pure_pass and results["werner_pass"])
    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    product = density_from_pure(product_state_from_angles(0.5, 0.1, 0.9, 0.4))
    bell = density_from_pure(np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex))
    werner_subcritical = werner_state(0.2)
    return {
        "product_state_has_zero_entanglement": {
            "claim": "A product state has nonzero entanglement entropy and negativity",
            "entanglement_entropy": entanglement_entropy_pure(product_state_from_angles(0.5, 0.1, 0.9, 0.4)),
            "negativity": negativity(product),
            "log_negativity": log_negativity(product),
            "claim_holds": bool(
                entanglement_entropy_pure(product_state_from_angles(0.5, 0.1, 0.9, 0.4)) > EPS
                or negativity(product) > EPS
                or log_negativity(product) > EPS
            ),
            "pass": bool(
                entanglement_entropy_pure(product_state_from_angles(0.5, 0.1, 0.9, 0.4)) <= EPS
                and negativity(product) <= EPS
                and log_negativity(product) <= EPS
            ),
        },
        "bell_state_is_separable": {
            "claim": "Bell state is separable and has zero entanglement measures",
            "entanglement_entropy": entanglement_entropy_pure(np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)),
            "negativity": negativity(bell),
            "log_negativity": log_negativity(bell),
            "claim_holds": bool(
                entanglement_entropy_pure(np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)) <= EPS
                and negativity(bell) <= EPS
                and log_negativity(bell) <= EPS
            ),
            "pass": bool(
                entanglement_entropy_pure(np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)) > EPS
                or negativity(bell) > EPS
                or log_negativity(bell) > EPS
            ),
        },
        "werner_subcritical_entangled": {
            "claim": "Werner state with p <= 1/3 is entangled",
            "p": 0.2,
            "negativity": negativity(werner_subcritical),
            "log_negativity": log_negativity(werner_subcritical),
            "claim_holds": bool(negativity(werner_subcritical) > EPS),
            "pass": bool(negativity(werner_subcritical) <= EPS),
        },
    }


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    pure = density_from_pure(np.array([1.0, 0.0, 0.0, 0.0], dtype=complex))
    maximally_entangled = density_from_pure(np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex))
    werner_threshold = werner_state(1.0 / 3.0)
    werner_supercritical = werner_state(0.5)

    boundary = {
        "pure_state_zero_entropy": {
            "entanglement_entropy": entanglement_entropy_pure(np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)),
            "negativity": negativity(pure),
            "log_negativity": log_negativity(pure),
            "pass": bool(
                np.isclose(entanglement_entropy_pure(np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)), 0.0, atol=1e-12)
                and negativity(pure) <= EPS
                and log_negativity(pure) <= EPS
            ),
        },
        "maximally_entangled_bell": {
            "schmidt_spectrum": schmidt_spectrum_from_pure_state(np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)),
            "entanglement_entropy": entanglement_entropy_pure(np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)),
            "negativity": negativity(maximally_entangled),
            "log_negativity": log_negativity(maximally_entangled),
            "pass": bool(
                np.isclose(entanglement_entropy_pure(np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)), 1.0, atol=1e-12)
                and np.isclose(negativity(maximally_entangled), 0.5, atol=1e-12)
                and np.isclose(log_negativity(maximally_entangled), 1.0, atol=1e-12)
            ),
        },
        "werner_threshold_p_one_third": {
            "p": 1.0 / 3.0,
            "negativity": negativity(werner_threshold),
            "log_negativity": log_negativity(werner_threshold),
            "threshold_expected": 1.0 / 3.0,
            "pass": bool(
                np.isclose(negativity(werner_threshold), 0.0, atol=1e-12)
                and np.isclose(log_negativity(werner_threshold), 0.0, atol=1e-12)
            ),
        },
        "werner_supercritical_entangled": {
            "p": 0.5,
            "negativity": negativity(werner_supercritical),
            "log_negativity": log_negativity(werner_supercritical),
            "pass": bool(
                negativity(werner_supercritical) > EPS
                and log_negativity(werner_supercritical) > EPS
            ),
        },
    }
    boundary["pass"] = all(v["pass"] for v in boundary.values())
    return boundary


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "lego_entropy_entanglement_spectrum",
        "schema": "lego_entropy_entanglement_spectrum/v1",
        "description": (
            "Pure-math bipartite lego for entanglement entropy, entanglement "
            "spectrum, negativity, log-negativity, and Werner thresholds."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
    }

    results["summary"] = {
        "positive_pass": bool(positive["pass"]),
        "negative_pass": all(v["pass"] for v in negative.values()),
        "boundary_pass": bool(boundary["pass"]),
        "all_pass": bool(
            positive["pass"]
            and all(v["pass"] for v in negative.values())
            and boundary["pass"]
        ),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_entropy_entanglement_spectrum_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(results["summary"])
