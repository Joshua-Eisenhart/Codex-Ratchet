#!/usr/bin/env python3
"""sim_bridge_maxwell_demon_distinguishability_cost

scope_note: Bridge -- a zero-distinguishability-cost Maxwell demon is
  inadmissible. Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md.
  z3 load-bearing: UNSAT under W>0, I_bits>=0, erase_cost = F01*I_bits*ln2,
  net = erase_cost - W, F01=0 AND W>0 => inconsistent with non-negative net.
  qutip/cirq/pennylane witness the same one-bit carrier surface without
  changing the theorem into a different law.
"""

from __future__ import annotations

import os

import cirq
import numpy as np
import pennylane as qml
import qutip
import z3

from _doc_illum_common import write_results

NAME = "bridge_maxwell_demon_distinguishability_cost"
SCOPE_NOTE = (
    "Bridge: z3 UNSAT that a demon extracts W>0 at F01=0 (no "
    "distinguishability cost) while maintaining non-negative "
    "net dissipation. Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md."
)
classification = "canonical"
divergence_log = (
    "Maxwell-demon distinguishability bridge: the theorem stays z3-UNSAT for "
    "W>0 at zero distinguishability cost, while qutip/cirq/pennylane witness "
    "the same one-bit carrier entropy floor (ln2 at p=1/2) on a supportive "
    "surface rather than adding a new theorem."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "binary entropy and bounded one-bit carrier bookkeeping",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "supportive one-bit density witness for the distinguishability floor",
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
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing UNSAT proof for zero-cost demon with W>0",
    },
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this theorem"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this theorem"},
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
    "z3": "load_bearing",
    "pytorch": None,
    "pyg": None,
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

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

Q0 = cirq.LineQubit(0)
QML_DEV = qml.device("default.mixed", wires=1, shots=None)
LN2 = z3.RealVal("0.6931471805599453")


def _carrier_density(p_one):
    p = float(np.clip(p_one, 0.0, 1.0))
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=np.complex128)


def _entropy_nats_from_density(rho):
    evals = np.linalg.eigvalsh(np.asarray(rho, dtype=np.complex128))
    evals = evals[evals > 1e-15]
    if evals.size == 0:
        return 0.0
    return float(-np.sum(evals * np.log(evals)))


def _entropy_nats_from_population(p_one):
    return _entropy_nats_from_density(_carrier_density(p_one))


def _distinguishability_cost_nats(F01, I_bits):
    return float(F01 * I_bits * np.log(2.0))


def qutip_distinguishability_witness(p_one):
    rho = qutip.Qobj(_carrier_density(p_one), dims=[[2], [2]])
    entropy_nats = float(qutip.entropy_vn(rho, base=np.e))
    return {
        "entropy_nats": entropy_nats,
        "expected_entropy_nats": _entropy_nats_from_population(p_one),
        "carrier_density": np.asarray(rho.full(), dtype=np.complex128).tolist(),
    }


def cirq_distinguishability_witness(p_one):
    rho = _carrier_density(p_one)
    sim = cirq.DensityMatrixSimulator(seed=13)
    result = sim.simulate(
        cirq.Circuit(cirq.I(Q0)),
        qubit_order=[Q0],
        initial_state=rho,
    )
    witness_rho = np.asarray(result.final_density_matrix, dtype=np.complex128)
    entropy_nats = _entropy_nats_from_density(witness_rho)
    return {
        "entropy_nats": entropy_nats,
        "expected_entropy_nats": _entropy_nats_from_population(p_one),
        "carrier_density": witness_rho.tolist(),
    }


@qml.qnode(QML_DEV)
def _pennylane_density(p_one):
    qml.QubitDensityMatrix(_carrier_density(p_one), wires=0)
    return qml.density_matrix(wires=0)


def pennylane_distinguishability_witness(p_one):
    rho = np.asarray(_pennylane_density(p_one), dtype=np.complex128)
    entropy_nats = _entropy_nats_from_density(rho)
    return {
        "entropy_nats": entropy_nats,
        "expected_entropy_nats": _entropy_nats_from_population(p_one),
        "carrier_density": rho.tolist(),
    }


def run_positive():
    F01, I_bits, W, net = z3.Reals("F01 I_bits W net")
    s = z3.Solver()
    s.add(F01 == 0, I_bits >= 0, W > 0)
    s.add(net == F01 * I_bits * LN2 - W)
    s.add(net >= 0)
    res = s.check()

    witness_floor = {
        "p_half": _entropy_nats_from_population(0.5),
        "qutip": qutip_distinguishability_witness(0.5),
        "cirq": cirq_distinguishability_witness(0.5),
        "pennylane": pennylane_distinguishability_witness(0.5),
    }
    witness_ok = all(
        abs(w["entropy_nats"] - witness_floor["p_half"]) < 1e-10
        and abs(w["expected_entropy_nats"] - witness_floor["p_half"]) < 1e-10
        for w in (witness_floor["qutip"], witness_floor["cirq"], witness_floor["pennylane"])
    )
    return {
        "zero_cost_demon": str(res),
        "unsat_as_expected": bool(res == z3.unsat),
        "witness_floor": witness_floor,
        "witness_floor_matches_ln2": bool(abs(witness_floor["p_half"] - np.log(2.0)) < 1e-10),
        "witnesses_ok": bool(witness_ok),
    }


def run_negative():
    F01, I_bits, W, net = z3.Reals("F01 I_bits W net")
    s = z3.Solver()
    s.add(F01 == 1, I_bits == 1, W == 0.5)
    s.add(net == F01 * I_bits * LN2 - W)
    s.add(net >= 0)
    res = s.check()
    return {
        "honest_demon": str(res),
        "sat_as_expected": bool(res == z3.sat),
        "distinguishability_cost_nats": _distinguishability_cost_nats(1.0, 1.0),
    }


def run_boundary():
    F01, I_bits, W, net = z3.Reals("F01 I_bits W net")
    s = z3.Solver()
    s.add(F01 == 0, I_bits == 0, W == 0)
    s.add(net == F01 * I_bits * LN2 - W)
    s.add(net == 0)
    res = s.check()
    boundary_floor = {
        "p_zero": {
            "qutip": qutip_distinguishability_witness(0.0),
            "cirq": cirq_distinguishability_witness(0.0),
            "pennylane": pennylane_distinguishability_witness(0.0),
        },
        "p_one": {
            "qutip": qutip_distinguishability_witness(1.0),
            "cirq": cirq_distinguishability_witness(1.0),
            "pennylane": pennylane_distinguishability_witness(1.0),
        },
    }
    return {
        "saturated_fence": str(res),
        "sat_as_expected": bool(res == z3.sat),
        "boundary_floor": boundary_floor,
    }


if __name__ == "__main__":
    pos = run_positive()
    neg = run_negative()
    bnd = run_boundary()
    ok = (
        pos["unsat_as_expected"]
        and pos["witness_floor_matches_ln2"]
        and pos["witnesses_ok"]
        and neg["sat_as_expected"]
        and bnd["sat_as_expected"]
    )
    results = {
        "name": NAME,
        "scope_note": SCOPE_NOTE,
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "load_bearing_tool": "z3",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
