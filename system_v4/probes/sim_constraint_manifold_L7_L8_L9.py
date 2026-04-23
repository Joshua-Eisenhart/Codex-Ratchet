#!/usr/bin/env python3
"""
Constraint Manifold Explorer — Layers 7, 8, 9
==============================================
Explores the FULL allowed space of dynamics at each layer,
then shows what the next layer's constraint cuts.

Layer 7: All valid stage orderings (permutations of 8 terrain indices)
Layer 8: All 256 polarity assignments (2^8 binary patterns)
Layer 9: Full strength hypercube [0,1]^4 (625-point coarse grid)

Each layer's output is the LANDSCAPE before constraints narrow it.
"""

import sys, os, json, time, itertools
import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this explores the L7-L9 constraint manifold numerically before later constraints cut it down, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "ordering, polarity, and strength-landscape numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, StageControls,
    TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER, LOOP_GRAMMAR,
    TORUS_CLIFFORD,
)
from geometric_operators import (
    apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
    OPERATOR_MAP_4X4, partial_trace_A, partial_trace_B,
    _ensure_valid_density, SIGMA_Y,
)
from hopf_manifold import von_neumann_entropy_2x2

# ── Concurrence for 4x4 density matrices ──────────────────────────
def concurrence_4x4(rho):
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)), reverse=True)
    return max(0.0, evals[0] - evals[1] - evals[2] - evals[3])

# ── Entropy of reduced state ──────────────────────────────────────
def subsystem_entropy(rho_4x4):
    rho_A = partial_trace_B(rho_4x4)
    rho_A = _ensure_valid_density(rho_A)
    return von_neumann_entropy_2x2(rho_A)

