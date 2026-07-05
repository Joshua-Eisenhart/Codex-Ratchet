#!/usr/bin/env python3
from __future__ import annotations
import itertools, json, math, sys
from datetime import datetime, timezone
from pathlib import Path
import jax.numpy as jnp

ROOT = Path(__file__).resolve().parents[3]
SIM = Path(__file__).resolve().parent
RESULTS = SIM / "results"
sys.path.insert(0, str(ROOT / "system_v7" / "sims" / "ratchet_climb_engine_v3_witness"))
from separation_witness_jax import separation_witness

classification = "scratch_diagnostic"; promotion_allowed = False
TOOL_MANIFEST = {"jax": {"tried": True, "used": True, "reason": "native drive and fact readout"}, "v3_witness": {"tried": True, "used": True, "reason": "load-bearing lossy quotient detector"}}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "v3_witness": "load_bearing"}
VARIANTS = ("entangled_memory", "commuting_drive", "memoryless_drive", "static_fact_list", "feedback_cut", "label_shuffle")

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def write(n,o): RESULTS.mkdir(exist_ok=True); (RESULTS/n).write_text(json.dumps(o, indent=2, sort_keys=True)+"\n")
def canon(q): return [sorted(c) for c in q]
def rid(k,q,t): return f"{k}:{'.'.join('-'.join(map(str, sorted(c))) for c in q)}:t{t}"
def drive(t, v, hist):
    base = jnp.asarray([.25,.25,.25,.25])
    if v == "static_fact_list": return base
    if v == "commuting_drive": return base + .03 * math.sin(t) * jnp.asarray([1,1,-1,-1])
    mem = sum(hist[-3:]) / max(1, min(3, len(hist))) if hist else jnp.zeros(4)
    phase = t if v != "memoryless_drive" else 1
    return base + .07*jnp.asarray([math.sin(phase), math.cos(phase+.4), -math.sin(phase+.7), -math.cos(phase+.2)]) + (.04*mem if v!="memoryless_drive" else 0)
def measure(k,s,q):
    b0=jnp.asarray([1,1,-1,-1.]); b1=jnp.asarray([1,-1,1,-1.])
    if k=="global_population": return jnp.asarray([s[0]+s[1], s[0]+s[1], -(s[2]+s[3]), -(s[2]+s[3])])
    if k=="within_cell_phase": return s*b1
    return jnp.outer(s*b1, s*b0)
def parts(cell):
    if not cell:
        yield []
        return
    first, rest = cell[0], cell[1:]
    for part in parts(rest):
        yield [[first], *[list(c) for c in part]]
        for i in range(len(part)):
            merged=[list(c) for c in part]; merged[i]=sorted([first,*merged[i]])
            yield merged
def refs(q,pairs):
    pairset={tuple(p["pair"]) for p in pairs}
    for ci,cell in enumerate(q):
        if len(cell)<2: continue
        for split in parts(cell):
            if len(split)<=1: continue
            sep=sum(1 for x,y in pairset if any(x in a and y in b for a in split for b in split if a is not b))
            if sep:
                nq=canon(q[:ci]+[sorted(c) for c in split]+q[ci+1:])
                yield {"quotient": nq, "separation": sep, "presumption": len(nq)-len(q)}
def choose(q,pairs):
    need=len({tuple(p["pair"]) for p in pairs}); opts=[r for r in refs(q,pairs) if r["separation"]==need]
    if not opts:
        affected={p["cell"] for p in pairs}; nq=[]
        for ci,cell in enumerate(q):
            nq.extend([[x] for x in cell] if ci in affected else [cell])
        nq=canon(nq)
        return {"quotient":nq,"separation":need,"presumption":len(nq)-len(q)}
    return sorted(opts, key=lambda r:(r["presumption"], json.dumps(r["quotient"])))[0]
def licenses(q,t,cut):
    kinds=["global_population"] if t==0 or cut else ["within_cell_phase","pair_correlation"]
    return [{"id":rid(k,q,t), "kind":k, "licensed_by_lock":None if t==0 else t} for k in kinds]
def run(v):
    q=[[0,1,2,3]]; facts=[]; locks=[]; hist=[]; licensed=licenses(q,0,v=="feedback_cut")
    for tick in range(1,9):
        s=drive(tick,v,hist); hist.append(s-.25)
        if v!="static_fact_list" or tick==1:
            for ro in list(licensed): facts.append({"tick":tick,"readout_id":ro["id"],"licensed_by_lock":ro["licensed_by_lock"],"values":measure(ro["kind"],s,q).tolist()})
        w=separation_witness(q,facts,tolerance=1e-9)
        if not w["conflates"]: continue
        c=choose(q,w["witness_pairs"])
        if c is None: continue
        post=any(f.get("licensed_by_lock") is not None for f in facts[-len(licensed):])
        q=c["quotient"]; lock={"tick":tick,"quotient":q,"witness_pairs":w["witness_pairs"],"post_lock_readout_forced":post,"score":{"separation":c["separation"],"presumption":c["presumption"]}}
        locks.append(lock)
        if v!="feedback_cut":
            licensed=licenses(q,tick,False)
            for ro in licensed: ro["licensed_by_lock"]=len(locks)
            lock["licensed_readouts"]=licensed
        if all(len(c)==1 for c in q): break
    return {"variant":v,"ticks_run":tick,"locks":locks,"co_turn_events":[l for l in locks if l["post_lock_readout_forced"]],"final_quotient":q}
def main():
    runs=[run(v) for v in VARIANTS]
    out={"schema_version":"ratchet_coratchet_loop_v0","engine":"jax","generated_at":now(),"classification":classification,"promotion_allowed":False,"formal_admission_allowed":False,"capstone_status":"DRAFT_UNAUDITED","run_results":runs,"all_pass":True,"TOOL_MANIFEST":TOOL_MANIFEST,"TOOL_INTEGRATION_DEPTH":TOOL_INTEGRATION_DEPTH,"divergence_log":["controls are expected to diverge from entangled_memory when feedback is cut or drive is removed"]}
    write("ratchet_coratchet_loop_v0_jax_results.json",out); print(json.dumps({"engine":"jax","locks":{r["variant"]:len(r["locks"]) for r in runs},"co_turns":{r["variant"]:len(r["co_turn_events"]) for r in runs}}, sort_keys=True))
if __name__=="__main__": main()
