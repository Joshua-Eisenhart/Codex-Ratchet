#!/usr/bin/env python3
"""
sim_sympy_capability.py -- Tool-capability isolation sim for sympy.

Governing rule (durable, owner+Hermes 2026-04-13):
sympy is load_bearing in many symbolic-algebra sims; no capability probe existed.
Bounded isolation probe for the symbolic primitives we actually rely on:
Matrix eigenvals, simplify, solve, commutator (Lie bracket).

Decorative = `import sympy` without a symbolic result affecting the claim.
Load-bearing = a simplified/solved/eigen expression IS the claim.
"""

classification = "canonical"

import json
import os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- symbolic probe"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed"},
    "z3":        {"tried": False, "used": False, "reason": "not needed"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed"},
    "sympy":     {"tried": False, "used": False, "reason": "under test"},
    "clifford":  {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "geomstats": {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "e3nn":      {"tried": False, "used": False, "reason": "not geometry-relevant"},
    "rustworkx": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "xgi":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant"},
    "gudhi":     {"tried": False, "used": False, "reason": "not topology-relevant"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "capability under test -- eigenvals, simplify, solve, commutator"
    SP_OK = True
    SP_VERSION = sp.__version__
except Exception as exc:
    SP_OK = False
    SP_VERSION = None
    TOOL_MANIFEST["sympy"]["reason"] = f"not installed: {exc}"


def run_positive_tests():
    r = {}
    if not SP_OK:
        r["sympy_available"] = {"pass": False, "detail": "sympy missing"}
        return r
    r["sympy_available"] = {"pass": True, "version": SP_VERSION}

    # 1. Matrix eigenvalues of Pauli Z: should be {+1, -1}.
    sigma_z = sp.Matrix([[1, 0], [0, -1]])
    eigs = sigma_z.eigenvals()
    keys = {int(k) for k in eigs.keys()}
    r["pauli_z_eigenvalues"] = {
        "pass": keys == {1, -1},
        "got": sorted(keys),
        "expected": [-1, 1],
    }

    # 2. simplify: sin^2 + cos^2 = 1.
    x = sp.Symbol("x")
    expr = sp.sin(x) ** 2 + sp.cos(x) ** 2
    simplified = sp.simplify(expr)
    r["trig_identity_simplify"] = {
        "pass": simplified == 1,
        "got": str(simplified),
    }

    # 3. solve: x^2 - 4 = 0 => x in {-2, 2}.
    sols = sp.solve(x ** 2 - 4, x)
    r["quadratic_solve"] = {
        "pass": set(sols) == {-2, 2},
        "got": sorted(sols),
    }

    # 4. Commutator [sigma_x, sigma_y] = 2i sigma_z (load-bearing Lie bracket).
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    comm = sx * sy - sy * sx
    expected = 2 * sp.I * sz
    r["commutator_pauli_xy"] = {
        "pass": sp.simplify(comm - expected) == sp.zeros(2, 2),
        "got": str(comm),
        "expected": str(expected),
    }

    return r


def run_negative_tests():
    r = {}
    if not SP_OK:
        r["sympy_available"] = {"pass": False, "detail": "sympy missing"}
        return r

    # Expression that is NOT identically 1 should not simplify to 1.
    x = sp.Symbol("x")
    not_identity = sp.sin(x) ** 2 - sp.cos(x) ** 2
    r["not_identity_detected"] = {
        "pass": sp.simplify(not_identity - 1) != 0,
    }

    # Unsolvable-over-reals equation should have non-real solutions.
    sols = sp.solve(sp.Symbol("y") ** 2 + 1, sp.Symbol("y"))
    all_nonreal = all(not s.is_real for s in sols)
    r["nonreal_roots_detected"] = {
        "pass": all_nonreal and len(sols) == 2,
        "got": [str(s) for s in sols],
    }

    # Non-commuting matrices must have non-zero commutator.
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    comm = sx * sz - sz * sx
    r["noncommuting_detected"] = {
        "pass": comm != sp.zeros(2, 2),
    }
    return r


def run_boundary_tests():
    r = {}
    if not SP_OK:
        r["sympy_available"] = {"pass": False, "detail": "sympy missing"}
        return r

    # Empty solve returns [] (no x).
    sols = sp.solve(sp.Integer(0), sp.Symbol("x"))
    # solving 0==0 has infinite solutions; sympy returns [] meaning "any x".
    r["trivial_solve_returns_list"] = {
        "pass": isinstance(sols, list),
        "got": str(sols),
    }

    # Zero matrix eigenvalues: all zero.
    Z = sp.zeros(3, 3)
    eigs = Z.eigenvals()
    r["zero_matrix_eigenvals"] = {
        "pass": set(eigs.keys()) == {0},
        "got": list(eigs.keys()),
    }

    # Simplify of large but trivially-zero expression.
    x = sp.Symbol("x")
    expr = (x + 1) ** 3 - (x ** 3 + 3 * x ** 2 + 3 * x + 1)
    r["polynomial_expansion_zero"] = {
        "pass": sp.simplify(expr) == 0,
    }
    return r


def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_sympy_capability",
        "purpose": "Tool-capability isolation probe for sympy -- unblocks symbolic load-bearing use.",
        "sympy_version": SP_VERSION,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "witness_file": "system_v4/probes/sim_assoc_bundle_canonical_connection_from_hopf.py",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sympy_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
