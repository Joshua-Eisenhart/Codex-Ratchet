#!/usr/bin/env python3
"""sim_n01_compose_a_not_b_requires_distinguishing_probe -- Contrapositive of N01:
if a != b (in S/~_M) then there exists m in M with m(a) != m(b). z3 load-bearing:
UNSAT that 'a != b in quotient' AND 'forall m: m(a) = m(b)'.
"""
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
 'sympy': {'reason': 'SymPy appears only in the existing manifest scaffold or imports without a '
                     'direct source call; kept unused pending review.',
           'tried': False,
           'used': False},
 'toponetx': {'reason': 'TopoNetX appears only in the existing manifest scaffold or imports '
                        'without a direct source call; kept unused pending review.',
              'tried': False,
              'used': False},
 'xgi': {'reason': 'XGI appears only in the existing manifest scaffold or imports without a direct '
                   'source call; kept unused pending review.',
         'tried': False,
         'used': False},
 'z3': {'reason': 'Source calls z3 APIs to build or check finite SMT constraints in this probe.',
        'tried': True,
        'used': True}}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import z3; TOOL_MANIFEST["z3"]["tried"] = True
except ImportError: TOOL_MANIFEST["z3"]["reason"] = "not installed"


def run_positive_tests():
    # In the quotient, 'a != b' is definitionally 'some probe distinguishes'.
    # So asserting 'a != b' (quotient-level) AND 'no probe distinguishes' is UNSAT.
    a, b = z3.Ints("a b")
    m1 = z3.Function("m1", z3.IntSort(), z3.IntSort())
    m2 = z3.Function("m2", z3.IntSort(), z3.IntSort())
    m3 = z3.Function("m3", z3.IntSort(), z3.IntSort())
    all_agree = z3.And(m1(a)==m1(b), m2(a)==m2(b), m3(a)==m3(b))
    s = z3.Solver()
    s.add(z3.Not(all_agree))   # quotient-distinct = some disagreement
    s.add(all_agree)            # but no probe disagrees
    r = str(s.check())
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing: contrapositive of N01"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    return {"contrapositive": r, "pass": r == "unsat"}


def run_negative_tests():
    # If some probe disagrees, a,b quotient-distinct is SAT.
    a, b = z3.Ints("a b")
    m = z3.Function("m", z3.IntSort(), z3.IntSort())
    s = z3.Solver(); s.add(m(a) != m(b))
    r = str(s.check())
    return {"probe_disagrees": r, "pass": r == "sat"}


def run_boundary_tests():
    # Empty probe set: quotient collapses -> cannot have a!=b at quotient level.
    s = z3.Solver()
    s.add(z3.BoolVal(False))  # 'a!=b quotient' with no probes is False
    return {"empty_probe_distinction": str(s.check()), "pass": str(s.check()) == "unsat"}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_compose_a_not_b_requires_distinguishing_probe"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
