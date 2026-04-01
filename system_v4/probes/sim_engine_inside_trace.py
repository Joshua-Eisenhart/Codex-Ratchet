#!/usr/bin/env python3
"""
Inside-geometry trace for the live engine.

This probe does not ask "are the axes orthogonal?"
It asks "what does the engine do from inside the geometry, microstep by microstep?"

It traces:
- torus coordinates
- ga0 target / ga0 update
- per-operator strength
- left/right spinor summaries
- chirality / coherence summaries

The trace is intended as an internal traversal surface, not a canonical proof.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from datetime import UTC, datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (  # noqa: E402
    GeometricEngine,
    EngineState,
    StageControls,
    OPERATORS,
    STAGES,
)
from geometric_operators import (  # noqa: E402
    apply_Ti,
    apply_Fe,
    apply_Te,
    apply_Fi,
    negentropy,
    partial_trace_A,
    partial_trace_B,
    trace_distance_2x2,
    _ensure_valid_density,
    SIGMA_X,
)
from hopf_manifold import (  # noqa: E402
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    inter_torus_transport_partial,
    density_to_bloch,
    torus_radii,
)


def density_summary(rho):
    b = density_to_bloch(rho)
    return {
        "negentropy": float(negentropy(rho)),
        "offdiag_mag": float(abs(rho[0, 1])),
        "bloch": [float(x) for x in b],
        "bloch_norm": float(np.linalg.norm(b)),
        "pop_gap": float(np.real(rho[0, 0] - rho[1, 1])),
    }


def q_vector(q):
    return [float(x) for x in q]


def wrapped_phase(theta2, theta1):
    return float(np.arctan2(np.sin(theta2 - theta1), np.cos(theta2 - theta1)))


def pair_summary(rho_L, rho_R):
    bL = density_to_bloch(rho_L)
    bR = density_to_bloch(rho_R)
    dot = float(np.dot(bL, bR) / (np.linalg.norm(bL) * np.linalg.norm(bR) + 1e-12))
    dot = float(np.clip(dot, -1.0, 1.0))
    return {
        "trace_distance_LR": float(trace_distance_2x2(rho_L, rho_R)),
        "bloch_angle": float(np.arccos(abs(dot))),
        "avg_negentropy": float(0.5 * (negentropy(rho_L) + negentropy(rho_R))),
    }


def control_program(name: str):
    if name == "default":
        return {i: StageControls() for i in range(8)}
    if name == "inner_outer_wave":
        torus_values = [
            0.39269908169872414,
            0.7853981633974483,
            1.1780972450961724,
            0.7853981633974483,
            1.1780972450961724,
            0.7853981633974483,
            0.39269908169872414,
            0.7853981633974483,
        ]
        return {
            i: StageControls(piston=0.8, lever=(i % 2 == 0), torus=torus_values[i], spinor="both")
            for i in range(8)
        }
    raise ValueError(f"unknown program: {name}")


def trace_one_cycle(engine_type: int, seed: int = 42, program: str = "default"):
    rng = np.random.default_rng(seed)
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(rng=rng)
    controls = control_program(program)
    microsteps = []

    current_state = copy.deepcopy(state)
    for stage_idx, terrain in enumerate(STAGES):
        ctrl = controls[stage_idx]
        for op_name in OPERATORS:
            before = copy.deepcopy(current_state)

            ga0_target = engine._ga0_target(terrain, op_name, ctrl)
            ga0_alpha = min(1.0, 0.10 + 0.45 * ctrl.piston + (0.10 if terrain["open"] else 0.0))
            if ga0_target is None:
                new_ga0 = float(current_state.ga0_level)
            else:
                new_ga0 = float(
                    np.clip((1.0 - ga0_alpha) * current_state.ga0_level + ga0_alpha * ga0_target, 0.0, 1.0)
                )
            strength = engine._operator_strength(terrain, op_name, ctrl, ga0_level=new_ga0)
            polarity = ctrl.lever
            angle_mod, dt_mod = engine._terrain_modulation(terrain)

            q_old = current_state.q()
            q_step = q_old
            new_eta = current_state.eta
            new_theta1 = current_state.theta1
            new_theta2 = current_state.theta2
            phase_before = wrapped_phase(before.theta2, before.theta1)

            if abs(ctrl.torus - current_state.eta) > 1e-8:
                alpha = engine._geometry_transport_alpha(current_state.eta, ctrl.torus, strength, new_ga0)
                q_step = inter_torus_transport_partial(q_old, current_state.eta, ctrl.torus, alpha)
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
                alpha = 0.0
                new_rho_L = current_state.rho_L.copy()
                new_rho_R = current_state.rho_R.copy()

            rho_AB_axis0 = engine._fiber_coarse_grained_density(q_step, new_ga0)
            rho_L_axis0 = _ensure_valid_density(partial_trace_B(rho_AB_axis0))
            rho_R_axis0 = _ensure_valid_density(partial_trace_A(rho_AB_axis0))
            axis0_blend = min(0.45, strength * (0.05 + 0.30 * new_ga0))
            axis0_injection_norm = float(
                np.linalg.norm(rho_L_axis0 - new_rho_L) + np.linalg.norm(rho_R_axis0 - new_rho_R)
            )
            axis0_effective_gain = float(axis0_blend * axis0_injection_norm)
            new_rho_L = _ensure_valid_density((1.0 - axis0_blend) * new_rho_L + axis0_blend * rho_L_axis0)
            new_rho_R = _ensure_valid_density((1.0 - axis0_blend) * new_rho_R + axis0_blend * rho_R_axis0)

            op_kwargs = {"polarity_up": polarity, "strength": strength}
            if op_name == "Te":
                op_kwargs["q"] = 0.3 * angle_mod
            if op_name == "Fe":
                op_kwargs["phi"] = 0.05 * dt_mod
            op_fn = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}[op_name]

            new_rho_L = op_fn(new_rho_L, **op_kwargs)

            right_kwargs = dict(op_kwargs)
            applied_op = op_name
            if op_name == "Te":
                right_kwargs["polarity_up"] = not polarity
            elif op_name == "Ti":
                phase = new_theta2 - new_theta1
                basis = np.array(
                    [[1.0, np.exp(1j * phase)], [1.0, -np.exp(1j * phase)]],
                    dtype=complex,
                ) / np.sqrt(2.0)
                rho_conj = basis @ new_rho_R @ basis.conj().T
                rho_conj = op_fn(rho_conj, **right_kwargs)
                new_rho_R = basis.conj().T @ rho_conj @ basis
                new_rho_R = _ensure_valid_density(new_rho_R)
                applied_op = None
            elif op_name == "Fe":
                rho_conj = SIGMA_X @ new_rho_R @ SIGMA_X
                rho_conj = op_fn(rho_conj, **right_kwargs)
                new_rho_R = SIGMA_X @ rho_conj @ SIGMA_X
                new_rho_R = _ensure_valid_density(new_rho_R)
                applied_op = None
            elif op_name == "Fi":
                rho_conj = SIGMA_X @ new_rho_R @ SIGMA_X
                rho_conj = op_fn(rho_conj, **right_kwargs)
                new_rho_R = SIGMA_X @ rho_conj @ SIGMA_X
                new_rho_R = _ensure_valid_density(new_rho_R)
                applied_op = None
            if applied_op is not None:
                new_rho_R = op_fn(new_rho_R, **right_kwargs)

            d_theta = (2 * np.pi / 32) * strength
            if terrain["loop"] == "fiber":
                new_theta2 = (new_theta2 + d_theta) % (2 * np.pi)
                new_theta1 = (new_theta1 + 0.5 * d_theta) % (2 * np.pi)
            else:
                new_theta1 = (new_theta1 + d_theta) % (2 * np.pi)
                new_theta2 = (new_theta2 + 0.5 * d_theta) % (2 * np.pi)

            q_current = np.array(
                [
                    np.cos(new_eta) * np.cos(new_theta1),
                    np.cos(new_eta) * np.sin(new_theta1),
                    np.sin(new_eta) * np.cos(new_theta2),
                    np.sin(new_eta) * np.sin(new_theta2),
                ],
                dtype=float,
            )
            current_state = EngineState(
                psi_L=left_weyl_spinor(q_current),
                psi_R=right_weyl_spinor(q_current),
                rho_AB=_ensure_valid_density(np.kron(new_rho_L, new_rho_R)),
                eta=new_eta,
                theta1=new_theta1,
                theta2=new_theta2,
                stage_idx=current_state.stage_idx,
                engine_type=engine_type,
                history=current_state.history + [],
            )

            R_major_before, R_minor_before = torus_radii(before.eta)
            R_major_after, R_minor_after = torus_radii(current_state.eta)
            q_after = current_state.q()
            microsteps.append(
                {
                    "stage_idx": stage_idx,
                    "terrain": terrain["name"],
                    "loop": terrain["loop"],
                    "expansion": terrain["expansion"],
                    "open": terrain["open"],
                    "operator": op_name,
                    "strength": float(strength),
                    "ga0_before": float(before.ga0_level),
                    "ga0_target": None if ga0_target is None else float(ga0_target),
                    "ga0_after": float(new_ga0),
                    "axis0_blend": float(axis0_blend),
                    "axis0_injection_norm": float(axis0_injection_norm),
                    "axis0_effective_gain": float(axis0_effective_gain),
                    "transport_alpha": float(alpha),
                    "transport_triggered": bool(abs(ctrl.torus - before.eta) > 1e-8),
                    "q_before": q_vector(q_old),
                    "q_after_transport": q_vector(q_step),
                    "q_after": q_vector(q_after),
                    "eta_before": float(before.eta),
                    "eta_after": float(current_state.eta),
                    "deta": float(current_state.eta - before.eta),
                    "theta1_before": float(before.theta1),
                    "theta1_after": float(current_state.theta1),
                    "dtheta1": float(current_state.theta1 - before.theta1),
                    "theta2_before": float(before.theta2),
                    "theta2_after": float(current_state.theta2),
                    "dtheta2": float(current_state.theta2 - before.theta2),
                    "phase_before": float(phase_before),
                    "phase_after_transport": float(wrapped_phase(new_theta2, new_theta1)),
                    "phase_after": float(wrapped_phase(current_state.theta2, current_state.theta1)),
                    "dphase": float(wrapped_phase(current_state.theta2, current_state.theta1) - phase_before),
                    "radii_before": [float(R_major_before), float(R_minor_before)],
                    "radii_after": [float(R_major_after), float(R_minor_after)],
                    "left_before": density_summary(before.rho_L),
                    "left_after": density_summary(current_state.rho_L),
                    "right_before": density_summary(before.rho_R),
                    "right_after": density_summary(current_state.rho_R),
                    "pair_before": pair_summary(before.rho_L, before.rho_R),
                    "pair_after": pair_summary(current_state.rho_L, current_state.rho_R),
                }
            )

        current_state.stage_idx += 1

    return {
        "engine_type": engine_type,
        "seed": seed,
        "program": program,
        "initial_pair": pair_summary(state.rho_L, state.rho_R),
        "final_pair": pair_summary(current_state.rho_L, current_state.rho_R),
        "microsteps": microsteps,
    }


def main():
    out = {
        "schema": "SIM_EVIDENCE_v1",
        "file": os.path.basename(__file__),
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "traces": [
            trace_one_cycle(1, 42, "default"),
            trace_one_cycle(2, 42, "default"),
            trace_one_cycle(1, 42, "inner_outer_wave"),
            trace_one_cycle(2, 42, "inner_outer_wave"),
        ],
    }

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "engine_inside_trace.json"
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)

    print("=" * 72)
    print("ENGINE INSIDE TRACE")
    print("=" * 72)
    for trace in out["traces"]:
        print(
            f"type {trace['engine_type']} [{trace['program']}]: "
            f"trace_distance {trace['initial_pair']['trace_distance_LR']:.4f}"
            f" -> {trace['final_pair']['trace_distance_LR']:.4f}, "
            f"avg_negentropy {trace['initial_pair']['avg_negentropy']:.4f}"
            f" -> {trace['final_pair']['avg_negentropy']:.4f}"
        )
    print(f"\nResults written to {out_file}")


if __name__ == "__main__":
    main()
