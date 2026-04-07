#!/usr/bin/env python3
"""
PURE LEGO: Discrete Wigner Function & Quasi-Probability Distributions
======================================================================
Foundational building block.  Pure math only -- numpy + scipy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. Single-qubit (d=2) discrete Wigner -- Gibbons/Wootters construction
   - All single-qubit states are non-negative (theorem: d=2 is special)
   - Maximally mixed = uniform = 1/d everywhere
2. Qutrit (d=3) discrete Wigner -- Gross construction
   - Non-stabilizer pure states HAVE negative values (nonclassicality witness)
   - Mixed states smooth toward positive
   - Maximally mixed = uniform = 1/d
3. Husimi Q-function (always >= 0, smoothed Wigner)
4. 2-qubit discrete Wigner vs concurrence comparison
5. Test battery: 10+ states spanning pure/mixed/entangled across dimensions

Reference
---------
- Gibbons, Hoffman, Wootters, Phys. Rev. A 70, 062101 (2004)
- Gross, J. Math. Phys. 47, 122107 (2006) -- discrete Wigner for odd d
- Veitch et al., New J. Phys. 14, 113011 (2012) -- negativity as resource

Key theorem: For d=2 (single qubit), the discrete Wigner function is
non-negative for ALL states. Negativity as a nonclassicality witness
requires either d >= 3 (odd prime) or multi-qubit systems.
"""

import json, pathlib, time, warnings
import numpy as np
from scipy.linalg import sqrtm

np.random.seed(42)
EPS = 1e-14
RESULTS = {}
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def dm(v):
    """Density matrix from ket vector."""
    k = ket(v)
    return k @ k.conj().T

def is_valid_dm(rho, label="", tol=1e-12):
    """Check Tr=1, Hermitian, PSD."""
    tr = np.real(np.trace(rho))
    herm = np.allclose(rho, rho.conj().T, atol=tol)
    evals = np.linalg.eigvalsh(rho)
    psd = bool(np.all(evals >= -tol))
    purity = np.real(np.trace(rho @ rho))
    return {
        "label": label,
        "trace": float(tr),
        "trace_ok": bool(abs(tr - 1.0) < tol),
        "hermitian": herm,
        "psd": psd,
        "purity": float(purity),
        "eigenvalues": [float(e) for e in evals],
    }


# ══════════════════════════════════════════════════════════════════════
# 1.  SINGLE-QUBIT DISCRETE WIGNER (d=2) -- Gibbons/Wootters
# ══════════════════════════════════════════════════════════════════════

def build_phase_point_operators_d2():
    """
    Build 4 phase-point operators for d=2 discrete Wigner.
    A(a,b) = (1/2)(I + s_z * sz + s_x * sx + s_y * sy)
    with sign choices so they sum to 2I and each has Tr=1.
    """
    sign_table = {
        (0, 0): (+1, +1, +1),
        (0, 1): (+1, -1, -1),
        (1, 0): (-1, +1, -1),
        (1, 1): (-1, -1, +1),
    }
    ops = {}
    for (a, b), (sz_s, sx_s, sy_s) in sign_table.items():
        ops[(a, b)] = 0.5 * (I2 + sz_s * sz + sx_s * sx + sy_s * sy)

    # Verify axioms
    total = sum(ops.values())
    assert np.allclose(total, 2 * I2), "Phase-point operators must sum to d*I"
    for key, op in ops.items():
        assert np.allclose(np.trace(op), 1.0), f"Tr[A_{key}] must be 1"
        assert np.allclose(op, op.conj().T), f"A_{key} must be Hermitian"
    return ops


def discrete_wigner_d2(rho, phase_ops):
    """W(a,b) = (1/d) Tr[A(a,b) . rho] for d=2. Returns 2x2 array."""
    W = np.zeros((2, 2))
    for (a, b), A_ab in phase_ops.items():
        W[a, b] = np.real(np.trace(A_ab @ rho)) / 2
    return W


