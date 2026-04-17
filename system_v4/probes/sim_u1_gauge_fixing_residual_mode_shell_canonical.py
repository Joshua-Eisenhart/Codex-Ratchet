#!/usr/bin/env python3
"""
Canonical shell-local U(1) gauge-fixing residual-mode probe.

QED-style shell-local claim: after local pure-gauge fixing on one cycle, the surviving
residual U(1) transformations are constant modes only; non-constant modes are excluded.
"""

import json
import os

classification = "canonical"
NAME = "sim_u1_gauge_fixing_residual_mode_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor numerics are not needed for residual-mode satisfiability"},
    "pyg": {"tried": False, "used": False, "reason": "graph message passing is not needed for one-cycle residual modes"},
    "z3": {"tried": False, "used": False, "reason": "z3 provides the load-bearing shell-local SAT/UNSAT witness that only constant residual modes survive gauge fixing"},
    "cvc5": {"tried": False, "used": False, "reason": "z3 already supplies the satisfiability witness for the local residual-mode shell"},
    "sympy": {"tried": False, "used": False, "reason": "sympy solves the same linear equal-difference system as a supportive algebraic cross-check"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not needed for scalar residual gauge modes"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are not needed for this local gauge-fixing shell"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this shell-local gauge-fixing lane"},
    "rustworkx": {"tried": False, "used": False, "reason": "graph construction is not needed beyond the local cycle equations encoded directly"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for residual U(1) modes on one cycle"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are not needed for the direct local gauge-fixing equations"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for residual-mode satisfiability"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

for _name, _importer in [
    ("pytorch", lambda: __import__("torch")),
    ("pyg", lambda: __import__("torch_geometric")),
    ("cvc5", lambda: __import__("cvc5")),
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

from z3 import Ints, Solver, sat, unsat
TOOL_MANIFEST["z3"]["tried"] = True

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def residual_mode_status(extra_constraints=None):
    chi0, chi1, chi2, chi3 = Ints("chi0 chi1 chi2 chi3")
    solver = Solver()
    solver.add(chi1 - chi0 == 0)
    solver.add(chi2 - chi1 == 0)
    solver.add(chi3 - chi2 == 0)
    solver.add(chi0 - chi3 == 0)
    if extra_constraints:
        solver.add(*extra_constraints([chi0, chi1, chi2, chi3]))
    return solver.check()


def run_positive_tests():
    results = {
        "constant_mode_family_nonempty": {"pass": bool(residual_mode_status() == sat)},
        "shifted_constant_mode_survives": {"pass": bool(residual_mode_status(lambda chis: [chis[0] == 3]) == sat)},
    }
    TOOL_MANIFEST["z3"]["used"] = True
    if sp is not None:
        chi0, chi1, chi2, chi3 = sp.symbols("chi0 chi1 chi2 chi3")
        solution = sp.linsolve([
            chi1 - chi0,
            chi2 - chi1,
            chi3 - chi2,
            chi0 - chi3,
        ], [chi0, chi1, chi2, chi3])
        expected = {(chi3, chi3, chi3, chi3)}
        results["sympy_residual_family_is_constant"] = {"pass": bool(solution == expected)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_residual_family_is_constant"] = {"pass": False, "reason": "sympy unavailable"}
    return results


def run_negative_tests():
    return {
        "adjacent_difference_mode_excluded": {"pass": bool(residual_mode_status(lambda chis: [chis[1] == chis[0] + 1]) == unsat)},
        "alternating_mode_excluded": {"pass": bool(residual_mode_status(lambda chis: [chis[0] == 0, chis[1] == 0, chis[2] == 1]) == unsat)},
    }


def run_boundary_tests():
    return {
        "zero_mode_survives": {"pass": bool(residual_mode_status(lambda chis: [chis[0] == 0]) == sat)},
        "large_constant_mode_survives": {"pass": bool(residual_mode_status(lambda chis: [chis[0] == 9, chis[1] == 9, chis[2] == 9, chis[3] == 9]) == sat)},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local QED-style residual U(1) modes after one-cycle gauge fixing",
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
