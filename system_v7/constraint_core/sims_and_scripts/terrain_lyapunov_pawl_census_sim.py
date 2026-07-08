#!/usr/bin/env python3
"""Per-terrain Lyapunov pawl census.

Additive scratch diagnostic for the pawl-coordinate edge.  It asks which
licensed entropy coordinates are monotone along each of the eight terrain
flows over a seeded dense qubit-state grid, then tests whether operator-pair
composition preserves the shared U-pawl.

No Shannon/classical entropy.  No promotion claim.
classification=scratch_diagnostic; promotion_allowed=false.
"""
from __future__ import annotations

import json
import math
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy.linalg import expm


HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "terrain_lyapunov_pawl_census_sim_results.json"

SIM_ID = "terrain_lyapunov_pawl_census_sim"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
structural_tokens_only = True

TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "density matrices, Bloch vectors, eigenspectra, seeded state grid, monotonicity census",
    },
    "scipy.linalg.expm": {
        "used": True,
        "reason": "unitary operator maps and unitary-only flow control",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy.linalg.expm": "supportive",
}

SEED = 0
NOISE_THRESHOLD = 1e-7
STRICT_HOLD_THRESHOLD = 1e-9
G = 0.35
KAP = 1.0
Q = 1.0 - float(np.exp(-1.0))
TH = np.pi / 4.0
FLOW_SEGMENTS = 24
STEPS_PER_SEGMENT = 10
FLOW_T = 2.4
GRID_RANDOM_STATES = 160
L3_SEGMENTS = 24

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
H0 = (SX + SY + SZ) / np.sqrt(3.0)
BASIS_MATS = (
    np.array([[1, 0], [0, 0]], complex),
    np.array([[0, 1], [0, 0]], complex),
    np.array([[0, 0], [1, 0]], complex),
    np.array([[0, 0], [0, 1]], complex),
)

TERR = {
    0: (+1, "damp", +1),
    1: (+1, "depol", 0),
    2: (+1, "damp", -1),
    3: (+1, "proj", 0),
    4: (-1, "damp", -1),
    5: (-1, "depol", 0),
    6: (-1, "damp", +1),
    7: (-1, "proj", 0),
}

TERRAIN_LABELS = {
    0: "Se_f/direct_damp_plus",
    1: "Ne_f/direct_depol",
    2: "Ni_f/conjugate_damp_minus",
    3: "Si_f/conjugate_proj",
    4: "Se_b/direct_damp_minus",
    5: "Ne_b/direct_depol_minus",
    6: "Ni_b/conjugate_damp_plus",
    7: "Si_b/conjugate_proj_minus",
}

NATIVE = {
    0: ("Ti", "Fi"),
    1: ("Ti", "Fi"),
    2: ("Te", "Fe"),
    3: ("Te", "Fe"),
    4: ("Ti", "Fi"),
    5: ("Ti", "Fi"),
    6: ("Te", "Fe"),
    7: ("Te", "Fe"),
}

OPS = ("Ti", "Te", "Fi", "Fe")
OPERATOR_PAIRS = (
    ("Ti", "Te"),
    ("Ti", "Fi"),
    ("Ti", "Fe"),
    ("Te", "Fi"),
    ("Te", "Fe"),
    ("Fi", "Fe"),
)


def round_float(value: float, digits: int = 10) -> float:
    return round(float(value), digits)


def normalize_rho(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / np.trace(rho).real


def rho_from_bloch(v: np.ndarray | list[float]) -> np.ndarray:
    vec = np.asarray(v, dtype=float)
    return normalize_rho(0.5 * (I2 + vec[0] * SX + vec[1] * SY + vec[2] * SZ))


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.trace(rho @ s).real) for s in (SX, SY, SZ)])


def bloch_radius(rho: np.ndarray) -> float:
    return float(np.linalg.norm(bloch(rho)))


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def eigenvalues_density(rho: np.ndarray) -> np.ndarray:
    vals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    return np.clip(vals.real, 0.0, 1.0)


