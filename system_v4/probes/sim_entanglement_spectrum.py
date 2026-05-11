#!/usr/bin/env python3
"""
PURE LEGO: Entanglement Spectrum
================================
Direct local reduced-spectrum lego on a tiny bipartite state family.
"""

from __future__ import annotations

import json
import os
import pathlib

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import numpy as np
import pennylane as qml
import qutip

classification = "canonical"

EPS = 1e-10
THETA = 0.35

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical reduced-spectrum bridge on a tiny bipartite carrier. "
    "The theorem stays local: the reduced entanglement spectrum is the object, "
    "and qutip/cirq/pennylane only witness the same carrier instead of "
    "collapsing it to a scalar entropy story."
)
divergence_log = (
    "The entanglement spectrum is the sorted reduced-density spectrum of a "
    "two-qubit carrier. QuTiP, Cirq, and PennyLane all prepare the same "
    "product, Bell, and partially entangled states; they witness the reduced "
    "spectrum, but they do not change the theorem or broaden the carrier."
)

LEGO_IDS = [
    "entanglement_spectrum",
]

PRIMARY_LEGO_IDS = [
    "entanglement_spectrum",
]

CLAIM_CEILING = "canonical_local_entanglement_spectrum_lego_only"
NEXT_LEGO_TARGET = "none"
PROMOTION_CONDITION = (
    "requires separate reconciled queue row before coupling, bridge, axis, engine, "
    "GStack, QIT, or nonclassical use"
)
BLOCKED_UNTIL = "exact parent receipts, queue row, result JSON, and ledger loopback are reconciled"
DEMOTION_CONDITION = (
    "demote if reduced-spectrum witnesses disagree, spectra fail probability-vector "
    "checks, or this row is used for scalar entropy or higher-stage claims"
)
OUT_OF_SCOPE = [
    "QIT engine admission",
    "GStack admission",
    "axis promotion",
    "engine promotion",
    "nonclassical proof",
    "scientific coupling closure",
]

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing reduced-spectrum algebra, sorting, and serialization",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density-operator and reduced-spectrum witness",
    },
    "cirq": {
        "tried": True,
        "used": True,
        "reason": "load-bearing two-qubit circuit witness for the same carrier states",
    },
    "pennylane": {
        "tried": True,
        "used": True,
        "reason": "load-bearing state-preparation witness for the same carrier states",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "qutip": "load_bearing",
    "cirq": "load_bearing",
    "pennylane": "load_bearing",
}

Q0, Q1 = cirq.LineQubit.range(2)
PENNYLANE_DEV = qml.device("default.qubit", wires=2, shots=None)


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, complex):
        return [float(np.real(obj)), float(np.imag(obj))]
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _state_vector(kind: str) -> np.ndarray:
    if kind == "product":
        return np.array([0.0, 1.0, 0.0, 0.0], dtype=np.complex128)
    if kind == "bell":
        return np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    if kind == "partial":
        return np.array(
            [
                np.cos(THETA),
                0.0,
                0.0,
                np.sin(THETA),
            ],
            dtype=np.complex128,
        )
    raise ValueError(f"unknown state kind: {kind}")


def _density(state: np.ndarray) -> np.ndarray:
    vec = np.asarray(state, dtype=np.complex128).reshape(-1)
    return np.outer(vec, np.conjugate(vec))


def _spectrum_from_density(rho: np.ndarray) -> list[float]:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    vals = np.sort(np.real(vals))[::-1]
    return [float(x) for x in vals]


def _reduced_density_from_state(state: np.ndarray) -> np.ndarray:
    rho = _density(state).reshape(2, 2, 2, 2)
    return np.trace(rho, axis1=1, axis2=3)


def _expected_spectrum(kind: str) -> list[float]:
    if kind == "product":
        return [1.0, 0.0]
    if kind == "bell":
        return [0.5, 0.5]
    if kind == "partial":
        vals = sorted([float(np.cos(THETA) ** 2), float(np.sin(THETA) ** 2)], reverse=True)
        return vals
    raise ValueError(f"unknown state kind: {kind}")


def _qutip_reduced_spectrum(kind: str) -> dict[str, object]:
    ket = qutip.Qobj(_state_vector(kind).reshape(-1, 1), dims=[[2, 2], [1, 1]])
    rho = ket * ket.dag()
    reduced = rho.ptrace(0)
    spec = _spectrum_from_density(np.asarray(reduced.full(), dtype=np.complex128))
    return {
        "reduced_spectrum": spec,
        "rho": np.asarray(rho.full(), dtype=np.complex128).tolist(),
        "reduced_density": np.asarray(reduced.full(), dtype=np.complex128).tolist(),
    }


