#!/usr/bin/env python3
"""
PURE LEGO: Finite-Blocklength / One-Shot Entropy Families
=========================================================
Pre-bridge pure math only.

This sim covers bounded one-shot / finite-blocklength-adjacent quantities on
finite-dimensional density matrices without claiming final Axis-0 closure:

1. Max-relative entropy    D_max(rho || sigma)
2. Min-relative entropy    D_min(rho || sigma)
3. Commuting hypothesis-testing relative entropy D_H^eps(rho || sigma)
4. A simple finite-sample smoothing envelope for D_max under convex mixing

The hypothesis-testing quantity is implemented exactly on commuting
(simultaneously diagonal) examples, which is the right finite classical test
bed before any bridge or full quantum optimizer is claimed.
"""

import json
import math
import os
classification = "classical_baseline"  # auto-backfill


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this lego"},
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

try:
    import torch

    torch.manual_seed(0)
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core finite-dimensional density-matrix arithmetic, eigendecomposition, "
        "support checks, and one-shot entropy evaluation"
    )
except ImportError as exc:
    raise SystemExit(f"PyTorch required for canonical sim: {exc}")


CDTYPE = torch.complex128
FDTYPE = torch.float64
EPS = 1e-10
LOG2 = math.log(2.0)


def dm_from_probs(probs):
    probs = torch.tensor(probs, dtype=FDTYPE)
    return torch.diag(probs).to(CDTYPE)


def ket_to_dm(amps):
    psi = torch.tensor(amps, dtype=CDTYPE).reshape(-1, 1)
    psi = psi / torch.linalg.norm(psi)
    return psi @ psi.conj().T


def validate_density_matrix(rho):
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        return False, "matrix must be square"
    if not torch.allclose(rho, rho.conj().T, atol=1e-9):
        return False, "matrix must be Hermitian"
    tr = torch.trace(rho).real.item()
    if abs(tr - 1.0) > 1e-8:
        return False, "trace must equal 1"
    evals = torch.linalg.eigvalsh(rho).real
    if evals.min().item() < -1e-8:
        return False, "matrix must be positive semidefinite"
    return True, "ok"


def support_projector(rho, tol=EPS):
    evals, evecs = torch.linalg.eigh(rho)
    mask = evals.real > tol
    if mask.sum().item() == 0:
        return torch.zeros_like(rho)
    vecs = evecs[:, mask]
    return vecs @ vecs.conj().T


def matrix_log_psd(rho, floor=1e-15):
    evals, evecs = torch.linalg.eigh(rho)
    clipped = torch.clamp(evals.real, min=floor)
    log_diag = torch.diag(torch.log(clipped)).to(CDTYPE)
    return evecs @ log_diag @ evecs.conj().T


def d_max(rho, sigma, tol=EPS):
    ok_rho, msg_rho = validate_density_matrix(rho)
    ok_sig, msg_sig = validate_density_matrix(sigma)
    if not ok_rho:
        raise ValueError(f"invalid rho: {msg_rho}")
    if not ok_sig:
        raise ValueError(f"invalid sigma: {msg_sig}")

    p_rho = support_projector(rho, tol)
    p_sig = support_projector(sigma, tol)
    support_violation = torch.linalg.matrix_norm((torch.eye(rho.shape[0], dtype=CDTYPE) - p_sig) @ p_rho).item()
    if support_violation > 1e-8:
        return math.inf

    evals, evecs = torch.linalg.eigh(sigma)
    inv_sqrt = torch.zeros_like(sigma)
    for idx, val in enumerate(evals.real):
        if val > tol:
            vec = evecs[:, idx:idx + 1]
            inv_sqrt += (1.0 / math.sqrt(val.item())) * (vec @ vec.conj().T)
    witness = inv_sqrt @ rho @ inv_sqrt
    lam = torch.linalg.eigvalsh(witness).real.max().item()
    return math.log(lam)


def d_min(rho, sigma, tol=EPS):
    ok_rho, msg_rho = validate_density_matrix(rho)
    ok_sig, msg_sig = validate_density_matrix(sigma)
    if not ok_rho:
        raise ValueError(f"invalid rho: {msg_rho}")
    if not ok_sig:
        raise ValueError(f"invalid sigma: {msg_sig}")

    p_rho = support_projector(rho, tol)
    overlap = torch.trace(p_rho @ sigma).real.item()
    if overlap <= tol:
        return math.inf
    return -math.log(overlap)


def von_neumann_entropy(rho):
    evals = torch.linalg.eigvalsh(rho).real
    evals = evals[evals > EPS]
    if evals.numel() == 0:
        return 0.0
    return float((-(evals * torch.log(evals)).sum()).item())


def hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon):
    if not (0.0 <= epsilon < 1.0):
        raise ValueError("epsilon must satisfy 0 <= epsilon < 1")
    rho_probs = [float(x) for x in rho_probs]
    sigma_probs = [float(x) for x in sigma_probs]
    if abs(sum(rho_probs) - 1.0) > 1e-9 or abs(sum(sigma_probs) - 1.0) > 1e-9:
        raise ValueError("probability vectors must sum to 1")

    n = len(rho_probs)
    best_beta = math.inf
    best_subset = None
    for mask in range(1 << n):
        accept = [(mask >> i) & 1 for i in range(n)]
        alpha = 1.0 - sum(r * a for r, a in zip(rho_probs, accept))
        beta = sum(s * a for s, a in zip(sigma_probs, accept))
        if alpha <= epsilon + 1e-12 and beta < best_beta:
            best_beta = beta
            best_subset = accept

    if best_subset is None:
        raise RuntimeError("no feasible acceptance test found")
    if best_beta <= EPS:
        return math.inf, best_subset, 0.0
    return -math.log(best_beta), best_subset, best_beta


def smooth_state_toward_sigma(rho, sigma, eps):
    if not (0.0 <= eps <= 1.0):
        raise ValueError("smoothing parameter must satisfy 0 <= eps <= 1")
    return (1.0 - eps) * rho + eps * sigma


def count_passes(tree):
    passed = 0
    failed = 0
    if isinstance(tree, dict):
        if "pass" in tree:
            return (1, 0) if tree["pass"] else (0, 1)
        for value in tree.values():
            p, f = count_passes(value)
            passed += p
            failed += f
    elif isinstance(tree, list):
        for value in tree:
            p, f = count_passes(value)
            passed += p
            failed += f
    return passed, failed


def run_positive_tests():
    results = {"tests": []}

    rho_pure = ket_to_dm([1.0, 0.0])
    sigma_mix = 0.5 * torch.eye(2, dtype=CDTYPE)
    dmax_val = d_max(rho_pure, sigma_mix)
    dmin_val = d_min(rho_pure, sigma_mix)
    expected = math.log(2.0)
    results["tests"].append({
        "name": "pure_vs_maximally_mixed",
        "d_max": dmax_val,
        "d_min": dmin_val,
        "expected_log2": expected,
        "pass": abs(dmax_val - expected) < 1e-8 and abs(dmin_val - expected) < 1e-8,
    })

    rho_diag = dm_from_probs([0.75, 0.25])
    sigma_diag = dm_from_probs([0.5, 0.5])
    dmax_diag = d_max(rho_diag, sigma_diag)
    expected_diag = math.log(1.5)
    results["tests"].append({
        "name": "diagonal_dmax_matches_ratio_formula",
        "d_max": dmax_diag,
        "expected": expected_diag,
        "pass": abs(dmax_diag - expected_diag) < 1e-8,
    })

    rho_probs = [0.9, 0.1]
    sigma_probs = [0.5, 0.5]
    dh0, subset0, beta0 = hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon=0.0)
    results["tests"].append({
        "name": "hypothesis_testing_zero_epsilon_exact_subset",
        "d_h_eps": dh0,
        "beta_eps": beta0,
        "accept_subset": subset0,
        "expected": 0.0,
        "pass": subset0 == [1, 1] and abs(dh0) < 1e-8 and abs(beta0 - 1.0) < 1e-8,
    })

    dh_relaxed, subset_relaxed, beta_relaxed = hypothesis_testing_relative_entropy_commuting(
        rho_probs, sigma_probs, epsilon=0.11
    )
    results["tests"].append({
        "name": "hypothesis_testing_relaxes_with_epsilon",
        "d_h_zero": dh0,
        "d_h_relaxed": dh_relaxed,
        "beta_relaxed": beta_relaxed,
        "accept_subset_relaxed": subset_relaxed,
        "expected_relaxed_value": math.log(2.0),
        "pass": False,
    })
    # Replace the last pass with the actual mathematical condition:
    results["tests"][-1]["pass"] = (
        dh_relaxed > dh0 and subset_relaxed == [1, 0] and abs(dh_relaxed - (-math.log(0.5))) < 1e-8
    )

    rho = dm_from_probs([0.8, 0.2])
    sigma = dm_from_probs([0.55, 0.45])
    eps_grid = [0.0, 0.1, 0.2, 0.4]
    smoothed = []
    for eps in eps_grid:
        rho_eps = smooth_state_toward_sigma(rho, sigma, eps)
        smoothed.append({"eps": eps, "d_max": d_max(rho_eps, sigma)})
    monotone = all(smoothed[i]["d_max"] >= smoothed[i + 1]["d_max"] - 1e-9 for i in range(len(smoothed) - 1))
    results["tests"].append({
        "name": "convex_smoothing_nonincreasing_dmax",
        "curve": smoothed,
        "pass": monotone,
    })

    rho_noncomm = ket_to_dm([1.0, 1.0j])
    sigma_noncomm = dm_from_probs([0.7, 0.3])
    dmax_nc = d_max(rho_noncomm, sigma_noncomm)
    dmin_nc = d_min(rho_noncomm, sigma_noncomm)
    entropy_nc = von_neumann_entropy(rho_noncomm)
    results["tests"].append({
        "name": "noncommuting_density_case_is_well_defined_prebridge",
        "d_max": dmax_nc,
        "d_min": dmin_nc,
        "entropy": entropy_nc,
        "pass": math.isfinite(dmax_nc) and math.isfinite(dmin_nc) and abs(entropy_nc) < 1e-8,
    })

    return results


