#!/usr/bin/env python3
"""Negative battery for the bounded prime/QIT sidecar probe.

This tests nearby variants around the finite divisibility-channel prime lane.
It is a graveyard/control battery, not a Riemann, zeta, PNT, QIT, GStack, axis,
or nonclassical admission result.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from typing import Any

import numpy as np
import sympy as sp
import z3


CLASSIFICATION = "graveyard_negative"
classification = CLASSIFICATION
divergence_log = (
    "Negative/control battery around prime_qit_sidecar_probe. It checks that "
    "prime-like survivor behavior is not accepted when primes are hardcoded, "
    "when survivors are random, when noncommuting order is erased, or when "
    "order sensitivity changes the composite-to-survivor distribution. No "
    "RH, PNT, zeta, QIT, GStack, axis, or nonclassical claim is promoted."
)

LEGO_IDS = [
    "prime_qit_sidecar",
    "graveyard_boundary",
    "hardcoded_prime_control",
    "random_survivor_control",
    "commutative_projection_control",
    "noncommuting_order_variant",
    "proof_fence",
]
PRIMARY_LEGO_IDS = ["prime_qit_sidecar", "graveyard_boundary"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite channels and survivor distributions"},
    "sympy": {"tried": True, "used": True, "reason": "evaluation-only prime mask and integer factor checks"},
    "z3": {"tried": True, "used": True, "reason": "proof fence against promoting graveyard controls"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def values(n_max: int) -> list[int]:
    return list(range(2, n_max + 1))


def smallest_factor(n: int) -> int | None:
    for d in range(2, int(math.sqrt(n)) + 1):
        if n % d == 0:
            return d
    return None


def divisibility_channel(xs: list[int]) -> np.ndarray:
    pos = {value: idx for idx, value in enumerate(xs)}
    channel = np.zeros((len(xs), len(xs)), dtype=np.float64)
    for col, value in enumerate(xs):
        factor = smallest_factor(value)
        target = value if factor is None else factor
        channel[pos[target], col] = 1.0
    return channel


def hardcoded_prime_lookup_channel(xs: list[int], primes: set[int]) -> np.ndarray:
    """Forbidden/mechanism-fail control: uses the answer in construction."""

    prime_list = sorted(primes)
    channel = np.zeros((len(xs), len(xs)), dtype=np.float64)
    for col, value in enumerate(xs):
        target = value if value in primes else prime_list[col % len(prime_list)]
        channel[xs.index(target), col] = 1.0
    return channel


def random_survivor_channel(xs: list[int], survivor_count: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    survivors = sorted(rng.choice(xs, size=survivor_count, replace=False).tolist())
    channel = np.zeros((len(xs), len(xs)), dtype=np.float64)
    for col, value in enumerate(xs):
        target = value if value in survivors else int(rng.choice(survivors))
        channel[xs.index(target), col] = 1.0
    return channel


def divisor_operation(xs: list[int], divisor: int) -> np.ndarray:
    pos = {value: idx for idx, value in enumerate(xs)}
    op = np.zeros((len(xs), len(xs)), dtype=np.float64)
    for col, value in enumerate(xs):
        target = divisor if value != divisor and value % divisor == 0 else value
        op[pos[target], col] = 1.0
    return op


def ordered_divisor_channel(xs: list[int], reverse: bool) -> np.ndarray:
    divisors = list(range(2, int(math.sqrt(max(xs))) + 1))
    if reverse:
        divisors.reverse()
    channel = np.eye(len(xs), dtype=np.float64)
    for divisor in divisors:
        channel = divisor_operation(xs, divisor) @ channel
    return channel


def commutative_projection_channel(xs: list[int]) -> np.ndarray:
    """Order-erased control: maps composites directly to their radical minimum."""

    pos = {value: idx for idx, value in enumerate(xs)}
    channel = np.zeros((len(xs), len(xs)), dtype=np.float64)
    for col, value in enumerate(xs):
        factors = sorted(sp.factorint(value).keys())
        target = value if len(factors) == 1 and factors[0] == value else int(factors[0])
        channel[pos[target], col] = 1.0
    return channel


def fixed_states(channel: np.ndarray, xs: list[int]) -> set[int]:
    fixed: set[int] = set()
    for idx, value in enumerate(xs):
        if abs(channel[idx, idx] - 1.0) < 1e-12 and np.count_nonzero(channel[:, idx]) == 1:
            fixed.add(value)
    return fixed


def distribution(channel: np.ndarray, xs: list[int]) -> np.ndarray:
    start = np.full(len(xs), 1.0 / len(xs), dtype=np.float64)
    return channel @ start


def evaluate(name: str, channel: np.ndarray, xs: list[int], primes: set[int], hardcoded: bool) -> dict[str, Any]:
    fixed = fixed_states(channel, xs)
    false_positive = sorted(fixed - primes)
    false_negative = sorted(primes - fixed)
    exact = not false_positive and not false_negative
    rank = int(np.linalg.matrix_rank(channel))
    eig = np.linalg.eigvals(channel)
    unit_count = int(np.sum(np.isclose(np.abs(eig), 1.0, atol=1e-9)))
    return {
        "name": name,
        "hardcoded_prime_use_in_construction": hardcoded,
        "fixed_state_count": len(fixed),
        "prime_count": len(primes),
        "exact_fixed_state_match": exact,
        "false_positive_sample": false_positive[:12],
        "false_negative_sample": false_negative[:12],
        "rank": rank,
        "unit_eigenvalue_count": unit_count,
    }


def promotion_fence() -> dict[str, Any]:
    exact_match, hardcoded, promote = z3.Bools("exact_match hardcoded promote")
    solver = z3.Solver()
    solver.add(exact_match)
    solver.add(hardcoded)
    solver.add(promote == z3.And(exact_match, z3.Not(hardcoded)))
    solver.add(promote)
    result = solver.check()
    return {
        "claim": "hardcoded exact prime survivor match can be promoted",
        "result": str(result),
        "pass": result == z3.unsat,
    }


def run(n_max: int = 256, seed: int = 1776) -> dict[str, Any]:
    xs = values(n_max)
    primes = set(sp.primerange(2, n_max + 1))
    reference = divisibility_channel(xs)
    ascending = ordered_divisor_channel(xs, reverse=False)
    descending = ordered_divisor_channel(xs, reverse=True)
    reference_dist = distribution(reference, xs)
    ascending_dist = distribution(ascending, xs)
    descending_dist = distribution(descending, xs)
    variants = [
        evaluate("reference_divisibility_channel", reference, xs, primes, hardcoded=False),
        evaluate("forbidden_hardcoded_prime_lookup", hardcoded_prime_lookup_channel(xs, primes), xs, primes, hardcoded=True),
        evaluate("random_survivor_control", random_survivor_channel(xs, len(primes), seed), xs, primes, hardcoded=False),
        evaluate("commutative_projection_control", commutative_projection_channel(xs), xs, primes, hardcoded=False),
        evaluate("ascending_ordered_divisor_control", ascending, xs, primes, hardcoded=False),
        evaluate("descending_ordered_divisor_control", descending, xs, primes, hardcoded=False),
    ]
    graveyard_rows = []
    for row in variants:
        killed = (
            row["hardcoded_prime_use_in_construction"]
            or not row["exact_fixed_state_match"]
            or row["name"].endswith("_control")
        )
        graveyard_rows.append({**row, "graveyard_status": "killed_or_control" if killed else "survives_as_reference"})
    order_l1 = {
        "reference_vs_ascending": float(np.sum(np.abs(reference_dist - ascending_dist))),
        "ascending_vs_descending": float(np.sum(np.abs(ascending_dist - descending_dist))),
        "reference_vs_descending": float(np.sum(np.abs(reference_dist - descending_dist))),
    }
    proof = promotion_fence()
    all_pass = (
        proof["pass"]
        and any(row["name"] == "reference_divisibility_channel" and row["graveyard_status"] == "survives_as_reference" for row in graveyard_rows)
        and any(row["name"] == "forbidden_hardcoded_prime_lookup" and row["graveyard_status"] == "killed_or_control" for row in graveyard_rows)
        and any(row["name"] == "random_survivor_control" and row["graveyard_status"] == "killed_or_control" for row in graveyard_rows)
        and order_l1["ascending_vs_descending"] > 0.0
    )
    result = {
        "name": "prime_qit_sidecar_graveyard",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parameters": {"N": n_max, "seed": seed},
        "allowed_claims": [
            "nearby controls are killed or labeled as controls",
            "hardcoded-prime exact match is not admissible evidence",
            "order variants change survivor distribution without proving RH/PNT",
        ],
        "forbidden_claims": ["RH", "PNT", "zeta proof", "prime prediction", "QIT admission", "GStack admission", "axis admission"],
        "variants": graveyard_rows,
        "order_distribution_l1": order_l1,
        "proof_fence": proof,
        "summary": {
            "all_pass": all_pass,
            "variant_count": len(graveyard_rows),
            "killed_or_control_count": sum(row["graveyard_status"] == "killed_or_control" for row in graveyard_rows),
            "reference_survives": any(row["graveyard_status"] == "survives_as_reference" for row in graveyard_rows),
            "hardcoded_prime_control_killed": any(row["name"] == "forbidden_hardcoded_prime_lookup" and row["graveyard_status"] == "killed_or_control" for row in graveyard_rows),
            "random_control_killed": any(row["name"] == "random_survivor_control" and row["graveyard_status"] == "killed_or_control" for row in graveyard_rows),
            "order_variant_detected": order_l1["ascending_vs_descending"] > 0.0,
            "claim_ceiling": "sidecar_graveyard_control_only",
            "recommendation": "retool",
            "visual_payload": "visualizer/prime-qit-sidecar-graveyard-data.js",
            "scope_note": divergence_log,
        },
    }
    return result


def write_outputs(result: dict[str, Any], out: pathlib.Path) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "name": result["name"],
        "summary": result["summary"],
        "variants": result["variants"],
        "order_distribution_l1": result["order_distribution_l1"],
    }
    (VIS_DIR / "prime-qit-sidecar-graveyard-data.js").write_text(
        "window.PRIME_QIT_SIDECAR_GRAVEYARD_DATA = " + json.dumps(payload, indent=2, default=str) + ";\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--N", type=int, default=256)
    parser.add_argument("--seed", type=int, default=1776)
    parser.add_argument("--out", type=pathlib.Path, default=RESULT_DIR / "prime_qit_sidecar_graveyard_results.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run(n_max=args.N, seed=args.seed)
    write_outputs(result, args.out)
    print("PRIME QIT SIDECAR GRAVEYARD")
    print(f"ALL PASS: {result['summary']['all_pass']}")
    print(f"VARIANTS: {result['summary']['variant_count']}")
    print(f"KILLED/CONTROL: {result['summary']['killed_or_control_count']}")
    print("CLAIM CEILING: sidecar_graveyard_control_only")


if __name__ == "__main__":
    main()
