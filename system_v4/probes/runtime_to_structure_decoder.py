#!/usr/bin/env python3
"""
Runtime-to-Structure Decoder
=============================
Status: [Exploratory probe]

This script attempts to decode the live engine's per-microstep runtime
variables into candidate 6-line hexagram state vectors, aligned with
the 64-hexagram proposal scaffold.

It does NOT assume the mapping is correct. It reports:
  1. What lines can be read unambiguously from runtime state.
  2. What lines require interpretation choices (and which choices were made).
  3. How stable the readout is across seeds and engine types.

The 6 candidate lines (from the proposal scaffold) are:
  L1 = Ax6 (Action Precedence)    : ρA (yin/0) vs Aρ (yang/1)
  L2 = Ax5 (Curvature)            : Flat (yin/0) vs Hysteresis (yang/1)
  L3 = Ax3 (Chirality)            : Left-phase (yin/0) vs Right-phase (yang/1)
  L4 = Ax4 (Process Direction)    : CCW/Inductive (yin/0) vs CW/Deductive (yang/1)
  L5 = Ax1 (Channel Coupling)     : Closed/Unitary (yin/0) vs Open/Dissipative (yang/1)
  L6 = Ax2 (Boundary / Frame)     : Spread/Eulerian (yin/0) vs Concentrated/Lagrangian (yang/1)

For each microstep, we attempt to read these lines from the runtime
variables that are actually available, and flag which lines are
unambiguous vs which are interpretation-dependent.
"""

import numpy as np
import json, os, sys
from dataclasses import dataclass
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, StageControls, TERRAINS, OPERATORS,
    TORUS_CLIFFORD,
)
from geometric_operators import (
    negentropy, trace_distance_2x2,
    _ensure_valid_density,
)
from hopf_manifold import torus_radii, density_to_bloch


# ═══════════════════════════════════════════════════════════════════
# LINE DECODERS: one function per candidate structural hexagram line
# Each returns (line_value: int, confidence: str, rationale: str)
#   0 = yin (broken), 1 = yang (solid)
#   confidence is one of: "DIRECT", "INFERRED", "GUESS"
# ═══════════════════════════════════════════════════════════════════

def decode_ax1_channel(terrain: dict, state: EngineState) -> Tuple[int, str, str]:
    """Ax1: Channel coupling. Open vs Closed.

    This is DIRECTLY readable from the terrain definition.
    terrain["open"] is an explicit boolean in engine_core.py.
    """
    line = 1 if terrain["open"] else 0
    return line, "DIRECT", f"terrain['open']={terrain['open']}"


def decode_ax2_boundary(terrain: dict, state: EngineState) -> Tuple[int, str, str]:
    """Ax2: Boundary / Frame. Expansion vs Compression.

    This is DIRECTLY readable from the terrain definition.
    terrain["expansion"] is an explicit boolean in engine_core.py.
    """
    line = 0 if terrain["expansion"] else 1
    return line, "DIRECT", f"terrain['expansion']={terrain['expansion']} → concentrated={not terrain['expansion']}"


def decode_ax3_chirality(terrain: dict, state: EngineState) -> Tuple[int, str, str]:
    """Ax3: Chirality / Spinor Phase.

    The proposal maps Ax3 to Left/Right phase of the Weyl spinor pair.
    engine_type is a global property (Type 1 = Left dominant, Type 2 = Right).
    But Ax3 is supposed to vary per-hexagram, not be a global engine constant.

    Candidate interpretation: measure L/R asymmetry of the density matrices
    at each microstep. If trace_distance(rho_L, rho_R) > median → yang.
    This is INFERRED, not direct.
    """
    td = trace_distance_2x2(state.rho_L, state.rho_R)
    # Use a fixed threshold; we will report the distribution
    # Bloch vector dot product sign is another candidate
    b_L = density_to_bloch(state.rho_L)
    b_R = density_to_bloch(state.rho_R)
    cross_z = float(np.cross(b_L[:2], b_R[:2]))
    line = 1 if cross_z >= 0 else 0
    return line, "INFERRED", f"cross(bL,bR).z={cross_z:+.4f}, td={td:.4f}"


def decode_ax4_traversal(terrain: dict, state: EngineState) -> Tuple[int, str, str]:
    """Ax4: Process Direction. Fiber vs Base loop.

    The proposal maps Ax4 to CW/CCW or Inductive/Deductive.
    The closest runtime variable is terrain["loop"] which is "fiber" or "base".
    This is DIRECTLY readable from the terrain, but whether it maps to 
    the Ax4 concept of "process direction" is the unsettled part.
    """
    line = 1 if terrain["loop"] == "base" else 0
    return line, "DIRECT", f"terrain['loop']={terrain['loop']}"


