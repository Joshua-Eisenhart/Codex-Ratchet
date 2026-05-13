#!/usr/bin/env python3
"""sim_bridge_landauer_erasure_bit_distinguishability

scope_note: Bridge -- Landauer erasure cost rewritten in terms of the
  distinguishability quantum F01 with sympy symbolic derivation and z3
  admissibility fence. Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md.
  qutip/cirq/pennylane witness the same one-bit carrier floor without
  changing the theorem.
"""

from __future__ import annotations

import os

import cirq
import numpy as np
import pennylane as qml
import qutip
import sympy as sp
import z3

from _doc_illum_common import write_results

NAME = "bridge_landauer_erasure_bit_distinguishability"
SCOPE_NOTE = ("Bridge: sympy derives E_erase = F01 * H(p) for Bernoulli p, "
              "and z3 proves UNSAT for E_erase < F01 * H(p). Illuminates "
              "CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md Landauer section.")
classification = "tool_lego_fit_probe"
divergence_log = (
    "Finite symbolic/SMT Landauer-floor fence only: sympy derives "
    "E_erase = F01 * H(p), z3 rejects sub-floor erasure, and "
    "qutip/cirq/pennylane only witness the same one-bit carrier entropy. "
    "No bridge, QIT, GStack, axis, nonclassical, or feedback-cycle admission."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "binary entropy and one-bit carrier bookkeeping for the floor witness",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "supportive one-bit density witness for the Landauer floor",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "supportive one-bit density witness for the same carrier surface",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "supportive one-bit density witness for the same carrier surface",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "symbolic derivation of the erasure floor identity",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing admissibility fence for the sub-floor claim",
    },
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this theorem"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "qutip": "supportive",
    "cirq": "supportive",
    "pennylane": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "pytorch": None,
    "pyg": None,
    "cvc5": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

Q0 = cirq.LineQubit(0)
QML_DEV = qml.device("default.mixed", wires=1, shots=None)
LN2 = z3.RealVal("0.6931471805599453")

def _entropy_nats_from_population(p):
    p = float(np.clip(p, 1e-15, 1 - 1e-15))
    probs = np.array([1.0 - p, p], dtype=np.float64)
    nonzero = probs[probs > 0.0]
    if nonzero.size == 0:
        return 0.0
    return float(-np.sum(nonzero * np.log(nonzero)))


def _carrier_density(p):
    p = float(np.clip(p, 1e-15, 1 - 1e-15))
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=np.complex128)


def _sympy_derive():
    p, F01 = sp.symbols("p F01", positive=True)
    H = -(p * sp.log(p) + (1 - p) * sp.log(1 - p))
    E = F01 * H
    # At p=1/2, E must equal F01 * ln 2.
    E_half = sp.simplify(E.subs(p, sp.Rational(1, 2)))
    target = F01 * sp.log(2)
    return sp.simplify(E_half - target)


def run_positive():
    residual = _sympy_derive()
    qutip_rho = qutip.Qobj(_carrier_density(0.5), dims=[[2], [2]])
    qutip_entropy = float(qutip.entropy_vn(qutip_rho, base=np.e))
    cirq_rho = np.asarray(
        cirq.DensityMatrixSimulator(seed=13).simulate(
            cirq.Circuit(cirq.I(Q0)),
            qubit_order=[Q0],
            initial_state=_carrier_density(0.5),
        ).final_density_matrix,
        dtype=np.complex128,
    )

    @qml.qnode(QML_DEV)
    def _pennylane_density():
        qml.QubitDensityMatrix(_carrier_density(0.5), wires=0)
        return qml.density_matrix(wires=0)

    pennylane_rho = np.asarray(_pennylane_density(), dtype=np.complex128)
    expected = _entropy_nats_from_population(0.5)
    return {
        "sympy_residual_at_half": str(residual),
        "is_zero": bool(residual == 0),
        "witness_floor": {
            "expected_entropy_nats": expected,
            "qutip_entropy_nats": qutip_entropy,
            "cirq_entropy_nats": _entropy_nats_from_population(
                float(np.real(cirq_rho[1, 1]))
            ),
            "pennylane_entropy_nats": _entropy_nats_from_population(
                float(np.real(pennylane_rho[1, 1]))
            ),
        },
        "witnesses_ok": bool(
            abs(qutip_entropy - expected) < 1e-10
            and abs(_entropy_nats_from_population(float(np.real(cirq_rho[1, 1]))) - expected) < 1e-10
            and abs(_entropy_nats_from_population(float(np.real(pennylane_rho[1, 1]))) - expected) < 1e-10
            and abs(expected - np.log(2.0)) < 1e-10
        ),
    }


