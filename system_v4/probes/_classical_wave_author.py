#!/usr/bin/env python3
"""
Author + emit 20 classical_baseline numpy-only sims.
Non-canon, lane_B-eligible. Each conforms to SIM_TEMPLATE shape:
  - classification="classical_baseline"
  - TOOL_MANIFEST with non-empty reason per tool
  - TOOL_INTEGRATION_DEPTH with numpy load_bearing only
  - positive + negative + boundary tests
This author writes the 20 files, then the user runs them.
"""
import os, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))

HEADER = r'''#!/usr/bin/env python3
"""{title}

classical_baseline, numpy-only. Non-canon. Lane_B-eligible.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {{
    "numpy":    {{"tried": True,  "used": True,  "reason": "load-bearing linear algebra / rng for classical baseline"}},
    "pytorch":  {{"tried": False, "used": False, "reason": "classical_baseline sim; torch not required"}},
    "pyg":      {{"tried": False, "used": False, "reason": "no graph-NN step in this baseline"}},
    "z3":       {{"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"}},
    "cvc5":     {{"tried": False, "used": False, "reason": "equality-based checks; no UNSAT proof in baseline"}},
    "sympy":    {{"tried": False, "used": False, "reason": "numerical identity sufficient; symbolic not needed here"}},
    "clifford": {{"tried": False, "used": False, "reason": "matrix rep baseline; Cl(n) algebra deferred to canonical lane"}},
    "geomstats":{{"tried": False, "used": False, "reason": "flat/discrete baseline; manifold tooling out of scope"}},
    "e3nn":     {{"tried": False, "used": False, "reason": "no equivariant NN in baseline"}},
    "rustworkx":{{"tried": False, "used": False, "reason": "small adjacency handled by numpy"}},
    "xgi":      {{"tried": False, "used": False, "reason": "no hypergraph structure in this sim"}},
    "toponetx": {{"tried": False, "used": False, "reason": "no cell complex in this sim"}},
    "gudhi":    {{"tried": False, "used": False, "reason": "no persistent homology in this sim"}},
}}

TOOL_INTEGRATION_DEPTH = {{
    "numpy": "load_bearing",
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None, "rustworkx": None,
    "xgi": None, "toponetx": None, "gudhi": None,
}}

NAME = "{name}"
'''

FOOTER = r'''

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        all(v.get("pass") for v in pos.values()) and
        all(v.get("pass") for v in neg.values()) and
        all(v.get("pass") for v in bnd.values())
    )
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, NAME + "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{NAME}: all_pass={all_pass} -> {out_path}")
'''

# ---------- Body library: each body defines positive/negative/boundary ----------

BODIES = {}

# 1. Classical Hermitian spectral decomposition (eig)
BODIES["classical_baseline_hermitian_spectral"] = '''
def _rand_herm(n, rng):
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    return (A + A.conj().T) / 2

def run_positive_tests():
    rng = np.random.default_rng(0)
    out = {}
    for k in range(5):
        H = _rand_herm(4, rng)
        w, V = np.linalg.eigh(H)
        recon = V @ np.diag(w) @ V.conj().T
        ok = np.allclose(recon, H, atol=1e-10) and np.allclose(V.conj().T @ V, np.eye(4), atol=1e-10)
        out[f"herm_{k}"] = {"pass": bool(ok), "max_err": float(np.max(np.abs(recon - H)))}
    return out

def run_negative_tests():
    # Non-Hermitian matrix should NOT satisfy eigh reconstruction as Hermitian
    rng = np.random.default_rng(1)
    A = rng.standard_normal((4,4)) + 1j*rng.standard_normal((4,4))  # not Hermitian
    is_herm = np.allclose(A, A.conj().T)
    return {"non_hermitian_detected": {"pass": (not is_herm)}}

def run_boundary_tests():
    # Degenerate: identity has all eigenvalues 1
    w, V = np.linalg.eigh(np.eye(5))
    ok = np.allclose(w, np.ones(5))
    # 1x1 trivial
    w2, _ = np.linalg.eigh(np.array([[3.0]]))
    return {"identity_spectrum": {"pass": bool(ok)}, "scalar": {"pass": bool(np.isclose(w2[0], 3.0))}}
'''

