#!/usr/bin/env python3
"""Nonassociative stacking, G2/F4, and bounded-stack entropic geometry.

This is a finite, dependency-light execution of the owner-proposed exceptional
rungs.  It earns O within the compared Cayley--Dickson ladder.  F4 is then run
as the symmetry of the Albert/Jordan extension, but remains a defaulted owner
hypothesis rather than a claim that the earlier layers uniquely force it.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EXCEPTIONAL_RESULT = (
    ROOT
    / "native_runs/repo_snapshot/system_v7/constraint_core/sims_and_scripts"
    / "exceptional_lie_ratchet_sim_results.json"
)


def conjugate(value: np.ndarray) -> np.ndarray:
    out = -np.asarray(value, dtype=float).copy()
    out[0] *= -1.0
    return out


def cd_multiply(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if len(left) == 1:
        return left * right
    half = len(left) // 2
    a, b = left[:half], left[half:]
    c, d = right[:half], right[half:]
    return np.concatenate((
        cd_multiply(a, c) - cd_multiply(conjugate(d), b),
        cd_multiply(d, a) + cd_multiply(b, conjugate(c)),
    ))


def basis(dimension: int, index: int) -> np.ndarray:
    out = np.zeros(dimension)
    out[index] = 1.0
    return out


def commutator(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return cd_multiply(a, b) - cd_multiply(b, a)


def associator(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    return cd_multiply(cd_multiply(a, b), c) - cd_multiply(a, cd_multiply(b, c))


def exact_basis_census(dimension: int) -> dict[str, Any]:
    vectors = [basis(dimension, index) for index in range(dimension)]
    commutator_norms = [
        float(np.linalg.norm(commutator(a, b)))
        for a in vectors
        for b in vectors
    ]
    associator_vectors = np.asarray([
        associator(a, b, c)
        for a in vectors
        for b in vectors
        for c in vectors
    ])
    associator_norms = np.linalg.norm(associator_vectors, axis=1)
    weights = associator_norms**2
    if float(weights.sum()) > 0.0:
        probabilities = weights / weights.sum()
        positive = probabilities[probabilities > 0.0]
        entropy = float(-np.sum(positive * np.log(positive)))
        mean = probabilities @ associator_vectors
        centered = associator_vectors - mean
        fisher = (centered * probabilities[:, None]).T @ centered
        eigenvalues = np.linalg.eigvalsh(0.5 * (fisher + fisher.T))
    else:
        entropy = 0.0
        fisher = np.zeros((dimension, dimension))
        eigenvalues = np.zeros(dimension)
    return {
        "dimension": dimension,
        "basis_pair_count": dimension**2,
        "basis_triple_count": dimension**3,
        "max_commutator_norm": max(commutator_norms),
        "max_associator_norm": float(associator_norms.max()),
        "nonzero_associator_count": int(np.sum(associator_norms > 1.0e-12)),
        "associator_distribution_entropy_nats": entropy,
        "associator_KL_hessian_trace": float(np.trace(fisher)),
        "associator_KL_hessian_rank": int(np.sum(eigenvalues > 1.0e-9)),
        "associator_KL_hessian_eigenvalues": [float(value) for value in eigenvalues],
        "geometry": "Fisher/KL Hessian of the exponential family whose sufficient statistic is the full signed associator vector",
    }


def norm_persistence(dimension: int, seed: int = 186) -> dict[str, Any]:
    rng = np.random.default_rng(seed + dimension)
    errors = []
    for _ in range(128):
        a = rng.normal(size=dimension)
        b = rng.normal(size=dimension)
        product = cd_multiply(a, b)
        errors.append(abs(float(product @ product) - float(a @ a) * float(b @ b)))
    return {"max_norm_multiplication_error": max(errors)}


def division_ladder() -> dict[str, Any]:
    names = [("R", 1), ("C", 2), ("H", 4), ("O", 8), ("S", 16)]
    rows = []
    for name, dimension in names:
        census = exact_basis_census(dimension)
        persistence = norm_persistence(dimension)
        row = {
            "candidate": name,
            **census,
            **persistence,
        }
        row["noncommutative"] = row["max_commutator_norm"] > 1.0e-12
        row["nonassociative"] = row["max_associator_norm"] > 1.0e-12
        row["norm_persistent"] = row["max_norm_multiplication_error"] < 1.0e-8
        row["meets_stacking_requirements"] = bool(
            row["noncommutative"] and row["nonassociative"] and row["norm_persistent"]
        )
        row["presumption_vector"] = [int(round(math.log2(dimension))), dimension]
        rows.append(row)

    a = basis(16, 1) + basis(16, 10)
    b = basis(16, 5) + basis(16, 14)
    zero_divisor_norm = float(np.linalg.norm(cd_multiply(a, b)))
    frontier = [row for row in rows if row["meets_stacking_requirements"]]
    frontier.sort(key=lambda row: tuple(row["presumption_vector"]))
    return {
        "requirements": ["noncommuting composition", "nonassociative renesting", "norm persistence"],
        "rows": rows,
        "packet_relative_mss": frontier[0]["candidate"] if frontier else None,
        "sedenion_deletion_witness": {
            "left_norm": float(np.linalg.norm(a)),
            "right_norm": float(np.linalg.norm(b)),
            "product_norm": zero_divisor_norm,
        },
    }


def jordan_spectral_geometry() -> dict[str, Any]:
    logits = np.asarray([0.31, -0.17, 0.0])
    weights = np.exp(logits - logits.max())
    eigenvalues = weights / weights.sum()
    entropy = float(-np.sum(eigenvalues * np.log(eigenvalues)))
    # Two independent diagonal Albert/Jordan spectral coordinates; the third
    # is fixed by normalization.  This is an exact simplex slice of J3(O).
    fisher_full = np.diag(eigenvalues) - np.outer(eigenvalues, eigenvalues)
    fisher = fisher_full[:2, :2]
    return {
        "object": "diagonal spectral slice of J3(O), lambda_i>=0, sum lambda_i=1",
        "jordan_eigenvalues": [float(value) for value in eigenvalues],
        "jordan_spectral_entropy_nats": entropy,
        "relative_entropy": "D_J(lambda||mu)=sum_i lambda_i log(lambda_i/mu_i)",
        "fisher_BKM_metric": [[float(value) for value in row] for row in fisher],
        "metric_eigenvalues": [float(value) for value in np.linalg.eigvalsh(fisher)],
        "geometry_scope": "exact positive diagonal Jordan slice; not a numerical atlas of all F4 orbits",
    }


def structure_reduction() -> dict[str, Any]:
    rows = [
        ("SO(8)", 28, "metric"),
        ("Spin(7)", 21, "Cayley_4_form"),
        ("G2", 14, "associator_3_form"),
        ("SU(3)", 8, "chosen_imaginary_octonion"),
        ("SU(2)", 3, "chosen_complex_line"),
    ]
    return {
        "chain": [
            {
                "group": name,
                "generator_capacity": dimension,
                "log_generator_capacity_nats": math.log(dimension),
                "stabilized_structure": structure,
                "codimension_from_previous": 0 if index == 0 else rows[index - 1][1] - dimension,
            }
            for index, (name, dimension, structure) in enumerate(rows)
        ],
        "geometry": "directed stabilizer-inclusion graph with codimension on each edge",
        "entropy_scope": "log finite generator capacity, not an uncomputed Haar orbit volume",
    }


def run_exceptional_stack_layer() -> dict[str, Any]:
    ladder = division_ladder()
    native = json.loads(EXCEPTIONAL_RESULT.read_text(encoding="utf-8"))
    derived = native["derived_from_scratch"]
    jordan = jordan_spectral_geometry()
    reduction = structure_reduction()
    o_row = next(row for row in ladder["rows"] if row["candidate"] == "O")
    h_row = next(row for row in ladder["rows"] if row["candidate"] == "H")
    s_row = next(row for row in ladder["rows"] if row["candidate"] == "S")
    checks = {
        "octonion_is_least_compared_persistent_nonassociative_stack": ladder["packet_relative_mss"] == "O",
        "quaternion_control_is_associative": h_row["max_associator_norm"] < 1.0e-12,
        "octonion_associator_geometry_nontrivial": (
            o_row["associator_KL_hessian_trace"] > 1.0e-6
            and o_row["associator_KL_hessian_rank"] >= 7
        ),
        "sedenion_zero_divisor_reproduced": ladder["sedenion_deletion_witness"]["product_norm"] < 1.0e-12,
        "sedenion_norm_persistence_fails": not s_row["norm_persistent"],
        "g2_dimension_derived": derived["g2_dim"] == 14,
        "f4_dimension_derived": derived["f4_dim"] == 52,
        "g2_embeds_in_f4": derived["g2_embeds_in_f4_jordan_derivation_defect"] < 1.0e-9,
        "jordan_spectral_metric_positive": min(jordan["metric_eigenvalues"]) > 0.0,
        "reduction_chain_strict": all(
            row["codimension_from_previous"] > 0 for row in reduction["chain"][1:]
        ),
    }
    return {
        "schema": "ratchet.exceptional_stack_entropic_geometry.v1",
        "stacking_layer": ladder,
        "g2_f4_native_result": native,
        "bounded_jordan_layer": jordan,
        "structure_reduction_layer": reduction,
        "ratchet_disposition": {
            "O_G2": "earned within the compared persistence/nonassociativity ladder",
            "J3O_F4": "executed owner-hypothesis default; not uniquely forced by lower residuals",
            "E6": "native dimension derived; not installed as a necessary manifold layer",
            "E7_E8": "cited-only in donor sim; excluded from this executed manifold",
        },
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def main() -> int:
    result = run_exceptional_stack_layer()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
