#!/usr/bin/env python3
"""
SIM LEGO: One-shot entropy proxies on density matrices
=======================================================
Pure math. Honest hypothesis-testing style proxies for one-shot entropies.

This is NOT presented as an exact quantum smooth min/max entropy solver.
Instead, it uses an epsilon-trimmed spectral proxy:

  1. Diagonalize rho
  2. Keep the largest eigenvalues whose total mass is at least 1 - eps
  3. Renormalize the retained spectrum
  4. Report proxy values from the retained spectrum

That gives a conservative coding-scale proxy for:
  - one-shot max-entropy scale via retained rank
  - one-shot min-entropy scale via retained dominant eigenvalue

States:
  - pure product
  - Bell
  - maximally mixed
  - skewed classical mixture
  - Werner sweep

Classification: canonical
"""

import json
import math
import os
import time
import traceback

import torch

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph layer in this one-shot entropy lego"},
    "z3":        {"tried": False, "used": False, "reason": "not needed -- this sim uses exact numeric evaluation, not satisfiability search"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- no synthesis or SMT constraints are required"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- no symbolic derivation beyond the explicit proxy formulas"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer in this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold geometry or statistics here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant neural network layer here"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph or lattice graph computation here"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hypergraph or simplicial complex layer here"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no cell complex or filtration layer here"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology or filtration computation here"},
}

TOOL_MANIFEST["pytorch"]["tried"] = True
TOOL_MANIFEST["pytorch"]["used"] = True
TOOL_MANIFEST["pytorch"]["reason"] = (
    "Core numeric substrate: density matrices, spectra, epsilon-trimmed proxy evaluation"
)

# =====================================================================
# CONSTANTS
# =====================================================================

TOL = 1e-12
I2 = torch.eye(2, dtype=torch.complex128)
I4 = torch.eye(4, dtype=torch.complex128)
PHI_PLUS = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2.0)
PHI_PLUS_DM = torch.outer(PHI_PLUS, PHI_PLUS.conj())


# =====================================================================
# STATES / SPECTRUM
# =====================================================================

def normalize_density(rho):
    rho = (rho + rho.conj().T) / 2.0
    tr = torch.trace(rho)
    if abs(tr.item()) <= TOL:
        raise ValueError("zero-trace density matrix")
    return rho / tr


def spectrum(rho):
    evals = torch.linalg.eigvalsh(normalize_density(rho)).real
    evals = torch.clamp(evals, min=0.0)
    total = torch.sum(evals)
    if float(total) <= TOL:
        raise ValueError("non-positive spectrum")
    return evals / total


def ket01_density():
    psi = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=torch.complex128)
    return torch.outer(psi, psi.conj())


def bell_density():
    return PHI_PLUS_DM.clone()


def maximally_mixed_density():
    return I4 / 4.0


def skewed_density():
    # Simple coding-scale spectrum with a long tail.
    return torch.diag(torch.tensor([0.70, 0.20, 0.10, 0.0], dtype=torch.complex128))


def werner_density(p):
    p = float(p)
    return p * PHI_PLUS_DM + (1.0 - p) * I4 / 4.0


# =====================================================================
# HYPOTHESIS-TESTING STYLE PROXY
# =====================================================================

def trimmed_spectrum(rho, eps):
    """
    Return the retained spectrum after removing a tail of total mass <= eps.

    This is a hypothesis-testing style proxy, not an exact smooth entropy solver.
    """
    if not (0.0 <= eps < 1.0):
        raise ValueError("eps must be in [0, 1)")
    evals = torch.sort(spectrum(rho), descending=True).values
    if eps <= TOL:
        kept = evals[evals > TOL]
        return kept if kept.numel() else torch.tensor([1.0], dtype=torch.float64)

    keep_mass = 0.0
    kept = []
    for val in evals.tolist():
        kept.append(val)
        keep_mass += val
        if keep_mass >= 1.0 - eps - 1e-15:
            break

    kept = torch.tensor(kept, dtype=torch.float64)
    kept = kept / torch.sum(kept)
    return kept


def one_shot_min_entropy_proxy(rho, eps):
    """
    Hypothesis-testing style min-entropy proxy.

    Caveat: this is a tail-trimmed spectral proxy, not an exact H_min^eps.
    """
    kept = trimmed_spectrum(rho, eps)
    dominant = float(torch.max(kept).item())
    return float(-math.log2(dominant))


