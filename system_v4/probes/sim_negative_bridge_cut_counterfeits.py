#!/usr/bin/env python3
"""
sim_negative_bridge_cut_counterfeits.py
======================================

Negative battery for counterfeit bridge/cut constructions on finite
families of quantum states.

Targets:
  - history scrambling
  - shell ablation
  - marginal inconsistency
  - non-PSD couplings
  - order-insensitive fake metrics
  - kernels that collapse to local entropy only

Pure math only. No engine jargon.

Output:
  system_v4/probes/a2_state/sim_results/sim_negative_bridge_cut_counterfeits_results.json
"""

import json
import os
from datetime import datetime, timezone

import numpy as np

EPS = 1e-12

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure numpy negative battery"},
    "pyg": {"tried": False, "used": False, "reason": "no graph layer in this probe"},
    "z3": {"tried": False, "used": False, "reason": "numeric rejection tests only"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric rejection tests only"},
    "sympy": {"tried": False, "used": False, "reason": "closed-form proofs not required here"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra layer"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold geometry layer"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "no DAG layer"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph layer"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex layer"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence layer"},
}


def hermitian(rho):
    rho = np.asarray(rho, dtype=np.complex128)
    return 0.5 * (rho + rho.conj().T)


def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    return obj


def validate_density(rho):
    rho = hermitian(rho)
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("density matrix has near-zero trace")
    rho = rho / tr
    evals = np.linalg.eigvalsh(rho)
    if np.min(evals) < -1e-8:
        raise ValueError("density matrix is not PSD")
    return rho


def entropy_bits(rho):
    rho = hermitian(rho)
    evals = np.linalg.eigvalsh(rho)
    evals = np.clip(evals, 0.0, None)
    nz = evals[evals > EPS]
    if nz.size == 0:
        return 0.0
    return float(-np.sum(nz * np.log2(nz)))


def fidelity_pure(phi, rho):
    phi = np.asarray(phi, dtype=np.complex128).reshape(-1, 1)
    return float(np.real((phi.conj().T @ rho @ phi)[0, 0]))


def dm(vec):
    vec = np.asarray(vec, dtype=np.complex128).ravel()
    return np.outer(vec, vec.conj())


ket0 = np.array([1.0, 0.0], dtype=np.complex128)
ket1 = np.array([0.0, 1.0], dtype=np.complex128)
I2 = np.eye(2, dtype=np.complex128)
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)


def bell_phi_plus():
    v = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    return dm(v)


def classical_correlated():
    return np.diag([0.5, 0.0, 0.0, 0.5]).astype(np.complex128)


def product_zero():
    return dm(np.kron(ket0, ket0))


def werner_state(p):
    return validate_density(p * bell_phi_plus() + (1.0 - p) * np.eye(4, dtype=np.complex128) / 4.0)


