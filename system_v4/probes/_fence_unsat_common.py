"""Shared helpers for BC/T fence UNSAT sims.

Each fence sim builds a z3 (or cvc5) encoding of a "smuggled" axiom plus a
preserved witness that contradicts it. UNSAT on the conjunction = fence holds
by construction (exclusion). SAT on the smuggled axiom alone (no witness) =
negative control. UNSAT independent of one extra dummy assertion = boundary.
"""
from __future__ import annotations

TOOL_MANIFEST_BASE = {
    "pytorch":   {"tried": False, "used": False, "reason": "fence is FOL admissibility, not numeric"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph message passing"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": "fence is relational, not symbolic algebra"},
    "clifford":  {"tried": False, "used": False, "reason": "no geometric algebra content"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph search"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistent homology"},
}


def fresh_manifest():
    import copy
    return copy.deepcopy(TOOL_MANIFEST_BASE)
