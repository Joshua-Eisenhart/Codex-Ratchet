#!/usr/bin/env python3
"""
Geometry Negative: No Chirality
================================
Runs the full 32-stage engine with right spinor getting IDENTICAL dynamics
(same left-branch operator law, no conjugate σ_x basis flip, no reversed Te rotation).
If chirality is real, removing it should collapse L/R divergence.

KILL token: S_NEG_NO_CHIRALITY
"""

import numpy as np
import os, sys, json
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine, EngineState, StageControls
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    trace_distance_2x2, negentropy, _ensure_valid_density,
)
from proto_ratchet_sim_runner import EvidenceToken


def step_no_chirality(engine: GeometricEngine, state: EngineState,
                      stage_idx: int, controls: StageControls) -> EngineState:
    """Run one stage with identical left-law dynamics on both spinors.

    We reuse the engine's real geometry / Axis 0 update by stepping the left path
    first. That step leaves rho_R updated by transport and coarse-graining but
    untouched by any operator-specific right-spinor conjugation. We then apply the
    same operator law used on the left branch directly to rho_R.
    """
    terrain = engine.stages[stage_idx]
    current_state = state
    new_history = list(state.history)

    from engine_core import OPERATORS, inter_torus_transport_partial, left_density, right_density, SIGMA_X, torus_coordinates

    for op_name in OPERATORS:
        ga0_target = engine._ga0_target(terrain, op_name, controls)
        ga0_alpha = min(1.0, 0.10 + 0.45 * controls.piston + (0.10 if terrain["open"] else 0.0))
        new_ga0 = float(np.clip((1.0 - ga0_alpha) * current_state.ga0_level + ga0_alpha * ga0_target, 0.0, 1.0))

        strength = engine._operator_strength(terrain, op_name, controls, ga0_level=new_ga0)
        polarity = controls.lever
        angle_mod, dt_mod = engine._terrain_modulation(terrain)

        q_old = current_state.q()
        q_step = q_old

        new_eta = controls.torus
        if abs(new_eta - current_state.eta) > 1e-8:
            alpha = engine._geometry_transport_alpha(current_state.eta, new_eta, strength, new_ga0)
            q_step = inter_torus_transport_partial(q_old, current_state.eta, new_eta, alpha)
            a, b, c, d = q_step
            z1 = a + 1j * b
            z2 = c + 1j * d
            new_theta1 = float(np.angle(z1))
            new_theta2 = float(np.angle(z2))
            new_eta = float(np.arctan2(abs(z2), abs(z1)))

            rho_L_geo = left_density(q_step)
            rho_R_geo = right_density(q_step)
            memory = 0.10 * (1.0 - alpha)
            new_rho_L = _ensure_valid_density((1.0 - memory) * rho_L_geo + memory * current_state.rho_L)
            new_rho_R = _ensure_valid_density((1.0 - memory) * rho_R_geo + memory * current_state.rho_R)
        else:
            new_eta = current_state.eta
            new_theta1 = current_state.theta1
            new_theta2 = current_state.theta2
            new_rho_L = current_state.rho_L.copy()
            new_rho_R = current_state.rho_R.copy()

        rho_L_axis0 = engine._fiber_coarse_grained_density(q_step, new_ga0, "left")
        rho_R_axis0 = engine._fiber_coarse_grained_density(q_step, new_ga0, "right")
        axis0_blend = min(0.45, strength * (0.05 + 0.30 * new_ga0))
        new_rho_L = _ensure_valid_density((1.0 - axis0_blend) * new_rho_L + axis0_blend * rho_L_axis0)
        new_rho_R = _ensure_valid_density((1.0 - axis0_blend) * new_rho_R + axis0_blend * rho_R_axis0)

        op_kwargs = {"polarity_up": polarity, "strength": strength}
        if op_name == "Te":
            op_kwargs["angle"] = 0.3 * angle_mod
        if op_name == "Fe":
            op_kwargs["dt"] = 0.05 * dt_mod

        op_fn = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}[op_name]

        # SAME LEFT-LAW DYNAMICS ON BOTH SPINORS
        new_rho_L = op_fn(new_rho_L, **op_kwargs)
        new_rho_R = op_fn(new_rho_R, **op_kwargs)  # NO CONJUGATION!

        d_theta = (2 * np.pi / 32) * strength
        if terrain["loop"] == "fiber":
            new_theta2 = (new_theta2 + d_theta) % (2 * np.pi)
            new_theta1 = (new_theta1 + 0.5 * d_theta) % (2 * np.pi)
        else:
            new_theta1 = (new_theta1 + d_theta) % (2 * np.pi)
            new_theta2 = (new_theta2 + 0.5 * d_theta) % (2 * np.pi)

        dphi_L = negentropy(new_rho_L) - negentropy(current_state.rho_L)
        dphi_R = negentropy(new_rho_R) - negentropy(current_state.rho_R)

        new_history.append({
            "stage": f"{terrain['name']}_{op_name}",
            "op_name": op_name,
            "dphi_L": dphi_L,
            "dphi_R": dphi_R,
            "rho_L": new_rho_L.copy(),
            "rho_R": new_rho_R.copy(),
            "strength": strength,
            "ga0_before": current_state.ga0_level,
            "ga0_after": new_ga0
        })

        current_state = EngineState(
            rho_L=new_rho_L, rho_R=new_rho_R,
            eta=new_eta, theta1=new_theta1, theta2=new_theta2,
            ga0_level=new_ga0,
            stage_idx=current_state.stage_idx,
            engine_type=engine.engine_type,
            history=new_history
        )

    current_state.stage_idx += 1
    return current_state


def run():
    tokens = []

    # Standard engine: full conjugate dynamics
    e = GeometricEngine(engine_type=1)
    s_chiral = e.init_state(rng=np.random.default_rng(42))
    s_chiral = e.run_cycle(s_chiral, controls={
        i: StageControls(piston=0.8) for i in range(8)
    })
    d_chiral = trace_distance_2x2(s_chiral.rho_L, s_chiral.rho_R)

    # De-chiralized engine: both spinors stay live, but R receives the same
    # left-branch operator law instead of the conjugate right-branch law.
    s_flat = e.init_state(rng=np.random.default_rng(42))
    for i in range(8):
        ctrl = StageControls(piston=0.8, spinor="both")
        s_flat = step_no_chirality(e, s_flat, stage_idx=i, controls=ctrl)
    d_flat = trace_distance_2x2(s_flat.rho_L, s_flat.rho_R)

    print(f"No-Chirality Negative:")
    print(f"  Chiral engine D(L,R): {d_chiral:.4f}")
    print(f"  De-chiralized D(L,R): {d_flat:.4f}")
    print(f"  Chirality creates divergence: {d_chiral > 0.05}")
    print(f"  → KILL (chirality removal must flatten L/R)")

    tokens.append(EvidenceToken("", "S_NEG_NO_CHIRALITY", "KILL",
                                float(d_chiral),
                                "CHIRALITY_FLATTENED"))

    base = os.path.dirname(os.path.abspath(__file__))
    outpath = os.path.join(base, "a2_state", "sim_results", "neg_no_chirality_results.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "d_chiral": float(d_chiral),
            "d_flat": float(d_flat),
            "chirality_matters": d_chiral > 0.05,
            "evidence_ledger": [t.__dict__ for t in tokens],
        }, f, indent=2)
    return tokens


if __name__ == "__main__":
    run()
