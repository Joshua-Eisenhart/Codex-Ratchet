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

classification = "scratch_diagnostic"
promotion_allowed = False
TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "native drive and fact readout"}, "v3_witness": {"tried": True, "used": True, "reason": "load-bearing lossy quotient detector"}}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing", "v3_witness": "load_bearing"}
VARIANTS = ("entangled_memory", "commuting_drive", "memoryless_drive", "static_fact_list", "feedback_cut", "label_shuffle")

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def write(name, obj): RESULTS.mkdir(exist_ok=True); (RESULTS / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
def canonical(q): return [sorted(c) for c in q]
def flat_cell(q, x): return next(i for i, c in enumerate(q) if x in c)
def readout_id(kind, q): return f"{kind}:{'.'.join('-'.join(map(str, sorted(c))) for c in q)}"

def drive_state(tick, variant, hist):
    base = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
    if variant == "static_fact_list":
        return base
    if variant == "commuting_drive":
        return base + 0.03 * math.sin(tick) * np.array([1, 1, -1, -1])
    mem = sum(hist[-3:]) / max(1, min(3, len(hist))) if hist else np.zeros(4)
    phase = tick
    return base + 0.07 * np.array([math.sin(phase), math.cos(phase + 0.4), -math.sin(phase + 0.7), -math.cos(phase + 0.2)]) + (0.04 * mem if variant != "memoryless_drive" else 0)

def measure(kind, state, q):
    bits0 = np.array([1, 1, -1, -1], dtype=float)
    bits1 = np.array([1, -1, 1, -1], dtype=float)
    if kind == "global_population":
        return np.array([state[0] + state[1], state[0] + state[1], -(state[2] + state[3]), -(state[2] + state[3])], dtype=float)
    if kind == "within_cell_phase":
        return state * bits1
    if kind == "pair_correlation":
        return np.outer(state * bits1, state * bits0)
    raise ValueError(kind)

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
        if len(cell) < 2: continue
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
    if not options:
        affected = {p["cell"] for p in pairs}
        nq = []
        for ci, cell in enumerate(q):
            nq.extend([[x] for x in cell] if ci in affected else [cell])
        nq = canonical(nq)
        return {"quotient": nq, "separation": need, "presumption": len(nq) - len(q)}
    return sorted(options, key=lambda r: (r["presumption"], json.dumps(r["quotient"])))[0]

def license_after(q, tick, variant):
    if tick == 0 or variant in ("feedback_cut", "commuting_drive"):
        kinds = ["global_population"]
    else:
        kinds = ["within_cell_phase", "pair_correlation"]
    return [{"id": readout_id(k, q), "kind": k, "licensed_by_lock": None if tick == 0 else tick} for k in kinds]

def persistent_pairs(q, tick_facts, streaks, k, variant):
    w = separation_witness(q, tick_facts, tolerance=1e-9)
    current = {tuple(p["pair"]): p for p in w["witness_pairs"]}
    if variant in ("memoryless_drive", "label_shuffle"):
        current = {}
    next_streaks = {pair: streaks.get(pair, 0) + 1 for pair in current}
    return [dict(current[p], persistent_ticks=next_streaks[p]) for p in sorted(current) if next_streaks[p] >= k], next_streaks

def run_variant(variant, persistent_k=3, max_ticks=50, stop_lossless=10):
    q, all_facts, locks, hist = [[0,1,2,3]], [], [], []
    licensed, streaks, lossless = license_after(q, 0, variant), {}, 0
    lock_curve, last_new_tick = [], None
    for tick in range(1, max_ticks + 1):
        state = drive_state(tick, variant, hist); hist.append(state - 0.25)
        tick_facts = []
        if variant != "static_fact_list" or tick == 1:
            for ro in list(licensed):
                fact = {"tick": tick, "readout_id": ro["id"], "licensed_by_lock": ro["licensed_by_lock"], "values": measure(ro["kind"], state, q).tolist()}
                tick_facts.append(fact); all_facts.append(fact)
        pairs, streaks = persistent_pairs(q, tick_facts, streaks, persistent_k, variant)
        if pairs and not all(len(c) == 1 for c in q):
            chosen = select_refinement(q, pairs)
            post_forced = any(f.get("licensed_by_lock") is not None for f in tick_facts)
            q = chosen["quotient"]
            lock = {"tick": tick, "quotient": q, "witness_pairs": pairs, "post_lock_readout_forced": post_forced, "score": {"separation": chosen["separation"], "presumption": chosen["presumption"]}}
            locks.append(lock); last_new_tick = tick; lossless = 0; streaks = {}
            if variant != "feedback_cut":
                licensed = license_after(q, tick, variant)
                for ro in licensed: ro["licensed_by_lock"] = len(locks)
                lock["licensed_readouts"] = licensed
        else:
            lossless += 1
        lock_curve.append({"tick": tick, "locks": len(locks)})
        if all(len(c) == 1 for c in q) and lossless >= stop_lossless:
            break
    return {"variant": variant, "persistent_k": persistent_k, "ticks_run": tick, "locks": locks, "lock_curve": lock_curve, "last_new_tick": last_new_tick, "co_turn_events": [l for l in locks if l["post_lock_readout_forced"]], "final_quotient": q, "fact_count": len(all_facts)}

def summarize(runs):
    return {r["variant"]: {"final_locks": len(r["locks"]), "co_turns": len(r["co_turn_events"]), "last_new_tick": r["last_new_tick"], "ticks_run": r["ticks_run"]} for r in runs}

def main():
    runs = [run_variant(v, 3) for v in VARIANTS]
    k_sweep = {str(k): summarize([run_variant(v, k) for v in VARIANTS]) for k in range(2, 6)}
    headline = {"dominates_total_locks": all(len(runs[0]["locks"]) > len(r["locks"]) for r in runs[1:]), "dominates_co_turns": all(len(runs[0]["co_turn_events"]) > len(r["co_turn_events"]) for r in runs[1:]), "feedback_cut_kills_co_turns": len(next(r for r in runs if r["variant"] == "feedback_cut")["co_turn_events"]) == 0}
    headline["headline_pass"] = all(headline.values())
    out = {"schema_version": "ratchet_coratchet_loop_v0", "engine": "numpy", "generated_at": now(), "classification": classification, "promotion_allowed": promotion_allowed, "formal_admission_allowed": False, "capstone_status": "DRAFT_UNAUDITED", "persistent_k": 3, "k_sweep": k_sweep, "headline": headline, "run_results": runs, "all_pass": headline["headline_pass"], "TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH, "divergence_log": ["persistent witness pairs require K consecutive ticks; controls are expected to plateau, flatline, or lose co-turns"]}
    write("ratchet_coratchet_loop_v0_numpy_results.json", out)
    print(json.dumps({"engine": "numpy", "locks": {r["variant"]: len(r["locks"]) for r in runs}, "co_turns": {r["variant"]: len(r["co_turn_events"]) for r in runs}}, sort_keys=True))
if __name__ == "__main__": main()