def _cirq_state(kind: str) -> np.ndarray:
    if kind == "product":
        circuit = cirq.Circuit(cirq.X(Q1))
    elif kind == "bell":
        circuit = cirq.Circuit(cirq.H(Q0), cirq.CNOT(Q0, Q1))
    elif kind == "partial":
        circuit = cirq.Circuit(cirq.ry(2.0 * THETA)(Q0), cirq.CNOT(Q0, Q1))
    else:
        raise ValueError(f"unknown state kind: {kind}")
    return np.asarray(
        cirq.Simulator(seed=13).simulate(circuit, qubit_order=[Q0, Q1]).final_state_vector,
        dtype=np.complex128,
    )


@qml.qnode(PENNYLANE_DEV)
def _qml_state(kind: str):
    if kind == "product":
        qml.BasisState(np.array([0, 1], dtype=np.int64), wires=[0, 1])
    elif kind == "bell":
        qml.Hadamard(wires=0)
        qml.CNOT(wires=[0, 1])
    elif kind == "partial":
        qml.RY(2.0 * THETA, wires=0)
        qml.CNOT(wires=[0, 1])
    else:
        raise ValueError(f"unknown state kind: {kind}")
    return qml.state()


def _witness_block(kind: str) -> dict[str, object]:
    target = _expected_spectrum(kind)
    qutip_w = _qutip_reduced_spectrum(kind)
    cirq_state = _cirq_state(kind)
    pl_state = np.asarray(_qml_state(kind), dtype=np.complex128)
    cirq_spec = _spectrum_from_density(_reduced_density_from_state(cirq_state))
    pl_spec = _spectrum_from_density(_reduced_density_from_state(pl_state))
    numpy_spec = _spectrum_from_density(_reduced_density_from_state(_state_vector(kind)))
    return {
        "expected_spectrum": target,
        "numpy": {
            "state": _state_vector(kind).tolist(),
            "reduced_spectrum": numpy_spec,
        },
        "qutip": qutip_w,
        "cirq": {
            "state": cirq_state.tolist(),
            "reduced_spectrum": cirq_spec,
        },
        "pennylane": {
            "state": pl_state.tolist(),
            "reduced_spectrum": pl_spec,
        },
        "pass": bool(
            np.allclose(numpy_spec, target, atol=1e-8)
            and np.allclose(qutip_w["reduced_spectrum"], target, atol=1e-8)
            and np.allclose(cirq_spec, target, atol=1e-8)
            and np.allclose(pl_spec, target, atol=1e-8)
        ),
    }


def main():
    product = _witness_block("product")
    bell = _witness_block("bell")
    partial = _witness_block("partial")

    positive = {
        "product_state_has_rank_one_reduced_spectrum": product,
        "bell_state_has_flat_reduced_spectrum": bell,
        "partially_entangled_state_has_nonflat_reduced_spectrum": partial,
    }

    negative = {
        "entanglement_spectrum_is_not_scalarized_to_entropy": {
            "pass": bool(
                not np.allclose(partial["numpy"]["reduced_spectrum"], [0.5, 0.5], atol=1e-8)
                and not np.allclose(partial["numpy"]["reduced_spectrum"], [1.0, 0.0], atol=1e-8)
            ),
        },
        "product_and_bell_spectra_are_distinct": {
            "pass": bool(
                not np.allclose(product["numpy"]["reduced_spectrum"], bell["numpy"]["reduced_spectrum"], atol=1e-8)
            ),
        },
    }

    boundary = {
        "all_reduced_spectra_are_probability_vectors": {
            "pass": all(
                abs(sum(block["numpy"]["reduced_spectrum"]) - 1.0) < 1e-8
                and all(x >= -EPS for x in block["numpy"]["reduced_spectrum"])
                for block in [product, bell, partial]
            ),
        },
        "all_tool_witnesses_agree_on_the_same_carrier": {
            "pass": all(block["pass"] for block in [product, bell, partial]),
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "entanglement_spectrum",
        "classification": classification if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": NEXT_LEGO_TARGET,
        "promotion_condition": PROMOTION_CONDITION,
        "blocked_until": BLOCKED_UNTIL,
        "demotion_condition": DEMOTION_CONDITION,
        "out_of_scope": OUT_OF_SCOPE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local reduced-spectrum lego on a tiny bipartite family.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "entanglement_spectrum_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=_json_default))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
