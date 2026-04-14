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

if __name__ == "__main__":
    main(A, B, __file__)
