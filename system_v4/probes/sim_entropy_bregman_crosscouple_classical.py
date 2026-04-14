#!/usr/bin/env python3
"""Cross-family coupling (classical): entropy x Bregman.
Shannon entropy of p equals log n - KL(p || uniform), i.e. expressible as a
Bregman divergence against the uniform distribution with generator phi(p)=sum p log p.
"""
import json, os, numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch":{"tried":True,"used":True,"reason":"supportive KL cross-check"},
    "pyg":{"tried":False,"used":False,"reason":"n/a"},
    "z3":{"tried":False,"used":False,"reason":"n/a"},
    "cvc5":{"tried":False,"used":False,"reason":"n/a"},
    "sympy":{"tried":False,"used":False,"reason":"n/a"},
    "clifford":{"tried":False,"used":False,"reason":"n/a"},
    "geomstats":{"tried":False,"used":False,"reason":"n/a"},
    "e3nn":{"tried":False,"used":False,"reason":"n/a"},
    "rustworkx":{"tried":False,"used":False,"reason":"n/a"},
    "xgi":{"tried":False,"used":False,"reason":"n/a"},
    "toponetx":{"tried":False,"used":False,"reason":"n/a"},
    "gudhi":{"tried":False,"used":False,"reason":"n/a"},
}
TOOL_INTEGRATION_DEPTH={k:None for k in TOOL_MANIFEST}; TOOL_INTEGRATION_DEPTH["pytorch"]="supportive"
try: import torch
except ImportError: torch=None

divergence_log = [
    "Classical entropy-as-Bregman identity assumes a fixed generator phi "
    "(negative entropy) against the uniform reference. Nonclassical "
    "entropy-Bregman coupling (where the generator itself is "
    "constraint-admissible and probe-dependent) is NOT modeled here.",
]

def H(p):
    p = np.clip(p, 1e-15, 1)
    return float(-(p*np.log(p)).sum())

def KL(p, q):
    p = np.clip(p, 1e-15, 1); q = np.clip(q, 1e-15, 1)
    return float((p*(np.log(p)-np.log(q))).sum())

def bregman_neg_entropy(p, q):
    # D_phi(p||q) with phi(x)=sum x log x = KL(p||q)
    return KL(p, q)

def run_positive_tests():
    r={}
    for seed in range(8):
        rng=np.random.default_rng(seed); n=6
        p = rng.dirichlet(np.ones(n))
        u = np.ones(n)/n
        lhs = H(p)
        rhs = np.log(n) - bregman_neg_entropy(p, u)
        r[f"seed_{seed}"] = {"lhs":lhs,"rhs":rhs,
                             "pass": bool(abs(lhs-rhs) < 1e-9)}
    if torch is not None:
        p = torch.tensor([0.25,0.25,0.25,0.25], dtype=torch.float64)
        h = float(-(p*torch.log(p)).sum())
        r["torch_xcheck"] = {"pass": bool(abs(h - np.log(4)) < 1e-9)}
    return r

def run_negative_tests():
    r={}
    n=5
    rng=np.random.default_rng(0)
    p = rng.dirichlet(np.ones(n))
    u = np.ones(n)/n
    # KL(p||u) >= 0
    r["kl_nonneg"] = {"pass": bool(bregman_neg_entropy(p,u) >= -1e-12)}
    # KL(p||p)=0
    r["kl_self_zero"] = {"pass": bool(abs(bregman_neg_entropy(p,p))<1e-12)}
    # asymmetric: KL(p||u) != KL(u||p) generically
    r["kl_asymmetric"] = {"pass": bool(abs(KL(p,u)-KL(u,p)) > 1e-6)}
    return r

def run_boundary_tests():
    r={}
    n=4
    u = np.ones(n)/n
    r["uniform_H_logn"] = {"pass": bool(abs(H(u)-np.log(n))<1e-12)}
    r["uniform_bregman_zero"] = {"pass": bool(abs(bregman_neg_entropy(u,u))<1e-12)}
    # near-delta: H ~ 0, KL -> log n
    p = np.zeros(n); p[0]=1-3e-12; p[1:]=1e-12
    p = p/p.sum()
    r["delta_H_small"] = {"pass": bool(H(p) < 1e-9)}
    return r

def all_pass(d):
    ok=True
    for v in d.values():
        if isinstance(v,dict):
            if "pass" in v: ok=ok and bool(v["pass"])
            else: ok=ok and all_pass(v)
    return ok

if __name__=="__main__":
    pos=run_positive_tests();neg=run_negative_tests();bnd=run_boundary_tests()
    ap=all_pass(pos) and all_pass(neg) and all_pass(bnd)
    results={"name":"entropy_bregman_crosscouple_classical","classification":classification,
             "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
             "divergence_log":divergence_log,"positive":pos,"negative":neg,"boundary":bnd,
             "all_pass":bool(ap),"summary":{"all_pass":bool(ap)}}
    out_dir=os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(out_dir,exist_ok=True)
    out_path=os.path.join(out_dir,"entropy_bregman_crosscouple_classical_results.json")
    with open(out_path,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={ap} -> {out_path}")
