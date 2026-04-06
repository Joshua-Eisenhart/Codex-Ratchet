#!/usr/bin/env python3
"""
Deep Entanglement & Correlation Measures Simulation
====================================================
Runs the geometric engine for 10 cycles (80 steps) and computes
EVERY quantum correlation measure that exists for 2-qubit systems
at every single step.

Measures computed:
  ENTANGLEMENT: concurrence, EoF, negativity, log-negativity,
                relative entropy of entanglement, robustness
  CORRELATION:  mutual information, conditional entropy, coherent info,
                classical correlation, quantum discord, l1 coherence,
                relative entropy of coherence
  BELL:         CHSH value, Bell violation flag
  SPECTRUM:     entanglement spectrum, entanglement gap
  ENTROPY:      full panel (vN, linear, Renyi-2, min-entropy, purity)
                for rho_A, rho_B, and rho_AB
  PER-OPERATOR: average delta in key measures per operator
"""

import sys
import os
import json
import warnings
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, StageControls
from geometric_operators import partial_trace_A, partial_trace_B

warnings.filterwarnings("ignore", category=RuntimeWarning)


# ═══════════════════════════════════════════════════════════════════
# UTILITY: Von Neumann entropy (works for any square density matrix)
# ═══════════════════════════════════════════════════════════════════

def vn_entropy(rho):
    """Von Neumann entropy S(rho) = -Tr(rho log2 rho), in bits."""
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def quantum_relative_entropy(rho, sigma):
    """D(rho || sigma) = Tr[rho (log2 rho - log2 sigma)].
    Returns 0 if sigma has zero eigenvalues in support of rho.
    """
    rho_h = (rho + rho.conj().T) / 2
    sigma_h = (sigma + sigma.conj().T) / 2
    evals_r, evecs_r = np.linalg.eigh(rho_h)
    evals_s, evecs_s = np.linalg.eigh(sigma_h)
    # Clamp
    evals_r = np.maximum(evals_r, 0)
    evals_s = np.maximum(evals_s, 0)
    # Build log matrices in eigenbasis
    log_r = np.zeros_like(rho_h)
    for i, ev in enumerate(evals_r):
        if ev > 1e-15:
            log_r += np.log2(ev) * np.outer(evecs_r[:, i], evecs_r[:, i].conj())
    log_s = np.zeros_like(sigma_h)
    for i, ev in enumerate(evals_s):
        if ev > 1e-15:
            log_s += np.log2(ev) * np.outer(evecs_s[:, i], evecs_s[:, i].conj())
    result = np.real(np.trace(rho_h @ (log_r - log_s)))
    return max(0.0, float(result))


# ═══════════════════════════════════════════════════════════════════
# ENTANGLEMENT MEASURES
# ═══════════════════════════════════════════════════════════════════

