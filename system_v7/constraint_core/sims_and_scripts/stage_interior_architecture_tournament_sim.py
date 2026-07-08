#!/usr/bin/env python3
"""Stage-interior architecture tournament.

Question under test: what are a stage's execution semantics?

This is additive, standalone, and diagnostic-only. It uses one shared one-qubit
GKSL/channel machinery for all candidate architectures and reports divergence
instead of selecting a single winner.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, replace
from itertools import permutations
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from scipy.linalg import expm


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULT_PATH = HERE / "stage_interior_architecture_tournament_sim_results.json"
SLOTS_PATH = (
    ROOT
    / "system_v7"
    / "constraint_core"
    / "reference_docs"
    / "engine_math"
    / "source_schedule_tables"
    / "engine_16_source_stage_slots.json"
)

ALLOPS = ("Ti", "Te", "Fi", "Fe")
C_SWEEP = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)
T_FLOW = 1.0
G = 0.35
KAP = 1.0
Q = 1.0 - math.exp(-1.0)
TH = math.pi / 4.0
EPS = 1e-12

VERDICT_RULE = (
    "PRE-REGISTERED VERDICT RULE: ADMITTED = passes compatibility gate AND "
    "(for multi-execution architectures) all executed microsteps contribute; "
    "RANKING among admitted = report dominance profile + which reading gives "
    "the 16-chart-locked/48-runtime split natural meaning -- but RANKING IS "
    "DESCRIPTIVE, the sim never declares a single winner; multiple admitted "
    "architectures are reported as surviving candidates for the owner."
)

SOURCE_SECTIONS = [
    {
        "path": "system_v7/constraint_core/reference_docs/engine_math/ENGINE_64_SCHEDULE_ATLAS.md",
        "section": "12. INVARIANTS",
        "used_for": "8 macro-stages per engine, 32 microsteps per engine, 64 total microsteps, 16 chart-locked macro-stages.",
    },
    {
        "path": "system_v7/constraint_core/reference_docs/engine_math/ENGINE_64_SCHEDULE_ATLAS.md",
        "section": "13. HARD NON-CLAIMS",
        "used_for": "schedule/index and correlation ceilings; no ontology or full 64-state closure claim.",
    },
    {
        "path": "system_v7/constraint_core/MODEL_LAYER_LEDGER.md",
        "section": "STAGED ENGINE BUILD RUNG 1 + THE 64-SCHEDULE DEFINED",
        "used_for": "owner correction: 16 stages, each runs all 4 operators with one shared up/down axis-6 sign.",
    },
    {
        "path": "system_v7/constraint_core/reference_docs/engine_math/source_schedule_tables/engine_16_source_stage_slots.json",
        "section": "16 source stage slots",
        "used_for": "slot terrain, canonical operator, canonical token, and axis-6 sign.",
    },
    {
        "path": "system_v7/constraint_core/sims_and_scripts/type1_single_loop_axis0_sim.py",
        "section": "rung-1 anchors",
        "used_for": "four ordered stages, order sensitivity, axis-0 drive/readout and no-drive collapse measurements.",
    },
    {
        "path": "system_v7/constraint_core/sims_and_scripts/sixteen_intelligences_substages_terrain_ratchet_sim.py",
        "section": "per-substage casing conventions",
        "used_for": "operator order tokens and stage-interior four-beat conventions.",
    },
    {
        "path": "system_v4/probes/sim_lego_gksl_kossakowski.py",
        "section": "house GKSL conventions",
        "used_for": "Lindblad/GKSL channel convention and diagnostic ceiling discipline.",
    },
]

TERRAIN_INDEX = {
    "Se-in": 0,
    "Ne-in": 1,
    "Ni-in": 2,
    "Si-in": 3,
    "Se-out": 4,
    "Si-out": 5,
    "Ni-out": 6,
    "Ne-out": 7,
}

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

SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
FLOW_CACHE: Dict[int, np.ndarray] = {}


@dataclass(frozen=True)
class Slot:
    slot_id: str
    engine: str
    loop: str
    step: int
    terrain_label: str
    terrain: int
    axis6_sign: str
    canonical_operator: str
    canonical_token: str


@dataclass(frozen=True)
class Architecture:
    key: str
    family: str
    label: str
    attenuation: float | None
    output_reading: str


def load_slots() -> Tuple[List[Slot], Dict[str, object]]:
    raw = json.loads(SLOTS_PATH.read_text())
    slots: List[Slot] = []
    seen: Dict[str, int] = {}
    source_flags_present = 0
    for row in raw:
        slot_id = row["slot_id"]
        seen[slot_id] = seen.get(slot_id, 0) + 1
        if row.get("is_source_canonical") is True:
            source_flags_present += 1
        slots.append(
            Slot(
                slot_id=slot_id,
                engine=row["engine"],
                loop=row["loop"],
                step=int(row["step"]),
                terrain_label=row["terrain"],
                terrain=TERRAIN_INDEX[row["terrain"]],
                axis6_sign=row["axis6_sign"],
                canonical_operator=row["canonical_operator"],
                canonical_token=row["canonical_token"],
            )
        )
    problems = []
    if len(slots) != 16:
        problems.append(f"expected 16 slots, found {len(slots)}")
    duplicates = sorted(k for k, v in seen.items() if v != 1)
    if duplicates:
        problems.append(f"non-unique slot rows: {duplicates}")
    return slots, {
        "path": str(SLOTS_PATH.relative_to(ROOT.parent)),
        "slot_count": len(slots),
        "unique_slot_count": len(seen),
        "one_row_per_slot": len(slots) == 16 and not duplicates,
        "is_source_canonical_field_present_count": source_flags_present,
        "note": (
            "The checked JSON has one row per canonical source slot; it does "
            "not expose an is_source_canonical boolean field in this checkout."
        ),
        "problems": problems,
    }


def dop(lindblad: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return lindblad @ rho @ lindblad.conj().T - 0.5 * (
        lindblad.conj().T @ lindblad @ rho + rho @ lindblad.conj().T @ lindblad
    )


def gen(terrain: int) -> Callable[[np.ndarray], np.ndarray]:
    eps, kind, pole = TERR[terrain]
    hamiltonian = eps * (SX + SY + SZ) / math.sqrt(3.0)

    def vector_field(rho: np.ndarray) -> np.ndarray:
        out = -1j * G * (hamiltonian @ rho - rho @ hamiltonian)
        if kind == "damp":
            out = out + KAP * dop(SP if pole > 0 else SM, rho)
        elif kind == "depol":
            out = out + 0.5 * KAP * (dop(SX, rho) + dop(SY, rho))
        else:
            out = out + KAP * dop(SZ, rho)
        return out

    return vector_field


def clean_density(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    tr = float(np.trace(rho).real)
    if abs(tr) < EPS:
        raise ValueError("density trace collapsed")
    return rho / tr


def terrain_flow_matrix(terrain: int) -> np.ndarray:
    if terrain in FLOW_CACHE:
        return FLOW_CACHE[terrain]
    vector_field = gen(terrain)
    liouvillian = np.zeros((4, 4), dtype=complex)
    for idx in range(4):
        basis = np.zeros((2, 2), dtype=complex)
        basis.reshape(4)[idx] = 1.0
        liouvillian[:, idx] = vector_field(basis).reshape(4)
    FLOW_CACHE[terrain] = expm(T_FLOW * liouvillian)
    return FLOW_CACHE[terrain]


def flow_terrain(terrain: int, rho: np.ndarray) -> np.ndarray:
    evolved = terrain_flow_matrix(terrain) @ rho.reshape(4)
    return clean_density(evolved.reshape((2, 2)))


def op(name: str) -> Callable[[np.ndarray], np.ndarray]:
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
    if name == "Ti":
        return lambda rho: (1 - Q) * rho + Q * (p0 @ rho @ p0 + p1 @ rho @ p1)
    if name == "Te":
        return lambda rho: (1 - Q) * rho + Q * (qp @ rho @ qp + qm @ rho @ qm)
    if name == "Fi":
        unitary = expm(-1j * TH / 2.0 * SX)
        return lambda rho: unitary @ rho @ unitary.conj().T
    if name == "Fe":
        unitary = expm(-1j * TH / 2.0 * SZ)
        return lambda rho: unitary @ rho @ unitary.conj().T
    raise KeyError(name)


def apply_op(name: str, rho: np.ndarray, strength: float = 1.0) -> np.ndarray:
    moved = op(name)(rho.copy())
    out = (1.0 - strength) * rho + strength * moved
    return clean_density(out)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.trace(rho @ sigma).real) for sigma in (SX, SY, SZ)])


def dm(vector: np.ndarray) -> np.ndarray:
    return clean_density(0.5 * (I2 + vector[0] * SX + vector[1] * SY + vector[2] * SZ))


def signed_volume(points: np.ndarray) -> float:
    return float(
        sum(np.dot(points[i], np.cross(points[i + 1], points[i + 2])) for i in range(len(points) - 2))
    )


def random_probe(rng: np.random.Generator, radius: float = 0.65) -> np.ndarray:
    vec = rng.standard_normal(3)
    vec = vec / np.linalg.norm(vec)
    return vec * radius


def probe_set(seed: int, n: int, radius: float = 0.65) -> List[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [random_probe(rng, radius) for _ in range(n)]


def architecture_suite() -> List[Architecture]:
    suite = [
        Architecture("A1", "A1", "RUN-ALL-4 canonical-first", None, "all four sequential; canonical first"),
        Architecture("A2", "A2", "RUN-ALL-4 canonical-last", None, "all four sequential; canonical last"),
        Architecture("B", "B", "SELECT-1 canonical only", None, "16 executed chart-locked stages"),
        Architecture("D", "D", "PARALLEL-BRANCH canonical output", None, "16 executed + 48 counterfactual readouts"),
    ]
    for alpha in C_SWEEP:
        suite.append(
            Architecture(
                f"C@{alpha:.2f}",
                "C",
                f"DOMINANCE-WEIGHTED alpha={alpha:.2f}",
                alpha,
                "all four sequential; canonical full, non-canonical swept",
            )
        )
    return suite


def microsteps(slot: Slot, arch: Architecture) -> List[Tuple[str, float, bool]]:
    canonical = slot.canonical_operator
    others = [name for name in ALLOPS if name != canonical]
    if arch.family == "A1":
        return [(canonical, 1.0, True)] + [(name, 1.0, False) for name in others]
    if arch.family == "A2":
        return [(name, 1.0, False) for name in others] + [(canonical, 1.0, True)]
    if arch.family in ("B", "D"):
        return [(canonical, 1.0, True)]
    if arch.family == "C":
        alpha = float(arch.attenuation)
        return [
            (name, 1.0 if name == canonical else alpha, name == canonical)
            for name in ALLOPS
        ]
    raise KeyError(arch.family)


def signed_step(slot: Slot, rho: np.ndarray, op_name: str, strength: float, drive: bool) -> np.ndarray:
    if not drive:
        full = apply_op(op_name, rho, 1.0)
        return clean_density((1.0 - strength) * rho + strength * full)
    if slot.axis6_sign == "up":
        full = flow_terrain(slot.terrain, apply_op(op_name, rho, 1.0))
    elif slot.axis6_sign == "down":
        full = apply_op(op_name, flow_terrain(slot.terrain, rho), 1.0)
    else:
        raise ValueError(slot.axis6_sign)
    return clean_density((1.0 - strength) * rho + strength * full)


def stage_apply(
    slot: Slot,
    arch: Architecture,
    rho: np.ndarray,
    drive: bool = True,
    drop_index: int | None = None,
    flip_sign: bool = False,
) -> Tuple[np.ndarray, Dict[str, object]]:
    active_slot = replace(slot, axis6_sign=("down" if slot.axis6_sign == "up" else "up")) if flip_sign else slot
    if arch.family == "D":
        branches = {}
        for op_name in ALLOPS:
            branches[op_name] = signed_step(active_slot, rho.copy(), op_name, 1.0, drive)
        return clean_density(branches[slot.canonical_operator]), {
            "counterfactual_bloch": {
                name: [round(x, 8) for x in bloch(val)]
                for name, val in branches.items()
                if name != slot.canonical_operator
            }
        }

    out = rho.copy()
    trace = []
    for idx, (op_name, strength, is_canonical) in enumerate(microsteps(active_slot, arch)):
        if drop_index is not None and idx == drop_index:
            trace.append({"op": op_name, "strength": strength, "canonical": is_canonical, "dropped": True})
            continue
        out = signed_step(active_slot, out, op_name, strength, drive)
        trace.append({"op": op_name, "strength": strength, "canonical": is_canonical, "dropped": False})
    return clean_density(out), {"microstep_trace": trace}


def loop_slots(slots: Sequence[Slot], engine: str, loop: str) -> List[Slot]:
    return sorted([slot for slot in slots if slot.engine == engine and slot.loop == loop], key=lambda s: s.step)


def run_loop(
    loop: Sequence[Slot],
    arch: Architecture,
    probe: np.ndarray,
    drive: bool = True,
    flip_sign: bool = False,
) -> np.ndarray:
    rho = dm(probe)
    traj = [bloch(rho)]
    for slot in loop:
        rho, _ = stage_apply(slot, arch, rho, drive=drive, flip_sign=flip_sign)
        traj.append(bloch(rho))
    return np.array(traj)


def stage_signature(slot: Slot, arch: Architecture, probes: Sequence[np.ndarray], drive: bool = True) -> np.ndarray:
    chunks = []
    for probe in probes:
        rho, _ = stage_apply(slot, arch, dm(probe), drive=drive)
        chunks.append(bloch(rho))
    return np.concatenate(chunks)


def min_pairwise(signatures: Sequence[np.ndarray]) -> float:
    return min(
        float(np.linalg.norm(signatures[i] - signatures[j]))
        for i in range(len(signatures))
        for j in range(i + 1, len(signatures))
    )


def endpoint_for_order(stage_order: Sequence[Slot], arch: Architecture, probe: np.ndarray) -> np.ndarray:
    rho = dm(probe)
    for slot in stage_order:
        rho, _ = stage_apply(slot, arch, rho, drive=True)
    return bloch(rho)


def permutation_spread(loop: Sequence[Slot], arch: Architecture, probe: np.ndarray) -> float:
    endpoints = [endpoint_for_order([loop[i] for i in perm], arch, probe) for perm in permutations(range(len(loop)))]
    distances = [
        float(np.linalg.norm(endpoints[i] - endpoints[j]))
        for i in range(len(endpoints))
        for j in range(i + 1, len(endpoints))
    ]
    return float(np.mean(distances))


def compatibility_gate(slots: Sequence[Slot], arch: Architecture) -> Dict[str, object]:
    t1_outer = loop_slots(slots, "Type1_left", "outer_deductive")
    t2_inner = loop_slots(slots, "Type2_right", "inner_deductive")
    sig_probes = probe_set(11, 6, 0.62)
    stage_sigs = [stage_signature(slot, arch, sig_probes) for slot in t1_outer]
    stage_min = min_pairwise(stage_sigs)
    order_spread = permutation_spread(t1_outer, arch, np.array([0.55, 0.35, 0.25]))

    readout_probes = probe_set(12, 12, 0.60)
    t1_vol = float(np.mean([signed_volume(run_loop(t1_outer, arch, probe, True)) for probe in readout_probes]))
    t2_vol = float(np.mean([signed_volume(run_loop(t2_inner, arch, probe, True)) for probe in readout_probes]))
    t1_nodrive = float(np.mean([signed_volume(run_loop(t1_outer, arch, probe, False)) for probe in readout_probes]))
    t2_nodrive = float(np.mean([signed_volume(run_loop(t2_inner, arch, probe, False)) for probe in readout_probes]))

    stage_distinct = stage_min > 1e-3
    order_sensitive = order_spread > 1e-2
    opposite_readout = np.sign(t1_vol) != np.sign(t2_vol) and abs(t1_vol) > 1e-8 and abs(t2_vol) > 1e-8
    nodrive_collapse = abs(t1_nodrive) < 0.25 * max(abs(t1_vol), EPS) and abs(t2_nodrive) < 0.25 * max(abs(t2_vol), EPS)
    axis0_threaded = opposite_readout and nodrive_collapse
    passed = bool(stage_distinct and order_sensitive and axis0_threaded)
    return {
        "four_ordered_stages_pairwise_distinct": bool(stage_distinct),
        "four_stage_min_pairwise": round(stage_min, 8),
        "order_sensitivity_present": bool(order_sensitive),
        "order_permutation_spread": round(order_spread, 8),
        "axis0_drive_to_readout_threading": bool(axis0_threaded),
        "density_signed_volume_type1": round(t1_vol, 10),
        "density_signed_volume_type2": round(t2_vol, 10),
        "nodrive_signed_volume_type1": round(t1_nodrive, 10),
        "nodrive_signed_volume_type2": round(t2_nodrive, 10),
        "nodrive_collapse": bool(nodrive_collapse),
        "passed": passed,
    }


def stage_identity(slots: Sequence[Slot], arch: Architecture) -> Dict[str, object]:
    probes = probe_set(21, 8, 0.63)
    signatures = [stage_signature(slot, arch, probes) for slot in slots]
    dmin = min_pairwise(signatures)
    return {
        "all_16_pairwise_distinct": bool(dmin > 1e-3),
        "min_pairwise": round(dmin, 8),
        "granularity": "16 source stage slots",
    }


def microstep_contributions(slots: Sequence[Slot], arch: Architecture) -> Dict[str, object]:
    msteps = microsteps(slots[0], arch)
    if len(msteps) <= 1:
        return {
            "applies": False,
            "all_executed_microsteps_contribute": True,
            "reason": "single executed path microstep; drop-one gate not required",
            "canonical_share": 1.0,
            "noncanonical_share": 0.0,
        }

    rng = np.random.default_rng(30)
    effects: Dict[Tuple[str, int], List[float]] = {}
    metas: Dict[Tuple[str, int], Dict[str, object]] = {}
    nulls: List[float] = []
    for slot in slots:
        slot_steps = microsteps(slot, arch)
        for idx, (op_name, strength, is_canonical) in enumerate(slot_steps):
            key = (slot.slot_id, idx)
            effects[key] = []
            metas[key] = {
                "slot_id": slot.slot_id,
                "position": idx,
                "op": op_name,
                "canonical_for_stage": is_canonical,
                "strength": strength,
            }
        for _ in range(10):
            probe = random_probe(rng, 0.64)
            rho = dm(probe)
            full, _ = stage_apply(slot, arch, rho, drive=True)
            jitter = rng.standard_normal(3)
            jitter = jitter / np.linalg.norm(jitter) * 1e-6
            full_jitter, _ = stage_apply(slot, arch, dm(probe + jitter), drive=True)
            nulls.append(float(np.linalg.norm(bloch(full) - bloch(full_jitter))))
            for idx in range(len(slot_steps)):
                dropped, _ = stage_apply(slot, arch, rho, drive=True, drop_index=idx)
                effects[(slot.slot_id, idx)].append(float(np.linalg.norm(bloch(full) - bloch(dropped))))

    null_threshold = float(np.quantile(nulls, 0.99)) * 10.0 + 1e-10
    by_position = {}
    canonical_total = 0.0
    noncanonical_total = 0.0
    all_contribute = True
    for key, vals in effects.items():
        mean_effect = float(np.mean(vals))
        meta = metas[key]
        contributes = mean_effect > null_threshold
        all_contribute = all_contribute and contributes
        if bool(meta["canonical_for_stage"]):
            canonical_total += mean_effect
        else:
            noncanonical_total += mean_effect
        by_position[f"{key[0]}:{key[1]}"] = {
            **meta,
            "mean_drop_effect": round(mean_effect, 10),
            "contributes_beyond_null": bool(contributes),
        }

    total = canonical_total + noncanonical_total
    canonical_share = canonical_total / total if total > 0 else 0.0
    noncanonical_share = noncanonical_total / total if total > 0 else 0.0
    return {
        "applies": True,
        "null": {
            "method": "independent probe draws plus 1e-6 state jitter through the same stage map",
            "p99_times_10_plus_eps": round(null_threshold, 12),
            "draw_count": len(nulls),
        },
        "all_executed_microsteps_contribute": bool(all_contribute),
        "by_position": by_position,
        "canonical_share": round(canonical_share, 8),
        "noncanonical_share": round(noncanonical_share, 8),
    }


def controls(slots: Sequence[Slot], arch: Architecture) -> Dict[str, object]:
    rng = np.random.default_rng(44)
    shuffled_slots = list(slots)
    shuffled_ops = [slot.canonical_operator for slot in shuffled_slots]
    rng.shuffle(shuffled_ops)
    shuffled_slots = [
        replace(slot, canonical_operator=op_name, canonical_token=f"{op_name}:{slot.terrain_label}")
        for slot, op_name in zip(shuffled_slots, shuffled_ops)
    ]
    shuffled_identity = stage_identity(shuffled_slots, arch)
    t1_outer = loop_slots(slots, "Type1_left", "outer_deductive")
    probes = probe_set(45, 8, 0.6)
    sign_flip_distances = []
    nodrive_distances = []
    for probe in probes:
        real = run_loop(t1_outer, arch, probe, drive=True)[-1]
        flipped = run_loop(t1_outer, arch, probe, drive=True, flip_sign=True)[-1]
        nodrive = run_loop(t1_outer, arch, probe, drive=False)[-1]
        sign_flip_distances.append(float(np.linalg.norm(real - flipped)))
        nodrive_distances.append(float(np.linalg.norm(real - nodrive)))
    return {
        "shuffled_operator_control": {
            "all_16_pairwise_distinct": shuffled_identity["all_16_pairwise_distinct"],
            "min_pairwise": shuffled_identity["min_pairwise"],
            "note": "canonical operators shuffled independently from source slots",
        },
        "sign_flip_control": {
            "mean_loop_output_distance": round(float(np.mean(sign_flip_distances)), 8),
            "sign_is_load_bearing_at_loop_output": bool(float(np.mean(sign_flip_distances)) > 1e-3),
        },
        "no_drive_control": {
            "mean_loop_output_distance": round(float(np.mean(nodrive_distances)), 8),
            "drive_is_load_bearing_at_loop_output": bool(float(np.mean(nodrive_distances)) > 1e-3),
        },
    }


def loop_output_signature(slots: Sequence[Slot], arch: Architecture) -> np.ndarray:
    t1_outer = loop_slots(slots, "Type1_left", "outer_deductive")
    chunks = [run_loop(t1_outer, arch, probe, drive=True)[-1] for probe in probe_set(51, 10, 0.61)]
    return np.concatenate(chunks)


def discriminability_matrix(slots: Sequence[Slot], suite: Sequence[Architecture]) -> Dict[str, object]:
    signatures = {arch.key: loop_output_signature(slots, arch) for arch in suite}
    matrix: Dict[str, Dict[str, float]] = {}
    equivalent_pairs = []
    distinguishable_pairs = []
    threshold = 1e-6
    for a in suite:
        matrix[a.key] = {}
        for b in suite:
            dist = float(np.linalg.norm(signatures[a.key] - signatures[b.key]))
            matrix[a.key][b.key] = round(dist, 10)
            if a.key < b.key:
                pair = [a.key, b.key]
                if dist <= threshold:
                    equivalent_pairs.append(pair)
                else:
                    distinguishable_pairs.append(pair)
    return {
        "granularity": "Type1 outer-deductive loop output over same initial states",
        "threshold": threshold,
        "matrix": matrix,
        "observationally_equivalent_pairs": equivalent_pairs,
        "distinguishable_pairs_count": len(distinguishable_pairs),
    }


def natural_split_note(arch: Architecture) -> str:
    if arch.family == "B":
        return "Natural chart-path split: 16 chart-locked executed stages; other operator tokens are settings."
    if arch.family == "D":
        return "Natural 16-executed/48-counterfactual split: canonical branch is output; other three branch outputs are recorded readouts."
    if arch.family in ("A1", "A2"):
        return "No 16/48 split: all 64 stage-operator microsteps execute sequentially."
    if arch.family == "C":
        return "Soft 16/48 split only if alpha<1: all 64 execute, but 48 non-canonical microsteps are attenuated by swept alpha."
    return "unclassified"


def run_architecture(slots: Sequence[Slot], arch: Architecture) -> Dict[str, object]:
    comp = compatibility_gate(slots, arch)
    contrib = microstep_contributions(slots, arch)
    ident = stage_identity(slots, arch)
    ctrl = controls(slots, arch)
    admitted = bool(comp["passed"] and contrib["all_executed_microsteps_contribute"])
    return {
        "key": arch.key,
        "family": arch.family,
        "label": arch.label,
        "attenuation": arch.attenuation,
        "output_reading": arch.output_reading,
        "compatibility_gate": comp,
        "microstep_contribution": contrib,
        "dominance_profile": {
            "canonical_share": contrib["canonical_share"],
            "noncanonical_share": contrib["noncanonical_share"],
            "natural_16_chart_locked_48_runtime_split": natural_split_note(arch),
        },
        "stage_identity": ident,
        "controls": ctrl,
        "verdict": "ADMITTED" if admitted else "INADMISSIBLE",
        "admitted": admitted,
    }


def counterfactual_sample(slots: Sequence[Slot]) -> Dict[str, object]:
    arch = Architecture("D", "D", "PARALLEL-BRANCH canonical output", None, "counterfactual sample")
    first = slots[0]
    rho, info = stage_apply(first, arch, dm(np.array([0.55, 0.35, 0.25])), drive=True)
    return {
        "slot_id": first.slot_id,
        "canonical_output_bloch": [round(x, 8) for x in bloch(rho)],
        **info,
    }


def print_gate_table(results: Sequence[Dict[str, object]]) -> None:
    print("PER-ARCHITECTURE GATE TABLE")
    print("arch        compat  microsteps  stage16  verdict")
    for res in results:
        comp = "PASS" if res["compatibility_gate"]["passed"] else "FAIL"
        micro = "PASS" if res["microstep_contribution"]["all_executed_microsteps_contribute"] else "FAIL"
        stage16 = "PASS" if res["stage_identity"]["all_16_pairwise_distinct"] else "FAIL"
        print(f"{res['key']:<10} {comp:<7} {micro:<11} {stage16:<8} {res['verdict']}")


def print_dominance(results: Sequence[Dict[str, object]]) -> None:
    print("\nDOMINANCE PROFILES")
    for res in results:
        profile = res["dominance_profile"]
        print(
            f"{res['key']:<10} canonical={profile['canonical_share']:.4f} "
            f"noncanonical={profile['noncanonical_share']:.4f} | "
            f"{profile['natural_16_chart_locked_48_runtime_split']}"
        )


def print_matrix(matrix: Dict[str, object]) -> None:
    labels = list(matrix["matrix"].keys())
    print("\nDISCRIMINABILITY MATRIX")
    print(" " * 10 + " ".join(f"{label:>10}" for label in labels))
    for row in labels:
        vals = " ".join(f"{matrix['matrix'][row][col]:10.6f}" for col in labels)
        print(f"{row:<10}{vals}")
    if matrix["observationally_equivalent_pairs"]:
        print("observationally equivalent at this granularity:", matrix["observationally_equivalent_pairs"])
    else:
        print("observationally equivalent at this granularity: []")


def main() -> int:
    slots, slot_check = load_slots()
    suite = architecture_suite()
    results = [run_architecture(slots, arch) for arch in suite]
    matrix = discriminability_matrix(slots, suite)
    admitted = [res["key"] for res in results if res["admitted"]]
    c_results = [res for res in results if res["family"] == "C"]

    out = {
        "classification": "scratch_diagnostic",
        "promotion_status": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "seed": 0,
        "question": "what is a stage's execution semantics?",
        "verdict_rule": VERDICT_RULE,
        "source_sections": SOURCE_SECTIONS,
        "source_slot_check": slot_check,
        "attenuation_policy": {
            "derived_from_sources": False,
            "reason": "checked source sections define all-4 stage interiors but provide no measured attenuation factor for non-canonical operators",
            "sweep": list(C_SWEEP),
        },
        "architectures": results,
        "dominance_weighted_sweep": c_results,
        "parallel_branch_counterfactual_sample": counterfactual_sample(slots),
        "discriminability_matrix": matrix,
        "admitted_architectures": admitted,
        "descriptive_ranking_basis": [
            "compatibility gate first",
            "microstep contribution gate for multi-execution architectures",
            "dominance profile",
            "natural meaning of 16 chart-locked / 48 runtime split",
        ],
        "claim_ceiling": "scratch_diagnostic only; no single winner, no promotion, no ontology or 64-state closure claim",
        "TOOL_MANIFEST": {
            "numpy": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density/channel measurements and matrix norms",
            },
            "scipy.linalg.expm": {
                "tried": True,
                "used": True,
                "reason": "supportive unitary construction for house operator maps",
            },
            "json": {
                "tried": True,
                "used": True,
                "reason": "source slot table input and result artifact output",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "numpy": "load_bearing",
            "scipy.linalg.expm": "supportive",
            "json": "supportive",
        },
        "divergence_log": [
            "B and D may be observationally equivalent at loop-output level even though D records counterfactual branch readouts.",
            "C is a sweep because the checked source sections do not provide a measured attenuation factor.",
            "Architecture admission is diagnostic; the sim reports survivors and does not declare a single winner.",
        ],
    }
    RESULT_PATH.write_text(json.dumps(out, indent=2) + "\n")

    print("STAGE-INTERIOR ARCHITECTURE TOURNAMENT")
    print("classification: scratch_diagnostic")
    print("promotion_allowed: false")
    print(VERDICT_RULE)
    print()
    print_gate_table(results)
    print_dominance(results)
    print_matrix(matrix)
    print("\nDOMINANCE-WEIGHTED SWEEP")
    for res in c_results:
        profile = res["dominance_profile"]
        print(
            f"{res['key']}: verdict={res['verdict']} "
            f"compat={res['compatibility_gate']['passed']} "
            f"microsteps={res['microstep_contribution']['all_executed_microsteps_contribute']} "
            f"canonical_share={profile['canonical_share']:.4f}"
        )
    print("\nADMITTED ARCHITECTURES:", admitted)
    print("RESULT_JSON:", RESULT_PATH)
    print("ALL_GATES: HONEST_MIX_REPORTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
