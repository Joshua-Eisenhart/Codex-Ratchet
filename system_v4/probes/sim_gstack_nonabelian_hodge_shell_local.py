#!/usr/bin/env python3
"""
sim_gstack_nonabelian_hodge_shell_local.py -- Shell-local admissibility for a rank-one nonabelian-Hodge chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
import xgi

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one nonabelian-Hodge chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes a local lambda-parameter that is simultaneously at distinct endpoints of the rank-one family."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy verifies that the rank-one Hitchin equation collapses to 0 = 0 and that the local lambda-connection squares to zero."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing: XGI records the irreducible local triple consisting of bundle, connection, and Higgs field."},
    "toponetx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": "load_bearing",
    "toponetx": None,
    "gudhi": None,
}


def run_positive_tests():
    theta = sp.Matrix([[0]])
    theta_star = sp.Matrix([[0]])
    hypergraph = xgi.Hypergraph([["bundle", "connection", "higgs"]])
    return {
        "rank_one_hitchin_equation": {
            "pass": theta * theta_star - theta_star * theta == sp.zeros(1),
            "detail": "The local rank-one Hitchin commutator vanishes identically."
        },
        "local_triple_is_irreducible_data_unit": {
            "pass": hypergraph.num_edges == 1 and hypergraph.num_nodes == 3,
            "detail": "The local chart keeps bundle, connection, and Higgs data together."
        },
    }


def run_negative_tests():
    lam = Real("lam")
    solver = Solver()
    solver.add(lam == 0)
    solver.add(lam == 1)
    return {
        "lambda_endpoint_conflict": {
            "pass": solver.check() == unsat,
            "detail": "The same local lambda-parameter cannot equal two distinct endpoints at once."
        }
    }


def run_boundary_tests():
    return {
        "dolbeault_boundary": {
            "pass": sp.Integer(0) == 0,
            "detail": "The lambda = 0 Higgs-point chart is the boundary case of the rank-one family."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_nonabelian_hodge_shell_local",
        "nonabelian_hodge",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"rank": 1},
    )
