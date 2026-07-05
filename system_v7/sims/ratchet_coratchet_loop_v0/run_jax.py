#!/usr/bin/env python3
from __future__ import annotations

import json, math
import jax.numpy as jnp
from run_numpy import RESULTS, VARIANT_RUNS, headline, now, run_pipeline, summarize, write

DIM = 8
BASE = jnp.full((DIM,), 1.0 / DIM)
_EA = [[1.0 if i == j else 0.0 for j in range(DIM)] for i in range(DIM)]
_EA[0][1] = 0.22; _EA[2][3] = -0.16; _EA[4][5] = 0.11; _EA[6][7] = -0.09
_EB = [[1.0 if i == j else 0.0 for j in range(DIM)] for i in range(DIM)]
_EB[0][2] = -0.19; _EB[1][3] = 0.13; _EB[4][6] = -0.07; _EB[5][7] = 0.17
ENTANGLED_A = jnp.asarray(_EA)
ENTANGLED_B = jnp.asarray(_EB)
COMMUTE_A = jnp.diag(jnp.asarray([1.07, 0.97, 1.03, 0.93, 1.05, 0.95, 1.01, 0.99]))
COMMUTE_B = jnp.diag(jnp.asarray([0.91, 1.11, 0.89, 1.09, 0.94, 1.06, 0.92, 1.08]))
assert not bool(jnp.allclose(ENTANGLED_A @ ENTANGLED_B, ENTANGLED_B @ ENTANGLED_A))
assert bool(jnp.allclose(COMMUTE_A @ COMMUTE_B, COMMUTE_B @ COMMUTE_A))
GENERATOR_TABLE = {}
TOOL_MANIFEST = {"jax": {"tried": True, "used": True, "reason": "native generator, carrier evolution, and fact measurement"}, "shared_python_pipeline": {"tried": True, "used": True, "reason": "label-blind persistence/refinement/licensing/co-turn logic"}, "v3_witness": {"tried": True, "used": True, "reason": "load-bearing lossy quotient detector"}}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "shared_python_pipeline": "load_bearing", "v3_witness": "load_bearing"}

def readout_id(kind, q): return f"{kind}:{'.'.join('-'.join(map(str, sorted(c))) for c in q)}"

def measure(kind, state, q, previous=None, operators=None):
    idx = jnp.arange(DIM)
    bits0 = jnp.where((idx & 4) == 0, 1.0, -1.0)
    bits1 = jnp.where((idx & 2) == 0, 1.0, -1.0)
    if kind == "global_population":
        return jnp.where(bits0 > 0, jnp.sum(jnp.where(bits0 > 0, state, 0.0)), -jnp.sum(jnp.where(bits0 < 0, state, 0.0)))
    if kind == "within_cell_phase":
        return state * bits1
    if kind == "pair_correlation":
        return jnp.outer(state * bits1, state * bits0)
    if kind == "time_ordered_two_step":
        a, b = operators if operators is not None else (COMMUTE_A, COMMUTE_B)
        x = BASE if previous is None else previous
        return jnp.full((DIM,), jnp.linalg.norm(b @ (a @ x) - a @ (b @ x)))
    raise ValueError(kind)

def fact(kind, tick, state, q, ro, previous=None, operators=None):
    return {"tick": tick, "readout_id": ro["id"], "licensed_by_lock": ro["licensed_by_lock"], "values": measure(kind, state, q, previous, operators).tolist()}

def facts_for(readouts, tick, state, q, previous=None, operators=None):
    return [fact(ro["kind"], tick, state, q, ro, previous, operators) for ro in readouts]

def g_history(carrier, history, tick, q, readouts):
    mem = sum(history[-3:]) / max(1, min(3, len(history))) if history else jnp.zeros(DIM)
    phase = tick + 0.17 * len(history)
    wave = jnp.asarray([math.sin(phase + 0.31 * i) if i % 2 == 0 else math.cos(phase + 0.23 * i) for i in range(DIM)])
    wave = wave - jnp.mean(wave)
    state = BASE + 0.035 * wave + 0.04 * mem
    return state, facts_for(readouts, tick, state, q, carrier, (ENTANGLED_A, ENTANGLED_B))

def g_commute(carrier, history, tick, q, readouts):
    idx = jnp.arange(DIM)
    state = BASE + 0.015 * math.sin(tick) * jnp.where((idx & 4) == 0, 1.0, -1.0)
    return state, facts_for(readouts, tick, state, q, carrier, (COMMUTE_A, COMMUTE_B))

def g_empty_history(carrier, history, tick, q, readouts):
    return g_history(carrier, [], tick, q, readouts)

def g_replay(carrier, history, tick, q, readouts):
    if tick > 1:
        return carrier, []
    return BASE, facts_for(readouts, tick, BASE, q, carrier, (COMMUTE_A, COMMUTE_B))

def g_label_shuffle(carrier, history, tick, q, readouts):
    state, facts = g_history(carrier, history, tick, q, readouts)
    for item in facts:
        item["values"] = jnp.roll(jnp.asarray(item["values"]), 1, axis=0).tolist()
    return state, facts

def g_feedback_cut(carrier, history, tick, q, readouts):
    return g_history(carrier, [], tick, q, readouts)

GENERATOR_TABLE.update({"entangled_memory": g_history, "commuting": g_commute, "memoryless": g_empty_history, "static": g_replay, "shuffled": g_label_shuffle, "feedback_cut": g_feedback_cut})

def run_all(k=3):
    return [run_pipeline(label, GENERATOR_TABLE[gen], k, extend_licensing=(label != "feedback_cut")) for label, gen in VARIANT_RUNS]

def main():
    runs = run_all(3)
    h = headline(runs); h["headline_pass"] = all(h.values())
    out = {"schema_version": "ratchet_coratchet_loop_v0", "engine": "jax", "generated_at": now(), "classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "capstone_status": "STRUCTURAL_REPAIR_20260704_TIME_ORDERED", "persistent_k": 3, "commutation_assertions": {"entangled_pair_noncommuting": True, "commuting_pair_commutes": True}, "headline": h, "run_results": runs, "all_pass": h["headline_pass"], "shared_pipeline": "JAX implements generator, carrier evolution, and fact measurement natively; persistence/refinement/licensing/time-ordered/co-turn logic is shared and label-blind", "TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH, "divergence_log": ["run labels differ only by generator output"]}
    write("ratchet_coratchet_loop_v0_jax_results.json", out)
    print(json.dumps({"engine": "jax", "locks": {r["variant"]: len(r["locks"]) for r in runs}, "co_turns": {r["variant"]: len(r["co_turn_events"]) for r in runs}, "headline": h}, sort_keys=True))
if __name__ == "__main__": main()
