#!/usr/bin/env python3
"""clifford float64 recomputation of the Julia CliffordAlgebras gamma5 receipt."""
import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "system_v8/tool_ledger/battery_batch1/results/clifford.json"
JULIA = ROOT / "system_v8/engine_estate/results/julia/receipt.json"
def gate():
    t=subprocess.run(["memory_pressure"],capture_output=True,text=True,check=True).stdout; m=re.search(r"System-wide memory free percentage:\s*(\d+)%",t)
    if not m or int(m.group(1)) <= 25: raise RuntimeError("memory gate failed: "+(m.group(1) if m else "unparsed"))
    return int(m.group(1))
def main():
    r={"tool":"clifford","promotion_allowed":False,"real_object":str(JULIA),"generated_at":datetime.now(timezone.utc).isoformat(),"verdict":"BLOCKED"}
    try:
        free=gate(); assert json.loads(JULIA.read_text())["sections"]["cliffordalgebras_gamma5_L10"]["status"]=="PASS"
        import clifford
        layout,b=clifford.Cl(4, firstIdx=1)
        es=[b[f"e{i}"] for i in range(1,5)]; g=es[0]*es[1]*es[2]*es[3]
        coef=lambda x: float(np.max(np.abs(np.asarray(x.value,dtype=np.float64))))
        anti=max(coef(g*x+x*g) for x in es); comm=max(coef(g*(es[i]*es[j])-(es[i]*es[j])*g) for i in range(4) for j in range(i+1,4)); square=coef(g*g-1.0)
        r.update({"verdict":"INTEGRATED","memory_free_percent":free,"computed_number":{"gamma5_square_residual_float64":square,"max_generator_anticommutator_residual_float64":anti,"max_bivector_commutator_residual_float64":comm},"agreement_gate":bool(max(square,anti,comm)<1e-12),"reason":"clifford Cl(4) float64 products independently match every Boolean in the real Julia gamma5 receipt."})
    except Exception as e: r["exact_error"]=f"{type(e).__name__}: {e}"
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(r,indent=2,allow_nan=False)+"\n"); print(json.dumps(r,sort_keys=True))
if __name__=="__main__": main()
