#!/usr/bin/env python3
"""CVXPY closest-CPTP projection of a real manifold stage channel Choi matrix."""
from __future__ import annotations
import json, sys, subprocess, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
REPO=Path('/Users/joshuaeisenhart/Codex-Ratchet'); OUT=REPO/'system_v8/tool_ledger/battery_batch1/results/cvxpy.json'; sys.path.insert(0,str(REPO/'system_v8/loop3_senses'))
def main():
 r={'tool':'cvxpy','state':'BLOCKED','verdict':'BLOCKED','promotion_allowed':False,'generated_at':datetime.now(timezone.utc).isoformat(),'inputs':{'stage64_receipt':'system_v8/nested_manifold/results/stage64/receipt.json'}}
 try:
  free=int(re.search(r'(\d+)%',subprocess.run(['memory_pressure'],capture_output=True,text=True,check=True).stdout.split('System-wide memory free percentage:')[1]).group(1)); r['memory_free_percent']=free
  if free<=25: raise RuntimeError(f'memory gate failed: {free}% is not >25%')
  import cvxpy as cp, visibility_sanity_gate as v
  channels,_=v.load_stage_channels(json.load(open(REPO/'system_v8/nested_manifold/results/stage64/receipt.json')),encoder_channel_fix=False); S=channels[(0,1)]; d=4; J=np.zeros((16,16),complex)
  for i in range(d):
   for j in range(d):
    E=np.zeros((d,d),complex); E[i,j]=1; J+=np.kron(E,v.unvec(S@v.vec(E)))
  J=(J+J.conj().T)/2; perturb=np.zeros_like(J); perturb[0,0]=-0.08; perturb[1,2]=perturb[2,1]=0.025; T=J+perturb
  X=cp.Variable((16,16),hermitian=True); xr=cp.reshape(X,(d,d,d,d),order='C'); constraints=[X>>0]
  # Choi layout is (input_i, output_k, input_j, output_l); TP traces k=l.
  constraints += [sum(xr[i,k,j,k] for k in range(d))==(1 if i==j else 0) for i in range(d) for j in range(d)]
  prob=cp.Problem(cp.Minimize(cp.sum_squares(cp.abs(X-T))),constraints); val=prob.solve(solver='CLARABEL',tol_gap_abs=1e-9,tol_feas=1e-9,max_iter=500)
  P=np.asarray(X.value); mineig=float(np.linalg.eigvalsh((P+P.conj().T)/2).min()); tp=float(np.max(np.abs(np.einsum('ikjk->ij',P.reshape(d,d,d,d))-np.eye(d)))); exact=float(np.linalg.norm(P-J)); pert=float(np.linalg.norm(T-J)); ok=prob.status in {'optimal','optimal_inaccurate'} and mineig>-1e-7 and tp<1e-6 and exact<pert
  r.update(state='INTEGRATED' if ok else 'BLOCKED',verdict='INTEGRATED' if ok else 'BLOCKED',real_object='manifold stage position=0 bit=1 exact Choi channel',computed_number=exact,checks={'channel':'manifold stage position=0 bit=1','solver_status':prob.status,'objective':float(val),'projected_min_choi_eigenvalue':mineig,'projected_tp_deviation':tp,'distance_to_exact_choi':exact,'perturbation_distance_to_exact_choi':pert,'exact_choi_recovery_gate':ok},reason='cvxpy solved the PSD plus exact partial-trace CPTP projection for a deliberately perturbed real stage-channel Choi matrix; the output is checked against the original exact Choi.')
 except Exception as e: r['exact_error']=f'{type(e).__name__}: {e}'
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
if __name__=='__main__': main()
