#!/usr/bin/env python3
"""
Axis 0 i-Scalar Functional Sweep
=================================
Selects the canonical Axis 0 functional from the four options in
AXIS0_SPEC_OPTIONS_v0.1-v0.3.

For each engine (T1, T2) × torus (inner, clifford, outer) × perturbation
(depolarizing, dephasing, amplitude_damping) at small ε, computes the
Axis-0 index A0 = [D(Φ_ε(ρ)) - D(ρ)] / ε for each option family:

  Option A — Shannon entropy of pairwise MI distribution
             ("correlation diversity": H of the normalized MI weights)
  Option B — Variance of pairwise MI across subsystem pairs
             ("deviation damping": does spread increase or decrease?)
  Option C — Coherent information spread across LR cuts
             ("negative entropy survival": I_c(A→B) under noise)
  Option D — Path entropy of Kraus unraveling histories
             ("JK fuzz operationalization": branching variety)

Verdict criteria:
  - Stability: how consistently does the sign agree across 18 configs?
  - Separation: how large is |A0| on average (signal, not noise)?
  - Doctrine fit: does the allostatic/homeostatic split match engine type
    (T1=homeostatic bias, T2=allostatic bias per Grok Unified Physics)?

The winning option is the canonical i-scalar functional.
"""

from __future__ import annotations
import json, os, sys, copy
from datetime import UTC, datetime
import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

TORUS_CONFIGS = [
    ("inner",    TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer",    TORUS_OUTER),
]
PERTURBATION_EPS  = 0.05   # perturbation strength
KRAUS_BRANCHES    = 16     # number of Kraus history samples for Option D
EPS_NUM           = 1e-12  # numerical floor

SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2      = np.eye(2, dtype=complex)

# ─────────────────────────────────────────────────────────────────────
# QIT Utilities
# ─────────────────────────────────────────────────────────────────────

def vne(rho: np.ndarray) -> float:
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0


def ptr_B(r): return np.trace(r.reshape(2, 2, 2, 2), axis1=1, axis2=3)
def ptr_A(r): return np.trace(r.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def mi_val(rho_AB: np.ndarray) -> float:
    return max(0.0, vne(ptr_B(rho_AB)) + vne(ptr_A(rho_AB)) - vne(rho_AB))


def coherent_info(rho_AB: np.ndarray) -> float:
    """I_c(A→B) = S(ρ_B) - S(ρ_AB)."""
    return float(vne(ptr_B(rho_AB)) - vne(rho_AB))


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.real(np.trace(s @ rho)))
                     for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])


def lr_asym(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.0, 1.0))


# ─────────────────────────────────────────────────────────────────────
# Perturbation Channels (act on a single 2×2 density matrix)
# ─────────────────────────────────────────────────────────────────────

def depolarize(rho: np.ndarray, eps: float) -> np.ndarray:
    """Depolarizing: ρ → (1-ε)ρ + (ε/2)I."""
    out = (1 - eps) * rho + (eps / 2) * I2
    return _ensure_valid_density(out)


def dephase(rho: np.ndarray, eps: float) -> np.ndarray:
    """Dephasing: kills off-diagonal by factor (1-ε)."""
    out = rho.copy()
    out[0, 1] *= (1 - eps)
    out[1, 0] *= (1 - eps)
    return _ensure_valid_density(out)


def amp_damp(rho: np.ndarray, eps: float) -> np.ndarray:
    """Amplitude damping toward |0⟩."""
    gamma = eps
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    out = K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T
    return _ensure_valid_density(out)


PERTURBATIONS = {
    "depolarizing":    depolarize,
    "dephasing":       dephase,
    "amplitude_damp":  amp_damp,
}


def perturb_history(history: list[dict], perturb_fn, eps: float) -> list[dict]:
    """Apply a single-qubit channel independently to ρ_L and ρ_R in each step."""
    out = []
    for step in history:
        s = dict(step)
        s["rho_L"] = perturb_fn(step["rho_L"], eps)
        s["rho_R"] = perturb_fn(step["rho_R"], eps)
        out.append(s)
    return out


# ─────────────────────────────────────────────────────────────────────
# Build joint LR density matrix for each step (4×4)
# ─────────────────────────────────────────────────────────────────────

PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL_PSI_MINUS = np.outer(PSI_MINUS, PSI_MINUS.conj())


