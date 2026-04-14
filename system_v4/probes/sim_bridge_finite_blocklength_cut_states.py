#!/usr/bin/env python3
classification = "classical_baseline"  # auto-backfill
r"""
PURE LEGO: Bridge Cut States -- Finite-Blocklength / One-Shot Quantities
=========================================================================
Pure math only. Pre-closure cut-state analysis on bridge-built rho_AB states.

This sim evaluates bounded one-shot / finite-blocklength-adjacent quantities on
bridge-built bipartite states against the product reference rho_A \otimes rho_B:

1. D_max(rho_AB || rho_A \otimes rho_B)
2. D_min(rho_AB || rho_A \otimes rho_B)
3. A commuting measurement hypothesis-testing proxy
4. A simple smoothing envelope under convex mixing toward rho_A \otimes rho_B

The hypothesis-testing quantity is explicitly a commuting proxy obtained after a
fixed computational-basis measurement. It is not claimed as a full quantum
hypothesis-testing optimizer.
"""

import json
import math
import os


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
        "Core bipartite density-matrix construction, partial trace, support tests, "
        "one-shot divergence evaluation, and smoothing sweeps"
    )
except ImportError as exc:
    raise SystemExit(f"PyTorch required for canonical sim: {exc}")


CDTYPE = torch.complex128
FDTYPE = torch.float64
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)


def ket_to_dm(amps):
    psi = torch.as_tensor(amps, dtype=CDTYPE).reshape(-1, 1)
    psi = psi / torch.linalg.norm(psi)
    return psi @ psi.conj().T


def dm_from_probs(probs):
    probs = torch.tensor(probs, dtype=FDTYPE)
    return torch.diag(probs).to(CDTYPE)


def normalize_density(rho):
    rho = 0.5 * (rho + rho.conj().T)
    tr = torch.trace(rho)
    if abs(tr.item()) <= EPS:
        raise ValueError("trace too small for normalization")
    return rho / tr


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


def is_psd(rho, tol=1e-10):
    evals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    return bool(evals.min().item() >= -tol), float(evals.min().item())


def partial_trace_a(rho_ab):
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", rho)


def partial_trace_b(rho_ab):
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("abad->bd", rho)


def support_projector(rho, tol=EPS):
    evals, evecs = torch.linalg.eigh(rho)
    mask = evals.real > tol
    if mask.sum().item() == 0:
        return torch.zeros_like(rho)
    vecs = evecs[:, mask]
    return vecs @ vecs.conj().T


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
    return math.log(torch.linalg.eigvalsh(witness).real.max().item())


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


def hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon):
    if not (0.0 <= epsilon < 1.0):
        raise ValueError("epsilon must satisfy 0 <= epsilon < 1")
    rho_probs = [float(x) for x in rho_probs]
    sigma_probs = [float(x) for x in sigma_probs]
    if abs(sum(rho_probs) - 1.0) > 1e-9 or abs(sum(sigma_probs) - 1.0) > 1.0e-9:
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


def computational_basis_probs(rho):
    probs = torch.diag(rho).real
    probs = torch.clamp(probs, min=0.0)
    probs = probs / probs.sum()
    return probs.tolist()


def smooth_toward_reference(rho, sigma, eps):
    if not (0.0 <= eps <= 1.0):
        raise ValueError("smoothing parameter must satisfy 0 <= eps <= 1")
    return normalize_density((1.0 - eps) * rho + eps * sigma)


def negativity(rho_ab):
    rho = rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    evals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    return float(max(0.0, (torch.sum(torch.abs(evals)).item() - 1.0) / 2.0))


def product_packet():
    rho_a = dm_from_probs([1.0, 0.0])
    rho_b = dm_from_probs([0.0, 1.0])
    rho_ab = torch.kron(rho_a, rho_b)
    return {"label": "product", "rho_ab": rho_ab}


def separable_packet():
    rho_ab = 0.6 * ket_to_dm([1.0, 0.0, 0.0, 0.0]) + 0.4 * ket_to_dm([0.0, 0.0, 0.0, 1.0])
    return {"label": "separable_correlated", "rho_ab": rho_ab}


def bell_packet():
    return {"label": "entangled_bell", "rho_ab": ket_to_dm([1.0, 0.0, 0.0, 1.0])}


def werner_packet(p):
    bell = ket_to_dm([1.0, 0.0, 0.0, 1.0])
    return {"label": f"werner_p_{p:.2f}", "rho_ab": normalize_density(p * bell + (1.0 - p) * I4 / 4.0), "p": p}


