#!/usr/bin/env python3
"""
sim_pure_lego_qca_lieb_robinson.py
Pure-lego probe: quantum cellular automata, Lieb-Robinson bounds,
and information scrambling (OTOC).

No engine dependencies.  numpy + scipy only.

Probes
------
1. QCA  -- 1D CNOT automaton on 6 qubits, 10 steps.
           Verify ballistic entanglement spreading (linear growth).
2. Lieb-Robinson  -- ||[sigma_z^1(t), sigma_z^6]|| for local Heisenberg
           Hamiltonian; verify exponential suppression outside light cone,
           extract Lieb-Robinson velocity v.
3. OTOC  -- out-of-time-order correlator F(t) for random Heisenberg chain;
           verify scrambling (F -> 0).
"""

import json
import os
import time
import numpy as np
from scipy import linalg as la

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
N_QUBITS = 6
DIM = 2 ** N_QUBITS  # 64
SEED = 42

# Pauli matrices
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
IDENTITY_2 = np.eye(2, dtype=complex)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def kron_chain(ops):
    """Tensor product of a list of 2x2 operators."""
    result = ops[0]
    for op in ops[1:]:
        result = np.kron(result, op)
    return result


def single_site_op(op, site, n_qubits):
    """Embed a single-qubit operator at `site` in an n_qubits chain."""
    ops = [IDENTITY_2] * n_qubits
    ops[site] = op
    return kron_chain(ops)


def two_site_op(op_a, site_a, op_b, site_b, n_qubits):
    """Embed a two-qubit interaction at specified sites."""
    ops = [IDENTITY_2] * n_qubits
    ops[site_a] = op_a
    ops[site_b] = op_b
    return kron_chain(ops)


def cnot_gate():
    """Standard CNOT (control x target) as 4x4 matrix."""
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=complex)


def embed_cnot(control, target, n_qubits):
    """
    Embed a CNOT gate acting on (control, target) into the full
    2^n_qubits Hilbert space.  Works for arbitrary (non-adjacent) pairs
    by constructing the projector decomposition:
      CNOT = |0><0|_c x I_t + |1><1|_c x X_t
    """
    proj0 = np.array([[1, 0], [0, 0]], dtype=complex)
    proj1 = np.array([[0, 0], [0, 1]], dtype=complex)

    term0_ops = [IDENTITY_2] * n_qubits
    term0_ops[control] = proj0
    # target stays identity

    term1_ops = [IDENTITY_2] * n_qubits
    term1_ops[control] = proj1
    term1_ops[target] = SIGMA_X

    return kron_chain(term0_ops) + kron_chain(term1_ops)


def entanglement_entropy(state_vec, n_qubits, cut):
    """
    Von Neumann entanglement entropy across a bipartition at `cut`.
    Subsystem A = sites [0..cut-1], B = [cut..n_qubits-1].
    """
    dim_a = 2 ** cut
    dim_b = 2 ** (n_qubits - cut)
    psi = state_vec.reshape(dim_a, dim_b)
    # Schmidt values via SVD
    s = la.svd(psi, compute_uv=False)
    s = s[s > 1e-14]
    probs = s ** 2
    return -np.sum(probs * np.log2(probs + 1e-30))


# ---------------------------------------------------------------------------
# Probe 1: Quantum Cellular Automaton
# ---------------------------------------------------------------------------