def partial_trace_A(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def mutual_information(rho_ab):
    rho_a = partial_trace_B(rho_ab)
    rho_b = partial_trace_A(rho_ab)
    return max(0.0, entropy_bits(rho_a) + entropy_bits(rho_b) - entropy_bits(rho_ab))


def apply_kraus(rho, kraus_ops):
    out = np.zeros_like(rho, dtype=np.complex128)
    for k in kraus_ops:
        out += k @ rho @ k.conj().T
    return validate_density(out)


def dephasing_kraus(gamma):
    return [np.sqrt(1.0 - gamma / 2.0) * I2, np.sqrt(gamma / 2.0) * Z]


def bit_flip_kraus(p):
    return [np.sqrt(1.0 - p) * I2, np.sqrt(p) * X]


def depolarizing_kraus(p):
    return [
        np.sqrt(1.0 - p) * I2,
        np.sqrt(p / 3.0) * X,
        np.sqrt(p / 3.0) * Y,
        np.sqrt(p / 3.0) * Z,
    ]


def lift_one_qubit_channel(kraus_ops):
    out = []
    for k in kraus_ops:
        out.append(np.kron(k, I2))
    return out


def weighted_shell_entropy(states, weights):
    weights = np.asarray(weights, dtype=float)
    weights = weights / np.sum(weights)
    entropies = np.array([entropy_bits(rho) for rho in states], dtype=float)
    weighted = float(np.sum(weights * entropies))
    return {
        "weights": weights.tolist(),
        "entropies": entropies.tolist(),
        "weighted_shell_entropy": weighted,
        "shell_spread": float(np.sum(weights * np.abs(entropies - weighted))),
    }


def history_window_entropy(states, window):
    if window < 1 or window > len(states):
        raise ValueError("invalid window")
    values = []
    for start in range(len(states) - window + 1):
        chunk = states[start:start + window]
        values.append({
            "start": start,
            "end": start + window - 1,
            "mean_entropy": float(np.mean([entropy_bits(r) for r in chunk])),
        })
    return values


def transport_weighted_entropy_change(states, channel_sequence, weights):
    if len(channel_sequence) != len(states) - 1:
        raise ValueError("need one channel per step")
    weights = np.asarray(weights, dtype=float)
    weights = weights / np.sum(weights)
    deltas = []
    for i, channel in enumerate(channel_sequence):
        before = entropy_bits(states[i])
        after = entropy_bits(apply_kraus(states[i], lift_one_qubit_channel(channel)))
        deltas.append(after - before)
    return {
        "step_deltas": [float(v) for v in deltas],
        "weighted_entropy_change": float(np.sum(weights * np.array(deltas, dtype=float))),
    }


def ordered_entropy_response(rho_ab, channel_a, channel_b):
    seq_ab = apply_kraus(apply_kraus(rho_ab, lift_one_qubit_channel(channel_a)), lift_one_qubit_channel(channel_b))
    seq_ba = apply_kraus(apply_kraus(rho_ab, lift_one_qubit_channel(channel_b)), lift_one_qubit_channel(channel_a))
    return {
        "entropy_ab": entropy_bits(seq_ab),
        "entropy_ba": entropy_bits(seq_ba),
        "entropy_gap": abs(entropy_bits(seq_ab) - entropy_bits(seq_ba)),
        "mi_ab": mutual_information(seq_ab),
        "mi_ba": mutual_information(seq_ba),
        "mi_gap": abs(mutual_information(seq_ab) - mutual_information(seq_ba)),
    }


def fake_order_insensitive_metric(states):
    return float(np.mean([entropy_bits(r) for r in states]))


def fake_sequence_metric(rho_ab, channel_a, channel_b):
    ea = entropy_bits(apply_kraus(rho_ab, lift_one_qubit_channel(channel_a)))
    eb = entropy_bits(apply_kraus(rho_ab, lift_one_qubit_channel(channel_b)))
    return 0.5 * (ea + eb)


def local_entropy_only_kernel(rho_ab):
    return float(entropy_bits(partial_trace_A(rho_ab)) + entropy_bits(partial_trace_B(rho_ab)))


def joint_bridge_kernel(rho_ab):
    return float(mutual_information(rho_ab) + abs(entropy_bits(rho_ab) - local_entropy_only_kernel(rho_ab)))


def valid_history_family():
    base = [
        product_zero(),
        validate_density(np.diag([0.75, 0.0, 0.0, 0.25]).astype(np.complex128)),
        classical_correlated(),
        werner_state(0.65),
        bell_phi_plus(),
    ]
    return base


def counterfeit_shell_family():
    return [
        product_zero(),
        validate_density(np.diag([0.60, 0.10, 0.10, 0.20]).astype(np.complex128)),
        classical_correlated(),
        werner_state(0.45),
        bell_phi_plus(),
    ]


def test_positive():
    results = {}

    family = valid_history_family()
    weights = [0.05, 0.10, 0.15, 0.25, 0.45]
    shell = weighted_shell_entropy(family, weights)
    history = history_window_entropy(family, window=3)
    transport = transport_weighted_entropy_change(
        family,
        [dephasing_kraus(0.15), bit_flip_kraus(0.10), depolarizing_kraus(0.08), dephasing_kraus(0.05)],
        weights[:4],
    )

    ordered = ordered_entropy_response(product_zero(), [np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)], dephasing_kraus(0.20))

    results["P1_weighted_shell"] = {
        "pass": shell["shell_spread"] > 0.08,
        "why": "nonuniform shell weights produce a real spread over the family",
        "weighted_shell_entropy": shell["weighted_shell_entropy"],
        "shell_spread": shell["shell_spread"],
    }
    results["P2_history_window"] = {
        "pass": len(history) == 3 and history[0]["mean_entropy"] != history[-1]["mean_entropy"],
        "why": "entropy varies across the path, so a history window is not flat",
        "windows": history,
    }
    results["P3_transport_weighted_change"] = {
        "pass": abs(transport["weighted_entropy_change"]) > 1e-4,
        "why": "transport changes entropy along the path",
        "transport": transport,
    }
    results["P4_ordered_response"] = {
        "pass": ordered["entropy_gap"] > 1e-3,
        "why": "channel order matters for noncommuting channels",
        "ordered_response": ordered,
    }

    return results