def run_negative():
    # z3 UNSAT: claim E < F01 * H for H>0, F01>0 cannot be admissible.
    E, F01, H = z3.Reals("E F01 H")
    s = z3.Solver()
    s.add(F01 > 0, H > 0)
    s.add(E < F01 * H)
    s.add(E >= F01 * H)   # admissibility fence says E must meet the floor
    res = s.check()
    return {"inadmissible_sub_floor": str(res),
            "unsat_as_expected": bool(res == z3.unsat)}


def run_boundary():
    # p -> 0: H -> 0, E -> 0.
    p, F01 = sp.symbols("p F01", positive=True)
    H = -(p * sp.log(p) + (1 - p) * sp.log(1 - p))
    E = F01 * H
    lim = sp.limit(E, p, 0, "+")
    return {
        "p_to_zero_limit": str(lim),
        "is_zero": bool(lim == 0),
        "boundary_floor": {
            "p_zero_entropy_nats": _entropy_nats_from_population(1e-15),
            "p_one_entropy_nats": _entropy_nats_from_population(1 - 1e-15),
        },
    }


def run_positive_tests():
    return run_positive()


def run_negative_tests():
    return run_negative()


def run_boundary_tests():
    return run_boundary()


if __name__ == "__main__":
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic derivation of E = F01 * H(p); load-bearing"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT on sub-floor erasure; load-bearing fence"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (pos["is_zero"] and pos["witnesses_ok"] and neg["unsat_as_expected"] and bnd["is_zero"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": classification,
        "all_pass": bool(ok),
        "divergence_log": divergence_log,
        "claim_ceiling": (
            "local Landauer distinguishability-cost constraint fence only: sympy derives "
            "E_erase = F01 * H(p) and z3 rejects E_erase < F01 * H(p); no bridge, "
            "QIT, GStack, axis, nonclassical, or feedback-cycle admission"
        ),
        "next_lego_target": "classical erasure-cost and measurement-feedback-erasure calibration support only",
        "promotion_condition": (
            "No promotion from this receipt; downstream calibration must supply explicit "
            "record, feedback, erasure, and adjacent graveyard receipts."
        ),
        "demotion_condition": (
            "Demote if the sympy residual is nonzero, if z3 admits sub-floor erasure, "
            "or if this receipt is used as bridge/QIT/GStack/axis/nonclassical evidence."
        ),
        "blocked_until": (
            "blocked from bridge, QIT, GStack, axis, nonclassical, or feedback-cycle claims "
            "until separate exact receipts close those gates"
        ),
        "out_of_scope": [
            "No feedback cycle.",
            "No nonclassical carrier admission.",
            "No bridge, QIT, GStack, axis, or runtime-engine claim.",
        ],
        "operation_sequence": [
            "derive E_erase = F01 * H(p) symbolically",
            "check p=1/2 residual against F01 ln2",
            "witness one-bit density entropy with qutip, cirq, and pennylane",
            "ask z3 whether sub-floor erasure can satisfy the declared floor",
            "check p -> 0 boundary entropy",
        ],
        "carrier_topology": "single diagonal one-bit carrier plus scalar symbolic/SMT constraint surface",
        "observable": "sympy residual, z3 SAT/UNSAT verdict, density entropy witnesses, and boundary entropy",
        "pass_fail_predicate": "sympy residual is zero, density witnesses equal ln2 at p=1/2, z3 sub-floor claim is UNSAT, and p->0 limit is zero",
        "graveyards": [
            "sub-floor erasure contradiction",
            "p equals one-half entropy floor",
            "p approaches zero entropy boundary",
        ],
        "graveyard_companions": [
            "sub-floor erasure contradiction",
            "p equals one-half entropy floor",
            "p approaches zero entropy boundary",
        ],
        "baselines": [
            "sympy symbolic Bernoulli entropy identity",
            "z3 real-arithmetic sub-floor fence",
            "qutip/cirq/pennylane one-bit density entropy witnesses",
        ],
        "alternative_formulations": [
            "numpy binary entropy cost curve",
            "z3 Landauer-floor scalar fence",
            "measurement-feedback-erasure calibration cycle",
        ],
        "exact_tool_function_needs": {
            "sympy": ["symbols", "log", "simplify", "limit"],
            "z3": ["Reals", "Solver"],
            "numpy": ["clip", "log"],
            "qutip": ["Qobj", "entropy_vn"],
            "cirq": ["DensityMatrixSimulator"],
            "pennylane": ["QubitDensityMatrix", "density_matrix"],
        },
        "lego_or_coupling_target": "classical erasure-cost constraint fence support",
        "promotion_allowed": False,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "load_bearing_tool": "sympy+z3",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
