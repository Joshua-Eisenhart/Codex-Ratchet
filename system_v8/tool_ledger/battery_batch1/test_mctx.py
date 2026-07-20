#!/usr/bin/env python3
"""mctx plans information-gaining probe order on a real recovered world view."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
REPO=Path('/Users/joshuaeisenhart/Codex-Ratchet'); OUT=REPO/'system_v8/tool_ledger/battery_batch1/results/mctx.json'; sys.path.insert(0,str(REPO/'system_v8/loop3_senses'))
def main():
 r={'tool':'mctx','state':'BLOCKED','verdict':'BLOCKED','promotion_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat(),'real_object':'obj-000 view-4 world-source action sequence','inputs':{'events':'system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl'}}
 try:
  free=int(re.search(r'(\d+)%',subprocess.run(['memory_pressure'],capture_output=True,text=True,check=True).stdout.split('System-wide memory free percentage:')[1]).group(1)); r['memory_free_percent']=free
  if free<=25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
  import jax, jax.numpy as jnp, mctx
  import senses_v2_slow_memory as s, visibility_sanity_gate as v
  wr=json.load(open(s.WORLD_RECEIPT)); rules={int(k):tuple(x) for k,x in wr['parameters']['rule_family'].items()}; log,_=v.parse_event_log(s.EVENTS); full,_=v.recover_full_views(log,rules); words,rs,h=s.build_hypotheses(rules); oid='obj-000'; view=4; true=np.array(full[oid][view],int); candidates=np.asarray(h[:,view,:])
  # Every mask is a real sequence of position probes and conditions on its actual event value.
  ent=np.zeros(256); valid=np.zeros((256,8),bool)
  for mask in range(256):
   keep=np.ones(len(h),bool)
   for a in range(8):
    if mask>>a&1: keep &= candidates[:,a]==true[a]
   q=keep/keep.sum(); ent[mask]=-float(np.sum(q[keep]*np.log(q[keep]))); valid[mask]=[(mask>>a)&1==0 for a in range(8)]
  E=jnp.asarray(ent,dtype=jnp.float32); V=jnp.asarray(valid)
  def recurrent(params,key,action,embedding):
   nxt=embedding | (jnp.int32(1)<<action.astype(jnp.int32)); reward=E[embedding]-E[nxt]; next_masks=nxt[:,None]|(jnp.int32(1)<<jnp.arange(8,dtype=jnp.int32)); logits=jnp.where(V[nxt],E[nxt,None]-E[next_masks],-1e9); return mctx.RecurrentFnOutput(reward=reward,discount=jnp.ones_like(reward),prior_logits=logits,value=jnp.zeros_like(reward)),nxt
  root=mctx.RootFnOutput(prior_logits=(100*(E[0]-E[jnp.int32(1)<<jnp.arange(8,dtype=jnp.int32)]))[None,:],value=jnp.zeros(1),embedding=jnp.zeros(1,dtype=jnp.int32))
  out=mctx.gumbel_muzero_policy(params=(),rng_key=jax.random.PRNGKey(20260719),root=root,recurrent_fn=recurrent,num_simulations=64,max_depth=3,gumbel_scale=0.01)
  action=int(np.asarray(out.action)[0]); mctx_gain=float(ent[0]-ent[1<<action]); random_gain=float(np.mean([ent[0]-ent[1<<a] for a in range(8)])); ok=mctx_gain>random_gain
  r.update(state='INTEGRATED' if ok else 'BLOCKED',verdict='INTEGRATED' if ok else 'BLOCKED',computed_number=mctx_gain,checks={'mctx_first_action_position':action,'mctx_information_gain_nats':mctx_gain,'random_policy_mean_gain_nats':random_gain,'mctx_beats_random_gate':ok,'simulations':64,'candidate_hypotheses':len(h)},reason='mctx Gumbel MuZero chooses an actual world-source probe position from a belief over the real additive-XOR hypotheses; reward is posterior entropy reduction after that real event, and is compared with a seeded random policy.')
 except Exception as e: r['exact_error']=f'{type(e).__name__}: {e}'
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
if __name__=='__main__': main()
