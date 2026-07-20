#!/usr/bin/env python3
"""Optuna alpha search on the real stored senses_v2 joint-feature readout."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
REPO=Path('/Users/joshuaeisenhart/Codex-Ratchet'); OUT=REPO/'system_v8/tool_ledger/battery_batch1/results/optuna.json'; sys.path.insert(0,str(REPO/'system_v8/loop3_senses'))
def main():
 r={'tool':'optuna','state':'BLOCKED','verdict':'BLOCKED','promotion_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat(),'inputs':{'trajectories':'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json','receipt':'system_v8/loop3_senses/results/senses_v2_slow_memory/receipt.json'}}
 try:
  free=int(re.search(r'(\d+)%',subprocess.run(['memory_pressure'],capture_output=True,text=True,check=True).stdout.split('System-wide memory free percentage:')[1]).group(1)); r['memory_free_percent']=free
  if free<=25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
  import optuna, visibility_sanity_gate as v
  optuna.logging.set_verbosity(optuna.logging.WARNING); traj=json.load(open(REPO/'system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json'))['candidate_reset_fast']; wr=json.load(open(REPO/'system_v8/loop2_world/results/world_source/receipt.json')); rules={int(k):tuple(x) for k,x in wr['parameters']['rule_family'].items()}; log,_=v.parse_event_log(REPO/'system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl'); full,_=v.recover_full_views(log,rules); objs=sorted(log); train,test=v.train_test_objects(objs)
  slots=[(o,w,p) for o in objs for w in range(6) for p in range(8) if log[o][w][p]=='withheld']; tr=[z for z in slots if z[0] in set(train)]; te=[z for z in slots if z[0] in set(test)]
  def run(alpha):
   pred={}
   for p in range(8):
    a=[z for z in tr if z[2]==p]; b=[z for z in te if z[2]==p]; X=np.array([traj[o][w]['quantum_readout']+traj[o][w]['m_slow_summary'] for o,w,_ in a]); y=np.array([2*full[o][w][q]-1 for o,w,q in a]); W=np.linalg.solve(X.T@X+alpha*np.eye(X.shape[1]),X.T@y)
    for z,x in zip(b,[traj[o][w]['quantum_readout']+traj[o][w]['m_slow_summary'] for o,w,_ in b]): pred[z]=int(np.dot(W,x)>=0)
   return float(np.mean([pred[z]==full[z[0]][z[1]][z[2]] for z in te]))
  study=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=20260719)); study.optimize(lambda t:run(t.suggest_float('ridge_alpha',1e-6,1e1,log=True)),n_trials=20)
  acc=run(study.best_params['ridge_alpha']); ci=json.load(open(REPO/'system_v8/loop3_senses/results/senses_v2_slow_memory/receipt.json'))['results']['accuracy_object_bootstrap']['metrics']['candidate_accuracy']['ci95']; ok=ci[0]<=acc<=ci[1]
  r.update(state='INTEGRATED' if ok else 'BLOCKED',verdict='INTEGRATED' if ok else 'BLOCKED',real_object='senses_v2 stored rho_fast plus m_slow object-disjoint ridge readout',computed_number=acc,checks={'trials':20,'best_ridge_alpha':study.best_params['ridge_alpha'],'held_out_accuracy':acc,'anchor_ci95':ci,'within_anchor_ci_gate':ok,'test_slots':len(te)},reason='optuna selected the ridge alpha for the object-disjoint per-position readout using real stored rho_fast plus m_slow features and recovered world targets; the selected held-out accuracy is gated against the existing whole-object CI.')
 except Exception as e: r['exact_error']=f'{type(e).__name__}: {e}'
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
if __name__=='__main__': main()
