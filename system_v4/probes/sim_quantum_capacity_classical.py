#!/usr/bin/env python3
"""Classical baseline sim: quantum_capacity lego (Shannon capacity baseline).

Lane B classical baseline with a bounded bridge surface. Shannon capacity of
a DMC is still the theorem here: C = max_{p_X} I(X;Y). The classical baseline
of quantum capacity is C itself; Q <= C for decohering channels. This file
computes C via a Blahut-Arimoto style iteration for a few channels and uses
qutip/cirq/pennylane only as a one-qubit nonclassical reference surface so the
audit can contrast classical channel coding against coherent channel dynamics
without turning the theorem into a quantum-capacity claim.
"""
import json
import os

import cirq
import numpy as np
import pennylane as qml
import qutip

from pathlib import Path

classification = "classical_baseline"
classification_note = (
    "Shannon capacity remains the classical ceiling for this DMC baseline. "
    "qutip/cirq/pennylane witness only a bounded coherent one-qubit reference "
    "surface on the same carrier so the file can contrast classical coding "
    "against nonclassical channel evolution without changing the theorem."
)
divergence_log = classification_note

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "Blahut-Arimoto iteration and closed-form channel checks",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "one-qubit amplitude-damping reference witness",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "one-qubit amplitude-damping reference witness",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "one-qubit amplitude-damping reference witness",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "qutip": "supportive",
    "cirq": "supportive",
    "pennylane": "supportive",
}

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

NAME = "quantum_capacity_classical"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
Q0 = cirq.LineQubit(0)
QML_DEV = qml.device("default.mixed", wires=1)
GAMMA_REF = 0.23


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
    p = np.asarray(p, float).ravel()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def h2(x):
    if x <= 0 or x >= 1: return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)


def MI_for_channel(p_x, W):
    # W[x,y]
    pxy = (p_x[:, None] * W)
    py = pxy.sum(axis=0)
    return H(py) - sum(p_x[x] * H(W[x]) for x in range(len(p_x)))


def blahut_arimoto(W, n_iter=400, tol=1e-9):
    nx = W.shape[0]
    p = np.ones(nx) / nx
    last = -1
    for _ in range(n_iter):
        py = p @ W
        # Di = exp( sum_y W[x,y] * log(W[x,y]/py) )
        logD = np.zeros(nx)
        for x in range(nx):
            mask = W[x] > 0
            logD[x] = np.sum(W[x, mask] * (np.log2(W[x, mask]) - np.log2(py[mask] + 1e-300)))
        D = np.power(2.0, logD)
        p = p * D; p /= p.sum()
        c = MI_for_channel(p, W)
        if abs(c - last) < tol: break
        last = c
    return c, p


def bsc(eps):
    return np.array([[1 - eps, eps], [eps, 1 - eps]])


def bec(eps):
    # X in {0,1}, Y in {0,E,1}
    return np.array([[1 - eps, eps, 0.0], [0.0, eps, 1 - eps]])


def _plus_density():
    ket = np.array([[1.0], [1.0]], dtype=np.complex128) / np.sqrt(2.0)
    return ket @ ket.conj().T


def _amplitude_damping_kraus(gamma):
    gamma = float(np.clip(gamma, 0.0, 1.0))
    return (
        np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]], dtype=np.complex128),
        np.array([[0.0, np.sqrt(gamma)], [0.0, 0.0]], dtype=np.complex128),
    )


def _apply_amplitude_damping(rho, gamma):
    e0, e1 = _amplitude_damping_kraus(gamma)
    rho = np.asarray(rho, dtype=np.complex128)
    return e0 @ rho @ e0.conj().T + e1 @ rho @ e1.conj().T


def _rho_metrics(rho):
    rho = np.asarray(rho, dtype=np.complex128)
    return {
        "rho": rho.tolist(),
        "coherence_l1": float(2.0 * abs(rho[0, 1])),
        "excited_population": float(np.real(rho[1, 1])),
        "ground_population": float(np.real(rho[0, 0])),
    }


def qutip_amplitude_damping_witness(gamma=GAMMA_REF):
    rho_in = qutip.Qobj(_plus_density(), dims=[[2], [2]])
    e0, e1 = _amplitude_damping_kraus(gamma)
    e0 = qutip.Qobj(e0, dims=[[2], [2]])
    e1 = qutip.Qobj(e1, dims=[[2], [2]])
    rho_out = e0 * rho_in * e0.dag() + e1 * rho_in * e1.dag()
    return _rho_metrics(rho_out.full())


