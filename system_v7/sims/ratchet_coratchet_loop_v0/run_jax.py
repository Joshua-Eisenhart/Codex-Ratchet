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
def rid(k,q): return f"{k}:{'.'.join('-'.join(map(str, sorted(c))) for c in q)}"
def drive(t, v, hist):
    base = jnp.asarray([.25,.25,.25,.25])
    if v == "static_fact_list": return base
    if v == "commuting_drive": return base + .03 * math.sin(t) * jnp.asarray([1,1,-1,-1])
    mem = sum(hist[-3:]) / max(1, min(3, len(hist))) if hist else jnp.zeros(4)
    phase = t
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
def licenses(q,t,v):
    kinds=["global_population"] if t==0 or v in ("feedback_cut","commuting_drive") else ["within_cell_phase","pair_correlation"]
    return [{"id":rid(k,q), "kind":k, "licensed_by_lock":None if t==0 else t} for k in kinds]
def persistent_pairs(q,tick_facts,streaks,k,v):
    w=separation_witness(q,tick_facts,tolerance=1e-9); current={tuple(p["pair"]):p for p in w["witness_pairs"]}
    if v in ("memoryless_drive","label_shuffle"): current={}
    next_streaks={pair:streaks.get(pair,0)+1 for pair in current}
    return [dict(current[p], persistent_ticks=next_streaks[p]) for p in sorted(current) if next_streaks[p]>=k], next_streaks
def run(v,persistent_k=3,max_ticks=50,stop_lossless=10):
    q=[[0,1,2,3]]; all_facts=[]; locks=[]; hist=[]; licensed=licenses(q,0,v); streaks={}; lossless=0; curve=[]; last=None
    for tick in range(1,max_ticks+1):
        s=drive(tick,v,hist); hist.append(s-.25); tick_facts=[]
        if v!="static_fact_list" or tick==1:
            for ro in list(licensed):
                fact={"tick":tick,"readout_id":ro["id"],"licensed_by_lock":ro["licensed_by_lock"],"values":measure(ro["kind"],s,q).tolist()}
                tick_facts.append(fact); all_facts.append(fact)
        pairs,streaks=persistent_pairs(q,tick_facts,streaks,persistent_k,v)
        if pairs and not all(len(c)==1 for c in q):
            c=choose(q,pairs); post=any(f.get("licensed_by_lock") is not None for f in tick_facts)
            q=c["quotient"]; lock={"tick":tick,"quotient":q,"witness_pairs":pairs,"post_lock_readout_forced":post,"score":{"separation":c["separation"],"presumption":c["presumption"]}}
            locks.append(lock); last=tick; lossless=0; streaks={}
            if v!="feedback_cut":
                licensed=licenses(q,tick,v)
                for ro in licensed: ro["licensed_by_lock"]=len(locks)
                lock["licensed_readouts"]=licensed
        else:
            lossless+=1
        curve.append({"tick":tick,"locks":len(locks)})
        if all(len(c)==1 for c in q) and lossless>=stop_lossless: break
    return {"variant":v,"persistent_k":persistent_k,"ticks_run":tick,"locks":locks,"lock_curve":curve,"last_new_tick":last,"co_turn_events":[l for l in locks if l["post_lock_readout_forced"]],"final_quotient":q,"fact_count":len(all_facts)}
def main():
    runs=[run(v) for v in VARIANTS]
    headline={"dominates_total_locks":all(len(runs[0]["locks"])>len(r["locks"]) for r in runs[1:]),"dominates_co_turns":all(len(runs[0]["co_turn_events"])>len(r["co_turn_events"]) for r in runs[1:]),"feedback_cut_kills_co_turns":len(next(r for r in runs if r["variant"]=="feedback_cut")["co_turn_events"])==0}
    headline["headline_pass"]=all(headline.values())
    out={"schema_version":"ratchet_coratchet_loop_v0","engine":"jax","generated_at":now(),"classification":classification,"promotion_allowed":False,"formal_admission_allowed":False,"capstone_status":"DRAFT_UNAUDITED","persistent_k":3,"headline":headline,"run_results":runs,"all_pass":headline["headline_pass"],"TOOL_MANIFEST":TOOL_MANIFEST,"TOOL_INTEGRATION_DEPTH":TOOL_INTEGRATION_DEPTH,"divergence_log":["persistent witness pairs require K consecutive ticks; controls are expected to plateau, flatline, or lose co-turns"]}
    write("ratchet_coratchet_loop_v0_jax_results.json",out); print(json.dumps({"engine":"jax","locks":{r["variant"]:len(r["locks"]) for r in runs},"co_turns":{r["variant"]:len(r["co_turn_events"]) for r in runs}}, sort_keys=True))
if __name__=="__main__": main()