def history_packets():
    plus = torch.tensor([1.0, 1.0], dtype=CDTYPE) / math.sqrt(2.0)
    zero = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    cnot = torch.tensor(
        [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 1],
         [0, 0, 1, 0]],
        dtype=CDTYPE,
    )
    bell_from_cnot = cnot @ torch.kron(plus, zero)
    rho_history_bell = ket_to_dm(bell_from_cnot)

    z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    z_a = torch.kron(z, I2)
    bell = ket_to_dm([1.0, 0.0, 0.0, 1.0])
    rho_dephased = normalize_density(0.65 * bell + 0.35 * (z_a @ bell @ z_a.conj().T))

    rho_history_mix = normalize_density(0.55 * ket_to_dm([0.0, 1.0, -1.0, 0.0]) + 0.45 * separable_packet()["rho_ab"])
    return [
        {"label": "history_cnot_bell", "rho_ab": rho_history_bell},
        {"label": "history_dephased_bell", "rho_ab": rho_dephased},
        {"label": "history_mixed", "rho_ab": rho_history_mix},
    ]


def counterfeit_packet():
    rho_a = dm_from_probs([0.7, 0.3])
    rho_b = dm_from_probs([0.4, 0.6])
    rho_ab = torch.kron(rho_a, rho_b).clone()
    rho_ab[0, 3] = 0.35
    rho_ab[3, 0] = 0.35
    return {"label": "counterfeit_coupling", "rho_ab": rho_ab, "claimed_rho_a": rho_a, "claimed_rho_b": rho_b}


def invalid_packet():
    rho_ab = torch.tensor(
        [[0.7, 0.3, 0.0, 0.0],
         [0.3, 0.4, 0.0, 0.0],
         [0.0, 0.0, -0.1, 0.0],
         [0.0, 0.0, 0.0, 0.0]],
        dtype=CDTYPE,
    )
    return {"label": "invalid_bridge_state", "rho_ab": rho_ab}


def packet_metrics(packet, epsilon=0.1):
    rho_ab = normalize_density(packet["rho_ab"])
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    sigma = torch.kron(rho_a, rho_b)
    dmax_val = d_max(rho_ab, sigma)
    dmin_val = d_min(rho_ab, sigma)
    rho_probs = computational_basis_probs(rho_ab)
    sigma_probs = computational_basis_probs(sigma)
    dh_val, subset, beta = hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon=epsilon)
    return {
        "rho_a": rho_a,
        "rho_b": rho_b,
        "sigma_product": sigma,
        "d_max": dmax_val,
        "d_min": dmin_val,
        "d_h_eps_commuting_proxy": dh_val,
        "d_h_eps_subset": subset,
        "beta_eps": beta,
        "negativity": negativity(rho_ab),
    }


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

    prod = packet_metrics(product_packet())
    results["tests"].append({
        "name": "product_bridge_zero_one_shot_correlation",
        "d_max": prod["d_max"],
        "d_min": prod["d_min"],
        "d_h_eps_commuting_proxy": prod["d_h_eps_commuting_proxy"],
        "pass": abs(prod["d_max"]) < 1e-8 and abs(prod["d_min"]) < 1e-8 and abs(prod["d_h_eps_commuting_proxy"]) < 1e-8,
    })

    sep = packet_metrics(separable_packet())
    results["tests"].append({
        "name": "separable_bridge_positive_correlation_without_negativity",
        "d_max": sep["d_max"],
        "d_min": sep["d_min"],
        "d_h_eps_commuting_proxy": sep["d_h_eps_commuting_proxy"],
        "negativity": sep["negativity"],
        "pass": sep["d_max"] > 0.0 and sep["d_min"] > 0.0 and sep["d_h_eps_commuting_proxy"] > 0.0 and abs(sep["negativity"]) < 1e-8,
    })

    bell = packet_metrics(bell_packet())
    results["tests"].append({
        "name": "bell_bridge_exceeds_separable_in_one_shot_correlation",
        "bell_d_max": bell["d_max"],
        "bell_d_min": bell["d_min"],
        "sep_d_max": sep["d_max"],
        "sep_d_min": sep["d_min"],
        "pass": bell["d_max"] > sep["d_max"] and bell["d_min"] > sep["d_min"] and bell["negativity"] > 0.0,
    })

    werner_low = packet_metrics(werner_packet(0.2))
    werner_high = packet_metrics(werner_packet(0.8))
    results["tests"].append({
        "name": "werner_like_strength_tracks_mixture_parameter",
        "d_max_low": werner_low["d_max"],
        "d_max_high": werner_high["d_max"],
        "d_h_low": werner_low["d_h_eps_commuting_proxy"],
        "d_h_high": werner_high["d_h_eps_commuting_proxy"],
        "pass": werner_high["d_max"] > werner_low["d_max"] and werner_high["d_h_eps_commuting_proxy"] >= werner_low["d_h_eps_commuting_proxy"],
    })

    hist = [packet_metrics(pkt) for pkt in history_packets()]
    positive_history = sum(int(m["d_max"] > 0.0) for m in hist)
    results["tests"].append({
        "name": "history_derived_bridges_are_finite_and_nontrivial",
        "d_max_values": [m["d_max"] for m in hist],
        "d_min_values": [m["d_min"] for m in hist],
        "pass": all(math.isfinite(m["d_max"]) and math.isfinite(m["d_min"]) for m in hist) and positive_history >= 2,
    })

    bell_packet_metrics = packet_metrics(bell_packet())
    sigma = bell_packet_metrics["sigma_product"]
    curve = []
    for eps in [0.0, 0.1, 0.25, 0.5, 1.0]:
        rho_eps = smooth_toward_reference(bell_packet()["rho_ab"], sigma, eps)
        curve.append({"eps": eps, "d_max": d_max(rho_eps, sigma)})
    monotone = all(curve[i]["d_max"] >= curve[i + 1]["d_max"] - 1e-9 for i in range(len(curve) - 1))
    results["tests"].append({
        "name": "smoothing_toward_product_reference_reduces_dmax",
        "curve": curve,
        "pass": monotone and abs(curve[-1]["d_max"]) < 1e-8,
    })

    return results