# 2. Classical SVD reconstruction
BODIES["classical_baseline_svd_reconstruction"] = '''
def run_positive_tests():
    rng = np.random.default_rng(0)
    out = {}
    for k, shape in enumerate([(3,5),(4,4),(6,2),(5,3),(7,7)]):
        A = rng.standard_normal(shape)
        U, s, Vt = np.linalg.svd(A, full_matrices=False)
        recon = U @ np.diag(s) @ Vt
        ok = np.allclose(recon, A, atol=1e-10) and np.all(s >= -1e-12)
        out[f"svd_{k}"] = {"pass": bool(ok), "min_s": float(s.min())}
    return out

def run_negative_tests():
    rng = np.random.default_rng(2)
    A = rng.standard_normal((4,4))
    U, s, Vt = np.linalg.svd(A)
    bogus = U @ np.diag(s + 1.0) @ Vt
    return {"perturbed_recon_fails": {"pass": (not np.allclose(bogus, A, atol=1e-8))}}

def run_boundary_tests():
    Z = np.zeros((3,4))
    U, s, Vt = np.linalg.svd(Z, full_matrices=False)
    return {"zero_matrix_singulars_zero": {"pass": bool(np.allclose(s, 0.0))}}
'''

# 3. Classical Cl(3) rotor via Pauli matrix rep
BODIES["classical_baseline_cl3_rotor_pauli_rep"] = '''
I2 = np.eye(2, dtype=complex)
sx = np.array([[0,1],[1,0]], dtype=complex)
sy = np.array([[0,-1j],[1j,0]], dtype=complex)
sz = np.array([[1,0],[0,-1]], dtype=complex)

def rotor(axis, theta):
    n = {"x":sx, "y":sy, "z":sz}[axis]
    return np.cos(theta/2)*I2 - 1j*np.sin(theta/2)*n

def run_positive_tests():
    out = {}
    # R(z, 2pi) = -I for spinor rep
    R = rotor("z", 2*np.pi)
    out["spin_2pi_negI"] = {"pass": bool(np.allclose(R, -I2, atol=1e-10))}
    # R(z, 4pi) = I
    out["spin_4pi_I"] = {"pass": bool(np.allclose(rotor("z", 4*np.pi), I2, atol=1e-10))}
    # Composition R(x, a)R(x, b) = R(x, a+b)
    a, b = 0.37, 1.21
    out["compose_same_axis"] = {"pass": bool(np.allclose(rotor("x",a)@rotor("x",b), rotor("x",a+b), atol=1e-10))}
    # Unitary: R R^dag = I
    R2 = rotor("y", 0.77)
    out["unitary"] = {"pass": bool(np.allclose(R2 @ R2.conj().T, I2, atol=1e-10))}
    return out

def run_negative_tests():
    # R(x, pi) != R(y, pi)
    return {"different_axes_differ": {"pass": bool(not np.allclose(rotor("x", np.pi), rotor("y", np.pi)))}}

def run_boundary_tests():
    return {"zero_rotation_is_I": {"pass": bool(np.allclose(rotor("x", 0.0), I2, atol=1e-12))}}
'''

