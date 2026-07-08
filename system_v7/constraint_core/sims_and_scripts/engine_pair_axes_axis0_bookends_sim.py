#!/usr/bin/env python3
"""engine_pair_axes_axis0_bookends_sim.

Scratch diagnostic for the engine pair (Type1 + Type2, both loops each) with
Axis-0 read as two distinct bookend objects:

* a0_front: measured before dynamics as the initial entropy-gradient polarity
  between a growth-polarity state and a record/lock-polarity state.
* a0_late: measured after dynamics as the cut-dependent Phi_0-style signed
  readout, using the UP-94 signed-volume witness machinery.

The middle readout reuses UP-94's per-axis witness + erasure controls for axes
1-6, lifted to a pair-level readout. This is a scratch_diagnostic only:
promotion_allowed=false, no bridge/Axis-0 closure claim, no component fusion.
If A0_raw appears, it remains an unfused list of the front and late objects.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm


HERE = Path(__file__).resolve().parent
STAGE_JOIN_PATH = HERE / "stage_token_join.json"
SOURCE_SLOTS_PATH = (
    HERE.parent / "reference_docs" / "engine_math" / "source_schedule_tables" / "engine_16_source_stage_slots.json"
)
RESULT_PATH = Path(__file__).with_name(Path(__file__).stem + "_results.json")

SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
G = 0.35
KAP = 1.0
Q = 1 - np.exp(-1)
TH = np.pi / 4
NS = 180
H0 = (SX + SY + SZ) / np.sqrt(3)

LOOP_ORDER = {
    "Type1_left": ["outer_deductive", "inner_inductive"],
    "Type2_right": ["outer_inductive", "inner_deductive"],
}


def _json_load(path: Path) -> Any:
    return json.loads(path.read_text())


def load_schedule() -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    stage_join = _json_load(STAGE_JOIN_PATH)
    source_slots = _json_load(SOURCE_SLOTS_PATH)
    join_by_slot = {row["source_slot_id"]: row for row in stage_join["stage_join"]}
    terrain_by_name = {
        row["terrain_name"]: row["terrain_index"] for row in stage_join["terrain_index_map"]
    }

    schedule: dict[str, list[dict[str, Any]]] = {"Type1_left": [], "Type2_right": []}
    for source in source_slots:
        joined = join_by_slot[source["slot_id"]]
        terrain_index = terrain_by_name[source["terrain"]]
        slot = {
            "slot_id": source["slot_id"],
            "engine": source["engine"],
            "loop": source["loop"],
            "step": int(source["step"]),
            "terrain": source["terrain"],
            "terrain_index": terrain_index,
            "operator": source["canonical_operator"],
            "axis6_sign": source["axis6_sign"],
            "canonical_token": source["canonical_token"],
            "joined_token": joined["canonical_token"],
            "source_line_range": joined["source_line_range"],
        }
        if slot["canonical_token"] != slot["joined_token"]:
            raise ValueError(f"schedule token mismatch at {slot['slot_id']}")
        schedule[source["engine"]].append(slot)

    for engine, loops in LOOP_ORDER.items():
        schedule[engine].sort(key=lambda row: (loops.index(row["loop"]), row["step"]))
        if len(schedule[engine]) != 8:
            raise ValueError(f"{engine} schedule has {len(schedule[engine])} slots, expected 8")

    schedule_meta = {
        "stage_token_join": str(STAGE_JOIN_PATH.relative_to(HERE.parents[2])),
        "source_slots": str(SOURCE_SLOTS_PATH.relative_to(HERE.parents[2])),
        "slot_ids_in_run_order": {
            engine: [row["slot_id"] for row in rows] for engine, rows in schedule.items()
        },
        "canonical_tokens_in_run_order": {
            engine: [row["canonical_token"] for row in rows] for engine, rows in schedule.items()
        },
    }
    return schedule, schedule_meta


def terrain_tuple(terrain_index: int) -> tuple[int, str, int]:
    terr = {
        0: (+1, "damp", +1),
        1: (+1, "depol", 0),
        2: (+1, "damp", -1),
        3: (+1, "proj", 0),
        4: (-1, "damp", -1),
        5: (-1, "depol", 0),
        6: (-1, "damp", +1),
        7: (-1, "proj", 0),
    }
    return terr[terrain_index]


def dop(lindblad_op: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return (
        lindblad_op @ rho @ lindblad_op.conj().T
        - 0.5 * (lindblad_op.conj().T @ lindblad_op @ rho + rho @ lindblad_op.conj().T @ lindblad_op)
    )


def dm(vec: np.ndarray | list[float]) -> np.ndarray:
    v = np.array(vec, float)
    return 0.5 * (I2 + v[0] * SX + v[1] * SY + v[2] * SZ)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([np.trace(rho @ s).real for s in (SX, SY, SZ)])


def entropy(rho: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh(rho)
    eigs = eigs[eigs > 1e-12]
    return float(-(eigs * np.log2(eigs)).sum())


def lindblad_ops(kind: str, pole: int) -> list[np.ndarray]:
    if kind == "damp":
        return [SP if pole > 0 else SM]
    if kind == "depol":
        return [SX / np.sqrt(2), SY / np.sqrt(2)]
    return [SZ]


def flow(
    hamiltonian: np.ndarray,
    lindblads: list[np.ndarray],
    rho: np.ndarray,
    *,
    t: float = 1.0,
    steps: int = NS,
    coherent_flow: bool = True,
) -> np.ndarray:
    dt = t / steps

    def x_dot(state: np.ndarray) -> np.ndarray:
        out = (-1j * G * (hamiltonian @ state - state @ hamiltonian)) if coherent_flow else 0 * state
        for lindblad_op in lindblads:
            out = out + KAP * dop(lindblad_op, state)
        return out

    state = rho.copy()
    for _ in range(steps):
        k1 = x_dot(state)
        k2 = x_dot(state + 0.5 * dt * k1)
        k3 = x_dot(state + 0.5 * dt * k2)
        k4 = x_dot(state + dt * k3)
        state = state + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
        state = 0.5 * (state + state.conj().T)
        state /= np.trace(state).real
    return state


def terrain_flow(terrain_index: int, rho: np.ndarray, *, coherent_flow: bool = True) -> np.ndarray:
    eps, kind, pole = terrain_tuple(terrain_index)
    return flow(eps * H0, lindblad_ops(kind, pole), rho, coherent_flow=coherent_flow)


def op(name: str, theta: float = TH):
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
    if name == "Ti":
        return lambda rho: (1 - Q) * rho + Q * (p0 @ rho @ p0 + p1 @ rho @ p1)
    if name == "Te":
        return lambda rho: (1 - Q) * rho + Q * (qp @ rho @ qp + qm @ rho @ qm)
    if name == "Fi":
        u = expm(-1j * theta / 2 * SX)
        return lambda rho: u @ rho @ u.conj().T
    if name == "Fe":
        u = expm(-1j * theta / 2 * SZ)
        return lambda rho: u @ rho @ u.conj().T
    raise ValueError(f"unknown operator {name}")


def step(slot: dict[str, Any], rho: np.ndarray, *, coherent_flow: bool = True) -> np.ndarray:
    terrain_index = int(slot["terrain_index"])
    operator = op(slot["operator"])
    if slot["axis6_sign"] == "up":
        return terrain_flow(terrain_index, operator(rho.copy()), coherent_flow=coherent_flow)
    return operator(terrain_flow(terrain_index, rho.copy(), coherent_flow=coherent_flow))


def run_engine(
    slots: list[dict[str, Any]], initial_vec: np.ndarray | list[float], *, coherent_flow: bool = True
) -> tuple[np.ndarray, np.ndarray]:
    rho = dm(initial_vec)
    trace = [bloch(rho).copy()]
    for slot in slots:
        rho = step(slot, rho, coherent_flow=coherent_flow)
        trace.append(bloch(rho).copy())
    return rho, np.array(trace)


def signed_volume(trace: np.ndarray) -> float:
    return float(
        sum(np.dot(trace[i], np.cross(trace[i + 1], trace[i + 2])) for i in range(len(trace) - 2))
    )


def state_pair(magnitude: float, sign: int = 1) -> tuple[np.ndarray, np.ndarray]:
    direction = np.array([0.35, -0.22, 0.91], float)
    direction /= np.linalg.norm(direction)
    growth_mag = magnitude
    record_mag = min(0.93, magnitude + 0.42)
    growth = sign * growth_mag * direction
    record = -sign * record_mag * direction
    return growth, record


def front_gradient(growth_vec: np.ndarray, record_vec: np.ndarray, orientation: int = 1) -> float:
    return float(orientation * (entropy(dm(growth_vec)) - entropy(dm(record_vec))))


def axis0_bookends(schedule: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    magnitudes = np.linspace(0.16, 0.40, 9)
    rows = []
    for idx, mag in enumerate(magnitudes):
        growth, record = state_pair(float(mag), sign=1 if idx % 2 == 0 else -1)
        front = front_gradient(growth, record)
        _, t1_trace = run_engine(schedule["Type1_left"], growth)
        _, t2_trace = run_engine(schedule["Type2_right"], record)
        t1_sv = signed_volume(t1_trace)
        t2_sv = signed_volume(t2_trace)
        late = float(t1_sv - t2_sv)
        rows.append(
            {
                "sample": idx,
                "growth_entropy": entropy(dm(growth)),
                "record_entropy": entropy(dm(record)),
                "a0_front": front,
                "type1_late_sv": t1_sv,
                "type2_late_sv": t2_sv,
                "a0_late": late,
            }
        )

    front_values = np.array([row["a0_front"] for row in rows], float)
    late_values = np.array([row["a0_late"] for row in rows], float)
    corr = float(np.corrcoef(front_values, late_values)[0, 1])
    measurable = bool(np.all(np.isfinite(front_values)) and np.all(np.isfinite(late_values)))
    distinct = bool(abs(corr) < 0.98 or abs(np.std(front_values) - np.std(late_values)) > 1e-3)

    no_g1 = no_g2 = np.array([0.28, 0.0, 0.0], float)
    no_front = front_gradient(no_g1, no_g2)
    _, no_t1 = run_engine(schedule["Type1_left"], no_g1)
    _, no_t2 = run_engine(schedule["Type2_right"], no_g2)
    no_late = float(signed_volume(no_t1) - signed_volume(no_t2))
    nominal_late = float(np.mean(np.abs(late_values)))
    flattened = bool(abs(no_front) < 1e-9 and abs(no_late) < 0.75 * nominal_late)

    growth, record = state_pair(0.28, sign=1)
    flipped_front = front_gradient(record, growth)
    sign_flips = bool(np.sign(flipped_front) == -np.sign(front_gradient(growth, record)))

    verdict = "not-measurable"
    if measurable and distinct:
        verdict = "distinct"
    elif measurable:
        verdict = "conflated"

    return {
        "installed_interpretation": (
            "Sections 37-38 specify full shell/bridge carriers and controls but do not determine a PEPS3D/Xi "
            "implementation inside this small engine-pair script. Installed reading: growth-polarity is represented "
            "by the higher-entropy initial density state, record/lock polarity by the lower-entropy initial density "
            "state, and a0_front is the signed entropy gradient S(growth)-S(record) measured before dynamics. "
            "The late object is the UP-94 signed-volume readout after the pair dynamics."
        ),
        "sample_table": [
            {
                "sample": row["sample"],
                "a0_front": round(row["a0_front"], 8),
                "a0_late": round(row["a0_late"], 8),
                "growth_entropy": round(row["growth_entropy"], 8),
                "record_entropy": round(row["record_entropy"], 8),
            }
            for row in rows
        ],
        "a0_front": {
            "mean": round(float(np.mean(front_values)), 8),
            "std": round(float(np.std(front_values)), 8),
            "values": [round(float(v), 8) for v in front_values],
        },
        "a0_late": {
            "mean": round(float(np.mean(late_values)), 8),
            "std": round(float(np.std(late_values)), 8),
            "values": [round(float(v), 8) for v in late_values],
        },
        "front_late_correlation": round(corr, 8),
        "measurable": measurable,
        "verdict": verdict,
        "controls": {
            "no_gradient_initialization": {
                "a0_front": round(no_front, 12),
                "a0_late": round(no_late, 8),
                "nominal_abs_late_mean": round(nominal_late, 8),
                "kills_front_drive_polarity": bool(abs(no_front) < 1e-9),
                "flattens_downstream_polarity_separation": flattened,
            },
            "gradient_sign_flip": {
                "nominal_front": round(front_gradient(growth, record), 8),
                "flipped_front": round(flipped_front, 8),
                "flips_front_sign": sign_flips,
            },
        },
        "controls_flip": bool(flattened and sign_flips),
    }


def psi(phi: float, chi: float, eta: float) -> np.ndarray:
    return np.array([np.cos(eta) * np.exp(1j * phi), np.sin(eta) * np.exp(1j * chi)], complex)


def rho_of(state: np.ndarray) -> np.ndarray:
    p = state / np.linalg.norm(state)
    return np.outer(p, p.conj())


PROBE = dm([0.55, 0.35, 0.25])


def axis1_pair() -> dict[str, Any]:
    pure_left = rho_of(psi(0.4, 0.3, 0.6))
    pure_right = rho_of(psi(0.2, 0.8, 0.45))

    def one(pure: np.ndarray, damp_op: np.ndarray) -> tuple[float, float, float]:
        unitary = expm(-1j * 0.7 * H0) @ pure @ expm(1j * 0.7 * H0)
        cptp = flow(H0, [damp_op], pure)
        erased = flow(H0, [], pure)
        return (
            abs(entropy(unitary) - entropy(pure)),
            abs(entropy(cptp) - entropy(pure)),
            abs(entropy(erased) - entropy(pure)),
        )

    vals = np.array([one(pure_left, SP), one(pure_right, SM)])
    unitary_dS, cptp_dS, erased_dS = vals.mean(axis=0)
    return {
        "witness": {"unitary_dS": round(float(unitary_dS), 8), "cptp_dS": round(float(cptp_dS), 8)},
        "erasure_control": {"drop_dissipator_dS": round(float(erased_dS), 8)},
        "collapse_only_axis": bool(unitary_dS < 1e-8 and cptp_dS > 0.01 and erased_dS < 1e-6),
        "load_bearing": bool(unitary_dS < 1e-8 and cptp_dS > 0.01 and erased_dS < 1e-6),
    }


def axis2_pair() -> dict[str, Any]:
    probes = [PROBE, dm([-0.40, 0.22, -0.35])]

    def frame(rho: np.ndarray, conj: bool, erase: bool = False) -> np.ndarray:
        v = expm(-1j * 0.6 * SY) if (conj and not erase) else I2
        state = rho.copy()
        if conj:
            state = v.conj().T @ state @ v
        state = flow(H0, [SX / np.sqrt(2), SY / np.sqrt(2)], state)
        if conj:
            state = v @ state @ v.conj().T
        return bloch(state)

    direct = np.concatenate([frame(p, False) for p in probes])
    conj = np.concatenate([frame(p, True) for p in probes])
    erased = np.concatenate([frame(p, True, erase=True) for p in probes])
    sep = float(np.linalg.norm(direct - conj))
    erased_sep = float(np.linalg.norm(direct - erased))
    return {
        "witness": {"pair_direct_vs_conjugated": round(sep, 8)},
        "erasure_control": {"set_frame_V_to_I_gap": round(erased_sep, 10)},
        "collapse_only_axis": bool(sep > 0.02 and erased_sep < 1e-8),
        "load_bearing": bool(sep > 0.02 and erased_sep < 1e-8),
    }


def axis3_pair() -> dict[str, Any]:
    def motions(eta: float, phi0: float, chi0: float) -> tuple[float, float]:
        us = np.linspace(0, 2 * np.pi, 48)
        fiber = [bloch(rho_of(psi(phi0 + u, chi0, eta))) for u in us]
        base = [bloch(rho_of(psi(phi0 - np.cos(2 * eta) * u, chi0 + u, eta))) for u in us]
        fm = float(np.mean([np.linalg.norm(fiber[i + 1] - fiber[i]) for i in range(len(fiber) - 1)]))
        bm = float(np.mean([np.linalg.norm(base[i + 1] - base[i]) for i in range(len(base) - 1)]))
        return fm, bm

    real = np.array([motions(0.60, 0.4, 0.3), motions(0.52, 0.2, 0.8)])
    erased = np.array([motions(np.pi / 4, 0.4, 0.3), motions(np.pi / 4, 0.2, 0.8)])
    gap = float(np.mean(real[:, 1] - real[:, 0]))
    erased_gap = float(np.mean(erased[:, 1] - erased[:, 0]))
    return {
        "witness": {"pair_loop_class_gap": round(gap, 8)},
        "erasure_control": {"degenerate_eta_gap": round(erased_gap, 8)},
        "collapse_only_axis": bool(gap > 0.02 and abs(erased_gap) < 0.01),
        "load_bearing": bool(gap > 0.02 and abs(erased_gap) < 0.01),
    }


def axis4_pair() -> dict[str, Any]:
    probes = [PROBE, dm([-0.40, 0.22, -0.35])]

    def gap(rho: np.ndarray, erase: bool = False) -> float:
        if erase:
            uz = expm(-1j * TH / 2 * SZ)
            evolve = lambda r: flow(SZ, [SZ], r)
            rotate = lambda r: uz @ r @ uz.conj().T
        else:
            evolve = lambda r: flow(H0, [SP], r)
            rotate = op("Fi")
        direct = rotate(evolve(rotate(evolve(rho.copy()))))
        inverse = evolve(rotate(evolve(rotate(rho.copy()))))
        return float(np.linalg.norm(bloch(direct) - bloch(inverse), 1))

    real_gap = float(np.mean([gap(p) for p in probes]))
    erased_gap = float(np.mean([gap(p, erase=True) for p in probes]))
    return {
        "witness": {"pair_order_gap_D_vs_I": round(real_gap, 8)},
        "erasure_control": {"commuting_generators_gap": round(erased_gap, 10)},
        "collapse_only_axis": bool(real_gap > 0.05 and erased_gap < 0.01),
        "load_bearing": bool(real_gap > 0.05 and erased_gap < 0.01),
    }


def axis5_pair() -> dict[str, Any]:
    left = terrain_flow(0, PROBE.copy())
    right = terrain_flow(4, dm([-0.40, 0.22, -0.35]))
    f_vals = [abs(entropy(op("Fi")(left)) - entropy(left)), abs(entropy(op("Fe")(right)) - entropy(right))]
    t_vals = [abs(entropy(op("Ti")(left)) - entropy(left)), abs(entropy(op("Te")(right)) - entropy(right))]
    f_ds = float(np.mean(f_vals))
    t_ds = float(np.mean(t_vals))
    erased_ds = t_ds
    return {
        "witness": {"F_rotation_dS": round(f_ds, 10), "T_pinch_dS": round(t_ds, 8)},
        "erasure_control": {"replace_F_with_pinch_dS": round(erased_ds, 8)},
        "collapse_only_axis": bool(f_ds < 0.005 and t_ds > 0.01 and erased_ds > 0.01),
        "load_bearing": bool(f_ds < 0.005 and t_ds > 0.01 and erased_ds > 0.01),
    }


def axis6_pair(schedule: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    probes = {"Type1_left": PROBE, "Type2_right": dm([-0.40, 0.22, -0.35])}

    def precedence_gap(slot: dict[str, Any], rho: np.ndarray, operator_name: str | None = None) -> float:
        if operator_name == "I":
            operator = lambda state: state
        else:
            operator = op(operator_name or slot["operator"])
        terrain_index = int(slot["terrain_index"])
        up = terrain_flow(terrain_index, operator(rho.copy()))
        down = operator(terrain_flow(terrain_index, rho.copy()))
        return float(np.linalg.norm(bloch(up) - bloch(down)))

    real_gaps = []
    erased_gaps = []
    for engine, slots in schedule.items():
        rho = probes[engine]
        for slot in slots:
            real_gaps.append(precedence_gap(slot, rho))
            erased_gaps.append(precedence_gap(slot, rho, operator_name="I"))
    real = float(np.mean(real_gaps))
    erased = float(np.mean(erased_gaps))
    return {
        "witness": {"pair_precedence_gap": round(real, 8)},
        "erasure_control": {"identity_operator_order_gap": round(erased, 10)},
        "collapse_only_axis": bool(real > 0.03 and erased < 0.75 * real),
        "load_bearing": bool(real > 0.03 and erased < 0.75 * real),
    }


def pair_axes(schedule: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {
        "axis1": axis1_pair(),
        "axis2": axis2_pair(),
        "axis3": axis3_pair(),
        "axis4": axis4_pair(),
        "axis5": axis5_pair(),
        "axis6": axis6_pair(schedule),
    }


def run() -> dict[str, Any]:
    np.random.default_rng(0)
    schedule, schedule_meta = load_schedule()
    bookends = axis0_bookends(schedule)
    axes = pair_axes(schedule)
    axes_load_bearing = all(axis["load_bearing"] for axis in axes.values())
    bookends_gate = bool(bookends["measurable"] and bookends["controls_flip"])
    exits_zero = bool(axes_load_bearing and bookends_gate)
    result = {
        "sim_id": "engine_pair_axes_axis0_bookends_sim",
        "classification": "scratch_diagnostic",
        "promotion_status": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_execution_kind": "classical",
        "sim_class": "engine_pair_axis_bookend_probe",
        "source_sections": [
            "system_v7/constraint_core/sims_and_scripts/unified_attractor_basin_seven_axes_sim.py:UP-94 per-axis witness and erasure machinery",
            "CLAUDE.md:BINDING STATE 2026-07-04 lines 7-14 Axis-0 front/late doctrine and A0_raw list rule",
            "system_v7/constraint_core/reference_docs_from_josh/physics_program/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md:37-38 Axis0 sim requirements and controls",
            "system_v7/constraint_core/sims_and_scripts/stage_token_join.json",
            "system_v7/constraint_core/reference_docs/engine_math/source_schedule_tables/engine_16_source_stage_slots.json",
        ],
        "installed_interpretation": bookends["installed_interpretation"],
        "schedule_meta": schedule_meta,
        "bookends": {k: v for k, v in bookends.items() if k != "installed_interpretation"},
        "pair_axis_verdicts": axes,
        "all_middle_axes_load_bearing": bool(axes_load_bearing),
        "bookends_gate_passed": bool(bookends_gate),
        "honest_verdict_mix_exits_zero": exits_zero,
        "A0_raw": [
            {"object": "a0_front", "values": bookends["a0_front"]["values"]},
            {"object": "a0_late", "values": bookends["a0_late"]["values"]},
        ],
        "binding_rule_8": {
            "A0_raw_status": "unfused_list",
            "component_mixing_performed": False,
            "note": "front and late Axis-0 objects are stored as separate list entries; no vector fusion or component algebra is used.",
        },
        "TOOL_MANIFEST": {
            "numpy": "density matrices, Bloch readouts, entropy arrays, correlations",
            "scipy.linalg.expm": "unitary rotations reused from UP-94",
            "json": "source schedule loading and result emission",
        },
        "TOOL_INTEGRATION_DEPTH": "supportive",
        "allowed_claims": [
            "engine-pair scratch diagnostic runs",
            "pair-level axes 1-6 witness/erasure controls are measured in this script",
            "Axis-0 front and late bookends are reported as distinct/conflated/not-measurable without promotion",
        ],
        "blocked_consumers": [
            "canonical Axis-0",
            "bridge or Phi_0 closure",
            "nonclassical manifold promotion",
            "physics-model completion claim",
        ],
        "divergence_log": [
            "UP-94's single-engine a0 readout is not reused as the front object; it is only reused as the late signed-volume readout.",
            "Sections 37-38 full shell/PEPS3D/Xi carrier is not implemented here; this is the closest doc-faithful engine-pair proxy and records that interpretation.",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    return result


def print_report(result: dict[str, Any]) -> None:
    bookends = result["bookends"]
    print("ENGINE PAIR AXES WITH AXIS-0 BOOKENDS")
    print("classification: scratch_diagnostic")
    print("promotion_allowed: False")
    print()
    print("A0 FRONT / A0 LATE TABLE")
    print("sample | a0_front | a0_late | growth_entropy | record_entropy")
    for row in bookends["sample_table"]:
        print(
            f"{row['sample']:>6} | {row['a0_front']:>9.6f} | {row['a0_late']:>8.6f} | "
            f"{row['growth_entropy']:>14.6f} | {row['record_entropy']:>14.6f}"
        )
    print(
        "summary | "
        f"front_mean={bookends['a0_front']['mean']:.6f} front_std={bookends['a0_front']['std']:.6f} | "
        f"late_mean={bookends['a0_late']['mean']:.6f} late_std={bookends['a0_late']['std']:.6f} | "
        f"corr={bookends['front_late_correlation']:.6f} | verdict={bookends['verdict']}"
    )
    print()
    print("PER-AXIS VERDICTS (PAIR-LEVEL READOUT)")
    for axis_name, axis in result["pair_axis_verdicts"].items():
        print(
            f"{axis_name}: load_bearing={axis['load_bearing']} "
            f"collapse_only_axis={axis['collapse_only_axis']} "
            f"witness={axis['witness']} control={axis['erasure_control']}"
        )
    print()
    print("CONTROL TABLE")
    no_grad = bookends["controls"]["no_gradient_initialization"]
    flip = bookends["controls"]["gradient_sign_flip"]
    print(
        "bookend no_gradient_initialization: "
        f"a0_front={no_grad['a0_front']} a0_late={no_grad['a0_late']} "
        f"kills_front={no_grad['kills_front_drive_polarity']} "
        f"flattens_downstream={no_grad['flattens_downstream_polarity_separation']}"
    )
    print(
        "bookend gradient_sign_flip: "
        f"nominal_front={flip['nominal_front']} flipped_front={flip['flipped_front']} "
        f"flips_front_sign={flip['flips_front_sign']}"
    )
    for axis_name, axis in result["pair_axis_verdicts"].items():
        print(f"{axis_name} erasure_control: {axis['erasure_control']}")
    print()
    print(f"all_middle_axes_load_bearing: {result['all_middle_axes_load_bearing']}")
    print(f"bookends_gate_passed: {result['bookends_gate_passed']}")
    print(f"honest_verdict_mix_exits_zero: {result['honest_verdict_mix_exits_zero']}")
    print(f"RESULT_JSON: {RESULT_PATH}")


def main() -> int:
    result = run()
    print_report(result)
    return 0 if result["honest_verdict_mix_exits_zero"] else 1


if __name__ == "__main__":
    sys.exit(main())
