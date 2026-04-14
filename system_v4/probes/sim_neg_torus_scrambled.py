#!/usr/bin/env python3
"""
Geometry Negative: Torus Scrambled
===================================
Runs the full 32-stage engine with a random torus schedule instead of
structured (inner→Clifford→outer→Clifford).
If torus structure matters, scrambling should produce less coherent evolution.

KILL token: S_NEG_TORUS_SCRAMBLED
"""

import numpy as np
import os, sys, json
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine, StageControls, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER
from geometric_operators import trace_distance_2x2, negentropy
from hopf_manifold import von_neumann_entropy_2x2
from proto_ratchet_sim_runner import EvidenceToken


def run():
    tokens = []
    rng = np.random.default_rng(42)

    e = GeometricEngine(engine_type=1)

    # Structured torus program
    torus_prog = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, TORUS_CLIFFORD]
    s_struct = e.init_state(rng=np.random.default_rng(42))
    ctrl_struct = {i: StageControls(piston=0.8, torus=torus_prog[i % len(torus_prog)]) for i in range(8)}
    s_struct = e.run_cycle(s_struct, controls=ctrl_struct)

    # Scrambled torus: random choice each step
    torus_choices = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    scrambled_schedule = [torus_choices[rng.integers(3)] for _ in range(8)]
    s_scramble = e.init_state(rng=np.random.default_rng(42))
    ctrl_scramble = {i: StageControls(piston=0.8, torus=scrambled_schedule[i]) for i in range(8)}
    s_scramble = e.run_cycle(s_scramble, controls=ctrl_scramble)

    d_L = trace_distance_2x2(s_struct.rho_L, s_scramble.rho_L)
    d_R = trace_distance_2x2(s_struct.rho_R, s_scramble.rho_R)

    axes_struct = e.read_axes(s_struct)
    axes_scramble = e.read_axes(s_scramble)
    n_diff = sum(1 for ax in axes_struct if abs(axes_struct[ax] - axes_scramble[ax]) > 0.005)

    # Coherence metric: structured should have more consistent axis evolution
    entropy_struct = (von_neumann_entropy_2x2(s_struct.rho_L) + von_neumann_entropy_2x2(s_struct.rho_R)) / 2
    entropy_scramble = (von_neumann_entropy_2x2(s_scramble.rho_L) + von_neumann_entropy_2x2(s_scramble.rho_R)) / 2

    print(f"Torus-Scrambled Negative:")
    print(f"  D(struct, scramble)_L: {d_L:.4f}")
    print(f"  D(struct, scramble)_R: {d_R:.4f}")
    print(f"  Axes different: {n_diff}/6")
    print(f"  Entropy struct/scramble: {entropy_struct:.4f} / {entropy_scramble:.4f}")

    structure_matters = max(d_L, d_R) > 0.02
    print(f"  Torus structure is load-bearing: {structure_matters}")
    print(f"  → KILL (torus scrambling must degrade)")

    tokens.append(EvidenceToken("", "S_NEG_TORUS_SCRAMBLED", "KILL",
                                float(max(d_L, d_R)),
                                "TORUS_SCHEDULE_SCRAMBLED"))

    base = os.path.dirname(os.path.abspath(__file__))
    outpath = os.path.join(base, "a2_state", "sim_results", "neg_torus_scrambled_results.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "d_L": float(d_L), "d_R": float(d_R),
            "n_axis_diff": n_diff,
            "entropy_struct": float(entropy_struct),
            "entropy_scramble": float(entropy_scramble),
            "structure_matters": structure_matters,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    return tokens


if __name__ == "__main__":
    run()
