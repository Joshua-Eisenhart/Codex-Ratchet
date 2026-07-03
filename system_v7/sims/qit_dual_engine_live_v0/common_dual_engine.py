"""QUARANTINE_EXPLORATORY: shared mechanics for qit_dual_engine_live_v0.

classification='scratch_diagnostic'; promotion_allowed=false.

This reuses qit_live_loop_3q_v1 loop mechanics: pending-stage prediction,
Lüders conditioning on the shared q0 outcome, hill relaxation, persistence-prior
EFE surrogate, and action feedback. It narrows action spaces to the pinned
eps-sheet direct/conjugated partition.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
from scipy.linalg import expm

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[2]
ENGINES_DIR = REPO_ROOT / "system_v7" / "constraint_core" / "engines"
RESULTS_DIR = BASE_DIR / "results" / "live_300"

SCHEMA = "cr.qit_dual_engine_live_v0.tick.v1"
STREAM_ID = "qit_dual_engine_live_v0.live_300"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
QUARANTINE = "QUARANTINE_EXPLORATORY"
EPS = 1e-12
ACTION_TIE_TOL = 1e-12
MEMORY_READ_TICKS = (0, 50, 100, 150, 200, 250, 299)

I2 = np.eye(2, dtype=np.complex128)
I8 = np.eye(8, dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)
PAULI_1Q = {"I": I2, "X": SX, "Y": SY, "Z": SZ}
PAULI_STRINGS = ["".join(p) for p in itertools.product("IXYZ", repeat=3) if set(p) != {"I"}]
PAULI_MATS = None

SHEET_STAGE_DEFS: dict[str, list[dict]] = {
    "D": [
        {"sheet": "eps-sheet direct", "engine_id": "D", "sheet_action_index": 0, "global_stage_id": 0, "terrain": 0, "op": "Ti", "v1_native_stage_index": 0},
        {"sheet": "eps-sheet direct", "engine_id": "D", "sheet_action_index": 1, "global_stage_id": 1, "terrain": 0, "op": "Fi", "v1_native_stage_index": 1},
        {"sheet": "eps-sheet direct", "engine_id": "D", "sheet_action_index": 2, "global_stage_id": 2, "terrain": 1, "op": "Ti", "v1_native_stage_index": 2},
        {"sheet": "eps-sheet direct", "engine_id": "D", "sheet_action_index": 3, "global_stage_id": 3, "terrain": 1, "op": "Fi", "v1_native_stage_index": 3},
        {"sheet": "eps-sheet direct", "engine_id": "D", "sheet_action_index": 4, "global_stage_id": 4, "terrain": 2, "op": "Ti", "v1_native_stage_index": None},
        {"sheet": "eps-sheet direct", "engine_id": "D", "sheet_action_index": 5, "global_stage_id": 5, "terrain": 2, "op": "Fi", "v1_native_stage_index": None},
        {"sheet": "eps-sheet direct", "engine_id": "D", "sheet_action_index": 6, "global_stage_id": 6, "terrain": 3, "op": "Ti", "v1_native_stage_index": None},
        {"sheet": "eps-sheet direct", "engine_id": "D", "sheet_action_index": 7, "global_stage_id": 7, "terrain": 3, "op": "Fi", "v1_native_stage_index": None},
    ],
    "C": [
        {"sheet": "eps-sheet conjugated", "engine_id": "C", "sheet_action_index": 0, "global_stage_id": 8, "terrain": 4, "op": "Te", "v1_native_stage_index": None},
        {"sheet": "eps-sheet conjugated", "engine_id": "C", "sheet_action_index": 1, "global_stage_id": 9, "terrain": 4, "op": "Fe", "v1_native_stage_index": None},
        {"sheet": "eps-sheet conjugated", "engine_id": "C", "sheet_action_index": 2, "global_stage_id": 10, "terrain": 5, "op": "Te", "v1_native_stage_index": None},
        {"sheet": "eps-sheet conjugated", "engine_id": "C", "sheet_action_index": 3, "global_stage_id": 11, "terrain": 5, "op": "Fe", "v1_native_stage_index": None},
        {"sheet": "eps-sheet conjugated", "engine_id": "C", "sheet_action_index": 4, "global_stage_id": 12, "terrain": 6, "op": "Te", "v1_native_stage_index": 12},
        {"sheet": "eps-sheet conjugated", "engine_id": "C", "sheet_action_index": 5, "global_stage_id": 13, "terrain": 6, "op": "Fe", "v1_native_stage_index": 13},
        {"sheet": "eps-sheet conjugated", "engine_id": "C", "sheet_action_index": 6, "global_stage_id": 14, "terrain": 7, "op": "Te", "v1_native_stage_index": 14},
        {"sheet": "eps-sheet conjugated", "engine_id": "C", "sheet_action_index": 7, "global_stage_id": 15, "terrain": 7, "op": "Fe", "v1_native_stage_index": 15},
    ],
}


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def ensure_targets_3q() -> None:
    target = ENGINES_DIR / "targets_3q.json"
    if target.exists():
        return
    oracle = load_module("cr_oracle_targets_3q_dual_build", ENGINES_DIR / "oracle_targets_3q.py")
    oracle.main()


def kron3(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    return np.kron(np.kron(a, b), c)


def on0(a: np.ndarray) -> np.ndarray:
    return kron3(a, I2, I2)


def vec(rho: np.ndarray) -> np.ndarray:
    return rho.T.reshape(-1)


def unvec(v: np.ndarray) -> np.ndarray:
    return v.reshape(8, 8).T


def sym_norm(rho: np.ndarray) -> np.ndarray:
    out = 0.5 * (rho + rho.conj().T)
    tr = np.trace(out).real
    if abs(tr) < EPS:
        raise ValueError("density trace collapsed to zero")
    return (out / tr).astype(np.complex128, copy=False)


def psd_floor(rho: np.ndarray) -> np.ndarray:
    rho = sym_norm(rho)
    ev, basis = np.linalg.eigh(rho)
    ev = np.clip(ev.real, EPS, None)
    return sym_norm(basis @ np.diag(ev) @ basis.conj().T)


def log_hermitian(a: np.ndarray) -> np.ndarray:
    clean = 0.5 * (a + a.conj().T)
    ev, basis = np.linalg.eigh(clean)
    return basis @ np.diag(np.log(ev.real)) @ basis.conj().T


def relative_entropy_bits(obs: np.ndarray, belief: np.ndarray) -> float:
    obs = sym_norm(obs)
    belief = psd_floor(belief)
    value = np.trace(obs @ ((log_hermitian(obs + EPS * I8) - log_hermitian(belief)) / np.log(2)))
    return float(np.real(value))


def von_neumann_entropy_bits(rho: np.ndarray) -> float:
    ev = np.linalg.eigvalsh(sym_norm(rho))
    ev = ev[ev > EPS]
    return float(-np.sum(ev * np.log2(ev)))


def reactive_risk_entropy_cost_surrogate(pred: np.ndarray, belief: np.ndarray, preference: np.ndarray) -> float:
    risk = relative_entropy_bits(pred, preference)
    pred = sym_norm(pred)
    return float(risk - (von_neumann_entropy_bits(belief) - von_neumann_entropy_bits(pred)))


def choose_action_index(scores: Iterable[float]) -> int:
    values = [float(x) for x in scores]
    minimum = min(values)
    for idx, value in enumerate(values):
        if value <= minimum + ACTION_TIE_TOL:
            return idx
    raise RuntimeError("unreachable action tie-break state")


def pauli_mats() -> list[np.ndarray]:
    global PAULI_MATS
    if PAULI_MATS is None:
        PAULI_MATS = [kron3(PAULI_1Q[s[0]], PAULI_1Q[s[1]], PAULI_1Q[s[2]]) for s in PAULI_STRINGS]
    return PAULI_MATS


def belief_pauli_63(rho: np.ndarray) -> list[float]:
    return [float(np.trace(rho @ p).real) for p in pauli_mats()]


def obs_density_from_outcome(outcome: int) -> np.ndarray:
    projector = np.array([[1, 0], [0, 0]], dtype=np.complex128) if outcome == 0 else np.array([[0, 0], [0, 1]], dtype=np.complex128)
    return kron3(projector, 0.5 * I2, 0.5 * I2)


def q0_projector_from_outcome(outcome: int) -> np.ndarray:
    projector = np.array([[1, 0], [0, 0]], dtype=np.complex128) if outcome == 0 else np.array([[0, 0], [0, 1]], dtype=np.complex128)
    return kron3(projector, I2, I2)


def luders_condition_q0(rho: np.ndarray, outcome: int) -> np.ndarray:
    projector = q0_projector_from_outcome(outcome)
    post = projector @ rho @ projector.conj().T
    prob = np.trace(post).real
    if prob < EPS:
        raise ValueError(f"Lüders conditioning probability collapsed for outcome {outcome}")
    return sym_norm(post / prob)


def signal_povm_from_record(record: dict) -> dict:
    return {"p0": float(record["signal_povm"]["p0"]), "p1": float(record["signal_povm"]["p1"])}


def super_from_density_map(fn: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    cols = []
    for idx in range(64):
        basis_vec = np.zeros(64, dtype=np.complex128)
        basis_vec[idx] = 1.0
        cols.append(vec(fn(unvec(basis_vec))))
    return np.stack(cols, axis=1).astype(np.complex128)


def build_hill_store_super() -> np.ndarray:
    ensure_targets_3q()
    oracle = load_module("cr_oracle_targets_3q_dual_hill", ENGINES_DIR / "oracle_targets_3q.py")
    zz01 = oracle.kron3(oracle.sz, oracle.sz, oracle.I2)
    zz12 = oracle.kron3(oracle.I2, oracle.sz, oracle.sz)
    h = oracle.on0((oracle.sx + oracle.sy + oracle.sz) / np.sqrt(3.0)) + oracle.J_COUP * (zz01 + zz12)

    def x(rho: np.ndarray) -> np.ndarray:
        return oracle.G * (-1j * (h @ rho - rho @ h)) + oracle.KAP * oracle.D(oracle.on0(oracle.sz), rho)

    return expm(0.15 * super_from_density_map(x))


def apply_super(superop: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return sym_norm(unvec(superop @ vec(rho)))


def trace_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(0.5 * np.sum(np.linalg.svd(a - b, compute_uv=False)))


def spinor_step(psi: np.ndarray, op_name: str) -> np.ndarray:
    if op_name == "Fi":
        u = expm(-1j * (np.pi / 2.0) / 2.0 * SY)
        return u @ psi
    if op_name == "Fe":
        u = expm(+1j * (np.pi / 2.0) / 2.0 * SY)
        return u @ psi
    return psi


def spinor_bit_fidelity(psi: np.ndarray, target: np.ndarray) -> float:
    overlap = float(np.real(np.vdot(target, psi)))
    return float(np.clip((1.0 + overlap) / 2.0, 0.0, 1.0))


def engine_tick(state: dict, rec: dict, hill: np.ndarray, stage_supers: list[np.ndarray], stage_defs: list[dict]) -> dict:
    predicted = apply_super(state["pending"], state["belief"])
    preference = apply_super(hill, predicted)
    obs = obs_density_from_outcome(int(rec["outcome"]))
    surprise = relative_entropy_bits(obs, predicted)
    conditioned = luders_condition_q0(predicted, int(rec["outcome"]))
    fe_gradient = surprise - relative_entropy_bits(obs, conditioned)
    belief = apply_super(hill, conditioned)
    scores = [reactive_risk_entropy_cost_surrogate(apply_super(stage, belief), belief, preference) for stage in stage_supers]
    chosen = choose_action_index(scores)
    stage_def = stage_defs[chosen]
    state["belief"] = belief
    state["pending"] = stage_supers[chosen]
    state["memory"] = spinor_step(state["memory"], stage_def["op"])
    return {
        "predicted": predicted,
        "belief": belief,
        "surprise_bits": surprise,
        "fe_gradient": fe_gradient,
        "entropy_bits": von_neumann_entropy_bits(belief),
        "scores": scores,
        "chosen_action_index": chosen,
        "stage_def": stage_def,
        "memory_bit_fidelity": spinor_bit_fidelity(state["memory"], state["memory_target"]),
    }


def row_from_tick(substrate: str, rec: dict, engine_id: str, tick_result: dict, gap_trace: float, gap_surprise: float) -> dict:
    stage_def = tick_result["stage_def"]
    return {
        "tick": int(rec["tick"]),
        "t_iso": rec["t_iso"],
        "schema": SCHEMA,
        "stream_id": STREAM_ID,
        "substrate": substrate,
        "engine_id": engine_id,
        "sheet": stage_def["sheet"],
        "belief_pauli_63": belief_pauli_63(tick_result["belief"]),
        "surprise_bits": float(tick_result["surprise_bits"]),
        "fe_gradient": float(tick_result["fe_gradient"]),
        "entropy_bits": float(tick_result["entropy_bits"]),
        "efe_scores_8": [float(x) for x in tick_result["scores"]],
        "chosen_action_index": int(tick_result["chosen_action_index"]),
        "chosen_global_stage_id": int(stage_def["global_stage_id"]),
        "chosen_stage": stage_def,
        "sheet_gap_trace_distance": float(gap_trace),
        "sheet_gap_abs_surprise_delta": float(gap_surprise),
        "memory_bit_fidelity": float(tick_result["memory_bit_fidelity"]),
        "memory_read_tick": int(rec["tick"]) in MEMORY_READ_TICKS,
        "world_segment": rec["world_segment"],
        "signal_povm": signal_povm_from_record(rec),
        "sampled_outcome": int(rec["outcome"]),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "quarantine": QUARANTINE,
    }


def run_records(
    fixture: dict,
    sheet_stage_supers: dict[str, list[np.ndarray]],
    substrate: str,
    precompute_seconds: float,
) -> tuple[dict[str, list[dict]], dict]:
    for engine_id in ("D", "C"):
        if len(sheet_stage_supers.get(engine_id, [])) != 8:
            raise ValueError(f"{substrate} precomputed {engine_id} {len(sheet_stage_supers.get(engine_id, []))} stages, expected 8")
    hill = build_hill_store_super()
    states = {
        "D": {"belief": I8 / 8.0, "pending": np.eye(64, dtype=np.complex128), "memory": np.array([1.0, 0.0], dtype=np.complex128), "memory_target": np.array([1.0, 0.0], dtype=np.complex128)},
        "C": {"belief": I8 / 8.0, "pending": np.eye(64, dtype=np.complex128), "memory": np.array([1.0, 0.0], dtype=np.complex128), "memory_target": np.array([1.0, 0.0], dtype=np.complex128)},
    }
    rows = {"D": [], "C": []}
    memory_reads: dict[str, dict[str, float]] = {"D": {}, "C": {}}
    started = time.perf_counter()
    for rec in fixture["ticks"]:
        d = engine_tick(states["D"], rec, hill, sheet_stage_supers["D"], SHEET_STAGE_DEFS["D"])
        c = engine_tick(states["C"], rec, hill, sheet_stage_supers["C"], SHEET_STAGE_DEFS["C"])
        gap_trace = trace_distance(d["belief"], c["belief"])
        gap_surprise = abs(d["surprise_bits"] - c["surprise_bits"])
        rows["D"].append(row_from_tick(substrate, rec, "D", d, gap_trace, gap_surprise))
        rows["C"].append(row_from_tick(substrate, rec, "C", c, gap_trace, gap_surprise))
        if int(rec["tick"]) in MEMORY_READ_TICKS:
            memory_reads["D"][str(int(rec["tick"]))] = float(d["memory_bit_fidelity"])
            memory_reads["C"][str(int(rec["tick"]))] = float(c["memory_bit_fidelity"])
    loop_seconds = time.perf_counter() - started
    return rows, {
        "substrate": substrate,
        "ticks": len(rows["D"]),
        "precompute_seconds": precompute_seconds,
        "loop_seconds": loop_seconds,
        "total_seconds": precompute_seconds + loop_seconds,
        "memory_reads": memory_reads,
    }


def read_fixture(path: Path) -> dict:
    with path.open() as fh:
        fixture = json.load(fh)
    if fixture.get("classification") != CLASSIFICATION or fixture.get("promotion_allowed") is not PROMOTION_ALLOWED:
        raise ValueError(f"fixture {path} has wrong classification/promotion boundary")
    return fixture


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def run_substrate_cli(substrate: str, build_sheet_stage_supers: Callable[[], dict[str, list[np.ndarray]]]) -> None:
    parser = argparse.ArgumentParser(description=f"Run {substrate} qit_dual_engine_live_v0 substrate")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    out_dir = args.out_dir or args.fixture.resolve().parent
    fixture = read_fixture(args.fixture)
    started = time.perf_counter()
    sheet_supers = build_sheet_stage_supers()
    precompute_seconds = time.perf_counter() - started
    rows, metrics = run_records(fixture, sheet_supers, substrate, precompute_seconds)
    outputs = {}
    for engine_id, engine_rows in rows.items():
        out = out_dir / f"{substrate}_engine_{engine_id}.jsonl"
        write_jsonl(out, engine_rows)
        outputs[engine_id] = str(out)
    metrics["outputs"] = outputs
    print(json.dumps(metrics, sort_keys=True))


def deterministic_iso(tick: int) -> str:
    base = datetime(2026, 7, 4, tzinfo=timezone.utc)
    return (base + timedelta(seconds=tick)).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_float(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError(f"non-finite float {value!r}")
    return float(value)