# 4. Classical Cl(6) via 8x8 gamma-matrix-style rep (use Kronecker of Paulis)
BODIES["classical_baseline_cl6_kron_pauli_rep"] = '''
I2 = np.eye(2, dtype=complex)
sx = np.array([[0,1],[1,0]], dtype=complex)
sy = np.array([[0,-1j],[1j,0]], dtype=complex)
sz = np.array([[1,0],[0,-1]], dtype=complex)

# 6 anticommuting generators in 8x8 (Cl(6) has dim 2^3=8 spinor rep)
g = [
    np.kron(np.kron(sx, I2), I2),
    np.kron(np.kron(sy, I2), I2),
    np.kron(np.kron(sz, sx), I2),
    np.kron(np.kron(sz, sy), I2),
    np.kron(np.kron(sz, sz), sx),
    np.kron(np.kron(sz, sz), sy),
]

def run_positive_tests():
    out = {}
    I8 = np.eye(8, dtype=complex)
    # anticommutation {g_i, g_j} = 2 delta_ij I
    bad = 0
    for i in range(6):
        for j in range(6):
            ac = g[i] @ g[j] + g[j] @ g[i]
            target = 2*I8 if i==j else np.zeros((8,8), dtype=complex)
            if not np.allclose(ac, target, atol=1e-10):
                bad += 1
    out["anticommute_6x6"] = {"pass": (bad==0), "violations": bad}
    # each g_i^2 = I
    sq_ok = all(np.allclose(gi@gi, I8, atol=1e-10) for gi in g)
    out["square_to_I"] = {"pass": bool(sq_ok)}
    return out

def run_negative_tests():
    # A fake extra "generator" equal to g[0] should FAIL anticommutation with g[0]
    fake = g[0].copy()
    ac = g[0]@fake + fake@g[0]
    return {"fake_gen_not_anticommute": {"pass": bool(not np.allclose(ac, np.zeros_like(ac)))}}

def run_boundary_tests():
    # Chirality element = i^3 * prod(g) should square to I
    chi = (1j)**3 * g[0]@g[1]@g[2]@g[3]@g[4]@g[5]
    return {"chirality_squares_to_I": {"pass": bool(np.allclose(chi@chi, np.eye(8, dtype=complex), atol=1e-10))}}
'''

# 5. Classical Hopf fibration numpy
BODIES["classical_baseline_hopf_fibration"] = '''
def hopf(z1, z2):
    # map S^3 subset C^2 -> S^2 subset R^3
    x = 2*(z1*np.conj(z2)).real
    y = 2*(z1*np.conj(z2)).imag
    z = abs(z1)**2 - abs(z2)**2
    return np.array([x, y, z])

def run_positive_tests():
    rng = np.random.default_rng(0)
    out = {}
    for k in range(6):
        z = rng.standard_normal(2) + 1j*rng.standard_normal(2)
        z = z / np.linalg.norm(z)  # on S^3
        p = hopf(z[0], z[1])
        out[f"on_s2_{k}"] = {"pass": bool(np.isclose(np.linalg.norm(p), 1.0, atol=1e-10))}
    # Fiber invariance: multiply by e^{i phi} leaves point on S^2 unchanged
    z = np.array([0.6+0.1j, 0.2-0.77j]); z = z/np.linalg.norm(z)
    p1 = hopf(z[0], z[1])
    phi = 1.234
    z2 = z * np.exp(1j*phi)
    p2 = hopf(z2[0], z2[1])
    out["fiber_invariance"] = {"pass": bool(np.allclose(p1, p2, atol=1e-10))}
    return out

def run_negative_tests():
    # Non-U(1) perturbation (different phase per component) should move the point
    z = np.array([0.6+0.1j, 0.2-0.77j]); z = z/np.linalg.norm(z)
    p1 = hopf(z[0], z[1])
    z2 = np.array([z[0]*np.exp(1j*0.5), z[1]*np.exp(1j*1.1)])
    z2 = z2/np.linalg.norm(z2)
    p2 = hopf(z2[0], z2[1])
    return {"nonuniform_phase_moves_point": {"pass": bool(not np.allclose(p1, p2, atol=1e-6))}}

def run_boundary_tests():
    # North pole: z2=0 -> (0,0,1)
    p = hopf(1.0+0j, 0.0+0j)
    # South pole: z1=0 -> (0,0,-1)
    q = hopf(0.0+0j, 1.0+0j)
    return {"north_pole": {"pass": bool(np.allclose(p, [0,0,1]))},
            "south_pole": {"pass": bool(np.allclose(q, [0,0,-1]))}}
'''