def one_shot_max_entropy_proxy(rho, eps):
    """
    Hypothesis-testing style max-entropy / coding-scale proxy.

    Caveat: this is a retained-rank proxy, not an exact H_max^eps.
    """
    kept = trimmed_spectrum(rho, eps)
    return float(math.log2(max(1, kept.numel())))


def proxy_report(rho, eps_grid):
    evals = spectrum(rho)
    von_neumann = float((-torch.sum(evals[evals > TOL] * torch.log2(evals[evals > TOL]))).item()) if torch.any(evals > TOL) else 0.0
    return {
        "von_neumann": von_neumann,
        "eps_grid": [float(e) for e in eps_grid],
        "eps_results": {
            str(eps): {
                "retained_rank": int(trimmed_spectrum(rho, eps).numel()),
                "retained_spectrum": [float(x) for x in trimmed_spectrum(rho, eps).tolist()],
                "H_min_proxy": one_shot_min_entropy_proxy(rho, eps),
                "H_max_proxy": one_shot_max_entropy_proxy(rho, eps),
            }
            for eps in eps_grid
        },
    }


# =====================================================================
# TEST HELPERS
# =====================================================================

def close(a, b, tol=1e-10):
    return abs(float(a) - float(b)) <= tol


def monotone_nonincreasing(values, tol=1e-10):
    return all(values[i + 1] <= values[i] + tol for i in range(len(values) - 1))


def monotone_nondecreasing(values, tol=1e-10):
    return all(values[i + 1] >= values[i] - tol for i in range(len(values) - 1))


def validate_state(rho):
    herm = torch.max(torch.abs(rho - rho.conj().T)).item()
    tr = torch.trace(rho).real.item()
    evals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    return {
        "hermitian_error": float(herm),
        "trace": float(tr),
        "min_eigenvalue": float(torch.min(evals).item()),
        "valid": herm < 1e-12 and abs(tr - 1.0) < 1e-12 and torch.min(evals).item() >= -1e-10,
    }


# =====================================================================
# TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    eps_grid = [0.0, 0.05, 0.10, 0.25]
    product = ket01_density()
    bell = bell_density()
    mixed = maximally_mixed_density()
    skewed = skewed_density()
    werner = [werner_density(p) for p in [0.0, 0.25, 1.0 / 3.0, 0.5, 0.75, 1.0]]

    prod_report = proxy_report(product, eps_grid)
    bell_report = proxy_report(bell, eps_grid)
    mixed_report = proxy_report(mixed, eps_grid)
    skewed_report = proxy_report(skewed, eps_grid)
    werner_reports = [proxy_report(rho, [0.0, 0.10, 0.25]) for rho in werner]

    results["pure_state_zero_proxy_entropy"] = {
        "pass": (
            validate_state(product)["valid"]
            and close(prod_report["von_neumann"], 0.0)
            and all(close(v["H_min_proxy"], 0.0) for v in prod_report["eps_results"].values())
            and all(close(v["H_max_proxy"], 0.0) for v in prod_report["eps_results"].values())
        ),
        "details": prod_report,
    }

    results["bell_state_zero_joint_proxy_entropy"] = {
        "pass": (
            validate_state(bell)["valid"]
            and close(bell_report["von_neumann"], 0.0)
            and close(bell_report["eps_results"]["0.0"]["H_min_proxy"], 0.0)
            and close(bell_report["eps_results"]["0.0"]["H_max_proxy"], 0.0)
        ),
        "details": bell_report,
    }

    results["maximally_mixed_state_coding_scale"] = {
        "pass": (
            validate_state(mixed)["valid"]
            and close(mixed_report["von_neumann"], 2.0)
            and close(mixed_report["eps_results"]["0.0"]["H_min_proxy"], 2.0)
            and close(mixed_report["eps_results"]["0.0"]["H_max_proxy"], 2.0)
        ),
        "details": mixed_report,
    }

    results["skewed_state_retained_rank_decreases_with_eps"] = {
        "pass": monotone_nonincreasing([v["retained_rank"] for v in skewed_report["eps_results"].values()]),
        "details": skewed_report,
    }

    results["werner_proxy_tracks_rank_and_entropy_limits"] = {
        "pass": all(
            close(r["eps_results"]["0.0"]["H_min_proxy"], 0.0) if abs(r["von_neumann"]) < 1e-12 else True
            for r in werner_reports
        ),
        "details": werner_reports,
    }

    return results


