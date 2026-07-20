#!/usr/bin/env python3
"""Hypothesis property battery for the real senses_v2 Bayes posterior updater."""
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]; OUT=ROOT/"system_v8/tool_ledger/battery_batch1/results/hypothesis.json"; EVENTS=ROOT/"system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl"; WORLD=ROOT/"system_v8/loop2_world/results/world_source/receipt.json"; STAGE=ROOT/"system_v8/nested_manifold/results/stage64/receipt.json"
def gate():
 t=subprocess.run(["memory_pressure"],capture_output=True,text=True,check=True).stdout;m=re.search(r"System-wide memory free percentage:\s*(\d+)%",t)
 if not m or int(m.group(1))<=25: raise RuntimeError("memory gate failed: "+(m.group(1) if m else "unparsed"))
 return int(m.group(1))
def main():
 r={"tool":"hypothesis","promotion_allowed":False,"real_object":str(EVENTS),"generated_at":datetime.now(timezone.utc).isoformat(),"verdict":"BLOCKED"}
 try:
  free=gate(); sys.path.insert(0,str(ROOT))
  from hypothesis import given, settings, strategies as st
  from system_v8.loop3_senses.senses_v2_slow_memory import QuantumReadoutBayes
  # Evidence is the real recorded first state: its 15-Pauli readout and its
  # 1024-state posterior. Hypothesis varies only the prior odds/permutation.
  traj=json.loads((ROOT/"system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json").read_text()); state=traj["candidate_reset_fast"]["obj-000"][0]
  q=np.asarray(state["quantum_readout"],float); real_post=np.maximum(np.asarray(state["m_slow_posterior"],float),np.finfo(float).tiny); real_post/=real_post.sum()
  candidate=np.tile(q,(len(real_post),1)); candidate[:,0]+=np.linspace(-0.3,0.3,len(real_post))
  engine=object.__new__(QuantumReadoutBayes); engine.sigma=0.15; count={"n":0}
  @settings(max_examples=80, deadline=None, derandomize=True)
  @given(st.lists(st.floats(min_value=1e-8,max_value=10,allow_nan=False,allow_infinity=False),min_size=8,max_size=8),st.booleans())
  def physicality(local_odds, reverse):
   # Keep the actual recorded 1024-state posterior as the base measure while
   # generating only eight local odds perturbations.  This remains a full
   # physical 1024-state update without Hypothesis's huge-base-example path.
   prior=real_post.copy(); prior[:8] *= np.asarray(local_odds,float); prior/=prior.sum(); cand=candidate[::-1] if reverse else candidate
   out=engine.update_posterior(prior,q,cand); count["n"]+=1
   assert np.all(np.isfinite(out)) and np.all(out>=0.0) and abs(float(out.sum())-1.0)<1e-12
   # Same real readout/candidate likelihood under a common positive rescale
   # must leave the physical normalized posterior unchanged.
   scaled=engine.update_posterior(prior*7.0,q,cand); assert np.max(np.abs(out-scaled))<1e-12
  physicality()
  r.update({"verdict":"INTEGRATED","memory_free_percent":free,"computed_number":{"hypothesis_examples":count["n"],"hypothesis_state_count":len(real_post),"posterior_sum_tolerance":1e-12},"agreement_gate":count["n"]==80,"reason":"Hypothesis ran 80 generated prior/permutation cases through the owner QuantumReadoutBayes.update_posterior using the actual obj-000 view-0 15-Pauli evidence and recorded 1024-hypothesis state; every posterior remained finite, nonnegative, normalized, and invariant to common prior rescaling."})
 except Exception as e:r["exact_error"]=f"{type(e).__name__}: {e}"
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n");print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
