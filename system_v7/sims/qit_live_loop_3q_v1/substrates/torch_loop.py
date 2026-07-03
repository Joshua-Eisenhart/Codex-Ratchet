"""QUARANTINE_EXPLORATORY: PyTorch substrate for qit_live_loop_3q_v1.

classification='scratch_diagnostic'; promotion_allowed=false.

Runs the full per-tick loop in PyTorch complex128: next-tick chosen-stage
prediction, Lüders conditioning on q0, hill relaxation, and the reactive-risk
+ entropy cost surrogate recorded under efe_scores_16, a schema-stable legacy
field name; the quantity is the cost surrogate, not active-inference EFE.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from common_3q import (
    CLASSIFICATION,
    ACTION_TIE_TOL,
    ENGINES_DIR,
    EPS,
    PROMOTION_ALLOWED,
    SCHEMA,
    STREAM_ID,
    default_output_for_fixture,
    load_module,
    read_fixture,
    signal_povm_from_record,
    write_jsonl,
)

torch_engine = load_module("cr_torch_engine_3q_loop", ENGINES_DIR / "torch_engine_3q.py")
torch = torch_engine.torch

I2 = torch_engine.I2
I8 = torch_engine.I8
SX = torch_engine.sx
SY = torch_engine.sy
SZ = torch_engine.sz
DT = torch_engine.dt
DEV = torch_engine.dev


def sym_norm(rho):
    out = 0.5 * (rho + rho.conj().T)
    tr = torch.trace(out).real
    if float(torch.abs(tr)) < EPS:
        raise ValueError("density trace collapsed to zero")
    return (out / tr).to(DT)


def psd_floor(rho):
    clean = sym_norm(rho)
    vals, vecs = torch.linalg.eigh(clean)
    vals = torch.clamp(vals.real, min=EPS).to(DT)
    return sym_norm(vecs @ torch.diag(vals) @ vecs.conj().T)


def log_hermitian(a):
    clean = 0.5 * (a + a.conj().T)
    vals, vecs = torch.linalg.eigh(clean)
    return vecs @ torch.diag(torch.log(vals.real).to(DT)) @ vecs.conj().T


def relative_entropy_bits(obs, belief):
    obs = sym_norm(obs)
    belief = psd_floor(belief)
    value = torch.trace(obs @ ((log_hermitian(obs + EPS * I8) - log_hermitian(belief)) / math.log(2.0)))
    return float(value.real)


def von_neumann_entropy_bits(rho):
    vals = torch.linalg.eigvalsh(sym_norm(rho)).real
    vals = vals[vals > EPS]
    return float(-torch.sum(vals * torch.log2(vals)))


def reactive_risk_entropy_cost_surrogate(pred, belief, preference):
    pred = sym_norm(pred)
    risk = relative_entropy_bits(pred, preference)
    return float(risk - (von_neumann_entropy_bits(belief) - von_neumann_entropy_bits(pred)))


def choose_action_index(scores):
    values = [float(x) for x in scores]
    minimum = min(values)
    for idx, value in enumerate(values):
        if value <= minimum + ACTION_TIE_TOL:
            return idx
    raise RuntimeError("unreachable action tie-break state")


def build_stage_supers():
    stages = []
    for t in range(8):
        terrain = torch.linalg.matrix_exp(torch_engine.T_FLOW * torch_engine.terrain_super(t))
        for op_name in torch_engine.NATIVE[t]:
            stage = torch_engine.op_super(op_name) @ terrain
            stages.append(stage.to(DT))
    return stages


def build_hill_store_super():
    h = torch_engine.on0((SX + SY + SZ) / math.sqrt(3.0)) + torch_engine.J_COUP * (torch_engine.ZZ01 + torch_engine.ZZ12)
    gen = torch_engine.G * torch_engine.sC(h) + torch_engine.KAP * torch_engine.sD(torch_engine.on0(SZ))
    return torch.linalg.matrix_exp(0.15 * gen).to(DT)


def apply_super(superop, rho):
    return sym_norm(torch_engine.unvec(superop @ torch_engine.vec(rho)))


def obs_density_from_outcome(outcome: int):
    projector = torch.tensor([[1, 0], [0, 0]], dtype=DT, device=DEV) if outcome == 0 else torch.tensor([[0, 0], [0, 1]], dtype=DT, device=DEV)
    return torch_engine.kron3(projector, 0.5 * I2, 0.5 * I2)


def q0_projector_from_outcome(outcome: int):
    projector = torch.tensor([[1, 0], [0, 0]], dtype=DT, device=DEV) if outcome == 0 else torch.tensor([[0, 0], [0, 1]], dtype=DT, device=DEV)
    return torch_engine.kron3(projector, I2, I2)


def luders_condition_q0(rho, outcome: int):
    projector = q0_projector_from_outcome(outcome)
    post = projector @ rho @ projector.conj().T
    prob = float(torch.trace(post).real)
    if prob < EPS:
        raise ValueError(f"Lüders conditioning probability collapsed for outcome {outcome}")
    return sym_norm(post / prob)


def q0_reduced(rho):
    reduced = torch.zeros((2, 2), dtype=DT, device=DEV)
    for a in range(2):
        for b in range(2):
            value = torch.tensor(0.0 + 0.0j, dtype=DT, device=DEV)
            for q1 in range(2):
                for q2 in range(2):
                    i = (a << 2) | (q1 << 1) | q2
                    j = (b << 2) | (q1 << 1) | q2
                    value = value + rho[i, j]
            reduced[a, b] = value
    return sym_norm(reduced)


def belief_bloch_q0(rho):
    reduced = q0_reduced(rho)
    return [float(torch.trace(reduced @ s).real) for s in (SX, SY, SZ)]


def belief_pauli_63(rho):
    return [float(torch.trace(rho @ p).real) for p in torch_engine.PMATS]


def stage_metadata():
    return [{"t": int(t), "op": str(op_name)} for t in range(8) for op_name in torch_engine.NATIVE[t]]


def run_records(fixture, stage_supers, precompute_seconds):
    stages = stage_metadata()
    if len(stage_supers) != 16:
        raise ValueError(f"torch_loop precomputed {len(stage_supers)} stage channels, expected 16")
    hill = build_hill_store_super()
    pending_stage_super = torch.eye(64, dtype=DT, device=DEV)
    belief = torch.eye(8, dtype=DT, device=DEV) / 8.0
    rows = []
    started = time.perf_counter()
    for rec in fixture["ticks"]:
        tick = int(rec["tick"])
        outcome = int(rec["outcome"])
        predicted = apply_super(pending_stage_super, belief)
        preference = apply_super(hill, predicted)
        obs = obs_density_from_outcome(outcome)
        surprise = relative_entropy_bits(obs, predicted)
        conditioned = luders_condition_q0(predicted, outcome)
        fe_gradient = surprise - relative_entropy_bits(obs, conditioned)
        belief = apply_super(hill, conditioned)
        scores = [reactive_risk_entropy_cost_surrogate(apply_super(stage, belief), belief, preference) for stage in stage_supers]
        chosen = choose_action_index(scores)
        pending_stage_super = stage_supers[chosen]
        rows.append(
            {
                "tick": tick,
                "t_iso": rec["t_iso"],
                "schema": SCHEMA,
                "stream_id": STREAM_ID,
                "substrate": "torch_loop",
                "belief_bloch": belief_bloch_q0(belief),
                "belief_pauli_63": belief_pauli_63(belief),
                "surprise_bits": surprise,
                "fe_gradient": fe_gradient,
                "chosen_action_index": chosen,
                "chosen_stage": stages[chosen],
                "efe_scores_16": [float(x) for x in scores],
                "world_segment": rec["world_segment"],
                "signal_povm": signal_povm_from_record(rec),
                "sampled_outcome": outcome,
                "classification": CLASSIFICATION,
                "promotion_allowed": PROMOTION_ALLOWED,
            }
        )
    loop_seconds = time.perf_counter() - started
    return rows, {
        "substrate": "torch_loop",
        "ticks": len(rows),
        "precompute_seconds": precompute_seconds,
        "loop_seconds": loop_seconds,
        "total_seconds": precompute_seconds + loop_seconds,
        "packages_used": ["torch"],
        "aligned_packages_load_bearing": ["torch.linalg"],
        "reads_peer_result": False,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run PyTorch qit_live_loop_3q_v1 substrate")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or default_output_for_fixture(args.fixture, "torch_loop")
    fixture = read_fixture(args.fixture)
    started = time.perf_counter()
    stage_supers = build_stage_supers()
    precompute_seconds = time.perf_counter() - started
    rows, metrics = run_records(fixture, stage_supers, precompute_seconds)
    write_jsonl(out, rows)
    metrics["output"] = str(out)
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()