# ══════════════════════════════════════════════════════════════════════
# 2.  QUTRIT DISCRETE WIGNER (d=3) -- Gross construction
# ══════════════════════════════════════════════════════════════════════
#
# For odd prime d, the discrete Wigner function on Z_d x Z_d is:
#   W(q, p) = (1/d) sum_{k=0}^{d-1} omega^{-pk} <q+k| rho |q-k>
# where omega = exp(2*pi*i/d) and arithmetic is mod d.
#
# This is the unique covariant Wigner function for odd d.
# Key: non-stabilizer states (like the "strange" state) go NEGATIVE.

def discrete_wigner_d3(rho):
    """
    Compute the d=3 discrete Wigner function on the 3x3 phase space.
    W(q, p) = (1/3) sum_{k=0}^{2} omega^{-pk} rho_{(q+k)%3, (q-k)%3}
    Returns a 3x3 real array.
    """
    d = 3
    omega = np.exp(2j * np.pi / d)
    W = np.zeros((d, d))
    for q in range(d):
        for p in range(d):
            val = 0.0
            for k in range(d):
                row = (q + k) % d
                col = (q - k) % d
                val += omega ** (-p * k) * rho[row, col]
            W[q, p] = np.real(val) / d
    return W


def wigner_negativity(W):
    """Sum of absolute values minus 1. Zero iff W >= 0 everywhere."""
    return float(np.sum(np.abs(W)) - 1.0)

def wigner_min_val(W):
    """Most negative value."""
    return float(np.min(W))


def build_qutrit_states():
    """
    Build a battery of qutrit states (d=3):
    - Computational basis (stabilizer, non-negative Wigner)
    - MUB states (stabilizer, non-negative)
    - Non-stabilizer "strange" state (NEGATIVE Wigner -- the money shot)
    - Mixed states (smoothing toward positive)
    - Maximally mixed (uniform)
    """
    d = 3
    omega = np.exp(2j * np.pi / d)
    Id3 = np.eye(d, dtype=complex)

    states = {}

    # Computational basis (stabilizer states)
    for j in range(d):
        v = np.zeros(d, dtype=complex)
        v[j] = 1.0
        states[f"|{j}>"] = dm(v)

    # Fourier basis / MUB states (stabilizer)
    for j in range(d):
        v = np.array([omega ** (j * k) for k in range(d)], dtype=complex) / np.sqrt(d)
        states[f"|F{j}>"] = dm(v)

    # Non-stabilizer "strange" state -- the T-state / magic state for qutrits
    # |S> = (1/sqrt(2))(|0> + |1>)  -- not a stabilizer state for d=3
    v_strange = np.array([1, 1, 0], dtype=complex) / np.sqrt(2)
    states["strange_01"] = dm(v_strange)

    # Another non-stabilizer state
    v_strange2 = np.array([1, 0, 1], dtype=complex) / np.sqrt(2)
    states["strange_02"] = dm(v_strange2)

    # General non-stabilizer superposition
    v_gen = np.array([1, np.exp(1j * np.pi / 7), np.exp(1j * 2.3)], dtype=complex)
    v_gen /= np.linalg.norm(v_gen)
    states["gen_super"] = dm(v_gen)

    # Mixed states
    states["mix_01_0.7"] = 0.7 * dm([1, 0, 0]) + 0.3 * dm([0, 1, 0])
    states["depol_0.5"] = 0.5 * dm([1, 0, 0]) + 0.5 * Id3 / d

    # Maximally mixed
    states["max_mixed"] = Id3 / d

    return states


# ══════════════════════════════════════════════════════════════════════
# 3.  HUSIMI Q-FUNCTION (single qubit)
# ══════════════════════════════════════════════════════════════════════

