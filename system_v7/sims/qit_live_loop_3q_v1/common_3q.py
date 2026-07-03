"""QUARANTINE_EXPLORATORY: shared NumPy 3q live-loop mechanics.

classification='scratch_diagnostic'; promotion_allowed=false.

belief_bloch is the reduced q0/signal-qubit projection of the 3q belief state,
not the full 3q state. The full 3q state is emitted as belief_pauli_63.

Belief updates use Lüders conditioning on the q0 projective outcome + hill
relaxation channel. surprise_bits is an EPS-regularized Umegaki surrogate
(psd_floor on the reference plus logm(obs + EPS I)), not exact relative entropy.
efe_scores_16 is a schema-stable legacy field name; the quantity is the cost
surrogate, not active-inference EFE. It is a reactive-risk + entropy cost
surrogate with persistence-prior preference and no ambiguity/epistemic term.
signal_povm is fixture metadata echoed for audit, not used in inference.
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

SCHEMA = "cr.qit_live_loop_3q_v1.tick.v1"
STREAM_ID = "qit_live_loop_3q_v1.live_300"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
EPS = 1e-12
ACTION_TIE_TOL = 1e-12

I2 = np.eye(2, dtype=np.complex128)
I8 = np.eye(8, dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)
PAULI_1Q = {"I": I2, "X": SX, "Y": SY, "Z": SZ}
PAULI_STRINGS = ["".join(p) for p in itertools.product("IXYZ", repeat=3) if set(p) != {"I"}]
PAULI_MATS = None


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
    oracle = load_module("cr_oracle_targets_3q_build", ENGINES_DIR / "oracle_targets_3q.py")
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
    out = out / tr
    return out.astype(np.complex128, copy=False)


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
    return risk - (von_neumann_entropy_bits(belief) - von_neumann_entropy_bits(pred))


def choose_action_index(scores: Iterable[float]) -> int:
    values = [float(x) for x in scores]
    minimum = min(values)
    for idx, value in enumerate(values):
        if value <= minimum + ACTION_TIE_TOL:
            return idx
    raise RuntimeError("unreachable action tie-break state")


def q0_reduced(rho: np.ndarray) -> np.ndarray:
    reduced = np.zeros((2, 2), dtype=np.complex128)
    for a in range(2):
        for b in range(2):
            for q1 in range(2):
                for q2 in range(2):
                    i = (a << 2) | (q1 << 1) | q2
                    j = (b << 2) | (q1 << 1) | q2
                    reduced[a, b] += rho[i, j]
    return sym_norm(reduced)


def belief_bloch_q0(rho: np.ndarray) -> list[float]:
    reduced = q0_reduced(rho)
    return [float(np.trace(reduced @ s).real) for s in (SX, SY, SZ)]


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


def stage_metadata() -> list[dict]:
    ensure_targets_3q()
    oracle = load_module("cr_oracle_targets_3q_meta", ENGINES_DIR / "oracle_targets_3q.py")
    stages = []
    for t in range(8):
        for op_name in oracle.NATIVE[t]:
            stages.append({"t": int(t), "op": str(op_name)})
    return stages


def build_hill_store_super() -> np.ndarray:
    ensure_targets_3q()
    oracle = load_module("cr_oracle_targets_3q_hill", ENGINES_DIR / "oracle_targets_3q.py")
    zz01 = oracle.kron3(oracle.sz, oracle.sz, oracle.I2)
    zz12 = oracle.kron3(oracle.I2, oracle.sz, oracle.sz)
    h = oracle.on0((oracle.sx + oracle.sy + oracle.sz) / np.sqrt(3.0)) + oracle.J_COUP * (zz01 + zz12)

    def x(rho: np.ndarray) -> np.ndarray:
        return oracle.G * (-1j * (h @ rho - rho @ h)) + oracle.KAP * oracle.D(oracle.on0(oracle.sz), rho)

    return expm(0.15 * super_from_density_map(x))


def apply_super(superop: np.ndarray, rho: np.ndarray) -> np.ndarray:
    return sym_norm(unvec(superop @ vec(rho)))


def run_records(
    fixture: dict,
    stage_supers: Iterable[np.ndarray],
    substrate: str,
    precompute_seconds: float,
) -> tuple[list[dict], dict]:
    stages = stage_metadata()
    stage_supers = [np.asarray(s, dtype=np.complex128) for s in stage_supers]
    if len(stage_supers) != 16:
        raise ValueError(f"{substrate} precomputed {len(stage_supers)} stage channels, expected 16")

    hill = build_hill_store_super()
    pending_stage_super = np.eye(64, dtype=np.complex128)
    belief = I8 / 8.0
    rows = []
    started = time.perf_counter()
    for rec in fixture["ticks"]:
        tick = int(rec["tick"])
        predicted = apply_super(pending_stage_super, belief)
        preference = apply_super(hill, predicted)
        obs = obs_density_from_outcome(int(rec["outcome"]))
        surprise = relative_entropy_bits(obs, predicted)
        conditioned = luders_condition_q0(predicted, int(rec["outcome"]))
        fe_gradient = surprise - relative_entropy_bits(obs, conditioned)
        belief = apply_super(hill, conditioned)

        scores = [reactive_risk_entropy_cost_surrogate(apply_super(stage, belief), belief, preference) for stage in stage_supers]
        chosen = choose_action_index(scores)
        stage = stages[chosen]
        pending_stage_super = stage_supers[chosen]
        rows.append(
            {
                "tick": tick,
                "t_iso": rec["t_iso"],
                "schema": SCHEMA,
                "stream_id": STREAM_ID,
                "substrate": substrate,
                "belief_bloch": belief_bloch_q0(belief),
                "belief_pauli_63": belief_pauli_63(belief),
                "surprise_bits": surprise,
                "fe_gradient": fe_gradient,
                "chosen_action_index": chosen,
                "chosen_stage": stage,
                "efe_scores_16": [float(x) for x in scores],
                "world_segment": rec["world_segment"],
                "signal_povm": signal_povm_from_record(rec),
                "sampled_outcome": int(rec["outcome"]),
                "classification": CLASSIFICATION,
                "promotion_allowed": PROMOTION_ALLOWED,
            }
        )
    runtime = time.perf_counter() - started
    return rows, {
        "substrate": substrate,
        "ticks": len(rows),
        "precompute_seconds": precompute_seconds,
        "loop_seconds": runtime,
        "total_seconds": precompute_seconds + runtime,
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


def default_output_for_fixture(fixture_path: Path, name: str) -> Path:
    return fixture_path.resolve().parent / f"{name}.jsonl"


def run_substrate_cli(substrate: str, build_stage_supers: Callable[[], list[np.ndarray]]) -> None:
    parser = argparse.ArgumentParser(description=f"Run {substrate} qit_live_loop_3q_v1 substrate")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or default_output_for_fixture(args.fixture, substrate)
    fixture = read_fixture(args.fixture)
    started = time.perf_counter()
    stage_supers = build_stage_supers()
    precompute_seconds = time.perf_counter() - started
    rows, metrics = run_records(fixture, stage_supers, substrate, precompute_seconds)
    write_jsonl(out, rows)
    metrics["output"] = str(out)
    print(json.dumps(metrics, sort_keys=True))


def deterministic_iso(tick: int) -> str:
    base = datetime(2026, 7, 3, tzinfo=timezone.utc)
    return (base + timedelta(seconds=tick)).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_float(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError(f"non-finite float {value!r}")
    return float(value)
