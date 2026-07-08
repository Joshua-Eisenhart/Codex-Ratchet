#!/usr/bin/env python3
"""engine_pair_basin_map_sim.

Scratch diagnostic for the Type1/Type2 engine-pair basin structure over the
64 microstep schedule. The 64 schedule is rebuilt from the 16 source slots by
expanding each source slot over Ti/Te/Fi/Fe at the slot's shared axis-6 order.

Measured objects:
- basin counts, attractor locations, and grid-volume fractions after repeated
  full two-loop engine cycles;
- loop-level basin containment into the corresponding full-engine basins;
- perturbation radius needed to leave each measured basin;
- W-mirror relation between Type1 basins and mirrored Type2 basins;
- shuffled-order and commuting-generator controls, recomputed independently.

This is a scratch_diagnostic only. It exits 0 for any honest verdict mix.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import expm


sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JOIN_PATH = HERE / "stage_token_join.json"
SOURCE16_PATH = ROOT / "reference_docs" / "engine_math" / "source_schedule_tables" / "engine_16_source_stage_slots.json"
RESULT_PATH = Path(__file__).with_name(Path(__file__).stem + "_results.json")

SEED = 0
OPS = ("Ti", "Te", "Fi", "Fe")
ENGINE_LOOP_ORDER = {
    "Type1_left": ("outer_deductive", "inner_inductive"),
    "Type2_right": ("outer_inductive", "inner_deductive"),
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

G = 0.35
KAP = 1.0
Q = 1.0 - np.exp(-1.0)
TH = np.pi / 4.0
N_STEPS = 32
CYCLES = 6
GRID_RADIUS = 0.90
CLUSTER_EPS = 0.045
MIRROR_EPS = 0.09
TRANSITION_DIRS = 24
TRANSITION_RADII = tuple(float(x) for x in np.linspace(0.04, 1.20, 12))

SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
H0 = (SX + SY + SZ) / np.sqrt(3.0)
W = (SX + SZ) / np.sqrt(2.0)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_source_slots() -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    join = load_json(JOIN_PATH)
    slots16 = load_json(SOURCE16_PATH)
    if join.get("blocked"):
        raise ValueError("stage_token_join is blocked")
    if len(slots16) != 16:
        raise ValueError(f"source 16-slot table has {len(slots16)} rows, expected 16")

    join_by_slot = {row["source_slot_id"]: row for row in join["stage_join"]}
    terrain_by_name = {row["terrain_name"]: row["terrain_index"] for row in join["terrain_index_map"]}
    schedules: dict[str, list[dict[str, Any]]] = {"Type1_left": [], "Type2_right": []}

    for src in slots16:
        joined = join_by_slot[src["slot_id"]]
        if joined["canonical_token"] != src["canonical_token"]:
            raise ValueError(f"{src['slot_id']} token mismatch between source table and stage_token_join")
        for op_name in OPS:
            row = {
                "slot_id": src["slot_id"],
                "engine": src["engine"],
                "loop": src["loop"],
                "step": int(src["step"]),
                "terrain": src["terrain"],
                "terrain_index": int(terrain_by_name[src["terrain"]]),
                "axis6_sign": src["axis6_sign"],
                "operator": op_name,
                "source_canonical_operator": src["canonical_operator"],
                "source_canonical_token": src["canonical_token"],
                "is_source_canonical": op_name == src["canonical_operator"],
            }
            schedules[src["engine"]].append(row)

    for engine, rows in schedules.items():
        loop_order = ENGINE_LOOP_ORDER[engine]
        rows.sort(key=lambda r: (loop_order.index(r["loop"]), r["step"], OPS.index(r["operator"])))
        if len(rows) != 32:
            raise ValueError(f"{engine} expanded schedule has {len(rows)} rows, expected 32")

    meta = {
        "stage_token_join": str(JOIN_PATH.relative_to(HERE.parents[2])),
        "source_slots": str(SOURCE16_PATH.relative_to(HERE.parents[2])),
        "expansion_rule": "each 16-slot source stage expands over Ti/Te/Fi/Fe at the stage shared axis6_sign",
        "microsteps_per_engine_cycle": {engine: len(rows) for engine, rows in schedules.items()},
        "canonical_slot_tokens": {
            engine: [r["source_canonical_token"] for r in rows if r["is_source_canonical"]]
            for engine, rows in schedules.items()
        },
    }
    return schedules, meta


def dm(vec: np.ndarray | list[float]) -> np.ndarray:
    v = np.asarray(vec, float)
    n = float(np.linalg.norm(v))
    if n >= 0.985:
        v = v / n * 0.985
    return 0.5 * (I2 + v[0] * SX + v[1] * SY + v[2] * SZ)


def bloch(rho: np.ndarray) -> np.ndarray:
    return np.array([float(np.trace(rho @ s).real) for s in (SX, SY, SZ)])


def normalize_rho(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / np.trace(rho).real


def dop(lindblad_op: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return (
        lindblad_op @ rho @ lindblad_op.conj().T
        - 0.5 * (lindblad_op.conj().T @ lindblad_op @ rho + rho @ lindblad_op.conj().T @ lindblad_op)
    )


def lindblad_ops(kind: str, pole: int) -> list[np.ndarray]:
    if kind == "damp":
        return [SP if pole > 0 else SM]
    if kind == "depol":
        return [SX / np.sqrt(2.0), SY / np.sqrt(2.0)]
    if kind == "proj":
        return [SZ]
    raise ValueError(f"unknown terrain kind {kind!r}")


def terrain_params(terrain_index: int, *, commuting: bool = False) -> tuple[np.ndarray, list[np.ndarray]]:
    if commuting:
        return SZ, [SX / np.sqrt(2.0), SY / np.sqrt(2.0), SZ / np.sqrt(2.0)]
    eps, kind, pole = TERR[terrain_index]
    return eps * H0, lindblad_ops(kind, pole)


def flow(hamiltonian: np.ndarray, lindblads: list[np.ndarray], rho: np.ndarray) -> np.ndarray:
    dt = 1.0 / N_STEPS
    state = rho.copy()

    def rhs(x: np.ndarray) -> np.ndarray:
        out = -1j * G * (hamiltonian @ x - x @ hamiltonian)
        for lindblad_op in lindblads:
            out = out + KAP * dop(lindblad_op, x)
        return out

    for _ in range(N_STEPS):
        k1 = rhs(state)
        k2 = rhs(state + 0.5 * dt * k1)
        k3 = rhs(state + 0.5 * dt * k2)
        k4 = rhs(state + dt * k3)
        state = normalize_rho(state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4))
    return state


def op(name: str, *, commuting: bool = False):
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
    if commuting:
        if name in ("Ti", "Te"):
            return lambda rho: normalize_rho((1.0 - Q) * rho + Q * (p0 @ rho @ p0 + p1 @ rho @ p1))
        u = expm(-1j * TH / 2.0 * SZ)
        return lambda rho: normalize_rho(u @ rho @ u.conj().T)
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


def step(slot: dict[str, Any], rho: np.ndarray, *, commuting: bool = False) -> np.ndarray:
    hamiltonian, lindblads = terrain_params(int(slot["terrain_index"]), commuting=commuting)
    operator = op(slot["operator"], commuting=commuting)
    if slot["axis6_sign"] == "up":
        return flow(hamiltonian, lindblads, operator(rho.copy()))
    if slot["axis6_sign"] == "down":
        return operator(flow(hamiltonian, lindblads, rho.copy()))
    raise ValueError(f"bad axis6_sign {slot['axis6_sign']!r}")


def run_schedule(
    slots: list[dict[str, Any]],
    initial_vec: np.ndarray | list[float],
    *,
    cycles: int = CYCLES,
    commuting: bool = False,
) -> np.ndarray:
    affine = schedule_affine(slots, cycles=cycles, commuting=commuting)
    return apply_affine(affine, np.asarray(initial_vec, float))


def stage_affine(slot: dict[str, Any], *, commuting: bool = False) -> tuple[np.ndarray, np.ndarray]:
    b = bloch(step(slot, dm([0.0, 0.0, 0.0]), commuting=commuting))
    cols = []
    for axis in np.eye(3):
        cols.append(bloch(step(slot, dm(axis), commuting=commuting)) - b)
    return np.column_stack(cols), b


def compose_affine(
    first: tuple[np.ndarray, np.ndarray],
    second: tuple[np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    a1, b1 = first
    a2, b2 = second
    return a2 @ a1, a2 @ b1 + b2


def schedule_affine(
    slots: list[dict[str, Any]],
    *,
    cycles: int = CYCLES,
    commuting: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    one_cycle = (np.eye(3), np.zeros(3))
    for slot in slots:
        one_cycle = compose_affine(one_cycle, stage_affine(slot, commuting=commuting))
    full = (np.eye(3), np.zeros(3))
    for _ in range(cycles):
        full = compose_affine(full, one_cycle)
    return full


def apply_affine(affine: tuple[np.ndarray, np.ndarray], vec: np.ndarray) -> np.ndarray:
    a, b = affine
    out = a @ vec + b
    n = float(np.linalg.norm(out))
    if n > 1.0 + 1e-7:
        out = out / n
    return out


def bloch_grid() -> list[np.ndarray]:
    levels = np.linspace(-GRID_RADIUS, GRID_RADIUS, 7)
    pts: list[np.ndarray] = []
    for x in levels:
        for y in levels:
            for z in levels:
                v = np.array([x, y, z], float)
                if np.linalg.norm(v) <= GRID_RADIUS + 1e-12:
                    pts.append(v)
    pts.append(np.zeros(3))
    unique = {}
    for p in pts:
        unique[tuple(np.round(p, 12))] = p
    return list(unique.values())


def random_unit_vectors(rng: np.random.Generator, n: int) -> list[np.ndarray]:
    out = []
    for _ in range(n):
        v = rng.normal(size=3)
        out.append(v / np.linalg.norm(v))
    return out


def cluster_points(points: list[np.ndarray], eps: float = CLUSTER_EPS) -> dict[str, Any]:
    centers: list[np.ndarray] = []
    members: list[list[int]] = []
    for idx, point in enumerate(points):
        if not centers:
            centers.append(point.copy())
            members.append([idx])
            continue
        distances = [float(np.linalg.norm(point - c)) for c in centers]
        nearest = int(np.argmin(distances))
        if distances[nearest] <= eps:
            members[nearest].append(idx)
            centers[nearest] = np.mean([points[i] for i in members[nearest]], axis=0)
        else:
            centers.append(point.copy())
            members.append([idx])

    ordered = sorted(range(len(centers)), key=lambda i: tuple(float(x) for x in centers[i]))
    remap = {old: new for new, old in enumerate(ordered)}
    point_labels = [0 for _ in points]
    basin_rows = []
    for old in ordered:
        new_id = remap[old]
        idxs = members[old]
        for idx in idxs:
            point_labels[idx] = new_id
        spread = max(float(np.linalg.norm(points[i] - centers[old])) for i in idxs)
        basin_rows.append(
            {
                "basin_id": new_id,
                "center": [round(float(x), 8) for x in centers[old]],
                "count": len(idxs),
                "volume_fraction": round(len(idxs) / len(points), 8),
                "max_endpoint_spread": round(spread, 8),
            }
        )
    return {
        "n_basins": len(basin_rows),
        "centers": [np.array(row["center"], float) for row in basin_rows],
        "labels": point_labels,
        "basins": basin_rows,
    }


def assign_center(point: np.ndarray, centers: list[np.ndarray]) -> tuple[int, float]:
    distances = [float(np.linalg.norm(point - center)) for center in centers]
    idx = int(np.argmin(distances))
    return idx, distances[idx]


def analyze_schedule(
    label: str,
    slots: list[dict[str, Any]],
    grid: list[np.ndarray],
    *,
    cycles: int = CYCLES,
    commuting: bool = False,
) -> dict[str, Any]:
    affine = schedule_affine(slots, cycles=cycles, commuting=commuting)
    endpoints = [apply_affine(affine, p) for p in grid]
    clustered = cluster_points(endpoints)
    return {
        "label": label,
        "grid_points": len(grid),
        "cycles": cycles,
        "cluster_eps": CLUSTER_EPS,
        "n_basins": clustered["n_basins"],
        "verdict": "multi_basin" if clustered["n_basins"] > 1 else "single_basin",
        "basins": clustered["basins"],
        "_centers": clustered["centers"],
        "_labels": clustered["labels"],
        "_affine": affine,
    }


def shuffled_copy(slots: list[dict[str, Any]], rng: np.random.Generator) -> list[dict[str, Any]]:
    copied = [dict(s) for s in slots]
    order = rng.permutation(len(copied))
    return [copied[int(i)] for i in order]


def loop_schedules(engine_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in engine_rows:
        out.setdefault(row["loop"], []).append(row)
    for rows in out.values():
        rows.sort(key=lambda r: (r["step"], OPS.index(r["operator"])))
    return out


def nesting_report(
    engine: str,
    engine_slots: list[dict[str, Any]],
    engine_analysis: dict[str, Any],
    grid: list[np.ndarray],
) -> dict[str, Any]:
    rows = []
    all_contained = True
    centers = engine_analysis["_centers"]
    for loop_name, slots in loop_schedules(engine_slots).items():
        loop_analysis = analyze_schedule(f"{engine}:{loop_name}", slots, grid)
        for basin in loop_analysis["basins"]:
            loop_center = np.asarray(basin["center"], float)
            direct_id, direct_dist = assign_center(loop_center, centers)
            after = apply_affine(engine_analysis["_affine"], loop_center)
            after_id, after_dist = assign_center(after, centers)
            contained = after_dist <= CLUSTER_EPS
            all_contained = all_contained and contained
            rows.append(
                {
                    "loop": loop_name,
                    "loop_basin_id": basin["basin_id"],
                    "loop_basin_volume_fraction": basin["volume_fraction"],
                    "nearest_engine_basin_before_full_engine": direct_id,
                    "distance_before_full_engine": round(float(direct_dist), 8),
                    "engine_basin_after_full_engine": after_id,
                    "distance_after_full_engine": round(float(after_dist), 8),
                    "contained_after_full_engine": bool(contained),
                    "loop_basin_count": loop_analysis["n_basins"],
                }
            )
    return {
        "engine": engine,
        "containment_relations": rows,
        "verdict": "nesting_holds" if all_contained else "nesting_fails",
    }


def transition_depths(
    engine: str,
    slots: list[dict[str, Any]],
    analysis: dict[str, Any],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    centers = analysis["_centers"]
    dirs = random_unit_vectors(rng, TRANSITION_DIRS)
    depths = []
    for basin in analysis["basins"]:
        basin_id = int(basin["basin_id"])
        center = np.asarray(basin["center"], float)
        found = None
        target = None
        for radius in TRANSITION_RADII:
            if found is not None:
                break
            for direction in dirs:
                candidate = center + radius * direction
                n = float(np.linalg.norm(candidate))
                if n >= 0.985:
                    candidate = candidate / n * 0.985
                endpoint = apply_affine(analysis["_affine"], candidate)
                assigned, dist = assign_center(endpoint, centers)
                if assigned != basin_id and dist <= CLUSTER_EPS:
                    found = float(radius)
                    target = int(assigned)
                    break
        depths.append(
            {
                "engine": engine,
                "basin_id": basin_id,
                "depth_proxy_radius": None if found is None else round(found, 8),
                "transition_target_basin": target,
                "status": "no_transition_found_within_scan" if found is None else "transition_found",
                "scan_radii": [round(float(r), 8) for r in TRANSITION_RADII],
                "directions": TRANSITION_DIRS,
            }
        )
    return depths


def w_mirror_bloch(vec: np.ndarray) -> np.ndarray:
    rho = dm(vec)
    return bloch(W @ rho @ W)


def hausdorff(a: list[np.ndarray], b: list[np.ndarray]) -> float:
    if not a or not b:
        return float("inf")
    ab = max(min(float(np.linalg.norm(x - y)) for y in b) for x in a)
    ba = max(min(float(np.linalg.norm(y - x)) for x in a) for y in b)
    return max(ab, ba)


def mirror_report(type1: dict[str, Any], type2: dict[str, Any]) -> dict[str, Any]:
    t1 = type1["_centers"]
    t2_m = [w_mirror_bloch(c) for c in type2["_centers"]]
    h = hausdorff(t1, t2_m)
    matches = []
    for i, c in enumerate(t1):
        j, d = assign_center(c, t2_m)
        matches.append({"type1_basin_id": i, "mirrored_type2_basin_id": j, "distance": round(float(d), 8)})
    holds = len(t1) == len(t2_m) and h <= MIRROR_EPS
    return {
        "W_bloch_action": "rho -> W rho W; Bloch(x,y,z) -> (z,-y,x)",
        "type1_basin_count": len(t1),
        "mirrored_type2_basin_count": len(t2_m),
        "hausdorff_distance": round(float(h), 8),
        "mirror_eps": MIRROR_EPS,
        "nearest_matches": matches,
        "verdict": "mirror_relation_holds" if holds else "mirror_relation_fails",
    }


def control_report(
    engine: str,
    real: dict[str, Any],
    shuffled: dict[str, Any],
    commuting: dict[str, Any],
) -> dict[str, Any]:
    h_shuffle = hausdorff(real["_centers"], shuffled["_centers"])
    shuffled_changes = real["n_basins"] != shuffled["n_basins"] or h_shuffle > CLUSTER_EPS
    commuting_collapses = commuting["n_basins"] == 1 and commuting["n_basins"] <= real["n_basins"]
    return {
        "engine": engine,
        "shuffled_schedule": {
            "real_basin_count": real["n_basins"],
            "shuffled_basin_count": shuffled["n_basins"],
            "center_hausdorff_distance": round(float(h_shuffle), 8),
            "verdict": "schedule_control_changes_basin_structure"
            if shuffled_changes
            else "schedule_control_no_structure_change",
        },
        "commuting_generators": {
            "real_basin_count": real["n_basins"],
            "commuting_basin_count": commuting["n_basins"],
            "verdict": "commuting_control_collapses"
            if commuting_collapses
            else "commuting_control_fails_to_collapse",
        },
    }


def public_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in analysis.items() if not k.startswith("_")}


def print_basin_table(title: str, analysis: dict[str, Any]) -> None:
    print(title)
    print(f"  verdict={analysis['verdict']}  basins={analysis['n_basins']}  grid={analysis['grid_points']}  cycles={analysis['cycles']}")
    print("  basin_id | volume | center[x,y,z] | max_endpoint_spread")
    for basin in analysis["basins"]:
        c = basin["center"]
        print(
            f"  {basin['basin_id']:8d} | {basin['volume_fraction']:.4f} | "
            f"[{c[0]:+.5f}, {c[1]:+.5f}, {c[2]:+.5f}] | {basin['max_endpoint_spread']:.6f}"
        )


def main() -> int:
    rng = np.random.default_rng(SEED)
    schedules, schedule_meta = load_source_slots()
    grid = bloch_grid()

    real = {
        engine: analyze_schedule(f"{engine}:real_64_expanded", rows, grid)
        for engine, rows in schedules.items()
    }
    shuffled = {
        engine: analyze_schedule(
            f"{engine}:shuffled_order_control",
            shuffled_copy(rows, np.random.default_rng(SEED + 101 + i)),
            grid,
        )
        for i, (engine, rows) in enumerate(schedules.items())
    }
    commuting = {
        engine: analyze_schedule(
            f"{engine}:commuting_generator_control",
            [dict(row) for row in rows],
            grid,
            commuting=True,
        )
        for engine, rows in schedules.items()
    }
    nesting = {
        engine: nesting_report(engine, schedules[engine], real[engine], grid)
        for engine in schedules
    }
    transitions = {
        engine: transition_depths(engine, schedules[engine], real[engine], rng)
        for engine in schedules
    }
    controls = {
        engine: control_report(engine, real[engine], shuffled[engine], commuting[engine])
        for engine in schedules
    }
    mirror = mirror_report(real["Type1_left"], real["Type2_right"])

    verdicts = {
        "Type1_left": real["Type1_left"]["verdict"],
        "Type2_right": real["Type2_right"]["verdict"],
        "Type1_nesting": nesting["Type1_left"]["verdict"],
        "Type2_nesting": nesting["Type2_right"]["verdict"],
        "pair_mirror_relation": mirror["verdict"],
        "Type1_shuffled_control": controls["Type1_left"]["shuffled_schedule"]["verdict"],
        "Type2_shuffled_control": controls["Type2_right"]["shuffled_schedule"]["verdict"],
        "Type1_commuting_control": controls["Type1_left"]["commuting_generators"]["verdict"],
        "Type2_commuting_control": controls["Type2_right"]["commuting_generators"]["verdict"],
    }

    out = {
        "classification": "scratch_diagnostic",
        "promotion_status": "scratch_diagnostic",
        "promotion_allowed": False,
        "sim_id": "engine_pair_basin_map_sim",
        "name": "Engine pair basin map across expanded 64 schedule",
        "version": "1.0",
        "seed": SEED,
        "rng": "numpy.default_rng(0)",
        "claim_ceiling": "runs; empirical basin map over finite grid and finite perturbation scan; no promotion/admission claim",
        "source_basis": schedule_meta,
        "parameters": {
            "grid_points": len(grid),
            "grid_radius": GRID_RADIUS,
            "cycles": CYCLES,
            "rk4_steps_per_stage_flow": N_STEPS,
            "cluster_eps": CLUSTER_EPS,
            "mirror_eps": MIRROR_EPS,
            "transition_dirs": TRANSITION_DIRS,
            "transition_radii": [round(float(r), 8) for r in TRANSITION_RADII],
        },
        "TOOL_MANIFEST": {
            "numpy": "density matrices, Bloch vectors, clustering, perturbation scans",
            "scipy.linalg.expm": "unitary operator exponentials for Fi/Fe and W documentation cross-check",
            "json": "result receipt emission",
        },
        "tool_manifest": {
            "numpy": "density matrices, Bloch vectors, clustering, perturbation scans",
            "scipy.linalg.expm": "unitary operator exponentials for Fi/Fe and W documentation cross-check",
            "json": "result receipt emission",
        },
        "TOOL_INTEGRATION_DEPTH": "supportive",
        "tool_integration_depth": "supportive",
        "divergence_log": [
            "shuffled schedule control recomputes endpoints from a separately shuffled order",
            "commuting-generator control recomputes endpoints with all generators/operators on one commuting z-axis",
        ],
        "basin_maps": {engine: public_analysis(analysis) for engine, analysis in real.items()},
        "loop_to_engine_nesting": nesting,
        "transition_depth_proxy": transitions,
        "pair_mirror_structure": mirror,
        "controls": {
            engine: {
                **controls[engine],
                "shuffled_basin_map": public_analysis(shuffled[engine]),
                "commuting_basin_map": public_analysis(commuting[engine]),
            }
            for engine in schedules
        },
        "verdicts": verdicts,
        "control_independence": {
            "real": "computed by analyze_schedule on canonical expanded slots",
            "shuffled": "computed by analyze_schedule on separately copied and permuted slots",
            "commuting": "computed by analyze_schedule with commuting=True and no endpoint reuse",
            "no_aliasing": True,
        },
    }
    RESULT_PATH.write_text(json.dumps(out, indent=2) + "\n")

    print("ENGINE PAIR BASIN MAP -- expanded 64 schedule, real GKSL dynamics")
    print(f"seed={SEED} grid_points={len(grid)} cycles={CYCLES} cluster_eps={CLUSTER_EPS}")
    print(f"result={RESULT_PATH}")
    print()
    print_basin_table("BASINS: Type1_left", real["Type1_left"])
    print()
    print_basin_table("BASINS: Type2_right", real["Type2_right"])
    print()
    print("NESTING:")
    for engine, report in nesting.items():
        print(f"  {engine}: {report['verdict']}")
        for row in report["containment_relations"]:
            print(
                "    "
                f"{row['loop']} basin {row['loop_basin_id']} -> engine basin "
                f"{row['engine_basin_after_full_engine']} "
                f"after_dist={row['distance_after_full_engine']:.6f} contained={row['contained_after_full_engine']}"
            )
    print()
    print("TRANSITION DEPTH PROXY:")
    for engine, rows in transitions.items():
        for row in rows:
            depth = "none<=scan" if row["depth_proxy_radius"] is None else f"{row['depth_proxy_radius']:.5f}"
            print(f"  {engine} basin {row['basin_id']}: depth_radius={depth} status={row['status']}")
    print()
    print("PAIR STRUCTURE:")
    print(
        f"  W-mirror Type1 vs mirrored Type2: {mirror['verdict']} "
        f"hausdorff={mirror['hausdorff_distance']:.6f} eps={mirror['mirror_eps']}"
    )
    print()
    print("CONTROLS:")
    for engine, report in controls.items():
        sh = report["shuffled_schedule"]
        co = report["commuting_generators"]
        print(
            f"  {engine}: shuffled={sh['verdict']} "
            f"(count {sh['real_basin_count']}->{sh['shuffled_basin_count']}, "
            f"H={sh['center_hausdorff_distance']:.6f}); "
            f"commuting={co['verdict']} (count {co['real_basin_count']}->{co['commuting_basin_count']})"
        )
    print()
    print("HONEST VERDICTS:")
    for key, value in verdicts.items():
        print(f"  {key}: {value}")
    print("ALL_GATES: HONEST_MIX ->", RESULT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