def test_negative():
    results = {}

    family = valid_history_family()
    scrambled = list(reversed(family))
    weights = [0.05, 0.10, 0.15, 0.25, 0.45]

    shell_true = weighted_shell_entropy(family, weights)
    shell_scrambled = weighted_shell_entropy(scrambled, weights)
    fake_metric_true = fake_order_insensitive_metric(family)
    fake_metric_scrambled = fake_order_insensitive_metric(scrambled)
    real_order_gap = ordered_entropy_response(bell_phi_plus(), dephasing_kraus(0.20), bit_flip_kraus(0.20))["entropy_gap"]
    local_only_gap = abs(local_entropy_only_kernel(bell_phi_plus()) - local_entropy_only_kernel(classical_correlated()))
    real_joint_gap = abs(joint_bridge_kernel(bell_phi_plus()) - joint_bridge_kernel(classical_correlated()))

    results["N1_history_scramble"] = {
        "pass": abs(shell_true["weighted_shell_entropy"] - shell_scrambled["weighted_shell_entropy"]) > 1e-3
        and abs(fake_metric_true - fake_metric_scrambled) < 1e-12,
        "rejected_counterfeit": "A fake metric that only averages entropies ignores path order.",
        "truth": {
            "shell_weighted_gap": abs(shell_true["weighted_shell_entropy"] - shell_scrambled["weighted_shell_entropy"]),
            "fake_metric_gap": abs(fake_metric_true - fake_metric_scrambled),
            "real_order_gap": real_order_gap,
        },
    }

    ablated = family[:3]
    ablated_shell = weighted_shell_entropy(ablated, [1.0, 1.0, 1.0])
    results["N2_shell_ablation"] = {
        "pass": shell_true["shell_spread"] > 0.05 and shell_true["weighted_shell_entropy"] != ablated_shell["weighted_shell_entropy"],
        "rejected_counterfeit": "A local-only or ablated shell metric misses the weighted outer states.",
        "truth": {
            "full_shell_spread": shell_true["shell_spread"],
            "full_weighted_entropy": shell_true["weighted_shell_entropy"],
            "ablated_weighted_entropy": ablated_shell["weighted_shell_entropy"],
        },
    }

    ra = np.diag([0.80, 0.20]).astype(np.complex128)
    rb = np.diag([0.65, 0.35]).astype(np.complex128)
    product = validate_density(np.kron(ra, rb))
    rho_fake = product.copy()
    rho_fake[0, 3] = 0.25
    rho_fake[3, 0] = 0.25
    rho_fake = rho_fake / np.trace(rho_fake)
    evals_fake = np.linalg.eigvalsh(rho_fake)
    marg_a = partial_trace_B(rho_fake)
    marg_b = partial_trace_A(rho_fake)
    results["N3_marginal_inconsistency"] = {
        "pass": np.allclose(marg_a, ra, atol=1e-9) and np.allclose(marg_b, rb, atol=1e-9) and np.min(evals_fake) < -1e-3,
        "rejected_counterfeit": "The marginals can match while the joint coupling is not PSD.",
        "truth": {
            "marginal_a_match": bool(np.allclose(marg_a, ra, atol=1e-9)),
            "marginal_b_match": bool(np.allclose(marg_b, rb, atol=1e-9)),
            "min_eig_joint": float(np.min(evals_fake)),
        },
    }

    coupling_matrix = np.array([[1.0, 1.20], [1.20, 1.0]], dtype=float)
    coupling_eigs = np.linalg.eigvalsh(coupling_matrix)
    results["N4_non_psd_coupling"] = {
        "pass": float(np.min(coupling_eigs)) < -1e-6,
        "rejected_counterfeit": "A coupling matrix with a negative eigenvalue is not a valid bridge kernel.",
        "truth": {
            "eigenvalues": [float(v) for v in coupling_eigs],
            "min_eigenvalue": float(np.min(coupling_eigs)),
        },
    }

    seq_ab = ordered_entropy_response(product_zero(), [np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)], dephasing_kraus(0.20))
    seq_ba = ordered_entropy_response(product_zero(), dephasing_kraus(0.20), [np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)])
    fake_metric_ab = fake_sequence_metric(product_zero(), [np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)], dephasing_kraus(0.20))
    fake_metric_ba = fake_sequence_metric(product_zero(), dephasing_kraus(0.20), [np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / np.sqrt(2.0)])
    results["N5_order_insensitive_fake_metric"] = {
        "pass": abs(fake_metric_ab - fake_metric_ba) < 1e-12 and seq_ab["entropy_gap"] > 1e-3,
        "rejected_counterfeit": "An order-insensitive score collapses distinct channel orders.",
        "truth": {
            "fake_metric_gap": abs(fake_metric_ab - fake_metric_ba),
            "sequence_entropy_gap": seq_ab["entropy_gap"],
        },
    }

    bell = bell_phi_plus()
    classical = classical_correlated()
    results["N6_local_entropy_only_kernel"] = {
        "pass": abs(local_entropy_only_kernel(bell) - local_entropy_only_kernel(classical)) < 1e-12 and abs(joint_bridge_kernel(bell) - joint_bridge_kernel(classical)) > 0.25,
        "rejected_counterfeit": "Local entropies alone cannot distinguish Bell and classically correlated states.",
        "truth": {
            "local_only_gap": local_only_gap,
            "joint_kernel_gap": real_joint_gap,
        },
    }

    return results


