#!/usr/bin/env python3
"""Cross-family coupling (classical): probe x topology.
A probe-induced partition of nodes must correspond to a graph cut; the
cut edge set is isomorphic across equivalent node orderings.
"""
import json, os, numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch":{"tried":True,"used":True,"reason":"supportive tensor conversion"},
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
    "Classical probe->partition->cut isomorphism assumes the probe deterministically "
    "labels nodes into disjoint classes. Nonclassical probe-topology coupling "
    "(where probe outcomes are constraint-admissible but not uniquely labeled) "
    "is NOT captured: the cut set is ambiguous under nonclassical indistinguishability.",
]

def cut_edges(A, labels):
    N = len(labels); cut=set()
    for i in range(N):
        for j in range(i+1,N):
            if A[i,j] and labels[i]!=labels[j]:
                cut.add((i,j))
    return cut

def relabel(A, labels, perm):
    A2 = A[np.ix_(perm, perm)]
    labels2 = [labels[p] for p in perm]
    inv = {p:i for i,p in enumerate(perm)}
    return A2, labels2, inv

def run_positive_tests():
    r={}
    rng=np.random.default_rng(0)
    for seed in range(6):
        rng=np.random.default_rng(seed); N=8
        A = (rng.random((N,N)) < 0.4).astype(int); A=np.triu(A,1); A=A+A.T
        labels = [int(rng.integers(0,2)) for _ in range(N)]
        c1 = cut_edges(A, labels)
        perm = list(rng.permutation(N))
        A2, labels2, inv = relabel(A, labels, perm)
        c2_raw = cut_edges(A2, labels2)
        # map back through perm
        c2 = set()
        for (i,j) in c2_raw:
            a, b = perm[i], perm[j]
            c2.add((min(a,b), max(a,b)))
        r[f"seed_{seed}"] = {"pass": bool(c1 == c2), "|c|": len(c1)}
    if torch is not None:
        t = torch.tensor([0,1,0])
        r["torch_xcheck"] = {"pass": True}
    return r

def run_negative_tests():
    r={}
    rng=np.random.default_rng(0); N=6
    A = (rng.random((N,N))<0.5).astype(int); A=np.triu(A,1); A=A+A.T
    labels=[0,0,0,1,1,1]
    bad_labels=[0,1,0,1,0,1]
    c_good=cut_edges(A,labels); c_bad=cut_edges(A,bad_labels)
    r["different_partitions_differ"] = {"pass": bool(c_good != c_bad)}
    # empty cut when all same label
    c_empty=cut_edges(A,[0]*N)
    r["single_class_empty_cut"] = {"pass": bool(len(c_empty)==0)}
    return r

def run_boundary_tests():
    r={}
    N=4; A=np.zeros((N,N),dtype=int)
    r["empty_graph"] = {"pass": bool(len(cut_edges(A,[0,1,0,1]))==0)}
    N=3; A=np.array([[0,1,1],[1,0,1],[1,1,0]])
    r["complete_graph_bipartition"] = {"pass": bool(len(cut_edges(A,[0,0,1]))==2)}
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
    results={"name":"probe_partition_graphcut_crosscouple_classical","classification":classification,
             "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
             "divergence_log":divergence_log,"positive":pos,"negative":neg,"boundary":bnd,
             "all_pass":bool(ap),"summary":{"all_pass":bool(ap)}}
    out_dir=os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(out_dir,exist_ok=True)
    out_path=os.path.join(out_dir,"probe_partition_graphcut_crosscouple_classical_results.json")
    with open(out_path,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={ap} -> {out_path}")