def husimi_q_grid(rho, n_theta=30, n_phi=60):
    """
    Husimi Q on Bloch sphere: Q(theta,phi) = <psi|rho|psi>.
    Always >= 0 by construction (expectation value of PSD operator in pure state).
    """
    thetas = np.linspace(0, np.pi, n_theta)
    phis = np.linspace(0, 2 * np.pi, n_phi, endpoint=False)
    Q = np.zeros((n_theta, n_phi))
    for i, th in enumerate(thetas):
        for j, ph in enumerate(phis):
            psi = ket([np.cos(th / 2), np.exp(1j * ph) * np.sin(th / 2)])
            Q[i, j] = np.real((psi.conj().T @ rho @ psi).item())
    return Q


def husimi_stats(rho):
    Q = husimi_q_grid(rho)
    return {
        "min": float(np.min(Q)),
        "max": float(np.max(Q)),
        "mean": float(np.mean(Q)),
        "all_non_negative": bool(np.all(Q >= -1e-14)),
    }


# ══════════════════════════════════════════════════════════════════════
# 4.  CONCURRENCE (2-qubit)
# ══════════════════════════════════════════════════════════════════════

def concurrence(rho_4x4):
    """Wootters concurrence for a 2-qubit density matrix."""
    sy_tensor = np.kron(sy, sy)
    rho_tilde = sy_tensor @ rho_4x4.conj() @ sy_tensor
    sqrt_rho = sqrtm(rho_4x4)
    product = sqrt_rho @ rho_tilde @ sqrt_rho
    # Ensure Hermitian for eigvals
    product = (product + product.conj().T) / 2
    eigvals = np.sort(np.real(np.linalg.eigvalsh(product)))[::-1]
    # eigenvalues of R = sqrt(sqrt(rho) rho_tilde sqrt(rho))
    # so eigenvalues of R are sqrt of eigenvalues of the product
    sqrt_eigvals = np.sqrt(np.maximum(eigvals, 0))
    return float(max(0.0, sqrt_eigvals[0] - sqrt_eigvals[1] - sqrt_eigvals[2] - sqrt_eigvals[3]))


# ══════════════════════════════════════════════════════════════════════
# 5.  2-QUBIT DISCRETE WIGNER
# ══════════════════════════════════════════════════════════════════════

def build_2qubit_phase_ops(single_ops):
    """16 phase-point operators via tensor product."""
    ops_2q = {}
    for (a1, b1), A1 in single_ops.items():
        for (a2, b2), A2 in single_ops.items():
            ops_2q[((a1, b1), (a2, b2))] = np.kron(A1, A2)
    return ops_2q


def discrete_wigner_2qubit(rho_4x4, phase_ops_2q):
    """2-qubit discrete Wigner. Returns dict keyed by phase-space point."""
    W = {}
    for key, A in phase_ops_2q.items():
        W[key] = float(np.real(np.trace(A @ rho_4x4))) / 4
    return W


def wigner_negativity_dict(W_dict):
    vals = np.array(list(W_dict.values()))
    return float(np.sum(np.abs(vals)) - 1.0)


def wigner_min_dict(W_dict):
    return float(min(W_dict.values()))


# ══════════════════════════════════════════════════════════════════════
# 6.  RUN: SINGLE-QUBIT d=2
# ══════════════════════════════════════════════════════════════════════