def test_boundary():
    results = {}

    family = valid_history_family()
    single = [bell_phi_plus()]
    identity_transport = transport_weighted_entropy_change(
        [product_zero(), product_zero()],
        [[I2]],
        [1.0],
    )
    commuting_response = ordered_entropy_response(bell_phi_plus(), dephasing_kraus(0.12), dephasing_kraus(0.24))

    results["B1_identity_transport"] = {
        "pass": abs(identity_transport["weighted_entropy_change"]) < 1e-12,
        "why": "identity transport should not change entropy",
        "truth": identity_transport,
    }
    results["B2_singleton_shell"] = {
        "pass": abs(weighted_shell_entropy(single, [1.0])["weighted_shell_entropy"] - entropy_bits(single[0])) < 1e-12,
        "why": "a singleton shell reduces to the state entropy",
        "truth": weighted_shell_entropy(single, [1.0]),
    }
    results["B3_commuting_order"] = {
        "pass": abs(commuting_response["entropy_gap"]) < 1e-12 and abs(commuting_response["mi_gap"]) < 1e-12,
        "why": "commuting channels should not produce an order gap",
        "truth": commuting_response,
    }

    return results


def main():
    positive = test_positive()
    negative = test_negative()
    boundary = test_boundary()

    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())
    passed = sum(1 for section in (positive, negative, boundary) for v in section.values() if v["pass"])
    total = sum(len(section) for section in (positive, negative, boundary))

    results = {
        "name": "sim_negative_bridge_cut_counterfeits",
        "classification": "canonical",
        "schema": {
            "version": "1.0",
            "sections": ["positive", "negative", "boundary", "tool_manifest", "summary"],
            "notes": [
                "pure math only",
                "negative battery: passes mean counterfeit rejection succeeded",
                "no bridge doctrine or engine jargon",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "tests_total": total,
            "tests_passed": passed,
            "all_pass": all_pass,
            "caveat": "This battery rejects counterfeit bridge/cut metrics; it does not claim a full bridge/cut theory.",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out_dir = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_negative_bridge_cut_counterfeits_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sanitize(results), f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"{passed}/{total} passed")
    print(f"wrote {out_path}")
    print("ALL PASS" if all_pass else "SOME FAIL")


if __name__ == "__main__":
    main()
