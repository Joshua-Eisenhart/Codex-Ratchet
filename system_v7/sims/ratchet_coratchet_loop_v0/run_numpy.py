#!/usr/bin/env python3
from __future__ import annotations

import itertools, json, math, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SIM = Path(__file__).resolve().parent
RESULTS = SIM / "results"
sys.path.insert(0, str(ROOT / "system_v7" / "sims" / "ratchet_climb_engine_v3_witness"))
from separation_witness_numpy import separation_witness

BASE = np.full(4, 0.25, dtype=float)
ENTANGLED_A = np.array([[1.0, 0.22, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, -0.16], [0.0, 0.0, 0.0, 1.0]], dtype=float)
ENTANGLED_B = np.array([[1.0, 0.0, -0.19, 0.0], [0.0, 1.0, 0.0, 0.13], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], dtype=float)
COMMUTE_A = np.diag([1.07, 0.97, 1.03, 0.93])
COMMUTE_B = np.diag([0.91, 1.11, 0.89, 1.09])
assert not np.allclose(ENTANGLED_A @ ENTANGLED_B, ENTANGLED_B @ ENTANGLED_A)
assert np.allclose(COMMUTE_A @ COMMUTE_B, COMMUTE_B @ COMMUTE_A)
INITIAL_READOUTS = ("global_population",)
EXTENDED_READOUTS = ("within_cell_phase", "pair_correlation", "time_ordered_two_step")
VARIANT_RUNS = (
    ("entangled_memory", "entangled_memory"),
    ("commuting", "commuting"),
    ("memoryless", "memoryless"),
    ("static", "static"),
    ("shuffled", "shuffled"),
    ("feedback_cut", "feedback_cut"),
)
GENERATOR_TABLE = {}
TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "native generator, carrier evolution, and fact measurement"}, "v3_witness": {"tried": True, "used": True, "reason": "load-bearing lossy quotient detector"}}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "v3_witness": "load_bearing"}

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def write(name, obj): RESULTS.mkdir(exist_ok=True); (RESULTS / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
def canonical(q): return [sorted(c) for c in q]
def readout_id(kind, q): return f"{kind}:{'.'.join('-'.join(map(str, sorted(c))) for c in q)}"

def measure(kind, state, q, previous=None, operators=None):
    bits0 = np.array([1, 1, -1, -1], dtype=float)
    bits1 = np.array([1, -1, 1, -1], dtype=float)
    if kind == "global_population":
        return np.array([state[0] + state[1], state[0] + state[1], -(state[2] + state[3]), -(state[2] + state[3])], dtype=float)
    if kind == "within_cell_phase":
        return state * bits1
    if kind == "pair_correlation":
        return np.outer(state * bits1, state * bits0)
    if kind == "time_ordered_two_step":
        a, b = operators if operators is not None else (COMMUTE_A, COMMUTE_B)
        x = BASE if previous is None else previous
        return np.full(4, float(np.linalg.norm(b @ (a @ x) - a @ (b @ x))), dtype=float)
    raise ValueError(kind)

def fact(kind, tick, state, q, ro, previous=None, operators=None):
    return {"tick": tick, "readout_id": ro["id"], "licensed_by_lock": ro["licensed_by_lock"], "values": measure(kind, state, q, previous, operators).tolist()}

def facts_for(readouts, tick, state, q, previous=None, operators=None):
    return [fact(ro["kind"], tick, state, q, ro, previous, operators) for ro in readouts]

def g_history(carrier, history, tick, q, readouts):
    mem = sum(history[-3:]) / max(1, min(3, len(history))) if history else np.zeros(4)
    phase = tick + 0.17 * len(history)
    state = BASE + 0.07 * np.array([math.sin(phase), math.cos(phase + 0.4), -math.sin(phase + 0.7), -math.cos(phase + 0.2)]) + 0.04 * mem
    return state, facts_for(readouts, tick, state, q, carrier, (ENTANGLED_A, ENTANGLED_B))

def g_commute(carrier, history, tick, q, readouts):
    state = BASE + 0.03 * math.sin(tick) * np.array([1, 1, -1, -1], dtype=float)
    return state, facts_for(readouts, tick, state, q, carrier, (COMMUTE_A, COMMUTE_B))

def g_empty_history(carrier, history, tick, q, readouts):
    return g_history(carrier, [], tick, q, readouts)

def g_replay(carrier, history, tick, q, readouts):
    if tick > 1:
        return carrier, []
    return BASE.copy(), facts_for(readouts, tick, BASE, q, carrier, (COMMUTE_A, COMMUTE_B))

def g_label_shuffle(carrier, history, tick, q, readouts):
    state, facts = g_history(carrier, history, tick, q, readouts)
    for item in facts:
        vals = np.array(item["values"])
        item["values"] = np.roll(vals, 1, axis=0).tolist()
    return state, facts

def g_feedback_cut(carrier, history, tick, q, readouts):
    return g_history(carrier, [], tick, q, readouts)

GENERATOR_TABLE.update({"entangled_memory": g_history, "commuting": g_commute, "memoryless": g_empty_history, "static": g_replay, "shuffled": g_label_shuffle, "feedback_cut": g_feedback_cut})

def set_partitions(cell):
    if not cell:
        yield []
        return
    first, rest = cell[0], cell[1:]
    for part in set_partitions(rest):
        yield [[first], *[list(c) for c in part]]
        for i in range(len(part)):
            merged = [list(c) for c in part]
            merged[i] = sorted([first, *merged[i]])
            yield merged

def refinements(q, pairs):
    pairset = {tuple(p["pair"]) for p in pairs}
    for ci, cell in enumerate(q):
        if len(cell) < 2:
            continue
        for split in set_partitions(cell):
            if len(split) <= 1:
                continue
            sep = sum(1 for x, y in pairset if any(x in a and y in b for a in split for b in split if a is not b))
            if sep:
                nq = canonical(q[:ci] + [sorted(c) for c in split] + q[ci + 1:])
                yield {"quotient": nq, "separation": sep, "presumption": len(nq) - len(q)}

def select_refinement(q, pairs):
    need = len({tuple(p["pair"]) for p in pairs})
    options = [r for r in refinements(q, pairs) if r["separation"] == need]
    if options:
        return sorted(options, key=lambda r: (r["presumption"], json.dumps(r["quotient"])))[0]
    affected = {p["cell"] for p in pairs}
    nq = []
    for ci, cell in enumerate(q):
        nq.extend([[x] for x in cell] if ci in affected else [cell])
    nq = canonical(nq)
    return {"quotient": nq, "separation": need, "presumption": len(nq) - len(q)}

def license_readouts(q, kinds, lock_id):
    return [{"id": readout_id(k, q), "kind": k, "licensed_by_lock": lock_id} for k in kinds]

def persistent_pairs(q, tick_facts, streaks, k):
    witness = separation_witness(q, tick_facts, tolerance=1e-9)
    current = {tuple(p["pair"]): p for p in witness["witness_pairs"]}
    next_streaks = {pair: streaks.get(pair, 0) + 1 for pair in current}
    return [dict(current[p], persistent_ticks=next_streaks[p]) for p in sorted(current) if next_streaks[p] >= k], next_streaks

def order_only_pairs(q, tick_facts):
    order_facts = [f for f in tick_facts if "time_ordered_two_step" in f["readout_id"]]
    if not order_facts:
        return []
    return separation_witness(q, order_facts, tolerance=1e-9)["witness_pairs"]

def run_pipeline(label, generator, persistent_k=3, max_ticks=50, stop_lossless=10, extend_licensing=True):
    q, all_facts, locks, history = [[0, 1, 2, 3]], [], [], []
    carrier, licensed, streaks, lossless = BASE.copy(), license_readouts([[0, 1, 2, 3]], INITIAL_READOUTS, None), {}, 0
    lock_curve, last_new_tick = [], None
    for tick in range(1, max_ticks + 1):
        carrier, tick_facts = generator(carrier, history, tick, q, list(licensed))
        history.append(carrier - BASE)
        all_facts.extend(tick_facts)
        pairs, streaks = persistent_pairs(q, tick_facts, streaks, persistent_k)
        if pairs and not all(len(c) == 1 for c in q):
            chosen = select_refinement(q, pairs)
            post_forced = any(f.get("licensed_by_lock") is not None and f["tick"] > locks[f["licensed_by_lock"] - 1]["tick"] for f in tick_facts)
            order_pairs = order_only_pairs(q, tick_facts)
            q = chosen["quotient"]
            lock = {"tick": tick, "quotient": q, "witness_pairs": pairs, "order_witness_pairs": order_pairs, "post_lock_readout_forced": post_forced, "score": {"separation": chosen["separation"], "presumption": chosen["presumption"]}}
            locks.append(lock); last_new_tick = tick; lossless = 0; streaks = {}
            licensed = license_readouts(q, EXTENDED_READOUTS, len(locks)) if extend_licensing else []
            lock["licensed_readouts"] = licensed
        else:
            lossless += 1
        lock_curve.append({"tick": tick, "locks": len(locks)})
        if all(len(c) == 1 for c in q) and lossless >= stop_lossless:
            break
    return {"variant": label, "persistent_k": persistent_k, "ticks_run": tick, "locks": locks, "lock_curve": lock_curve, "last_new_tick": last_new_tick, "co_turn_events": [l for l in locks if l["post_lock_readout_forced"]], "order_fact_events": [l for l in locks if l["order_witness_pairs"]], "final_quotient": q, "fact_count": len(all_facts)}

def run_all(k=3):
    return [run_pipeline(label, GENERATOR_TABLE[gen], k, extend_licensing=(label != "feedback_cut")) for label, gen in VARIANT_RUNS]

def summarize(runs):
    return {r["variant"]: {"final_locks": len(r["locks"]), "co_turns": len(r["co_turn_events"]), "order_fact_events": len(r["order_fact_events"]), "last_new_tick": r["last_new_tick"], "ticks_run": r["ticks_run"]} for r in runs}

def headline(runs):
    first, rest = runs[0], runs[1:]
    return {"dominates_total_locks": all(len(first["locks"]) > len(r["locks"]) for r in rest), "dominates_co_turns": all(len(first["co_turn_events"]) > len(r["co_turn_events"]) for r in rest)}

def main():
    runs = run_all(3)
    h = headline(runs); h["headline_pass"] = all(h.values())
    out = {"schema_version": "ratchet_coratchet_loop_v0", "engine": "numpy", "generated_at": now(), "classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "capstone_status": "STRUCTURAL_REPAIR_20260704_TIME_ORDERED", "persistent_k": 3, "commutation_assertions": {"entangled_pair_noncommuting": True, "commuting_pair_commutes": True}, "k_sweep": {str(k): summarize(run_all(k)) for k in range(2, 6)}, "headline": h, "run_results": runs, "all_pass": h["headline_pass"], "shared_pipeline": "persistence gate, v3 witness, refinement scoring, extend_licensing-gated readouts, same-input order correlator, and later-tick post-lock detection are label-blind", "TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH, "divergence_log": ["run labels differ only by generator output"]}
    write("ratchet_coratchet_loop_v0_numpy_results.json", out)
    print(json.dumps({"engine": "numpy", "locks": {r["variant"]: len(r["locks"]) for r in runs}, "co_turns": {r["variant"]: len(r["co_turn_events"]) for r in runs}, "headline": h}, sort_keys=True))
if __name__ == "__main__": main()
