#!/usr/bin/env python3
"""
Entropy & Correlation Measure Sweep — Constraint Layers L7–L12
===============================================================
Dynamics layers: ordering, polarity, strength, dual-stack, transport, entanglement.

For every entropy form and correlation measure, tests discrimination power
at each of the 6 dynamics layers, then ranks cross-layer survival.

Output: a2_state/sim_results/entropy_type_sweep_L7_L12_results.json
"""

import json
import os
import sys
import traceback
from datetime import datetime, timezone

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: entropy and correlation survival across L7-L12 is explored here by numeric dynamics-layer sweeps, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "entropy-family sweeps, correlation measures, and dynamics-layer numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, StageControls, EngineState,
    TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER,
    LOOP_STAGE_ORDER,
)
from geometric_operators import (
    partial_trace_A, partial_trace_B, _ensure_valid_density,
    I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
)
from hopf_manifold import TORUS_INNER as HM_INNER, TORUS_OUTER as HM_OUTER


# ═══════════════════════════════════════════════════════════════════
# ENTROPY MEASURES (2×2)
# ═══════════════════════════════════════════════════════════════════

def _safe_evals(rho: np.ndarray) -> np.ndarray:
    """Get positive eigenvalues of a density matrix."""
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    return evals[evals > 1e-15]


def von_neumann(rho: np.ndarray) -> float:
    evals = _safe_evals(rho)
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def shannon(rho: np.ndarray) -> float:
    """Shannon entropy of the diagonal (measurement in computational basis)."""
    diag = np.real(np.diag(rho))
    diag = diag[diag > 1e-15]
    if len(diag) == 0:
        return 0.0
    return float(-np.sum(diag * np.log2(diag)))


def renyi(rho: np.ndarray, alpha: float) -> float:
    """Renyi entropy S_alpha = (1/(1-alpha)) log2(Tr(rho^alpha))."""
    evals = _safe_evals(rho)
    if len(evals) == 0:
        return 0.0
    if abs(alpha - 1.0) < 1e-10:
        return von_neumann(rho)
    tr_rho_alpha = float(np.sum(evals ** alpha))
    if tr_rho_alpha <= 0:
        return 0.0
    return float((1.0 / (1.0 - alpha)) * np.log2(tr_rho_alpha))


def min_entropy(rho: np.ndarray) -> float:
    """Min-entropy = -log2(lambda_max)."""
    evals = _safe_evals(rho)
    if len(evals) == 0:
        return 0.0
    return float(-np.log2(np.max(evals)))


def max_entropy(rho: np.ndarray) -> float:
    """Max-entropy = log2(rank(rho))."""
    evals = _safe_evals(rho)
    if len(evals) == 0:
        return 0.0
    return float(np.log2(len(evals)))


def linear_entropy(rho: np.ndarray) -> float:
    """Linear entropy S_L = 1 - Tr(rho^2). Ranges [0, 1-1/d]."""
    return float(1.0 - np.real(np.trace(rho @ rho)))


def tsallis(rho: np.ndarray, q: float) -> float:
    """Tsallis entropy S_q = (1 - Tr(rho^q)) / (q - 1)."""
    evals = _safe_evals(rho)
    if len(evals) == 0:
        return 0.0
    if abs(q - 1.0) < 1e-10:
        return float(-np.sum(evals * np.log(evals)))
    tr_rho_q = float(np.sum(evals ** q))
    return float((1.0 - tr_rho_q) / (q - 1.0))


def purity(rho: np.ndarray) -> float:
    """Purity Tr(rho^2)."""
    return float(np.real(np.trace(rho @ rho)))


# ═══════════════════════════════════════════════════════════════════
# CORRELATION MEASURES (4×4)
# ═══════════════════════════════════════════════════════════════════

def _vn_4x4(rho: np.ndarray) -> float:
    """Von Neumann entropy for arbitrary-size density matrix."""
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def conditional_entropy(rho_AB: np.ndarray) -> float:
    """S(A|B) = S(AB) - S(B)."""
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    return _vn_4x4(rho_AB) - von_neumann(rho_B)


