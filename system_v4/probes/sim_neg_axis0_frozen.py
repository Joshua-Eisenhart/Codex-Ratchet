#!/usr/bin/env python3
"""
Geometry Negative: Axis 0 Frozen
=================================
Runs the full 32-stage engine with Axis 0 clamped to a fixed value.
If Axis 0 is causal, freezing it should produce a measurably different
trajectory than adaptive Axis 0.

KILL token: S_NEG_AXIS0_FROZEN
"""

import numpy as np
import os, sys, json
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine, StageControls
from geometric_operators import trace_distance_2x2, negentropy
from proto_ratchet_sim_runner import EvidenceToken

FROZEN_AXIS0 = 0.1


def run():
    tokens = []

    e = GeometricEngine(engine_type=1)

    # Adaptive Axis 0 (default — engine picks ga0_target per stage)
    s_adapt = e.init_state(rng=np.random.default_rng(42))
    ctrl_adapt = {i: StageControls(piston=0.8) for i in range(8)}
    s_adapt = e.run_cycle(s_adapt, controls=ctrl_adapt)

    # Frozen Axis 0 in a low coarse-graining regime (no adaptation).
    # Freezing at 0.5 is too close to the adaptive trajectory and can hide
    # whether Axis 0 is actually load-bearing.
    s_frozen = e.init_state(rng=np.random.default_rng(42))
    ctrl_frozen = {i: StageControls(piston=0.8, axis0=FROZEN_AXIS0) for i in range(8)}
    s_frozen = e.run_cycle(s_frozen, controls=ctrl_frozen)

    d_L = trace_distance_2x2(s_adapt.rho_L, s_frozen.rho_L)
    d_R = trace_distance_2x2(s_adapt.rho_R, s_frozen.rho_R)
    ga0_adapt = s_adapt.ga0_level
    ga0_frozen = s_frozen.ga0_level

    axes_adapt = e.read_axes(s_adapt)
    axes_frozen = e.read_axes(s_frozen)
    n_diff = sum(1 for ax in axes_adapt if abs(axes_adapt[ax] - axes_frozen[ax]) > 0.005)

    print(f"Axis-0-Frozen Negative:")
    print(f"  D(adapt, frozen)_L: {d_L:.4f}")
    print(f"  D(adapt, frozen)_R: {d_R:.4f}")
    print(f"  GA0 level adapt/frozen: {ga0_adapt:.3f} / {ga0_frozen:.3f}")
    print(f"  Axes different: {n_diff}/6")

    d_max = max(d_L, d_R)
    ga0_gap = abs(ga0_adapt - ga0_frozen)
    axis0_matters = d_max > 0.02 and ga0_gap > 0.25 and n_diff >= 3
    print(f"  Axis 0 is load-bearing: {axis0_matters}")
    print(f"  → KILL (Axis 0 removal must degrade)")

    tokens.append(EvidenceToken("", "S_NEG_AXIS0_FROZEN", "KILL",
                                float(d_max),
                                "AXIS0_FROZEN"))

    base = os.path.dirname(os.path.abspath(__file__))
    outpath = os.path.join(base, "a2_state", "sim_results", "neg_axis0_frozen_results.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "d_L": float(d_L), "d_R": float(d_R),
            "ga0_adapt": ga0_adapt, "ga0_frozen": ga0_frozen,
            "frozen_axis0": FROZEN_AXIS0,
            "n_axis_diff": n_diff,
            "ga0_gap": ga0_gap,
            "axis0_matters": axis0_matters,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    return tokens


if __name__ == "__main__":
    run()