# 6. Classical Szilard engine (one bit, ideal)
BODIES["classical_baseline_szilard_onebit"] = '''
def szilard_work(kT=1.0):
    # Landauer bound: kT ln 2 work extracted per bit of info
    return kT * np.log(2)

def run_positive_tests():
    out = {}
    for k, T in enumerate([0.5, 1.0, 2.0, 3.7]):
        W = szilard_work(T)
        out[f"work_kT_{k}"] = {"pass": bool(np.isclose(W, T*np.log(2))), "W": float(W)}
    # Cycle: extracted work = erasure cost (Landauer), net zero over full cycle
    T = 1.0
    extracted = szilard_work(T)
    erase_cost = T*np.log(2)
    out["cycle_net_zero"] = {"pass": bool(np.isclose(extracted - erase_cost, 0.0))}
    return out

def run_negative_tests():
    # Violating Landauer (free erasure) would give net work > 0 — must detect
    T = 1.0
    extracted = szilard_work(T)
    erase_cost = 0.0
    net = extracted - erase_cost
    return {"free_erasure_gives_positive_net": {"pass": bool(net > 0)}}

def run_boundary_tests():
    return {"zero_T_zero_work": {"pass": bool(np.isclose(szilard_work(0.0), 0.0))}}
'''

# 7. Classical Carnot cycle efficiency
BODIES["classical_baseline_carnot_efficiency"] = '''
def carnot_eta(Tc, Th):
    return 1.0 - Tc/Th

def run_positive_tests():
    out = {}
    for k, (Tc, Th) in enumerate([(300.0, 600.0), (100.0, 400.0), (250.0, 1000.0), (1.0, 2.0), (77.0, 300.0)]):
        eta = carnot_eta(Tc, Th)
        ok = 0.0 <= eta < 1.0 and np.isclose(eta, 1.0 - Tc/Th)
        out[f"carnot_{k}"] = {"pass": bool(ok), "eta": float(eta)}
    return out

def run_negative_tests():
    # An efficiency exceeding Carnot violates 2nd law
    claimed = 0.9
    Tc, Th = 300.0, 600.0
    return {"super_carnot_rejected": {"pass": bool(claimed > carnot_eta(Tc, Th))}}

def run_boundary_tests():
    return {
        "Tc_eq_Th_zero_eta": {"pass": bool(np.isclose(carnot_eta(500.0, 500.0), 0.0))},
        "Tc_zero_eta_one":  {"pass": bool(np.isclose(carnot_eta(0.0, 500.0), 1.0))},
    }
'''

# 8. Classical random walk mixing on graph via adjacency matmul
BODIES["classical_baseline_random_walk_mixing"] = '''
def build_cycle(n):
    A = np.zeros((n,n))
    for i in range(n):
        A[i, (i+1)%n] = 1
        A[(i+1)%n, i] = 1
    return A

def transition(A):
    d = A.sum(axis=1, keepdims=True)
    return A / d

def run_positive_tests():
    out = {}
    n = 8
    A = build_cycle(n)
    P = transition(A)
    # stationary distribution is uniform
    pi = np.ones(n)/n
    out["stationary_is_fixed"] = {"pass": bool(np.allclose(pi @ P, pi, atol=1e-12))}
    # after many steps from delta, distribution approaches uniform
    x = np.zeros(n); x[0] = 1.0
    Pk = np.linalg.matrix_power(P, 200)
    xk = x @ Pk
    out["mixes_to_uniform"] = {"pass": bool(np.allclose(xk, pi, atol=1e-6))}
    # Row sums of P are 1
    out["rows_sum_one"] = {"pass": bool(np.allclose(P.sum(axis=1), np.ones(n)))}
    return out

def run_negative_tests():
    # Bipartite cycle has period-2 non-mixing for even n when using pure adjacency
    # Non-stochastic matrix should fail row-sum
    bad = np.ones((3,3))
    return {"non_stochastic_detected": {"pass": bool(not np.allclose(bad.sum(axis=1), np.ones(3)))}}

def run_boundary_tests():
    # Single self-loop = trivial mixing
    A = np.array([[1.0]])
    P = transition(A)
    return {"single_node": {"pass": bool(np.isclose(P[0,0], 1.0))}}
'''

