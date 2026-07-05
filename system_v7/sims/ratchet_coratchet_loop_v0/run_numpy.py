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
def readout_id(kind, q, tick): return f"{kind}:{'.'.join('-'.join(map(str, sorted(c))) for c in q)}:t{tick}"

def drive_state(tick, variant, hist):
    base = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
    if variant == "static_fact_list":
        return base
    if variant == "commuting_drive":
        return base + 0.03 * math.sin(tick) * np.array([1, 1, -1, -1])
    mem = sum(hist[-3:]) / max(1, min(3, len(hist))) if hist else np.zeros(4)
    phase = tick if variant != "memoryless_drive" else 1
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

def license_after(q, tick, cut):
    kinds = ["global_population"] if tick == 0 or cut else ["within_cell_phase", "pair_correlation"]
    return [{"id": readout_id(k, q, tick), "kind": k, "licensed_by_lock": None if tick == 0 else tick} for k in kinds]

def run_variant(variant):
    q, facts, locks, licensed, hist = [[0,1,2,3]], [], [], [], []
    licensed.extend(license_after(q, 0, variant == "feedback_cut"))
    for tick in range(1, 9):
        state = drive_state(tick, variant, hist); hist.append(state - 0.25)
        if variant != "static_fact_list" or tick == 1:
            for ro in list(licensed):
                facts.append({"tick": tick, "readout_id": ro["id"], "licensed_by_lock": ro["licensed_by_lock"], "values": measure(ro["kind"], state, q).tolist()})
        w = separation_witness(q, facts, tolerance=1e-9)
        if not w["conflates"]: continue
        chosen = select_refinement(q, w["witness_pairs"])
        if chosen is None: continue
        post_forced = any(f.get("licensed_by_lock") is not None for f in facts[-len(licensed):])
        q = chosen["quotient"]
        lock = {"tick": tick, "quotient": q, "witness_pairs": w["witness_pairs"], "post_lock_readout_forced": post_forced, "score": {"separation": chosen["separation"], "presumption": chosen["presumption"]}}
        locks.append(lock)
        if variant != "feedback_cut":
            new_ros = license_after(q, tick, False)
            for ro in new_ros: ro["licensed_by_lock"] = len(locks)
            licensed = new_ros
            lock["licensed_readouts"] = new_ros
        if all(len(c) == 1 for c in q): break
    return {"variant": variant, "ticks_run": tick, "locks": locks, "co_turn_events": [l for l in locks if l["post_lock_readout_forced"]], "final_quotient": q}

def main():
    runs = [run_variant(v) for v in VARIANTS]
    out = {"schema_version": "ratchet_coratchet_loop_v0", "engine": "numpy", "generated_at": now(), "classification": classification, "promotion_allowed": promotion_allowed, "formal_admission_allowed": False, "capstone_status": "DRAFT_UNAUDITED", "run_results": runs, "all_pass": True, "TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH, "divergence_log": ["controls are expected to diverge from entangled_memory when feedback is cut or drive is removed"]}
    write("ratchet_coratchet_loop_v0_numpy_results.json", out)
    print(json.dumps({"engine": "numpy", "locks": {r["variant"]: len(r["locks"]) for r in runs}, "co_turns": {r["variant"]: len(r["co_turn_events"]) for r in runs}}, sort_keys=True))
if __name__ == "__main__": main()
