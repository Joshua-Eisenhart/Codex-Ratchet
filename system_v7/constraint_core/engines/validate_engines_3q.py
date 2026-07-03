"""
validate_engines_3q.py -- compares 3-qubit substrate results (jax_results_3q.json,
torch_results_3q.json) to the numpy oracle contract targets_3q.json. Recomputes
invariants substrate-side; never trusts them from file. Exit 0 = GREEN.
"""
import json, os, sys
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
tgt=json.load(open(os.path.join(HERE,"targets_3q.json")))
tol=tgt["tolerances"]["pvec_abs"]
tstages=tgt["stages"]
def check(fn):
    path=os.path.join(HERE,fn)
    if not os.path.exists(path): return None,"absent"
    got=json.load(open(path))["stages"]
    if len(got)!=len(tstages): return False,f"stage count {len(got)}!=16"
    worst=0.0
    for a,b in zip(tstages,got):
        if a["t"]!=b["t"] or a["op"]!=b["op"]: return False,"stage order mismatch"
        for key in ("pvec_down","pvec_up"):
            d=np.max(np.abs(np.array(a[key])-np.array(b[key]))); worst=max(worst,float(d))
    # recompute distinctness substrate-side
    M=np.array([s["pvec_down"]+s["pvec_up"] for s in got])
    dmin=min(np.linalg.norm(M[i]-M[j]) for i in range(16) for j in range(i+1,16))
    ok=(worst<=max(tol,1e-6)) and dmin>1e-3
    return ok,f"worst pvec dev {worst:.2e}, min pairwise {dmin:.4f}"
res={}
for fn in ("jax_results_3q.json","torch_results_3q.json","julia_results_3q.json"):
    ok,detail=check(fn); res[fn]=(ok,detail)
    tag={True:"PASS",False:"FAIL",None:"skip"}[ok]
    print(f"{tag} {fn.split('_results')[0]}: {detail}")
passed=[k for k,(ok,_) in res.items() if ok]
failed=[k for k,(ok,_) in res.items() if ok is False]
print()
if failed: print(f"=== RED ({len(failed)} substrate(s) disagree with oracle) ==="); sys.exit(1)
if not passed: print("=== no 3q substrate results present (run jax_engine_3q.py first) ==="); sys.exit(1)
print(f"=== GREEN ({len(passed)} substrate(s) validated vs 3-qubit oracle) ===")