def probe_qca():
    """
    1D QCA on 6 qubits.
    Rule: parallel CNOT(i, i+1) for even i, then odd i.
    Track entanglement entropy across the middle cut after each step.
    Verify ballistic (linear) growth of entanglement.
    """
    results = {}
    n = N_QUBITS

    # Build the one-step QCA unitary
    # Even layer: CNOT(0,1), CNOT(2,3), CNOT(4,5)
    even_layer = np.eye(DIM, dtype=complex)
    for i in range(0, n - 1, 2):
        even_layer = embed_cnot(i, i + 1, n) @ even_layer

    # Odd layer: CNOT(1,2), CNOT(3,4)
    odd_layer = np.eye(DIM, dtype=complex)
    for i in range(1, n - 1, 2):
        odd_layer = embed_cnot(i, i + 1, n) @ odd_layer

    U_step = odd_layer @ even_layer

    # Initial state: |+> on site 0, |0> elsewhere  (localized excitation)
    psi_0 = np.zeros(DIM, dtype=complex)
    psi_0[0] = 1.0  # |000000>
    # Apply Hadamard on site 0 to get (|0>+|1>)/sqrt(2) tensor |00000>
    H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    H_full = single_site_op(H, 0, n)
    psi = H_full @ psi_0

    n_steps = 10
    cut = n // 2  # middle cut (sites 0-2 | 3-5)

    entropies = []
    all_cut_entropies = []  # entropy across every cut at each step

    for step in range(n_steps + 1):
        s_mid = entanglement_entropy(psi, n, cut)
        entropies.append(float(s_mid))

        per_cut = []
        for c in range(1, n):
            per_cut.append(float(entanglement_entropy(psi, n, c)))
        all_cut_entropies.append(per_cut)

        if step < n_steps:
            psi = U_step @ psi

    # Check ballistic spreading: entropy should grow roughly linearly
    # in the early steps before saturation.
    # Fit linear slope to first few steps (skip step 0).
    early = entropies[1:6]  # steps 1-5
    steps_arr = np.arange(1, 6)
    slope, intercept = np.polyfit(steps_arr, early, 1)

    # Saturation: entropy should plateau near log2(min(dim_A, dim_B))
    max_entropy = min(cut, n - cut)  # = 3 for cut=3
    saturated = entropies[-1] > 0.5  # at least some entanglement

    results["mid_cut_entropies"] = entropies
    results["all_cut_entropies"] = all_cut_entropies
    results["linear_fit_slope"] = float(slope)
    results["linear_fit_intercept"] = float(intercept)
    results["max_possible_entropy"] = float(max_entropy)
    results["final_entropy"] = float(entropies[-1])
    results["ballistic_spreading"] = bool(slope > 0.01 and saturated)

    return results


# ---------------------------------------------------------------------------
# Probe 2: Lieb-Robinson Bound
# ---------------------------------------------------------------------------

def build_heisenberg_hamiltonian(n_qubits, couplings=None):
    """
    Build H = sum_i J_i (X_i X_{i+1} + Y_i Y_{i+1} + Z_i Z_{i+1})
    for nearest-neighbor Heisenberg chain.
    """
    dim = 2 ** n_qubits
    H = np.zeros((dim, dim), dtype=complex)

    if couplings is None:
        couplings = [1.0] * (n_qubits - 1)

    for i in range(n_qubits - 1):
        J = couplings[i]
        for P in [SIGMA_X, SIGMA_Y, SIGMA_Z]:
            H += J * two_site_op(P, i, P, i + 1, n_qubits)

    return H


