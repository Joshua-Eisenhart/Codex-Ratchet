#!/usr/bin/env python3
"""
Entropy & Correlation Measure Sweep — Layers L4-L6
====================================================
Massive sweep testing every entropy form and correlation measure
against constraint layers L4 (chirality), L5 (four topologies),
L6 (su(2) noncommutation). The constraints FORCE which measures survive.

Output: a2_state/sim_results/entropy_type_sweep_L4_L6_results.json
"""

import sys
import os
import json
import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: entropy and correlation survival across L4-L6 is explored here by numeric layer sweeps, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "entropy-family sweeps, correlation measures, and layer-response numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState, TERRAINS, STAGE_OPERATOR_LUT
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    partial_trace_A, partial_trace_B,
    SIGMA_X, SIGMA_Y, SIGMA_Z,
    OPERATOR_MAP_4X4,
    _ensure_valid_density,
)
from hopf_manifold import (
    von_neumann_entropy_2x2, density_to_bloch,
    left_weyl_spinor, right_weyl_spinor,
)


# ═══════════════════════════════════════════════════════════════════
# ENTROPY FUNCTIONS — every type
# ═══════════════════════════════════════════════════════════════════

def _safe_evals(rho):
    """Get eigenvalues of a density matrix, sanitized."""
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    return np.maximum(evals, 0)