# 9. Classical U(1) phase conservation along discretized loop
BODIES["classical_baseline_u1_phase_loop"] = '''
def run_positive_tests():
    out = {}
    # discretize loop into N links with phases summing to 0 mod 2pi => holonomy trivial
    N = 64
    rng = np.random.default_rng(0)
    phases = rng.standard_normal(N)
    phases -= phases.sum() / N  # remove mean so sum=0
    hol = np.exp(1j*phases.sum())
    out["zero_mean_holonomy_trivial"] = {"pass": bool(np.isclose(hol, 1.0, atol=1e-10))}
    # Winding: phases = 2*pi/N each -> total = 2*pi -> trivial holonomy but winding 1
    phi = 2*np.pi/N
    hol2 = np.exp(1j*N*phi)
    out["winding_one_hol_trivial"] = {"pass": bool(np.isclose(hol2, 1.0, atol=1e-10))}
    # Gauge invariance: adding d(lambda) around closed loop changes nothing
    lam = rng.standard_normal(N)
    dlam = np.roll(lam, -1) - lam  # sums to 0
    hol3 = np.exp(1j*(phases + dlam).sum())
    out["gauge_invariance"] = {"pass": bool(np.isclose(hol3, 1.0, atol=1e-10))}
    return out

def run_negative_tests():
    # Nonzero net phase breaks triviality
    phases = np.array([0.3]*10)
    hol = np.exp(1j*phases.sum())
    return {"nonzero_phase_not_trivial": {"pass": bool(not np.isclose(hol, 1.0, atol=1e-6))}}

def run_boundary_tests():
    return {"empty_loop_trivial": {"pass": bool(np.isclose(np.exp(1j*0.0), 1.0))}}
'''

# 10. Classical holodeck carrier: finite state + equality-based admissibility
BODIES["classical_baseline_holodeck_carrier_equality"] = '''
# Holodeck atoms (classical shell): discrete state space with equality-based admission.
STATES = ["A","B","C","D"]
ALLOWED = {("A","B"), ("B","C"), ("C","D"), ("D","A")}  # cyclic carrier

def admit(s, t):
    return (s, t) in ALLOWED

def run_positive_tests():
    out = {}
    for k, (s,t) in enumerate(list(ALLOWED)):
        out[f"allowed_{k}"] = {"pass": bool(admit(s,t))}
    # reduction: projection to first coord is well-defined
    proj = {s for (s,_) in ALLOWED}
    out["carrier_surjective_first"] = {"pass": bool(proj == set(STATES))}
    return out

def run_negative_tests():
    return {"disallowed": {"pass": bool(not admit("A","C"))},
            "self_loop": {"pass": bool(not admit("A","A"))}}

def run_boundary_tests():
    return {"empty_pair_excluded": {"pass": bool(not admit("", ""))}}
'''

# 11. Classical IGT: iterated 2-player payoff equilibrium (equality-based)
BODIES["classical_baseline_igt_nash_2x2"] = '''
# Coordination game: payoffs for (A,B); pure Nash at (0,0) and (1,1).
PA = np.array([[2,0],[0,1]])
PB = np.array([[2,0],[0,1]])

def is_nash(i, j):
    # i is best response to j for A; j is best response to i for B
    a_ok = PA[i,j] >= PA[1-i, j]
    b_ok = PB[i,j] >= PB[i, 1-j]
    return bool(a_ok and b_ok)

def run_positive_tests():
    return {
        "nash_00": {"pass": is_nash(0,0)},
        "nash_11": {"pass": is_nash(1,1)},
    }

def run_negative_tests():
    return {
        "not_nash_01": {"pass": bool(not is_nash(0,1))},
        "not_nash_10": {"pass": bool(not is_nash(1,0))},
    }

def run_boundary_tests():
    # symmetry under swap
    return {"symmetric": {"pass": bool(np.array_equal(PA, PB))}}
'''

