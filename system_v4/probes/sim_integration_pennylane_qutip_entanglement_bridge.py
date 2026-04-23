#!/usr/bin/env python3
"""Pennylane/QuTiP 2-qubit entanglement bridge probe.

This bridge keeps one small 2-qubit entangling surface honest across:
  - numpy/scipy exact matrix algebra
  - PennyLane statevector and correlation readout
  - QuTiP unitary/state witness

The bridge is intentionally bounded:
  - positive: the same entangling circuit matches across all three surfaces
  - negative: the reversed entangler does not match the reference surface
  - boundary: the zero-control axis stays separable and numerically stable
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import numpy as np
import pennylane as qml
import qutip
from scipy.linalg import expm

classification = "classical_baseline"
divergence_log = (
    "Classical-to-nonclassical bridge baseline: the same 2-qubit unitary must agree "
    "across explicit numpy/scipy matrix algebra, PennyLane statevector evaluation, "
    "and QuTiP unitary/state evaluation. The entanglement witness is the same Bell-like "
    "surface, not a separate ad hoc check."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "statevector, density-matrix, concurrence, and ZZ expectation arithmetic for the bridge",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "matrix exponential for the exact 2-qubit reference rotations",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "two-qubit statevector and ZZ witness for the bridge",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "two-qubit unitary/state witness for the same entangling surface",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "pennylane": "load_bearing",
    "qutip": "load_bearing",
}

OUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state",
    "sim_results",
    "pennylane_qutip_entanglement_bridge_results.json",
)

Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
I2 = np.eye(2, dtype=np.complex128)
CNOT_01 = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=np.complex128,
)
CNOT_10 = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ],
    dtype=np.complex128,
)

DEV = qml.device("default.qubit", wires=2, shots=None)


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    if isinstance(section.get("pass"), bool):
        return bool(section["pass"])
    return all(bool(row.get("pass", False)) for row in section.values() if isinstance(row, dict))


def _ry(theta: float) -> np.ndarray:
    return expm(-0.5j * theta * Y)


def _ket00() -> np.ndarray:
    return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)


def _density(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    return np.outer(state, np.conjugate(state))


def _concurrence(state: np.ndarray) -> float:
    a, b, c, d = np.asarray(state, dtype=np.complex128).reshape(-1)
    return float(2.0 * abs(a * d - b * c))


def _partial_trace_qubit1(rho: np.ndarray) -> np.ndarray:
    reshaped = rho.reshape(2, 2, 2, 2)
    return np.einsum("abcb->ac", reshaped)


def _entropy_from_state(state: np.ndarray) -> float:
    rho_a = _partial_trace_qubit1(_density(state))
    evals = np.linalg.eigvalsh((rho_a + rho_a.conj().T) / 2.0)
    evals = np.clip(np.real(evals), 1e-15, 1.0)
    return float(-np.sum(evals * np.log2(evals)))


def _zz_expectation(state: np.ndarray) -> float:
    zz = np.kron(Z, Z)
    return float(np.real(np.vdot(state, zz @ state)))


def _reference_state(theta: float, phi: float) -> np.ndarray:
    unitary = CNOT_01 @ np.kron(_ry(theta), _ry(phi))
    return unitary @ _ket00()


@qml.qnode(DEV)
def _pennylane_state(theta: float, phi: float, reversed_entangler: bool = False):
    qml.RY(theta, wires=0)
    qml.RY(phi, wires=1)
    if reversed_entangler:
        qml.CNOT(wires=[1, 0])
    else:
        qml.CNOT(wires=[0, 1])
    return qml.state()


@qml.qnode(DEV)
def _pennylane_zz(theta: float, phi: float, reversed_entangler: bool = False):
    qml.RY(theta, wires=0)
    qml.RY(phi, wires=1)
    if reversed_entangler:
        qml.CNOT(wires=[1, 0])
    else:
        qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


def _qutip_state(theta: float, phi: float, reversed_entangler: bool = False) -> np.ndarray:
    psi0 = qutip.tensor(qutip.basis(2, 0), qutip.basis(2, 0))
    ry0 = qutip.Qobj(_ry(theta), dims=[[2], [2]])
    ry1 = qutip.Qobj(_ry(phi), dims=[[2], [2]])
    cnot = qutip.Qobj(CNOT_10 if reversed_entangler else CNOT_01, dims=[[2, 2], [2, 2]])
    unitary = cnot * qutip.tensor(ry0, ry1)
    state = unitary * psi0
    return np.asarray(state.full(), dtype=np.complex128).reshape(-1)


def _summarize_case(theta: float, phi: float, *, reversed_entangler: bool = False) -> dict[str, object]:
    reference = _reference_state(theta, phi)
    pennylane_state = np.asarray(
        _pennylane_state(theta, phi, reversed_entangler=reversed_entangler),
        dtype=np.complex128,
    )
    qutip_state = _qutip_state(theta, phi, reversed_entangler=reversed_entangler)

    ref_rho = _density(reference)
    pl_rho = _density(pennylane_state)
    qutip_rho = _density(qutip_state)

    ref_zz = _zz_expectation(reference)
    pl_zz = float(_pennylane_zz(theta, phi, reversed_entangler=reversed_entangler))
    qutip_zz = _zz_expectation(qutip_state)

    return {
        "theta": float(theta),
        "phi": float(phi),
        "reversed_entangler": bool(reversed_entangler),
        "density_gap_pennylane": float(np.linalg.norm(ref_rho - pl_rho, ord="fro")),
        "density_gap_qutip": float(np.linalg.norm(ref_rho - qutip_rho, ord="fro")),
        "state_overlap_pennylane": float(abs(np.vdot(reference, pennylane_state)) ** 2),
        "state_overlap_qutip": float(abs(np.vdot(reference, qutip_state)) ** 2),
        "zz_gap_pennylane": abs(ref_zz - pl_zz),
        "zz_gap_qutip": abs(ref_zz - qutip_zz),
        "concurrence": _concurrence(reference),
        "entropy": _entropy_from_state(reference),
    }


def run_positive_tests() -> dict[str, dict[str, object]]:
    cases = [(1.127, -0.713), (0.889, 0.531)]
    rows = {}
    ok = True
    for idx, (theta, phi) in enumerate(cases, start=1):
        row = _summarize_case(theta, phi)
        row["pass"] = bool(
            row["density_gap_pennylane"] < 5e-7
            and row["density_gap_qutip"] < 5e-7
            and row["zz_gap_pennylane"] < 5e-7
            and row["zz_gap_qutip"] < 5e-7
            and row["concurrence"] > 0.05
            and row["entropy"] > 0.01
        )
        ok = ok and row["pass"]
        rows[f"entangled_case_{idx}"] = row
    return {"pass": ok, "cases": rows}


def run_negative_tests() -> dict[str, dict[str, object]]:
    row = _summarize_case(1.127, -0.713, reversed_entangler=True)
    row["pass"] = bool(
        row["density_gap_pennylane"] > 1e-2
        and row["density_gap_qutip"] > 1e-2
        and row["state_overlap_pennylane"] < 0.99
        and row["state_overlap_qutip"] < 0.99
    )
    return {"pass": bool(row["pass"]), "reversed_entangler": row}


def run_boundary_tests() -> dict[str, dict[str, object]]:
    separable = _summarize_case(0.0, 1.231)
    separable["pass"] = bool(
        separable["density_gap_pennylane"] < 1e-7
        and separable["density_gap_qutip"] < 1e-7
        and abs(separable["concurrence"]) < 1e-9
        and abs(separable["entropy"]) < 1e-9
    )
    return {"pass": bool(separable["pass"]), "separable_case": separable}


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(positive),
        "negative_all_pass": _all_pass(negative),
        "boundary_all_pass": _all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())

    results = {
        "name": "sim_integration_pennylane_qutip_entanglement_bridge",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }

    out_dir = os.path.dirname(OUT_PATH)
    os.makedirs(out_dir, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)
    print(f"Results written to {OUT_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
