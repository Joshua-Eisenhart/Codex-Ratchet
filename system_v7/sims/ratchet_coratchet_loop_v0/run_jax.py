#!/usr/bin/env python3
from __future__ import annotations

import json, math
import jax.numpy as jnp
from run_numpy import RESULTS, VARIANT_RUNS, headline, now, run_pipeline, summarize, write

BASE = jnp.full((4,), 0.25)
GENERATOR_TABLE = {}
TOOL_MANIFEST = {"jax": {"tried": True, "used": True, "reason": "native generator, carrier evolution, and fact measurement"}, "shared_python_pipeline": {"tried": True, "used": True, "reason": "label-blind persistence/refinement/licensing/co-turn logic"}, "v3_witness": {"tried": True, "used": True, "reason": "load-bearing lossy quotient detector"}}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "shared_python_pipeline": "load_bearing", "v3_witness": "load_bearing"}

def readout_id(kind, q): return f"{kind}:{'.'.join('-'.join(map(str, sorted(c))) for c in q)}"

def measure(kind, state, q):
    bits0 = jnp.asarray([1.0, 1.0, -1.0, -1.0])
    bits1 = jnp.asarray([1.0, -1.0, 1.0, -1.0])
    if kind == "global_population":
        return jnp.asarray([state[0] + state[1], state[0] + state[1], -(state[2] + state[3]), -(state[2] + state[3])])
    if kind == "within_cell_phase":
        return state * bits1
    if kind == "pair_correlation":
        return jnp.outer(state * bits1, state * bits0)
    raise ValueError(kind)

def fact(kind, tick, state, q, ro):
    return {"tick": tick, "readout_id": ro["id"], "licensed_by_lock": ro["licensed_by_lock"], "values": measure(kind, state, q).tolist()}

def g_history(carrier, history, tick, q, readouts):
    mem = sum(history[-3:]) / max(1, min(3, len(history))) if history else jnp.zeros(4)
    phase = tick + 0.17 * len(history)
    state = BASE + 0.07 * jnp.asarray([math.sin(phase), math.cos(phase + 0.4), -math.sin(phase + 0.7), -math.cos(phase + 0.2)]) + 0.04 * mem
    return state, [fact(ro["kind"], tick, state, q, ro) for ro in readouts]

def g_commute(carrier, history, tick, q, readouts):
    state = BASE + 0.03 * math.sin(tick) * jnp.asarray([1.0, 1.0, -1.0, -1.0])
    return state, [fact(ro["kind"], tick, state, q, ro) for ro in readouts]

def g_empty_history(carrier, history, tick, q, readouts):
    return g_history(carrier, [], tick, q, readouts)

def g_replay(carrier, history, tick, q, readouts):
    if tick > 1:
        return carrier, []
    return BASE, [fact(ro["kind"], tick, BASE, q, ro) for ro in readouts]

def g_label_shuffle(carrier, history, tick, q, readouts):
    state, facts = g_history(carrier, history, tick, q, readouts)
    for item in facts:
        item["values"] = jnp.roll(jnp.asarray(item["values"]), 1, axis=0).tolist()
    return state, facts

GENERATOR_TABLE.update({"entangled_memory": g_history, "commuting": g_commute, "memoryless": g_empty_history, "static": g_replay, "shuffled": g_label_shuffle})

def run_all(k=3):
    return [run_pipeline(label, GENERATOR_TABLE[gen], flag, k) for label, gen, flag in VARIANT_RUNS]

def main():
    runs = run_all(3)
    h = headline(runs); h["headline_pass"] = all(h.values())
    out = {"schema_version": "ratchet_coratchet_loop_v0", "engine": "jax", "generated_at": now(), "classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "capstone_status": "STRUCTURAL_REPAIR_20260704", "persistent_k": 3, "headline": h, "run_results": runs, "all_pass": h["headline_pass"], "shared_pipeline": "JAX implements generator, carrier evolution, and fact measurement natively; persistence/refinement/licensing/co-turn logic is shared and label-blind", "TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH, "divergence_log": ["run labels differ only by generator output or the single licensing-extension flag"]}
    write("ratchet_coratchet_loop_v0_jax_results.json", out)
    print(json.dumps({"engine": "jax", "locks": {r["variant"]: len(r["locks"]) for r in runs}, "co_turns": {r["variant"]: len(r["co_turn_events"]) for r in runs}, "headline": h}, sort_keys=True))
if __name__ == "__main__": main()