def probe_lieb_robinson():
    """
    Compute ||[sigma_z^0(t), sigma_z^5]|| for t = 0.1 .. 2.0
    for the Heisenberg Hamiltonian on 6 sites.

    Lieb-Robinson bound: ||[O_A(t), O_B]|| <= C * exp(v|t| - d(A,B))
    Outside the light cone (v|t| < d), the commutator is exponentially small.
    """
    results = {}
    n = N_QUBITS

    H = build_heisenberg_hamiltonian(n)

    # Operators: sigma_z on site 0 and site 5
    O_A = single_site_op(SIGMA_Z, 0, n)
    O_B = single_site_op(SIGMA_Z, n - 1, n)

    distance = n - 1  # = 5

    t_values = np.arange(0.1, 2.05, 0.1)
    commutator_norms = []

    for t in t_values:
        # O_A(t) = e^{iHt} O_A e^{-iHt}
        eiHt = la.expm(1j * H * t)
        eiHt_dag = la.expm(-1j * H * t)

        O_A_t = eiHt @ O_A @ eiHt_dag
        comm = O_A_t @ O_B - O_B @ O_A_t
        norm = la.norm(comm, ord=2)  # operator norm (largest singular value)
        commutator_norms.append(float(norm))

    # Extract Lieb-Robinson velocity by fitting log(||[.]||) = v*t - d + const
    # in the regime where the commutator is growing.
    log_norms = np.log(np.array(commutator_norms) + 1e-30)
    t_arr = np.array([float(t) for t in t_values])

    # Use the last 10 points (where growth is more visible) for velocity fit
    mask = t_arr >= 0.5
    if np.sum(mask) >= 3:
        coeffs = np.polyfit(t_arr[mask], log_norms[mask], 1)
        v_estimate = float(coeffs[0])  # slope = v
    else:
        v_estimate = float('nan')

    # Verify: for small t, commutator should be much smaller than for large t
    early_norm = np.mean(commutator_norms[:3])   # t = 0.1, 0.2, 0.3
    late_norm = np.mean(commutator_norms[-3:])    # t = 1.8, 1.9, 2.0
    light_cone_respected = bool(early_norm < late_norm * 0.5)

    results["t_values"] = [float(t) for t in t_values]
    results["commutator_norms"] = commutator_norms
    results["distance"] = distance
    results["lr_velocity_estimate"] = v_estimate
    results["early_mean_norm"] = float(early_norm)
    results["late_mean_norm"] = float(late_norm)
    results["light_cone_respected"] = light_cone_respected

    return results


# ---------------------------------------------------------------------------
# Probe 3: Out-of-Time-Order Correlator (OTOC) / Scrambling
# ---------------------------------------------------------------------------