def vn_entropy(rho: np.ndarray) -> float:
    vals = eigenvalues_density(rho)
    vals = vals[vals > 1e-14]
    return float(-np.sum(vals * np.log(vals)))


def matrix_log_psd(rho: np.ndarray, floor: float = 1e-12) -> np.ndarray:
    vals, vecs = np.linalg.eigh(0.5 * (rho + rho.conj().T))
    vals = np.clip(vals.real, floor, None)
    return vecs @ np.diag(np.log(vals)) @ vecs.conj().T


def relative_entropy(rho: np.ndarray, sigma: np.ndarray) -> float:
    rho = normalize_rho(rho)
    sigma = normalize_rho(sigma + 1e-12 * I2)
    log_rho = matrix_log_psd(rho, floor=1e-12)
    log_sigma = matrix_log_psd(sigma, floor=1e-12)
    value = float(np.real(np.trace(rho @ (log_rho - log_sigma))))
    return max(value, 0.0)


def projectors_for_axis(axis: str) -> list[np.ndarray]:
    if axis == "z":
        return [0.5 * (I2 + SZ), 0.5 * (I2 - SZ)]
    if axis == "x":
        return [0.5 * (I2 + SX), 0.5 * (I2 - SX)]
    if axis == "h0":
        _, vecs = np.linalg.eigh(H0)
        return [np.outer(vecs[:, i], vecs[:, i].conj()) for i in range(2)]
    raise ValueError(f"unknown pointer axis {axis!r}")


def dephase_in_basis(rho: np.ndarray, projectors: list[np.ndarray]) -> np.ndarray:
    return normalize_rho(sum(p @ rho @ p for p in projectors))


def coherence_in_basis(rho: np.ndarray, projectors: list[np.ndarray]) -> float:
    return max(vn_entropy(dephase_in_basis(rho, projectors)) - vn_entropy(rho), 0.0)


def pointer_axis_for_terrain(ti: int) -> str:
    _, kind, _ = TERR[ti]
    if kind in {"damp", "proj"}:
        return "z"
    return "h0"


def foreign_pointer_axis(axis: str) -> str:
    if axis == "z":
        return "x"
    if axis == "x":
        return "z"
    return "z"


def dop(lindblad_op: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return (
        lindblad_op @ rho @ lindblad_op.conj().T
        - 0.5 * (lindblad_op.conj().T @ lindblad_op @ rho + rho @ lindblad_op.conj().T @ lindblad_op)
    )


def terrain_generator(ti: int) -> Callable[[np.ndarray], np.ndarray]:
    eps, kind, pole = TERR[ti]
    hamiltonian = eps * H0

    def x_dot(rho: np.ndarray) -> np.ndarray:
        out = -1j * G * (hamiltonian @ rho - rho @ hamiltonian)
        if kind == "damp":
            out = out + KAP * dop(SP if pole > 0 else SM, rho)
        elif kind == "depol":
            out = out + 0.5 * KAP * (dop(SX, rho) + dop(SY, rho))
        elif kind == "proj":
            out = out + KAP * dop(SZ, rho)
        else:
            raise ValueError(f"unknown terrain kind {kind!r}")
        return out

    return x_dot


def rk4_step(x_dot: Callable[[np.ndarray], np.ndarray], rho: np.ndarray, dt: float) -> np.ndarray:
    k1 = x_dot(rho)
    k2 = x_dot(rho + 0.5 * dt * k1)
    k3 = x_dot(rho + 0.5 * dt * k2)
    k4 = x_dot(rho + dt * k3)
    return normalize_rho(rho + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4))


@lru_cache(maxsize=None)
def terrain_channel_matrix(ti: int, dt: float) -> np.ndarray:
    x_dot = terrain_generator(ti)
    generator = np.column_stack([x_dot(basis).reshape(-1) for basis in BASIS_MATS])
    return expm(generator * dt)