def decode_ax5_curvature(terrain: dict, state: EngineState) -> Tuple[int, str, str]:
    """Ax5: Curvature / Torus Hysteresis.

    The proposal maps Ax5 to Flat vs Curved (FGA vs FSA).
    No single runtime variable cleanly maps to this.
    Candidate: use the torus latitude (eta) relative to Clifford.
    If eta is near TORUS_CLIFFORD (pi/4), curvature is minimal (flat).
    If eta deviates, curvature increases (hysteresis).
    This is INFERRED.
    """
    eta_deviation = abs(state.eta - TORUS_CLIFFORD)
    # Threshold: if deviation > 0.1 rad from Clifford, call it "curved"
    line = 1 if eta_deviation > 0.1 else 0
    return line, "INFERRED", f"eta={state.eta:.4f}, dev={eta_deviation:.4f}"


def decode_ax6_precedence(terrain: dict, state: EngineState, op_name: str) -> Tuple[int, str, str]:
    """Ax6: Action Precedence. ρA vs Aρ (pre vs post multiply).

    The engine applies operators in a fixed order: Ti → Fe → Te → Fi.
    The conceptual split is: Ti/Fi constrain BEFORE exploring (ρA),
    while Te/Fe explore BEFORE constraining (Aρ).
    This is an INFERRED structural interpretation of operator role.
    """
    if op_name in ("Te", "Fe"):
        line = 1  # yang / Aρ (generative / explore-first)
    else:
        line = 0  # yin / ρA (receptive / constrain-first)
    return line, "INFERRED", f"op={op_name} → {'Aρ(yang)' if line else 'ρA(yin)'}"


# ═══════════════════════════════════════════════════════════════════
# MAIN DECODER
# ═══════════════════════════════════════════════════════════════════

def decode_trajectory(engine_type: int = 1, seed: int = 42, n_cycles: int = 1) -> Dict:
    """Run one engine and decode every microstep into a candidate 6-line hexagram."""
    rng = np.random.default_rng(seed)
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(rng=rng)

    microsteps = []
    line_stats = {f"L{i+1}": {"direct": 0, "inferred": 0, "guess": 0, "yang": 0, "total": 0}
                  for i in range(6)}

    for cycle in range(n_cycles):
        for stage_idx in range(8):
            terrain = TERRAINS[stage_idx]
            for op_idx, op_name in enumerate(OPERATORS):
                # Step the engine one microstep manually by calling step
                # But step() applies all 4 operators at once.
                # We need to read state BETWEEN operator applications.
                # Since step() is monolithic, we decode at the macro-stage level
                # and split by operator conceptually.
                pass

    # Since engine_core.step() applies all 4 operators atomically,
    # we decode at the 4-operator-per-stage granularity.
    # Each macro-stage gives us 4 microstep readouts (one per operator).
    state = engine.init_state(rng=np.random.default_rng(seed))
    for cycle in range(n_cycles):
        for stage_idx in range(8):
            terrain = TERRAINS[stage_idx]
            state_before = state

            # Run the macro-stage
            state = engine.step(state, stage_idx=stage_idx)

            # The history now contains 4 new entries (one per operator)
            n_history = len(state.history)
            new_entries = state.history[n_history - 4: n_history]

            for op_idx, entry in enumerate(new_entries):
                op_name = entry["op_name"]
                rho_L_snap = entry["rho_L"]
                rho_R_snap = entry["rho_R"]

                # Build a snapshot state for the decoders
                snap = EngineState(
                    rho_L=rho_L_snap, rho_R=rho_R_snap,
                    eta=state.eta, theta1=state.theta1, theta2=state.theta2,
                    ga0_level=entry["ga0_after"],
                    stage_idx=stage_idx, engine_type=engine_type,
                )

                # Decode all 6 lines
                b1, c1, r1 = decode_ax1_channel(terrain, snap)
                b2, c2, r2 = decode_ax2_boundary(terrain, snap)
                b3, c3, r3 = decode_ax3_chirality(terrain, snap)
                b4, c4, r4 = decode_ax4_traversal(terrain, snap)
                b5, c5, r5 = decode_ax5_curvature(terrain, snap)
                b6, c6, r6 = decode_ax6_precedence(terrain, snap, op_name)

                lines = [b6, b5, b4, b3, b2, b1]  # L6..L1 order
                confidences = [c6, c5, c4, c3, c2, c1]
                rationales = [r6, r5, r4, r3, r2, r1]

                hex_int = sum(b << i for i, b in enumerate(lines))
                linestring = "".join(str(b) for b in reversed(lines))

                step_record = {
                    "cycle": cycle,
                    "stage": terrain["name"],
                    "operator": op_name,
                    "lines": linestring,
                    "hex_int": hex_int,
                    "confidences": confidences,
                    "rationales": rationales,
                    "ga0": entry["ga0_after"],
                    "dphi_L": entry["dphi_L"],
                    "dphi_R": entry["dphi_R"],
                }
                microsteps.append(step_record)

                # Track stats
                for idx, (line_val, conf) in enumerate(zip(lines, confidences)):
                    key = f"L{idx+1}"
                    line_stats[key]["total"] += 1
                    line_stats[key][conf.lower()] += 1
                    line_stats[key]["yang"] += line_val

    return {
        "engine_type": engine_type,
        "seed": seed,
        "n_cycles": n_cycles,
        "total_microsteps": len(microsteps),
        "microsteps": microsteps,
        "line_stats": line_stats,
    }


