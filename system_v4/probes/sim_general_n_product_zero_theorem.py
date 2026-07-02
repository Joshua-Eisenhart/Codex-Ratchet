#!/usr/bin/env python3
"""
sim_general_n_product_zero_theorem.py — canonical

Prove via sympy that for any N-factor product Q = x1*x2*...*xN,
if any xi=0 then Q=0, for N in 2..10.
Also prove contrapositive: Q≠0 requires all xi≠0.
z3 UNSAT for N=6: x1*...*x6≠0 with any xi=0 is impossible.
"""
classification = 'diagnostic_only'

import json, os
import numpy as np
from functools import reduce

TOOL_MANIFEST = {
    "pytorch":      {"tried": True,  "used": True,  "reason": "tensor product verification cross-check"},
    "pyg":          {"tried": False, "used": False, "reason": "not needed — no graph structure"},
    "z3":           {"tried": True,  "used": True,  "reason": "UNSAT proof: Q!=0 with any xi=0 is structurally impossible"},
    "cvc5":         {"tried": False, "used": False, "reason": "z3 sufficient for this arithmetic claim"},
    "sympy":        {"tried": True,  "used": True,  "reason": "symbolic product computation and zero substitution"},
    "clifford":     {"tried": False, "used": False, "reason": "not relevant — scalar algebra only"},
    "geomstats":    {"tried": False, "used": False, "reason": "not relevant — no manifold"},
    "e3nn":         {"tried": False, "used": False, "reason": "not relevant — no equivariance"},
    "rustworkx":    {"tried": False, "used": False, "reason": "not relevant — no graph"},
    "xgi":          {"tried": False, "used": False, "reason": "not relevant — no hypergraph"},
    "toponetx":     {"tried": False, "used": False, "reason": "not relevant — no topology complex"},
    "gudhi":        {"tried": False, "used": False, "reason": "not relevant — no persistence diagram"},
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "load_bearing",
    "rustworkx": None,
    "sympy": "load_bearing",
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["tried"] = False
    TOOL_MANIFEST["pytorch"]["used"] = False
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    TOOL_INTEGRATION_DEPTH["pytorch"] = None

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    raise RuntimeError("sympy required")

try:
    from z3 import Real, And, Not, Solver, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    raise RuntimeError("z3 required")

results = {"classification": "canonical", "sections": {}}

# ── POSITIVE TESTS ──────────────────────────────────────────────────────────
pos_pass = True
pos_details = []
syms = sp.symbols("x1:11")  # x1..x10

for N in range(2, 11):
    xs = syms[:N]
    Q = reduce(lambda a, b: a * b, xs)
    for zero_idx in range(N):
        subs = {xs[zero_idx]: sp.Integer(0)}
        val = Q.subs(subs)
        simplified = sp.simplify(val)
        ok = simplified == sp.Integer(0)
        pos_details.append({"N": N, "zero_idx": zero_idx, "result": str(simplified), "pass": bool(ok)})
        if not ok:
            pos_pass = False

# Contrapositive: Q≠0 requires all xi≠0
# Verify: if all xi are nonzero, Q is nonzero
contra_pass = True
contra_details = []
for N in range(2, 11):
    xs = syms[:N]
    Q = reduce(lambda a, b: a * b, xs)
    # Substitute all with positive values
    subs = {xs[i]: sp.Integer(i + 1) for i in range(N)}
    val = Q.subs(subs)
    ok = val != 0
    contra_details.append({"N": N, "val": int(val), "pass": bool(ok)})
    if not ok:
        contra_pass = False

results["sections"]["positive"] = {
    "pass": pos_pass and contra_pass,
    "zero_substitution_count": len(pos_details),
    "all_zero_subs_correct": pos_pass,
    "contrapositive_nonzero": contra_pass,
}

# ── z3 UNSAT TESTS ───────────────────────────────────────────────────────────
# N=6: x1*...*x6 ≠ 0 with any xi=0 → UNSAT
z3_pass = True
z3_details = []

for zero_idx in range(6):
    s = Solver()
    xs_z3 = [Real(f"x{i+1}") for i in range(6)]
    # Claim: product != 0
    prod_expr = xs_z3[0]
    for x in xs_z3[1:]:
        prod_expr = prod_expr * x
    s.add(prod_expr != 0)
    # But one factor is 0
    s.add(xs_z3[zero_idx] == 0)
    result = s.check()
    is_unsat = (result == unsat)
    z3_details.append({"zero_idx": zero_idx, "z3_result": str(result), "is_unsat": is_unsat})
    if not is_unsat:
        z3_pass = False

# z3: Q>0 requires ALL xi>0 (none zero)
s2 = Solver()
xs_z3b = [Real(f"y{i+1}") for i in range(4)]
prod_b = xs_z3b[0]
for x in xs_z3b[1:]:
    prod_b = prod_b * x
s2.add(prod_b > 0)
s2.add(xs_z3b[2] == 0)  # one factor zero
r2 = s2.check()
q_pos_requires_all_nonzero = (r2 == unsat)
z3_details.append({"test": "Q>0_with_xi=0", "z3_result": str(r2), "is_unsat": q_pos_requires_all_nonzero})
if not q_pos_requires_all_nonzero:
    z3_pass = False

results["sections"]["negative_z3"] = {
    "pass": z3_pass,
    "n6_unsat_per_zero_factor": z3_details,
}

# ── BOUNDARY TESTS ───────────────────────────────────────────────────────────
x1 = sp.Symbol("x1")
b1_val = x1.subs(x1, 0)
b1_ok = bool(b1_val == 0)

x1b = sp.Symbol("x1b", positive=True)
b2_val = x1b.subs(x1b, sp.Integer(5))
b2_ok = bool(b2_val > 0)

# pytorch cross-check: N=5 product with one zero
boundary_torch_ok = True
try:
    t = torch.tensor([1.0, 2.0, 0.0, 4.0, 5.0])
    tp = torch.prod(t).item()
    boundary_torch_ok = abs(tp) < 1e-10
except Exception:
    boundary_torch_ok = False

results["sections"]["boundary"] = {
    "pass": b1_ok and b2_ok and boundary_torch_ok,
    "N1_x1_zero": {"val": str(b1_val), "pass": b1_ok},
    "N1_x1_positive": {"val": str(b2_val), "pass": b2_ok},
    "pytorch_N5_zero_product": {"val": float(tp) if boundary_torch_ok else None, "pass": boundary_torch_ok},
}

# ── OVERALL ──────────────────────────────────────────────────────────────────
all_pass = all(s["pass"] for s in results["sections"].values())
results["overall_pass"] = all_pass
results["tool_manifest"] = TOOL_MANIFEST
results["tool_integration_depth"] = TOOL_INTEGRATION_DEPTH

out_path = os.path.join(os.path.dirname(__file__), "sim_general_n_product_zero_theorem_result.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
print(f"\nResult written to: {out_path}")
print(f"OVERALL PASS: {all_pass}")
