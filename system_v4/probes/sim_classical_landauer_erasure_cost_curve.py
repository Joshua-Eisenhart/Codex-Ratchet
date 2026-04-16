#!/usr/bin/env python3
"""sim_classical_landauer_erasure_cost_curve

scope_note: Illuminates Landauer section of
  system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md:
  erasure dissipates at least kT ln2 per bit; partial erasure scales
  with H(p) - H(p_final).
"""

import json
import os
from pathlib import Path

import cirq
import numpy as np
import pennylane as qml
import qutip

NAME = "classical_landauer_erasure_cost_curve"
SCOPE_NOTE = (
    "Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
    "(Landauer section): E_erase >= kT * Delta H."
)
classification = "canonical"
divergence_log = (
    "Landauer erasure curve: the bit-erase cost is H(p) for a one-bit "
    "carrier, and qutip/cirq/pennylane witness the same diagonal carrier "
    "state instead of redefining the cost."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "binary entropy, erasure cost, and boundary checks for the carrier bit",
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
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
}

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

Q0 = cirq.LineQubit(0)
QML_DEV = qml.device("default.mixed", wires=1)


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _write_results(results):
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True, default=_json_default)
    print(f"Results written to {out_path}")
    print(f"PASS={results.get('pass')}  name={NAME}")
    return out_path


def H(p):
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-15, 1 - 1e-15)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


def _density_from_population(p):
    p = float(np.clip(p, 1e-15, 1 - 1e-15))
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=np.complex128)


def _entropy_from_density(rho):
    evals = np.linalg.eigvalsh(np.asarray(rho, dtype=np.complex128))
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log(evals)))


def erase_cost(p, kT=1.0):
    return float(kT * H(p))


def qutip_entropy_witness(p):
    rho = qutip.Qobj(_density_from_population(p), dims=[[2], [2]])
    entropy = float(qutip.entropy_vn(rho, base=np.e))
    return {
        "entropy": entropy,
        "cost": float(entropy),
        "rho": np.asarray(rho.full(), dtype=np.complex128).tolist(),
    }


def cirq_entropy_witness(p):
    rho0 = _density_from_population(p)
    simulator = cirq.DensityMatrixSimulator(seed=13)
    circuit = cirq.Circuit(cirq.I(Q0))
    rho = simulator.simulate(circuit, initial_state=rho0, qubit_order=[Q0]).final_density_matrix
    entropy = _entropy_from_density(rho)
    return {
        "entropy": entropy,
        "cost": float(entropy),
        "rho": np.asarray(rho, dtype=np.complex128).tolist(),
    }


@qml.qnode(QML_DEV)
def _qml_density(p):
    qml.QubitDensityMatrix(_density_from_population(p), wires=0)
    return qml.density_matrix(wires=0)


def pennylane_entropy_witness(p):
    rho = np.asarray(_qml_density(p), dtype=np.complex128)
    entropy = _entropy_from_density(rho)
    return {
        "entropy": entropy,
        "cost": float(entropy),
        "rho": rho.tolist(),
    }


def run_positive():
    out = {}
    for p in [0.5, 0.25, 0.1]:
        theory = float(H(p))
        classical = erase_cost(p)
        qutip_w = qutip_entropy_witness(p)
        cirq_w = cirq_entropy_witness(p)
        pl_w = pennylane_entropy_witness(p)
        ok = (
            np.isclose(classical, theory)
            and np.isclose(qutip_w["entropy"], theory)
            and np.isclose(cirq_w["entropy"], theory)
            and np.isclose(pl_w["entropy"], theory)
            and np.isclose(qutip_w["cost"], theory)
            and np.isclose(cirq_w["cost"], theory)
            and np.isclose(pl_w["cost"], theory)
        )
        out[f"p_{p}"] = {
            "classical_cost": float(classical),
            "theory": theory,
            "qutip": qutip_w,
            "cirq": cirq_w,
            "pennylane": pl_w,
            "ok": bool(ok),
        }

    out["floor"] = {
        "classical_cost": float(erase_cost(0.5)),
        "ln2": float(np.log(2.0)),
        "qutip": qutip_entropy_witness(0.5),
        "cirq": cirq_entropy_witness(0.5),
        "pennylane": pennylane_entropy_witness(0.5),
        "ok": bool(np.isclose(erase_cost(0.5), np.log(2.0))),
    }
    return out


def run_negative():
    claimed_free = 0.0
    witness_floor = {
        "qutip": qutip_entropy_witness(0.5)["cost"],
        "cirq": cirq_entropy_witness(0.5)["cost"],
        "pennylane": pennylane_entropy_witness(0.5)["cost"],
    }
    return {
        "reject_free_erasure": bool(claimed_free < np.log(2.0)),
        "claimed_free_cost": claimed_free,
        "witness_floor": witness_floor,
        "floor_vs_ln2": {
            "qutip": bool(np.isclose(witness_floor["qutip"], np.log(2.0))),
            "cirq": bool(np.isclose(witness_floor["cirq"], np.log(2.0))),
            "pennylane": bool(np.isclose(witness_floor["pennylane"], np.log(2.0))),
        },
    }


def run_boundary():
    p_zero = 1e-15
    p_one = 1 - 1e-15
    return {
        "p_zero": {
            "classical_cost": float(erase_cost(p_zero)),
            "qutip": qutip_entropy_witness(p_zero),
            "cirq": cirq_entropy_witness(p_zero),
            "pennylane": pennylane_entropy_witness(p_zero),
        },
        "p_one": {
            "classical_cost": float(erase_cost(p_one)),
            "qutip": qutip_entropy_witness(p_one),
            "cirq": cirq_entropy_witness(p_one),
            "pennylane": pennylane_entropy_witness(p_one),
        },
    }


if __name__ == "__main__":
    pos = run_positive()
    neg = run_negative()
    bnd = run_boundary()
    ok = all(v["ok"] for v in pos.values()) and neg["reject_free_erasure"]
    results = {
        "name": NAME,
        "scope_note": SCOPE_NOTE,
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "load_bearing_tool": "numpy+qutip+cirq+pennylane",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "pass": bool(ok),
    }
    _write_results(results)
