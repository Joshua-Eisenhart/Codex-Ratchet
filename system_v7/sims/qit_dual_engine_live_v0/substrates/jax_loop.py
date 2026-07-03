"""QUARANTINE_EXPLORATORY: JAX substrate for qit_dual_engine_live_v0.

classification='scratch_diagnostic'; promotion_allowed=false.

Runs both dual-engine sheets per tick in JAX arrays: pending-stage prediction,
Luders conditioning on q0, hill relaxation, EFE over the sheet's 8 stages,
action feedback, and spinor memory-bit mechanics. NumPy is used only at JSON
egress and scalar boundary conversion.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from common_dual_engine import (
    ACTION_TIE_TOL,
    CLASSIFICATION,
    ENGINES_DIR,
    EPS,
    MEMORY_READ_TICKS,
    PROMOTION_ALLOWED,
    QUARANTINE,
    SCHEMA,
    SHEET_STAGE_DEFS,
    STREAM_ID,
    load_module,
    read_fixture,
    signal_povm_from_record,
    write_jsonl,
)

jax_engine = load_module("cr_jax_engine_3q_dual_loop", ENGINES_DIR / "jax_engine_3q.py")
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


def build_sheet_stage_supers():
    out = {"D": [], "C": []}
    for engine_id, stage_defs in SHEET_STAGE_DEFS.items():
        for stage in stage_defs:
            terrain = expm(jax_engine.T_FLOW * jax_engine.gen_super(int(stage["terrain"])))
            out[engine_id].append((jax_engine.op_map(str(stage["op"])) @ terrain).astype(jnp.complex128))
    return out


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
        raise ValueError(f"Luders conditioning probability collapsed for outcome {outcome}")
    return sym_norm(post / prob)


def belief_pauli_63(rho):
    return [float(jnp.trace(rho @ p).real) for p in jax_engine.PMATS]


def trace_distance(a, b):
    return float(0.5 * jnp.sum(jnp.linalg.svd(a - b, compute_uv=False)))


def spinor_step(psi, op_name: str):
    if op_name == "Fi":
        u = expm(-1j * (jnp.pi / 2.0) / 2.0 * SY)
        return u @ psi
    if op_name == "Fe":
        u = expm(+1j * (jnp.pi / 2.0) / 2.0 * SY)
        return u @ psi
    return psi


def spinor_bit_fidelity(psi, target):
    overlap = float(jnp.real(jnp.vdot(target, psi)))
    return float(jnp.clip((1.0 + overlap) / 2.0, 0.0, 1.0))


def engine_tick(state, rec, hill, stage_supers, stage_defs):
    outcome = int(rec["outcome"])
    predicted = apply_super(state["pending"], state["belief"])
    preference = apply_super(hill, predicted)
    obs = obs_density_from_outcome(outcome)
    surprise = relative_entropy_bits(obs, predicted)
    conditioned = luders_condition_q0(predicted, outcome)
    fe_gradient = surprise - relative_entropy_bits(obs, conditioned)
    belief = apply_super(hill, conditioned)
    scores = [reactive_risk_entropy_cost_surrogate(apply_super(stage, belief), belief, preference) for stage in stage_supers]
    chosen = choose_action_index(scores)
    stage_def = stage_defs[chosen]
    state["belief"] = belief
    state["pending"] = stage_supers[chosen]
    state["memory"] = spinor_step(state["memory"], str(stage_def["op"]))
    return {
        "belief": belief,
        "surprise_bits": surprise,
        "fe_gradient": fe_gradient,
        "entropy_bits": von_neumann_entropy_bits(belief),
        "scores": scores,
        "chosen_action_index": chosen,
        "stage_def": stage_def,
        "memory_bit_fidelity": spinor_bit_fidelity(state["memory"], state["memory_target"]),
    }


def row_from_tick(substrate, rec, engine_id, tick_result, gap_trace, gap_surprise):
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


def run_records(fixture, sheet_stage_supers, precompute_seconds):
    for engine_id in ("D", "C"):
        if len(sheet_stage_supers.get(engine_id, [])) != 8:
            raise ValueError(f"jax_loop precomputed {engine_id} {len(sheet_stage_supers.get(engine_id, []))} stages, expected 8")
    hill = build_hill_store_super()
    states = {
        "D": {"belief": I8 / 8.0, "pending": jnp.eye(64, dtype=jnp.complex128), "memory": jnp.array([1.0, 0.0], dtype=jnp.complex128), "memory_target": jnp.array([1.0, 0.0], dtype=jnp.complex128)},
        "C": {"belief": I8 / 8.0, "pending": jnp.eye(64, dtype=jnp.complex128), "memory": jnp.array([1.0, 0.0], dtype=jnp.complex128), "memory_target": jnp.array([1.0, 0.0], dtype=jnp.complex128)},
    }
    rows = {"D": [], "C": []}
    memory_reads = {"D": {}, "C": {}}
    started = time.perf_counter()
    for rec in fixture["ticks"]:
        d = engine_tick(states["D"], rec, hill, sheet_stage_supers["D"], SHEET_STAGE_DEFS["D"])
        c = engine_tick(states["C"], rec, hill, sheet_stage_supers["C"], SHEET_STAGE_DEFS["C"])
        gap_trace = trace_distance(d["belief"], c["belief"])
        gap_surprise = abs(float(d["surprise_bits"]) - float(c["surprise_bits"]))
        rows["D"].append(row_from_tick("jax_loop", rec, "D", d, gap_trace, gap_surprise))
        rows["C"].append(row_from_tick("jax_loop", rec, "C", c, gap_trace, gap_surprise))
        if int(rec["tick"]) in MEMORY_READ_TICKS:
            memory_reads["D"][str(int(rec["tick"]))] = float(d["memory_bit_fidelity"])
            memory_reads["C"][str(int(rec["tick"]))] = float(c["memory_bit_fidelity"])
    loop_seconds = time.perf_counter() - started
    return rows, {
        "substrate": "jax_loop",
        "ticks": len(rows["D"]),
        "precompute_seconds": precompute_seconds,
        "loop_seconds": loop_seconds,
        "total_seconds": precompute_seconds + loop_seconds,
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg"],
        "aligned_packages_load_bearing": ["jax.numpy", "jax.scipy.linalg"],
        "reads_peer_result": False,
        "memory_reads": memory_reads,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run jax_loop qit_dual_engine_live_v0 substrate")
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    out_dir = args.out_dir or args.fixture.resolve().parent
    fixture = read_fixture(args.fixture)
    started = time.perf_counter()
    sheet_supers = build_sheet_stage_supers()
    precompute_seconds = time.perf_counter() - started
    rows, metrics = run_records(fixture, sheet_supers, precompute_seconds)
    outputs = {}
    for engine_id, engine_rows in rows.items():
        out = out_dir / f"jax_loop_engine_{engine_id}.jsonl"
        write_jsonl(out, engine_rows)
        outputs[engine_id] = str(out)
    metrics["outputs"] = outputs
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()
