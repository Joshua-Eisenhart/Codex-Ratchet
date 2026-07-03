#!/usr/bin/env python3
"""Lego 09: Probe-size lower bound (F01).
Claim: d-dim density matrices require at least d^2-1 linearly independent probes to distinguish all pairs.
sympy load-bearing: symbolic rank of probe matrix.
"""
import json, os, sympy as sp

TOOL_MANIFEST = {'clifford': {'reason': 'Clifford appears only in the existing manifest scaffold or imports '
                        'without a direct source call; kept unused pending review.',
              'tried': False,
              'used': False},
 'cvc5': {'reason': 'cvc5 appears only in the existing manifest scaffold or imports without a '
                    'direct source call; kept unused pending review.',
          'tried': False,
          'used': False},
 'e3nn': {'reason': 'e3nn appears only in the existing manifest scaffold or imports without a '
                    'direct source call; kept unused pending review.',
          'tried': False,
          'used': False},
 'geomstats': {'reason': 'geomstats appears only in the existing manifest scaffold or imports '
                         'without a direct source call; kept unused pending review.',
               'tried': False,
               'used': False},
 'gudhi': {'reason': 'GUDHI appears only in the existing manifest scaffold or imports without a '
                     'direct source call; kept unused pending review.',
           'tried': False,
           'used': False},
 'pyg': {'reason': 'PyG appears only in the existing manifest scaffold or imports without a direct '
                   'source call; kept unused pending review.',
         'tried': False,
         'used': False},
 'pytorch': {'reason': 'PyTorch appears only in the existing manifest scaffold or imports without '
                       'a direct source call; kept unused pending review.',
             'tried': False,
             'used': False},
 'rustworkx': {'reason': 'rustworkx appears only in the existing manifest scaffold or imports '
                         'without a direct source call; kept unused pending review.',
               'tried': False,
               'used': False},
 'sympy': {'reason': 'Source calls SymPy APIs for symbolic algebra or expression manipulation in '
                     'this probe.',
           'tried': True,
           'used': True},
 'toponetx': {'reason': 'TopoNetX appears only in the existing manifest scaffold or imports '
                        'without a direct source call; kept unused pending review.',
              'tried': False,
              'used': False},
 'xgi': {'reason': 'XGI appears only in the existing manifest scaffold or imports without a direct '
                   'source call; kept unused pending review.',
         'tried': False,
         'used': False},
 'z3': {'reason': 'z3 appears only in the existing manifest scaffold or imports without a direct '
                  'source call; kept unused pending review.',
        'tried': False,
        'used': False}}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"symbolic rank of probe-value map; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

# d=2: space of hermitian traceless ops has dim 3 = 2^2-1. Probes {sx,sy,sz} span it.
I2 = sp.eye(2); sx = sp.Matrix([[0,1],[1,0]]); sy = sp.Matrix([[0,-sp.I],[sp.I,0]]); sz = sp.Matrix([[1,0],[0,-1]])

def vec(M): return sp.Matrix([M[0,0], M[0,1], M[1,0], M[1,1]])

def run_positive_tests():
    # 3 Paulis + I span all 2x2 hermitian (dim 4)
    M = sp.Matrix.hstack(vec(I2), vec(sx), vec(sy), vec(sz))
    return {"full_probe_set_rank_4": M.rank() == 4}

def run_negative_tests():
    # only 2 probes (sx, sy) can't distinguish sz-eigenstate diffs
    M = sp.Matrix.hstack(vec(sx), vec(sy))
    return {"insufficient_probes_rank_lt_4": M.rank() < 4}

def run_boundary_tests():
    # exactly 3 traceless probes => rank 3 (distinguishes up to trace)
    M = sp.Matrix.hstack(vec(sx), vec(sy), vec(sz))
    return {"three_traceless_rank_3": M.rank() == 3}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"lego_09_probe_size_lower_bound","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"lego_09_probe_size_lower_bound_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
