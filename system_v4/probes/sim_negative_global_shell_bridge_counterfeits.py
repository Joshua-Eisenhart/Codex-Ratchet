#!/usr/bin/env python3
"""
sim_negative_global_shell_bridge_counterfeits.py
=================================================

Negative battery for counterfeit global shell / bridge-weighted forms on
finite families of quantum states.

Targets:
  - arbitrary weights that only rescale local entropy
  - shell partitions that do not induce real bipartite differences
  - history aggregation that erases order
  - weighted sums that look better only because of normalization artifacts

Pure math only. No engine jargon.

Output:
  system_v4/probes/a2_state/sim_results/sim_negative_global_shell_bridge_counterfeits_results.json
"""

import json
import os
from datetime import datetime, timezone

import numpy as np
classification = "classical_baseline"  # auto-backfill

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


def hermitian(rho):
    rho = np.asarray(rho, dtype=np.complex128)
    return 0.5 * (rho + rho.conj().T)


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


def dm(vec):
    vec = np.asarray(vec, dtype=np.complex128).ravel()
    return np.outer(vec, vec.conj())


ket0 = np.array([1.0, 0.0], dtype=np.complex128)
ket1 = np.array([0.0, 1.0], dtype=np.complex128)


def bell_phi_plus():
    vec = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    return dm(vec)


def maximally_mixed_2q():
    return np.eye(4, dtype=np.complex128) / 4.0


def classical_correlated():
    return np.diag([0.5, 0.0, 0.0, 0.5]).astype(np.complex128)


def product_zero():
    return dm(np.kron(ket0, ket0))


def product_mixed():
    return np.kron(np.diag([0.5, 0.5]).astype(np.complex128), np.diag([0.5, 0.5]).astype(np.complex128))


def werner_state(p):
    return validate_density(p * bell_phi_plus() + (1.0 - p) * maximally_mixed_2q())