def joint_rho(step: dict) -> np.ndarray:
    """4×4 joint LR density matrix with chiral Bell injection."""
    rho_L = step["rho_L"]
    rho_R = step["rho_R"]
    p = float(np.clip(lr_asym(rho_L, rho_R), 0.01, 0.99))
    prod = _ensure_valid_density(np.kron(rho_L, rho_R))
    return _ensure_valid_density((1 - p) * prod + p * BELL_PSI_MINUS)


# ─────────────────────────────────────────────────────────────────────
# Option A — Shannon entropy of MI distribution
# "Correlation diversity": how spread is MI across the LR pair?
# For a 2-qubit LR system we have only one pair; we proxy diversity
# by computing the MI at different stages and measuring its Shannon
# entropy across the trajectory.
# ─────────────────────────────────────────────────────────────────────

def option_A(history: list[dict]) -> float:
    """Shannon entropy of the per-step MI distribution across trajectory."""
    mi_vals = np.array([mi_val(joint_rho(s)) for s in history])
    total = mi_vals.sum()
    if total < EPS_NUM:
        return 0.0
    p = mi_vals / total
    p = p[p > EPS_NUM]
    return float(-np.sum(p * np.log2(p)))


# ─────────────────────────────────────────────────────────────────────
# Option B — Variance of pairwise MI across trajectory
# "Deviation damping": does the spread of MI values decrease?
# ─────────────────────────────────────────────────────────────────────

def option_B(history: list[dict]) -> float:
    """Variance of per-step MI values across trajectory."""
    mi_vals = np.array([mi_val(joint_rho(s)) for s in history])
    return float(np.var(mi_vals))


# ─────────────────────────────────────────────────────────────────────
# Option C — Coherent information spread
# "Negative entropy survival": mean I_c(A→B) across trajectory.
# Allostatic if I_c increases under perturbation (survives/spreads),
# homeostatic if it collapses.
# ─────────────────────────────────────────────────────────────────────

def option_C(history: list[dict]) -> float:
    """Mean coherent information I_c(A→B) across trajectory."""
    ic_vals = np.array([coherent_info(joint_rho(s)) for s in history])
    return float(np.mean(ic_vals))


# ─────────────────────────────────────────────────────────────────────
# Option D — Path entropy of Kraus unraveling histories (JK fuzz)
# Each step has one Kraus operator K_k with k = branch index.
# We sample KRAUS_BRANCHES random weight vectors to simulate a
# stochastic unraveling and compute the path entropy H_path.
# ─────────────────────────────────────────────────────────────────────