def mutual_information(rho_AB: np.ndarray) -> float:
    """I(A:B) = S(A) + S(B) - S(AB)."""
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    return von_neumann(rho_A) + von_neumann(rho_B) - _vn_4x4(rho_AB)


def coherent_information(rho_AB: np.ndarray) -> float:
    """I_c(A>B) = S(B) - S(AB)."""
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    return von_neumann(rho_B) - _vn_4x4(rho_AB)


def concurrence(rho_AB: np.ndarray) -> float:
    """Wootters concurrence for a 4x4 density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho_AB.conj() @ sy_sy
    product = rho_AB @ rho_tilde
    evals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvalsh(product), 0))))[::-1]
    return float(max(0.0, evals[0] - evals[1] - evals[2] - evals[3]))


def negativity(rho_AB: np.ndarray) -> float:
    """Negativity N(rho) = (||rho^{T_B}||_1 - 1) / 2."""
    # Partial transpose over B
    rho_pt = rho_AB.copy().reshape(2, 2, 2, 2)
    rho_pt = rho_pt.transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh((rho_pt + rho_pt.conj().T) / 2)
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def log_negativity(rho_AB: np.ndarray) -> float:
    """Log-negativity E_N = log2(2*N + 1)."""
    neg = negativity(rho_AB)
    return float(np.log2(2.0 * neg + 1.0))


def entanglement_of_formation(rho_AB: np.ndarray) -> float:
    """EoF from concurrence: E = h((1+sqrt(1-C^2))/2) where h is binary entropy."""
    C = concurrence(rho_AB)
    if C < 1e-15:
        return 0.0
    x = (1.0 + np.sqrt(max(0.0, 1.0 - C * C))) / 2.0
    if x < 1e-15 or x > 1.0 - 1e-15:
        return 0.0
    return float(-x * np.log2(x) - (1.0 - x) * np.log2(1.0 - x))


def relative_entropy_to_identity(rho_AB: np.ndarray) -> float:
    """D(rho || I/d) = log2(d) - S(rho)."""
    d = rho_AB.shape[0]
    return float(np.log2(d) - _vn_4x4(rho_AB))


# ═══════════════════════════════════════════════════════════════════
# MEASURE REGISTRY
# ═══════════════════════════════════════════════════════════════════

def compute_all_measures(rho_AB: np.ndarray) -> dict:
    """Compute all entropy & correlation measures from a 4x4 joint state."""
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))

    measures = {}
    # 2x2 entropy measures on marginal A
    measures["von_neumann_A"] = von_neumann(rho_A)
    measures["shannon_A"] = shannon(rho_A)
    measures["renyi_0.5_A"] = renyi(rho_A, 0.5)
    measures["renyi_2_A"] = renyi(rho_A, 2.0)
    measures["renyi_5_A"] = renyi(rho_A, 5.0)
    measures["min_entropy_A"] = min_entropy(rho_A)
    measures["max_entropy_A"] = max_entropy(rho_A)
    measures["linear_entropy_A"] = linear_entropy(rho_A)
    measures["tsallis_0.5_A"] = tsallis(rho_A, 0.5)
    measures["tsallis_2_A"] = tsallis(rho_A, 2.0)
    measures["purity_A"] = purity(rho_A)

    # 4x4 correlation measures
    measures["conditional_entropy"] = conditional_entropy(rho_AB)
    measures["mutual_information"] = mutual_information(rho_AB)
    measures["coherent_information"] = coherent_information(rho_AB)
    measures["concurrence"] = concurrence(rho_AB)
    measures["negativity"] = negativity(rho_AB)
    measures["log_negativity"] = log_negativity(rho_AB)
    measures["entanglement_of_formation"] = entanglement_of_formation(rho_AB)
    measures["relative_entropy_D"] = relative_entropy_to_identity(rho_AB)

    return measures


MEASURE_NAMES = list(compute_all_measures(np.eye(4, dtype=complex) / 4.0).keys())


# ═══════════════════════════════════════════════════════════════════
# ENGINE HELPERS
# ═══════════════════════════════════════════════════════════════════

def run_cycles(engine: GeometricEngine, state: EngineState, n_cycles: int,
               controls_override: dict = None) -> EngineState:
    """Run n full 8-stage cycles."""
    for _ in range(n_cycles):
        if controls_override:
            state = engine.run_cycle(state, controls=controls_override)
        else:
            state = engine.run_cycle(state)
    return state


def default_controls(piston: float = 0.5, all_up: bool = None,
                     torus: float = TORUS_CLIFFORD) -> dict:
    """Generate 8-stage controls with optional uniform polarity."""
    ctrls = {}
    for i in range(8):
        lever = (i % 2 == 0) if all_up is None else all_up
        ctrls[i] = StageControls(piston=piston, lever=lever, torus=torus, spinor="both")
    return ctrls


def measures_after_run(engine: GeometricEngine, n_cycles: int = 5,
                       controls: dict = None, seed: int = 42) -> dict:
    """Init engine, run n_cycles, return all measures on final rho_AB."""
    state = engine.init_state(rng=np.random.default_rng(seed))
    state = run_cycles(engine, state, n_cycles, controls_override=controls)
    return compute_all_measures(state.rho_AB)


def discrimination(m_a: dict, m_b: dict) -> dict:
    """Per-measure discrimination: |a - b| / max(|a|, |b|, 1e-10)."""
    disc = {}
    for k in MEASURE_NAMES:
        a = m_a.get(k, 0.0)
        b = m_b.get(k, 0.0)
        denom = max(abs(a), abs(b), 1e-10)
        disc[k] = abs(a - b) / denom
    return disc


def rank_measures(disc: dict) -> list:
    """Return measures ranked by discrimination (descending)."""
    return sorted(disc.items(), key=lambda x: x[1], reverse=True)


# ═══════════════════════════════════════════════════════════════════
# L7: ORDERING — which measures detect order sensitivity?
# ═══════════════════════════════════════════════════════════════════

def sweep_L7_ordering() -> dict:
    """Run canonical vs reversed operator ordering."""
    print("  L7: Ordering sweep...")
    engine = GeometricEngine(engine_type=1)

    # Canonical order: default run_cycle uses LOOP_STAGE_ORDER
    m_canonical = measures_after_run(engine, n_cycles=5)

    # Reversed: manually reverse the stage order
    state = engine.init_state(rng=np.random.default_rng(42))
    reversed_order = list(reversed(LOOP_STAGE_ORDER[1]))
    for _ in range(5):
        for terrain_idx in reversed_order:
            ctrl = StageControls()
            state = engine.step(state, stage_idx=terrain_idx, controls=ctrl)
    m_reversed = compute_all_measures(state.rho_AB)

    disc = discrimination(m_canonical, m_reversed)
    ranked = rank_measures(disc)

    return {
        "canonical_measures": m_canonical,
        "reversed_measures": m_reversed,
        "discrimination": disc,
        "ranking": [[name, float(val)] for name, val in ranked],
    }


# ═══════════════════════════════════════════════════════════════════
# L8: POLARITY — which measures detect polarity?
# ═══════════════════════════════════════════════════════════════════

def sweep_L8_polarity() -> dict:
    """All-up vs all-down vs canonical mixed polarity."""
    print("  L8: Polarity sweep...")
    engine = GeometricEngine(engine_type=1)

    m_up = measures_after_run(engine, n_cycles=5, controls=default_controls(all_up=True))
    m_down = measures_after_run(engine, n_cycles=5, controls=default_controls(all_up=False))
    m_mixed = measures_after_run(engine, n_cycles=5)  # canonical alternating

    disc_up_down = discrimination(m_up, m_down)
    disc_mixed_up = discrimination(m_mixed, m_up)

    ranked_up_down = rank_measures(disc_up_down)
    ranked_mixed_up = rank_measures(disc_mixed_up)

    return {
        "all_up_measures": m_up,
        "all_down_measures": m_down,
        "mixed_measures": m_mixed,
        "disc_up_vs_down": disc_up_down,
        "disc_mixed_vs_up": disc_mixed_up,
        "ranking_up_vs_down": [[n, float(v)] for n, v in ranked_up_down],
        "ranking_mixed_vs_up": [[n, float(v)] for n, v in ranked_mixed_up],
    }


# ═══════════════════════════════════════════════════════════════════
# L9: STRENGTH — which measures show Goldilocks?
# ═══════════════════════════════════════════════════════════════════

def sweep_L9_strength() -> dict:
    """Run at multiple piston strengths, test for peak at intermediate values."""
    print("  L9: Strength sweep...")
    engine = GeometricEngine(engine_type=1)
    strengths = [0.0, 0.25, 0.5, 0.75, 1.0]

    all_measures = {}
    for s in strengths:
        ctrls = default_controls(piston=s)
        m = measures_after_run(engine, n_cycles=5, controls=ctrls)
        all_measures[str(s)] = m

    # For each measure: check if there's a peak at intermediate strength
    goldilocks = {}
    monotonic = {}
    for name in MEASURE_NAMES:
        vals = [all_measures[str(s)][name] for s in strengths]
        # Peak at intermediate: max is NOT at index 0 or 4
        max_idx = int(np.argmax(np.abs(vals)))
        if 0 < max_idx < len(strengths) - 1:
            goldilocks[name] = {
                "peak_strength": strengths[max_idx],
                "peak_value": float(vals[max_idx]),
                "values": [float(v) for v in vals],
            }
        else:
            monotonic[name] = {
                "max_at": strengths[max_idx],
                "values": [float(v) for v in vals],
            }

    return {
        "strengths": strengths,
        "per_strength_measures": all_measures,
        "goldilocks_measures": goldilocks,
        "monotonic_measures": monotonic,
        "n_goldilocks": len(goldilocks),
        "n_monotonic": len(monotonic),
    }


# ═══════════════════════════════════════════════════════════════════
# L10: DUAL-STACK — which measures detect interleaving?
# ═══════════════════════════════════════════════════════════════════

def sweep_L10_dual_stack() -> dict:
    """Pure T1, pure T2, alternating T1/T2."""
    print("  L10: Dual-stack sweep...")
    engine1 = GeometricEngine(engine_type=1)
    engine2 = GeometricEngine(engine_type=2)

    # Pure T1: 10 cycles of engine type 1
    m_t1 = measures_after_run(engine1, n_cycles=10)

    # Pure T2: 10 cycles of engine type 2
    m_t2 = measures_after_run(engine2, n_cycles=10)

    # Alternating T1/T2: 5 cycles each, interleaved
    state1 = engine1.init_state(rng=np.random.default_rng(42))
    for cycle in range(10):
        if cycle % 2 == 0:
            state1 = engine1.run_cycle(state1)
        else:
            # Use engine2 on the same state — type mismatch is intentional
            # We manually run engine2's stage order on the state
            for terrain_idx in LOOP_STAGE_ORDER[2]:
                ctrl = StageControls()
                state1 = engine2.step(state1, stage_idx=terrain_idx, controls=ctrl)
    m_alt = compute_all_measures(state1.rho_AB)

    disc_t1_t2 = discrimination(m_t1, m_t2)
    disc_t1_alt = discrimination(m_t1, m_alt)
    disc_t2_alt = discrimination(m_t2, m_alt)

    # Best discriminator = max across the three comparisons
    combined_disc = {}
    for name in MEASURE_NAMES:
        combined_disc[name] = max(
            disc_t1_t2[name], disc_t1_alt[name], disc_t2_alt[name]
        )

    ranked = rank_measures(combined_disc)

    return {
        "pure_t1_measures": m_t1,
        "pure_t2_measures": m_t2,
        "alternating_measures": m_alt,
        "disc_t1_vs_t2": disc_t1_t2,
        "disc_t1_vs_alt": disc_t1_alt,
        "disc_t2_vs_alt": disc_t2_alt,
        "combined_discrimination": combined_disc,
        "ranking": [[n, float(v)] for n, v in ranked],
    }


# ═══════════════════════════════════════════════════════════════════
# L11: TORUS TRANSPORT — which measures detect eta?
# ═══════════════════════════════════════════════════════════════════

def sweep_L11_torus_transport() -> dict:
    """Run at TORUS_INNER, CLIFFORD, OUTER."""
    print("  L11: Torus transport sweep...")
    engine = GeometricEngine(engine_type=1)

    eta_labels = ["inner", "clifford", "outer"]
    eta_values = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]

    all_measures = {}
    for label, eta in zip(eta_labels, eta_values):
        ctrls = default_controls(torus=eta)
        m = measures_after_run(engine, n_cycles=5, controls=ctrls)
        all_measures[label] = m

    # Spread per measure = max - min across eta values
    spread = {}
    for name in MEASURE_NAMES:
        vals = [all_measures[label][name] for label in eta_labels]
        denom = max(max(abs(v) for v in vals), 1e-10)
        spread[name] = (max(vals) - min(vals)) / denom

    ranked = rank_measures(spread)

    return {
        "eta_measures": all_measures,
        "spread": spread,
        "ranking": [[n, float(v)] for n, v in ranked],
    }


# ═══════════════════════════════════════════════════════════════════
# L12: ENTANGLEMENT — which measures detect Fi removal?
# ═══════════════════════════════════════════════════════════════════

def sweep_L12_entanglement() -> dict:
    """Run with full operators vs without Fi."""
    print("  L12: Entanglement (Fi removal) sweep...")
    engine = GeometricEngine(engine_type=1)

    # Full operators
    m_full = measures_after_run(engine, n_cycles=5)

    # Without Fi: override OPERATOR_MAP_4X4 temporarily
    from geometric_operators import OPERATOR_MAP_4X4
    original_fi = OPERATOR_MAP_4X4["Fi"]
    # Replace Fi with identity channel
    OPERATOR_MAP_4X4["Fi"] = lambda rho_AB, **kwargs: rho_AB.copy()

    m_no_fi = measures_after_run(engine, n_cycles=5)

    # Restore
    OPERATOR_MAP_4X4["Fi"] = original_fi

    disc = discrimination(m_full, m_no_fi)
    ranked = rank_measures(disc)

    return {
        "full_measures": m_full,
        "no_fi_measures": m_no_fi,
        "discrimination": disc,
        "ranking": [[n, float(v)] for n, v in ranked],
    }


# ═══════════════════════════════════════════════════════════════════
# CROSS-LAYER SURVIVAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def cross_layer_analysis(layer_results: dict) -> dict:
    """Compute cross-layer survival for all measures."""
    print("  Cross-layer survival analysis...")

    # Extract discrimination per layer per measure
    layer_disc = {}

    # L7: ordering
    layer_disc["L7_ordering"] = layer_results["L7_ordering"]["discrimination"]

    # L8: polarity (use up_vs_down as primary)
    layer_disc["L8_polarity"] = layer_results["L8_polarity"]["disc_up_vs_down"]

    # L9: strength — discrimination = spread across strengths
    l9 = layer_results["L9_strength"]
    l9_disc = {}
    for name in MEASURE_NAMES:
        vals = [l9["per_strength_measures"][str(s)][name] for s in l9["strengths"]]
        denom = max(max(abs(v) for v in vals), 1e-10)
        l9_disc[name] = (max(vals) - min(vals)) / denom
    layer_disc["L9_strength"] = l9_disc

    # L10: dual-stack (combined)
    layer_disc["L10_dual_stack"] = layer_results["L10_dual_stack"]["combined_discrimination"]

    # L11: torus transport (spread)
    layer_disc["L11_transport"] = layer_results["L11_torus_transport"]["spread"]

    # L12: entanglement
    layer_disc["L12_entanglement"] = layer_results["L12_entanglement"]["discrimination"]

    layers = list(layer_disc.keys())

    # Total discrimination per measure
    total_disc = {}
    for name in MEASURE_NAMES:
        total_disc[name] = sum(layer_disc[layer].get(name, 0.0) for layer in layers)

    # Per-measure survival: killed if disc < 0.01 at a layer
    KILL_THRESHOLD = 0.01
    killed_at = {}
    survived_all = []
    for name in MEASURE_NAMES:
        kills = [layer for layer in layers if layer_disc[layer].get(name, 0.0) < KILL_THRESHOLD]
        if kills:
            killed_at[name] = kills
        else:
            survived_all.append(name)

    # Rank by total discrimination
    ranked_total = sorted(total_disc.items(), key=lambda x: x[1], reverse=True)

    # Per-layer breakdown
    per_layer_rankings = {}
    for layer in layers:
        per_layer_rankings[layer] = [
            [n, float(v)] for n, v in
            sorted(layer_disc[layer].items(), key=lambda x: x[1], reverse=True)
        ]

    return {
        "layers": layers,
        "layer_discrimination": {layer: {k: float(v) for k, v in d.items()} for layer, d in layer_disc.items()},
        "total_discrimination": {k: float(v) for k, v in total_disc.items()},
        "total_ranking": [[n, float(v)] for n, v in ranked_total],
        "survived_all_layers": survived_all,
        "killed_at_layer": killed_at,
        "per_layer_rankings": per_layer_rankings,
        "kill_threshold": KILL_THRESHOLD,
    }


# ═══════════════════════════════════════════════════════════════════
# JSON SANITIZER
# ═══════════════════════════════════════════════════════════════════

def sanitize_for_json(obj):
    """Recursively sanitize numpy types for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        v = float(obj)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    elif isinstance(obj, (np.complexfloating,)):
        return float(np.real(obj))
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Entropy & Correlation Measure Sweep — L7–L12 Dynamics Layers")
    print("=" * 70)

    results = {
        "meta": {
            "probe": "sim_entropy_type_sweep_L7_L12",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "measure_count": len(MEASURE_NAMES),
            "measure_names": MEASURE_NAMES,
        }
    }

    # Run all layer sweeps
    results["L7_ordering"] = sweep_L7_ordering()
    results["L8_polarity"] = sweep_L8_polarity()
    results["L9_strength"] = sweep_L9_strength()
    results["L10_dual_stack"] = sweep_L10_dual_stack()
    results["L11_torus_transport"] = sweep_L11_torus_transport()
    results["L12_entanglement"] = sweep_L12_entanglement()

    # Cross-layer survival
    results["cross_layer_survival"] = cross_layer_analysis(results)

    # Sanitize and write
    results = sanitize_for_json(results)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entropy_type_sweep_L7_L12_results.json")

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults written to: {out_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("CROSS-LAYER SURVIVAL SUMMARY")
    print("=" * 70)

    xls = results["cross_layer_survival"]

    print(f"\nMeasures that SURVIVED all 6 layers (disc >= {xls['kill_threshold']} everywhere):")
    for name in xls["survived_all_layers"]:
        total = xls["total_discrimination"][name]
        print(f"  {name:35s}  total_disc = {total:.4f}")

    print(f"\nMeasures KILLED at specific layers:")
    for name, layers in xls["killed_at_layer"].items():
        total = xls["total_discrimination"][name]
        print(f"  {name:35s}  killed at {layers}  (total = {total:.4f})")

    print(f"\nTOTAL DISCRIMINATION RANKING (top 10):")
    for name, val in xls["total_ranking"][:10]:
        print(f"  {name:35s}  {val:.4f}")

    print(f"\nPER-LAYER TOP-3 DISCRIMINATORS:")
    for layer, ranking in xls["per_layer_rankings"].items():
        top3 = ranking[:3]
        top3_str = ", ".join(f"{n}={v:.3f}" for n, v in top3)
        print(f"  {layer:20s}: {top3_str}")

    return results


if __name__ == "__main__":
    main()
