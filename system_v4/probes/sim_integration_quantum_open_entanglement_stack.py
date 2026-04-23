#!/usr/bin/env python3
"""
sim_integration_quantum_open_entanglement_stack.py

Bridge lane for:
  numpy + scipy + qutip + cirq + pennylane

Claim:
one small 2-qubit Bell surface plus one bounded open-system amplitude-damping
evolution should agree across exact classical algebra, Cirq, PennyLane, and
QuTiP. The entanglement witness and the open-system witness are intentionally
separate but coupled on the same two-qubit carrier.
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import numpy as np
import pennylane as qml
import qutip
from scipy.linalg import expm

classification = "classical_baseline"
divergence_log = (
    "Classical-to-nonclassical bridge baseline: the same 2-qubit Bell surface "
    "and a bounded one-qubit amplitude-damping open-system evolution must agree "
    "between exact numpy/scipy algebra, Cirq, PennyLane, and QuTiP instead of "
    "being re-glued per sim."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing classical density algebra, concurrence, and serialization",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "supportive exact Liouvillian and unitary matrix-exponential reference",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing open-system mesolve witness on the same 2-qubit carrier",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 2-qubit Bell state circuit witness on the same carrier",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 2-qubit Bell state and entanglement witness on the same carrier",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
}

OUT_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "sim_integration_quantum_open_entanglement_stack_results.json",
)

Q0, Q1 = cirq.LineQubit.range(2)
PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
PAULI_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
PAULI_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
IDENTITY_2 = np.eye(2, dtype=np.complex128)
IDENTITY_4 = np.eye(4, dtype=np.complex128)
KET00 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.complex128)
DEV = qml.device("default.qubit", wires=2, shots=None)


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _all_pass(section: dict[str, dict[str, object]]) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def _density(state: np.ndarray) -> np.ndarray:
    state = np.asarray(state, dtype=np.complex128).reshape(-1)
    return np.outer(state, np.conjugate(state))


def _vec(rho: np.ndarray) -> np.ndarray:
    return np.asarray(rho, dtype=np.complex128).reshape(-1, order="F")


def _unvec(vec: np.ndarray) -> np.ndarray:
    return np.asarray(vec, dtype=np.complex128).reshape(4, 4, order="F")


def _concurrence(rho: np.ndarray) -> float:
    yy = np.kron(PAULI_Y, PAULI_Y)
    r = rho @ yy @ np.conjugate(rho) @ yy
    eigvals = np.linalg.eigvals(r)
    roots = np.sort(np.sqrt(np.maximum(np.real(eigvals), 0.0)))[::-1]
    return float(max(0.0, roots[0] - roots[1] - roots[2] - roots[3]))


def _zz_expectation(state: np.ndarray) -> float:
    zz = np.kron(PAULI_Z, PAULI_Z)
    return float(np.real(np.vdot(state, zz @ state)))


def _is_density(rho: np.ndarray, tol: float = 1e-7) -> tuple[bool, dict[str, object]]:
    hermitian = np.allclose(rho, rho.conjugate().T, atol=tol)
    trace_one = abs(np.trace(rho) - 1.0) < tol
    eigs = np.linalg.eigvalsh((rho + rho.conjugate().T) / 2.0)
    psd = bool(np.all(eigs >= -tol))
    return bool(hermitian and trace_one and psd), {
        "hermitian": bool(hermitian),
        "trace_one": bool(trace_one),
        "psd": bool(psd),
        "min_eig": float(np.min(eigs)),
    }


def _bell_reference_state() -> np.ndarray:
    hadamard = (1.0 / np.sqrt(2.0)) * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
    cnot = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
        dtype=np.complex128,
    )
    return cnot @ np.kron(hadamard, IDENTITY_2) @ KET00


def _cirq_bell_state(reversed_entangler: bool = False) -> np.ndarray:
    if reversed_entangler:
        circuit = cirq.Circuit(cirq.H(Q0), cirq.CNOT(Q1, Q0))
    else:
        circuit = cirq.Circuit(cirq.H(Q0), cirq.CNOT(Q0, Q1))
    return np.asarray(cirq.Simulator(seed=13).simulate(circuit).final_state_vector, dtype=np.complex128)


@qml.qnode(DEV)
def _pennylane_bell_state(reversed_entangler: bool = False):
    qml.Hadamard(wires=0)
    if reversed_entangler:
        qml.CNOT(wires=[1, 0])
    else:
        qml.CNOT(wires=[0, 1])
    return qml.state()


@qml.qnode(DEV)
def _pennylane_zz(reversed_entangler: bool = False):
    qml.Hadamard(wires=0)
    if reversed_entangler:
        qml.CNOT(wires=[1, 0])
    else:
        qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0) @ qml.PauliZ(1))


def _open_system_liouvillian(gamma: float, *, damp_on_second_qubit: bool = True) -> np.ndarray:
    lower = np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)
    if damp_on_second_qubit:
        c = np.kron(IDENTITY_2, lower)
    else:
        c = np.kron(lower, IDENTITY_2)
    cdagc = c.conjugate().T @ c
    return gamma * (
        np.kron(c.conjugate(), c)
        - 0.5 * np.kron(IDENTITY_4, cdagc)
        - 0.5 * np.kron(cdagc.T, IDENTITY_4)
    )


def _classical_open_reference(rho0: np.ndarray, gamma: float, t: float, *, damp_on_second_qubit: bool = True) -> np.ndarray:
    liouvillian = _open_system_liouvillian(gamma, damp_on_second_qubit=damp_on_second_qubit)
    rho_t = expm(liouvillian * t) @ _vec(rho0)
    return _unvec(rho_t)


def _qutip_open_evolution(rho0: np.ndarray, gamma: float, times: list[float]) -> list[np.ndarray]:
    rho_q = qutip.Qobj(rho0, dims=[[2, 2], [2, 2]])
    h = 0.0 * qutip.tensor(qutip.sigmaz(), qutip.sigmaz())
    c_ops = [np.sqrt(gamma) * qutip.tensor(qutip.qeye(2), qutip.sigmap())]
    result = qutip.mesolve(H=h, rho0=rho_q, tlist=times, c_ops=c_ops, e_ops=[])
    return [np.asarray(state.full(), dtype=np.complex128) for state in result.states]


def run_positive_tests() -> dict[str, dict[str, object]]:
    bell = _bell_reference_state()
    cirq_state = _cirq_bell_state()
    pennylane_state = np.asarray(_pennylane_bell_state(), dtype=np.complex128)
    ref_rho = _density(bell)
    cirq_rho = _density(cirq_state)
    pennylane_rho = _density(pennylane_state)
    bell_qutip = qutip.Qobj(ref_rho, dims=[[2, 2], [2, 2]])
    entanglement = {
        "pass": bool(
            np.linalg.norm(ref_rho - cirq_rho) < 1e-7
            and np.linalg.norm(ref_rho - pennylane_rho) < 1e-8
            and _concurrence(ref_rho) > 0.999999
            and abs(_zz_expectation(bell)) > 0.999999
            and abs(float(_pennylane_zz())) > 0.999999
        ),
        "reference_concurrence": float(_concurrence(ref_rho)),
        "zz_expectation": float(_zz_expectation(bell)),
        "cirq_gap": float(np.linalg.norm(ref_rho - cirq_rho)),
        "pennylane_gap": float(np.linalg.norm(ref_rho - pennylane_rho)),
        "qutip_concurrence": float(qutip.concurrence(bell_qutip)),
    }

    gamma = 0.42
    times = [0.0, 0.19, 0.71, 1.23]
    qutip_states = _qutip_open_evolution(ref_rho, gamma, times)
    open_rows: list[dict[str, object]] = []
    max_error = 0.0
    all_density_ok = True
    all_trace_ok = True
    all_psd_ok = True
    all_concurrence_nonincreasing = True
    previous_concurrence = _concurrence(ref_rho)
    for t, rho_q in zip(times, qutip_states, strict=True):
        rho_ref = _classical_open_reference(ref_rho, gamma, t)
        error = float(np.linalg.norm(rho_q - rho_ref))
        max_error = max(max_error, error)
        density_ok, density_detail = _is_density(rho_q)
        conc_q = _concurrence(rho_q)
        conc_ref = _concurrence(rho_ref)
        open_rows.append(
            {
                "t": t,
                "pass": error < 1e-6 and density_ok,
                "error": error,
                "density": density_detail,
                "concurrence_qutip": conc_q,
                "concurrence_reference": conc_ref,
            }
        )
        all_density_ok = all_density_ok and density_ok
        all_trace_ok = all_trace_ok and abs(np.trace(rho_q) - 1.0) < 1e-10
        all_psd_ok = all_psd_ok and density_detail["psd"] is True
        all_concurrence_nonincreasing = all_concurrence_nonincreasing and conc_q <= previous_concurrence + 1e-10
        previous_concurrence = conc_q

    open_system = {
        "pass": bool(max_error < 1e-6 and all_density_ok and all_trace_ok and all_psd_ok and all_concurrence_nonincreasing),
        "reference_match": {
            "pass": bool(max_error < 1e-6),
            "max_error": max_error,
            "cases": open_rows,
        },
        "density_structure_preserved": {
            "pass": bool(all_density_ok and all_trace_ok and all_psd_ok),
            "trace_preserved": bool(all_trace_ok),
            "psd_preserved": bool(all_psd_ok),
        },
        "concurrence_nonincreasing": {
            "pass": bool(all_concurrence_nonincreasing),
            "note": "local amplitude damping should not increase Bell-state concurrence",
        },
    }

    return {
        "bell_entanglement_surface": entanglement,
        "open_system_surface": open_system,
    }


def run_negative_tests() -> dict[str, dict[str, object]]:
    bell = _bell_reference_state()
    ref_rho = _density(bell)
    reversed_cirq = _cirq_bell_state(reversed_entangler=True)
    reversed_pl = np.asarray(_pennylane_bell_state(reversed_entangler=True), dtype=np.complex128)
    wrong_entangler = _density(reversed_cirq)
    qutip_bad = _qutip_open_evolution(ref_rho, 0.42, [0.0, 0.71])[-1]
    wrong_open_ref = _classical_open_reference(ref_rho, 0.42, 0.71, damp_on_second_qubit=False)

    return {
        "reversed_entangler_rejected": {
            "pass": bool(
                np.linalg.norm(ref_rho - wrong_entangler) > 1e-2
                and np.linalg.norm(ref_rho - _density(reversed_pl)) > 1e-2
                and _concurrence(wrong_entangler) < 0.999999
            ),
            "cirq_gap": float(np.linalg.norm(ref_rho - wrong_entangler)),
            "pennylane_gap": float(np.linalg.norm(ref_rho - _density(reversed_pl))),
            "concurrence": float(_concurrence(wrong_entangler)),
        },
        "wrong_open_channel_rejected": {
            "pass": bool(np.linalg.norm(qutip_bad - wrong_open_ref) > 1e-2),
            "error": float(np.linalg.norm(qutip_bad - wrong_open_ref)),
            "claim": "amplitude damping on the wrong qubit should not match the witness surface",
        },
    }


def run_boundary_tests() -> dict[str, dict[str, object]]:
    bell = _bell_reference_state()
    ref_rho = _density(bell)
    t0_qutip = _qutip_open_evolution(ref_rho, 0.42, [0.0])[0]
    t0_ref = _classical_open_reference(ref_rho, 0.42, 0.0)
    tiny_gamma = 1e-9
    tiny_t = 0.33
    tiny_qutip = _qutip_open_evolution(ref_rho, tiny_gamma, [0.0, tiny_t])[-1]
    tiny_ref = _classical_open_reference(ref_rho, tiny_gamma, tiny_t)
    tiny_concurrence = _concurrence(tiny_qutip)

    zero_time_identity = {
        "pass": bool(np.linalg.norm(t0_qutip - ref_rho) < 1e-12 and np.linalg.norm(t0_ref - ref_rho) < 1e-12),
        "qutip_error": float(np.linalg.norm(t0_qutip - ref_rho)),
        "reference_error": float(np.linalg.norm(t0_ref - ref_rho)),
    }
    tiny_damping_boundary = {
        "pass": bool(
            np.linalg.norm(tiny_qutip - tiny_ref) < 1e-8
            and abs(tiny_concurrence - _concurrence(ref_rho)) < 1e-6
            and np.isfinite(tiny_concurrence)
        ),
        "reference_error": float(np.linalg.norm(tiny_qutip - tiny_ref)),
        "concurrence": float(tiny_concurrence),
    }

    return {
        "pass": bool(zero_time_identity["pass"] and tiny_damping_boundary["pass"]),
        "zero_time_identity": zero_time_identity,
        "tiny_damping_boundary": tiny_damping_boundary,
    }


def main() -> int:
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    summary = {
        "positive_all_pass": bool(all(row["pass"] for row in positive.values())),
        "negative_all_pass": bool(all(row["pass"] for row in negative.values())),
        "boundary_all_pass": bool(boundary["pass"]),
    }
    summary["all_pass"] = all(summary.values())

    result = {
        "name": "sim_integration_quantum_open_entanglement_stack",
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

    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, default=_json_default)

    print(f"Results written to {OUT_PATH}")
    print(f"summary.all_pass = {summary['all_pass']}")
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
