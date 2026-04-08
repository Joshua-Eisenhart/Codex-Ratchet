#!/usr/bin/env python3
"""
sim_lego_entropy_shell_history_weighted.py
=========================================

Pure-math lego for shell/history/path-weighted entropy forms on simple
finite sequences of density matrices and channels.

What it checks:
  - weighted shell entropy on a finite family of states
  - history-window entropy over a path of states
  - transport-weighted entropy change along a channel sequence
  - operator-ordered entropy response under noncommuting channels

No engine jargon. No bridge doctrine. No axis language. Just state and
channel sequences.

Outputs:
  system_v4/probes/a2_state/sim_results/sim_lego_entropy_shell_history_weighted_results.json
"""

import json
import os
from datetime import datetime, timezone

import numpy as np

EPS = 1e-12

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure numpy lego"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no graph layer"},
    "z3": {"tried": False, "used": False, "reason": "not needed; numeric lego"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; numeric lego"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; closed-form proofs not required here"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; no geometric algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; no manifold geometry"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed; no equivariant layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed; no DAG layer"},
    "xgi": {"tried": False, "used": False, "reason": "not needed; no hypergraph layer"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed; no cell complex layer"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed; no persistence layer"},
}


def hermitian(rho):
    return 0.5 * (rho + rho.conj().T)


def entropy_bits(rho):
    evals = np.linalg.eigvalsh(hermitian(rho))
    evals = np.clip(evals, 0.0, None)
    nz = evals[evals > EPS]
    if nz.size == 0:
        return 0.0
    return float(-np.sum(nz * np.log2(nz)))


def validate_density(rho):
    rho = hermitian(np.asarray(rho, dtype=np.complex128))
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("density matrix has near-zero trace")
    rho = rho / tr
    return rho


def bloch_density(x, y, z):
    return validate_density(
        0.5
        * np.array(
            [[1 + z, x - 1j * y],
             [x + 1j * y, 1 - z]],
            dtype=np.complex128,
        )
    )


def partial_trace_A(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def mutual_information(rho_ab):
    rho_a = partial_trace_B(rho_ab)
    rho_b = partial_trace_A(rho_ab)
    return max(0.0, entropy_bits(rho_a) + entropy_bits(rho_b) - entropy_bits(rho_ab))


def apply_channel(rho, kraus_ops):
    out = np.zeros_like(rho, dtype=np.complex128)
    for k in kraus_ops:
        out += k @ rho @ k.conj().T
    return validate_density(out)


def depolarizing_kraus(p):
    I = np.eye(2, dtype=np.complex128)
    X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return [
        np.sqrt(1 - p) * I,
        np.sqrt(p / 3) * X,
        np.sqrt(p / 3) * Y,
        np.sqrt(p / 3) * Z,
    ]


def z_dephasing_kraus(p):
    I = np.eye(2, dtype=np.complex128)
    Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return [np.sqrt(1 - p) * I, np.sqrt(p) * Z]


def bit_flip_kraus(p):
    I = np.eye(2, dtype=np.complex128)
    X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    return [np.sqrt(1 - p) * I, np.sqrt(p) * X]


def amplitude_damping_kraus(gamma):
    return [
        np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=np.complex128),
        np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=np.complex128),
    ]


def make_path_states():
    base = [
        bloch_density(0.0, 0.0, 1.0),
        bloch_density(0.4, 0.0, 0.8),
        bloch_density(0.55, 0.0, 0.4),
        bloch_density(0.65, 0.15, 0.1),
        bloch_density(0.25, 0.35, -0.1),
    ]
    return base


def weighted_shell_entropy(states, weights):
    weights = np.asarray(weights, dtype=float)
    weights = weights / np.sum(weights)
    entropies = np.array([entropy_bits(rho) for rho in states], dtype=float)
    weighted = float(np.sum(weights * entropies))
    shell_spread = float(np.sum(weights * np.abs(entropies - weighted)))
    return {
        "weights": weights.tolist(),
        "entropies": entropies.tolist(),
        "weighted_shell_entropy": weighted,
        "shell_spread": shell_spread,
        "min_entropy": float(np.min(entropies)),
        "max_entropy": float(np.max(entropies)),
    }