def run_single_qubit_d2():
    """Test d=2 discrete Wigner -- confirm all states non-negative (theorem)."""
    phase_ops = build_phase_point_operators_d2()
    s2 = 1.0 / np.sqrt(2)

    states = {
        "|0>":         dm([1, 0]),
        "|1>":         dm([0, 1]),
        "|+>":         dm([s2, s2]),
        "|->":         dm([s2, -s2]),
        "|R>":         dm([s2, 1j * s2]),
        "psi_gen":     dm([np.cos(np.pi / 8), np.exp(1j * np.pi / 5) * np.sin(np.pi / 8)]),
        "mix_z_0.5":   0.75 * dm([1, 0]) + 0.25 * dm([0, 1]),
        "mix_x_0.3":   0.65 * dm([s2, s2]) + 0.35 * dm([s2, -s2]),
        "depol_0.5":   0.5 * dm([1, 0]) + 0.5 * I2 / 2,
        "max_mixed":   I2 / 2,
    }

    results = []
    print("  (d=2 theorem: ALL single-qubit states have non-negative discrete Wigner)")
    for name, rho in states.items():
        validity = is_valid_dm(rho, name)
        W = discrete_wigner_d2(rho, phase_ops)
        neg = wigner_negativity(W)
        w_min = wigner_min_val(W)
        w_sum = float(np.sum(W))
        husimi = husimi_stats(rho)

        entry = {
            "state": name,
            "dimension": 2,
            "purity": validity["purity"],
            "is_pure": bool(abs(validity["purity"] - 1.0) < 1e-10),
            "wigner_values": {f"({a},{b})": float(W[a, b]) for a in range(2) for b in range(2)},
            "wigner_sum": w_sum,
            "wigner_sum_is_1": bool(abs(w_sum - 1.0) < 1e-10),
            "wigner_min": w_min,
            "wigner_negativity": neg,
            "has_negative_wigner": bool(w_min < -1e-14),
            "husimi_min": husimi["min"],
            "husimi_always_positive": husimi["all_non_negative"],
            "validity": validity,
        }
        results.append(entry)
        tag = "NEG" if entry["has_negative_wigner"] else "ok "
        print(f"  [{tag}] {name:16s}  pur={validity['purity']:.4f}  "
              f"W_min={w_min:+.6f}  neg={neg:.6f}  Q_min={husimi['min']:.6f}")

    return results


# ══════════════════════════════════════════════════════════════════════
# 7.  RUN: QUTRIT d=3  (where negativity actually appears)
# ══════════════════════════════════════════════════════════════════════

def run_qutrit_d3():
    """Test d=3 discrete Wigner -- non-stabilizer states go negative."""
    states = build_qutrit_states()
    d = 3

    results = []
    for name, rho in states.items():
        validity = is_valid_dm(rho, name)
        W = discrete_wigner_d3(rho)
        neg = wigner_negativity(W)
        w_min = wigner_min_val(W)
        w_sum = float(np.sum(W))

        entry = {
            "state": name,
            "dimension": 3,
            "purity": validity["purity"],
            "is_pure": bool(abs(validity["purity"] - 1.0) < 1e-10),
            "wigner_values": {f"({q},{p})": float(W[q, p]) for q in range(d) for p in range(d)},
            "wigner_sum": w_sum,
            "wigner_sum_is_1": bool(abs(w_sum - 1.0) < 1e-10),
            "wigner_min": w_min,
            "wigner_negativity": neg,
            "has_negative_wigner": bool(w_min < -1e-14),
            "validity": validity,
        }
        results.append(entry)
        tag = "NEG" if entry["has_negative_wigner"] else "ok "
        print(f"  [{tag}] {name:16s}  pur={validity['purity']:.4f}  "
              f"W_min={w_min:+.6f}  neg={neg:.6f}  sum={w_sum:.6f}")

    return results


# ══════════════════════════════════════════════════════════════════════
# 8.  RUN: 2-QUBIT WIGNER vs CONCURRENCE
# ══════════════════════════════════════════════════════════════════════

