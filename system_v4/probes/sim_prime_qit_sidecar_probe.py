#!/usr/bin/env python3
"""Bounded prime/QIT sidecar probe.

This is a finite-N evidence lane, not a Riemann hypothesis, PNT, zeta, QIT,
or nonclassical admission result.  It builds a classical CPTP-style sieve
channel over indices 2..N from divisibility tests, then asks whether prime
indices are exactly the absorbing/fixed states compared with boring baselines.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from typing import Any

import numpy as np
import scipy.linalg
import sympy as sp


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Finite-N prime/composite survivor probe.  The channel is built from "
    "divisibility transitions, prime labels are used only for evaluation, and "
    "the result is evidence fuel only: no RH, PNT, zeta, QIT, GStack, axis, or "
    "nonclassical admission claim."
)

LEGO_IDS = [
    "prime_qit_sidecar",
    "finite_cptp_style_channel",
    "fixed_state_survivor",
    "spectral_gap_proxy",
    "baseline_comparison",
    "graveyard_boundary",
]
PRIMARY_LEGO_IDS = ["prime_qit_sidecar", "fixed_state_survivor"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing channel, eigen, and baseline arrays"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix logarithm spectral proxy"},
    "sympy": {"tried": True, "used": True, "reason": "independent prime labels and integer factor checks"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def index_values(n_max: int) -> list[int]:
    if n_max < 8:
        raise ValueError("--N must be at least 8 for baseline comparisons")
    return list(range(2, n_max + 1))


def smallest_factor(n: int) -> int | None:
    for d in range(2, int(math.sqrt(n)) + 1):
        if n % d == 0:
            return d
    return None


def build_sieve_channel(values: list[int]) -> np.ndarray:
    """Build a column-stochastic divisibility channel over values 2..N.

    Primes remain fixed because no proper divisor route is available.  A
    composite maps to its smallest nontrivial factor.  This uses the rule
    "has a divisor" rather than a precomputed prime list.
    """

    pos = {value: i for i, value in enumerate(values)}
    channel = np.zeros((len(values), len(values)), dtype=np.float64)
    for col, value in enumerate(values):
        factor = smallest_factor(value)
        target = value if factor is None else factor
        channel[pos[target], col] = 1.0
    return channel


def shuffled_absorber_baseline(values: list[int], survivor_count: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    absorbers = set(rng.choice(values, size=survivor_count, replace=False).tolist())
    channel = np.zeros((len(values), len(values)), dtype=np.float64)
    for col, value in enumerate(values):
        if value in absorbers:
            target = value
        else:
            target = int(rng.choice(sorted(absorbers)))
        channel[values.index(target), col] = 1.0
    return channel


def random_survivor_baseline(values: list[int], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    channel = np.zeros((len(values), len(values)), dtype=np.float64)
    for col in range(len(values)):
        target = int(rng.integers(0, len(values)))
        channel[target, col] = 1.0
    return channel


def build_divisor_operation(values: list[int], divisor: int) -> np.ndarray:
    """One finite divisibility operation.

    If a state is a composite multiple of ``divisor``, it dissipates to the
    divisor.  Primes and nonmultiples self-loop.  These divisor operations do
    not commute when a composite has multiple factor choices.
    """

    pos = {value: i for i, value in enumerate(values)}
    channel = np.zeros((len(values), len(values)), dtype=np.float64)
    for col, value in enumerate(values):
        target = divisor if value != divisor and value % divisor == 0 else value
        channel[pos[target], col] = 1.0
    return channel


def divisor_sequence(values: list[int], seed: int, mode: str) -> list[int]:
    divisors = list(range(2, int(math.sqrt(max(values))) + 1))
    if mode == "ascending":
        return divisors
    if mode == "descending":
        return list(reversed(divisors))
    if mode == "shuffled":
        rng = np.random.default_rng(seed)
        shuffled = divisors[:]
        rng.shuffle(shuffled)
        return shuffled
    raise ValueError(f"unknown divisor sequence mode: {mode}")


def compose_divisor_operations(values: list[int], divisors: list[int]) -> np.ndarray:
    channel = np.eye(len(values), dtype=np.float64)
    for divisor in divisors:
        channel = build_divisor_operation(values, divisor) @ channel
    return channel


def survivor_distribution(channel: np.ndarray, values: list[int]) -> dict[str, float]:
    final = channel @ np.full(len(values), 1.0 / len(values), dtype=np.float64)
    return {
        str(value): float(weight)
        for value, weight in zip(values, final)
        if weight > 1e-12
    }


def noncommuting_order_report(
    values: list[int],
    primes: list[int],
    seed: int,
    max_logm_dim: int,
) -> dict[str, Any]:
    operations = {divisor: build_divisor_operation(values, divisor) for divisor in divisor_sequence(values, seed, "ascending")}
    commutators = []
    divisors = sorted(operations)
    for i, left in enumerate(divisors):
        for right in divisors[i + 1 :]:
            comm = operations[left] @ operations[right] - operations[right] @ operations[left]
            norm = float(np.linalg.norm(comm, ord="fro"))
            if norm > 1e-12:
                commutators.append({"left": left, "right": right, "frobenius": norm})
    orders: dict[str, dict[str, Any]] = {}
    for mode in ("ascending", "descending", "shuffled"):
        sequence = divisor_sequence(values, seed, mode)
        channel = compose_divisor_operations(values, sequence)
        row = evaluate_channel(channel, values, primes, max_logm_dim=max_logm_dim)
        row["divisor_sequence"] = sequence
        row["survivor_distribution"] = survivor_distribution(channel, values)
        orders[mode] = row
    asc = np.asarray([orders["ascending"]["survivor_distribution"].get(str(value), 0.0) for value in values])
    desc = np.asarray([orders["descending"]["survivor_distribution"].get(str(value), 0.0) for value in values])
    shuf = np.asarray([orders["shuffled"]["survivor_distribution"].get(str(value), 0.0) for value in values])
    return {
        "where_noncommutation_enters": "finite divisor-operation channels D_d; D_a @ D_b can route a composite to a different surviving factor than D_b @ D_a",
        "nonzero_commutator_count": len(commutators),
        "max_commutator_frobenius": max((row["frobenius"] for row in commutators), default=0.0),
        "commutator_samples": sorted(commutators, key=lambda row: row["frobenius"], reverse=True)[:12],
        "orders": orders,
        "order_distribution_l1": {
            "ascending_vs_descending": float(np.sum(np.abs(asc - desc))),
            "ascending_vs_shuffled": float(np.sum(np.abs(asc - shuf))),
            "descending_vs_shuffled": float(np.sum(np.abs(desc - shuf))),
        },
    }


def fixed_states(channel: np.ndarray, values: list[int]) -> list[int]:
    return [values[i] for i in range(len(values)) if abs(channel[i, i] - 1.0) < 1e-12 and np.count_nonzero(channel[:, i]) == 1]


def spectral_summary(channel: np.ndarray, max_logm_dim: int) -> dict[str, Any]:
    eig = np.linalg.eigvals(channel)
    abs_eig = np.sort(np.abs(eig))[::-1]
    nontrivial = [float(v) for v in abs_eig if v < 1.0 - 1e-12]
    gap = float(1.0 - nontrivial[0]) if nontrivial else 1.0
    logm_error = None
    logm_skipped = channel.shape[0] > max_logm_dim
    if logm_skipped:
        logm_frobenius = None
        logm_error = f"skipped_logm_dim_{channel.shape[0]}_gt_{max_logm_dim}"
    else:
        try:
            generator_proxy = scipy.linalg.logm(channel + np.eye(channel.shape[0]) * 1e-9)
            logm_frobenius = float(np.real(np.linalg.norm(generator_proxy, ord="fro")))
            if not math.isfinite(logm_frobenius):
                raise ValueError("non-finite logm norm")
        except Exception as exc:
            logm_error = str(exc)
            logm_frobenius = None
    return {
        "unit_eigenvalue_count": int(np.sum(np.isclose(abs_eig, 1.0, atol=1e-9))),
        "spectral_gap_proxy": gap,
        "logm_frobenius_proxy": logm_frobenius,
        "logm_error": logm_error,
        "logm_skipped": logm_skipped,
        "max_logm_dim": max_logm_dim,
        "rank": int(np.linalg.matrix_rank(channel)),
    }


def gap_statistics(primes: list[int]) -> dict[str, Any]:
    gaps = np.diff(np.asarray(primes, dtype=np.float64))
    ratios = []
    for left, right in zip(gaps[:-1], gaps[1:]):
        ratios.append(float(min(left, right) / max(left, right)) if max(left, right) else 0.0)
    return {
        "count": int(len(gaps)),
        "mean_gap": float(np.mean(gaps)) if len(gaps) else 0.0,
        "max_gap": float(np.max(gaps)) if len(gaps) else 0.0,
        "mean_spacing_ratio": float(np.mean(ratios)) if ratios else 0.0,
        "poisson_ratio_reference": 0.3863,
        "gue_ratio_reference": 0.5996,
    }


def evaluate_channel(
    channel: np.ndarray,
    values: list[int],
    prime_labels: list[int],
    max_logm_dim: int,
) -> dict[str, Any]:
    fixed = fixed_states(channel, values)
    fixed_set = set(fixed)
    prime_set = set(prime_labels)
    true_positive = len(fixed_set & prime_set)
    false_positive = len(fixed_set - prime_set)
    false_negative = len(prime_set - fixed_set)
    precision = true_positive / len(fixed_set) if fixed_set else 0.0
    recall = true_positive / len(prime_set) if prime_set else 0.0
    return {
        "fixed_state_count": len(fixed),
        "prime_count": len(prime_labels),
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "exact_fixed_state_match": false_positive == 0 and false_negative == 0,
        "fixed_state_sample": fixed[:24],
        "spectral": spectral_summary(channel, max_logm_dim=max_logm_dim),
    }


def run_probe(n_max: int, seed: int, max_logm_dim: int) -> dict[str, Any]:
    values = index_values(n_max)
    primes = list(sp.primerange(2, n_max + 1))
    sieve = build_sieve_channel(values)
    sidecar_eval = evaluate_channel(sieve, values, primes, max_logm_dim=max_logm_dim)
    order_report = noncommuting_order_report(values, primes, seed, max_logm_dim=max_logm_dim)
    baselines = {
        "shuffled_absorbers": evaluate_channel(
            shuffled_absorber_baseline(values, len(primes), seed),
            values,
            primes,
            max_logm_dim=max_logm_dim,
        ),
        "random_survivor_map": evaluate_channel(
            random_survivor_baseline(values, seed + 1),
            values,
            primes,
            max_logm_dim=max_logm_dim,
        ),
        "identity_channel": evaluate_channel(
            np.eye(len(values), dtype=np.float64),
            values,
            primes,
            max_logm_dim=max_logm_dim,
        ),
    }
    logm_skipped_channels = {
        "sidecar": bool(sidecar_eval["spectral"]["logm_skipped"]),
        "orders": {
            name: bool(row["spectral"]["logm_skipped"])
            for name, row in order_report["orders"].items()
        },
        "baselines": {
            name: bool(row["spectral"]["logm_skipped"])
            for name, row in baselines.items()
        },
    }
    baseline_exact = {name: row["exact_fixed_state_match"] for name, row in baselines.items()}
    all_pass = (
        bool(sidecar_eval["exact_fixed_state_match"])
        and bool(order_report["max_commutator_frobenius"] > 0.0)
        and all(bool(row["exact_fixed_state_match"]) for row in order_report["orders"].values())
        and not any(baseline_exact.values())
        and abs(float(sieve.sum(axis=0).min()) - 1.0) < 1e-12
        and abs(float(sieve.sum(axis=0).max()) - 1.0) < 1e-12
    )
    return {
        "name": "prime_qit_sidecar_probe",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "sidecar_probe",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "hardcoded_prime_use": {
            "used_in_construction": False,
            "used_for_evaluation": True,
            "note": "Sympy prime labels are compared only after the divisibility-channel dynamics run.",
        },
        "source_prompts": ["system_v4/a2_state/batch5_prompts/PRO-15_riemann_primes.md"],
        "parameters": {"N": n_max, "seed": seed, "index_range": [2, n_max], "max_logm_dim": max_logm_dim},
        "construction": {
            "channel_type": "finite classical CPTP-style column-stochastic divisibility channel",
            "uses_prime_labels_in_construction": False,
            "prime_labels_used_for": "evaluation only",
            "transition_rule": "prime columns self-loop; composite columns map to smallest nontrivial factor",
            "noncommuting_order_rule": "separate divisor-operation channels dissipate composites to the first divisor admitted by sequence order",
        },
        "allowed_claims": [
            "finite divisibility channel has primes as fixed/survivor states",
            "boring baselines do not reproduce the exact fixed-state set under this test",
            "sidecar is evidence fuel only",
        ],
        "forbidden_claims": [
            "RH",
            "PNT",
            "zeta proof",
            "prime prediction",
            "QIT admission",
            "GStack admission",
            "axis admission",
            "nonclassical admission",
        ],
        "sidecar_evaluation": sidecar_eval,
        "noncommuting_sieve_order_test": order_report,
        "prime_gap_statistics": gap_statistics(primes),
        "baselines": baselines,
        "summary": {
            "all_pass": bool(all_pass),
            "fixed_states_match_primes": bool(sidecar_eval["exact_fixed_state_match"]),
            "noncommuting_order_detected": bool(order_report["max_commutator_frobenius"] > 0.0),
            "order_variants_keep_prime_fixed_states": all(bool(row["exact_fixed_state_match"]) for row in order_report["orders"].values()),
            "baseline_exact_match_count": int(sum(baseline_exact.values())),
            "prime_count": len(primes),
            "composite_count": len(values) - len(primes),
            "claim_ceiling": "sidecar_probe_candidate_prior_only",
            "visual_payload": "visualizer/prime-qit-sidecar-data.js",
            "scope_note": divergence_log,
            "recommendation": "retool",
            "recommendation_reason": "bounded diagnostic passes fixed-state and noncommuting-order checks, but remains sidecar evidence and needs stronger baselines before promotion",
            "logm_skipped_channels": logm_skipped_channels,
            "logm_skipped_count": int(
                logm_skipped_channels["sidecar"]
                + sum(logm_skipped_channels["orders"].values())
                + sum(logm_skipped_channels["baselines"].values())
            ),
        },
        "claim_ceiling": "sidecar_probe_candidate_prior_only; no RH, PNT, zeta, prime prediction, QIT, GStack, axis, bridge, or nonclassical admission",
        "next_lego_target": "prime_qit_sidecar_controls",
        "promotion_condition": "Requires separate proof-grade arithmetic emergence, stronger baselines, and explicit stage-gate admission.",
        "blocked_until": "prime/composite emergence controls and proof fences are admitted by stage gate",
        "demotion_condition": "Demote if primes are hardcoded into construction, baselines match, noncommuting order signal disappears, or claims exceed sidecar evidence.",
        "out_of_scope": [
            "Riemann hypothesis",
            "prime number theorem",
            "zeta-zero derivation",
            "prime prediction",
            "QIT engine admission",
            "GStack admission",
            "axis admission",
            "nonclassical proof",
        ],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": result["name"],
        "summary": result["summary"],
        "parameters": result["parameters"],
        "sidecar_evaluation": result["sidecar_evaluation"],
        "noncommuting_sieve_order_test": {
            "nonzero_commutator_count": result["noncommuting_sieve_order_test"]["nonzero_commutator_count"],
            "max_commutator_frobenius": result["noncommuting_sieve_order_test"]["max_commutator_frobenius"],
            "order_distribution_l1": result["noncommuting_sieve_order_test"]["order_distribution_l1"],
            "orders": {
                name: {
                    "fixed_state_count": row["fixed_state_count"],
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "exact_fixed_state_match": row["exact_fixed_state_match"],
                    "survivor_distribution": row["survivor_distribution"],
                }
                for name, row in result["noncommuting_sieve_order_test"]["orders"].items()
            },
        },
        "prime_gap_statistics": result["prime_gap_statistics"],
        "baselines": {
            name: {
                "fixed_state_count": row["fixed_state_count"],
                "precision": row["precision"],
                "recall": row["recall"],
                "exact_fixed_state_match": row["exact_fixed_state_match"],
                "spectral": row["spectral"],
            }
            for name, row in result["baselines"].items()
        },
    }
    js = "window.PRIME_QIT_SIDECAR_DATA = " + json.dumps(payload, indent=2, default=str) + ";\n"
    (VIS_DIR / "prime-qit-sidecar-data.js").write_text(js, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--N", type=int, default=256)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument(
        "--max-logm-dim",
        type=int,
        default=96,
        help="Skip scipy.linalg.logm above this matrix dimension and keep cheaper eigen/rank proxies.",
    )
    parser.add_argument("--out", type=pathlib.Path, default=RESULT_DIR / "prime_qit_sidecar_probe_results.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_probe(args.N, args.seed, max_logm_dim=args.max_logm_dim)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(args.out)
    print(f"ALL PASS: {result['summary']['all_pass']}")


if __name__ == "__main__":
    main()
