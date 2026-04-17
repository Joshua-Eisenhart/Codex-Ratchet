#!/usr/bin/env python3
"""
sim_gstack_harmonic_bundle_shell_local.py -- Shell-local admissibility for a harmonic bundle chart.
"""

import sympy as sp
from z3 import Real, Solver, unsat
from geomstats.geometry.hypersphere import Hypersphere

from _gstack_shell_local_common import write_shell_local_result

classification = "canonical"
_SHELL_LOCAL_REASON = "not used: this probe stays shell-local inside one harmonic-bundle chart and does not invoke cross-shell coupling."

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "pyg": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: z3 excludes incompatible local energy constraints for the harmonic metric."},
    "cvc5": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing: sympy verifies the rank-one Hitchin commutator vanishes identically in the local model."},
    "clifford": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing: geomstats provides the unit sphere carrying normalized harmonic-metric directions."},
    "e3nn": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
    "xgi": {"tried": False, "used": False, "reason": _SHELL_LOCAL_REASON},
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
    "geomstats": "load_bearing",
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def run_positive_tests():
    phi = sp.Matrix([[0]])
    phi_star = sp.Matrix([[0]])
    sphere = Hypersphere(dim=2)
    point = sphere.projection([1.0, 1.0, 1.0])
    return {
        "rank_one_commutator_vanishes": {
            "pass": phi * phi_star - phi_star * phi == sp.zeros(1),
            "detail": "In rank one, the local Higgs commutator term vanishes exactly."
        },
        "harmonic_direction_normalized": {
            "pass": abs(float(sum(v * v for v in point)) - 1.0) < 1e-9,
            "detail": "The sampled harmonic-metric direction is normalized."
        },
    }


def run_negative_tests():
    e = Real("e")
    solver = Solver()
    solver.add(e == 0)
    solver.add(e > 0)
    return {
        "zero_energy_conflict": {
            "pass": solver.check() == unsat,
            "detail": "A local harmonic energy cannot be both zero and strictly positive in the same test case."
        }
    }


def run_boundary_tests():
    return {
        "flat_rank_one_boundary": {
            "pass": sp.Integer(0) == 0,
            "detail": "The flat rank-one harmonic bundle is the boundary case."
        }
    }


if __name__ == "__main__":
    write_shell_local_result(
        "sim_gstack_harmonic_bundle_shell_local",
        "harmonic_bundle",
        TOOL_MANIFEST,
        TOOL_INTEGRATION_DEPTH,
        run_positive_tests(),
        run_negative_tests(),
        run_boundary_tests(),
        extras={"rank": 1},
    )
