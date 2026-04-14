#!/usr/bin/env python3
"""Cross-family coupling (classical): distinguishability x admission.
Total-variation distance is jointly convex: TV(sum t_i p_i, sum t_i q_i) <=
sum t_i TV(p_i, q_i). Convex-hull admission of distributions respects TV.
"""
import json, os, numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch":{"tried":True,"used":True,"reason":"supportive TV cross-check"},
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
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
try:
    import torch
except ImportError:
    torch = None

divergence_log = [
    "Classical TV convexity treats admission as convex mixing of classical "
    "distributions. Nonclassical distinguishability-admission coupling "
    "(where constraint exclusion on one component removes admissibility of "
    "the mixture even if each component is admissible) is lost.",
]

def TV(p, q): return 0.5 * float(np.sum(np.abs(p - q)))

def run_positive_tests():
    r = {}
    rng = np.random.default_rng(0)
    n = 6
    for seed in range(6):
        rng = np.random.default_rng(seed)
        k = 3
        ts = rng.dirichlet(np.ones(k))
        ps = [rng.dirichlet(np.ones(n)) for _ in range(k)]
        qs = [rng.dirichlet(np.ones(n)) for _ in range(k)]
        p_mix = sum(t*p for t,p in zip(ts,ps))
        q_mix = sum(t*q for t,q in zip(ts,qs))
        lhs = TV(p_mix, q_mix)
        rhs = sum(t*TV(p,q) for t,p,q in zip(ts,ps,qs))
        r[f"seed_{seed}"] = {"lhs":lhs,"rhs":rhs,"pass":bool(lhs <= rhs + 1e-12)}
    if torch is not None:
        p = torch.tensor([0.5,0.5], dtype=torch.float64); q = torch.tensor([0.3,0.7], dtype=torch.float64)
        r["torch_xcheck"] = {"pass": bool(abs(0.5*float((p-q).abs().sum()) - 0.2) < 1e-9)}
    return r

def run_negative_tests():
    r = {}
    rng = np.random.default_rng(3)
    n = 5
    p = rng.dirichlet(np.ones(n)); q = rng.dirichlet(np.ones(n))
    # TV is bounded by 1; any claim TV>1 fails
    r["tv_bounded_by_1"] = {"pass": bool(TV(p,q) <= 1.0 + 1e-12)}
    # anti-claim: TV(p,p) != 0 should fail
    r["tv_self_is_zero"] = {"pass": bool(TV(p,p) < 1e-12)}
    # wrong direction: claim lhs > rhs should generally fail
    k = 2
    ts = np.array([0.5,0.5])
    ps = [rng.dirichlet(np.ones(n)) for _ in range(k)]
    qs = [rng.dirichlet(np.ones(n)) for _ in range(k)]
    lhs = TV(sum(t*p for t,p in zip(ts,ps)), sum(t*q for t,q in zip(ts,qs)))
    rhs = sum(t*TV(p,q) for t,p,q in zip(ts,ps,qs))
    r["wrong_direction_fails"] = {"pass": bool(not (lhs > rhs + 1e-9))}
    return r

def run_boundary_tests():
    r = {}
    n = 4
    p = np.zeros(n); p[0]=1.0
    q = np.zeros(n); q[1]=1.0
    r["disjoint_vertices_tv_one"] = {"pass": bool(abs(TV(p,q)-1.0)<1e-12)}
    ts = np.array([1.0, 0.0])
    ps = [p, q]; qs = [q, p]
    lhs = TV(sum(t*pp for t,pp in zip(ts,ps)), sum(t*qq for t,qq in zip(ts,qs)))
    rhs = sum(t*TV(a,b) for t,a,b in zip(ts,ps,qs))
    r["degenerate_weights"] = {"pass": bool(lhs <= rhs + 1e-12)}
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
    results={"name":"tv_convex_admission_crosscouple_classical","classification":classification,
             "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
             "divergence_log":divergence_log,"positive":pos,"negative":neg,"boundary":bnd,
             "all_pass":bool(ap),"summary":{"all_pass":bool(ap)}}
    out_dir=os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(out_dir,exist_ok=True)
    out_path=os.path.join(out_dir,"tv_convex_admission_crosscouple_classical_results.json")
    with open(out_path,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={ap} -> {out_path}")