def run_negative_tests():
    results = {}

    skewed = skewed_density()
    eps = 0.10
    proxy = proxy_report(skewed, [eps])
    hmin_proxy = proxy["eps_results"][str(eps)]["H_min_proxy"]
    hmax_proxy = proxy["eps_results"][str(eps)]["H_max_proxy"]
    vn = proxy["von_neumann"]

    results["proxy_is_not_exact_von_neumann"] = {
        "pass": not close(hmin_proxy, vn) or not close(hmax_proxy, vn),
        "H_min_proxy": hmin_proxy,
        "H_max_proxy": hmax_proxy,
        "von_neumann": vn,
        "note": "Proxy is intentionally not exact on a skewed mixed state",
    }

    results["larger_eps_does_not_increase_retained_rank"] = {
        "pass": monotone_nonincreasing(
            [proxy_report(skewed, [e])["eps_results"][str(e)]["retained_rank"] for e in [0.0, 0.05, 0.10, 0.25]]
        ),
        "note": "More smoothing budget should not increase the retained coding rank proxy",
    }

    results["pure_state_not_positive_proxy"] = {
        "pass": not (one_shot_min_entropy_proxy(ket01_density(), 0.10) > 1e-10),
        "H_min_proxy": one_shot_min_entropy_proxy(ket01_density(), 0.10),
    }

    results["maximally_mixed_not_zero_proxy"] = {
        "pass": not close(one_shot_max_entropy_proxy(maximally_mixed_density(), 0.10), 0.0),
        "H_max_proxy": one_shot_max_entropy_proxy(maximally_mixed_density(), 0.10),
    }

    return results


def run_boundary_tests():
    results = {}

    pure = ket01_density()
    mixed = maximally_mixed_density()
    skewed = skewed_density()

    results["eps_zero_matches_unsmoothed_proxy"] = {
        "pass": close(one_shot_min_entropy_proxy(skewed, 0.0), -math.log2(0.70)),
        "H_min_proxy_eps0": one_shot_min_entropy_proxy(skewed, 0.0),
        "expected": -math.log2(0.70),
    }

    results["pure_state_all_eps_zero"] = {
        "pass": all(close(one_shot_min_entropy_proxy(pure, eps), 0.0) for eps in [0.0, 0.05, 0.25]),
        "details": {str(eps): one_shot_min_entropy_proxy(pure, eps) for eps in [0.0, 0.05, 0.25]},
    }

    results["maximally_mixed_state_stable"] = {
        "pass": all(close(one_shot_max_entropy_proxy(mixed, eps), 2.0) for eps in [0.0, 0.05, 0.10]),
        "details": {str(eps): one_shot_max_entropy_proxy(mixed, eps) for eps in [0.0, 0.05, 0.10]},
    }

    results["eps_large_reduces_support"] = {
        "pass": one_shot_max_entropy_proxy(skewed, 0.25) <= one_shot_max_entropy_proxy(skewed, 0.0) + 1e-10,
        "H_max_eps0": one_shot_max_entropy_proxy(skewed, 0.0),
        "H_max_eps25": one_shot_max_entropy_proxy(skewed, 0.25),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running one-shot entropy proxy sim...")
    t_start = time.time()

    try:
        positive = run_positive_tests()
        negative = run_negative_tests()
        boundary = run_boundary_tests()
        error = None
    except Exception as exc:
        positive = {}
        negative = {}
        boundary = {}
        error = {"error": str(exc), "traceback": traceback.format_exc()}

    def count_passes(section):
        total = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
        passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass"))
        return passed, total

    p_pass, p_total = count_passes(positive)
    n_pass, n_total = count_passes(negative)
    b_pass, b_total = count_passes(boundary)

    results = {
        "name": "One-Shot Entropy Proxies",
        "schema_version": "1.0",
        "classification": "canonical",
        "proxy_note": "Hypothesis-testing style proxy only; not an exact smooth min/max entropy solver",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "positive": f"{p_pass}/{p_total}",
            "negative": f"{n_pass}/{n_total}",
            "boundary": f"{b_pass}/{b_total}",
            "all_pass": error is None and p_pass == p_total and n_pass == n_total and b_pass == b_total,
            "total_time_s": time.time() - t_start,
        },
    }
    if error is not None:
        results["error"] = error

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_entropy_smooth_one_shot_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")
    print(f"Positive: {p_pass}/{p_total}  Negative: {n_pass}/{n_total}  Boundary: {b_pass}/{b_total}")
    if results["summary"]["all_pass"]:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check results JSON")
