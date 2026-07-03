#!/usr/bin/env python3
"""sim_gtower_deep_so_lie_algebra_structure_constants -- Deep G-tower lego.

Claim (admissibility):
  so(3) antisymmetric generators L1,L2,L3 satisfy [Li,Lj]=eps_ijk Lk.
  Candidates violating this structure are EXCLUDED from so(3).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- so(3) bracket fence.
"""
import json, os
import numpy as np

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
 'numpy': {'reason': 'NumPy appears only in the existing manifest scaffold or imports without a '
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
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def L(i):
    M = sp.zeros(3,3)
    for a in range(3):
        for b in range(3):
            if a==b: continue
            # eps_{i,a,b} generator (Lk)_{ab} = -eps_{kab}
            eps = sp.LeviCivita(i,a,b)
            M[a,b] = -eps
    return M


def bracket(A,B):
    return A*B - B*A


def run_positive_tests():
    r = {}
    L1,L2,L3 = L(0),L(1),L(2)
    # [L1,L2] = L3, [L2,L3]=L1, [L3,L1]=L2
    r["L1_L2"] = {"pass": bracket(L1,L2) == L3}
    r["L2_L3"] = {"pass": bracket(L2,L3) == L1}
    r["L3_L1"] = {"pass": bracket(L3,L1) == L2}
    # Jacobi identity
    J = bracket(L1, bracket(L2,L3)) + bracket(L2, bracket(L3,L1)) + bracket(L3, bracket(L1,L2))
    r["jacobi"] = {"pass": J == sp.zeros(3,3)}
    return r


def run_negative_tests():
    r = {}
    L1,L2 = L(0),L(1)
    # Symmetric (non-antisymm) matrix is excluded from so(3) -- fails antisymmetry
    S = sp.Matrix([[1,2,0],[2,3,0],[0,0,0]])
    r["symmetric_excluded"] = {"pass": S != -S.T}
    # Bracket that does NOT match Levi-Civita (swap sign)
    r["wrong_sign_excluded"] = {"pass": bracket(L1,L2) != -L(2)}
    return r


def run_boundary_tests():
    r = {}
    # zero matrix is trivially antisymmetric but gives trivial bracket
    Z = sp.zeros(3,3)
    r["zero_trivial"] = {"pass": bracket(Z, L(0)) == sp.zeros(3,3)}
    # scaled generator: [aL1,L2] = a L3
    a = sp.symbols('a')
    r["scaling_linear"] = {"pass": sp.simplify(bracket(a*L(0), L(1)) - a*L(2)) == sp.zeros(3,3)}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic Lie bracket + Jacobi decide so(3) admissibility"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    results = {
        "name": "sim_gtower_deep_so_lie_algebra_structure_constants",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: so(3) bracket fence",
        "language": "admissible iff [Li,Lj]=eps_ijk Lk and Jacobi holds; else excluded",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sim_gtower_deep_so_lie_algebra_structure_constants_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