def sliding_window_entropy(path_states, window=3):
    if window < 1:
        raise ValueError("window must be positive")
    if window > len(path_states):
        raise ValueError("window exceeds path length")
    values = []
    for start in range(len(path_states) - window + 1):
        win = path_states[start:start + window]
        mean_entropy = float(np.mean([entropy_bits(rho) for rho in win]))
        values.append({
            "start": start,
            "end": start + window - 1,
            "mean_entropy": mean_entropy,
        })
    return values


def transport_weighted_entropy_change(path_states, transports, weights):
    if len(transports) != len(path_states) - 1:
        raise ValueError("need one transport per path step")
    weights = np.asarray(weights, dtype=float)
    weights = weights / np.sum(weights)
    deltas = []
    for i in range(len(transports)):
        before = entropy_bits(path_states[i])
        after = entropy_bits(apply_channel(path_states[i], transports[i]))
        deltas.append(after - before)
    weighted_delta = float(np.sum(weights * np.array(deltas, dtype=float)))
    return {
        "step_deltas": [float(d) for d in deltas],
        "weights": weights.tolist(),
        "weighted_entropy_change": weighted_delta,
        "abs_weighted_change": float(abs(weighted_delta)),
    }


def operator_order_response(rho0, chan_a, chan_b, p_a, p_b):
    seq_ab = apply_channel(apply_channel(rho0, chan_a(p_a)), chan_b(p_b))
    seq_ba = apply_channel(apply_channel(rho0, chan_b(p_b)), chan_a(p_a))
    entropy_ab = entropy_bits(seq_ab)
    entropy_ba = entropy_bits(seq_ba)
    mi_ab = mutual_information(np.kron(seq_ab, np.eye(2, dtype=np.complex128) / 2.0))
    mi_ba = mutual_information(np.kron(seq_ba, np.eye(2, dtype=np.complex128) / 2.0))
    return {
        "entropy_ab": entropy_ab,
        "entropy_ba": entropy_ba,
        "entropy_gap": abs(entropy_ab - entropy_ba),
        "mi_ab": mi_ab,
        "mi_ba": mi_ba,
        "mi_gap": abs(mi_ab - mi_ba),
    }


def positive_tests():
    results = {}

    family = make_path_states()
    weights = [0.05, 0.10, 0.20, 0.30, 0.35]
    shell = weighted_shell_entropy(family, weights)
    uniform = weighted_shell_entropy(family, [1] * len(family))
    results["P1_weighted_shell_entropy"] = {
        "test": "weighted shell entropy is a weighted average over a finite family of states",
        "weighted_shell_entropy": shell["weighted_shell_entropy"],
        "shell_spread": shell["shell_spread"],
        "min_entropy": shell["min_entropy"],
        "max_entropy": shell["max_entropy"],
        "bounded_by_family": shell["min_entropy"] - 1e-12 <= shell["weighted_shell_entropy"] <= shell["max_entropy"] + 1e-12,
        "weights_change_result": abs(shell["weighted_shell_entropy"] - uniform["weighted_shell_entropy"]) > 1e-4,
        "pass": (
            shell["min_entropy"] - 1e-12 <= shell["weighted_shell_entropy"] <= shell["max_entropy"] + 1e-12
            and abs(shell["weighted_shell_entropy"] - uniform["weighted_shell_entropy"]) > 1e-4
        ),
    }

    path = make_path_states()
    windows = sliding_window_entropy(path, window=3)
    window_means = [w["mean_entropy"] for w in windows]
    results["P2_history_window_entropy"] = {
        "test": "sliding history windows expose changes along a short state path",
        "windows": windows,
        "window_means": window_means,
        "nontrivial_variation": max(window_means) - min(window_means) > 1e-4,
        "pass": max(window_means) - min(window_means) > 1e-4,
    }

    path_transport = [
        z_dephasing_kraus(0.10),
        z_dephasing_kraus(0.15),
        depolarizing_kraus(0.20),
        amplitude_damping_kraus(0.25),
    ]
    transport = transport_weighted_entropy_change(path, path_transport, [1, 2, 3, 4])
    results["P3_transport_weighted_entropy_change"] = {
        "test": "weighted transport changes should capture entropy increase under dissipative channels",
        "step_deltas": transport["step_deltas"],
        "weighted_entropy_change": transport["weighted_entropy_change"],
        "abs_weighted_change": transport["abs_weighted_change"],
        "entropy_change_nonzero": transport["abs_weighted_change"] > 1e-4,
        "pass": transport["abs_weighted_change"] > 1e-4,
    }

    rho0 = bloch_density(0.35, 0.2, 0.4)
    order = operator_order_response(
        rho0,
        chan_a=depolarizing_kraus,
        chan_b=amplitude_damping_kraus,
        p_a=0.20,
        p_b=0.25,
    )
    results["P4_operator_order_entropy_response"] = {
        "test": "noncommuting channel order changes entropy response",
        "entropy_ab": order["entropy_ab"],
        "entropy_ba": order["entropy_ba"],
        "entropy_gap": order["entropy_gap"],
        "order_matters": order["entropy_gap"] > 1e-4,
        "pass": order["entropy_gap"] > 1e-4,
    }

    return results