def cirq_amplitude_damping_witness(gamma=GAMMA_REF):
    circuit = cirq.Circuit(
        cirq.H(Q0),
        cirq.AmplitudeDampingChannel(float(np.clip(gamma, 0.0, 1.0))).on(Q0),
    )
    rho_out = cirq.DensityMatrixSimulator(seed=13).simulate(
        circuit, qubit_order=[Q0]
    ).final_density_matrix
    return _rho_metrics(rho_out)


@qml.qnode(QML_DEV)
def _qml_amplitude_damping_density(gamma):
    qml.Hadamard(wires=0)
    qml.AmplitudeDamping(float(np.clip(gamma, 0.0, 1.0)), wires=0)
    return qml.density_matrix(wires=0)


def pennylane_amplitude_damping_witness(gamma=GAMMA_REF):
    return _rho_metrics(np.asarray(_qml_amplitude_damping_density(gamma), dtype=np.complex128))


def run_positive_tests():
    C_bsc, _ = blahut_arimoto(bsc(0.1))
    C_bec, _ = blahut_arimoto(bec(0.3))
    qutip_ref = qutip_amplitude_damping_witness()
    cirq_ref = cirq_amplitude_damping_witness()
    pl_ref = pennylane_amplitude_damping_witness()
    return {
        "BSC_capacity_1_minus_h2": abs(C_bsc - (1 - h2(0.1))) < 1e-4,
        "BEC_capacity_1_minus_eps": abs(C_bec - (1 - 0.3)) < 1e-4,
        "capacity_nonneg": C_bsc >= 0 and C_bec >= 0,
        "qutip_cirq_density_match": np.allclose(qutip_ref["rho"], cirq_ref["rho"], atol=1e-6),
        "qutip_pennylane_density_match": np.allclose(qutip_ref["rho"], pl_ref["rho"], atol=1e-6),
        "coherence_survives_reference_channel": 0.0 < qutip_ref["coherence_l1"] < 1.0,
    }


def run_negative_tests():
    # totally depolarizing classical channel => C=0
    W = np.array([[0.5, 0.5], [0.5, 0.5]])
    C, _ = blahut_arimoto(W)
    dead_ref = qutip_amplitude_damping_witness(1.0)
    return {
        "useless_channel_zero_capacity": abs(C) < 1e-6,
        "full_damping_kills_coherence": abs(dead_ref["coherence_l1"]) < 1e-12,
    }


def run_boundary_tests():
    # identity channel => C = log2(n)
    I2 = np.eye(2); I3 = np.eye(3)
    C2, _ = blahut_arimoto(I2); C3, _ = blahut_arimoto(I3)
    undamped_ref = qutip_amplitude_damping_witness(0.0)
    return {
        "identity_2ary_capacity_1": abs(C2 - 1.0) < 1e-4,
        "identity_3ary_capacity_log2_3": abs(C3 - np.log2(3)) < 1e-4,
        "BSC_at_half_zero_capacity": abs(blahut_arimoto(bsc(0.5))[0]) < 1e-6,
        "no_damping_preserves_coherence": abs(undamped_ref["coherence_l1"] - 1.0) < 1e-12,
    }


def run_bridge_tests():
    gamma = 0.23
    qutip_ref = qutip_amplitude_damping_witness(gamma)
    cirq_ref = cirq_amplitude_damping_witness(gamma)
    pl_ref = pennylane_amplitude_damping_witness(gamma)
    return {
        "bridge_qutip_cirq_density_match": np.allclose(qutip_ref["rho"], cirq_ref["rho"], atol=1e-6),
        "bridge_qutip_pennylane_density_match": np.allclose(qutip_ref["rho"], pl_ref["rho"], atol=1e-6),
        "bridge_cirq_pennylane_density_match": np.allclose(cirq_ref["rho"], pl_ref["rho"], atol=1e-6),
        "bridge_reference_coherence_consistent": (
            abs(qutip_ref["coherence_l1"] - cirq_ref["coherence_l1"]) < 1e-6
            and abs(cirq_ref["coherence_l1"] - pl_ref["coherence_l1"]) < 1e-6
        ),
        "bridge_reference_remains_nonclassical": qutip_ref["coherence_l1"] > 0.0,
    }


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    bridge = run_bridge_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values()) and all(bridge.values())
    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "classification_note": classification_note,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "bridge_witnesses": bridge,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": divergence_log,
    }
    out = RESULTS_DIR / f"{NAME}_results.json"
    os.makedirs(out.parent, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=_json_default)
    print(f"all_pass={all_pass} -> {out}")
