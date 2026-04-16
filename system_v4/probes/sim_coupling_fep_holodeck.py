#!/usr/bin/env python3
"""Pairwise coupling sim: fep x holodeck.

Coupling-program step 2: test whether shell-local admissible sets of
fep and holodeck intersect non-trivially under a joint admissibility
predicate (see _coupling_common.COUPLINGS).  z3 is load-bearing for
verifying per-pair admissibility (SAT) and exclusion (UNSAT).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _coupling_template import (
    run_positive_tests, run_negative_tests, run_boundary_tests, main,
)

A, B = "fep", "holodeck"
classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "z3": {"tried": True, "used": True, "reason": "joint admissibility SMT (load-bearing)"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed; coupling is a finite SMT check"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

if __name__ == "__main__":
    main(A, B, __file__)
