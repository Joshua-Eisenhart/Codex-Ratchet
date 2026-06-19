#!/usr/bin/env python3
"""Shared finite schedule runner for engine_64_stage_full_run_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import random
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


SIM_ID = "engine_64_stage_full_run_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}.py"
COMMON_PATH = SIM_DIR / f"{SIM_ID}_common.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "realization_relative_matrix64_stage_full_run"
RNG_SEED = 20260612
EPS = 1.0e-10

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


PARENT_PATHS = {
    "matrix64_mine": ROOT / "system_v6/receipts/matrix64_mine_20260610.md",
    "two_engine_readout_automaton": ROOT / "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "substage_transition_convention_mining": ROOT
    / "system_v6/receipts/substage_transition_convention_mining_20260611.md",
    "eng_64_julia_source": ROOT / "system_v5/julia_carrier/eng_64_hexagram_julia.jl",
    "eng_64_julia_result": ROOT / "system_v5/julia_carrier/eng_64_hexagram_julia_results.json",
}

STROKES = [
    {"stroke_index": 0, "axis1": 0, "axis2": 0, "operator_family": "Ti", "stroke_label": "expand_open"},
    {"stroke_index": 1, "axis1": 0, "axis2": 1, "operator_family": "Te", "stroke_label": "expand_closed"},
    {"stroke_index": 2, "axis1": 1, "axis2": 0, "operator_family": "Fi", "stroke_label": "compress_open"},
    {"stroke_index": 3, "axis1": 1, "axis2": 1, "operator_family": "Fe", "stroke_label": "compress_closed"},
]
STROKE_BY_BITS = {(row["axis1"], row["axis2"]): row for row in STROKES}

SUBSTAGES = [
    {"substage_index": 0, "axis5": 0, "axis6": 0, "substage_label": "family0_operator_first"},
    {"substage_index": 1, "axis5": 0, "axis6": 1, "substage_label": "family0_terrain_first"},
    {"substage_index": 2, "axis5": 1, "axis6": 0, "substage_label": "family1_operator_first"},
    {"substage_index": 3, "axis5": 1, "axis6": 1, "substage_label": "family1_terrain_first"},
]
SUBSTAGE_BY_BITS = {(row["axis5"], row["axis6"]): row for row in SUBSTAGES}

ENGINE_SPECS = {
    0: {
        "engine_family": "Type1-L",
        "sheet": "L",
        "chirality_sign": 1.0,
        "base_order_name": "C_D",
        "base_order": ["Se", "Ne", "Ni", "Si"],
        "readout_discipline": "alternating",
        "readouts": ["LOSE", "WIN", "LOSE", "WIN"],
    },
    1: {
        "engine_family": "Type2-R",
        "sheet": "R",
        "chirality_sign": -1.0,
        "base_order_name": "C_I",
        "base_order": ["Se", "Si", "Ni", "Ne"],
        "readout_discipline": "paired",
        "readouts": ["WIN", "WIN", "LOSE", "LOSE"],
    },
}

TERRAIN_REALIZATIONS = {
    ("L", "Se"): "Se/Funnel",
    ("R", "Se"): "Se/Cannon",
    ("L", "Ne"): "Ne/Vortex",
    ("R", "Ne"): "Ne/Spiral",
    ("L", "Ni"): "Ni/Pit",
    ("R", "Ni"): "Ni/Source",
    ("L", "Si"): "Si/Hill",
    ("R", "Si"): "Si/Citadel",
}

TERRAIN_SPECS = {
    "Se/Funnel": {"axis": "y", "angle": 0.11, "scale": [0.91, 0.88, 0.94], "bias": [0.018, 0.000, 0.014]},
    "Se/Cannon": {"axis": "x", "angle": 0.13, "scale": [0.90, 0.93, 0.89], "bias": [-0.015, 0.006, 0.011]},
    "Ne/Vortex": {"axis": "z", "angle": 0.17, "scale": [0.88, 0.92, 0.91], "bias": [0.004, 0.018, -0.010]},
    "Ne/Spiral": {"axis": "y", "angle": 0.19, "scale": [0.93, 0.87, 0.90], "bias": [-0.006, 0.015, 0.012]},
    "Ni/Pit": {"axis": "x", "angle": -0.15, "scale": [0.86, 0.90, 0.92], "bias": [0.010, -0.014, -0.012]},
    "Ni/Source": {"axis": "z", "angle": -0.12, "scale": [0.92, 0.89, 0.88], "bias": [-0.012, -0.011, 0.015]},
    "Si/Hill": {"axis": "y", "angle": 0.21, "scale": [0.89, 0.91, 0.87], "bias": [0.014, 0.010, 0.010]},
    "Si/Citadel": {"axis": "x", "angle": -0.18, "scale": [0.87, 0.88, 0.93], "bias": [-0.011, 0.012, -0.014]},
}

PINNED_INITIAL_STATE = np.asarray([0.2718281828459045, -0.3141592653589793, 0.5772156649015329], dtype=float)


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    return row


def parent_source_locks() -> dict[str, Any]:
    return {
        name: source_lock(path, role=name)
        for name, path in PARENT_PATHS.items()
    }


def round_float(value: float, digits: int = 15) -> float:
    value = float(value)
    if abs(value) < EPS:
        return 0.0
    return round(value, digits)


def round_vec(values: np.ndarray | list[float], digits: int = 15) -> list[float]:
    return [round_float(float(value), digits) for value in values]


def rotation(axis: str, angle: float) -> np.ndarray:
    c = math.cos(angle)
    s = math.sin(angle)
    if axis == "x":
        return np.asarray([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=float)
    if axis == "y":
        return np.asarray([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]], dtype=float)
    if axis == "z":
        return np.asarray([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)
    raise ValueError(f"unknown axis: {axis}")


def clamp_bloch(state: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(state))
    if norm > 0.999999:
        return state / norm * 0.999999
    return state


def bloch_entropy(state: np.ndarray) -> float:
    radius = min(1.0, max(0.0, float(np.linalg.norm(state))))
    vals = [(1.0 + radius) / 2.0, (1.0 - radius) / 2.0]
    return -sum(value * math.log(value) for value in vals if value > EPS)


def bloch_purity(state: np.ndarray) -> float:
    return (1.0 + float(np.dot(state, state))) / 2.0


def operator_apply(state: np.ndarray, family: str, axis5: int, chirality_sign: float, direction_sign: float) -> np.ndarray:
    q = 0.18 + 0.05 * axis5
    angle = chirality_sign * direction_sign * (0.27 + 0.04 * axis5)
    if family == "Ti":
        mat = np.diag([1.0 - q, 1.0 - q, 1.0])
    elif family == "Te":
        mat = np.diag([1.0, 1.0 - q, 1.0 - q])
    elif family == "Fi":
        mat = rotation("x", angle)
    elif family == "Fe":
        mat = rotation("z", -angle)
    else:
        raise ValueError(f"unknown operator family: {family}")
    return clamp_bloch(mat @ state)


def terrain_apply(
    state: np.ndarray,
    terrain_id: str,
    axis5: int,
    chirality_sign: float,
    direction_sign: float,
) -> np.ndarray:
    spec = TERRAIN_SPECS[terrain_id]
    angle = float(spec["angle"]) * chirality_sign * direction_sign * (1.0 + 0.25 * axis5)
    scale = np.diag(np.asarray(spec["scale"], dtype=float) - 0.015 * axis5)
    bias = np.asarray(spec["bias"], dtype=float) * chirality_sign * (1.0 + 0.2 * axis5)
    return clamp_bloch(rotation(str(spec["axis"]), angle) @ scale @ state + bias)


def matrix64_index(axis_bits: dict[str, int]) -> int:
    return (
        axis_bits["axis1"]
        + 2 * axis_bits["axis2"]
        + 4 * axis_bits["axis3"]
        + 8 * axis_bits["axis4"]
        + 16 * axis_bits["axis5"]
        + 32 * axis_bits["axis6"]
    )


def expected_stage_sequence(axis3: int, axis4: int) -> tuple[list[str], list[str]]:
    spec = ENGINE_SPECS[axis3]
    stages = list(spec["base_order"])
    readouts = list(spec["readouts"])
    if axis4 == 1:
        stages.reverse()
        readouts.reverse()
    return stages, readouts


def make_slot(axis3: int, axis4: int, stroke: dict[str, Any], substage: dict[str, Any], slot_index: int) -> dict[str, Any]:
    stages, readouts = expected_stage_sequence(axis3, axis4)
    stage = stages[int(stroke["stroke_index"])]
    readout = readouts[int(stroke["stroke_index"])]
    spec = ENGINE_SPECS[axis3]
    axis_bits = {
        "axis1": int(stroke["axis1"]),
        "axis2": int(stroke["axis2"]),
        "axis3": axis3,
        "axis4": axis4,
        "axis5": int(substage["axis5"]),
        "axis6": int(substage["axis6"]),
    }
    return {
        "slot_index": slot_index,
        "matrix64_index": matrix64_index(axis_bits),
        "axis_bits": axis_bits,
        "engine_family": spec["engine_family"],
        "sheet": spec["sheet"],
        "chirality_sign": spec["chirality_sign"],
        "direction": "CW" if axis4 == 0 else "CCW",
        "direction_sign": 1.0 if axis4 == 0 else -1.0,
        "stroke_index": int(stroke["stroke_index"]),
        "stroke_label": stroke["stroke_label"],
        "stage": stage,
        "readout": readout,
        "readout_discipline": spec["readout_discipline"],
        "substage_index": int(substage["substage_index"]),
        "substage_label": substage["substage_label"],
        "operator_family": stroke["operator_family"],
        "precedence": "operator_first" if axis_bits["axis6"] == 0 else "terrain_first",
        "signed_operator_id": f'{stroke["operator_family"]}{"+" if axis_bits["axis6"] == 0 else "-"}',
        "terrain_id": TERRAIN_REALIZATIONS[(spec["sheet"], stage)],
    }


def build_schedule() -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    slot_index = 0
    for axis3 in (0, 1):
        for axis4 in (0, 1):
            for stroke in STROKES:
                for substage in SUBSTAGES:
                    slots.append(make_slot(axis3, axis4, stroke, substage, slot_index))
                    slot_index += 1
    return slots


def erase_slot_coordinates(slot: dict[str, Any]) -> dict[str, Any]:
    erased = deepcopy(slot)
    axis3 = int(slot["axis_bits"]["axis3"])
    axis_bits = {"axis1": 0, "axis2": 0, "axis3": axis3, "axis4": 0, "axis5": 0, "axis6": 0}
    stroke = STROKE_BY_BITS[(0, 0)]
    substage = SUBSTAGE_BY_BITS[(0, 0)]
    replacement = make_slot(axis3, 0, stroke, substage, int(slot["slot_index"]))
    replacement["matrix64_index"] = matrix64_index(axis_bits)
    replacement["erased_from_axis_bits"] = slot["axis_bits"]
    return replacement


def apply_slot(state: np.ndarray, slot: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    before = np.asarray(state, dtype=float)
    axis_bits = slot["axis_bits"]
    chirality_sign = float(slot["chirality_sign"])
    direction_sign = float(slot["direction_sign"])
    family = str(slot["operator_family"])
    terrain_id = str(slot["terrain_id"])
    axis5 = int(axis_bits["axis5"])
    if slot["precedence"] == "operator_first":
        mid = operator_apply(before, family, axis5, chirality_sign, direction_sign)
        after = terrain_apply(mid, terrain_id, axis5, chirality_sign, direction_sign)
    else:
        mid = terrain_apply(before, terrain_id, axis5, chirality_sign, direction_sign)
        after = operator_apply(mid, family, axis5, chirality_sign, direction_sign)
    ledger = {
        "entry_type": "engine_64_stage_transition",
        "slot_index": slot["slot_index"],
        "matrix64_index": slot["matrix64_index"],
        "axis_bits": axis_bits,
        "engine_family": slot["engine_family"],
        "sheet": slot["sheet"],
        "direction": slot["direction"],
        "stage": slot["stage"],
        "stroke_index": slot["stroke_index"],
        "substage_index": slot["substage_index"],
        "readout": slot["readout"],
        "readout_discipline": slot["readout_discipline"],
        "active_operator": {
            "family": family,
            "signed_operator_id": slot["signed_operator_id"],
            "precedence": slot["precedence"],
            "axis_bits_source": "axis1_axis2_for_family_axis6_for_precedence",
        },
        "active_terrain": {
            "terrain_id": terrain_id,
            "stage": slot["stage"],
            "sheet": slot["sheet"],
            "axis_bits_source": "axis3_axis4_axis1_axis2_for_engine_direction_stage",
        },
        "state_before": round_vec(before),
        "state_mid": round_vec(mid),
        "state_after": round_vec(after),
        "delta_norm": round_float(float(np.linalg.norm(after - before))),
        "entropy_before": round_float(bloch_entropy(before)),
        "entropy_after": round_float(bloch_entropy(after)),
        "purity_before": round_float(bloch_purity(before)),
        "purity_after": round_float(bloch_purity(after)),
    }
    return after, ledger


def run_schedule(slots: list[dict[str, Any]], label: str, initial_state: np.ndarray | None = None) -> dict[str, Any]:
    state = np.asarray(PINNED_INITIAL_STATE if initial_state is None else initial_state, dtype=float)
    trajectory = []
    for slot in slots:
        state, row = apply_slot(state, slot)
        trajectory.append(row)
    signature_rows = [
        {
            "slot_index": row["slot_index"],
            "matrix64_index": row["matrix64_index"],
            "state_after": row["state_after"],
            "operator": row["active_operator"]["signed_operator_id"],
            "terrain": row["active_terrain"]["terrain_id"],
        }
        for row in trajectory
    ]
    return {
        "label": label,
        "slot_count": len(slots),
        "initial_state": round_vec(PINNED_INITIAL_STATE if initial_state is None else initial_state),
        "final_state": round_vec(state),
        "final_entropy": round_float(bloch_entropy(state)),
        "final_purity": round_float(bloch_purity(state)),
        "trajectory_signature_sha256": stable_sha256(signature_rows),
        "trajectory": trajectory,
    }


def slot_coordinate_consistency(slot: dict[str, Any]) -> dict[str, Any]:
    axis_bits = slot["axis_bits"]
    stroke = STROKE_BY_BITS[(axis_bits["axis1"], axis_bits["axis2"])]
    substage = SUBSTAGE_BY_BITS[(axis_bits["axis5"], axis_bits["axis6"])]
    stages, readouts = expected_stage_sequence(axis_bits["axis3"], axis_bits["axis4"])
    expected_stage = stages[int(stroke["stroke_index"])]
    expected_readout = readouts[int(stroke["stroke_index"])]
    expected_sheet = ENGINE_SPECS[axis_bits["axis3"]]["sheet"]
    expected_terrain = TERRAIN_REALIZATIONS[(expected_sheet, expected_stage)]
    expected_precedence = "operator_first" if axis_bits["axis6"] == 0 else "terrain_first"
    checks = {
        "operator_family_matches_axis1_axis2": slot["operator_family"] == stroke["operator_family"],
        "substage_matches_axis5_axis6": slot["substage_index"] == substage["substage_index"],
        "precedence_matches_axis6": slot["precedence"] == expected_precedence,
        "stage_matches_engine_direction_and_stroke": slot["stage"] == expected_stage,
        "terrain_matches_sheet_and_stage": slot["terrain_id"] == expected_terrain,
        "readout_matches_committed_discipline_row": slot["readout"] == expected_readout,
        "matrix64_index_matches_axis_bits": slot["matrix64_index"] == matrix64_index(axis_bits),
    }
    return {
        "slot_index": slot["slot_index"],
        "matrix64_index": slot["matrix64_index"],
        "axis_bits": axis_bits,
        "expected_operator_family": stroke["operator_family"],
        "actual_operator_family": slot["operator_family"],
        "expected_stage": expected_stage,
        "actual_stage": slot["stage"],
        "expected_terrain": expected_terrain,
        "actual_terrain": slot["terrain_id"],
        "expected_precedence": expected_precedence,
        "actual_precedence": slot["precedence"],
        "checks": checks,
        "pass": all(checks.values()),
    }


def l2(left: list[float] | np.ndarray, right: list[float] | np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(left, dtype=float) - np.asarray(right, dtype=float)))


def structural_solver_gates(values: dict[str, Any]) -> dict[str, Any]:
    z3_solver = z3.Solver()
    z_total = z3.Int("total_slots")
    z_type1 = z3.Int("type1_slots")
    z_type2 = z3.Int("type2_slots")
    z_unique = z3.Int("unique_coords")
    z_bad = z3.Int("bad_coordinate_rows")
    z_shuffle = z3.Int("shuffle_differs")
    z_erasure = z3.Int("erasure_differs")
    z_truncated = z3.Int("truncated_slots")
    z3_solver.add(z_total == int(values["total_slots"]))
    z3_solver.add(z_type1 == int(values["type1_slots"]))
    z3_solver.add(z_type2 == int(values["type2_slots"]))
    z3_solver.add(z_unique == int(values["unique_coordinate_count"]))
    z3_solver.add(z_bad == int(values["bad_coordinate_rows"]))
    z3_solver.add(z_shuffle == int(values["shuffle_differs"]))
    z3_solver.add(z_erasure == int(values["erasure_differs"]))
    z3_solver.add(z_truncated == int(values["truncated_slots"]))
    z3_goal = z3.And(
        z_total == 64,
        z_type1 == 32,
        z_type2 == 32,
        z_unique == 64,
        z_bad == 0,
        z_shuffle == 1,
        z_erasure == 1,
        z_truncated == 32,
    )
    z3_solver.add(z3.Not(z3_goal))
    z3_verdict = str(z3_solver.check()).lower()

    z3_control = z3.Solver()
    erased_unique = z3.Int("erased_unique_coords")
    z3_control.add(erased_unique == int(values["erased_unique_coordinate_count"]))
    z3_control.add(erased_unique < 64)
    z3_control_verdict = str(z3_control.check()).lower()

    cv = cvc5.Solver()
    cv.setLogic("QF_LIA")
    int_sort = cv.getIntegerSort()
    terms = {name: cv.mkConst(int_sort, f"cvc5_{name}") for name in values}

    def eq_int(name: str, number: int) -> Any:
        return cv.mkTerm(Kind.EQUAL, terms[name], cv.mkInteger(number))

    for key in (
        "total_slots",
        "type1_slots",
        "type2_slots",
        "unique_coordinate_count",
        "bad_coordinate_rows",
        "shuffle_differs",
        "erasure_differs",
        "truncated_slots",
    ):
        cv.assertFormula(eq_int(key, int(values[key])))
    cv_goal = cv.mkTerm(
        Kind.AND,
        eq_int("total_slots", 64),
        eq_int("type1_slots", 32),
        eq_int("type2_slots", 32),
        eq_int("unique_coordinate_count", 64),
        eq_int("bad_coordinate_rows", 0),
        eq_int("shuffle_differs", 1),
        eq_int("erasure_differs", 1),
        eq_int("truncated_slots", 32),
    )
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv_goal))
    cvc5_result = cv.checkSat()
    cvc5_verdict = "sat" if cvc5_result.isSat() else "unsat" if cvc5_result.isUnsat() else str(cvc5_result).lower()

    cv_control = cvc5.Solver()
    cv_control.setLogic("QF_LIA")
    cv_int = cv_control.getIntegerSort()
    cv_erased = cv_control.mkConst(cv_int, "cvc5_erased_unique_coords")
    cv_control.assertFormula(
        cv_control.mkTerm(Kind.EQUAL, cv_erased, cv_control.mkInteger(int(values["erased_unique_coordinate_count"])))
    )
    cv_control.assertFormula(cv_control.mkTerm(Kind.LT, cv_erased, cv_control.mkInteger(64)))
    cvc5_control_result = cv_control.checkSat()
    cvc5_control_verdict = (
        "sat"
        if cvc5_control_result.isSat()
        else "unsat"
        if cvc5_control_result.isUnsat()
        else str(cvc5_control_result).lower()
    )
    return {
        "z3": {
            "ran": True,
            "verdict": z3_verdict,
            "load_bearing": True,
            "identity": "computed schedule counts, coordinate consistency, and controls imply the Matrix64 full-run gate",
            "positive_case": "negating any required full-run gate is UNSAT after binding computed values",
            "erased_control_verdict": z3_control_verdict,
            "erased_control": "bit-coordinate-erased schedule has fewer than 64 unique realized coordinates",
        },
        "cvc5": {
            "ran": True,
            "verdict": cvc5_verdict,
            "load_bearing": True,
            "identity": "same computed Matrix64 full-run gate independently encoded in cvc5",
            "positive_case": "negating any required full-run gate is UNSAT after binding computed values",
            "erased_control_verdict": cvc5_control_verdict,
            "erased_control": "bit-coordinate-erased schedule has fewer than 64 unique realized coordinates",
        },
    }


def eng64_parent_context() -> dict[str, Any]:
    result = load_json(PARENT_PATHS["eng_64_julia_result"])
    return {
        "object_id": result.get("object_id"),
        "classification": result.get("classification"),
        "promotion_allowed": result.get("promotion_allowed"),
        "all_checks_passed": result.get("all_checks_passed"),
        "stage_count": result.get("stage_count"),
        "fingerprint_counts": result.get("fingerprint_counts"),
        "allowed_use": "hash-pinned parent context only; this packet computes a new stateful 64-slot trajectory and does not inherit the old final-density fingerprint claim",
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    schedule = build_schedule()
    consistency_rows = [slot_coordinate_consistency(slot) for slot in schedule]
    full = run_schedule(schedule, "full_type1_l_then_type2_r")

    shuffled_slots = list(schedule)
    rng = random.Random(RNG_SEED)
    rng.shuffle(shuffled_slots)
    shuffled = run_schedule(shuffled_slots, "shuffled_64_slot_control")

    truncated_slots = [slot for slot in schedule if slot["axis_bits"]["axis3"] == 0]
    truncated = run_schedule(truncated_slots, "truncated_type1_l_32_slot_boundary")

    erased_slots = [erase_slot_coordinates(slot) for slot in schedule]
    erased = run_schedule(erased_slots, "bit_coordinate_erasure_control")

    type1 = run_schedule([slot for slot in schedule if slot["axis_bits"]["axis3"] == 0], "type1_l_independent_half")
    type2 = run_schedule([slot for slot in schedule if slot["axis_bits"]["axis3"] == 1], "type2_r_independent_half")

    unique_coords = {tuple(slot["axis_bits"][f"axis{i}"] for i in range(1, 7)) for slot in schedule}
    erased_unique_coords = {tuple(slot["axis_bits"][f"axis{i}"] for i in range(1, 7)) for slot in erased_slots}
    type1_count = sum(1 for slot in schedule if slot["axis_bits"]["axis3"] == 0)
    type2_count = sum(1 for slot in schedule if slot["axis_bits"]["axis3"] == 1)
    bad_rows = sum(1 for row in consistency_rows if not row["pass"])
    shuffled_diff = l2(full["final_state"], shuffled["final_state"])
    erased_diff = l2(full["final_state"], erased["final_state"])
    truncated_diff = l2(full["final_state"], truncated["final_state"])
    lr_diff = l2(type1["final_state"], type2["final_state"])
    gate_values = {
        "total_slots": len(schedule),
        "type1_slots": type1_count,
        "type2_slots": type2_count,
        "unique_coordinate_count": len(unique_coords),
        "bad_coordinate_rows": bad_rows,
        "shuffle_differs": int(shuffled_diff > EPS),
        "erasure_differs": int(erased_diff > EPS),
        "truncated_slots": len(truncated_slots),
        "erased_unique_coordinate_count": len(erased_unique_coords),
    }
    solver_gates = structural_solver_gates(gate_values)
    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    all_pass = all(
        [
            len(schedule) == 64,
            type1_count == 32,
            type2_count == 32,
            len(unique_coords) == 64,
            bad_rows == 0,
            shuffled_diff > EPS,
            erased_diff > EPS,
            truncated_diff > EPS,
            lr_diff > EPS,
            len(truncated_slots) == 32,
            solver_gates["z3"]["verdict"] == "unsat",
            solver_gates["z3"]["erased_control_verdict"] == "sat",
            solver_gates["cvc5"]["verdict"] == "unsat",
            solver_gates["cvc5"]["erased_control_verdict"] == "sat",
            boundary_ok,
        ]
    )
    return {
        "schema_version": f"{SIM_ID}_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "generated_at": now_z(),
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "common_source_path": rel(COMMON_PATH),
        "common_source_sha256": sha256_file(COMMON_PATH),
        "result_path": rel(RESULT_PATH),
        "claim": "One realization-relative finite run of Type1-L then Type2-R through all 64 Matrix64 schedule slots, with per-slot state and coordinate ledger.",
        "claim_ceiling": "scratch_diagnostic; realization-relative schedule trajectory only; no source admission, no match-lane claim, no basin/subbasin claim",
        "allowed_claims": [
            "64 schedule slots computed on a pinned finite carrier",
            "32 slots per engine family under the declared Matrix64 coordinate schedule",
            "per-slot coordinate consistency rows computed",
            "Type1-L versus Type2-R full-run chirality difference computed on this carrier",
            "shuffled, truncated, and bit-coordinate-erasure controls computed",
        ],
        "disallowed_claims": [
            "source-admitted substage convention",
            "I Ching or hexagram matching claim",
            "64-subsubbasin, basin, or subbasin claim",
            "canonical Matrix64 admission",
            "physics, bridge, or axis-level admission",
        ],
        "fences": {
            "realization_relative_only": True,
            "source_admitted_substage_convention": False,
            "match_lane_claim": False,
            "basin_claim": False,
            "formal_admission_allowed": False,
        },
        "substage_realization": {
            "name": "v2_v3_cyclic_substage_realization_choice",
            "status": "UNPINNED",
            "realization_relative_only": True,
            "source_admitted": False,
            "substage_cycle": "axis5_axis6 ordered as (0,0),(0,1),(1,0),(1,1); substage wrap advances stroke/stage inside the declared schedule",
            "stage_wrap": "after four strokes, direction advances; after two directions, engine family advances from Type1-L to Type2-R",
            "registration_discipline": "cite this packet only as realization-relative evidence under the declared cyclic convention",
        },
        "parent_source_locks": parent_source_locks(),
        "eng_64_parent_context": eng64_parent_context(),
        "matrix64_schedule": {
            "factorization": "2 engine families x 2 directions(axis4) x 4 strokes(axis1xaxis2) x 4 substages(axis5xaxis6) = 64",
            "per_engine_family": "4 strokes x 4 substages x 2 directions = 32",
            "slot_order": "Type1-L first, then Type2-R; within each family: axis4 direction, stroke_index, substage_index",
            "strokes": STROKES,
            "substages": SUBSTAGES,
            "engine_specs": ENGINE_SPECS,
            "terrain_realizations": {f"{sheet}:{stage}": terrain for (sheet, stage), terrain in TERRAIN_REALIZATIONS.items()},
        },
        "pinned_carrier": {
            "carrier": "3-component Bloch vector inside unit ball",
            "initial_state": round_vec(PINNED_INITIAL_STATE),
            "initial_entropy": round_float(bloch_entropy(PINNED_INITIAL_STATE)),
            "initial_purity": round_float(bloch_purity(PINNED_INITIAL_STATE)),
            "clamp_rule": "states with norm above 0.999999 are projected back to radius 0.999999",
        },
        "coordinate_consistency": {
            "rows": consistency_rows,
            "bad_row_count": bad_rows,
            "all_rows_pass": bad_rows == 0,
        },
        "runs": {
            "full_64_slot_trajectory": full,
            "type1_l_independent_half": {
                key: value for key, value in type1.items() if key != "trajectory"
            },
            "type2_r_independent_half": {
                key: value for key, value in type2.items() if key != "trajectory"
            },
        },
        "type1_l_vs_type2_r_comparison": {
            "same_initial_state": True,
            "type1_l_final_state": type1["final_state"],
            "type2_r_final_state": type2["final_state"],
            "final_state_l2": round_float(lr_diff),
            "trajectory_signature_equal": type1["trajectory_signature_sha256"] == type2["trajectory_signature_sha256"],
            "chirality_difference_detected": lr_diff > EPS and type1["trajectory_signature_sha256"] != type2["trajectory_signature_sha256"],
        },
        "controls": {
            "shuffled_schedule_control": {
                "slot_count": shuffled["slot_count"],
                "rng_seed": RNG_SEED,
                "final_state_l2_vs_full": round_float(shuffled_diff),
                "trajectory_signature_equal_to_full": shuffled["trajectory_signature_sha256"] == full["trajectory_signature_sha256"],
                "pass": shuffled_diff > EPS and shuffled["trajectory_signature_sha256"] != full["trajectory_signature_sha256"],
            },
            "truncated_schedule_boundary": {
                "slot_count": truncated["slot_count"],
                "boundary": "32 slots = one engine family (Type1-L)",
                "final_state_l2_vs_full": round_float(truncated_diff),
                "pass": len(truncated_slots) == 32 and truncated_diff > EPS,
            },
            "bit_coordinate_erasure_control": {
                "slot_count": erased["slot_count"],
                "erasure_rule": "preserve slot count and engine family; erase axis1, axis2, axis4, axis5, axis6 to zero in active map decoding",
                "unique_coordinate_count_after_erasure": len(erased_unique_coords),
                "final_state_l2_vs_full": round_float(erased_diff),
                "trajectory_signature_equal_to_full": erased["trajectory_signature_sha256"] == full["trajectory_signature_sha256"],
                "pass": erased_diff > EPS and len(erased_unique_coords) < 64,
            },
        },
        "gate_values": gate_values,
        "crossover_proofs": solver_gates,
        "TOOL_MANIFEST": {
            "numpy": {
                "used": True,
                "reason": "load-bearing finite Bloch-vector carrier, affine terrain/operator maps, norms, entropy/purity readouts, and trajectory controls",
            },
            "z3": {
                "used": True,
                "reason": "load-bearing computed-value SMT gate for 64-slot coordinate counts and controls with erased-coordinate SAT control",
            },
            "cvc5": {
                "used": True,
                "reason": "load-bearing independent computed-value SMT gate for the same Matrix64 schedule facts",
            },
            "builder_audit_boundary": {
                "used": True,
                "reason": "load-bearing builder/auditor file-boundary gate; builder must not author audit_verdict.md",
            },
            "python_stdlib": {
                "used": True,
                "reason": "supportive JSON, hashing, deterministic shuffle, timestamps, and path handling",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "numpy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "builder_audit_boundary": "load_bearing",
            "python_stdlib": "supportive",
        },
        "builder_audit_boundary": {
            "helper_path": "scripts/builder_audit_boundary.py",
            "no_builder_audit_verdict": boundary_ok,
            "no_builder_audit_verdict_envelope_gate": boundary_ok,
            "audit_verdict_path": rel(SIM_DIR / "audit_verdict.md"),
        },
        "no_builder_audit_verdict": boundary_ok,
        "no_builder_audit_verdict_envelope_gate": boundary_ok,
    }


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(stable_json({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