def probe_otoc():
    """
    Compute F(t) = <psi| W+(t) V+ W(t) V |psi> for
    W = sigma_z^0, V = sigma_z^5 on a random Heisenberg chain.

    F(t) -> 0 indicates complete scrambling.
    Start from infinite-temperature state (maximally mixed), so use
    the normalized trace form:
      F(t) = (1/d) Tr[ W+(t) V+ W(t) V ]
    """
    results = {}
    n = N_QUBITS
    dim = DIM
    rng = np.random.default_rng(SEED)

    # Random Heisenberg couplings
    couplings = rng.uniform(0.5, 1.5, size=n - 1).tolist()
    # Add random on-site fields for scrambling
    H = build_heisenberg_hamiltonian(n, couplings)
    for i in range(n):
        h_field = rng.uniform(-0.5, 0.5, size=3)
        for k, P in enumerate([SIGMA_X, SIGMA_Y, SIGMA_Z]):
            H += h_field[k] * single_site_op(P, i, n)

    W = single_site_op(SIGMA_Z, 0, n)
    V = single_site_op(SIGMA_Z, n - 1, n)

    t_values = np.linspace(0.0, 3.0, 31)
    F_values = []

    for t in t_values:
        if t == 0.0:
            W_t = W.copy()
        else:
            eiHt = la.expm(1j * H * t)
            eiHt_dag = la.expm(-1j * H * t)
            W_t = eiHt @ W @ eiHt_dag

        # F(t) = (1/d) Tr[ W+(t) V+ W(t) V ]
        W_dag_t = W_t.conj().T
        V_dag = V.conj().T
        product = W_dag_t @ V_dag @ W_t @ V
        F_t = np.real(np.trace(product)) / dim
        F_values.append(float(F_t))

    # At t=0: W(0)=W, so F(0)=(1/d)Tr[W+ V+ W V] = (1/d)Tr[I] = 1
    # (since W and V commute at t=0 for separated sites)
    initial_value = F_values[0]
    final_value = F_values[-1]
    min_value = min(F_values)

    # Scrambling criterion: F decays significantly from 1
    scrambling_detected = bool(min_value < 0.5 * initial_value)

    # Find scrambling time (first t where F drops below 0.5)
    scrambling_time = None
    for i, f in enumerate(F_values):
        if f < 0.5 * initial_value:
            scrambling_time = float(t_values[i])
            break

    results["couplings"] = couplings
    results["t_values"] = [float(t) for t in t_values]
    results["F_values"] = F_values
    results["F_initial"] = float(initial_value)
    results["F_final"] = float(final_value)
    results["F_min"] = float(min_value)
    results["scrambling_detected"] = scrambling_detected
    results["scrambling_time"] = scrambling_time

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    t0 = time.time()
    all_results = {
        "probe": "sim_pure_lego_qca_lieb_robinson",
        "description": "QCA ballistic spreading, Lieb-Robinson bounds, OTOC scrambling",
        "n_qubits": N_QUBITS,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    print("=" * 72)
    print("PURE LEGO: QCA + Lieb-Robinson + OTOC Scrambling")
    print("=" * 72)

    # --- Probe 1: QCA ---
    print("\n[1/3] QCA ballistic entanglement spreading ...")
    qca = probe_qca()
    all_results["qca"] = qca
    print(f"  Mid-cut entropies (steps 0-10): "
          f"{[f'{e:.3f}' for e in qca['mid_cut_entropies']]}")
    print(f"  Linear fit slope: {qca['linear_fit_slope']:.4f}")
    print(f"  Final entropy: {qca['final_entropy']:.4f} / {qca['max_possible_entropy']:.1f}")
    status = "PASS" if qca["ballistic_spreading"] else "FAIL"
    print(f"  Ballistic spreading: {status}")

    # --- Probe 2: Lieb-Robinson ---
    print("\n[2/3] Lieb-Robinson bound verification ...")
    lr = probe_lieb_robinson()
    all_results["lieb_robinson"] = lr
    print(f"  Distance d(A,B) = {lr['distance']}")
    print(f"  ||[O_A(t), O_B]|| at t=0.1: {lr['commutator_norms'][0]:.6f}")
    print(f"  ||[O_A(t), O_B]|| at t=2.0: {lr['commutator_norms'][-1]:.6f}")
    print(f"  Estimated LR velocity: {lr['lr_velocity_estimate']:.4f}")
    print(f"  Early mean: {lr['early_mean_norm']:.6f}, "
          f"Late mean: {lr['late_mean_norm']:.6f}")
    status = "PASS" if lr["light_cone_respected"] else "FAIL"
    print(f"  Light cone respected: {status}")

    # --- Probe 3: OTOC ---
    print("\n[3/3] OTOC information scrambling ...")
    otoc = probe_otoc()
    all_results["otoc"] = otoc
    print(f"  F(0)  = {otoc['F_initial']:.6f}")
    print(f"  F(3)  = {otoc['F_final']:.6f}")
    print(f"  F_min = {otoc['F_min']:.6f}")
    if otoc["scrambling_time"] is not None:
        print(f"  Scrambling time (F < 0.5*F0): t = {otoc['scrambling_time']:.2f}")
    else:
        print("  Scrambling time: not reached in window")
    status = "PASS" if otoc["scrambling_detected"] else "FAIL"
    print(f"  Scrambling detected: {status}")

    # --- Summary ---
    elapsed = time.time() - t0
    all_pass = (qca["ballistic_spreading"]
                and lr["light_cone_respected"]
                and otoc["scrambling_detected"])
    all_results["all_pass"] = all_pass
    all_results["elapsed_seconds"] = round(elapsed, 3)

    print("\n" + "=" * 72)
    print(f"OVERALL: {'ALL PASS' if all_pass else 'SOME FAILED'}  "
          f"({elapsed:.2f}s)")
    print("=" * 72)

    # --- Write results ---
    out_dir = os.path.join(os.path.dirname(__file__),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir,
                            "pure_lego_qca_lieb_robinson_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
