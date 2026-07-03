"""QUARANTINE_EXPLORATORY: JAX substrate for qit_live_loop_3q_v1.

classification='scratch_diagnostic'; promotion_allowed=false.

Runs the full per-tick loop in JAX arrays: next-tick chosen-stage prediction,
Lüders conditioning on q0, hill relaxation, and the reactive-risk + entropy
cost surrogate recorded under efe_scores_16, a schema-stable legacy field name;
the quantity is the cost surrogate, not active-inference EFE.
"""
from __future__ import annotations

import json
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
    I2 as NP_I2,
    PROMOTION_ALLOWED,
    SCHEMA,
    STREAM_ID,
    default_output_for_fixture,
    load_module,
    read_fixture,
    signal_povm_from_record,
    write_jsonl,
)

jax_engine = load_module("cr_jax_engine_3q_loop", ENGINES_DIR / "jax_engine_3q.py")
jnp = jax_engine.jnp
expm = jax_engine.expm

I2 = jax_engine.I2
I8 = jax_engine.I8
SX = jax_engine.sx
SY = jax_engine.sy
SZ = jax_engine.sz


def sym_norm(rho):
    out = 0.5 * (rho + rho.conj().T)
    tr = jnp.trace(out).real
    if float(jnp.abs(tr)) < EPS:
        raise ValueError("density trace collapsed to zero")
    return (out / tr).astype(jnp.complex128)


def psd_floor(rho):
    clean = sym_norm(rho)
    vals, vecs = jnp.linalg.eigh(clean)
    vals = jnp.clip(vals.real, EPS)
    return sym_norm(vecs @ jnp.diag(vals).astype(jnp.complex128) @ vecs.conj().T)


def log_hermitian(a):
    clean = 0.5 * (a + a.conj().T)
    vals, vecs = jnp.linalg.eigh(clean)
    return vecs @ jnp.diag(jnp.log(vals.real)).astype(jnp.complex128) @ vecs.conj().T


def relative_entropy_bits(obs, belief):
    obs = sym_norm(obs)
    belief = psd_floor(belief)
    value = jnp.trace(obs @ ((log_hermitian(obs + EPS * I8) - log_hermitian(belief)) / jnp.log(2.0)))
    return float(value.real)


def von_neumann_entropy_bits(rho):
    vals = jnp.linalg.eigvalsh(sym_norm(rho)).real
    vals = vals[vals > EPS]
    return float(-jnp.sum(vals * jnp.log2(vals)))


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
        terrain = expm(jax_engine.T_FLOW * jax_engine.gen_super(t))
        for op_name in jax_engine.NATIVE[t]:
            stages.append((jax_engine.op_map(op_name) @ terrain).astype(jnp.complex128))
    return stages


def build_hill_store_super():
    h = jax_engine.on0((SX + SY + SZ) / jnp.sqrt(3.0)) + jax_engine.J_COUP * (jax_engine.ZZ01 + jax_engine.ZZ12)
    gen = jax_engine.G * jax_engine.superH(h) + jax_engine.KAP * jax_engine.superD(jax_engine.on0(SZ))
    return expm(0.15 * gen).astype(jnp.complex128)


def apply_super(superop, rho):
    return sym_norm(jax_engine.unvec(superop @ jax_engine.vec(rho)))


def obs_density_from_outcome(outcome: int):
    projector = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128) if outcome == 0 else jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)
    return jax_engine.kron3(projector, 0.5 * I2, 0.5 * I2)


def q0_projector_from_outcome(outcome: int):
    projector = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128) if outcome == 0 else jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)
    return jax_engine.kron3(projector, I2, I2)


def luders_condition_q0(rho, outcome: int):
    projector = q0_projector_from_outcome(outcome)
    post = projector @ rho @ projector.conj().T
    prob = float(jnp.trace(post).real)
    if prob < EPS:
        raise ValueError(f"Lüders conditioning probability collapsed for outcome {outcome}")
    return sym_norm(post / prob)


def q0_reduced(rho):
    reduced = jnp.zeros((2, 2), dtype=jnp.complex128)
    for a in range(2):
        for b in range(2):
            value = 0.0 + 0.0j
            for q1 in range(2):
                for q2 in range(2):
                    i = (a << 2) | (q1 << 1) | q2
                    j = (b << 2) | (q1 << 1) | q2
                    value = value + rho[i, j]
            reduced = reduced.at[a, b].set(value)
    return sym_norm(reduced)


def belief_bloch_q0(rho):
    reduced = q0_reduced(rho)
    return [float(jnp.trace(reduced @ s).real) for s in (SX, SY, SZ)]


def belief_pauli_63(rho):
    return [float(jnp.trace(rho @ p).real) for p in jax_engine.PMATS]


def stage_metadata():
    return [{"t": int(t), "op": str(op_name)} for t in range(8) for op_name in jax_engine.NATIVE[t]]


def run_records(fixture, stage_supers, precompute_seconds):
    stages = stage_metadata()
    if len(stage_supers) != 16:
        raise ValueError(f"jax_loop precomputed {len(stage_supers)} stage channels, expected 16")
    hill = build_hill_store_super()
    pending_stage_super = jnp.eye(64, dtype=jnp.complex128)
    belief = jnp.eye(8, dtype=jnp.complex128) / 8.0
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
                "substrate": "jax_loop",
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
        "substrate": "jax_loop",
        "ticks": len(rows),
        "precompute_seconds": precompute_seconds,
        "loop_seconds": loop_seconds,
        "total_seconds": precompute_seconds + loop_seconds,
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg"],
        "aligned_packages_load_bearing": ["jax.numpy", "jax.scipy.linalg"],
        "reads_peer_result": False,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run JAX qit_live_loop_3q_v1 substrate")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or default_output_for_fixture(args.fixture, "jax_loop")
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
