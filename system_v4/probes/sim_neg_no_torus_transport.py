#!/usr/bin/env python3
"""
Geometry Negative: No Torus Transport
======================================
Runs the full 32-stage engine cycle with torus clamped to Clifford.
If the torus control is load-bearing, removing it should produce a
measurably different (worse) trajectory than the standard engine.

KILL token: S_NEG_NO_TORUS_TRANSPORT
"""

import numpy as np
import os, sys, json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine, StageControls, TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER
from geometric_operators import trace_distance_2x2, negentropy
from proto_ratchet_sim_runner import EvidenceToken


def run():
    tokens = []
    rng = np.random.default_rng(42)

    # Standard engine: uses torus program (inner→Clifford→outer→Clifford cycling)
    e = GeometricEngine(engine_type=1)
    s_std = e.init_state(rng=np.random.default_rng(42))
    torus_prog = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, TORUS_CLIFFORD]
    ctrl_std = {i: StageControls(piston=0.8, torus=torus_prog[i % len(torus_prog)]) for i in range(8)}
    s_std = e.run_cycle(s_std, controls=ctrl_std)

    # Clamped engine: torus always Clifford (no transport)
    s_clamp = e.init_state(rng=np.random.default_rng(42))
    ctrl_clamp = {i: StageControls(piston=0.8, torus=TORUS_CLIFFORD) for i in range(8)}
    s_clamp = e.run_cycle(s_clamp, controls=ctrl_clamp)

    # Measure divergence
    d_L = trace_distance_2x2(s_std.rho_L, s_clamp.rho_L)
    d_R = trace_distance_2x2(s_std.rho_R, s_clamp.rho_R)

    # Axis comparison
    axes_std = e.read_axes(s_std)
    axes_clamp = e.read_axes(s_clamp)
    n_axis_diff = sum(1 for ax in axes_std if abs(axes_std[ax] - axes_clamp[ax]) > 0.005)

    print(f"No-Torus-Transport Negative:")
    print(f"  D(std, clamp)_L: {d_L:.4f}")
    print(f"  D(std, clamp)_R: {d_R:.4f}")
    print(f"  Axes different: {n_axis_diff}/6")

    # This SHOULD show a real difference — if it doesn't, torus is NOT load-bearing
    torus_matters = max(d_L, d_R) > 0.02
    print(f"  Torus transport is load-bearing: {torus_matters}")
    print(f"  → KILL (geometry removal must degrade)")

    tokens.append(EvidenceToken("", "S_NEG_NO_TORUS_TRANSPORT", "KILL",
                                float(max(d_L, d_R)),
                                "TORUS_TRANSPORT_REMOVED"))

    base = os.path.dirname(os.path.abspath(__file__))
    outpath = os.path.join(base, "a2_state", "sim_results", "neg_no_torus_transport_results.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "d_L": float(d_L), "d_R": float(d_R),
            "n_axis_diff": n_axis_diff,
            "torus_matters": torus_matters,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    return tokens


if __name__ == "__main__":
    run()