def print_summary(result: Dict):
    """Print a human-readable summary of the decoding."""
    et = result["engine_type"]
    n = result["total_microsteps"]
    print(f"\n{'='*80}")
    print(f"RUNTIME-TO-STRUCTURE DECODER: Engine Type {et}, {n} microsteps")
    print(f"{'='*80}")

    # Line confidence breakdown
    print(f"\n  LINE CONFIDENCE BREAKDOWN:")
    print(f"  {'Line':<6} {'DIRECT':>8} {'INFERRED':>10} {'GUESS':>8} {'% yang':>8}")
    print(f"  {'-'*42}")
    for i in range(1, 7):
        key = f"L{i}"
        s = result["line_stats"][key]
        pct_yang = 100.0 * s["yang"] / max(s["total"], 1)
        print(f"  {key:<6} {s['direct']:>8} {s['inferred']:>10} {s['guess']:>8} {pct_yang:>7.1f}%")

    # Unique hexagram states visited
    hex_counts = {}
    for step in result["microsteps"]:
        ls = step["lines"]
        hex_counts[ls] = hex_counts.get(ls, 0) + 1

    print(f"\n  UNIQUE HEXAGRAM STATES VISITED: {len(hex_counts)} / 64")
    print(f"  TOP 10 MOST FREQUENT:")
    for ls, count in sorted(hex_counts.items(), key=lambda x: -x[1])[:10]:
        pct = 100.0 * count / n
        hexint = int(ls, 2)
        print(f"    {ls} (hex {hexint:>2d}): {count:>4} times ({pct:>5.1f}%)")

    # How many lines change per step?
    prev_lines = None
    transitions = []
    for step in result["microsteps"]:
        if prev_lines is not None:
            flips = sum(1 for a, b in zip(prev_lines, step["lines"]) if a != b)
            transitions.append(flips)
        prev_lines = step["lines"]

    if transitions:
        avg_flips = np.mean(transitions)
        print(f"\n  AVG LINES CHANGED PER MICROSTEP: {avg_flips:.2f}")
        print(f"  DISTRIBUTION: {dict(zip(*np.unique(transitions, return_counts=True)))}")


def main():
    print("RUNTIME-TO-STRUCTURE DECODER")
    print("Attempting to read candidate 6-line hexagram states from live engine.\n")
    print("This is an EXPLORATORY probe. Results are hypotheses, not canon.\n")

    all_results = {}
    for engine_type in (1, 2):
        for seed in (42, 123, 999):
            result = decode_trajectory(engine_type=engine_type, seed=seed, n_cycles=2)
            print_summary(result)
            all_results[f"type{engine_type}_seed{seed}"] = result

    # Cross-seed consistency check
    print(f"\n{'='*80}")
    print("CROSS-SEED CONSISTENCY CHECK")
    print(f"{'='*80}")
    for engine_type in (1, 2):
        keys = [k for k in all_results if k.startswith(f"type{engine_type}")]
        all_linestrings = []
        for k in keys:
            linestrings = [s["lines"] for s in all_results[k]["microsteps"]]
            all_linestrings.append(linestrings)

        # Compare sequences pairwise
        if len(all_linestrings) >= 2:
            for i in range(len(all_linestrings)):
                for j in range(i+1, len(all_linestrings)):
                    matches = sum(1 for a, b in zip(all_linestrings[i], all_linestrings[j]) if a == b)
                    total = min(len(all_linestrings[i]), len(all_linestrings[j]))
                    pct = 100.0 * matches / max(total, 1)
                    print(f"  Type {engine_type} {keys[i]} vs {keys[j]}: {pct:.1f}% identical hexagrams")

    # Save results (just the stats, not the full microstep arrays)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "runtime_to_structure_decoder.json")

    save_data = {}
    for k, v in all_results.items():
        save_data[k] = {
            "engine_type": v["engine_type"],
            "seed": v["seed"],
            "total_microsteps": v["total_microsteps"],
            "line_stats": v["line_stats"],
            "unique_states": len(set(s["lines"] for s in v["microsteps"])),
            "first_20_hexagrams": [s["lines"] for s in v["microsteps"][:20]],
        }

    with open(out_file, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\n  Results saved to {out_file}")


if __name__ == "__main__":
    main()
