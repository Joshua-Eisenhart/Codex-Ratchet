#!/usr/bin/env python3
"""Pairwise coupling sim: holodeck x igt.

Coupling-program step 2: test whether shell-local admissible sets of
holodeck and igt intersect non-trivially under a joint admissibility
predicate (see _coupling_common.COUPLINGS).  z3 is load-bearing for
verifying per-pair admissibility (SAT) and exclusion (UNSAT).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _coupling_template import (
    TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH,
    run_positive_tests, run_negative_tests, run_boundary_tests, main,
)

classification = "canonical"
TOOL_MANIFEST = {
    "z3": {"tried": True, "used": True, "reason": "joint admissibility SMT (load-bearing)"},
}
TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}

A, B = "holodeck", "igt"

if __name__ == "__main__":
    main(A, B, __file__)
