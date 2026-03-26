from __future__ import annotations
import numpy as np
from engine_core import GeometricEngine, EngineState, StageControls, OPERATORS, TERRAINS
from geometric_operators import apply_Ti, apply_Fe, apply_Te, apply_Fi, negentropy, trace_distance_2x2, _ensure_valid_density, SIGMA_X
from hopf_manifold import left_density, right_density, inter_torus_transport_partial
from process_cycle_stage_matrix_sim import terrain_name_from_row, torus_for_loop

AXIS_EPS = 0.005
TERRAIN_INDEX = {terrain["name"]: idx for idx, terrain in enumerate(TERRAINS)}
OP_FN = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}

def init_stage(engine_type: int, row: tuple, trial_seed: int) -> tuple[GeometricEngine, EngineState, dict]:
    stage_num, topo, native_operator, label, axis6_up, loop_role = row
    terrain_name = terrain_name_from_row(topo, loop_role)
    torus_target = torus_for_loop(loop_role)

    rng = np.random.default_rng(trial_seed)
    theta1 = float(rng.uniform(0, 2 * np.pi))
    theta2 = float(rng.uniform(0, 2 * np.pi))

    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(
        eta=torus_target,
        theta1=theta1,
        theta2=theta2,
        rng=rng,
    )
    meta = {
        "stage_num": stage_num,
        "topology": topo,
        "native_operator": native_operator,
        "label": label,
        "axis6_up": bool(axis6_up),
        "loop_role": loop_role,
        "terrain_name": terrain_name,
        "terrain_idx": TERRAIN_INDEX[terrain_name],
        "torus_target": float(torus_target),
    }
    return engine, state, meta

def summarize_axes(delta_axes: dict[str, float]) -> dict[str, float]:
    return {k: float(v) for k, v in delta_axes.items()}

def axes_delta(engine: GeometricEngine, before: EngineState, after: EngineState) -> dict[str, float]:
    axes_before = engine.read_axes(before)
    axes_after = engine.read_axes(after)
    return {k: float(axes_after[k] - axes_before[k]) for k in axes_before}

def apply_subcycle_variant(
    engine: GeometricEngine,
    state: EngineState,
    terrain: dict,
    op_name: str,
    controls: StageControls,
    *,
    lever_override: bool | None = None,
    flatten_type_weighting: bool = False,
) -> EngineState:
    ga0_target = engine._ga0_target(terrain, op_name, controls)
    ga0_alpha = min(1.0, 0.10 + 0.45 * controls.piston + (0.10 if terrain["open"] else 0.0))
    new_ga0 = float(np.clip((1.0 - ga0_alpha) * state.ga0_level + ga0_alpha * ga0_target, 0.0, 1.0))

    if flatten_type_weighting:
        strength = controls.piston
        if op_name in ("Te", "Fe"):
            strength *= 0.7 + 0.6 * new_ga0
        else:
            strength *= 1.3 - 0.6 * new_ga0
        strength = float(np.clip(strength, 0.0, 1.0))
    else:
        strength = float(engine._operator_strength(terrain, op_name, controls, ga0_level=new_ga0))

    polarity = controls.lever if lever_override is None else lever_override
    angle_mod, dt_mod = engine._terrain_modulation(terrain)

    q_old = state.q()
    q_step = q_old
    new_eta = controls.torus
    if abs(new_eta - state.eta) > 1e-8:
        alpha = engine._geometry_transport_alpha(state.eta, new_eta, strength, new_ga0)
        q_step = inter_torus_transport_partial(q_old, state.eta, new_eta, alpha)
        a, b, c, d = q_step
        z1 = a + 1j * b
        z2 = c + 1j * d
        new_theta1 = float(np.angle(z1))
        new_theta2 = float(np.angle(z2))
        new_eta = float(np.arctan2(abs(z2), abs(z1)))

        rho_L_geo = left_density(q_step)
        rho_R_geo = right_density(q_step)
        memory = 0.10 * (1.0 - alpha)
        new_rho_L = _ensure_valid_density((1.0 - memory) * rho_L_geo + memory * state.rho_L)
        new_rho_R = _ensure_valid_density((1.0 - memory) * rho_R_geo + memory * state.rho_R)
    else:
        new_eta = state.eta
        new_theta1 = state.theta1
        new_theta2 = state.theta2
        new_rho_L = state.rho_L.copy()
        new_rho_R = state.rho_R.copy()

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

    op_fn = OP_FN[op_name]

    if controls.spinor in ("left", "both"):
        new_rho_L = op_fn(new_rho_L, **op_kwargs)

    if controls.spinor in ("right", "both"):
        right_kwargs = dict(op_kwargs)
        applied_op = op_name
        if applied_op == "Te":
            right_kwargs["polarity_up"] = not polarity
        elif applied_op == "Ti":
            phase = new_theta2 - new_theta1
            basis = np.array(
                [[1.0, np.exp(1j * phase)],
                 [1.0, -np.exp(1j * phase)]],
                dtype=complex,
            ) / np.sqrt(2.0)
            rho_conj = basis @ new_rho_R @ basis.conj().T
            rho_conj = op_fn(rho_conj, **right_kwargs)
            new_rho_R = basis.conj().T @ rho_conj @ basis
            new_rho_R = _ensure_valid_density(new_rho_R)
            applied_op = None
        elif applied_op == "Fe":
            rho_conj = SIGMA_X @ new_rho_R @ SIGMA_X
            rho_conj = op_fn(rho_conj, **right_kwargs)
            new_rho_R = SIGMA_X @ rho_conj @ SIGMA_X
            new_rho_R = _ensure_valid_density(new_rho_R)
            applied_op = None
        elif applied_op == "Fi":
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

    return EngineState(
        rho_L=new_rho_L,
        rho_R=new_rho_R,
        eta=new_eta,
        theta1=new_theta1,
        theta2=new_theta2,
        ga0_level=new_ga0,
        stage_idx=state.stage_idx,
        engine_type=state.engine_type,
        history=list(state.history),
    )

