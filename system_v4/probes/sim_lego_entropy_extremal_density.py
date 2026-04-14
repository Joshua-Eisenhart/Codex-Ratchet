#!/usr/bin/env python3
"""
PURE LEGO: Extremal Entropy Families on Density Matrices
=========================================================
One-shot / extremal entropy lego for density matrices.

This probe tests:
  - Min-entropy: H_min(rho) = -log2(lambda_max(rho))
  - Max-entropy: H_max(rho) = 2 log2(Tr sqrt(rho))
  - Unitary invariance of both
  - Boundary cases: pure, mixed, maximally mixed, rank-deficient states
  - Simple regularized proxy approximations

The regularized proxies are explicitly labeled approximations:
  rho_eps = (1-eps) rho + eps * I/d
They are not the formal smooth entropies, but they are a minimal
smoothed spectral proxy that is easy to audit in a self-contained lego.
"""

import json
import os
import time

import numpy as np
classification = "classical_baseline"  # auto-backfill

np.random.seed(42)
EPS = 1e-12

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this entropy lego"},
}


# =====================================================================
# DENSITY MATRIX HELPERS
# =====================================================================

def normalize_hermitian(rho):
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("density matrix trace too small")
    return rho / tr


def density_from_spectrum(spectrum, rng=None):
    """Build a density matrix with a prescribed spectrum."""
    spectrum = np.array(spectrum, dtype=float)
    spectrum = spectrum / np.sum(spectrum)
    d = len(spectrum)
    if rng is None:
        rng = np.random.RandomState(42)
    z = rng.randn(d, d) + 1j * rng.randn(d, d)
    q, r = np.linalg.qr(z)
    phases = np.diag(r)
    phases = phases / np.where(np.abs(phases) < EPS, 1.0, np.abs(phases))
    u = q * phases.conj()
    rho = u @ np.diag(spectrum) @ u.conj().T
    return normalize_hermitian(rho)


def random_density(rng, d=2):
    """Random full-rank density matrix."""
    z = rng.randn(d, d) + 1j * rng.randn(d, d)
    rho = z @ z.conj().T
    return normalize_hermitian(rho)


def von_neumann_entropy(rho):
    eigs = np.clip(np.linalg.eigvalsh(normalize_hermitian(rho)), 0.0, None)
    nz = eigs[eigs > EPS]
    return float(-np.sum(nz * np.log2(nz))) if len(nz) else 0.0


def min_entropy(rho):
    """H_min(rho) = -log2(lambda_max(rho))."""
    lam_max = float(np.max(np.clip(np.linalg.eigvalsh(normalize_hermitian(rho)), 0.0, None)))
    return float(-np.log2(max(lam_max, EPS)))


def max_entropy(rho):
    """H_max(rho) = 2 log2(Tr sqrt(rho))."""
    eigs = np.clip(np.linalg.eigvalsh(normalize_hermitian(rho)), 0.0, None)
    return float(2.0 * np.log2(np.sum(np.sqrt(eigs))))


def regularized_proxy_state(rho, eps):
    """Simple smoothed proxy state: mix with identity."""
    rho = normalize_hermitian(rho)
    d = rho.shape[0]
    return normalize_hermitian((1.0 - eps) * rho + eps * np.eye(d, dtype=complex) / d)


def approx_min_entropy(rho, eps):
    """Approximation proxy for a smoothed min-entropy."""
    return min_entropy(regularized_proxy_state(rho, eps))


def approx_max_entropy(rho, eps):
    """Approximation proxy for a smoothed max-entropy."""
    return max_entropy(regularized_proxy_state(rho, eps))