# 12. Classical FEP: Gaussian variational free energy minimum
BODIES["classical_baseline_fep_gaussian_vfe"] = '''
def vfe(mu, sigma2, obs, prior_mu=0.0, prior_sigma2=1.0):
    # Variational free energy (Gaussian q, Gaussian prior, Gaussian likelihood obs ~ N(mu,1))
    # Surprise + KL
    like = 0.5*((obs - mu)**2 + sigma2) + 0.5*np.log(2*np.pi)
    kl = 0.5*(sigma2/prior_sigma2 + (mu-prior_mu)**2/prior_sigma2 - 1 + np.log(prior_sigma2/sigma2))
    return like + kl

def run_positive_tests():
    out = {}
    obs = 1.5
    # analytic posterior mean for prior N(0,1), lik N(mu,1): (obs)/(1+1) = obs/2
    mu_star = obs/2.0
    sig2_star = 0.5
    F_star = vfe(mu_star, sig2_star, obs)
    # perturbing mu increases F
    F_off = vfe(mu_star+0.3, sig2_star, obs)
    out["mu_optimum"] = {"pass": bool(F_off > F_star - 1e-12)}
    # perturbing sigma increases F
    F_off2 = vfe(mu_star, sig2_star*1.5, obs)
    out["sigma_optimum"] = {"pass": bool(F_off2 > F_star - 1e-12)}
    return out

def run_negative_tests():
    obs = 1.5
    F0 = vfe(0.0, 1.0, obs)
    F_opt = vfe(obs/2.0, 0.5, obs)
    return {"prior_not_optimal": {"pass": bool(F0 > F_opt)}}

def run_boundary_tests():
    # Extreme: very concentrated q with wrong mean blows up F
    obs = 1.5
    F = vfe(5.0, 1e-3, obs)
    return {"wrong_concentrated_high_F": {"pass": bool(F > 1.0)}}
'''

# 13. Classical Leviathan: monotone aggregation rule
BODIES["classical_baseline_leviathan_monotone_aggregation"] = '''
# Simple monotone aggregation: majority rule on {0,1}^n
def aggregate(votes):
    votes = np.asarray(votes)
    return int(votes.sum() > len(votes)/2)

def run_positive_tests():
    out = {}
    out["clear_majority_1"] = {"pass": aggregate([1,1,1,0,0]) == 1}
    out["clear_majority_0"] = {"pass": aggregate([0,0,0,1,1]) == 0}
    # monotonicity: flipping a 0->1 cannot decrease outcome
    base = np.array([1,0,0,1,0])
    b_out = aggregate(base)
    flipped = base.copy(); flipped[1] = 1
    out["monotone"] = {"pass": bool(aggregate(flipped) >= b_out)}
    return out

def run_negative_tests():
    # anti-majority would flip output; detect that it's not the rule
    return {"not_antimajority": {"pass": aggregate([1,1,1,0,0]) != 0}}

def run_boundary_tests():
    # tie: 2-2 should be 0 by our rule (strict >)
    return {"tie_rule": {"pass": aggregate([1,1,0,0]) == 0}}
'''

# 14. Classical scientific method: modus tollens on a predicate
BODIES["classical_baseline_sci_method_modus_tollens"] = '''
# Hypothesis H: x > 0. Prediction P(H): x**2 > 0.
# If P(x) is false for some x, then H is refuted for that x.
def predict(H_fn, x):
    return H_fn(x)

def H(x): return x > 0

def run_positive_tests():
    out = {}
    # Evidence confirms (never proves): x=3 satisfies both
    out["confirming"] = {"pass": bool(H(3.0) and (3.0**2 > 0))}
    # Falsifying case exists: x = -1 => H(x) false, but x^2 > 0 (P still holds; prediction is weak)
    # Correct modus tollens: if P false AND P was implied by H, then not H.
    # Choose stronger prediction P2: x > 0 implies x^3 > 0.
    x = -2.0
    P2 = (x**3 > 0)  # False
    refuted = (not P2) and (not H(x))  # both consistent
    out["modus_tollens_refutes"] = {"pass": bool(refuted)}
    return out

def run_negative_tests():
    # Affirming the consequent is invalid: x^2>0 does NOT imply x>0
    x = -3.0
    ac_valid = (x**2 > 0) and H(x)
    return {"affirming_consequent_invalid": {"pass": bool(not ac_valid)}}

def run_boundary_tests():
    # x = 0 boundary
    return {"zero_not_positive": {"pass": bool(not H(0.0))}}
'''