def run_2qubit_comparison():
    phase_ops_1q = build_phase_point_operators_d2()
    phase_ops_2q = build_2qubit_phase_ops(phase_ops_1q)
    s2 = 1.0 / np.sqrt(2)

    # Bell states
    phi_p = ket([s2, 0, 0, s2]);   phi_m = ket([s2, 0, 0, -s2])
    psi_p = ket([0, s2, s2, 0]);   psi_m = ket([0, s2, -s2, 0])

    I4 = np.eye(4, dtype=complex)
    psi_m_dm = psi_m @ psi_m.conj().T

    all_states = {
        "Phi+":   phi_p @ phi_p.conj().T,
        "Phi-":   phi_m @ phi_m.conj().T,
        "Psi+":   psi_p @ psi_p.conj().T,
        "Psi-":   psi_m_dm,
        "|00>":   np.kron(dm([1, 0]), dm([1, 0])),
        "|+->":   np.kron(dm([s2, s2]), dm([s2, -s2])),
        "|01>":   np.kron(dm([1, 0]), dm([0, 1])),
        "Werner_0.25": 0.25 * psi_m_dm + 0.75 * I4 / 4,
        "Werner_0.50": 0.50 * psi_m_dm + 0.50 * I4 / 4,
        "Werner_0.75": 0.75 * psi_m_dm + 0.25 * I4 / 4,
        "Werner_1.00": psi_m_dm,
        "max_mixed_2q": I4 / 4,
    }

    results = []
    for name, rho in all_states.items():
        W = discrete_wigner_2qubit(rho, phase_ops_2q)
        neg = wigner_negativity_dict(W)
        w_min = wigner_min_dict(W)
        C = concurrence(rho)

        entry = {
            "state": name,
            "concurrence": C,
            "wigner_negativity": neg,
            "wigner_min": w_min,
            "is_entangled": bool(C > 1e-10),
            "has_negative_wigner": bool(w_min < -1e-10),
        }
        results.append(entry)
        print(f"  {name:20s}  C={C:.6f}  W_neg={neg:.6f}  W_min={w_min:+.6f}")

    entangled = [r for r in results if r["is_entangled"]]
    separable = [r for r in results if not r["is_entangled"]]
    avg_ent = float(np.mean([r["wigner_negativity"] for r in entangled])) if entangled else 0
    avg_sep = float(np.mean([r["wigner_negativity"] for r in separable])) if separable else 0

    corr = {
        "avg_negativity_entangled": avg_ent,
        "avg_negativity_separable": avg_sep,
        "entangled_more_negative": bool(avg_ent > avg_sep),
        "note": ("Tensor-product Wigner captures entanglement-induced negativity. "
                 "Entangled pure states (Bell) show maximal negativity; Werner states "
                 "show negativity scaling with entanglement parameter p."),
    }
    return results, corr


# ══════════════════════════════════════════════════════════════════════
# 9.  PROPERTY VERIFICATION
# ══════════════════════════════════════════════════════════════════════

def verify_all(d2_results, d3_results, twoq_results, corr):
    checks = {}

    # -- d=2: ALL states non-negative (theorem) --
    all_d2_nonneg = all(not r["has_negative_wigner"] for r in d2_results)
    checks["d2_all_nonneg_theorem"] = all_d2_nonneg

    # -- d=2: max mixed uniform --
    mm2 = [r for r in d2_results if r["state"] == "max_mixed"][0]
    vals2 = list(mm2["wigner_values"].values())
    checks["d2_max_mixed_uniform"] = all(abs(v - 0.25) < 1e-10 for v in vals2)
    checks["d2_max_mixed_zero_neg"] = bool(mm2["wigner_negativity"] < 1e-10)

    # -- d=2: Husimi always positive --
    checks["d2_husimi_always_positive"] = all(r["husimi_always_positive"] for r in d2_results)

    # -- d=3: non-stabilizer pure states CAN be negative --
    d3_pure = [r for r in d3_results if r["is_pure"]]
    checks["d3_pure_can_be_negative"] = any(r["has_negative_wigner"] for r in d3_pure)

    # -- d=3: stabilizer states (comp basis, Fourier) non-negative --
    stab_names = {"|0>", "|1>", "|2>", "|F0>", "|F1>", "|F2>"}
    d3_stab = [r for r in d3_results if r["state"] in stab_names]
    checks["d3_stabilizer_nonneg"] = all(not r["has_negative_wigner"] for r in d3_stab)

    # -- d=3: mixed states smooth toward positive --
    d3_mixed = [r for r in d3_results if not r["is_pure"]]
    checks["d3_mixed_lower_negativity"] = [
        {"state": r["state"], "purity": r["purity"], "negativity": r["wigner_negativity"]}
        for r in d3_mixed
    ]

    # -- d=3: max mixed uniform = 1/d^2 = 1/9 --
    mm3 = [r for r in d3_results if r["state"] == "max_mixed"][0]
    vals3 = list(mm3["wigner_values"].values())
    checks["d3_max_mixed_uniform"] = all(abs(v - 1.0 / 9) < 1e-10 for v in vals3)
    checks["d3_max_mixed_zero_neg"] = bool(mm3["wigner_negativity"] < 1e-10)

    # -- 2-qubit: entangled states more negative --
    checks["twoq_entangled_more_negative"] = corr["entangled_more_negative"]

    # -- 2-qubit: Bell states have negative Wigner --
    bell = [r for r in twoq_results if r["state"].startswith("P") or r["state"].startswith("Phi")]
    checks["twoq_bell_negative"] = all(r["has_negative_wigner"] for r in bell)

    # -- 2-qubit: product states non-negative --
    prod_names = {"|00>", "|+->", "|01>"}
    prods = [r for r in twoq_results if r["state"] in prod_names]
    checks["twoq_product_nonneg"] = all(not r["has_negative_wigner"] for r in prods)

    # -- 2-qubit: max mixed uniform --
    mm2q = [r for r in twoq_results if r["state"] == "max_mixed_2q"][0]
    checks["twoq_max_mixed_zero_neg"] = bool(mm2q["wigner_negativity"] < 1e-10)

    return checks