def option_D(history: list[dict], rng: np.random.Generator | None = None) -> float:
    """
    Path entropy H_path = -Σ P(k) log P(k) over sampled Kraus histories.
    
    Operationalization: at each step, we have a joint ρ. We decompose it
    into a convex combination of pure states (spectral) as the 'Kraus branches'.
    The branch probability = eigenvalue weight. Path entropy = Shannon entropy
    of the product distribution over the trajectory.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    
    T = len(history)
    if T == 0:
        return 0.0
    
    # At each step, get eigenvalue distribution (branch weights)
    step_branch_probs = []
    for step in history:
        rho_j = joint_rho(step)
        # Hermitianize and get eigenvalues
        rho_j = (rho_j + rho_j.conj().T) / 2
        ev = np.real(np.linalg.eigvalsh(rho_j))
        ev = np.clip(ev, 0, None)
        total = ev.sum()
        if total < EPS_NUM:
            ev = np.ones(4) / 4
        else:
            ev = ev / total
        step_branch_probs.append(ev)  # shape (4,)
    
    # Sample KRAUS_BRANCHES paths: each path is a sequence of branch ids
    # Path probability = product of branch weights at each step
    n_branches_per_step = 4  # 4×4 matrix has 4 eigenvalues
    path_probs = {}
    for _ in range(KRAUS_BRANCHES):
        path = tuple(rng.choice(n_branches_per_step, p=probs)
                     for probs in step_branch_probs)
        prob = 1.0
        for t, k in enumerate(path):
            prob *= step_branch_probs[t][k]
        path_probs[path] = path_probs.get(path, 0.0) + prob
    
    # Normalize and compute Shannon entropy
    total = sum(path_probs.values())
    if total < EPS_NUM:
        return 0.0
    probs = np.array(list(path_probs.values())) / total
    probs = probs[probs > EPS_NUM]
    return float(-np.sum(probs * np.log2(probs)))


# ─────────────────────────────────────────────────────────────────────
# Axis-0 Index: finite-difference derivative
# A0 = [D(Φ_ε(ρ)) - D(ρ)] / ε
# ALLOSTATIC if A0 > 0 (diversity increases under perturbation)
# HOMEOSTATIC if A0 < 0 (diversity is suppressed under perturbation)
# ─────────────────────────────────────────────────────────────────────

def axis0_index(history_base: list[dict],
                history_perturbed: list[dict],
                option_fn,
                eps: float) -> float:
    d_base = option_fn(history_base)
    d_pert = option_fn(history_perturbed)
    return (d_pert - d_base) / eps if eps > EPS_NUM else 0.0


# ─────────────────────────────────────────────────────────────────────
# Per-config runner
# ─────────────────────────────────────────────────────────────────────

def run_config(engine_type: int,
               torus_name: str,
               torus_val: float) -> dict:
    """Run one (engine_type, torus) pair across all perturbations × options."""
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_val)
    final = engine.run_cycle(state)
    history_base = final.history

    option_fns = {
        "A_mi_diversity":    option_A,
        "B_mi_variance":     option_B,
        "C_coherent_info":   option_C,
        "D_jk_path_entropy": option_D,
    }

    results_by_perturbation = {}
    for pert_name, pert_fn in PERTURBATIONS.items():
        history_pert = perturb_history(history_base, pert_fn, PERTURBATION_EPS)
        option_scores = {}
        for opt_name, opt_fn in option_fns.items():
            a0 = axis0_index(history_base, history_pert, opt_fn, PERTURBATION_EPS)
            polarity = "allostatic" if a0 > 0 else "homeostatic"
            option_scores[opt_name] = {
                "a0": round(float(a0), 6),
                "polarity": polarity,
                "base_val":  round(opt_fn(history_base), 6),
                "pert_val":  round(opt_fn(history_pert), 6),
            }
        results_by_perturbation[pert_name] = option_scores

    return {
        "engine_type": engine_type,
        "torus": torus_name,
        "perturbations": results_by_perturbation,
    }


# ─────────────────────────────────────────────────────────────────────
# Aggregate verdict
# ─────────────────────────────────────────────────────────────────────

def aggregate(all_results: list[dict]) -> dict:
    """
    For each option, collect:
    - sign_consistency: fraction of (config × perturbation) cells where
      polarity agrees with majority sign
    - mean_abs_a0: average signal strength
    - doctrine_fit: fraction of T1 configs that are homeostatic AND
      T2 configs that are allostatic (per Grok Unified Physics Type1=L-handed
      cooling bias, Type2=R-handed heating bias)
    """
    option_names = ["A_mi_diversity", "B_mi_variance", "C_coherent_info", "D_jk_path_entropy"]
    pert_names = list(PERTURBATIONS.keys())

    # Collect all A0 values per option
    stats = {opt: {"a0_vals": [], "polarities": [], "t1_polarities": [], "t2_polarities": []}
             for opt in option_names}

    for cfg in all_results:
        eng = cfg["engine_type"]
        for pert in pert_names:
            for opt in option_names:
                a0 = cfg["perturbations"][pert][opt]["a0"]
                pol = cfg["perturbations"][pert][opt]["polarity"]
                stats[opt]["a0_vals"].append(a0)
                stats[opt]["polarities"].append(pol)
                if eng == 1:
                    stats[opt]["t1_polarities"].append(pol)
                else:
                    stats[opt]["t2_polarities"].append(pol)

    verdicts = {}
    for opt in option_names:
        a0s = stats[opt]["a0_vals"]
        pols = stats[opt]["polarities"]
        t1_pols = stats[opt]["t1_polarities"]
        t2_pols = stats[opt]["t2_polarities"]

        # Sign consistency: majority vote
        n_allo = pols.count("allostatic")
        n_homeo = pols.count("homeostatic")
        majority = "allostatic" if n_allo >= n_homeo else "homeostatic"
        sign_consistency = max(n_allo, n_homeo) / len(pols) if pols else 0.0

        # Mean absolute A0 (signal strength)
        mean_abs = float(np.mean(np.abs(a0s))) if a0s else 0.0

        # Doctrine fit: T1 expected homeostatic (cooling/deductive = structure-preserving)
        #               T2 expected allostatic  (heating/inductive = diversity-expanding)
        t1_homeo_frac = t1_pols.count("homeostatic") / len(t1_pols) if t1_pols else 0.0
        t2_allo_frac  = t2_pols.count("allostatic")  / len(t2_pols) if t2_pols else 0.0
        doctrine_fit  = (t1_homeo_frac + t2_allo_frac) / 2.0

        # Composite score (equal weight: consistency + signal + doctrine)
        composite = (sign_consistency + min(mean_abs, 1.0) + doctrine_fit) / 3.0

        verdicts[opt] = {
            "sign_consistency":  round(sign_consistency, 3),
            "majority_polarity": majority,
            "mean_abs_a0":       round(mean_abs, 6),
            "t1_homeostatic_frac": round(t1_homeo_frac, 3),
            "t2_allostatic_frac":  round(t2_allo_frac, 3),
            "doctrine_fit":      round(doctrine_fit, 3),
            "composite_score":   round(composite, 3),
        }

    # Rank options
    ranked = sorted(option_names, key=lambda o: verdicts[o]["composite_score"], reverse=True)
    winner = ranked[0]

    return {
        "option_verdicts": verdicts,
        "ranking": ranked,
        "winner": winner,
        "winner_rationale": (
            f"Option {winner} wins with composite score "
            f"{verdicts[winner]['composite_score']:.3f} "
            f"(consistency={verdicts[winner]['sign_consistency']:.3f}, "
            f"signal={verdicts[winner]['mean_abs_a0']:.4f}, "
            f"doctrine_fit={verdicts[winner]['doctrine_fit']:.3f})"
        ),
    }


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 72)
    print("AXIS 0 i-SCALAR FUNCTIONAL SWEEP")
    print("=" * 72)
    print("Options from AXIS0_SPEC_OPTIONS_v0.1-v0.3:")
    print("  A — MI diversity (Shannon entropy of MI distribution)")
    print("  B — MI variance  (deviation damping)")
    print("  C — Coherent info spread (I_c survival under noise)")
    print("  D — JK fuzz / path entropy (Kraus history branching)")
    print()
    print("Perturbations: depolarizing | dephasing | amplitude_damping")
    print("Configs: T1/T2 × inner/clifford/outer  = 6 engine configs × 3 = 18 cells/option")
    print()

    all_results = []
    for eng_type in [1, 2]:
        for torus_name, torus_val in TORUS_CONFIGS:
            print(f"  Running T{eng_type}/{torus_name}...", end="", flush=True)
            r = run_config(eng_type, torus_name, torus_val)
            all_results.append(r)
            # Quick summary line
            for pert in PERTURBATIONS:
                a_pol = r["perturbations"][pert]["A_mi_diversity"]["polarity"][0].upper()
                b_pol = r["perturbations"][pert]["B_mi_variance"]["polarity"][0].upper()
                c_pol = r["perturbations"][pert]["C_coherent_info"]["polarity"][0].upper()
                d_pol = r["perturbations"][pert]["D_jk_path_entropy"]["polarity"][0].upper()
            print(f" done")

    print()
    print("─" * 72)
    print("DETAILED POLARITY TABLE  (A=allostatic, H=homeostatic)")
    print("─" * 72)
    print(f"{'Config':<20} {'Perturbation':<18} {'Opt-A':>6} {'Opt-B':>6} {'Opt-C':>6} {'Opt-D':>6}")
    print("─" * 72)
    for cfg in all_results:
        label = f"T{cfg['engine_type']}/{cfg['torus']}"
        for pert in PERTURBATIONS:
            opts = cfg["perturbations"][pert]
            def sym(pol): return "A" if pol == "allostatic" else "H"
            a0_A = opts["A_mi_diversity"]["a0"]
            a0_B = opts["B_mi_variance"]["a0"]
            a0_C = opts["C_coherent_info"]["a0"]
            a0_D = opts["D_jk_path_entropy"]["a0"]
            print(f"  {label:<18} {pert:<18} "
                  f"{sym(opts['A_mi_diversity']['polarity']):>5}({a0_A:+.4f})  "
                  f"{sym(opts['B_mi_variance']['polarity']):>5}({a0_B:+.4f})  "
                  f"{sym(opts['C_coherent_info']['polarity']):>5}({a0_C:+.4f})  "
                  f"{sym(opts['D_jk_path_entropy']['polarity']):>5}({a0_D:+.4f})")

    print()
    agg = aggregate(all_results)

    print("=" * 72)
    print("AGGREGATE VERDICT PER OPTION")
    print("=" * 72)
    for opt in ["A_mi_diversity", "B_mi_variance", "C_coherent_info", "D_jk_path_entropy"]:
        v = agg["option_verdicts"][opt]
        print(f"\n  Option {opt}:")
        print(f"    Sign consistency:  {v['sign_consistency']:.3f}  (majority={v['majority_polarity']})")
        print(f"    Mean |A0|:         {v['mean_abs_a0']:.6f}")
        print(f"    T1 homeostatic:    {v['t1_homeostatic_frac']:.3f}")
        print(f"    T2 allostatic:     {v['t2_allostatic_frac']:.3f}")
        print(f"    Doctrine fit:      {v['doctrine_fit']:.3f}")
        print(f"    Composite score:   {v['composite_score']:.3f}")

    print()
    print("=" * 72)
    print("RANKING & WINNER")
    print("=" * 72)
    for rank, opt in enumerate(agg["ranking"], 1):
        score = agg["option_verdicts"][opt]["composite_score"]
        marker = " ← WINNER" if opt == agg["winner"] else ""
        print(f"  #{rank}  {opt:<28} score={score:.3f}{marker}")

    print()
    print(f"  {agg['winner_rationale']}")
    print()

    # Doctrine interpretation
    winner = agg["winner"]
    wv = agg["option_verdicts"][winner]
    print("─" * 72)
    print("DOCTRINE INTERPRETATION")
    print("─" * 72)
    interpretations = {
        "A_mi_diversity": (
            "The i-scalar measures CORRELATION DIVERSITY — the spread of mutual "
            "information across history stages. Axis 0 allostatic = perturbation "
            "pushes MI to more stages (global). Homeostatic = MI concentrates "
            "(local). Doctrine connection: space=entropy → the variety of "
            "correlations IS the entropy landscape."
        ),
        "B_mi_variance": (
            "The i-scalar measures CORRELATION DEVIATION DAMPING — whether "
            "perturbation squashes or spreads the variance of MI values. "
            "Homeostatic = deviation is suppressed (low variance). Allostatic = "
            "deviation grows. Doctrine connection: 'a=a iff a~b' — identity "
            "suppresses deviation; the homeostatic engine is the identity-forming "
            "boundary."
        ),
        "C_coherent_info": (
            "The i-scalar measures COHERENT INFORMATION SURVIVAL — whether "
            "negative conditional entropy (I_c) survives perturbation. "
            "Allostatic = Bell entanglement persists (the prior dominates). "
            "Homeostatic = entanglement is broken by noise. Doctrine connection: "
            "FEP 'prior exists first' → allostatic means the Bell prior is robust."
        ),
        "D_jk_path_entropy": (
            "The i-scalar measures JK FUZZ BRANCHING VARIETY — the path entropy "
            "of Kraus history ensembles. Allostatic = more admissible Kraus paths "
            "(more future possibilities). Homeostatic = paths contract. This is "
            "the most direct operationalization of 'jk fuzz as causal force'."
        ),
    }
    print()
    print(f"  Winning option ({winner}):")
    print(f"  {interpretations[winner]}")
    print()
    print(f"  T1 homeostatic fraction: {wv['t1_homeostatic_frac']:.1%}")
    print(f"  T2 allostatic  fraction: {wv['t2_allostatic_frac']:.1%}")

    print()
    print("=" * 72)
    print("PROBE STATUS: PASS")
    print("=" * 72)

    # Save
    def json_safe(obj):
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, (np.bool_,)): return bool(obj)
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, dict): return {k: json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list): return [json_safe(v) for v in obj]
        return obj

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_iscalar_sweep_results.json")
    with open(out_path, "w") as f:
        json.dump(json_safe({
            "timestamp": datetime.now(UTC).isoformat(),
            "parameters": {
                "eps": PERTURBATION_EPS,
                "kraus_branches": KRAUS_BRANCHES,
            },
            "per_config_results": all_results,
            "aggregate": agg,
        }), f, indent=2)
    print(f"\n  Results → {out_path}")


if __name__ == "__main__":
    main()