def unitary_from_rng(rng, d):
    z = rng.randn(d, d) + 1j * rng.randn(d, d)
    q, r = np.linalg.qr(z)
    phases = np.diag(r)
    phases = phases / np.where(np.abs(phases) < EPS, 1.0, np.abs(phases))
    return q * phases.conj()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    rng = np.random.RandomState(123)
    results = {}
    t0 = time.time()

    spectra = {
        "pure_qubit": [1.0, 0.0],
        "balanced_qubit": [0.5, 0.5],
        "skew_qubit": [0.8, 0.2],
        "rank2_qutrit": [0.6, 0.4, 0.0],
        "generic_qutrit": [0.5, 0.3, 0.2],
    }

    exact_matches = {}
    ordering_checks = {}
    unitary_invariance = {}

    for name, spectrum in spectra.items():
        rho = density_from_spectrum(spectrum, rng=rng)
        d = rho.shape[0]
        exact_min = min_entropy(rho)
        exact_max = max_entropy(rho)
        spectrum_min = -np.log2(max(np.max(spectrum), EPS))
        spectrum_max = float(2.0 * np.log2(np.sum(np.sqrt(np.clip(spectrum, 0.0, None)))))
        exact_matches[name] = {
            "min_entropy": exact_min,
            "min_entropy_expected": float(spectrum_min),
            "min_entropy_pass": bool(np.isclose(exact_min, spectrum_min, atol=1e-12)),
            "max_entropy": exact_max,
            "max_entropy_expected": spectrum_max,
            "max_entropy_pass": bool(np.isclose(exact_max, spectrum_max, atol=1e-12)),
            "dimension": d,
        }

        ordering_checks[name] = {
            "min_leq_max": bool(exact_min <= exact_max + 1e-12),
            "bounded_above_by_log_dim": bool(exact_max <= np.log2(d) + 1e-12),
        }

        u = unitary_from_rng(rng, d)
        rho_u = u @ rho @ u.conj().T
        unitary_invariance[name] = {
            "min_invariant": bool(np.isclose(min_entropy(rho), min_entropy(rho_u), atol=1e-7)),
            "max_invariant": bool(np.isclose(max_entropy(rho), max_entropy(rho_u), atol=1e-7)),
        }

    proxy_state = density_from_spectrum([0.78, 0.22], rng=rng)
    eps_grid = [0.0, 0.05, 0.15, 0.3]
    proxy_trace = []
    for eps in eps_grid:
        rho_eps = regularized_proxy_state(proxy_state, eps)
        proxy_trace.append(
            {
                "eps": eps,
                "min_entropy_approx": approx_min_entropy(proxy_state, eps),
                "max_entropy_approx": approx_max_entropy(proxy_state, eps),
                "trace_error": float(abs(np.trace(rho_eps) - 1.0)),
                "hermitian_error": float(np.max(np.abs(rho_eps - rho_eps.conj().T))),
            }
        )

    proxy_pass = (
        np.isclose(proxy_trace[0]["min_entropy_approx"], min_entropy(proxy_state), atol=1e-12)
        and np.isclose(proxy_trace[0]["max_entropy_approx"], max_entropy(proxy_state), atol=1e-12)
        and proxy_trace[-1]["min_entropy_approx"] >= proxy_trace[0]["min_entropy_approx"] - 1e-12
        and proxy_trace[-1]["max_entropy_approx"] >= proxy_trace[0]["max_entropy_approx"] - 1e-12
    )

    results["exact_spectrum_matches"] = exact_matches
    results["ordering_checks"] = ordering_checks
    results["unitary_invariance"] = unitary_invariance
    results["regularized_proxy_trace"] = proxy_trace
    results["regularized_proxy_pass"] = bool(proxy_pass)
    results["pass"] = all(
        item["min_entropy_pass"] and item["max_entropy_pass"] for item in exact_matches.values()
    ) and all(
        item["min_leq_max"] and item["bounded_above_by_log_dim"] for item in ordering_checks.values()
    ) and all(
        item["min_invariant"] and item["max_invariant"] for item in unitary_invariance.values()
    ) and proxy_pass
    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    rho = np.array([[0.8, 0.0], [0.0, 0.2]], dtype=complex)
    s_vn = von_neumann_entropy(rho)
    s_min = min_entropy(rho)
    s_max = max_entropy(rho)
    return {
        "vN_equals_min_entropy": {
            "claim": "Von Neumann entropy equals min-entropy for generic mixed states",
            "counterexample": {
                "spectrum": [0.8, 0.2],
                "von_neumann_entropy": s_vn,
                "min_entropy": s_min,
            },
            "claim_holds": bool(np.isclose(s_vn, s_min, atol=1e-12)),
            "pass": bool(not np.isclose(s_vn, s_min, atol=1e-12)),
        },
        "vN_equals_max_entropy": {
            "claim": "Von Neumann entropy equals max-entropy for generic mixed states",
            "counterexample": {
                "spectrum": [0.8, 0.2],
                "von_neumann_entropy": s_vn,
                "max_entropy": s_max,
            },
            "claim_holds": bool(np.isclose(s_vn, s_max, atol=1e-12)),
            "pass": bool(not np.isclose(s_vn, s_max, atol=1e-12)),
        },
        "proxy_equals_exact_for_positive_eps": {
            "claim": "Regularized proxy entropies equal the exact entropies for eps > 0",
            "counterexample": {
                "eps": 0.2,
                "approx_min_entropy": approx_min_entropy(rho, 0.2),
                "exact_min_entropy": s_min,
                "approx_max_entropy": approx_max_entropy(rho, 0.2),
                "exact_max_entropy": s_max,
            },
            "claim_holds": bool(
                np.isclose(approx_min_entropy(rho, 0.2), s_min, atol=1e-12)
                and np.isclose(approx_max_entropy(rho, 0.2), s_max, atol=1e-12)
            ),
            "pass": bool(
                not (
                    np.isclose(approx_min_entropy(rho, 0.2), s_min, atol=1e-12)
                    and np.isclose(approx_max_entropy(rho, 0.2), s_max, atol=1e-12)
                )
            ),
        },
    }


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    cases = {
        "pure_qubit": np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex),
        "maximally_mixed_qubit": np.eye(2, dtype=complex) / 2.0,
        "rank2_qutrit_edge": np.diag([0.75, 0.25, 0.0]).astype(complex),
        "near_pure_qubit": np.diag([0.999, 0.001]).astype(complex),
    }

    details = {}
    pure_ok = True
    maxmix_ok = True
    rank_edge_ok = True
    approx_ok = True

    for name, rho in cases.items():
        hmin = min_entropy(rho)
        hmax = max_entropy(rho)
        details[name] = {
            "min_entropy": hmin,
            "max_entropy": hmax,
            "trace": float(np.trace(rho).real),
            "hermitian_error": float(np.max(np.abs(rho - rho.conj().T))),
        }

    pure_ok = np.isclose(details["pure_qubit"]["min_entropy"], 0.0, atol=1e-12) and np.isclose(
        details["pure_qubit"]["max_entropy"], 0.0, atol=1e-12
    )
    maxmix_ok = np.isclose(details["maximally_mixed_qubit"]["min_entropy"], 1.0, atol=1e-12) and np.isclose(
        details["maximally_mixed_qubit"]["max_entropy"], 1.0, atol=1e-12
    )
    rank_edge_ok = np.isclose(details["rank2_qutrit_edge"]["min_entropy"], -np.log2(0.75), atol=1e-12)

    near_pure = cases["near_pure_qubit"]
    approx_trace = []
    for eps in [0.0, 0.05, 0.2]:
        approx_trace.append(
            {
                "eps": eps,
                "min_entropy_approx": approx_min_entropy(near_pure, eps),
                "max_entropy_approx": approx_max_entropy(near_pure, eps),
            }
        )
    approx_ok = (
        np.isclose(approx_trace[0]["min_entropy_approx"], min_entropy(near_pure), atol=1e-12)
        and np.isclose(approx_trace[0]["max_entropy_approx"], max_entropy(near_pure), atol=1e-12)
        and approx_trace[-1]["min_entropy_approx"] > approx_trace[0]["min_entropy_approx"]
        and approx_trace[-1]["max_entropy_approx"] > approx_trace[0]["max_entropy_approx"]
    )

    return {
        "boundary_cases": details,
        "regularized_proxy_boundary_trace": approx_trace,
        "pure_state_zero_entropy": bool(pure_ok),
        "maximally_mixed_qubit_one_bit": bool(maxmix_ok),
        "rank_edge_matches_spectrum": bool(rank_edge_ok),
        "proxy_moves_toward_mixing": bool(approx_ok),
        "pass": bool(pure_ok and maxmix_ok and rank_edge_ok and approx_ok),
    }


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    results = {
        "name": "lego_entropy_extremal_density",
        "schema": "lego_entropy_extremal_density/v1",
        "description": (
            "Pure-math density-matrix lego for min-entropy, max-entropy, "
            "and explicit regularized proxy approximations."
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
    out_path = os.path.join(out_dir, "lego_entropy_extremal_density_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(results["summary"])