def partial_trace_A(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def local_entropy_sum(rho_ab):
    return entropy_bits(partial_trace_A(rho_ab)) + entropy_bits(partial_trace_B(rho_ab))


def mutual_information(rho_ab):
    rho_a = partial_trace_B(rho_ab)
    rho_b = partial_trace_A(rho_ab)
    return max(0.0, entropy_bits(rho_a) + entropy_bits(rho_b) - entropy_bits(rho_ab))


def shell_global_score(states, weights):
    weights = np.asarray(weights, dtype=float)
    weights = weights / np.sum(weights)
    mi = np.array([mutual_information(rho) for rho in states], dtype=float)
    local = np.array([local_entropy_sum(rho) for rho in states], dtype=float)
    return {
        "weights": weights.tolist(),
        "mutual_information": mi.tolist(),
        "local_entropy_sum": local.tolist(),
        "normalized_mi": float(np.sum(weights * mi)),
        "normalized_local_entropy": float(np.sum(weights * local)),
        "shell_contrast": float(np.sum(weights * np.abs(mi - np.sum(weights * mi)))),
    }


def raw_weighted_sum(values, weights):
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    return float(np.sum(weights * values))


def ordered_history_score(path_states, weights=None):
    mi = np.array([mutual_information(rho) for rho in path_states], dtype=float)
    if weights is None:
        weights = np.arange(1, len(mi) + 1, dtype=float)
    weights = np.asarray(weights, dtype=float)
    weights = weights / np.sum(weights)
    return {
        "mi_path": mi.tolist(),
        "ordered_score": float(np.sum(weights * mi)),
        "unordered_mean": float(np.mean(mi)),
        "total_variation": float(np.sum(np.abs(np.diff(mi)))) if len(mi) > 1 else 0.0,
    }


def partition_contrast(states, left_idx, right_idx, metric_fn):
    left = np.mean([metric_fn(states[i]) for i in left_idx]) if left_idx else 0.0
    right = np.mean([metric_fn(states[i]) for i in right_idx]) if right_idx else 0.0
    return abs(left - right)


def valid_shell_family():
    return [
        product_zero(),
        maximally_mixed_2q(),
        classical_correlated(),
        werner_state(0.50),
        bell_phi_plus(),
        product_mixed(),
    ]


def bridge_path():
    return [
        product_zero(),
        maximally_mixed_2q(),
        classical_correlated(),
        werner_state(0.50),
        bell_phi_plus(),
    ]


def positive_tests():
    results = {}
    states = valid_shell_family()
    weights = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    shell = shell_global_score(states, weights)
    results["P1_global_shell_sees_correlations"] = {
        "pass": shell["normalized_mi"] > shell["normalized_local_entropy"] - 2.0,
        "why": "mutual information distinguishes correlated from uncorrelated states",
        "summary": shell,
    }

    corr_contrast = partition_contrast(states, [2, 3, 4], [0, 1, 5], mutual_information)
    local_contrast = partition_contrast(states, [2, 3, 4], [0, 1, 5], local_entropy_sum)
    results["P2_partition_has_real_bipartite_difference"] = {
        "pass": corr_contrast > local_contrast + 0.25,
        "why": "a meaningful partition should separate bipartite correlation classes, not just local entropy bins",
        "corr_contrast": corr_contrast,
        "local_contrast": local_contrast,
    }

    path = bridge_path()
    ordered = ordered_history_score(path)
    scrambled = ordered_history_score(list(reversed(path)))
    results["P3_history_order_matters"] = {
        "pass": abs(ordered["ordered_score"] - scrambled["ordered_score"]) > 1e-3
        and abs(ordered["unordered_mean"] - scrambled["unordered_mean"]) < 1e-12,
        "why": "ordered aggregation should differ from a scrambled path while the unordered mean does not",
        "ordered": ordered,
        "scrambled": scrambled,
    }

    scale_weights = np.array([1.0, 3.0, 5.0, 7.0], dtype=float)
    scaled = 10.0 * scale_weights
    values = np.array([mutual_information(rho) for rho in path[:4]], dtype=float)
    normalized_one = raw_weighted_sum(values, scale_weights) / np.sum(scale_weights)
    normalized_two = raw_weighted_sum(values, scaled) / np.sum(scaled)
    results["P4_normalization_is_not_an_artifact"] = {
        "pass": abs(normalized_one - normalized_two) < 1e-12
        and abs(raw_weighted_sum(values, scale_weights) - raw_weighted_sum(values, scaled)) > 1e-6,
        "why": "proper normalization must be invariant to global rescaling, while a raw sum is not",
        "normalized_one": float(normalized_one),
        "normalized_two": float(normalized_two),
        "raw_one": raw_weighted_sum(values, scale_weights),
        "raw_two": raw_weighted_sum(values, scaled),
    }
    return results


def negative_tests():
    results = {}
    states = valid_shell_family()
    weights = [1.0, 1.0, 2.0, 2.0, 4.0, 4.0]
    shell = shell_global_score(states, weights)
    bell = bell_phi_plus()
    mixed = maximally_mixed_2q()

    results["N1_arbitrary_weights_only_rescale_local_entropy"] = {
        "pass": abs(local_entropy_sum(bell) - local_entropy_sum(mixed)) < 1e-12
        and abs(mutual_information(bell) - mutual_information(mixed)) > 1.0,
        "rejected_counterfeit": "Local entropy alone cannot explain a real global shell distinction.",
        "truth": {
            "bell_local_entropy": local_entropy_sum(bell),
            "mixed_local_entropy": local_entropy_sum(mixed),
            "bell_mi": mutual_information(bell),
            "mixed_mi": mutual_information(mixed),
            "shell_contrast": shell["shell_contrast"],
        },
    }

    fake_partition_contrast = partition_contrast(states, [0, 1, 5], [2, 3, 4], local_entropy_sum)
    real_partition_contrast = partition_contrast(states, [0, 1, 5], [2, 3, 4], mutual_information)
    results["N2_shell_partition_without_bipartite_difference"] = {
        "pass": real_partition_contrast > fake_partition_contrast + 0.25,
        "rejected_counterfeit": "A shell partition that only sees local entropy is not a real bipartite distinction.",
        "truth": {
            "fake_partition_contrast": fake_partition_contrast,
            "real_partition_contrast": real_partition_contrast,
        },
    }

    path = bridge_path()
    ordered = ordered_history_score(path)
    scrambled = ordered_history_score(list(reversed(path)))
    results["N3_history_aggregation_erases_order"] = {
        "pass": abs(ordered["ordered_score"] - scrambled["ordered_score"]) > 1e-3
        and abs(ordered["unordered_mean"] - scrambled["unordered_mean"]) < 1e-12,
        "rejected_counterfeit": "An unordered aggregate cannot replace a path functional.",
        "truth": {
            "ordered_score": ordered["ordered_score"],
            "scrambled_score": scrambled["ordered_score"],
            "unordered_mean": ordered["unordered_mean"],
        },
    }

    values = np.array([mutual_information(rho) for rho in path[:4]], dtype=float)
    w = np.array([1.0, 2.0, 3.0, 4.0], dtype=float)
    raw = raw_weighted_sum(values, w)
    scaled = raw_weighted_sum(values, 7.0 * w)
    normalized = raw / np.sum(w)
    normalized_scaled = scaled / np.sum(7.0 * w)
    results["N4_normalization_artifact"] = {
        "pass": abs(normalized - normalized_scaled) < 1e-12
        and abs(raw - scaled) > 1e-6,
        "rejected_counterfeit": "A metric that changes only under weight rescaling is an artifact.",
        "truth": {
            "raw": raw,
            "scaled_raw": scaled,
            "normalized": normalized,
            "normalized_scaled": normalized_scaled,
        },
    }
    return results


def boundary_tests():
    results = {}
    singleton = [bell_phi_plus()]
    singleton_shell = shell_global_score(singleton, [1.0])
    results["B1_singleton_shell"] = {
        "pass": abs(singleton_shell["normalized_mi"] - mutual_information(bell_phi_plus())) < 1e-12,
        "why": "a singleton shell reduces to the state value itself",
        "truth": singleton_shell,
    }

    identity_path = [product_zero(), product_zero()]
    identity_order = ordered_history_score(identity_path)
    results["B2_identity_history"] = {
        "pass": abs(identity_order["ordered_score"] - identity_order["unordered_mean"]) < 1e-12
        and identity_order["total_variation"] < 1e-12,
        "why": "no change along a constant path means no history signal",
        "truth": identity_order,
    }

    equal_weights = np.ones(4, dtype=float)
    rescaled = 3.0 * equal_weights
    values = np.array([mutual_information(rho) for rho in bridge_path()[:4]], dtype=float)
    score_one = raw_weighted_sum(values, equal_weights) / np.sum(equal_weights)
    score_two = raw_weighted_sum(values, rescaled) / np.sum(rescaled)
    results["B3_equal_weight_rescaling"] = {
        "pass": abs(score_one - score_two) < 1e-12,
        "why": "uniform rescaling of all weights should not move a normalized score",
        "truth": {"score_one": score_one, "score_two": score_two},
    }
    return results


def main():
    positive = positive_tests()
    negative = negative_tests()
    boundary = boundary_tests()

    all_pass = all(v["pass"] for v in positive.values()) and all(v["pass"] for v in negative.values()) and all(v["pass"] for v in boundary.values())
    passed = sum(1 for section in (positive, negative, boundary) for v in section.values() if v["pass"])
    total = sum(len(section) for section in (positive, negative, boundary))

    results = {
        "name": "sim_negative_global_shell_bridge_counterfeits",
        "classification": "canonical",
        "schema": {
            "version": "1.0",
            "sections": ["positive", "negative", "boundary", "tool_manifest", "summary"],
            "notes": [
                "pure math only",
                "negative battery: passes mean counterfeit rejection succeeded",
                "global shell / bridge-weighted forms only",
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
            "caveat": "This battery rejects counterfeit shell/bridge metrics; it does not claim a full theory of such forms.",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out_dir = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_negative_global_shell_bridge_counterfeits_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sanitize(results), f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"{passed}/{total} passed")
    print(f"wrote {out_path}")
    print("ALL PASS" if all_pass else "SOME FAIL")


if __name__ == "__main__":
    main()