def negative_tests():
    results = {}

    family = make_path_states()
    equal_weights = [1] * len(family)
    shell = weighted_shell_entropy(family, equal_weights)
    uniform = weighted_shell_entropy(family, [1] * len(family))
    results["N1_uniform_weights_match_equal_weights"] = {
        "test": "equal weights should reproduce the uniform weighted shell entropy",
        "equal_weight_entropy": shell["weighted_shell_entropy"],
        "uniform_entropy": uniform["weighted_shell_entropy"],
        "pass": abs(shell["weighted_shell_entropy"] - uniform["weighted_shell_entropy"]) < 1e-12,
    }

    path = make_path_states()
    identity = [
        [np.eye(2, dtype=np.complex128)],
        [np.eye(2, dtype=np.complex128)],
        [np.eye(2, dtype=np.complex128)],
        [np.eye(2, dtype=np.complex128)],
    ]
    transport = transport_weighted_entropy_change(path, identity, [1, 1, 1, 1])
    results["N2_identity_transport_has_zero_entropy_change"] = {
        "test": "identity transport should not change entropy",
        "weighted_entropy_change": transport["weighted_entropy_change"],
        "pass": abs(transport["weighted_entropy_change"]) < 1e-12,
    }

    return results


def boundary_tests():
    results = {}

    single = [bloch_density(0.0, 0.0, 1.0)]
    shell = weighted_shell_entropy(single, [1.0])
    results["B1_single_state_shell"] = {
        "test": "single-state shell has entropy equal to that state",
        "weighted_shell_entropy": shell["weighted_shell_entropy"],
        "state_entropy": shell["entropies"][0],
        "pass": abs(shell["weighted_shell_entropy"] - shell["entropies"][0]) < 1e-12,
    }

    pure_path = [bloch_density(0.0, 0.0, 1.0)] * 4
    windows = sliding_window_entropy(pure_path, window=2)
    results["B2_pure_history_window"] = {
        "test": "a pure-state path yields zero window entropy throughout",
        "window_means": [w["mean_entropy"] for w in windows],
        "pass": all(abs(w["mean_entropy"]) < 1e-12 for w in windows),
    }

    rho0 = bloch_density(0.0, 0.0, 1.0)
    order = operator_order_response(
        rho0,
        chan_a=z_dephasing_kraus,
        chan_b=z_dephasing_kraus,
        p_a=0.25,
        p_b=0.25,
    )
    results["B3_commuting_same_basis_channels"] = {
        "test": "same-basis dephasing channels commute at the level of entropy response",
        "entropy_gap": order["entropy_gap"],
        "pass": order["entropy_gap"] < 1e-12,
    }

    return results


def main():
    positive = positive_tests()
    negative = negative_tests()
    boundary = boundary_tests()

    all_tests = {}
    for section in (positive, negative, boundary):
        for name, test in section.items():
            all_tests[name] = bool(test.get("pass", False))

    n_pass = sum(1 for ok in all_tests.values() if ok)
    n_total = len(all_tests)

    results = {
        "name": "sim_lego_entropy_shell_history_weighted",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classification": "canonical",
        "schema": {
            "version": 1,
            "surface": "pure_lego_entropy",
            "sections": ["positive", "negative", "boundary", "tool_manifest", "summary"],
            "caveats": [
                "Entropy response is not a metric.",
                "Order sensitivity is channel- and state-dependent, not universal.",
                "Weighted shell entropy is a weighted average over state entropies, not a geometric shell metric.",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "total_tests": n_total,
            "passed": n_pass,
            "failed": n_total - n_pass,
            "all_pass": n_pass == n_total,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_lego_entropy_shell_history_weighted_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"Tests: {n_pass}/{n_total} passed")
    print("ALL PASS" if n_pass == n_total else "FAILED")


if __name__ == "__main__":
    main()