def von_neumann(rho):
    evals = _safe_evals(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def shannon(rho):
    """Shannon entropy of diagonal (populations)."""
    p = np.real(np.diag(rho))
    p = p[p > 1e-15]
    if len(p) == 0:
        return 0.0
    p = p / np.sum(p)
    return float(-np.sum(p * np.log2(p)))


def renyi(rho, alpha):
    """Renyi entropy S_alpha = (1/(1-alpha)) * log2(Tr(rho^alpha))."""
    evals = _safe_evals(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    if abs(alpha - 1.0) < 1e-10:
        return von_neumann(rho)
    val = np.sum(evals ** alpha)
    if val <= 0:
        return 0.0
    return float(np.log2(val) / (1 - alpha))


def min_entropy(rho):
    """Min-entropy = -log2(max eigenvalue) = Renyi(inf)."""
    evals = _safe_evals(rho)
    lam_max = np.max(evals)
    if lam_max < 1e-15:
        return 0.0
    return float(-np.log2(lam_max))


def max_entropy(rho):
    """Max-entropy = log2(rank) = Renyi(0)."""
    evals = _safe_evals(rho)
    rank = np.sum(evals > 1e-15)
    if rank == 0:
        return 0.0
    return float(np.log2(rank))


def linear_entropy(rho):
    """Linear entropy = (d/(d-1))*(1 - Tr(rho^2))."""
    d = rho.shape[0]
    purity_val = float(np.real(np.trace(rho @ rho)))
    if d <= 1:
        return 0.0
    return float((d / (d - 1)) * (1 - purity_val))


def tsallis(rho, q):
    """Tsallis entropy S_q = (1/(q-1))*(1 - Tr(rho^q))."""
    evals = _safe_evals(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0 or abs(q - 1.0) < 1e-10:
        return von_neumann(rho)
    return float((1 - np.sum(evals ** q)) / (q - 1))


def purity(rho):
    """Purity = Tr(rho^2)."""
    return float(np.real(np.trace(rho @ rho)))


# Registry: name -> (function, extra_args)
ENTROPY_REGISTRY = {
    "von_neumann":   (von_neumann, {}),
    "shannon":       (shannon, {}),
    "renyi_0.5":     (renyi, {"alpha": 0.5}),
    "renyi_2":       (renyi, {"alpha": 2}),
    "renyi_5":       (renyi, {"alpha": 5}),
    "renyi_10":      (renyi, {"alpha": 10}),
    "min_entropy":   (min_entropy, {}),
    "max_entropy":   (max_entropy, {}),
    "linear_entropy":(linear_entropy, {}),
    "tsallis_0.5":   (tsallis, {"q": 0.5}),
    "tsallis_2":     (tsallis, {"q": 2}),
    "purity":        (purity, {}),
}


def compute_all_entropies(rho):
    """Compute every entropy type on rho. Returns dict."""
    result = {}
    for name, (fn, kwargs) in ENTROPY_REGISTRY.items():
        try:
            result[name] = fn(rho, **kwargs)
        except Exception as e:
            result[name] = f"ERROR: {e}"
    return result


# ═══════════════════════════════════════════════════════════════════
# CORRELATION MEASURES
# ═══════════════════════════════════════════════════════════════════

def concurrence_4x4(rho):
    """Concurrence for a 4x4 density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0))
    evals = sorted(evals, reverse=True)
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))


def negativity(rho_AB):
    """Negativity via partial transpose."""
    d = int(np.sqrt(rho_AB.shape[0]))
    rho_pt = rho_AB.reshape(d, d, d, d).transpose(0, 3, 2, 1).reshape(d * d, d * d)
    evals = np.linalg.eigvalsh(rho_pt)
    return float((np.sum(np.abs(evals)) - 1) / 2)


def log_negativity(rho_AB):
    """Log-negativity = log2(2*N + 1)."""
    d = int(np.sqrt(rho_AB.shape[0]))
    rho_pt = rho_AB.reshape(d, d, d, d).transpose(0, 3, 2, 1).reshape(d * d, d * d)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(np.log2(max(np.sum(np.abs(evals)), 1)))


def partial_trace_B_general(rho_AB, dA, dB):
    """General partial trace over B for dA x dB system."""
    rho_reshaped = rho_AB.reshape(dA, dB, dA, dB)
    return np.trace(rho_reshaped, axis1=1, axis2=3)


def quantum_discord_approx(rho_AB, rho_A, rho_B):
    """Approximate quantum discord = I(A:B) - classical correlations."""
    MI = von_neumann(rho_A) + von_neumann(rho_B) - von_neumann(rho_AB)
    d = rho_B.shape[0]
    dA = rho_A.shape[0]
    classical_corr = 0.0
    for k in range(d):
        proj = np.zeros((d, d), dtype=complex)
        proj[k, k] = 1.0
        proj_AB = np.kron(np.eye(dA, dtype=complex), proj)
        rho_post = proj_AB @ rho_AB @ proj_AB
        p_k = np.real(np.trace(rho_post))
        if p_k > 1e-15:
            rho_A_post = partial_trace_B_general(rho_post / p_k, dA, d)
            classical_corr += p_k * von_neumann(rho_A_post)
    classical_MI = von_neumann(rho_A) - classical_corr
    return float(MI - classical_MI)


def entanglement_of_formation(rho_AB):
    """EoF = h(0.5 + 0.5*sqrt(1 - C^2)) where C = concurrence."""
    C = concurrence_4x4(rho_AB)
    x = 0.5 + 0.5 * np.sqrt(max(1 - C ** 2, 0))
    if x < 1e-15 or x > 1 - 1e-15:
        return 0.0
    return float(-x * np.log2(x) - (1 - x) * np.log2(1 - x))


def mutual_information(rho_AB, rho_A, rho_B):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    return float(von_neumann(rho_A) + von_neumann(rho_B) - von_neumann(rho_AB))


def classical_correlation(rho_AB, rho_A, rho_B):
    """Classical correlation I_c = I(A:B) - discord."""
    MI = mutual_information(rho_AB, rho_A, rho_B)
    disc = quantum_discord_approx(rho_AB, rho_A, rho_B)
    return float(MI - disc)


def conditional_entropy(rho_AB, rho_B):
    """S(A|B) = S(AB) - S(B)."""
    return float(von_neumann(rho_AB) - von_neumann(rho_B))


def compute_all_correlations(rho_AB, rho_A, rho_B):
    """Compute every correlation measure. Returns dict."""
    result = {}
    try:
        result["concurrence"] = concurrence_4x4(rho_AB)
    except Exception as e:
        result["concurrence"] = f"ERROR: {e}"
    try:
        result["negativity"] = negativity(rho_AB)
    except Exception as e:
        result["negativity"] = f"ERROR: {e}"
    try:
        result["log_negativity"] = log_negativity(rho_AB)
    except Exception as e:
        result["log_negativity"] = f"ERROR: {e}"
    try:
        result["discord"] = quantum_discord_approx(rho_AB, rho_A, rho_B)
    except Exception as e:
        result["discord"] = f"ERROR: {e}"
    try:
        result["entanglement_of_formation"] = entanglement_of_formation(rho_AB)
    except Exception as e:
        result["entanglement_of_formation"] = f"ERROR: {e}"
    try:
        result["mutual_information"] = mutual_information(rho_AB, rho_A, rho_B)
    except Exception as e:
        result["mutual_information"] = f"ERROR: {e}"
    try:
        result["classical_correlation"] = classical_correlation(rho_AB, rho_A, rho_B)
    except Exception as e:
        result["classical_correlation"] = f"ERROR: {e}"
    try:
        result["conditional_entropy"] = conditional_entropy(rho_AB, rho_B)
    except Exception as e:
        result["conditional_entropy"] = f"ERROR: {e}"
    return result


# ═══════════════════════════════════════════════════════════════════
# SANITIZE — make everything JSON-serializable
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to native Python."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    if isinstance(obj, np.complexfloating):
        return {"re": float(np.real(obj)), "im": float(np.imag(obj))}
    return obj


# ═══════════════════════════════════════════════════════════════════
# L4: CHIRALITY — which measures detect L/R anti-alignment?
# ═══════════════════════════════════════════════════════════════════

def run_L4_chirality():
    """L4 sweep: chirality detection across entropy and correlation measures."""
    print("=" * 70)
    print("L4: CHIRALITY SWEEP")
    print("=" * 70)

    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()

    # --- Run engine 5 cycles (5 * 8 = 40 steps) ---
    for cycle in range(5):
        for si in range(8):
            state = engine.step(state, stage_idx=si)

    rho_L = state.rho_L
    rho_R = state.rho_R
    rho_AB = state.rho_AB

    # 1. All entropy types on rho_L and rho_R
    entropy_L = compute_all_entropies(rho_L)
    entropy_R = compute_all_entropies(rho_R)
    print("\n  Entropy on rho_L:", {k: f"{v:.6f}" if isinstance(v, float) else v for k, v in entropy_L.items()})
    print("  Entropy on rho_R:", {k: f"{v:.6f}" if isinstance(v, float) else v for k, v in entropy_R.items()})

    # 2. L/R asymmetry for each entropy type
    lr_asymmetry = {}
    for name in ENTROPY_REGISTRY:
        vL = entropy_L.get(name, 0)
        vR = entropy_R.get(name, 0)
        if isinstance(vL, (int, float)) and isinstance(vR, (int, float)):
            lr_asymmetry[name] = abs(vL - vR)
        else:
            lr_asymmetry[name] = "ERROR"
    print("\n  L/R asymmetry |S(L)-S(R)|:")
    for k, v in sorted(lr_asymmetry.items(), key=lambda x: x[1] if isinstance(x[1], float) else -1, reverse=True):
        print(f"    {k:20s}: {v:.8f}" if isinstance(v, float) else f"    {k:20s}: {v}")

    # 3. NEGATIVE: force L=R (set psi_R = psi_L after each cycle)
    engine_neg = GeometricEngine(engine_type=1)
    state_neg = engine_neg.init_state()
    for cycle in range(5):
        for si in range(8):
            state_neg = engine_neg.step(state_neg, stage_idx=si)
        # Force L=R by replacing rho_AB with product state from rho_L only
        rho_L_neg = state_neg.rho_L
        forced_rho_AB = np.kron(rho_L_neg, rho_L_neg)
        forced_rho_AB = _ensure_valid_density(forced_rho_AB)
        state_neg = EngineState(
            psi_L=state_neg.psi_L, psi_R=state_neg.psi_L,  # force R=L
            rho_AB=forced_rho_AB,
            eta=state_neg.eta, theta1=state_neg.theta1, theta2=state_neg.theta2,
            stage_idx=state_neg.stage_idx, engine_type=state_neg.engine_type,
            history=state_neg.history,
        )

    rho_L_forced = state_neg.rho_L
    rho_R_forced = state_neg.rho_R
    entropy_L_forced = compute_all_entropies(rho_L_forced)
    entropy_R_forced = compute_all_entropies(rho_R_forced)

    chirality_loss_detection = {}
    for name in ENTROPY_REGISTRY:
        vL = entropy_L_forced.get(name, 0)
        vR = entropy_R_forced.get(name, 0)
        if isinstance(vL, (int, float)) and isinstance(vR, (int, float)):
            chirality_loss_detection[name] = {
                "forced_asymmetry": abs(vL - vR),
                "original_asymmetry": lr_asymmetry[name] if isinstance(lr_asymmetry[name], float) else 0,
                "detected_loss": abs(vL - vR) < 1e-10 and (isinstance(lr_asymmetry[name], float) and lr_asymmetry[name] > 1e-10),
            }
    print("\n  Chirality loss detection (L=R forced):")
    for k, v in chirality_loss_detection.items():
        det = "YES" if v["detected_loss"] else "no"
        print(f"    {k:20s}: forced_asym={v['forced_asymmetry']:.8f}  orig_asym={v['original_asymmetry']:.8f}  detect={det}")

    # 4. Correlation measures on rho_AB (natural)
    corr_natural = compute_all_correlations(rho_AB, rho_L, rho_R)
    print("\n  Correlation measures (natural chirality):")
    for k, v in corr_natural.items():
        print(f"    {k:30s}: {v:.8f}" if isinstance(v, float) else f"    {k:30s}: {v}")

    # 5. Correlation measures with L=R forced
    rho_AB_forced = state_neg.rho_AB
    rho_L_f = state_neg.rho_L
    rho_R_f = state_neg.rho_R
    corr_forced = compute_all_correlations(rho_AB_forced, rho_L_f, rho_R_f)
    print("\n  Correlation measures (L=R forced):")
    for k, v in corr_forced.items():
        print(f"    {k:30s}: {v:.8f}" if isinstance(v, float) else f"    {k:30s}: {v}")

    corr_change = {}
    for k in corr_natural:
        vn = corr_natural[k]
        vf = corr_forced[k]
        if isinstance(vn, (int, float)) and isinstance(vf, (int, float)):
            corr_change[k] = {"natural": vn, "forced": vf, "delta": abs(vn - vf)}
        else:
            corr_change[k] = {"natural": str(vn), "forced": str(vf), "delta": "ERROR"}

    print("\n  Correlation change from chirality forcing:")
    for k, v in corr_change.items():
        if isinstance(v["delta"], float):
            print(f"    {k:30s}: delta={v['delta']:.8f}")
        else:
            print(f"    {k:30s}: {v['delta']}")

    return {
        "entropy_L": entropy_L,
        "entropy_R": entropy_R,
        "lr_asymmetry": lr_asymmetry,
        "chirality_loss_detection": chirality_loss_detection,
        "correlations_natural": corr_natural,
        "correlations_forced_L_eq_R": corr_forced,
        "correlation_change": corr_change,
    }


# ═══════════════════════════════════════════════════════════════════
# L5: FOUR TOPOLOGIES — which measures distinguish the 4 operators?
# ═══════════════════════════════════════════════════════════════════

def run_L5_topologies():
    """L5 sweep: operator discrimination via entropy and correlation measures."""
    print("\n" + "=" * 70)
    print("L5: FOUR TOPOLOGIES SWEEP")
    print("=" * 70)

    # Build a reference state from 2 cycles of engine
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    for cycle in range(2):
        for si in range(8):
            state = engine.step(state, stage_idx=si)

    rho_2x2 = state.rho_L.copy()
    rho_4x4 = state.rho_AB.copy()

    ops_2x2 = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}

    # 6. Apply each 2x2 operator to same input, compute all entropies
    op_entropies_2x2 = {}
    for op_name, op_fn in ops_2x2.items():
        rho_out = op_fn(rho_2x2)
        op_entropies_2x2[op_name] = compute_all_entropies(rho_out)

    print("\n  Per-operator entropy (2x2):")
    for op_name, ents in op_entropies_2x2.items():
        print(f"    {op_name}: {', '.join(f'{k}={v:.4f}' if isinstance(v, float) else f'{k}={v}' for k, v in ents.items())}")

    # 7. Pairwise discrimination for each entropy type
    op_names = list(ops_2x2.keys())
    pairwise_discrim = {}
    for i in range(len(op_names)):
        for j in range(i + 1, len(op_names)):
            pair = f"{op_names[i]}_vs_{op_names[j]}"
            pairwise_discrim[pair] = {}
            for etype in ENTROPY_REGISTRY:
                v1 = op_entropies_2x2[op_names[i]].get(etype, 0)
                v2 = op_entropies_2x2[op_names[j]].get(etype, 0)
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    pairwise_discrim[pair][etype] = abs(v1 - v2)
                else:
                    pairwise_discrim[pair][etype] = "ERROR"

    print("\n  Pairwise discrimination |S_op1 - S_op2| (2x2):")
    for pair, discrim in pairwise_discrim.items():
        best = max((v for v in discrim.values() if isinstance(v, float)), default=0)
        best_name = [k for k, v in discrim.items() if isinstance(v, float) and abs(v - best) < 1e-15]
        print(f"    {pair:20s}: best discriminator = {best_name[0] if best_name else 'none'} ({best:.6f})")

    # 8. Key comparisons
    key_pairs = {
        "Ti_vs_Fe": "Ti vs Fe (constraint vs release)",
        "Te_vs_Fi": "Te vs Fi (explore vs filter)",
        "Ti_vs_Te": "Dissipative(Ti) vs Dissipative(Te)",
        "Fe_vs_Fi": "Unitary(Fe) vs Unitary(Fi)",
    }
    print("\n  Key discriminations:")
    for pair_key, label in key_pairs.items():
        if pair_key in pairwise_discrim:
            d = pairwise_discrim[pair_key]
            ranked = sorted([(k, v) for k, v in d.items() if isinstance(v, float)], key=lambda x: x[1], reverse=True)
            print(f"    {label}:")
            for rank_name, rank_val in ranked[:3]:
                print(f"      {rank_name:20s}: {rank_val:.8f}")

    # 9. 4x4 operator application + correlation measures
    op_correlations_4x4 = {}
    for op_name in ops_2x2:
        op_fn_4x4 = OPERATOR_MAP_4X4[op_name]
        rho_out_4x4 = op_fn_4x4(rho_4x4)
        rho_out_4x4 = _ensure_valid_density(rho_out_4x4)
        rho_A = _ensure_valid_density(partial_trace_B(rho_out_4x4))
        rho_B = _ensure_valid_density(partial_trace_A(rho_out_4x4))
        op_correlations_4x4[op_name] = compute_all_correlations(rho_out_4x4, rho_A, rho_B)

    print("\n  Per-operator correlations (4x4):")
    for op_name, corrs in op_correlations_4x4.items():
        vals = ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in corrs.items())
        print(f"    {op_name}: {vals}")

    # Pairwise correlation discrimination
    corr_pairwise = {}
    for i in range(len(op_names)):
        for j in range(i + 1, len(op_names)):
            pair = f"{op_names[i]}_vs_{op_names[j]}"
            corr_pairwise[pair] = {}
            for meas in op_correlations_4x4[op_names[i]]:
                v1 = op_correlations_4x4[op_names[i]][meas]
                v2 = op_correlations_4x4[op_names[j]][meas]
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    corr_pairwise[pair][meas] = abs(v1 - v2)

    print("\n  Correlation discrimination (4x4):")
    for pair, discrim in corr_pairwise.items():
        if discrim:
            best_val = max(discrim.values())
            best_name = [k for k, v in discrim.items() if abs(v - best_val) < 1e-15]
            print(f"    {pair:20s}: best = {best_name[0]} ({best_val:.6f})")

    return {
        "op_entropies_2x2": op_entropies_2x2,
        "pairwise_discrimination_2x2": pairwise_discrim,
        "op_correlations_4x4": op_correlations_4x4,
        "correlation_discrimination_4x4": corr_pairwise,
    }


# ═══════════════════════════════════════════════════════════════════
# L6: su(2) ALGEBRA — noncommutation sensitivity
# ═══════════════════════════════════════════════════════════════════

def run_L6_noncommutation():
    """L6 sweep: which measures detect operator noncommutation?"""
    print("\n" + "=" * 70)
    print("L6: su(2) NONCOMMUTATION SWEEP")
    print("=" * 70)

    # Reference state from engine
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    for cycle in range(2):
        for si in range(8):
            state = engine.step(state, stage_idx=si)

    rho_2x2 = state.rho_L.copy()
    rho_4x4 = state.rho_AB.copy()

    # 10. Ti then Fi vs Fi then Ti (2x2)
    rho_TiFi = apply_Fi(apply_Ti(rho_2x2))
    rho_FiTi = apply_Ti(apply_Fi(rho_2x2))

    entropy_TiFi = compute_all_entropies(rho_TiFi)
    entropy_FiTi = compute_all_entropies(rho_FiTi)

    # 4x4 versions
    rho_TiFi_4x4 = OPERATOR_MAP_4X4["Fi"](OPERATOR_MAP_4X4["Ti"](rho_4x4))
    rho_TiFi_4x4 = _ensure_valid_density(rho_TiFi_4x4)
    rho_FiTi_4x4 = OPERATOR_MAP_4X4["Ti"](OPERATOR_MAP_4X4["Fi"](rho_4x4))
    rho_FiTi_4x4 = _ensure_valid_density(rho_FiTi_4x4)

    rho_A_TiFi = _ensure_valid_density(partial_trace_B(rho_TiFi_4x4))
    rho_B_TiFi = _ensure_valid_density(partial_trace_A(rho_TiFi_4x4))
    rho_A_FiTi = _ensure_valid_density(partial_trace_B(rho_FiTi_4x4))
    rho_B_FiTi = _ensure_valid_density(partial_trace_A(rho_FiTi_4x4))

    corr_TiFi = compute_all_correlations(rho_TiFi_4x4, rho_A_TiFi, rho_B_TiFi)
    corr_FiTi = compute_all_correlations(rho_FiTi_4x4, rho_A_FiTi, rho_B_FiTi)

    # 11. Discrimination for each measure
    entropy_discrim = {}
    for name in ENTROPY_REGISTRY:
        v1 = entropy_TiFi.get(name, 0)
        v2 = entropy_FiTi.get(name, 0)
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            entropy_discrim[name] = abs(v1 - v2)
        else:
            entropy_discrim[name] = "ERROR"

    corr_discrim = {}
    for name in corr_TiFi:
        v1 = corr_TiFi[name]
        v2 = corr_FiTi[name]
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            corr_discrim[name] = abs(v1 - v2)
        else:
            corr_discrim[name] = "ERROR"

    print("\n  Entropy discrimination |S(TiFi) - S(FiTi)| (2x2):")
    ranked_ent = sorted([(k, v) for k, v in entropy_discrim.items() if isinstance(v, float)], key=lambda x: x[1], reverse=True)
    for k, v in ranked_ent:
        print(f"    {k:20s}: {v:.8f}")

    print("\n  Correlation discrimination |C(TiFi) - C(FiTi)| (4x4):")
    ranked_corr = sorted([(k, v) for k, v in corr_discrim.items() if isinstance(v, float)], key=lambda x: x[1], reverse=True)
    for k, v in ranked_corr:
        print(f"    {k:30s}: {v:.8f}")

    # 12. NEGATIVE: commuting operators (all Z-axis rotations)
    def apply_Uz(rho, angle=0.3):
        U = np.array([[np.exp(-1j * angle / 2), 0],
                       [0, np.exp(1j * angle / 2)]], dtype=complex)
        return _ensure_valid_density(U @ rho @ U.conj().T)

    def apply_Uz2(rho, angle=0.5):
        U = np.array([[np.exp(-1j * angle / 2), 0],
                       [0, np.exp(1j * angle / 2)]], dtype=complex)
        return _ensure_valid_density(U @ rho @ U.conj().T)

    rho_comm_AB = apply_Uz2(apply_Uz(rho_2x2))
    rho_comm_BA = apply_Uz(apply_Uz2(rho_2x2))

    entropy_comm_AB = compute_all_entropies(rho_comm_AB)
    entropy_comm_BA = compute_all_entropies(rho_comm_BA)

    commuting_discrim = {}
    for name in ENTROPY_REGISTRY:
        v1 = entropy_comm_AB.get(name, 0)
        v2 = entropy_comm_BA.get(name, 0)
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            commuting_discrim[name] = abs(v1 - v2)
        else:
            commuting_discrim[name] = "ERROR"

    # Also do 4x4 commuting test using Fe (Uz) at different angles
    def apply_Fe_4x4_angle(rho_AB, phi):
        return _ensure_valid_density(OPERATOR_MAP_4X4["Fe"](rho_AB, phi=phi))

    rho_comm_4x4_AB = apply_Fe_4x4_angle(apply_Fe_4x4_angle(rho_4x4, 0.3), 0.5)
    rho_comm_4x4_BA = apply_Fe_4x4_angle(apply_Fe_4x4_angle(rho_4x4, 0.5), 0.3)
    rho_comm_4x4_AB = _ensure_valid_density(rho_comm_4x4_AB)
    rho_comm_4x4_BA = _ensure_valid_density(rho_comm_4x4_BA)

    rho_A_cAB = _ensure_valid_density(partial_trace_B(rho_comm_4x4_AB))
    rho_B_cAB = _ensure_valid_density(partial_trace_A(rho_comm_4x4_AB))
    rho_A_cBA = _ensure_valid_density(partial_trace_B(rho_comm_4x4_BA))
    rho_B_cBA = _ensure_valid_density(partial_trace_A(rho_comm_4x4_BA))

    corr_comm_AB = compute_all_correlations(rho_comm_4x4_AB, rho_A_cAB, rho_B_cAB)
    corr_comm_BA = compute_all_correlations(rho_comm_4x4_BA, rho_A_cBA, rho_B_cBA)

    corr_commuting_discrim = {}
    for name in corr_comm_AB:
        v1 = corr_comm_AB[name]
        v2 = corr_comm_BA[name]
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            corr_commuting_discrim[name] = abs(v1 - v2)

    print("\n  NEGATIVE: commuting operators (Uz at different angles):")
    print("    Entropy discrimination (should be ~0):")
    for k, v in commuting_discrim.items():
        flag = " <-- NONZERO!" if isinstance(v, float) and v > 1e-10 else ""
        print(f"      {k:20s}: {v:.10f}{flag}" if isinstance(v, float) else f"      {k:20s}: {v}")

    print("    Correlation discrimination (should be ~0):")
    for k, v in corr_commuting_discrim.items():
        flag = " <-- NONZERO!" if v > 1e-10 else ""
        print(f"      {k:30s}: {v:.10f}{flag}")

    # 13. Most sensitive measures
    all_noncomm = {}
    for k, v in entropy_discrim.items():
        if isinstance(v, float):
            all_noncomm[f"entropy_{k}"] = v
    for k, v in corr_discrim.items():
        if isinstance(v, float):
            all_noncomm[f"corr_{k}"] = v

    ranked_noncomm = sorted(all_noncomm.items(), key=lambda x: x[1], reverse=True)
    print("\n  NONCOMMUTATION SENSITIVITY RANKING (all measures):")
    for i, (k, v) in enumerate(ranked_noncomm):
        print(f"    {i+1:2d}. {k:40s}: {v:.8f}")

    return {
        "entropy_TiFi": entropy_TiFi,
        "entropy_FiTi": entropy_FiTi,
        "entropy_discrimination": entropy_discrim,
        "correlation_TiFi": corr_TiFi,
        "correlation_FiTi": corr_FiTi,
        "correlation_discrimination": corr_discrim,
        "commuting_entropy_discrimination": commuting_discrim,
        "commuting_correlation_discrimination": corr_commuting_discrim,
        "noncommutation_sensitivity_ranking": dict(ranked_noncomm),
    }


# ═══════════════════════════════════════════════════════════════════
# CROSS-LAYER RANKING
# ═══════════════════════════════════════════════════════════════════

def cross_layer_ranking(L4, L5, L6):
    """Rank all measures by total discrimination power across L4+L5+L6."""
    print("\n" + "=" * 70)
    print("CROSS-LAYER RANKING")
    print("=" * 70)

    measure_scores = {}

    # L4 contribution: LR asymmetry + correlation change
    lr_asym = L4.get("lr_asymmetry", {})
    for k, v in lr_asym.items():
        key = f"entropy_{k}"
        if isinstance(v, float):
            measure_scores[key] = measure_scores.get(key, 0) + v

    corr_change = L4.get("correlation_change", {})
    for k, v in corr_change.items():
        key = f"corr_{k}"
        delta = v.get("delta", 0) if isinstance(v, dict) else 0
        if isinstance(delta, (int, float)):
            measure_scores[key] = measure_scores.get(key, 0) + delta

    # L5 contribution: mean pairwise discrimination
    pairwise_2x2 = L5.get("pairwise_discrimination_2x2", {})
    for pair, discrim in pairwise_2x2.items():
        for etype, val in discrim.items():
            key = f"entropy_{etype}"
            if isinstance(val, (int, float)):
                measure_scores[key] = measure_scores.get(key, 0) + val

    corr_4x4 = L5.get("correlation_discrimination_4x4", {})
    for pair, discrim in corr_4x4.items():
        for meas, val in discrim.items():
            key = f"corr_{meas}"
            if isinstance(val, (int, float)):
                measure_scores[key] = measure_scores.get(key, 0) + val

    # L6 contribution: noncommutation discrimination
    ent_disc = L6.get("entropy_discrimination", {})
    for k, v in ent_disc.items():
        key = f"entropy_{k}"
        if isinstance(v, (int, float)):
            measure_scores[key] = measure_scores.get(key, 0) + v

    corr_disc = L6.get("correlation_discrimination", {})
    for k, v in corr_disc.items():
        key = f"corr_{k}"
        if isinstance(v, (int, float)):
            measure_scores[key] = measure_scores.get(key, 0) + v

    # Rank
    ranked = sorted(measure_scores.items(), key=lambda x: x[1], reverse=True)

    print("\n  TOTAL DISCRIMINATION POWER (L4+L5+L6):")
    print("  " + "-" * 60)
    for i, (k, v) in enumerate(ranked):
        status = "SURVIVES" if v > 0.01 else "KILLED"
        print(f"    {i+1:2d}. {k:40s}: {v:.8f}  [{status}]")

    # Layer-by-layer survival check
    survival = {}
    for k, total_v in ranked:
        layers_active = []
        # Check L4
        base_name = k.replace("entropy_", "").replace("corr_", "")
        if k.startswith("entropy_"):
            if base_name in lr_asym and isinstance(lr_asym[base_name], float) and lr_asym[base_name] > 1e-10:
                layers_active.append("L4")
            l5_sum = sum(d.get(base_name, 0) for d in pairwise_2x2.values() if isinstance(d.get(base_name, 0), float))
            if l5_sum > 1e-10:
                layers_active.append("L5")
            if base_name in ent_disc and isinstance(ent_disc[base_name], float) and ent_disc[base_name] > 1e-10:
                layers_active.append("L6")
        elif k.startswith("corr_"):
            if base_name in corr_change:
                cc = corr_change[base_name]
                if isinstance(cc, dict) and isinstance(cc.get("delta", 0), float) and cc["delta"] > 1e-10:
                    layers_active.append("L4")
            l5_sum = sum(d.get(base_name, 0) for d in corr_4x4.values() if isinstance(d.get(base_name, 0), float))
            if l5_sum > 1e-10:
                layers_active.append("L5")
            if base_name in corr_disc and isinstance(corr_disc[base_name], float) and corr_disc[base_name] > 1e-10:
                layers_active.append("L6")

        survival[k] = {
            "total_score": total_v,
            "active_layers": layers_active,
            "survives_all": len(layers_active) == 3,
        }

    print("\n  LAYER SURVIVAL:")
    for k, info in survival.items():
        layers_str = "+".join(info["active_layers"]) if info["active_layers"] else "NONE"
        tag = " *** UNIVERSAL ***" if info["survives_all"] else ""
        print(f"    {k:40s}: active at [{layers_str}]{tag}")

    return {
        "ranked_scores": dict(ranked),
        "survival": survival,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("ENTROPY & CORRELATION MEASURE SWEEP — L4, L5, L6")
    print("=" * 70)

    L4 = run_L4_chirality()
    L5 = run_L5_topologies()
    L6 = run_L6_noncommutation()
    ranking = cross_layer_ranking(L4, L5, L6)

    results = sanitize({
        "L4_chirality": L4,
        "L5_topologies": L5,
        "L6_noncommutation": L6,
        "cross_layer_ranking": ranking,
    })

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entropy_type_sweep_L4_L6_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")
    print("DONE.")
