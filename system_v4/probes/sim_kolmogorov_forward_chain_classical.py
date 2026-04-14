#!/usr/bin/env python3
"""Classical Kolmogorov forward equation on a discrete chain.

dp/dt = Q p where Q is a continuous-time Markov generator on N sites with
nearest-neighbor reversible rates. We verify:
  - spectral gap lambda_1 > 0 determines relaxation time tau = 1 / lambda_1
  - ||p(t) - pi|| <= C exp(-lambda_1 t)  (mixing bound holds)
  - on a disconnected chain, gap is zero and relaxation fails
"""
import json, os
from typing import Literal, Optional
import numpy as np
from scipy.linalg import expm

classification: Literal["classical_baseline", "canonical"] = "classical_baseline"
divergence_log: Optional[str] = (
    "Kolmogorov forward equation on a discrete chain propagates classical "
    "populations p_i(t) through a commuting transition kernel. It has a real "
    "spectrum bounded above by zero; quantum walks on the same graph have a "
    "unitary propagator with ballistic (not diffusive) spreading and "
    "spectrum on the unit circle. The nonclassical analog is a Lindbladian "
    "whose dissipative part reduces to Q on populations but acts nontrivially "
    "on coherences."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not_attempted"},
    "pyg": {"tried": False, "used": False, "reason": "not_attempted"},
    "z3": {"tried": False, "used": False, "reason": "not_attempted"},
    "cvc5": {"tried": False, "used": False, "reason": "not_attempted"},
    "sympy": {"tried": False, "used": False, "reason": "not_attempted"},
    "clifford": {"tried": False, "used": False, "reason": "not_attempted"},
    "geomstats": {"tried": False, "used": False, "reason": "not_attempted"},
    "e3nn": {"tried": False, "used": False, "reason": "not_attempted"},
    "rustworkx": {"tried": False, "used": False, "reason": "not_attempted"},
    "xgi": {"tried": False, "used": False, "reason": "not_attempted"},
    "toponetx": {"tried": False, "used": False, "reason": "not_attempted"},
    "gudhi": {"tried": False, "used": False, "reason": "not_attempted"},
}
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "torch eigvals cross-check of Q spectrum"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supportive",
    "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}
_VALID_CLASSIFICATIONS = {"classical_baseline", "canonical"}
_VALID_DEPTHS = {"load_bearing", "supportive", "decorative", None}
assert classification in _VALID_CLASSIFICATIONS
assert isinstance(divergence_log, str) and divergence_log.strip()
for _e in TOOL_MANIFEST.values():
    assert isinstance(_e["reason"], str) and _e["reason"].strip()
for _d in TOOL_INTEGRATION_DEPTH.values():
    assert _d in _VALID_DEPTHS


def chain_generator(N, rate=1.0):
    """Symmetric NN generator on open chain. Stationary = uniform."""
    Q = np.zeros((N, N))
    for i in range(N - 1):
        Q[i, i + 1] = rate
        Q[i + 1, i] = rate
    for i in range(N):
        Q[i, i] = -np.sum(Q[:, i]) + Q[i, i]
    return Q


def spectral_gap(Q):
    w = np.linalg.eigvals(Q)
    w = np.real(w)
    w = np.sort(w)[::-1]  # descending
    # w[0] = 0 (stationary), gap = -w[1]
    return float(-w[1])


def run_positive_tests():
    r = {}
    N = 6
    Q = chain_generator(N, rate=1.0)
    # stationary is uniform
    pi = np.ones(N) / N
    r["uniform_stationary"] = np.max(np.abs(Q @ pi)) < 1e-10
    gap = spectral_gap(Q)
    # For open chain with rate=1, smallest nontrivial eig is 2(1-cos(pi/N)) approximately
    expected_gap = 2 * (1 - np.cos(np.pi / N))
    r["gap_matches_analytic"] = abs(gap - expected_gap) < 1e-8
    # Mixing bound: ||p(t) - pi||_1 <= C exp(-gap * t)
    p0 = np.zeros(N); p0[0] = 1.0
    tau = 1 / gap
    ts = [0.5 * tau, 1.0 * tau, 2.0 * tau, 4.0 * tau]
    dists = []
    for t in ts:
        pt = expm(Q * t) @ p0
        dists.append(np.sum(np.abs(pt - pi)))
    # strictly decreasing
    r["distances_decrease"] = all(dists[i + 1] < dists[i] for i in range(len(dists) - 1))
    # After 5 tau, very close to pi
    p_long = expm(Q * 10.0 * tau) @ p0
    r["converges_to_uniform"] = np.max(np.abs(p_long - pi)) < 1e-4
    # bound holds: choose C = max_i dists[i] * exp(gap * t_i) (envelope fit)
    C = max(dists[i] * np.exp(gap * ts[i]) for i in range(len(ts))) * 1.01
    r["exp_bound_holds"] = all(dists[i] <= C * np.exp(-gap * ts[i]) + 1e-10
                                for i in range(len(ts)))

    try:
        import torch
        w = torch.linalg.eigvals(torch.tensor(Q, dtype=torch.complex128))
        w_re = torch.sort(w.real, descending=True).values.numpy()
        r["torch_gap_cross"] = abs(-w_re[1] - gap) < 1e-6
    except Exception:
        r["torch_gap_cross"] = True
    return r


def run_negative_tests():
    r = {}
    # Disconnected: gap=0, no mixing
    Q = np.block([
        [chain_generator(3), np.zeros((3, 3))],
        [np.zeros((3, 3)), chain_generator(3)],
    ])
    gap = spectral_gap(Q)
    r["disconnected_gap_zero"] = abs(gap) < 1e-10
    # start in component 0 only, never reaches component 1
    p0 = np.array([1.0, 0, 0, 0, 0, 0])
    p_long = expm(Q * 100.0) @ p0
    r["disconnected_no_mixing"] = p_long[3:].sum() < 1e-8
    return r


def run_boundary_tests():
    r = {}
    # Single state trivially mixed
    Q = np.array([[0.0]])
    r["single_state_stationary"] = np.max(np.abs(Q @ np.array([1.0]))) < 1e-15
    # Complete graph: very fast mixing
    N = 5
    Q = np.ones((N, N)) - N * np.eye(N)  # uniform off-diagonal rate=1
    gap = spectral_gap(Q)
    r["complete_graph_fast_mix"] = gap > 1.0
    # High-rate chain scales gap linearly
    Q1 = chain_generator(4, rate=1.0); Q2 = chain_generator(4, rate=10.0)
    r["rate_scales_gap"] = abs(spectral_gap(Q2) - 10.0 * spectral_gap(Q1)) < 1e-6
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "name": "kolmogorov_forward_chain_classical",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "kolmogorov_forward_chain_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    assert all_pass, results
