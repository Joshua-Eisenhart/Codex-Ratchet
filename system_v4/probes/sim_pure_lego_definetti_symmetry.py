#!/usr/bin/env python3
"""
sim_pure_lego_definetti_symmetry.py
===================================

Pure-lego probe: quantum de Finetti theorem and permutation symmetry.
No engine dependencies. numpy/scipy only.

Sections
--------
1. Classical de Finetti   – exchangeable sequence as mixture of iid;
                            verify SWAP symmetry of the 2-site state.
2. Quantum de Finetti     – 4-qubit Dicke state |D_4^2>; trace to 2 qubits;
                            measure separability distance.
3. SWAP test              – build SWAP operator; verify action on product
                            states; estimate |<psi|phi>|^2 via measurement
                            statistics.
4. Bell-state permutation – classify each Bell state as symmetric (triplet)
                            or antisymmetric (singlet) under SWAP.
"""

import json
import os
import sys
from datetime import datetime, UTC
from itertools import combinations

import warnings
import numpy as np
from scipy.linalg import sqrtm

classification = "classical_baseline"

# ─── output path ──────────────────────────────────────────────────────
RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results",
)
os.makedirs(RESULTS_DIR, exist_ok=True)

OUT_FILE = os.path.join(RESULTS_DIR, "pure_lego_definetti_symmetry_results.json")


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def ket(*bits):
    """Return computational-basis ket for a bit string."""
    n = len(bits)
    dim = 2 ** n
    idx = int("".join(str(b) for b in bits), 2)
    v = np.zeros(dim, dtype=complex)
    v[idx] = 1.0
    return v


def outer(v):
    """Outer product |v><v|."""
    v = v.reshape(-1, 1)
    return v @ v.conj().T


def partial_trace(rho, keep, dims):
    """
    Trace out all subsystems except those in `keep`.
    `dims` is a list of subsystem dimensions, e.g. [2,2,2,2] for 4 qubits.
    `keep` is a list of subsystem indices to retain.
    Uses einsum for correctness.
    """
    n = len(dims)
    rho_r = rho.reshape(dims + dims)
    # Build einsum index lists.
    # Input axes: 0..n-1 (row), n..2n-1 (col)
    # For traced-out subsystems, contract row & col indices.
    # For kept subsystems, leave them free.
    trace_out = sorted(set(range(n)) - set(keep))
    keep_sorted = sorted(keep)

    in_indices = list(range(2 * n))   # row: 0..n-1, col: n..2n-1
    # For traced-out subsystems, make col index = row index
    for i in trace_out:
        in_indices[n + i] = i  # contract axis i with axis n+i

    # Output indices: kept row axes then kept col axes
    out_indices = [i for i in keep_sorted] + [n + i for i in keep_sorted]
    # But the col indices for kept subsystems in in_indices are n+i,
    # which we haven't touched, so they remain distinct. Good.

    rho_out = np.einsum(rho_r, in_indices, out_indices)
    d_keep = int(np.prod([dims[i] for i in keep_sorted]))
    return rho_out.reshape(d_keep, d_keep)