# ── Sanitize numpy types for JSON ─────────────────────────────────
def sanitize(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    return obj

def distribution_stats(vals):
    arr = np.array(vals, dtype=float)
    return {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "median": float(np.median(arr)),
    }


# ══════════════════════════════════════════════════════════════════
# ENGINE RUNNER: run with a given ordering, polarity pattern, strengths
# ══════════════════════════════════════════════════════════════════

def run_engine_custom(engine_type, stage_order, polarity_pattern, strengths, n_cycles):
    """Run engine with custom ordering, polarity, and strengths.

    IMPORTANT: For L7 (ordering sweep) we use the engine.step() path which
    respects the engine's internal LUT polarity. For L8 (polarity sweep) we
    bypass engine.step() entirely and apply operators directly to rho_AB so
    that polarity_pattern actually takes effect.

    Args:
        engine_type: 1 or 2
        stage_order: list of 8 terrain indices (the ordering)
        polarity_pattern: list of 8 bools (polarity per stage position)
        strengths: dict mapping op_name -> strength float
        n_cycles: number of full 8-stage cycles

    Returns:
        dict with final concurrence, entropy, per-cycle data
    """
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state()

    conc_per_cycle = []
    ent_per_cycle = []

    for cycle in range(n_cycles):
        for pos, terrain_idx in enumerate(stage_order):
            terrain = TERRAINS[terrain_idx]
            op_name, _ = STAGE_OPERATOR_LUT[
                (engine_type, terrain["loop"], terrain["topo"])
            ]
            polarity_up = polarity_pattern[pos]
            ctrl = StageControls(
                piston=strengths.get(op_name, 0.5),
                lever=polarity_up,
            )
            state = engine.step(state, stage_idx=terrain_idx, controls=ctrl)

        c = concurrence_4x4(state.rho_AB)
        e = subsystem_entropy(state.rho_AB)
        conc_per_cycle.append(c)
        ent_per_cycle.append(e)

    return {
        "final_concurrence": float(conc_per_cycle[-1]) if conc_per_cycle else 0.0,
        "final_entropy": float(ent_per_cycle[-1]) if ent_per_cycle else 0.0,
        "mean_concurrence": float(np.mean(conc_per_cycle)) if conc_per_cycle else 0.0,
        "mean_entropy": float(np.mean(ent_per_cycle)) if ent_per_cycle else 0.0,
    }


def run_engine_with_lut_override(engine_type, stage_order, polarity_pattern, strengths, n_cycles):
    """Run engine through engine.step() but temporarily override STAGE_OPERATOR_LUT
    polarities so that our polarity_pattern actually takes effect.

    This preserves all the geometry transport, coarse-graining, and angular
    advancement that engine.step() provides, while letting us vary polarity.
    """
    import engine_core as ec

    # Build override map: for each position in stage_order, override the LUT polarity
    saved_lut = {}
    for pos, terrain_idx in enumerate(stage_order):
        terrain = TERRAINS[terrain_idx]
        key = (engine_type, terrain["loop"], terrain["topo"])
        if key not in saved_lut:
            saved_lut[key] = ec.STAGE_OPERATOR_LUT[key]
        op_name = saved_lut[key][0]
        ec.STAGE_OPERATOR_LUT[key] = (op_name, polarity_pattern[pos])

    try:
        engine = GeometricEngine(engine_type=engine_type)
        state = engine.init_state()

        conc_per_cycle = []
        ent_per_cycle = []

        for cycle in range(n_cycles):
            for pos, terrain_idx in enumerate(stage_order):
                terrain = TERRAINS[terrain_idx]
                op_name, _ = STAGE_OPERATOR_LUT[
                    (engine_type, terrain["loop"], terrain["topo"])
                ]
                ctrl = StageControls(piston=strengths.get(op_name, 0.5))
                state = engine.step(state, stage_idx=terrain_idx, controls=ctrl)

            c = concurrence_4x4(state.rho_AB)
            e = subsystem_entropy(state.rho_AB)
            conc_per_cycle.append(c)
            ent_per_cycle.append(e)

        return {
            "final_concurrence": float(conc_per_cycle[-1]) if conc_per_cycle else 0.0,
            "final_entropy": float(ent_per_cycle[-1]) if ent_per_cycle else 0.0,
            "mean_concurrence": float(np.mean(conc_per_cycle)) if conc_per_cycle else 0.0,
            "mean_entropy": float(np.mean(ent_per_cycle)) if ent_per_cycle else 0.0,
        }
    finally:
        # Restore original LUT
        for key, val in saved_lut.items():
            ec.STAGE_OPERATOR_LUT[key] = val


# ══════════════════════════════════════════════════════════════════
# LAYER 7: ALL VALID ORDERINGS
# ══════════════════════════════════════════════════════════════════

def get_canonical_polarity(engine_type, stage_order):
    """Extract the canonical polarity pattern for a given ordering."""
    pols = []
    for terrain_idx in stage_order:
        terrain = TERRAINS[terrain_idx]
        _, is_up = STAGE_OPERATOR_LUT[(engine_type, terrain["loop"], terrain["topo"])]
        pols.append(is_up)
    return pols


def enumerate_valid_orderings(engine_type):
    """Enumerate valid stage orderings for an engine type.

    Structure: each loop has 4 terrains. Fiber=[0,1,2,3], Base=[4,5,6,7].
    The engine runs outer loop first, then inner loop.
    Type-1: outer=base(4,5,6,7), inner=fiber(0,1,2,3)
    Type-2: outer=fiber(0,1,2,3), inner=base(4,5,6,7)

    Valid orderings = all permutations of each 4-terrain set,
    with outer always before inner (loop sequencing is structural).
    4! x 4! = 576 total orderings per engine type.

    But further constraints from the loop grammar:
    - Deductive: Se -> Ne -> Ni -> Si
    - Inductive: Se -> Si -> Ni -> Ne
    These are the TOPOLOGY traversal orders. But the question is
    whether OTHER permutations within each loop are valid.

    We enumerate ALL 576 and test them, but also flag which ones
    match the deductive/inductive grammar.
    """
    grammar = LOOP_GRAMMAR[engine_type]
    outer_indices = grammar["outer"].terrain_indices  # 4 indices
    inner_indices = grammar["inner"].terrain_indices  # 4 indices

    orderings = []
    for outer_perm in itertools.permutations(outer_indices):
        for inner_perm in itertools.permutations(inner_indices):
            orderings.append(list(outer_perm) + list(inner_perm))

    return orderings


def layer7_explore(engine_type=1, n_cycles=10):
    """Explore the full ordering space."""
    print(f"[L7] Enumerating all orderings for Type-{engine_type}...")
    all_orderings = enumerate_valid_orderings(engine_type)
    print(f"[L7] Total orderings: {len(all_orderings)}")

    canonical_order = LOOP_STAGE_ORDER[engine_type]
    default_strengths = {"Ti": 0.5, "Fe": 0.5, "Te": 0.5, "Fi": 0.5}

    results = []
    for i, ordering in enumerate(all_orderings):
        if i % 100 == 0:
            print(f"  [L7] Running ordering {i}/{len(all_orderings)}...")
        polarity = get_canonical_polarity(engine_type, ordering)
        r = run_engine_custom(engine_type, ordering, polarity, default_strengths, n_cycles)
        r["ordering"] = ordering
        r["is_canonical"] = (ordering == canonical_order)
        results.append(r)

    # Find canonical rank
    conc_vals = [r["final_concurrence"] for r in results]
    ent_vals = [r["final_entropy"] for r in results]

    # Sort by concurrence descending
    sorted_by_conc = sorted(results, key=lambda x: x["final_concurrence"], reverse=True)
    canonical_rank = None
    for rank, r in enumerate(sorted_by_conc):
        if r["is_canonical"]:
            canonical_rank = rank + 1
            break

    top5 = [{"ordering": r["ordering"], "concurrence": r["final_concurrence"],
             "entropy": r["final_entropy"]} for r in sorted_by_conc[:5]]
    bottom5 = [{"ordering": r["ordering"], "concurrence": r["final_concurrence"],
                "entropy": r["final_entropy"]} for r in sorted_by_conc[-5:]]

    # Check bimodality
    conc_arr = np.array(conc_vals)
    nonzero_frac = float(np.mean(conc_arr > 1e-6))

    return {
        "total_valid_orderings": len(all_orderings),
        "concurrence_distribution": distribution_stats(conc_vals),
        "entropy_distribution": distribution_stats(ent_vals),
        "canonical_order": canonical_order,
        "canonical_rank_by_concurrence": canonical_rank,
        "fraction_with_concurrence_gt_0": nonzero_frac,
        "top_5_orderings": top5,
        "bottom_5_orderings": bottom5,
    }


# ══════════════════════════════════════════════════════════════════
# LAYER 8: ALL 256 POLARITY ASSIGNMENTS
# ══════════════════════════════════════════════════════════════════

def layer8_explore(engine_type=1, n_cycles=5):
    """Sweep all 256 polarity patterns on the canonical ordering."""
    print(f"[L8] Sweeping all 256 polarity patterns for Type-{engine_type}...")
    canonical_order = LOOP_STAGE_ORDER[engine_type]
    canonical_polarity = get_canonical_polarity(engine_type, canonical_order)
    default_strengths = {"Ti": 0.5, "Fe": 0.5, "Te": 0.5, "Fi": 0.5}

    results = []
    for pattern_int in range(256):
        polarity = [(pattern_int >> bit) & 1 == 1 for bit in range(8)]
        r = run_engine_with_lut_override(engine_type, canonical_order, polarity, default_strengths, n_cycles)
        r["pattern"] = polarity
        r["pattern_int"] = pattern_int
        results.append(r)

    # Canonical pattern as int
    canonical_int = sum((1 << bit) if canonical_polarity[bit] else 0 for bit in range(8))

    conc_vals = [r["final_concurrence"] for r in results]
    ent_vals = [r["final_entropy"] for r in results]

    sorted_by_conc = sorted(results, key=lambda x: x["final_concurrence"], reverse=True)
    canonical_rank = None
    for rank, r in enumerate(sorted_by_conc):
        if r["pattern_int"] == canonical_int:
            canonical_rank = rank + 1
            break

    patterns_that_kill = sum(1 for c in conc_vals if c < 1e-6)
    nonzero_frac = float(np.mean(np.array(conc_vals) > 1e-6))

    # Equivalence classes: group by (rounded concurrence, rounded entropy)
    equiv_map = {}
    for r in results:
        key = (round(r["final_concurrence"], 4), round(r["final_entropy"], 4))
        equiv_map.setdefault(key, []).append(r["pattern_int"])
    n_equiv_classes = len(equiv_map)

    top5 = [{"pattern": r["pattern"], "pattern_int": r["pattern_int"],
             "concurrence": r["final_concurrence"], "entropy": r["final_entropy"]}
            for r in sorted_by_conc[:5]]

    return {
        "total_patterns": 256,
        "concurrence_distribution": distribution_stats(conc_vals),
        "entropy_distribution": distribution_stats(ent_vals),
        "fraction_with_concurrence_gt_0": nonzero_frac,
        "canonical_pattern": canonical_polarity,
        "canonical_pattern_int": canonical_int,
        "canonical_pattern_rank": canonical_rank,
        "patterns_that_kill": patterns_that_kill,
        "equivalence_classes": n_equiv_classes,
        "top_5_patterns": top5,
    }


# ══════════════════════════════════════════════════════════════════
# LAYER 9: FULL STRENGTH LANDSCAPE [0,1]^4
# ══════════════════════════════════════════════════════════════════

def layer9_explore(engine_type=1, n_cycles=5):
    """Sweep the 4D strength hypercube on a 5^4 = 625 grid."""
    print(f"[L9] Sweeping 625-point strength grid for Type-{engine_type}...")
    canonical_order = LOOP_STAGE_ORDER[engine_type]
    canonical_polarity = get_canonical_polarity(engine_type, canonical_order)
    strength_vals = [0.0, 0.25, 0.5, 0.75, 1.0]
    op_names = ["Ti", "Fe", "Te", "Fi"]

    results = []
    for i, combo in enumerate(itertools.product(strength_vals, repeat=4)):
        if i % 100 == 0:
            print(f"  [L9] Running strength point {i}/625...")
        s_dict = {op_names[j]: combo[j] for j in range(4)}
        r = run_engine_with_lut_override(engine_type, canonical_order, canonical_polarity, s_dict, n_cycles)
        r["strengths"] = list(combo)
        results.append(r)

    conc_vals = [r["final_concurrence"] for r in results]
    ent_vals = [r["final_entropy"] for r in results]
    nonzero_frac = float(np.mean(np.array(conc_vals) > 1e-6))

    # Optimal
    best = max(results, key=lambda x: x["final_concurrence"])
    optimal_vector = best["strengths"]

    # Engine default strengths
    default_strengths = [0.5, 0.5, 0.5, 0.5]
    default_result = None
    for r in results:
        if r["strengths"] == default_strengths:
            default_result = r
            break

    # Marginal curves: for each operator, average concurrence over all other dims
    marginals = {}
    for dim_idx, op_name in enumerate(op_names):
        curve_strengths = []
        curve_concs = []
        for s_val in strength_vals:
            matching = [r["final_concurrence"] for r in results if r["strengths"][dim_idx] == s_val]
            curve_strengths.append(s_val)
            curve_concs.append(float(np.mean(matching)))
        marginals[op_name] = {
            "strengths": curve_strengths,
            "mean_concurrence": curve_concs,
        }

    return {
        "grid_size": len(results),
        "concurrence_distribution": distribution_stats(conc_vals),
        "entropy_distribution": distribution_stats(ent_vals),
        "fraction_with_concurrence_gt_0": nonzero_frac,
        "optimal_strength_vector": optimal_vector,
        "optimal_concurrence": float(best["final_concurrence"]),
        "engine_default_strengths": default_strengths,
        "engine_default_concurrence": float(default_result["final_concurrence"]) if default_result else None,
        "marginal_curves": marginals,
    }


# ══════════════════════════════════════════════════════════════════
# Z3 VERIFICATION: enumeration count check
# ══════════════════════════════════════════════════════════════════

def z3_verify_ordering_count():
    """Use z3 to verify the count of valid orderings matches our enumeration.
    The structure: outer loop = perm(4), inner loop = perm(4), outer before inner.
    Total = 4! * 4! = 576. z3 confirms this is the full space.
    """
    try:
        from z3 import Solver, Int, Distinct, And, Or, sat
        s = Solver()
        # 8 positions, each assigned a terrain index 0-7
        pos = [Int(f"p{i}") for i in range(8)]

        # All distinct
        s.add(Distinct(pos))

        # Range constraints
        for p in pos:
            s.add(And(p >= 0, p <= 7))

        # Outer loop = first 4 positions get base terrains (4,5,6,7) for Type-1
        for i in range(4):
            s.add(Or(pos[i] == 4, pos[i] == 5, pos[i] == 6, pos[i] == 7))
        # Inner loop = last 4 positions get fiber terrains (0,1,2,3) for Type-1
        for i in range(4, 8):
            s.add(Or(pos[i] == 0, pos[i] == 1, pos[i] == 2, pos[i] == 3))

        count = 0
        while s.check() == sat:
            m = s.model()
            count += 1
            # Block this solution
            block = Or([pos[i] != m[pos[i]] for i in range(8)])
            s.add(block)

        return {"z3_count": count, "expected": 576, "match": count == 576}
    except ImportError:
        return {"z3_count": None, "expected": 576, "match": None, "note": "z3 not installed"}


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    engine_type = 1

    # Layer 7
    l7 = layer7_explore(engine_type=engine_type, n_cycles=10)
    print(f"[L7] Done. {l7['total_valid_orderings']} orderings explored.")
    print(f"  Canonical rank: {l7['canonical_rank_by_concurrence']}/{l7['total_valid_orderings']}")
    print(f"  Concurrence range: [{l7['concurrence_distribution']['min']:.4f}, {l7['concurrence_distribution']['max']:.4f}]")

    # Layer 8
    l8 = layer8_explore(engine_type=engine_type, n_cycles=5)
    print(f"[L8] Done. 256 polarity patterns explored.")
    print(f"  Canonical rank: {l8['canonical_pattern_rank']}/256")
    print(f"  Patterns that kill: {l8['patterns_that_kill']}")

    # Layer 9
    l9 = layer9_explore(engine_type=engine_type, n_cycles=5)
    print(f"[L9] Done. 625 strength points explored.")
    print(f"  Optimal vector: {l9['optimal_strength_vector']}")
    print(f"  Optimal concurrence: {l9['optimal_concurrence']:.4f}")
    print(f"  Default concurrence: {l9['engine_default_concurrence']:.4f}")

    # z3 verification
    print("[Z3] Verifying ordering count...")
    z3_result = z3_verify_ordering_count()
    print(f"  z3 count: {z3_result['z3_count']}, expected: {z3_result['expected']}, match: {z3_result['match']}")

    elapsed = time.time() - t0

    output = {
        "name": "constraint_manifold_L7_L8_L9",
        "engine_type": engine_type,
        "L7_ordering_space": l7,
        "L8_polarity_space": l8,
        "L9_strength_landscape": l9,
        "z3_verification": z3_result,
        "runtime_seconds": round(elapsed, 1),
        "timestamp": "2026-04-06",
    }

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results",
        "constraint_manifold_L7_L8_L9_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(sanitize(output), f, indent=2)
    print(f"\nResults written to {out_path}")
    print(f"Total runtime: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