def run_negative_tests():
    results = {"tests": []}

    ok_invalid, msg_invalid = validate_density_matrix(invalid_packet()["rho_ab"])
    results["tests"].append({
        "name": "reject_invalid_bridge_state",
        "message": msg_invalid,
        "pass": not ok_invalid,
    })

    counterfeit = counterfeit_packet()
    valid_counterfeit, _ = validate_density_matrix(normalize_density(counterfeit["rho_ab"]))
    rho_a_true = partial_trace_a(normalize_density(counterfeit["rho_ab"]))
    rho_b_true = partial_trace_b(normalize_density(counterfeit["rho_ab"]))
    mismatch = (
        torch.max(torch.abs(rho_a_true - counterfeit["claimed_rho_a"])).item() > 1e-6
        or torch.max(torch.abs(rho_b_true - counterfeit["claimed_rho_b"])).item() > 1e-6
    )
    results["tests"].append({
        "name": "counterfeit_coupling_breaks_claimed_marginals",
        "valid_after_normalization": valid_counterfeit,
        "pass": (not valid_counterfeit) or mismatch,
    })

    bell = bell_packet()["rho_ab"]
    sigma_singular = product_packet()["rho_ab"]
    results["tests"].append({
        "name": "support_violation_gives_infinite_dmax_and_dmin",
        "d_max_is_inf": math.isinf(d_max(bell, sigma_singular)),
        "d_min_is_inf": math.isinf(d_min(bell, sigma_singular)),
        "pass": math.isinf(d_max(bell, sigma_singular)) and math.isinf(d_min(bell, sigma_singular)),
    })

    try:
        hypothesis_testing_relative_entropy_commuting([0.25, 0.25, 0.25, 0.25], [0.25, 0.25, 0.25, 0.25], 1.0)
        eps_rejected = False
    except ValueError:
        eps_rejected = True
    results["tests"].append({
        "name": "reject_invalid_commuting_proxy_epsilon",
        "pass": eps_rejected,
    })

    return results


def run_boundary_tests():
    results = {"tests": []}

    werner_zero = packet_metrics(werner_packet(0.0))
    results["tests"].append({
        "name": "werner_zero_is_uncorrelated_against_product_reference",
        "d_max": werner_zero["d_max"],
        "d_min": werner_zero["d_min"],
        "d_h_eps_commuting_proxy": werner_zero["d_h_eps_commuting_proxy"],
        "pass": abs(werner_zero["d_max"]) < 1e-8 and abs(werner_zero["d_min"]) < 1e-8 and abs(werner_zero["d_h_eps_commuting_proxy"]) < 1e-8,
    })

    werner_sep = packet_metrics(werner_packet(1.0 / 3.0))
    results["tests"].append({
        "name": "werner_separability_boundary_keeps_correlation_without_entanglement_claim",
        "d_max": werner_sep["d_max"],
        "d_min": werner_sep["d_min"],
        "negativity": werner_sep["negativity"],
        "pass": werner_sep["d_max"] > 0.0 and werner_sep["negativity"] <= 1e-8,
    })

    bell = packet_metrics(bell_packet())
    results["tests"].append({
        "name": "bell_against_product_reference_has_exact_log4_one_shot_values",
        "d_max": bell["d_max"],
        "d_min": bell["d_min"],
        "expected": math.log(4.0),
        "pass": abs(bell["d_max"] - math.log(4.0)) < 1e-8 and abs(bell["d_min"] - math.log(4.0)) < 1e-8,
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
        "name": "bridge_finite_blocklength_cut_states",
        "probe": "bridge_finite_blocklength_cut_states",
        "purpose": (
            "Apply bounded one-shot / finite-blocklength cut quantities to bridge-built "
            "bipartite states before any final kernel closure claim"
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
                "Uses D_max, D_min, and a commuting measurement hypothesis-testing proxy "
                "on bridge-built cut states. No final Axis-0 closure claim."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_finite_blocklength_cut_states_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Positive: {p_pass} passed, {p_fail} failed")
    print(f"Negative: {n_pass} passed, {n_fail} failed")
    print(f"Boundary: {b_pass} passed, {b_fail} failed")
    print(f"ALL PASS: {results['summary']['all_pass']}")
    print(f"Results written to {out_path}")
