#!/usr/bin/env python3
"""Per-terrain entropy-kind ratchet census.

Scratch diagnostic only.  This sim keeps the owner binding as the spine:
for d=2, von Neumann entropy S(rho) is a strict monotone readout of the
Bloch radius.  Radial motion and entropy motion are therefore one coordinate
with two readings.  Every measured entropy motion is reported with its
radial/tangential geometry, and the S-vs-radius identity is checked directly
from density matrices rather than from a classical/Shannon substitute.

Licensed entropy kinds only:
  - S(rho), von Neumann entropy;
  - U(rho)=S(rho || terrain fixed point), Umegaki relative entropy;
  - C_H0(rho)=S(Delta_H0(rho))-S(rho), relative entropy of coherence in
    the H0 eigenbasis.

No promotion claim.  classification=scratch_diagnostic;
promotion_allowed=false.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy.linalg import expm


HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "terrain_entropy_kind_ratchet_sim_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "density matrices, Bloch vectors, eigenspectra, and trajectory aggregation",
    },
    "scipy.linalg.expm": {
        "used": True,
        "reason": "unitary operator maps and reversible unitary flip control",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy.linalg.expm": "supportive",
}

SEED = 0
TOL = 1e-8
G = 0.35
KAP = 1.0
Q = 1.0 - float(np.exp(-1.0))
TH = np.pi / 4.0
FLOW_SEGMENTS = 16
STEPS_PER_SEGMENT = 14
FLOW_T = 2.4

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
H0 = (SX + SY + SZ) / np.sqrt(3.0)

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

OPS = ("Ti", "Te", "Fi", "Fe")
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


H0_EVALS, H0_EVECS = np.linalg.eigh(H0)
H0_PROJECTORS = [np.outer(H0_EVECS[:, i], H0_EVECS[:, i].conj()) for i in range(2)]


def dephase_h0(rho: np.ndarray) -> np.ndarray:
    return normalize_rho(sum(p @ rho @ p for p in H0_PROJECTORS))


def coherence_h0(rho: np.ndarray) -> float:
    return max(vn_entropy(dephase_h0(rho)) - vn_entropy(rho), 0.0)


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


def terrain_flow(
    ti: int,
    rho: np.ndarray,
    *,
    total_t: float = FLOW_T,
    segments: int = FLOW_SEGMENTS,
    steps_per_segment: int = STEPS_PER_SEGMENT,
) -> list[np.ndarray]:
    x_dot = terrain_generator(ti)
    state = rho.copy()
    traj = [state.copy()]
    dt = total_t / float(segments * steps_per_segment)
    for _ in range(segments):
        for _ in range(steps_per_segment):
            state = rk4_step(x_dot, state, dt)
        traj.append(state.copy())
    return traj


def terrain_endpoint(ti: int, rho: np.ndarray, *, total_t: float = FLOW_T) -> np.ndarray:
    return terrain_flow(ti, rho, total_t=total_t)[-1]


def long_fixed_point(ti: int) -> np.ndarray:
    state = rho_from_bloch([0.23, -0.31, 0.41])
    for _ in range(14):
        state = terrain_endpoint(ti, state, total_t=2.0)
    return normalize_rho(state)


def operator_map(name: str) -> Callable[[np.ndarray], np.ndarray]:
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
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


def stage_trajectory(ti: int, opname: str, sign: str, rho: np.ndarray) -> list[np.ndarray]:
    op = operator_map(opname)
    if sign == "up":
        after_op = op(rho.copy())
        return terrain_flow(ti, after_op)
    if sign == "down":
        flow = terrain_flow(ti, rho.copy())
        after = op(flow[-1])
        return flow + [after]
    raise ValueError(f"unknown sign {sign!r}")


def unitary_flip_control(ti: int, rho: np.ndarray, segments: int = FLOW_SEGMENTS) -> list[np.ndarray]:
    eps, _, _ = TERR[ti]
    dt = FLOW_T / segments
    state = rho.copy()
    traj = [state.copy()]
    for idx in range(segments):
        sign = 1.0 if idx < segments // 2 else -1.0
        u = expm(-1j * sign * eps * G * dt * H0)
        state = normalize_rho(u @ state @ u.conj().T)
        traj.append(state.copy())
    return traj


def seeded_state_grid(rng: np.random.Generator) -> list[np.ndarray]:
    states: list[np.ndarray] = []
    radii = [0.0, 0.18, 0.42, 0.68, 0.91]
    directions = [
        [1, 0, 0],
        [-1, 0, 0],
        [0, 1, 0],
        [0, -1, 0],
        [0, 0, 1],
        [0, 0, -1],
        [1, 1, 1],
        [1, -1, 0.5],
    ]
    for radius in radii:
        for direction in directions:
            d = np.asarray(direction, dtype=float)
            n = np.linalg.norm(d)
            states.append(rho_from_bloch(np.zeros(3) if n == 0.0 else radius * d / n))
    for _ in range(24):
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        radius = rng.uniform(0.05, 0.95)
        states.append(rho_from_bloch(radius * d))
    return states


def metric_functions(fixed_points: dict[int, np.ndarray], ti: int) -> dict[str, Callable[[np.ndarray], float]]:
    return {
        "S": vn_entropy,
        "U_to_fixed_point": lambda rho: relative_entropy(rho, fixed_points[ti]),
        "Coh_H0": coherence_h0,
    }


def motion_word(delta: float, tol: float = 1e-7) -> str:
    if delta > tol:
        return "increase"
    if delta < -tol:
        return "decrease"
    return "hold"


def motion_set(deltas: list[float]) -> str:
    seen = {motion_word(delta) for delta in deltas}
    order = ["increase", "decrease", "hold"]
    return "+".join(word for word in order if word in seen)


def sequence_pawl(seq: list[float], tol: float = 1e-7) -> tuple[bool, float]:
    if len(seq) < 2:
        return True, 0.0
    net = seq[-1] - seq[0]
    steps = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    if net > tol:
        unwinding = max([max(0.0, -step) for step in steps] + [0.0])
    elif net < -tol:
        unwinding = max([max(0.0, step) for step in steps] + [0.0])
    else:
        unwinding = max([abs(step) for step in steps] + [0.0])
    return unwinding <= 1e-6, float(unwinding)


def geometry_summary(transitions: list[tuple[np.ndarray, np.ndarray]]) -> dict[str, Any]:
    drs = []
    tangents = []
    s_match = []
    readings: set[str] = set()
    for before, after in transitions:
        b0 = bloch(before)
        b1 = bloch(after)
        r0 = float(np.linalg.norm(b0))
        r1 = float(np.linalg.norm(b1))
        dr = r1 - r0
        chord = float(np.linalg.norm(b1 - b0))
        tangent = math.sqrt(max(chord * chord - dr * dr, 0.0))
        ds = vn_entropy(after) - vn_entropy(before)
        drs.append(dr)
        tangents.append(tangent)
        if abs(ds) <= 1e-7 and abs(dr) <= 1e-7:
            s_match.append(True)
        else:
            s_match.append(np.sign(ds) == -np.sign(dr))
        if dr > 1e-7:
            readings.add("inward_radial_purify")
        elif dr < -1e-7:
            readings.add("outward_radial_mix")
        if tangent > 1e-7:
            readings.add("tangential_transport")
        if abs(dr) <= 1e-7 and tangent <= 1e-7:
            readings.add("hold")
    ordered = ["inward_radial_purify", "outward_radial_mix", "tangential_transport", "hold"]
    return {
        "radial_delta_min": round_float(min(drs) if drs else 0.0, 9),
        "radial_delta_max": round_float(max(drs) if drs else 0.0, 9),
        "tangential_norm_max": round_float(max(tangents) if tangents else 0.0, 9),
        "geometry_reading": "+".join(x for x in ordered if x in readings),
        "s_vs_radius_transition_match_fraction": round_float(float(np.mean(s_match)) if s_match else 1.0, 6),
    }


def summarize_trajectories(
    trajectories: list[list[np.ndarray]],
    metrics: dict[str, Callable[[np.ndarray], float]],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    transitions = [(traj[0], traj[-1]) for traj in trajectories]
    geom = geometry_summary(transitions)
    for metric_name, metric in metrics.items():
        deltas = [metric(traj[-1]) - metric(traj[0]) for traj in trajectories]
        pawls = []
        unwindings = []
        for traj in trajectories:
            seq = [metric(state) for state in traj]
            pawl, unwinding = sequence_pawl(seq)
            pawls.append(pawl)
            unwindings.append(unwinding)
        out[metric_name] = {
            "motion": motion_set(deltas),
            "delta_min": round_float(min(deltas), 9),
            "delta_max": round_float(max(deltas), 9),
            "monotone_pawl": bool(all(pawls)),
            "max_unwinding": round_float(max(unwindings), 9),
            **geom,
        }
    return out


def bijection_check(states: list[np.ndarray], terrain_trajectories: list[list[np.ndarray]]) -> dict[str, Any]:
    shell_rows = []
    for radius in [0.1, 0.25, 0.5, 0.75, 0.93]:
        vals = []
        for direction in ([1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1], [1, -1, 0.5]):
            d = np.asarray(direction, dtype=float)
            vals.append(vn_entropy(rho_from_bloch(radius * d / np.linalg.norm(d))))
        shell_rows.append({"radius": radius, "S_span_same_radius": max(vals) - min(vals), "S_mean": float(np.mean(vals))})
    means = [row["S_mean"] for row in shell_rows]
    strict_decrease = all(means[i + 1] < means[i] for i in range(len(means) - 1))
    transition_matches = []
    for traj in terrain_trajectories:
        for i in range(len(traj) - 1):
            ds = vn_entropy(traj[i + 1]) - vn_entropy(traj[i])
            dr = bloch_radius(traj[i + 1]) - bloch_radius(traj[i])
            transition_matches.append((abs(ds) <= 1e-7 and abs(dr) <= 1e-7) or np.sign(ds) == -np.sign(dr))
    return {
        "d2_exact_reading": "S(rho) is numerically a strict single-valued monotone of Bloch radius on sampled qubit states",
        "same_radius_max_S_span": round_float(max(row["S_span_same_radius"] for row in shell_rows), 12),
        "strict_S_decreases_as_radius_increases": bool(strict_decrease),
        "flow_transition_match_fraction": round_float(float(np.mean(transition_matches)), 8),
        "shell_rows": [
            {
                "radius": round_float(row["radius"], 4),
                "S_mean": round_float(row["S_mean"], 10),
                "S_span_same_radius": round_float(row["S_span_same_radius"], 12),
            }
            for row in shell_rows
        ],
    }


def expected_motion(kind: str) -> str:
    if kind == "damp":
        return "S_decrease_or_mixed_surprise_descent"
    if kind == "depol":
        return "S_increase_mixer"
    if kind == "proj":
        return "population_hold_coherence_destroy"
    return "unknown"


def l1_census(states: list[np.ndarray], fixed_points: dict[int, np.ndarray]) -> tuple[dict[str, Any], list[list[np.ndarray]]]:
    rows = []
    all_terrain_trajectories: list[list[np.ndarray]] = []
    for ti in range(8):
        eps, kind, pole = TERR[ti]
        trajectories = [terrain_flow(ti, state.copy()) for state in states]
        all_terrain_trajectories.extend(trajectories)
        metrics = metric_functions(fixed_points, ti)
        summary = summarize_trajectories(trajectories, metrics)
        unitary_trajectories = [unitary_flip_control(ti, state.copy()) for state in states[:20]]
        unitary_summary = summarize_trajectories(unitary_trajectories, metrics)
        rows.append(
            {
                "terrain": ti,
                "label": TERRAIN_LABELS[ti],
                "eps": eps,
                "kind": kind,
                "pole": pole,
                "expected_structure_checked_not_assumed": expected_motion(kind),
                "native_ops": NATIVE[ti],
                "entropy_kinds": summary,
                "unitary_unwinding_control": {
                    key: {
                        "motion": val["motion"],
                        "max_unwinding": val["max_unwinding"],
                        "return_error": round_float(
                            max(np.linalg.norm(bloch(traj[-1]) - bloch(traj[0])) for traj in unitary_trajectories),
                            12,
                        ),
                    }
                    for key, val in unitary_summary.items()
                },
            }
        )
    return {"level": "L1_per_terrain_census", "rows": rows}, all_terrain_trajectories


def l2_operator_census(states: list[np.ndarray], fixed_points: dict[int, np.ndarray], l1: dict[str, Any]) -> dict[str, Any]:
    terrain_motion = {
        row["terrain"]: {kind: data["motion"] for kind, data in row["entropy_kinds"].items()}
        for row in l1["rows"]
    }
    signed_rows = []
    cell_rows = []
    for ti in range(8):
        metrics = metric_functions(fixed_points, ti)
        for opname in OPS:
            aggregate: dict[str, set[str]] = {kind: set() for kind in metrics}
            signs: dict[str, Any] = {}
            for sign in ("up", "down"):
                trajectories = [stage_trajectory(ti, opname, sign, state.copy()) for state in states]
                summary = summarize_trajectories(trajectories, metrics)
                signs[sign] = summary
                for kind, data in summary.items():
                    aggregate[kind].update(data["motion"].split("+"))
                signed_rows.append(
                    {
                        "terrain": ti,
                        "operator": opname,
                        "axis6_sign": sign,
                        "native_for_terrain": opname in NATIVE[ti],
                        "entropy_kinds": summary,
                    }
                )
            add_remove = {}
            for kind in metrics:
                base = set(terrain_motion[ti][kind].split("+"))
                cell = aggregate[kind]
                add_remove[kind] = {
                    "motion": "+".join(x for x in ["increase", "decrease", "hold"] if x in cell),
                    "adds": "+".join(x for x in ["increase", "decrease", "hold"] if x in cell - base) or "none",
                    "removes": "+".join(x for x in ["increase", "decrease", "hold"] if x in base - cell) or "none",
                    "operator_as_entropy_valve": bool(cell - base or base - cell),
                    "up_pawl": signs["up"][kind]["monotone_pawl"],
                    "down_pawl": signs["down"][kind]["monotone_pawl"],
                }
            cell_rows.append(
                {
                    "terrain": ti,
                    "operator": opname,
                    "native_for_terrain": opname in NATIVE[ti],
                    "entropy_kinds": add_remove,
                }
            )
    return {"level": "L2_per_terrain_operator_census", "cells_32": cell_rows, "signed_rows_64": signed_rows}


def shuffled_generator_control(l1: dict[str, Any]) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    perm = list(rng.permutation(8))
    expected_by_label = {idx: expected_motion(TERR[idx][1]) for idx in range(8)}
    real_matches = 0
    shuffled_matches = 0
    for row in l1["rows"]:
        terrain = row["terrain"]
        s_motion = row["entropy_kinds"]["S"]["motion"]
        expected = expected_by_label[terrain]
        if ("decrease" in s_motion and "decrease" in expected) or ("increase" in s_motion and "increase" in expected):
            real_matches += 1
    for row, fake_label in zip(l1["rows"], perm):
        s_motion = row["entropy_kinds"]["S"]["motion"]
        expected = expected_by_label[int(fake_label)]
        if ("decrease" in s_motion and "decrease" in expected) or ("increase" in s_motion and "increase" in expected):
            shuffled_matches += 1
    return {
        "control": "terrain labels scrambled over measured generator rows",
        "permutation": [int(x) for x in perm],
        "real_expected_motion_matches": int(real_matches),
        "shuffled_expected_motion_matches": int(shuffled_matches),
        "structure_destroyed": bool(shuffled_matches < real_matches),
    }


def build_result() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    states = seeded_state_grid(rng)
    fixed_points = {ti: long_fixed_point(ti) for ti in range(8)}
    l1, terrain_trajectories = l1_census(states, fixed_points)
    l2 = l2_operator_census(states, fixed_points, l1)
    checks = {
        "s_vs_bloch_radius_bijection": bijection_check(states, terrain_trajectories),
        "shuffled_generator_control": shuffled_generator_control(l1),
    }
    verdict = {
        "exit_policy": "always_exit_0_for_honest_verdict_mix",
        "promotion_allowed": False,
        "all_S_radius_checks_pass": bool(
            checks["s_vs_bloch_radius_bijection"]["same_radius_max_S_span"] < 1e-10
            and checks["s_vs_bloch_radius_bijection"]["strict_S_decreases_as_radius_increases"]
            and checks["s_vs_bloch_radius_bijection"]["flow_transition_match_fraction"] > 0.999
        ),
        "L1_rows": len(l1["rows"]),
        "L2_cells": len(l2["cells_32"]),
        "L2_signed_rows": len(l2["signed_rows_64"]),
        "L3_composition_micro_budgets": "unmeasured_in_this_run",
    }
    return {
        "sim_id": "terrain_entropy_kind_ratchet_sim",
        "name": "per-terrain entropy-kind ratchet census",
        "version": "1.0",
        "seed": SEED,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "structural_tokens_only": True,
        "claim_ceiling": "runs/pass-local-rerun only; no canonical, bridge, axis, manifold-completion, or admission claim",
        "licensed_entropy_kinds": [
            "von_Neumann_entropy_S",
            "Umegaki_relative_entropy_to_terrain_fixed_point_U",
            "relative_entropy_of_coherence_in_H0_eigenbasis",
        ],
        "source_spine": [
            "system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim.py",
            "system_v7/constraint_core/sims_and_scripts/known_unknown_fep_field_sim.py",
            "system_v7/constraint_core/sims_and_scripts/manifold_ratchet_depth_sim.py",
            "system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md",
            "system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "terrain_table": {
            str(ti): {"eps": TERR[ti][0], "kind": TERR[ti][1], "pole": TERR[ti][2], "native_ops": NATIVE[ti]}
            for ti in range(8)
        },
        "L1_per_terrain_census": l1,
        "L2_per_terrain_operator_census": l2,
        "L3_composition_micro_budgets": {
            "status": "unmeasured",
            "reason": "L1 and L2 census plus controls were completed first; no promotion depends on L3 in this additive card",
        },
        "controls_and_internal_checks": checks,
        "verdict": verdict,
    }


def print_l1_table(l1: dict[str, Any]) -> None:
    print("L1 PER-TERRAIN CENSUS")
    print("terrain kind pole | S motion pawl unwind | U motion pawl unwind | C_H0 motion pawl unwind | geometry")
    for row in l1["rows"]:
        s = row["entropy_kinds"]["S"]
        u = row["entropy_kinds"]["U_to_fixed_point"]
        c = row["entropy_kinds"]["Coh_H0"]
        print(
            f"t{row['terrain']} {row['kind']:5s} {row['pole']:>2} | "
            f"S {s['motion']:<22s} pawl={str(s['monotone_pawl']):5s} unw={s['max_unwinding']:.2e} | "
            f"U {u['motion']:<22s} pawl={str(u['monotone_pawl']):5s} unw={u['max_unwinding']:.2e} | "
            f"C {c['motion']:<22s} pawl={str(c['monotone_pawl']):5s} unw={c['max_unwinding']:.2e} | "
            f"{s['geometry_reading']} S-r={s['s_vs_radius_transition_match_fraction']:.3f}"
        )
        uc = row["unitary_unwinding_control"]
        print(
            f"    unitary flip control: S_unw={uc['S']['max_unwinding']:.2e}, "
            f"U_unw={uc['U_to_fixed_point']['max_unwinding']:.2e}, "
            f"C_unw={uc['Coh_H0']['max_unwinding']:.2e}, return_err={uc['S']['return_error']:.2e}"
        )


def print_l2_table(l2: dict[str, Any]) -> None:
    print("\nL2 32-CELL TERRAIN x OPERATOR TABLE")
    print("terrain op native | S motion add/remove pawl(up,down) | U motion add/remove | C_H0 motion add/remove")
    for row in l2["cells_32"]:
        s = row["entropy_kinds"]["S"]
        u = row["entropy_kinds"]["U_to_fixed_point"]
        c = row["entropy_kinds"]["Coh_H0"]
        native = "Y" if row["native_for_terrain"] else "N"
        print(
            f"t{row['terrain']} {row['operator']:>2s} {native} | "
            f"S {s['motion']:<22s} +{s['adds']:<13s} -{s['removes']:<13s} pawl=({s['up_pawl']},{s['down_pawl']}) | "
            f"U {u['motion']:<22s} +{u['adds']:<13s} -{u['removes']:<13s} | "
            f"C {c['motion']:<22s} +{c['adds']:<13s} -{c['removes']:<13s}"
        )


def print_controls(result: dict[str, Any]) -> None:
    checks = result["controls_and_internal_checks"]
    bij = checks["s_vs_bloch_radius_bijection"]
    shuf = checks["shuffled_generator_control"]
    print("\nCONTROLS AND IDENTITY CHECKS")
    print(
        "S-vs-r bijection: "
        f"same-radius max S span={bij['same_radius_max_S_span']:.3e}, "
        f"strict monotone={bij['strict_S_decreases_as_radius_increases']}, "
        f"flow transition match={bij['flow_transition_match_fraction']:.6f}"
    )
    print(
        "shuffled-generator control: "
        f"real_matches={shuf['real_expected_motion_matches']} "
        f"shuffled_matches={shuf['shuffled_expected_motion_matches']} "
        f"destroyed={shuf['structure_destroyed']}"
    )
    print("L3 composition micro-budgets: unmeasured in this run")


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("PER-TERRAIN ENTROPY-KIND RATCHET CENSUS")
    print("classification=scratch_diagnostic promotion_allowed=false seed=0")
    print("licensed kinds: S(rho), U(rho)=S(rho||fixed point), C_H0 relative entropy of coherence")
    print("geometry spine: d=2 S/r identity checked; radial motion and S motion are one coordinate, two readings\n")
    print_l1_table(result["L1_per_terrain_census"])
    print_l2_table(result["L2_per_terrain_operator_census"])
    print_controls(result)
    print("\nVERDICT")
    for key, value in result["verdict"].items():
        print(f"{key}: {value}")
    print(f"ALL_GATES: HONEST_MIX_EXIT_0 -> {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
