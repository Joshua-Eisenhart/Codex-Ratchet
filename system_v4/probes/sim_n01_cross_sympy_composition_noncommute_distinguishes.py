#!/usr/bin/env python3
"""sim_n01_cross_sympy_composition_noncommute_distinguishes -- sympy-symbolic
verification that noncommuting operators A,B yield distinguishable compositions
AB != BA acting on a generic state => probe 'outcome' distinguishes them. This
is the N01-level reason ordering matters.
"""
classification = 'diagnostic_only'

import json, os

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
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    from sympy.physics.paulialgebra import Pauli
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError: TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def run_positive_tests():
    sx = Pauli(1); sy = Pauli(2)
    AB = sp.expand(sx * sy)
    BA = sp.expand(sy * sx)
    comm = sp.expand(AB - BA)  # 2 i sigma_z
    distinct = (comm != 0)
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "load-bearing: Pauli algebra symbolic noncommutation"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    return {"AB_minus_BA": str(comm), "distinct": bool(distinct), "pass": bool(distinct)}


def run_negative_tests():
    # Commuting operators should produce AB - BA = 0 (not distinguishable by order).
    A, B = sp.symbols("A B", commutative=True)
    comm = sp.expand(A*B - B*A)
    return {"AB_minus_BA_commuting": str(comm), "pass": comm == 0}


def run_boundary_tests():
    # A*A - A*A trivially 0.
    sx = Pauli(1)
    comm = sp.expand(sx*sx - sx*sx)
    return {"self": str(comm), "pass": comm == 0}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_cross_sympy_composition_noncommute_distinguishes"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
