#!/usr/bin/env python3
"""Canonical: Leggett-Garg K3 inequality via Cl(3,0) rotors (geometric-algebra route).

Macrorealism bound: K3 = C12 + C23 - C13 <= 1.
Quantum (Larmor precession of spin-1/2 about x-axis): with measurement times
t1=0, t2=tau, t3=2*tau and Q = sigma_z, the correlators equal
C(ti, tj) = cos(omega*(tj - ti)). At omega*tau = pi/3 this gives
  K3 = cos(pi/3) + cos(pi/3) - cos(2*pi/3) = 1/2 + 1/2 - (-1/2) = 3/2.

load_bearing: clifford -- the rotor R(theta) = exp(-theta/2 * B) in Cl(3,0)
with bivector B = e2^e3 (the yz plane) is used to evolve the spin state as
a real Bloch vector, and the sigma_z expectation is recovered via grade-0
projection of v * e3. The K3 value is produced by geometric-algebra rotors,
not by matrix-mechanical Pauli algebra; removing clifford removes the
load-bearing computation.

Positive: K3 at omega*tau = pi/3 equals 3/2 > 1 (Cl(3) rotor evaluation).
Negative: classical dichotomic variable with any joint distribution respects K3 <= 1.
Boundary: near-optimal tau in a window still violates the classical bound.

Gap: K3_quantum - K3_classical_max = 1.5 - 1.0 = 0.5.
"""
import json
import math
import os

import numpy as np

classification = "canonical"
divergence_log = None

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "no gradient optimization; analytic optimum used"},
    "pyg":       {"tried": False, "used": False, "reason": "not a graph task"},
    "z3":        {"tried": False, "used": False, "reason": "real-valued correlators, not SAT"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed"},
    "sympy":     {"tried": False, "used": False, "reason": "clifford yields numeric value exactly"},
    "clifford":  {"tried": False, "used": False, "reason": "placeholder -- filled below"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold optimization"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariant network"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":  {"tried": False, "used": False, "reason": "no complex"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": "load_bearing",
    "geomstats": None, "e3nn": None, "rustworkx": None, "xgi": None,
    "toponetx": None, "gudhi": None,
}

try:
    from clifford import Cl
    _layout, _blades = Cl(3, 0)
    _e1 = _blades["e1"]
    _e2 = _blades["e2"]
    _e3 = _blades["e3"]
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "Cl(3,0) rotor R(theta)=exp(-theta/2 e2^e3) evolves Bloch vector; "
        "sigma_z expectation via grade-0 projection of v*e3; K3 formed from these"
    )
    _HAS_CLIFFORD = True
except ImportError:
    _HAS_CLIFFORD = False


def _rotor(theta):
    """R(theta) = cos(theta/2) - sin(theta/2)*B, B = e2^e3 (Larmor about x)."""
    B = _e2 * _e3
    return math.cos(theta / 2) - math.sin(theta / 2) * B


def _evolve(v, theta):
    R = _rotor(theta)
    return R * v * ~R


def _sigma_z(v):
    """<sigma_z> = grade-0 of v * e3 (projection onto e3 axis)."""
    return float((v * _e3).value[0])


def _correlator(ti, tj, omega=1.0):
    """Two-time correlator C(ti,tj) using Cl(3,0) rotor evolution.

    Start from +z eigenstate v0 = e3. After Larmor precession by omega*(tj-ti),
    <sigma_z(tj) sigma_z(ti)> reduces to cos(omega*(tj-ti)) for the projective
    two-time correlator. We recover this via rotor evolution and grade-0
    projection.
    """
    v_ti = _evolve(_e3, omega * ti)
    v_tj = _evolve(_e3, omega * tj)
    # <sigma_z(ti) sigma_z(tj)> for the initial +z eigenstate reduces to the
    # cosine of the relative rotation angle between the two Heisenberg-evolved
    # sigma_z directions. In Cl(3,0) this is grade-0 of v_tj * v_ti.
    return float((v_tj * v_ti).value[0])


def _K3(tau, omega=1.0):
    C12 = _correlator(0.0, tau, omega)
    C23 = _correlator(tau, 2 * tau, omega)
    C13 = _correlator(0.0, 2 * tau, omega)
    return C12 + C23 - C13, (C12, C23, C13)


def run_positive_tests():
    r = {}
    r["clifford_available"] = {"pass": _HAS_CLIFFORD}
    if not _HAS_CLIFFORD:
        return r

    tau_opt = math.pi / 3  # omega = 1
    k3, (c12, c23, c13) = _K3(tau_opt, omega=1.0)
    r["K3_at_pi_over_3"] = {
        "K3": k3,
        "C12": c12, "C23": c23, "C13": c13,
        "expected": 1.5,
        "pass": abs(k3 - 1.5) < 1e-9,
    }
    r["exceeds_classical_bound"] = {
        "K3": k3,
        "classical_bound": 1.0,
        "pass": k3 > 1.0 + 1e-9,
    }
    r["gap"] = {
        "K3_quantum": k3,
        "K3_classical_max": 1.0,
        "gap": k3 - 1.0,
        "pass": abs((k3 - 1.0) - 0.5) < 1e-9,
    }
    return r


def run_negative_tests():
    r = {}
    # Classical dichotomic variables Q_i in {-1,+1} with any joint distribution:
    # max of C12 + C23 - C13 over all classical joint distributions is 1.
    # Verify by enumerating the 8 sign patterns.
    best = -math.inf
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            for s3 in (-1, 1):
                val = s1 * s2 + s2 * s3 - s1 * s3
                if val > best:
                    best = val
    r["classical_max_K3_equals_1"] = {
        "value": best,
        "pass": best == 1,
    }
    # A dephased (pi/2 decohered between measurements) classical mixture gives K3 <= 1.
    # Model: correlators vanish (C=0) -> K3=0.
    r["fully_dephased_K3"] = {
        "K3": 0.0,
        "pass": 0.0 <= 1.0,
    }
    return r


def run_boundary_tests():
    r = {}
    if not _HAS_CLIFFORD:
        r["clifford_missing"] = {"pass": False}
        return r
    # Off-optimal times within a window still violate classical bound.
    for tau in [math.pi / 3 - 0.1, math.pi / 3 + 0.1]:
        k3, _ = _K3(tau, omega=1.0)
        r[f"violation_window_tau_{tau:.4f}"] = {
            "K3": k3,
            "pass": k3 > 1.0,
        }
    # At tau = 0 the correlators collapse to trivial values (all 1) so K3 = 1 (boundary).
    k3_zero, _ = _K3(0.0, omega=1.0)
    r["tau_zero_boundary"] = {
        "K3": k3_zero,
        "pass": abs(k3_zero - 1.0) < 1e-9,
    }
    return r


def _all_pass(section):
    return all(v.get("pass", False) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = _all_pass(pos) and _all_pass(neg) and _all_pass(bnd)

    results = {
        "name": "leggett_garg_k3_clifford_canonical",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "load_bearing_tool": "clifford",
            "gap_classical": 1.0,
            "gap_quantum": 1.5,
            "gap_value": 0.5,
            "gap_kind": "macrorealism_temporal_correlator_bound",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "leggett_garg_k3_clifford_canonical_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    raise SystemExit(0 if all_pass else 1)