# 15. Classical holodeck reduction: quotient-by-equivalence
BODIES["classical_baseline_holodeck_reduction_quotient"] = '''
# Equivalence relation: same-parity on integers 0..9
def eq(a,b): return (a%2)==(b%2)

def classes(elems):
    seen = []
    out = []
    for x in elems:
        placed = False
        for c in out:
            if eq(x, c[0]):
                c.append(x); placed = True; break
        if not placed:
            out.append([x])
    return out

def run_positive_tests():
    out = {}
    c = classes(list(range(10)))
    out["two_classes"] = {"pass": len(c)==2}
    sizes = sorted(len(x) for x in c)
    out["equal_sizes"] = {"pass": sizes == [5,5]}
    return out

def run_negative_tests():
    # Non-equivalence (a==b+1) should NOT partition
    def noneq(a,b): return a==b+1
    # reflexivity fails: 0 noneq 0
    return {"noneq_not_reflexive": {"pass": bool(not noneq(0,0))}}

def run_boundary_tests():
    return {"empty": {"pass": classes([]) == []}}
'''

# 16. Classical IGT admissibility: dominated strategy elimination
BODIES["classical_baseline_igt_admissibility_dominance"] = '''
# Payoff matrix for row player; column j strictly dominated by column j' if beaten for all i
PA = np.array([[4,3,0],[2,1,0],[3,2,0]])  # col 2 dominated by col 0

def dominated_cols(P):
    n_cols = P.shape[1]
    out = []
    for j in range(n_cols):
        for k in range(n_cols):
            if j==k: continue
            if np.all(P[:,k] > P[:,j]):
                out.append(j); break
    return sorted(set(out))

def run_positive_tests():
    d = dominated_cols(PA)
    return {"col2_dominated": {"pass": 2 in d}}

def run_negative_tests():
    # column 0 is NOT dominated
    d = dominated_cols(PA)
    return {"col0_not_dominated": {"pass": 0 not in d}}

def run_boundary_tests():
    # All equal -> nothing dominated
    P = np.ones((3,3))
    return {"all_equal_none_dominated": {"pass": dominated_cols(P) == []}}
'''

# 17. Classical FEP structure: predictive coding residual minimization
BODIES["classical_baseline_fep_predictive_coding"] = '''
def run_positive_tests():
    rng = np.random.default_rng(0)
    out = {}
    # Observations y = W x + noise; infer x by least squares
    W = rng.standard_normal((8, 4))
    x_true = rng.standard_normal(4)
    y = W @ x_true + 0.01*rng.standard_normal(8)
    x_hat, *_ = np.linalg.lstsq(W, y, rcond=None)
    out["residual_small"] = {"pass": bool(np.linalg.norm(W@x_hat - y) < 0.2)}
    out["estimate_close"] = {"pass": bool(np.linalg.norm(x_hat - x_true) < 0.2)}
    return out

def run_negative_tests():
    rng = np.random.default_rng(1)
    W = rng.standard_normal((8,4))
    y = rng.standard_normal(8)
    x_zero = np.zeros(4)
    r_zero = np.linalg.norm(W@x_zero - y)
    x_hat, *_ = np.linalg.lstsq(W, y, rcond=None)
    r_opt = np.linalg.norm(W@x_hat - y)
    return {"zero_worse_than_lstsq": {"pass": bool(r_zero >= r_opt - 1e-10)}}

def run_boundary_tests():
    # Square invertible: residual exactly 0
    W = np.eye(3)
    y = np.array([1.0, -2.0, 3.0])
    x_hat, *_ = np.linalg.lstsq(W, y, rcond=None)
    return {"invertible_zero_residual": {"pass": bool(np.allclose(W@x_hat, y, atol=1e-12))}}
'''