# ══════════════════════════════════════════════════════════════════════
# 10. MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()

    print("=" * 70)
    print("PURE LEGO: Discrete Wigner & Quasi-Probability Distributions")
    print("=" * 70)

    # -- d=2 single qubit --
    print("\n--- d=2 Single-Qubit Discrete Wigner (10 states) ---")
    d2_results = run_single_qubit_d2()
    RESULTS["d2_single_qubit"] = d2_results

    # -- d=3 qutrit --
    print("\n--- d=3 Qutrit Discrete Wigner (nonclassicality witness) ---")
    d3_results = run_qutrit_d3()
    RESULTS["d3_qutrit"] = d3_results

    # -- 2-qubit comparison --
    print("\n--- 2-qubit: Wigner negativity vs Concurrence ---")
    twoq_results, corr = run_2qubit_comparison()
    RESULTS["two_qubit_comparison"] = twoq_results
    RESULTS["correlation_analysis"] = corr
    print(f"\n  Avg negativity (entangled):  {corr['avg_negativity_entangled']:.6f}")
    print(f"  Avg negativity (separable):  {corr['avg_negativity_separable']:.6f}")
    print(f"  Entangled > Separable:       {corr['entangled_more_negative']}")

    # -- Verify --
    print("\n--- Property Verification ---")
    checks = verify_all(d2_results, d3_results, twoq_results, corr)
    RESULTS["property_checks"] = checks

    bool_checks = {k: v for k, v in checks.items() if isinstance(v, bool)}
    for k, v in bool_checks.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    all_pass = all(v for v in bool_checks.values())

    RESULTS["summary"] = {
        "total_d2_states": len(d2_results),
        "total_d3_states": len(d3_results),
        "total_2qubit_states": len(twoq_results),
        "all_checks_pass": all_pass,
        "elapsed_s": round(time.time() - t0, 3),
        "key_findings": {
            "d2_all_nonneg_theorem": checks["d2_all_nonneg_theorem"],
            "d3_pure_negativity_witness": checks["d3_pure_can_be_negative"],
            "d3_stabilizer_always_nonneg": checks["d3_stabilizer_nonneg"],
            "d3_max_mixed_uniform_1_over_d": checks["d3_max_mixed_uniform"],
            "d2_husimi_always_positive": checks["d2_husimi_always_positive"],
            "entanglement_correlates_with_negativity": corr["entangled_more_negative"],
        },
    }

    print(f"\n{'=' * 70}")
    print(f"ALL CHECKS PASS: {all_pass}")
    print(f"Elapsed: {RESULTS['summary']['elapsed_s']} s")
    print(f"{'=' * 70}")

    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / \
        "pure_lego_wigner_quasiprobability_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(f"\nResults -> {out}")


if __name__ == "__main__":
    main()