def fidelity(rho, sigma):
    """Fidelity F(rho, sigma) = (Tr sqrt(sqrt(rho) sigma sqrt(rho)))^2."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        sq_rho = sqrtm(rho)
    inner = sq_rho @ sigma @ sq_rho
    evals = np.linalg.eigvalsh(inner)
    evals = np.maximum(evals.real, 0.0)
    return float(np.sum(np.sqrt(evals))) ** 2


def trace_distance(rho, sigma):
    """Trace distance 0.5 * ||rho - sigma||_1."""
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return 0.5 * float(np.sum(np.abs(evals)))


def is_separable_2qubit(rho, tol=1e-6):
    """Check PPT criterion (necessary & sufficient for 2-qubit)."""
    # Partial transpose w.r.t. second subsystem
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(rho_pt)
    return bool(np.all(evals > -tol)), float(np.min(evals))


# ═══════════════════════════════════════════════════════════════════════
# SECTION 1 — CLASSICAL DE FINETTI
# ═══════════════════════════════════════════════════════════════════════

def run_classical_definetti():
    """
    An exchangeable 2-site classical probability is a mixture of iid.
    Build: p(x1,x2) = 0.5 * Bernoulli(0.3)^2 + 0.5 * Bernoulli(0.7)^2
    This is exchangeable: p(x1,x2) = p(x2,x1).
    Embed as a 4x4 diagonal density matrix (classical state) and verify
    SWAP symmetry.
    """
    results = {}

    # Mixture of two iid Bernoullis
    p1 = 0.3
    p2 = 0.7
    w1, w2 = 0.5, 0.5

    # Joint distribution: P(x1, x2) for x1, x2 in {0, 1}
    joint = np.zeros((2, 2))
    for x1 in range(2):
        for x2 in range(2):
            bern1 = (p1 ** x1) * ((1 - p1) ** (1 - x1))
            bern2 = (p1 ** x2) * ((1 - p1) ** (1 - x2))
            bern3 = (p2 ** x1) * ((1 - p2) ** (1 - x1))
            bern4 = (p2 ** x2) * ((1 - p2) ** (1 - x2))
            joint[x1, x2] = w1 * bern1 * bern2 + w2 * bern3 * bern4

    results["joint_distribution"] = joint.tolist()
    results["sum_joint"] = float(np.sum(joint))

    # Exchangeability check: P(x1,x2) == P(x2,x1)
    swap_diff = np.max(np.abs(joint - joint.T))
    results["exchangeability_max_diff"] = float(swap_diff)
    results["is_exchangeable"] = bool(swap_diff < 1e-12)

    # Embed as diagonal density matrix in 4-dim Hilbert space
    rho_classical = np.diag(joint.flatten())
    SWAP_4 = build_swap_2qubit()
    rho_swapped = SWAP_4 @ rho_classical @ SWAP_4.conj().T
    swap_invariance = np.max(np.abs(rho_classical - rho_swapped))
    results["swap_invariance_residual"] = float(swap_invariance)
    results["swap_symmetric"] = bool(swap_invariance < 1e-12)

    # Verify it's a proper mixture of product (iid) states
    rho_prod1 = np.diag([1 - p1, p1])
    rho_prod2 = np.diag([1 - p2, p2])
    rho_mix = w1 * np.kron(rho_prod1, rho_prod1) + w2 * np.kron(rho_prod2, rho_prod2)
    mix_diff = np.max(np.abs(rho_classical - rho_mix))
    results["mixture_of_iid_residual"] = float(mix_diff)
    results["confirmed_mixture_of_iid"] = bool(mix_diff < 1e-12)

    return results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 2 — QUANTUM DE FINETTI (DICKE STATE)
# ═══════════════════════════════════════════════════════════════════════

def build_dicke_state(n, k):
    """
    Build the Dicke state |D_n^k>: equal superposition of all n-qubit
    computational basis states with exactly k excitations (ones).
    Returns the state vector (normalized).
    """
    dim = 2 ** n
    psi = np.zeros(dim, dtype=complex)
    # Enumerate all bit strings with exactly k ones
    count = 0
    for positions in combinations(range(n), k):
        bits = [0] * n
        for p in positions:
            bits[p] = 1
        idx = int("".join(str(b) for b in bits), 2)
        psi[idx] = 1.0
        count += 1
    psi /= np.sqrt(count)
    return psi


def run_quantum_definetti():
    """
    Build 4-qubit Dicke state |D_4^2>, trace out 2 qubits,
    check how close the reduced 2-qubit state is to separable.
    """
    results = {}

    psi = build_dicke_state(4, 2)
    rho_4 = outer(psi)

    results["dicke_state_norm"] = float(np.real(psi.conj() @ psi))
    results["dicke_state_purity"] = float(np.real(np.trace(rho_4 @ rho_4)))

    # Verify full state is permutation-symmetric
    # Check SWAP on qubits 0,1
    SWAP_01 = np.eye(16, dtype=complex)
    for i in range(16):
        bits = [(i >> (3 - q)) & 1 for q in range(4)]
        bits[0], bits[1] = bits[1], bits[0]
        j = sum(b << (3 - q) for q, b in enumerate(bits))
        SWAP_01[i, :] = 0
        SWAP_01[i, j] = 1.0
    # Rebuild as permutation matrix
    SWAP_01 = np.zeros((16, 16), dtype=complex)
    for i in range(16):
        bits = [(i >> (3 - q)) & 1 for q in range(4)]
        bits[0], bits[1] = bits[1], bits[0]
        j = sum(b << (3 - q) for q, b in enumerate(bits))
        SWAP_01[j, i] = 1.0

    psi_swapped = SWAP_01 @ psi
    overlap_01 = float(np.abs(psi.conj() @ psi_swapped) ** 2)
    results["swap_01_overlap"] = overlap_01
    results["swap_01_symmetric"] = bool(abs(overlap_01 - 1.0) < 1e-10)

    # Trace out qubits 2,3 → reduced state on qubits 0,1
    rho_01 = partial_trace(rho_4, keep=[0, 1], dims=[2, 2, 2, 2])
    results["reduced_trace"] = float(np.real(np.trace(rho_01)))
    results["reduced_purity"] = float(np.real(np.trace(rho_01 @ rho_01)))

    # Check separability via PPT
    is_sep, min_eval = is_separable_2qubit(rho_01)
    results["reduced_is_PPT"] = is_sep
    results["reduced_PT_min_eigenvalue"] = min_eval

    # Distance to closest separable state: maximally mixed
    rho_mm = np.eye(4, dtype=complex) / 4.0
    td_mm = trace_distance(rho_01, rho_mm)
    fid_mm = fidelity(rho_01, rho_mm)
    results["trace_distance_to_maximally_mixed"] = td_mm
    results["fidelity_to_maximally_mixed"] = fid_mm

    # Distance to closest product state: (|0><0|+|1><1|)/2 tensor itself
    rho_prod = np.kron(np.eye(2) / 2, np.eye(2) / 2)
    td_prod = trace_distance(rho_01, rho_prod)
    results["trace_distance_to_product"] = td_prod

    # De Finetti approximation bound: for symmetric state of n qubits,
    # reduced k-qubit state is O(k*d^2/n)-close to separable in trace dist.
    # Here n=4, k=2, d=2 → bound ~ 2*4/4 = 2 (vacuous for small n)
    definetti_bound = 2.0 * 4.0 / 4.0
    results["definetti_bound_k_d2_over_n"] = definetti_bound
    results["bound_is_vacuous"] = definetti_bound >= 1.0

    # Negativity of the reduced state (entanglement measure)
    rho_pt = rho_01.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    pt_evals = np.linalg.eigvalsh(rho_pt)
    negativity = float(-np.sum(pt_evals[pt_evals < 0]))
    results["reduced_negativity"] = negativity

    # Eigenspectrum of reduced state
    evals_reduced = np.linalg.eigvalsh(rho_01)
    results["reduced_eigenvalues"] = sorted(evals_reduced.tolist(), reverse=True)

    # Convergence demonstration: trace out more qubits from larger Dicke states
    # As n grows, the k-qubit reduced state approaches separable.
    convergence = {}
    for n_qubits in [4, 6, 8, 10]:
        k_excite = n_qubits // 2
        psi_n = build_dicke_state(n_qubits, k_excite)
        rho_n = outer(psi_n)
        dims_n = [2] * n_qubits
        rho_2q = partial_trace(rho_n, keep=[0, 1], dims=dims_n)
        is_ppt, min_ev = is_separable_2qubit(rho_2q)
        convergence[f"n={n_qubits}"] = {
            "PT_min_eigenvalue": min_ev,
            "is_PPT": is_ppt,
            "negativity": float(-min(min_ev, 0.0)),
        }
    results["convergence_toward_separable"] = convergence

    return results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 3 — SWAP TEST
# ═══════════════════════════════════════════════════════════════════════

def build_swap_2qubit():
    """Build the 4x4 SWAP operator for 2 qubits."""
    SWAP = np.zeros((4, 4), dtype=complex)
    for i in range(2):
        for j in range(2):
            # |ij> -> |ji>
            src = 2 * i + j
            dst = 2 * j + i
            SWAP[dst, src] = 1.0
    return SWAP


def run_swap_test():
    """
    (a) Verify SWAP|psi>|phi> = |phi>|psi>.
    (b) SWAP test circuit: ancilla + controlled-SWAP (Fredkin).
        P(ancilla=0) = (1 + |<psi|phi>|^2) / 2
    Simulate with Monte-Carlo sampling.
    """
    results = {}

    SWAP = build_swap_2qubit()

    # (a) Verify SWAP action on product states
    psi = np.array([1, 0], dtype=complex)         # |0>
    phi = np.array([1, 1], dtype=complex) / np.sqrt(2)  # |+>

    product_psi_phi = np.kron(psi, phi)
    product_phi_psi = np.kron(phi, psi)
    swapped = SWAP @ product_psi_phi
    swap_correct = np.allclose(swapped, product_phi_psi)
    results["swap_action_correct"] = bool(swap_correct)
    results["swap_residual"] = float(np.max(np.abs(swapped - product_phi_psi)))

    # Verify SWAP is unitary and Hermitian (SWAP^2 = I)
    results["swap_is_unitary"] = bool(np.allclose(SWAP @ SWAP.conj().T, np.eye(4)))
    results["swap_is_hermitian"] = bool(np.allclose(SWAP, SWAP.conj().T))
    results["swap_squared_is_identity"] = bool(np.allclose(SWAP @ SWAP, np.eye(4)))

    # SWAP eigenvalues: +1 (symmetric subspace, dim 3) and -1 (antisymmetric, dim 1)
    evals_swap = np.linalg.eigvalsh(SWAP)
    results["swap_eigenvalues"] = sorted(evals_swap.tolist())

    # (b) SWAP test circuit simulation
    # For states |psi>, |phi>, the SWAP test gives:
    # P(ancilla=0) = (1 + |<psi|phi>|^2) / 2
    test_pairs = [
        ("same_state", psi, psi),
        ("orthogonal", np.array([1, 0], dtype=complex), np.array([0, 1], dtype=complex)),
        ("partial_overlap", psi, phi),
    ]

    swap_test_results = {}
    np.random.seed(42)
    n_shots = 100_000

    for name, a, b in test_pairs:
        # Exact overlap
        exact_overlap_sq = float(np.abs(a.conj() @ b) ** 2)
        exact_p0 = (1 + exact_overlap_sq) / 2

        # Build the 3-qubit state: |0>|psi>|phi>
        ancilla_0 = np.array([1, 0], dtype=complex)
        state_3q = np.kron(np.kron(ancilla_0, a), b)  # 8-dim

        # Apply H to ancilla
        H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        H_full = np.kron(np.kron(H, np.eye(2)), np.eye(2))
        state_3q = H_full @ state_3q

        # Apply controlled-SWAP (Fredkin gate)
        # |0>|x>|y> -> |0>|x>|y>;  |1>|x>|y> -> |1>|y>|x>
        CSWAP = np.eye(8, dtype=complex)
        SWAP_2q = build_swap_2qubit()
        # Controlled on ancilla=1: act on indices 4..7
        CSWAP[4:8, 4:8] = SWAP_2q
        state_3q = CSWAP @ state_3q

        # Apply H to ancilla again
        state_3q = H_full @ state_3q

        # Probability of ancilla=0: sum |c_{0xy}|^2 for all x,y
        p0_exact = float(np.sum(np.abs(state_3q[:4]) ** 2))

        # Monte-Carlo sampling
        probs = np.abs(state_3q) ** 2
        probs /= probs.sum()  # renormalize for floating-point
        samples = np.random.choice(8, size=n_shots, p=probs)
        p0_sampled = float(np.mean(samples < 4))

        swap_test_results[name] = {
            "exact_overlap_sq": exact_overlap_sq,
            "formula_p0": exact_p0,
            "circuit_p0": p0_exact,
            "sampled_p0": round(p0_sampled, 5),
            "n_shots": n_shots,
            "formula_matches_circuit": bool(abs(exact_p0 - p0_exact) < 1e-10),
        }

    results["swap_test"] = swap_test_results
    return results


# ═══════════════════════════════════════════════════════════════════════
# SECTION 4 — BELL STATE PERMUTATION SYMMETRY
# ═══════════════════════════════════════════════════════════════════════

def run_bell_symmetry():
    """
    Classify each Bell state under SWAP:
      |Phi+> = (|00> + |11>) / sqrt(2)   → symmetric  (triplet)
      |Phi-> = (|00> - |11>) / sqrt(2)   → symmetric  (triplet)
      |Psi+> = (|01> + |10>) / sqrt(2)   → symmetric  (triplet)
      |Psi-> = (|01> - |10>) / sqrt(2)   → antisymmetric (singlet)
    """
    results = {}
    SWAP = build_swap_2qubit()

    bell_states = {
        "Phi+": (ket(0, 0) + ket(1, 1)) / np.sqrt(2),
        "Phi-": (ket(0, 0) - ket(1, 1)) / np.sqrt(2),
        "Psi+": (ket(0, 1) + ket(1, 0)) / np.sqrt(2),
        "Psi-": (ket(0, 1) - ket(1, 0)) / np.sqrt(2),
    }

    for name, psi in bell_states.items():
        swapped = SWAP @ psi
        # eigenvalue: SWAP|psi> = lambda|psi>, lambda = +1 or -1
        # Compute lambda as <psi|SWAP|psi>
        eigenvalue = float(np.real(psi.conj() @ swapped))
        is_symmetric = abs(eigenvalue - 1.0) < 1e-10
        is_antisymmetric = abs(eigenvalue + 1.0) < 1e-10

        if is_symmetric:
            classification = "symmetric (triplet)"
        elif is_antisymmetric:
            classification = "antisymmetric (singlet)"
        else:
            classification = "neither"

        results[name] = {
            "swap_eigenvalue": eigenvalue,
            "classification": classification,
            "is_symmetric": is_symmetric,
            "is_antisymmetric": is_antisymmetric,
        }

    # Verify: symmetric subspace is 3-dim, antisymmetric is 1-dim
    evals, evecs = np.linalg.eigh(SWAP)
    n_symmetric = int(np.sum(np.abs(evals - 1.0) < 1e-10))
    n_antisymmetric = int(np.sum(np.abs(evals + 1.0) < 1e-10))
    results["subspace_dimensions"] = {
        "symmetric_dim": n_symmetric,
        "antisymmetric_dim": n_antisymmetric,
    }

    # Expected: Psi- is the unique antisymmetric state (singlet)
    results["singlet_is_Psi_minus"] = results["Psi-"]["is_antisymmetric"]
    results["triplet_count"] = sum(
        1 for k in ["Phi+", "Phi-", "Psi+"] if results[k]["is_symmetric"]
    )

    return results


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  PURE LEGO: de Finetti theorem & permutation symmetry")
    print("=" * 70)

    report = {
        "probe": "sim_pure_lego_definetti_symmetry",
        "timestamp": datetime.now(UTC).isoformat(),
        "sections": {},
        "verdicts": {},
    }

    # ── Section 1: Classical de Finetti ────────────────────────────────
    print("\n[1] Classical de Finetti ...")
    sec1 = run_classical_definetti()
    report["sections"]["classical_definetti"] = sec1
    v1 = sec1["is_exchangeable"] and sec1["swap_symmetric"] and sec1["confirmed_mixture_of_iid"]
    report["verdicts"]["classical_definetti"] = "PASS" if v1 else "FAIL"
    print(f"    exchangeable={sec1['is_exchangeable']}  "
          f"swap_symmetric={sec1['swap_symmetric']}  "
          f"mixture_of_iid={sec1['confirmed_mixture_of_iid']}  → {report['verdicts']['classical_definetti']}")

    # ── Section 2: Quantum de Finetti ─────────────────────────────────
    print("\n[2] Quantum de Finetti (Dicke |D_4^2>) ...")
    sec2 = run_quantum_definetti()
    report["sections"]["quantum_definetti"] = sec2
    # Verdict: (a) Dicke state is permutation-symmetric, (b) negativity
    # decreases as n grows → de Finetti convergence toward separability.
    conv = sec2["convergence_toward_separable"]
    sorted_keys = sorted(conv.keys(), key=lambda k: int(k.split("=")[1]))
    neg_values = [conv[k]["negativity"] for k in sorted_keys]
    negativity_decreasing = all(neg_values[i] >= neg_values[i+1] - 1e-10
                                for i in range(len(neg_values) - 1))
    v2 = sec2["swap_01_symmetric"] and negativity_decreasing
    report["verdicts"]["quantum_definetti"] = "PASS" if v2 else "FAIL"
    print(f"    Dicke norm={sec2['dicke_state_norm']:.6f}  "
          f"purity={sec2['dicke_state_purity']:.6f}")
    print(f"    swap_01_symmetric={sec2['swap_01_symmetric']}  "
          f"reduced_is_PPT={sec2['reduced_is_PPT']}  "
          f"PT_min_eval={sec2['reduced_PT_min_eigenvalue']:.6e}")
    print(f"    reduced negativity={sec2['reduced_negativity']:.6f}  "
          f"bound_vacuous={sec2['bound_is_vacuous']}")
    print(f"    reduced eigenvalues={[f'{e:.4f}' for e in sec2['reduced_eigenvalues']]}")
    print(f"    convergence (negativity as n grows):")
    for k in sorted_keys:
        print(f"      {k}: negativity={conv[k]['negativity']:.6f}  PPT={conv[k]['is_PPT']}")
    print(f"    negativity_decreasing={negativity_decreasing}")
    print(f"    → {report['verdicts']['quantum_definetti']}")

    # ── Section 3: SWAP test ──────────────────────────────────────────
    print("\n[3] SWAP test ...")
    sec3 = run_swap_test()
    report["sections"]["swap_test"] = sec3
    all_match = all(
        v["formula_matches_circuit"] for v in sec3["swap_test"].values()
    )
    v3 = sec3["swap_action_correct"] and sec3["swap_is_hermitian"] and all_match
    report["verdicts"]["swap_test"] = "PASS" if v3 else "FAIL"
    print(f"    action_correct={sec3['swap_action_correct']}  "
          f"hermitian={sec3['swap_is_hermitian']}  "
          f"SWAP^2=I: {sec3['swap_squared_is_identity']}")
    for name, data in sec3["swap_test"].items():
        print(f"    {name}: overlap²={data['exact_overlap_sq']:.4f}  "
              f"formula_p0={data['formula_p0']:.4f}  "
              f"circuit_p0={data['circuit_p0']:.4f}  "
              f"sampled_p0={data['sampled_p0']:.4f}")
    print(f"    → {report['verdicts']['swap_test']}")

    # ── Section 4: Bell-state symmetry ────────────────────────────────
    print("\n[4] Bell-state permutation symmetry ...")
    sec4 = run_bell_symmetry()
    report["sections"]["bell_symmetry"] = sec4
    v4 = (
        sec4["singlet_is_Psi_minus"]
        and sec4["triplet_count"] == 3
        and sec4["subspace_dimensions"]["symmetric_dim"] == 3
        and sec4["subspace_dimensions"]["antisymmetric_dim"] == 1
    )
    report["verdicts"]["bell_symmetry"] = "PASS" if v4 else "FAIL"
    for name in ["Phi+", "Phi-", "Psi+", "Psi-"]:
        data = sec4[name]
        print(f"    {name:5s}: eigenvalue={data['swap_eigenvalue']:+.0f}  "
              f"{data['classification']}")
    print(f"    symmetric subspace dim={sec4['subspace_dimensions']['symmetric_dim']}  "
          f"antisymmetric dim={sec4['subspace_dimensions']['antisymmetric_dim']}")
    print(f"    → {report['verdicts']['bell_symmetry']}")

    # ── Summary ───────────────────────────────────────────────────────
    all_pass = all(v == "PASS" for v in report["verdicts"].values())
    report["overall"] = "ALL PASS" if all_pass else "SOME FAIL"

    print("\n" + "=" * 70)
    print(f"  OVERALL: {report['overall']}")
    for sec_name, verdict in report["verdicts"].items():
        tag = "OK" if verdict == "PASS" else "XX"
        print(f"    [{tag}] {sec_name}: {verdict}")
    print("=" * 70)

    with open(OUT_FILE, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nResults → {OUT_FILE}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