def apply_channel_matrix(channel: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return normalize_rho((channel @ rho.reshape(-1)).reshape(2, 2))


def terrain_flow(
    ti: int,
    rho: np.ndarray,
    *,
    total_t: float = FLOW_T,
    segments: int = FLOW_SEGMENTS,
    steps_per_segment: int = STEPS_PER_SEGMENT,
) -> list[np.ndarray]:
    state = rho.copy()
    traj = [state.copy()]
    del steps_per_segment
    dt = total_t / float(segments)
    channel = terrain_channel_matrix(ti, dt)
    for _ in range(segments):
        state = apply_channel_matrix(channel, state)
        traj.append(state.copy())
    return traj


def terrain_endpoint(ti: int, rho: np.ndarray, *, total_t: float = FLOW_T) -> np.ndarray:
    return terrain_flow(ti, rho, total_t=total_t)[-1]


def long_fixed_point(ti: int) -> np.ndarray:
    _, kind, _ = TERR[ti]
    if kind in {"depol", "proj"}:
        return 0.5 * I2
    generator = np.column_stack([terrain_generator(ti)(basis).reshape(-1) for basis in BASIS_MATS])
    _, _, vh = np.linalg.svd(generator)
    candidate = vh[-1].reshape(2, 2)
    candidate = 0.5 * (candidate + candidate.conj().T)
    if np.trace(candidate).real < 0:
        candidate = -candidate
    return normalize_rho(candidate)


def operator_map(name: str) -> Callable[[np.ndarray], np.ndarray]:
    p0, p1 = projectors_for_axis("z")
    qp, qm = projectors_for_axis("x")
    if name == "Ti":
        return lambda rho: normalize_rho((1.0 - Q) * rho + Q * (p0 @ rho @ p0 + p1 @ rho @ p1))
    if name == "Te":
        return lambda rho: normalize_rho((1.0 - Q) * rho + Q * (qp @ rho @ qp + qm @ rho @ qm))
    if name == "Fi":
        u = expm(-1j * TH / 2.0 * SX)
        return lambda rho: normalize_rho(u @ rho @ u.conj().T)
    if name == "Fe":
        u = expm(-1j * TH / 2.0 * SZ)
        return lambda rho: normalize_rho(u @ rho @ u.conj().T)
    raise ValueError(f"unknown operator {name!r}")


def pair_family(pair: tuple[str, str]) -> str:
    deph = {"Ti", "Te"}
    unit = {"Fi", "Fe"}
    if pair[0] in deph and pair[1] in deph:
        return "dissipative_dissipative_control"
    if pair[0] in unit and pair[1] in unit:
        return "unitary_unitary_control"
    return "dissipative_unitary"


def pair_map(pair: tuple[str, str]) -> Callable[[np.ndarray], np.ndarray]:
    first = operator_map(pair[0])
    second = operator_map(pair[1])
    return lambda rho: second(first(rho))


def terrain_pair_composed_flow(
    ti: int,
    pair: tuple[str, str],
    rho: np.ndarray,
    *,
    total_t: float = FLOW_T,
    segments: int = L3_SEGMENTS,
    steps_per_segment: int = STEPS_PER_SEGMENT,
) -> list[np.ndarray]:
    op_pair = pair_map(pair)
    state = rho.copy()
    traj = [state.copy()]
    del steps_per_segment
    dt = total_t / float(segments)
    channel = terrain_channel_matrix(ti, dt)
    for _ in range(segments):
        state = apply_channel_matrix(channel, state)
        state = op_pair(state)
        traj.append(state.copy())
    return traj


def unitary_only_flow(ti: int, rho: np.ndarray, *, total_t: float = FLOW_T, segments: int = FLOW_SEGMENTS) -> list[np.ndarray]:
    eps, _, _ = TERR[ti]
    dt = total_t / float(segments)
    state = rho.copy()
    traj = [state.copy()]
    for _ in range(segments):
        u = expm(-1j * eps * G * dt * H0)
        state = normalize_rho(u @ state @ u.conj().T)
        traj.append(state.copy())
    return traj


def seeded_state_grid(rng: np.random.Generator) -> list[np.ndarray]:
    states: list[np.ndarray] = []
    directions = [
        [1, 0, 0],
        [-1, 0, 0],
        [0, 1, 0],
        [0, -1, 0],
        [0, 0, 1],
        [0, 0, -1],
        [1, 1, 1],
        [1, 1, -1],
        [1, -1, 1],
        [-1, 1, 1],
        [1, -1, 0.5],
        [-0.5, 1, 1],
    ]
    radii = [0.0, 0.05, 0.18, 0.33, 0.52, 0.71, 0.88, 0.97]
    for radius in radii:
        for direction in directions:
            d = np.asarray(direction, dtype=float)
            n = np.linalg.norm(d)
            states.append(rho_from_bloch(np.zeros(3) if n == 0.0 else radius * d / n))
    for _ in range(GRID_RANDOM_STATES):
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        radius = rng.uniform(0.01, 0.985)
        states.append(rho_from_bloch(radius * d))
    return states


def metric_functions(fixed_points: dict[int, np.ndarray], ti: int) -> dict[str, Callable[[np.ndarray], float]]:
    axis = pointer_axis_for_terrain(ti)
    projectors = projectors_for_axis(axis)
    return {
        "S_von_Neumann": vn_entropy,
        "U_relative_to_fixed_point": lambda rho: relative_entropy(rho, fixed_points[ti]),
        "C_pointer_coherence": lambda rho: coherence_in_basis(rho, projectors),
        "bloch_radius_r": bloch_radius,
        "purity_tr_rho2": purity,
    }


def monotonicity_class(seq_values: list[list[float]], threshold: float = NOISE_THRESHOLD) -> dict[str, Any]:
    inc_violations = []
    dec_violations = []
    net_deltas = []
    worst_inc_case: dict[str, Any] | None = None
    worst_dec_case: dict[str, Any] | None = None
    for state_idx, seq in enumerate(seq_values):
        if len(seq) < 2:
            continue
        net_deltas.append(float(seq[-1] - seq[0]))
        for step_idx in range(len(seq) - 1):
            delta = float(seq[step_idx + 1] - seq[step_idx])
            inc_violation = max(0.0, -delta)
            dec_violation = max(0.0, delta)
            inc_violations.append(inc_violation)
            dec_violations.append(dec_violation)
            if worst_inc_case is None or inc_violation > worst_inc_case["violation"]:
                worst_inc_case = {"state_index": state_idx, "step": step_idx, "violation": inc_violation, "delta": delta}
            if worst_dec_case is None or dec_violation > worst_dec_case["violation"]:
                worst_dec_case = {"state_index": state_idx, "step": step_idx, "violation": dec_violation, "delta": delta}
    max_inc_violation = max(inc_violations) if inc_violations else 0.0
    max_dec_violation = max(dec_violations) if dec_violations else 0.0
    inc_ok = max_inc_violation <= threshold
    dec_ok = max_dec_violation <= threshold
    all_hold = max([abs(x) for x in net_deltas] + [0.0]) <= STRICT_HOLD_THRESHOLD
    if inc_ok and not all_hold:
        cls = "monotone-increasing"
        direction = "increasing"
        max_violation = max_inc_violation
        worst_case = worst_inc_case
    elif dec_ok and not all_hold:
        cls = "monotone-decreasing"
        direction = "decreasing"
        max_violation = max_dec_violation
        worst_case = worst_dec_case
    elif inc_ok and dec_ok:
        cls = "constant"
        direction = "constant"
        max_violation = max(max_inc_violation, max_dec_violation)
        worst_case = worst_inc_case if max_inc_violation >= max_dec_violation else worst_dec_case
    else:
        cls = "non-monotone"
        direction = "none"
        max_violation = min(max_inc_violation, max_dec_violation)
        worst_case = worst_inc_case if max_inc_violation <= max_dec_violation else worst_dec_case
    return {
        "classification": cls,
        "direction": direction,
        "pawl": cls in {"monotone-increasing", "monotone-decreasing", "constant"},
        "threshold": threshold,
        "max_increasing_violation": round_float(max_inc_violation, 12),
        "max_decreasing_violation": round_float(max_dec_violation, 12),
        "max_violation_against_assigned_direction": round_float(max_violation, 12),
        "net_delta_min": round_float(min(net_deltas) if net_deltas else 0.0, 12),
        "net_delta_max": round_float(max(net_deltas) if net_deltas else 0.0, 12),
        "worst_case": {
            "state_index": int(worst_case["state_index"]) if worst_case else None,
            "step": int(worst_case["step"]) if worst_case else None,
            "delta": round_float(worst_case["delta"], 12) if worst_case else 0.0,
            "violation": round_float(worst_case["violation"], 12) if worst_case else 0.0,
        },
    }


def l1_census(states: list[np.ndarray], fixed_points: dict[int, np.ndarray]) -> dict[str, Any]:
    rows = []
    for ti in range(8):
        trajectories = [terrain_flow(ti, state.copy()) for state in states]
        metrics = metric_functions(fixed_points, ti)
        coordinate_results = {}
        for name, metric in metrics.items():
            seqs = [[metric(rho) for rho in traj] for traj in trajectories]
            coordinate_results[name] = monotonicity_class(seqs)
        rows.append(
            {
                "terrain": ti,
                "label": TERRAIN_LABELS[ti],
                "kind": TERR[ti][1],
                "eps": TERR[ti][0],
                "pole": TERR[ti][2],
                "native_ops": list(NATIVE[ti]),
                "pointer_axis": pointer_axis_for_terrain(ti),
                "coordinates": coordinate_results,
                "pawl_signature": [
                    name
                    for name, result in coordinate_results.items()
                    if result["pawl"] and result["classification"] != "constant"
                ],
            }
        )
    return {"level": "L1_per_terrain_5_coordinate_census", "rows": rows}


def l2_signatures(l1: dict[str, Any]) -> dict[str, Any]:
    rows = l1["rows"]
    coordinate_names = list(rows[0]["coordinates"].keys())
    universal_pawls = [
        name
        for name in coordinate_names
        if all(row["coordinates"][name]["pawl"] and row["coordinates"][name]["classification"] != "constant" for row in rows)
    ]
    signatures = {
        str(row["terrain"]): {
            "label": row["label"],
            "signature": row["pawl_signature"],
            "coordinate_classes": {
                name: row["coordinates"][name]["classification"] for name in coordinate_names
            },
        }
        for row in rows
    }
    unique_universal = universal_pawls == ["U_relative_to_fixed_point"]
    return {
        "level": "L2_forced_vs_installed_pawl_side",
        "universal_pawls": universal_pawls,
        "U_unique_universal_pawl": bool(unique_universal),
        "forced_coordinate_verdict": (
            "FORCED: shared ratchet coordinate is distinguishability from terrain fixed point"
            if unique_universal
            else "NOT_UNIQUE_OR_U_FAILED: do not claim unique universal U forcing"
        ),
        "terrain_entropy_kind_signatures": signatures,
    }


def l3_floor_probe(states: list[np.ndarray], fixed_points: dict[int, np.ndarray]) -> dict[str, Any]:
    rows = []
    for ti in range(8):
        u_metric = lambda rho, ti=ti: relative_entropy(rho, fixed_points[ti])
        preserving_pairs = []
        for pair in OPERATOR_PAIRS:
            trajectories = [terrain_pair_composed_flow(ti, pair, state.copy()) for state in states]
            seqs = [[u_metric(rho) for rho in traj] for traj in trajectories]
            mono = monotonicity_class(seqs)
            preserves = mono["classification"] == "monotone-decreasing"
            if preserves:
                preserving_pairs.append(pair)
            rows.append(
                {
                    "terrain": ti,
                    "label": TERRAIN_LABELS[ti],
                    "pair": list(pair),
                    "pair_family": pair_family(pair),
                    "native_pair": tuple(pair) == tuple(NATIVE[ti]),
                    "U_classification_under_tick_composition": mono["classification"],
                    "preserves_U_pawl": bool(preserves),
                    "max_violation": mono["max_violation_against_assigned_direction"],
                    "worst_case": mono["worst_case"],
                }
            )
        native_pair = tuple(NATIVE[ti])
        native_only = preserving_pairs == [native_pair]
        if native_only:
            verdict = "FORCED_native_pair_only"
        elif len(preserving_pairs) == 0:
            verdict = "BREAKS_all_pairs"
        elif native_pair in preserving_pairs:
            verdict = "INSTALLED_multiple_pairs_preserve"
        else:
            verdict = "NON_NATIVE_ONLY_native_breaks"
        for row in rows:
            if row["terrain"] == ti:
                row["terrain_preserving_pairs"] = [list(pair) for pair in preserving_pairs]
                row["terrain_pair_assignment_verdict"] = verdict
    terrain_verdicts = {
        str(ti): next(row["terrain_pair_assignment_verdict"] for row in rows if row["terrain"] == ti)
        for ti in range(8)
    }
    return {
        "level": "L3_floor_probe_operator_pair_preservation",
        "pair_interpretation": "all six unordered pairs among Ti,Te,Fi,Fe; four are dissipative+unitary, two are same-family controls",
        "composition_order": "per tick: terrain micro-flow segment, then pair[0], then pair[1]",
        "rows_48": rows,
        "terrain_verdicts": terrain_verdicts,
    }


def wrong_fixed_point_control(states: list[np.ndarray], fixed_points: dict[int, np.ndarray]) -> dict[str, Any]:
    rows = []
    lost = 0
    for ti in range(8):
        foreign = (ti + 1) % 8
        metric = lambda rho, foreign=foreign: relative_entropy(rho, fixed_points[foreign])
        trajectories = [terrain_flow(ti, state.copy()) for state in states]
        seqs = [[metric(rho) for rho in traj] for traj in trajectories]
        mono = monotonicity_class(seqs)
        loses = mono["classification"] != "monotone-decreasing"
        lost += int(loses)
        rows.append(
            {
                "terrain": ti,
                "foreign_fixed_point_terrain": foreign,
                "classification": mono["classification"],
                "lost_monotonicity": bool(loses),
                "max_violation": mono["max_violation_against_assigned_direction"],
            }
        )
    return {
        "control": "wrong_fixed_point_U_against_foreign_terrain_fixed_point",
        "lost_count": lost,
        "rows": rows,
        "passes_expected_loss": bool(lost >= 1),
    }


def shuffled_pointer_basis_control(states: list[np.ndarray]) -> dict[str, Any]:
    rows = []
    lost = 0
    for ti in range(8):
        native_axis = pointer_axis_for_terrain(ti)
        foreign_axis = foreign_pointer_axis(native_axis)
        projectors = projectors_for_axis(foreign_axis)
        metric = lambda rho, projectors=projectors: coherence_in_basis(rho, projectors)
        trajectories = [terrain_flow(ti, state.copy()) for state in states]
        seqs = [[metric(rho) for rho in traj] for traj in trajectories]
        mono = monotonicity_class(seqs)
        loses = mono["classification"] == "non-monotone"
        lost += int(loses)
        rows.append(
            {
                "terrain": ti,
                "native_pointer_axis": native_axis,
                "shuffled_pointer_axis": foreign_axis,
                "classification": mono["classification"],
                "non_monotone_under_shuffle": bool(loses),
                "max_violation": mono["max_violation_against_assigned_direction"],
            }
        )
    return {
        "control": "shuffled_pointer_basis_for_coherence",
        "non_monotone_count": lost,
        "rows": rows,
        "passes_expected_loss": bool(lost >= 1),
    }


def unitary_flow_control(states: list[np.ndarray], fixed_points: dict[int, np.ndarray]) -> dict[str, Any]:
    rows = []
    any_nonconstant_pawl = False
    for ti in range(8):
        trajectories = [unitary_only_flow(ti, state.copy()) for state in states[:80]]
        metrics = metric_functions(fixed_points, ti)
        coords = {}
        for name, metric in metrics.items():
            seqs = [[metric(rho) for rho in traj] for traj in trajectories]
            mono = monotonicity_class(seqs)
            coords[name] = mono["classification"]
            any_nonconstant_pawl = any_nonconstant_pawl or (
                mono["pawl"] and mono["classification"] != "constant"
            )
        rows.append({"terrain": ti, "coordinate_classes": coords})
    return {
        "control": "unitary_only_no_dissipation",
        "rows": rows,
        "no_nonconstant_pawls": not any_nonconstant_pawl,
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    states = seeded_state_grid(rng)
    fixed_points = {ti: long_fixed_point(ti) for ti in range(8)}
    l1 = l1_census(states, fixed_points)
    l2 = l2_signatures(l1)
    l3 = l3_floor_probe(states, fixed_points)
    controls = {
        "wrong_fixed_point_control": wrong_fixed_point_control(states, fixed_points),
        "shuffled_pointer_basis_control": shuffled_pointer_basis_control(states),
        "unitary_flow_control": unitary_flow_control(states, fixed_points),
    }
    all_u_pawls = all(
        row["coordinates"]["U_relative_to_fixed_point"]["classification"] == "monotone-decreasing"
        for row in l1["rows"]
    )
    verdict = {
        "exit_policy": "always_exit_0_for_honest_verdict_mix",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "state_grid_size": len(states),
        "noise_threshold": NOISE_THRESHOLD,
        "all_U_monotone_decreasing": bool(all_u_pawls),
        "U_unique_universal_pawl": l2["U_unique_universal_pawl"],
        "wrong_fixed_point_control_passes": controls["wrong_fixed_point_control"]["passes_expected_loss"],
        "shuffled_pointer_basis_control_passes": controls["shuffled_pointer_basis_control"]["passes_expected_loss"],
        "unitary_flow_control_passes": controls["unitary_flow_control"]["no_nonconstant_pawls"],
        "L3_summary": l3["terrain_verdicts"],
    }
    return {
        "sim_id": SIM_ID,
        "name": "per-terrain Lyapunov census for forced pawl coordinates",
        "version": "1.0",
        "seed": SEED,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "structural_tokens_only": structural_tokens_only,
        "claim_ceiling": "scratch_diagnostic; runs/pass-local-rerun only; no canonical, bridge, axis, manifold-completion, or admission claim",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "licensed_coordinates": [
            "S_von_Neumann",
            "U_relative_to_fixed_point",
            "C_pointer_coherence",
            "bloch_radius_r",
            "purity_tr_rho2",
        ],
        "source_spine": [
            "system_v7/constraint_core/sims_and_scripts/terrain_entropy_kind_ratchet_sim.py",
            "system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md",
            "system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md",
            "system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md",
        ],
        "run_parameters": {
            "state_grid_size": len(states),
            "flow_segments": FLOW_SEGMENTS,
            "steps_per_segment": STEPS_PER_SEGMENT,
            "flow_t": FLOW_T,
            "noise_threshold": NOISE_THRESHOLD,
            "l3_segments": L3_SEGMENTS,
        },
        "fixed_points_bloch": {
            str(ti): [round_float(x, 12) for x in bloch(fixed_points[ti])] for ti in range(8)
        },
        "L1_per_terrain_census": l1,
        "L2_forced_vs_installed": l2,
        "L3_floor_probe": l3,
        "controls": controls,
        "verdict": verdict,
    }


def print_l1_table(l1: dict[str, Any]) -> None:
    print("L1 8x5 LYAPUNOV CENSUS")
    print("threshold=%.1e; class entries show max assigned-direction violation" % NOISE_THRESHOLD)
    print("terrain kind ptr | S | U | C_ptr | r | purity | signature")
    for row in l1["rows"]:
        coords = row["coordinates"]

        def cell(name: str) -> str:
            data = coords[name]
            cls = data["classification"].replace("monotone-", "")
            return f"{cls}:{data['max_violation_against_assigned_direction']:.1e}"

        print(
            f"t{row['terrain']} {row['kind']:5s} {row['pointer_axis']:>2s} | "
            f"{cell('S_von_Neumann'):<22s} | "
            f"{cell('U_relative_to_fixed_point'):<22s} | "
            f"{cell('C_pointer_coherence'):<22s} | "
            f"{cell('bloch_radius_r'):<22s} | "
            f"{cell('purity_tr_rho2'):<22s} | "
            f"{','.join(row['pawl_signature']) or 'none'}"
        )


def print_l2(l2: dict[str, Any]) -> None:
    print("\nL2 FORCED VS INSTALLED")
    print(f"universal_pawls={l2['universal_pawls']}")
    print(f"U_unique_universal_pawl={l2['U_unique_universal_pawl']}")
    print(l2["forced_coordinate_verdict"])
    print("terrain signatures:")
    for terrain, data in l2["terrain_entropy_kind_signatures"].items():
        print(f"  t{terrain} {data['label']}: {','.join(data['signature']) or 'none'}")


def print_l3(l3: dict[str, Any]) -> None:
    print("\nL3 FLOOR PROBE: OPERATOR-PAIR U-PAWL PRESERVATION")
    print(l3["pair_interpretation"])
    print("terrain pair family native preserves max_violation verdict")
    for row in l3["rows_48"]:
        pair = "".join(row["pair"])
        native = "Y" if row["native_pair"] else "N"
        preserves = "Y" if row["preserves_U_pawl"] else "N"
        print(
            f"t{row['terrain']} {pair:<4s} {row['pair_family']:<31s} "
            f"native={native} preserves={preserves} "
            f"viol={row['max_violation']:.1e} {row['terrain_pair_assignment_verdict']}"
        )


def print_controls(result: dict[str, Any]) -> None:
    controls = result["controls"]
    print("\nCONTROLS")
    wrong = controls["wrong_fixed_point_control"]
    shuf = controls["shuffled_pointer_basis_control"]
    unitary = controls["unitary_flow_control"]
    print(
        "wrong-fixed-point: "
        f"lost_count={wrong['lost_count']}/8 passes_expected_loss={wrong['passes_expected_loss']}"
    )
    print(
        "shuffled-pointer-basis: "
        f"non_monotone_count={shuf['non_monotone_count']}/8 passes_expected_loss={shuf['passes_expected_loss']}"
    )
    print(f"unitary-flow: no_nonconstant_pawls={unitary['no_nonconstant_pawls']}")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("PER-TERRAIN LYAPUNOV PAWL CENSUS")
    print("classification=scratch_diagnostic promotion_allowed=false formal_admission_allowed=false")
    print("seed=0 structural_tokens_only=true")
    print("licensed coordinates: S, U=S(rho||fixed point), C_pointer, Bloch radius r, purity tr(rho^2)\n")
    print_l1_table(result["L1_per_terrain_census"])
    print_l2(result["L2_forced_vs_installed"])
    print_l3(result["L3_floor_probe"])
    print_controls(result)
    print("\nVERDICT")
    for key, value in result["verdict"].items():
        print(f"{key}: {value}")
    print(f"ALL_GATES: HONEST_MIX_EXIT_0 -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
