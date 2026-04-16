#!/usr/bin/env python3
"""Pairwise coupling sim: holodeck x sci_method.

Coupling-program step 2: test whether shell-local admissible sets of
holodeck and sci_method intersect non-trivially under a joint admissibility
predicate (see _coupling_common.COUPLINGS).  z3 is load-bearing for
verifying per-pair admissibility (SAT) and exclusion (UNSAT).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _coupling_template import (
    TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH,
    run_positive_tests, run_negative_tests, run_boundary_tests, main,
)

A, B = "holodeck", "sci_method"
classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed; pair coupling is a finite SMT check"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no graph learning required"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: per-pair admissibility and exclusion are verified by SMT"},
    "cvc5": {"tried": False, "used": False, "reason": "z3 is sufficient for the coupling witness"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; coupling is finite SMT"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; no geometric algebra in this wrapper"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; no manifold computation required"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed; no equivariant network required"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; finite pair check only"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; no cell complex structure"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed; no persistent homology"},
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
