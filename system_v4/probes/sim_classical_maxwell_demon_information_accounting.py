#!/usr/bin/env python3
"""sim_classical_maxwell_demon_information_accounting

scope_note: Illuminates Landauer section of
  system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md:
  a Maxwell demon's extracted work is bookended by memory-erasure cost
  so net dissipation >= 0.
"""

import os

import cirq
import numpy as np
import pennylane as qml
import qutip

from _doc_illum_common import write_results

NAME = "classical_maxwell_demon_information_accounting"
SCOPE_NOTE = (
    "Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
    "(Landauer section): W_demon <= kT * I_memory, net dissipation non-negative "
    "once memory erasure is included."
)
classification = "canonical"
divergence_log = (
    "Maxwell-demon accounting baseline: extracted work stays bounded by one-bit "
    "memory erasure, and qutip/cirq/pennylane witness the same diagonal memory "
    "carrier rather than changing the inequality."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "information accounting, entropy, and work-bound checks for the one-bit memory carrier",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "density-matrix entropy witness for the same one-bit carrier",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "density-matrix simulator witness for the same one-bit carrier",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "mixed-state QNode witness for the same one-bit carrier",
    },
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this accounting baseline"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "qutip": "supportive",
    "cirq": "supportive",
    "pennylane": "supportive",
    "pytorch": None,
    "pyg": None,
    "z3": None,
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


def _entropy_nats_from_probs(p_one):
    p = float(np.clip(p_one, 0.0, 1.0))
    probs = np.array([1.0 - p, p], dtype=np.float64)
    nonzero = probs[probs > 0.0]
    if nonzero.size == 0:
        return 0.0
    return float(-np.sum(nonzero * np.log(nonzero)))


def _carrier_density(p_one):
    p = float(np.clip(p_one, 0.0, 1.0))
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=np.complex128)


def _entropy_nats_from_density(rho):
    evals = np.linalg.eigvalsh(np.asarray(rho, dtype=np.complex128))
    evals = evals[evals > 1e-15]
    if evals.size == 0:
        return 0.0
    return float(-np.sum(evals * np.log(evals)))


def demon_balance(I_bits, W_extracted, kT=1.0):
    erase_cost = kT * I_bits * np.log(2)
    net = erase_cost - W_extracted
    return net, erase_cost


def qutip_memory_witness(p_one):
    rho = _carrier_density(p_one)
    qrho = qutip.Qobj(rho, dims=[[2], [2]])
    entropy_nats = float(qutip.entropy_vn(qrho, base=np.e))
    return {
        "entropy_nats": entropy_nats,
        "expected_entropy_nats": _entropy_nats_from_density(rho),
        "erase_cost": float(entropy_nats),
    }


def cirq_memory_witness(p_one):
    rho = _carrier_density(p_one)
    sim = cirq.DensityMatrixSimulator()
    result = sim.simulate(
        cirq.Circuit(cirq.I(Q0)),
        qubit_order=[Q0],
        initial_state=rho,
    )
    witness_rho = np.asarray(result.final_density_matrix, dtype=np.complex128)
    entropy_nats = _entropy_nats_from_density(witness_rho)
    return {
        "entropy_nats": entropy_nats,
        "expected_entropy_nats": _entropy_nats_from_density(rho),
        "erase_cost": float(entropy_nats),
    }


@qml.qnode(QML_DEV)
def _pennylane_memory_density(rho):
    qml.QubitDensityMatrix(rho, wires=0)
    return qml.density_matrix(wires=0)


def pennylane_memory_witness(p_one):
    rho = _carrier_density(p_one)
    witness_rho = np.asarray(_pennylane_memory_density(rho), dtype=np.complex128)
    entropy_nats = _entropy_nats_from_density(witness_rho)
    return {
        "entropy_nats": entropy_nats,
        "expected_entropy_nats": _entropy_nats_from_density(rho),
        "erase_cost": float(entropy_nats),
    }


def run_bridge_witnesses():
    witness_cases = {}
    ok = True
    tol = 1e-6
    for p_one in (0.0, 0.1, 0.5, 0.9, 1.0):
        expected_entropy_nats = _entropy_nats_from_density(_carrier_density(p_one))
        qutip_w = qutip_memory_witness(p_one)
        cirq_w = cirq_memory_witness(p_one)
        pennylane_w = pennylane_memory_witness(p_one)
        case_ok = all(
            abs(w["entropy_nats"] - expected_entropy_nats) < tol
            and abs(w["erase_cost"] - expected_entropy_nats) < tol
            for w in (qutip_w, cirq_w, pennylane_w)
        )
        witness_cases[f"p_{p_one}"] = {
            "p_one": float(p_one),
            "expected_entropy_nats": float(expected_entropy_nats),
            "expected_erase_cost": float(expected_entropy_nats),
            "qutip": qutip_w,
            "cirq": cirq_w,
            "pennylane": pennylane_w,
            "ok": bool(case_ok),
        }
        ok = ok and case_ok
    return witness_cases, bool(ok)


def run_positive():
    out = {}
    for I_bits, W in [(1.0, 0.5), (2.0, 1.0), (0.1, 0.05)]:
        net, ec = demon_balance(I_bits, W)
        out[f"I_{I_bits}_W_{W}"] = {
            "net_dissipation": float(net),
            "erase_cost": float(ec),
            "ok": bool(net >= -1e-12),
        }
    return out


def run_negative():
    # Claimed "free" demon extracting W > kT*I*ln2 violates balance.
    I_bits, W = 1.0, 2.0  # W > ln2
    net, _ = demon_balance(I_bits, W)
    return {"reject_overdraw_demon": bool(net < 0)}


def run_boundary():
    # Zero information => zero extractable work.
    net, ec = demon_balance(0.0, 0.0)
    return {"zero_info": {"net": float(net), "erase_cost": float(ec)}}


if __name__ == "__main__":
    pos = run_positive()
    neg = run_negative()
    bnd = run_boundary()
    bridge_witnesses, bridge_ok = run_bridge_witnesses()
    accounting_ok = all(v["ok"] for v in pos.values()) and neg["reject_overdraw_demon"]
    ok = bool(accounting_ok and bridge_ok)
    results = {
        "name": NAME,
        "scope_note": SCOPE_NOTE,
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "load_bearing_tool": "numpy",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "bridge_witnesses": bridge_witnesses,
        "bridge_all_pass": bool(bridge_ok),
        "pass": bool(ok),
    }
    write_results(NAME, results)