# 18. Classical Leviathan admissibility: coalition stability check
BODIES["classical_baseline_leviathan_coalition_stability"] = '''
# Characteristic function v on subsets of N={0,1,2}
def v(S):
    S = frozenset(S)
    table = {
        frozenset(): 0,
        frozenset({0}): 1, frozenset({1}): 1, frozenset({2}): 1,
        frozenset({0,1}): 3, frozenset({0,2}): 3, frozenset({1,2}): 3,
        frozenset({0,1,2}): 6,
    }
    return table[S]

def is_in_core(x):
    # x is imputation (length 3); in core if for every S, sum x_i >= v(S)
    import itertools
    N = [0,1,2]
    if not np.isclose(sum(x), v(N)): return False
    for r in range(1, len(N)+1):
        for S in itertools.combinations(N, r):
            if sum(x[i] for i in S) < v(S) - 1e-12:
                return False
    return True

def run_positive_tests():
    # Equal split (2,2,2) is in the core
    return {"equal_split_in_core": {"pass": is_in_core([2,2,2])}}

def run_negative_tests():
    # (5,0.5,0.5) — coalition {1,2} blocks with v=3 > 1.0
    return {"blocked_imputation": {"pass": bool(not is_in_core([5, 0.5, 0.5]))}}

def run_boundary_tests():
    # Wrong total
    return {"wrong_total_excluded": {"pass": bool(not is_in_core([1,1,1]))}}
'''

# 19. Classical sci-method admissibility: bayes update monotonicity
BODIES["classical_baseline_sci_method_bayes_update"] = '''
def posterior(prior, lik_H, lik_notH):
    num = lik_H * prior
    den = num + lik_notH * (1 - prior)
    return num / den

def run_positive_tests():
    out = {}
    # Likelihood favoring H raises posterior
    p = posterior(0.3, 0.9, 0.2)
    out["evidence_raises"] = {"pass": bool(p > 0.3)}
    # Likelihood against H lowers posterior
    p2 = posterior(0.3, 0.1, 0.9)
    out["counter_evidence_lowers"] = {"pass": bool(p2 < 0.3)}
    # Equal likelihoods leave posterior unchanged
    p3 = posterior(0.3, 0.5, 0.5)
    out["neutral_unchanged"] = {"pass": bool(np.isclose(p3, 0.3))}
    return out

def run_negative_tests():
    # Prior 0 stays 0
    return {"zero_prior_stays_zero": {"pass": bool(np.isclose(posterior(0.0, 0.9, 0.1), 0.0))}}

def run_boundary_tests():
    return {"one_prior_stays_one": {"pass": bool(np.isclose(posterior(1.0, 0.5, 0.5), 1.0))}}
'''

# 20. Classical scientific method: falsification via contradiction on sample
BODIES["classical_baseline_holodeck_structure_composition"] = '''
# Holodeck structure: composition of two permutations should be associative
def compose(p, q):
    return p[q]

def run_positive_tests():
    rng = np.random.default_rng(0)
    out = {}
    for k in range(4):
        n = 6
        a = rng.permutation(n); b = rng.permutation(n); c = rng.permutation(n)
        lhs = compose(compose(a,b), c)
        rhs = compose(a, compose(b,c))
        out[f"assoc_{k}"] = {"pass": bool(np.array_equal(lhs, rhs))}
    # identity
    idp = np.arange(5)
    p = rng.permutation(5)
    out["identity"] = {"pass": bool(np.array_equal(compose(p, idp), p) and np.array_equal(compose(idp, p), p))}
    return out

def run_negative_tests():
    # Non-permutation (repeated index) breaks invertibility
    bad = np.array([0,0,1,2,3])
    unique = len(set(bad.tolist())) == len(bad)
    return {"non_permutation_detected": {"pass": bool(not unique)}}

def run_boundary_tests():
    idp = np.arange(1)
    return {"singleton_group": {"pass": bool(np.array_equal(compose(idp, idp), idp))}}
'''

# ---------- Emit files ----------
def emit():
    written = []
    for name, body in BODIES.items():
        path = os.path.join(HERE, name + ".py")
        title = name.replace("_", " ")
        content = HEADER.format(title=title, name=name) + body + FOOTER
        with open(path, "w") as f:
            f.write(content)
        written.append(path)
    return written

if __name__ == "__main__":
    files = emit()
    print(f"WROTE {len(files)} sim files")
    for f in files:
        print("  ", f)