def run_negative_tests():
    results = {"tests": []}

    rho_bad_trace = torch.diag(torch.tensor([0.6, 0.6], dtype=FDTYPE)).to(CDTYPE)
    ok, msg = validate_density_matrix(rho_bad_trace)
    results["tests"].append({
        "name": "reject_non_normalized_matrix",
        "message": msg,
        "pass": not ok and "trace" in msg,
    })

    sigma_support_gap = dm_from_probs([1.0, 0.0])
    rho_off_support = dm_from_probs([0.0, 1.0])
    dmax_inf = d_max(rho_off_support, sigma_support_gap)
    dmin_inf = d_min(rho_off_support, sigma_support_gap)
    results["tests"].append({
        "name": "support_violation_gives_infinite_one_shot_divergence",
        "d_max_is_inf": math.isinf(dmax_inf),
        "d_min_is_inf": math.isinf(dmin_inf),
        "pass": math.isinf(dmax_inf) and math.isinf(dmin_inf),
    })

    try:
        hypothesis_testing_relative_entropy_commuting([0.5, 0.5], [0.5, 0.5], epsilon=1.0)
        eps_rejected = False
    except ValueError:
        eps_rejected = True
    results["tests"].append({
        "name": "reject_invalid_hypothesis_testing_epsilon",
        "pass": eps_rejected,
    })

    rho_probs = [0.6, 0.4]
    sigma_probs = [0.6, 0.4]
    dh_equal, subset_equal, beta_equal = hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon=0.2)
    results["tests"].append({
        "name": "identical_commuting_states_do_not_fake_discrimination",
        "d_h_eps": dh_equal,
        "beta_eps": beta_equal,
        "subset": subset_equal,
        "pass": abs(dh_equal) < 1e-8 and abs(beta_equal - 1.0) < 1e-8,
    })

    return results


def run_boundary_tests():
    results = {"tests": []}

    rho = dm_from_probs([0.5, 0.5])
    sigma = dm_from_probs([0.5, 0.5])
    results["tests"].append({
        "name": "identical_states_zero_dmax_dmin",
        "d_max": d_max(rho, sigma),
        "d_min": d_min(rho, sigma),
        "pass": abs(d_max(rho, sigma)) < 1e-8 and abs(d_min(rho, sigma)) < 1e-8,
    })

    rho_probs = [1.0, 0.0]
    sigma_probs = [0.5, 0.5]
    dh0, subset0, beta0 = hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon=0.0)
    dh_relaxed, subset_relaxed, beta_relaxed = hypothesis_testing_relative_entropy_commuting(
        rho_probs, sigma_probs, epsilon=0.01
    )
    results["tests"].append({
        "name": "perfectly_distinguishable_commuting_case_stays_exact",
        "d_h_eps0": dh0,
        "d_h_eps_small": dh_relaxed,
        "beta_eps0": beta0,
        "beta_eps_small": beta_relaxed,
        "subsets": [subset0, subset_relaxed],
        "expected": math.log(2.0),
        "pass": (
            subset0 == [1, 0]
            and subset_relaxed == [1, 0]
            and abs(beta0 - 0.5) < 1e-8
            and abs(beta_relaxed - 0.5) < 1e-8
            and abs(dh0 - math.log(2.0)) < 1e-8
            and abs(dh_relaxed - math.log(2.0)) < 1e-8
        ),
    })

    rho_eps = smooth_state_toward_sigma(dm_from_probs([0.9, 0.1]), dm_from_probs([0.5, 0.5]), 1.0)
    results["tests"].append({
        "name": "full_smoothing_reaches_reference_state",
        "pass": torch.allclose(rho_eps, dm_from_probs([0.5, 0.5]), atol=1e-10),
    })

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    p_pass, p_fail = count_passes(positive)
    n_pass, n_fail = count_passes(negative)
    b_pass, b_fail = count_passes(boundary)

    results = {
        "name": "lego_entropy_finite_blocklength",
        "probe": "lego_entropy_finite_blocklength",
        "purpose": (
            "Evaluate bounded one-shot / finite-blocklength entropy-adjacent quantities "
            "on finite density matrices before any bridge or Axis-0 closure claim"
        ),
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tools_used": [name for name, meta in TOOL_MANIFEST.items() if meta["used"]],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "positive": {"passed": p_pass, "failed": p_fail},
            "negative": {"passed": n_pass, "failed": n_fail},
            "boundary": {"passed": b_pass, "failed": b_fail},
            "total_passed": p_pass + n_pass + b_pass,
            "total_failed": p_fail + n_fail + b_fail,
            "all_pass": (p_fail + n_fail + b_fail) == 0,
            "scope_note": (
                "Finite-blocklength / one-shot pre-bridge math only. "
                "No claim of final Axis-0 kernel selection."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_entropy_finite_blocklength_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Positive: {p_pass} passed, {p_fail} failed")
    print(f"Negative: {n_pass} passed, {n_fail} failed")
    print(f"Boundary: {b_pass} passed, {b_fail} failed")
    print(f"ALL PASS: {results['summary']['all_pass']}")
    print(f"Results written to {out_path}")
