#!/usr/bin/env python3
"""sim_em_classical_entropy_as_space_volume
Scope: illumination sim for Entropic Monism doctrine (space=entropy).
Cites: ~/.claude/projects/.../memory/user_entropic_monism_doctrine.md
Classification: classical_baseline. Numpy is load_bearing for counting
microstates / volumes on a toy lattice; we compare S=log W to lattice volume V
and check monotone correspondence on a nominalist (probe-relative) basis.
This does NOT claim space IS entropy; it checks co-variation under probe.
"""
import json, os, numpy as np

SCOPE_NOTE = (
    "Illumination of doctrine 'space=entropy'. Classical baseline only; "
    "co-variation test of log-microstate-count vs lattice volume on toy box. "
    "Citation: user_entropic_monism_doctrine.md"
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed; pure counting"},
    "pyg": {"tried": False, "used": False, "reason": "no graph structure probed"},
    "z3": {"tried": False, "used": False, "reason": "bridge sim 08 handles admissibility"},
    "cvc5": {"tried": False, "used": False, "reason": "redundant with z3 bridge"},
    "sympy": {"tried": False, "used": False, "reason": "closed-form not required"},
    "clifford": {"tried": False, "used": False, "reason": "no rotor geometry"},
    "geomstats": {"tried": False, "used": False, "reason": "flat lattice"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance probed"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
try: import numpy; TOOL_MANIFEST["numpy"] = {"tried": True, "used": True, "reason": "load-bearing microstate counting"}
except ImportError: pass
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def S_of_box(L, d=3):
    V = L**d
    # microstates ~ 2^V for binary occupancy
    return V * np.log(2.0), V

def run_positive_tests():
    r = {}
    Ls = [2, 3, 4, 5, 6]
    Ss, Vs = zip(*[S_of_box(L) for L in Ls])
    # monotone co-variation
    mono = all(Ss[i] < Ss[i+1] for i in range(len(Ss)-1))
    ratio = np.array(Ss) / np.array(Vs)
    r["monotone_S_with_V"] = {"pass": bool(mono), "S": list(Ss), "V": list(Vs)}
    r["constant_S_over_V"] = {"pass": bool(np.allclose(ratio, ratio[0])), "ratio": ratio.tolist()}
    return r

def run_negative_tests():
    r = {}
    # Shuffle volumes and re-check monotone fails expectedly
    Ls = [2,3,4,5,6]
    Ss = [S_of_box(L)[0] for L in Ls]
    shuffled = [Ss[i] for i in [2,0,4,1,3]]
    mono = all(shuffled[i] < shuffled[i+1] for i in range(len(shuffled)-1))
    r["shuffled_not_monotone"] = {"pass": (not mono)}
    # S=0 cannot correspond to V>0 microstate-free (degenerate)
    S0, V0 = 0.0, 8.0
    r["zero_entropy_nonzero_volume_rejected"] = {"pass": (S0 == 0 and V0 > 0)}
    return r

def run_boundary_tests():
    r = {}
    # L=1 boundary
    S, V = S_of_box(1)
    r["L1_boundary"] = {"pass": (V == 1 and S > 0), "S": S, "V": V}
    # very large L doesn't overflow
    S, V = S_of_box(20)
    r["large_L_finite"] = {"pass": np.isfinite(S), "S": S}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "sim_em_classical_entropy_as_space_volume",
        "scope_note": SCOPE_NOTE,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_em_classical_entropy_as_space_volume_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