def run_program_variant(
    engine_type: int,
    row: tuple,
    trial_seed: int,
    *,
    operator_order: list[str],
    lever_program: list[bool],
    flatten_type_weighting: bool = False,
) -> dict:
    engine, state, meta = init_stage(engine_type, row, trial_seed)
    terrain = TERRAINS[meta["terrain_idx"]]
    before = state
    controls = StageControls(
        piston=0.8,
        lever=meta["axis6_up"],
        torus=meta["torus_target"],
        spinor="both",
    )

    subcycles = []
    prev_L = state.rho_L.copy()
    prev_R = state.rho_R.copy()

    for idx, (op_name, lever) in enumerate(zip(operator_order, lever_program), start=1):
        state = apply_subcycle_variant(
            engine,
            state,
            terrain,
            op_name,
            controls,
            lever_override=lever,
            flatten_type_weighting=flatten_type_weighting,
        )
        subcycles.append({
            "subcycle_idx": idx,
            "operator": op_name,
            "axis6_up": bool(lever),
            "trace_L": float(trace_distance_2x2(prev_L, state.rho_L)),
            "trace_R": float(trace_distance_2x2(prev_R, state.rho_R)),
            "dphi_L": float(negentropy(state.rho_L) - negentropy(prev_L)),
            "dphi_R": float(negentropy(state.rho_R) - negentropy(prev_R)),
        })
        prev_L = state.rho_L.copy()
        prev_R = state.rho_R.copy()

    return {
        "meta": meta,
        "final_state": state,
        "macro_trace_L": float(trace_distance_2x2(before.rho_L, state.rho_L)),
        "macro_trace_R": float(trace_distance_2x2(before.rho_R, state.rho_R)),
        "delta_axes": summarize_axes(axes_delta(engine, before, state)),
        "subcycles": subcycles,
    }

def compare_variants(base: dict, alt: dict) -> dict:
    base_state = base["final_state"]
    alt_state = alt["final_state"]
    axis_diff = {
        key: float(alt["delta_axes"][key] - base["delta_axes"][key])
        for key in base["delta_axes"]
    }
    return {
        "d_L": float(trace_distance_2x2(base_state.rho_L, alt_state.rho_L)),
        "d_R": float(trace_distance_2x2(base_state.rho_R, alt_state.rho_R)),
        "axis_diff": axis_diff,
        "n_axis_diff": int(sum(abs(v) > AXIS_EPS for v in axis_diff.values())),
    }

def mean_metric(records: list[dict], key: str) -> float:
    return float(np.mean([r[key] for r in records]))

def summarize_family(records_by_name: dict[str, list[dict]]) -> dict:
    summary = {}
    for name, records in records_by_name.items():
        summary[name] = {
            "mean_d_L": mean_metric(records, "d_L"),
            "mean_d_R": mean_metric(records, "d_R"),
            "mean_total_d": float(np.mean([r["d_L"] + r["d_R"] for r in records])),
            "mean_axis_diff_count": float(np.mean([r["n_axis_diff"] for r in records])),
        }
    return summary