def concurrence(rho):
    """Wootters concurrence for a 2-qubit state."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)), reverse=True)
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))


def entanglement_of_formation(rho):
    """EoF from concurrence via Wootters formula."""
    C = concurrence(rho)
    x = 0.5 + 0.5 * np.sqrt(max(1 - C**2, 0))
    if x < 1e-15 or x > 1 - 1e-15:
        return 0.0
    return float(-x * np.log2(x) - (1 - x) * np.log2(1 - x))


def negativity(rho):
    """Negativity: (||rho^{T_B}||_1 - 1) / 2."""
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(max(0, (np.sum(np.abs(evals)) - 1) / 2))


def log_negativity(rho):
    """Log-negativity: log2(||rho^{T_B}||_1)."""
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(np.log2(max(np.sum(np.abs(evals)), 1)))


def relative_entropy_of_entanglement(rho):
    """D(rho || closest separable). Approximated via product state rho_A x rho_B."""
    rho_A = partial_trace_B(rho)
    rho_B = partial_trace_A(rho)
    sigma = np.kron(rho_A, rho_B)
    return quantum_relative_entropy(rho, sigma)


def robustness_of_entanglement(rho):
    """R(rho) = min s such that (rho + s*I/4)/(1+s) is PPT."""
    for s in np.linspace(0, 2, 200):
        mixed = (rho + s * np.eye(4) / 4) / (1 + s)
        rho_pt = mixed.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
        if np.min(np.linalg.eigvalsh(rho_pt)) >= -1e-10:
            return float(s)
    return 2.0


# ═══════════════════════════════════════════════════════════════════
# CORRELATION MEASURES
# ═══════════════════════════════════════════════════════════════════

def quantum_mutual_information(rho_AB, rho_A, rho_B):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    return float(vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho_AB))


def conditional_entropy(rho_AB, rho_B):
    """S(A|B) = S(AB) - S(B)."""
    return float(vn_entropy(rho_AB) - vn_entropy(rho_B))


def coherent_information(rho_AB, rho_B):
    """I_c(A>B) = S(B) - S(AB). Negative of conditional entropy."""
    return float(vn_entropy(rho_B) - vn_entropy(rho_AB))


def classical_correlation(rho_AB, rho_A):
    """J(A|B) = max over B measurements of [S(A) - sum_k p_k S(A|k)].
    Optimized over Bloch sphere measurement bases on B.
    """
    s_A = vn_entropy(rho_A)
    best_J = 0.0
    for theta in np.linspace(0, np.pi, 20):
        for phi in np.linspace(0, 2 * np.pi, 20):
            m0 = np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)])
            m1 = np.array([-np.exp(-1j * phi) * np.sin(theta / 2), np.cos(theta / 2)])

            J = s_A
            for m in [m0, m1]:
                proj_B = np.outer(m, m.conj())
                proj_AB = np.kron(np.eye(2), proj_B)
                rho_post = proj_AB @ rho_AB @ proj_AB
                p = np.real(np.trace(rho_post))
                if p > 1e-15:
                    rho_A_cond = partial_trace_B(rho_post / p)
                    J -= p * vn_entropy(rho_A_cond)
            best_J = max(best_J, J)
    return float(best_J)


def quantum_discord(rho_AB, rho_A, rho_B):
    """D(A|B) = I(A:B) - J(A|B)."""
    MI = quantum_mutual_information(rho_AB, rho_A, rho_B)
    J = classical_correlation(rho_AB, rho_A)
    return float(MI - J)


def l1_coherence(rho):
    """Sum of off-diagonal magnitudes."""
    return float(np.sum(np.abs(rho)) - np.sum(np.abs(np.diag(rho))))


def relative_entropy_of_coherence(rho):
    """S(rho_diag) - S(rho)."""
    rho_diag = np.diag(np.diag(rho))
    return float(vn_entropy(rho_diag) - vn_entropy(rho))


# ═══════════════════════════════════════════════════════════════════
# BELL INEQUALITY
# ═══════════════════════════════════════════════════════════════════

def correlation_tensor(rho):
    """3x3 correlation tensor T_ij = Tr[rho (sigma_i x sigma_j)]."""
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    sigmas = [sx, sy, sz]
    T = np.zeros((3, 3))
    for i, si in enumerate(sigmas):
        for j, sj in enumerate(sigmas):
            T[i, j] = np.real(np.trace(rho @ np.kron(si, sj)))
    return T


def chsh_value(rho):
    """Maximum CHSH value over all measurement settings.
    B_max = 2 * sqrt(M1 + M2) where M1, M2 are two largest eigenvalues of T^T T.
    """
    T = correlation_tensor(rho)
    U = T.T @ T
    evals = sorted(np.real(np.linalg.eigvalsh(U)), reverse=True)
    return float(2 * np.sqrt(max(evals[0] + evals[1], 0)))


def bell_violation(rho):
    """True if CHSH > 2 (Bell inequality violated)."""
    return bool(chsh_value(rho) > 2.0)


# ═══════════════════════════════════════════════════════════════════
# ENTANGLEMENT SPECTRUM
# ═══════════════════════════════════════════════════════════════════

def entanglement_spectrum(rho_AB):
    """Schmidt coefficients from reduced state eigenvalues."""
    rho_A = partial_trace_B(rho_AB)
    evals = np.real(np.linalg.eigvalsh(rho_A))
    return sorted([float(max(e, 0)) for e in evals], reverse=True)


def entanglement_gap(rho_AB):
    """Gap between largest and second-largest Schmidt coefficient."""
    spec = entanglement_spectrum(rho_AB)
    if len(spec) > 1:
        return float(spec[0] - spec[1])
    return float(spec[0])


# ═══════════════════════════════════════════════════════════════════
# ENTROPY PANELS
# ═══════════════════════════════════════════════════════════════════

def full_entropy_panel(rho):
    """Full entropy characterization of a density matrix."""
    tr_rho2 = float(np.real(np.trace(rho @ rho)))
    max_eval = float(np.max(np.real(np.linalg.eigvalsh(rho))))
    return {
        "von_neumann": vn_entropy(rho),
        "linear": float(1 - tr_rho2),
        "renyi_2": float(-np.log2(max(tr_rho2, 1e-15))),
        "min_entropy": float(-np.log2(max(max_eval, 1e-15))),
        "purity": tr_rho2,
    }


# ═══════════════════════════════════════════════════════════════════
# NUMPY SANITIZER
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    return obj


# ═══════════════════════════════════════════════════════════════════
# MAIN SIMULATION
# ═══════════════════════════════════════════════════════════════════

def run_deep_measures(n_cycles=10):
    """Run engine for n_cycles (8 steps each) = 80 steps total.
    Compute ALL measures at every step.
    """
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()

    n_steps = n_cycles * 8  # 80

    # Storage
    ent = {k: [] for k in ["concurrence", "eof", "negativity", "log_negativity",
                            "relative_entropy_ent", "robustness"]}
    cor = {k: [] for k in ["mutual_information", "conditional_entropy",
                            "coherent_information", "classical_correlation",
                            "quantum_discord", "l1_coherence", "rel_entropy_coherence"]}
    bell_data = {"chsh_value": [], "bell_violated": []}
    spec = {"entanglement_spectrum": [], "entanglement_gap": []}
    ent_A = {k: [] for k in ["von_neumann", "linear", "renyi_2", "min_entropy", "purity"]}
    ent_B = {k: [] for k in ["von_neumann", "linear", "renyi_2", "min_entropy", "purity"]}
    ent_AB = {k: [] for k in ["von_neumann", "linear", "renyi_2", "min_entropy", "purity"]}

    # Per-operator delta tracking
    op_names = ["Ti", "Fe", "Te", "Fi"]
    op_deltas = {op: {"delta_concurrence": [], "delta_MI": [], "delta_discord": []}
                 for op in op_names}

    # We need to track which operator is applied at each step
    step_operators = []

    print(f"Running {n_cycles} cycles ({n_steps} steps)...")
    print("Computing all entanglement/correlation measures at each step...\n")

    for cycle in range(n_cycles):
        for step_in_cycle in range(8):
            global_step = cycle * 8 + step_in_cycle

            # --- Pre-step measures (for delta computation) ---
            rho_pre = state.rho_AB.copy()
            C_pre = concurrence(rho_pre)
            rho_A_pre = partial_trace_B(rho_pre)
            rho_B_pre = partial_trace_A(rho_pre)
            MI_pre = quantum_mutual_information(rho_pre, rho_A_pre, rho_B_pre)
            # Discord pre is expensive; compute only for delta tracking
            discord_pre = quantum_discord(rho_pre, rho_A_pre, rho_B_pre)

            # --- Step the engine ---
            history_len_before = len(state.history)
            state = engine.step(state)

            # Extract which operator was applied
            if len(state.history) > history_len_before:
                last_entry = state.history[-1]
                op_applied = last_entry.get("op_name", "unknown")
            else:
                op_applied = "unknown"
            step_operators.append(op_applied)

            # --- Post-step: extract joint state ---
            rho = state.rho_AB.copy()
            rho_A = partial_trace_B(rho)
            rho_B = partial_trace_A(rho)

            # --- ENTANGLEMENT ---
            C = concurrence(rho)
            ent["concurrence"].append(C)
            ent["eof"].append(entanglement_of_formation(rho))
            ent["negativity"].append(negativity(rho))
            ent["log_negativity"].append(log_negativity(rho))
            ent["relative_entropy_ent"].append(relative_entropy_of_entanglement(rho))
            ent["robustness"].append(robustness_of_entanglement(rho))

            # --- CORRELATION ---
            MI = quantum_mutual_information(rho, rho_A, rho_B)
            cor["mutual_information"].append(MI)
            cor["conditional_entropy"].append(conditional_entropy(rho, rho_B))
            cor["coherent_information"].append(coherent_information(rho, rho_B))
            cc = classical_correlation(rho, rho_A)
            cor["classical_correlation"].append(cc)
            disc = quantum_discord(rho, rho_A, rho_B)
            cor["quantum_discord"].append(disc)
            cor["l1_coherence"].append(l1_coherence(rho))
            cor["rel_entropy_coherence"].append(relative_entropy_of_coherence(rho))

            # --- BELL ---
            chsh = chsh_value(rho)
            bell_data["chsh_value"].append(chsh)
            bell_data["bell_violated"].append(bell_violation(rho))

            # --- SPECTRUM ---
            spec["entanglement_spectrum"].append(entanglement_spectrum(rho))
            spec["entanglement_gap"].append(entanglement_gap(rho))

            # --- ENTROPY PANELS ---
            panel_A = full_entropy_panel(rho_A)
            panel_B = full_entropy_panel(rho_B)
            panel_AB = full_entropy_panel(rho)
            for k in ent_A:
                ent_A[k].append(panel_A[k])
                ent_B[k].append(panel_B[k])
                ent_AB[k].append(panel_AB[k])

            # --- PER-OPERATOR DELTAS ---
            if op_applied in op_deltas:
                op_deltas[op_applied]["delta_concurrence"].append(C - C_pre)
                op_deltas[op_applied]["delta_MI"].append(MI - MI_pre)
                op_deltas[op_applied]["delta_discord"].append(disc - discord_pre)

            # Progress
            if (global_step + 1) % 10 == 0:
                print(f"  Step {global_step+1:3d}/{n_steps}: C={C:.4f}  N={ent['negativity'][-1]:.4f}  "
                      f"MI={MI:.4f}  CHSH={chsh:.4f}  D={disc:.4f}  op={op_applied}")

    # --- Per-operator effect summary ---
    per_op_summary = {}
    for op in op_names:
        per_op_summary[op] = {}
        for metric in ["delta_concurrence", "delta_MI", "delta_discord"]:
            vals = op_deltas[op][metric]
            if vals:
                per_op_summary[op][metric] = {
                    "mean": float(np.mean(vals)),
                    "std": float(np.std(vals)),
                    "min": float(np.min(vals)),
                    "max": float(np.max(vals)),
                    "n_applications": len(vals),
                }
            else:
                per_op_summary[op][metric] = {"mean": 0, "std": 0, "min": 0, "max": 0, "n_applications": 0}

    # --- Assemble output ---
    output = {
        "name": "deep_entanglement_measures",
        "n_steps": n_steps,
        "n_cycles": n_cycles,
        "step_operators": step_operators,
        "entanglement": ent,
        "correlation": cor,
        "bell": bell_data,
        "spectrum": spec,
        "entropy_A": ent_A,
        "entropy_B": ent_B,
        "entropy_AB": ent_AB,
        "per_operator_effect": per_op_summary,
    }

    return sanitize(output)


def print_summary(results):
    """Print a readable summary of the simulation."""
    n = results["n_steps"]
    print(f"\n{'='*72}")
    print(f"DEEP ENTANGLEMENT MEASURES — {n} steps across {results['n_cycles']} cycles")
    print(f"{'='*72}")

    def stat(arr):
        a = np.array(arr)
        return f"mean={np.mean(a):.4f}  std={np.std(a):.4f}  min={np.min(a):.4f}  max={np.max(a):.4f}"

    print("\n--- ENTANGLEMENT ---")
    for k, v in results["entanglement"].items():
        print(f"  {k:28s}: {stat(v)}")

    print("\n--- CORRELATION ---")
    for k, v in results["correlation"].items():
        print(f"  {k:28s}: {stat(v)}")

    print("\n--- BELL ---")
    chsh = results["bell"]["chsh_value"]
    violated = results["bell"]["bell_violated"]
    print(f"  {'chsh_value':28s}: {stat(chsh)}")
    print(f"  {'bell_violated':28s}: {sum(violated)}/{n} steps ({100*sum(violated)/n:.1f}%)")

    print("\n--- ENTANGLEMENT SPECTRUM ---")
    gaps = results["spectrum"]["entanglement_gap"]
    print(f"  {'entanglement_gap':28s}: {stat(gaps)}")

    print("\n--- ENTROPY rho_A ---")
    for k, v in results["entropy_A"].items():
        print(f"  {k:28s}: {stat(v)}")

    print("\n--- ENTROPY rho_B ---")
    for k, v in results["entropy_B"].items():
        print(f"  {k:28s}: {stat(v)}")

    print("\n--- ENTROPY rho_AB ---")
    for k, v in results["entropy_AB"].items():
        print(f"  {k:28s}: {stat(v)}")

    print("\n--- PER-OPERATOR EFFECTS ---")
    for op, metrics in results["per_operator_effect"].items():
        print(f"  {op}:")
        for metric, vals in metrics.items():
            print(f"    {metric:24s}: mean={vals['mean']:+.6f}  std={vals['std']:.6f}  "
                  f"[{vals['min']:+.6f}, {vals['max']:+.6f}]  (n={vals['n_applications']})")

    # Trajectory summary: first/last 5 steps
    print(f"\n--- TRAJECTORY SNAPSHOTS ---")
    print(f"  {'Step':>4s}  {'Op':>3s}  {'Concur':>7s}  {'Negat':>7s}  {'MI':>7s}  "
          f"{'Discord':>7s}  {'CHSH':>7s}  {'Bell?':>5s}")
    for i in list(range(min(5, n))) + (["..."] if n > 10 else []) + list(range(max(5, n-5), n)):
        if i == "...":
            print(f"  {'...':>4s}")
            continue
        print(f"  {i:4d}  {results['step_operators'][i]:>3s}  "
              f"{results['entanglement']['concurrence'][i]:7.4f}  "
              f"{results['entanglement']['negativity'][i]:7.4f}  "
              f"{results['correlation']['mutual_information'][i]:7.4f}  "
              f"{results['correlation']['quantum_discord'][i]:7.4f}  "
              f"{results['bell']['chsh_value'][i]:7.4f}  "
              f"{'YES' if results['bell']['bell_violated'][i] else 'no':>5s}")


if __name__ == "__main__":
    results = run_deep_measures(n_cycles=10)

    # Save
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "deep_entanglement_measures_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {out_path}")

    print_summary(results)
