#!/usr/bin/env python3
"""
Canonical shell-local U(1) charge-sector selection probe.

QED-style shell-local claim: local U(1) charge sectors that survive 2*pi phase closure are
integer-labeled QED sectors, while fractional labels are excluded on this single-shell carrier.
"""

import json
import os

classification = "canonical"
NAME = "sim_u1_charge_sector_selection_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor numerics are not needed for integer charge-sector admissibility"},
    "pyg": {"tried": False, "used": False, "reason": "graph tooling is not needed for one-shell charge labels"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 handles the load-bearing integer/rational sector arithmetic here"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 proves shell-local charge labels survive 2*pi closure only when the sector is integer-valued"},
    "sympy": {"tried": False, "used": False, "reason": "sympy symbolically checks exp(i(alpha+2*pi*q))=exp(i alpha) for integer charge q"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for scalar U(1) charge sectors"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are not needed for local charge closure"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this local charge-sector lane"},
    "rustworkx": {"tried": False, "used": False, "reason": "cycle graphs are not needed for single-shell charge labels"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for local charge admissibility"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are not needed for charge-sector arithmetic"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for one-shell charge closure"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

for _name, _importer in [
    ("pytorch", lambda: __import__("torch")),
    ("pyg", lambda: __import__("torch_geometric")),
    ("z3", lambda: __import__("z3")),
    ("clifford", lambda: __import__("clifford")),
    ("geomstats", lambda: __import__("geomstats")),
    ("e3nn", lambda: __import__("e3nn")),
    ("rustworkx", lambda: __import__("rustworkx")),
    ("xgi", lambda: __import__("xgi")),
    ("toponetx", lambda: __import__("toponetx")),
    ("gudhi", lambda: __import__("gudhi")),
]:
    try:
        _importer()
        TOOL_MANIFEST[_name]["tried"] = True
    except Exception as exc:
        TOOL_MANIFEST[_name]["reason"] = f"not installed: {exc}"

import cvc5
TOOL_MANIFEST["cvc5"]["tried"] = True

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def sector_is_admissible(num: int, den: int = 1) -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIRA")
    int_sort = solver.getIntegerSort()
    real_sort = solver.getRealSort()
    charge = solver.mkConst(int_sort, "charge")
    sector = solver.mkConst(real_sort, "sector")
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, sector, solver.mkTerm(cvc5.Kind.TO_REAL, charge)))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, sector, solver.mkReal(num, den)))
    return solver.checkSat().isSat()


def run_positive_tests():
    results = {
        "unit_charge_sector_survives": {"pass": bool(sector_is_admissible(1, 1))},
        "double_charge_sector_survives": {"pass": bool(sector_is_admissible(2, 1))},
    }
    TOOL_MANIFEST["cvc5"]["used"] = True
    if sp is not None:
        alpha = sp.symbols("alpha", real=True)
        q = sp.symbols("q", integer=True)
        closure = sp.simplify(sp.exp(sp.I * (alpha + 2 * sp.pi * q)) - sp.exp(sp.I * alpha)) == 0
        results["sympy_integer_charge_closure"] = {"pass": bool(closure)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_integer_charge_closure"] = {"pass": False, "reason": "sympy unavailable"}
    return results


def run_negative_tests():
    return {
        "half_charge_sector_excluded": {"pass": bool(not sector_is_admissible(1, 2))},
        "third_charge_sector_excluded": {"pass": bool(not sector_is_admissible(1, 3))},
    }


def run_boundary_tests():
    return {
        "neutral_sector_survives": {"pass": bool(sector_is_admissible(0, 1))},
        "negative_integer_sector_survives": {"pass": bool(sector_is_admissible(-1, 1))},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local QED-style charge sectors on a U(1) carrier",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "passes_local_rerun": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, RESULTS_BASENAME)
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"{NAME}: {'PASS' if all_pass else 'FAIL'} -> {out_path}")
