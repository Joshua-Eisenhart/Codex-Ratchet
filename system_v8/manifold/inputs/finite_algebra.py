#!/usr/bin/env python3
"""Exact finite division-algebra, Hopf, spinor-memory, and bracket witnesses.

No NumPy, SciPy, solver, physics label, or desired owner outcome is used.  The
module reproduces the load-bearing mathematics of two pinned repository sims
with rational Cayley-Dickson arithmetic and analytic two-component spinors.
"""

from __future__ import annotations

import cmath
import itertools
import math
import random
from fractions import Fraction
from functools import lru_cache
from typing import Any, Iterable


Vector = tuple[Fraction, ...]


def vec(values: Iterable[int | Fraction]) -> Vector:
    return tuple(value if isinstance(value, Fraction) else Fraction(value) for value in values)


def add(left: Vector, right: Vector) -> Vector:
    return tuple(a + b for a, b in zip(left, right))


def subtract(left: Vector, right: Vector) -> Vector:
    return tuple(a - b for a, b in zip(left, right))


def scale(factor: int | Fraction, value: Vector) -> Vector:
    factor = factor if isinstance(factor, Fraction) else Fraction(factor)
    return tuple(factor * item for item in value)


def conjugate(value: Vector) -> Vector:
    return (value[0],) + tuple(-item for item in value[1:])


def cayley_dickson_multiply(left: Vector, right: Vector) -> Vector:
    if len(left) != len(right) or not len(left) or len(left) & (len(left) - 1):
        raise ValueError("Cayley-Dickson operands require equal power-of-two dimension")
    if len(left) == 1:
        return (left[0] * right[0],)
    half = len(left) // 2
    a1, a2 = left[:half], left[half:]
    b1, b2 = right[:half], right[half:]
    first = subtract(
        cayley_dickson_multiply(a1, b1),
        cayley_dickson_multiply(conjugate(b2), a2),
    )
    second = add(
        cayley_dickson_multiply(b2, a1),
        cayley_dickson_multiply(a2, conjugate(b1)),
    )
    return first + second


def basis(dimension: int, index: int) -> Vector:
    if index < 0 or index >= dimension:
        raise ValueError("basis index out of range")
    return tuple(Fraction(int(position == index)) for position in range(dimension))


def norm_squared(value: Vector) -> Fraction:
    return sum((item * item for item in value), Fraction(0))


def associator(a: Vector, b: Vector, c: Vector) -> Vector:
    return subtract(
        cayley_dickson_multiply(cayley_dickson_multiply(a, b), c),
        cayley_dickson_multiply(a, cayley_dickson_multiply(b, c)),
    )


def hopf_map(a: Vector, b: Vector) -> tuple[Vector, Fraction]:
    if len(a) not in (2, 4, 8) or len(a) != len(b):
        raise ValueError("finite Hopf map implemented for C, H, and O pairs")
    algebra_part = scale(2, cayley_dickson_multiply(a, conjugate(b)))
    real_part = norm_squared(a) - norm_squared(b)
    return algebra_part, real_part


def hopf_norm_identity(a: Vector, b: Vector) -> dict[str, Any]:
    algebra_part, real_part = hopf_map(a, b)
    left = norm_squared(algebra_part) + real_part * real_part
    right = (norm_squared(a) + norm_squared(b)) ** 2
    return {
        "algebra_dimension": len(a),
        "total_space_sphere_dimension": 2 * len(a) - 1,
        "base_sphere_dimension": len(a),
        "left": left,
        "right": right,
        "passed": left == right,
    }


def embedded(value: Vector, dimension: int) -> Vector:
    if len(value) > dimension:
        raise ValueError("cannot embed into a smaller algebra")
    return value + tuple(Fraction(0) for _ in range(dimension - len(value)))


@lru_cache(maxsize=1)
def division_ladder_report() -> dict[str, Any]:
    # One nontrivial exact pair is embedded C -> H -> O.  This tests a real
    # higher-Hopf ladder without declaring it the physical shell order.
    a2 = vec((2, 1))
    b2 = vec((1, -2))
    rows = []
    bases = []
    for dimension in (2, 4, 8):
        a = embedded(a2, dimension)
        b = embedded(b2, dimension)
        rows.append(hopf_norm_identity(a, b))
        algebra_part, real_part = hopf_map(a, b)
        bases.append((algebra_part, real_part))
    projection_consistent = (
        bases[1][0][:2] == bases[0][0]
        and all(value == 0 for value in bases[1][0][2:])
        and bases[2][0][:4] == bases[1][0]
        and all(value == 0 for value in bases[2][0][4:])
        and len({row[1] for row in bases}) == 1
    )
    return {
        "hopf_rungs": ["S3_to_S2", "S7_to_S4", "S15_to_S8"],
        "norm_identities": rows,
        "nested_subalgebra_projection_consistent": projection_consistent,
        "all_pass": all(row["passed"] for row in rows) and projection_consistent,
        "claim_ceiling": "exact division-algebra Hopf identities and embeddings only",
    }


def density_from_spinor(spinor: tuple[complex, complex]) -> list[list[complex]]:
    return [
        [spinor[row] * spinor[column].conjugate() for column in range(2)]
        for row in range(2)
    ]


def matrix_distance(left: list[list[complex]], right: list[list[complex]]) -> float:
    return math.sqrt(sum(abs(left[i][j] - right[i][j]) ** 2 for i in range(2) for j in range(2)))


@lru_cache(maxsize=1)
def spinor_memory_report() -> dict[str, Any]:
    overlaps = []
    density_distances = []
    psi0 = (1 + 0j, 0j)
    rho0 = density_from_spinor(psi0)
    for angle in (0.0, 2.0 * math.pi, 4.0 * math.pi):
        phase = cmath.exp(-0.5j * angle)
        spinor = (phase, 0j)
        overlaps.append((psi0[0].conjugate() * spinor[0] + psi0[1].conjugate() * spinor[1]).real)
        density_distances.append(matrix_distance(rho0, density_from_spinor(spinor)))

    ticks = 300
    rate = 0.03
    # For two opposed z eigenstates, z-dephasing preserves trace distance 1.
    # x-dephasing multiplies their Bloch-z separation by (1-2*rate) per tick.
    direct = 1.0
    conjugated = (1.0 - 2.0 * rate) ** ticks
    return {
        "overlaps_0_2pi_4pi": overlaps,
        "density_distances": density_distances,
        "direct_sheet_retention_after_300": direct,
        "conjugated_sheet_retention_after_300": conjugated,
        "retention_ratio": direct / max(conjugated, 1e-300),
        "spinor_lift_retains_density_erased_loop_parity": (
            abs(overlaps[0] - 1.0) < 1e-12
            and abs(overlaps[1] + 1.0) < 1e-12
            and abs(overlaps[2] - 1.0) < 1e-12
            and max(density_distances) < 1e-12
        ),
        "sheet_selective_retention": direct > 0.95 and conjugated < 0.05,
        "all_pass": False,
    }


def apply_unsigned_permutation(value: Vector, permutation: tuple[int, ...]) -> Vector:
    result = [value[0]] + [Fraction(0) for _ in permutation]
    for old_index, new_index in enumerate(permutation, start=1):
        result[new_index] = value[old_index]
    return tuple(result)


@lru_cache(maxsize=1)
def find_basis_automorphism() -> tuple[int, ...]:
    dimension = 8
    imaginary = tuple(range(1, dimension))
    products = {
        (left, right): cayley_dickson_multiply(basis(dimension, left), basis(dimension, right))
        for left in range(dimension)
        for right in range(dimension)
    }
    for permutation_values in itertools.permutations(imaginary):
        permutation = (0,) + permutation_values
        if permutation == tuple(range(dimension)):
            continue
        valid = True
        for left in range(dimension):
            for right in range(dimension):
                mapped_product = apply_unsigned_permutation(products[(left, right)], permutation_values)
                image_product = products[(permutation[left], permutation[right])]
                if mapped_product != image_product:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            return permutation_values
    raise AssertionError("no nonidentity basis automorphism found")


@lru_cache(maxsize=1)
def octonion_network_report() -> dict[str, Any]:
    dimension = 8
    witness = None
    rng = random.Random(3)
    trials = []
    for _ in range(4096):
        rows = []
        for _item in range(4):
            candidate = tuple(Fraction(rng.choice((-1, 0, 1))) for _coordinate in range(dimension))
            while not any(candidate):
                candidate = tuple(Fraction(rng.choice((-1, 0, 1))) for _coordinate in range(dimension))
            rows.append(candidate)
        trials.append(rows)
    for trial_index, rows in enumerate(trials):
        edges = rows[:3]
        signal = rows[3]
        left = cayley_dickson_multiply(
            edges[2],
            cayley_dickson_multiply(edges[1], cayley_dickson_multiply(edges[0], signal)),
        )
        mixed = cayley_dickson_multiply(
            cayley_dickson_multiply(edges[2], edges[1]),
            cayley_dickson_multiply(edges[0], signal),
        )
        gap = norm_squared(subtract(left, mixed))
        edge_associator_gap = norm_squared(associator(edges[0], edges[1], edges[2]))
        left_chiral = signal
        right_chiral = signal
        for edge in edges:
            left_chiral = cayley_dickson_multiply(edge, left_chiral)
            right_chiral = cayley_dickson_multiply(right_chiral, conjugate(edge))
        chiral_gap = norm_squared(subtract(left_chiral, right_chiral))
        if gap and edge_associator_gap and chiral_gap:
            witness = (
                edges,
                signal,
                left,
                mixed,
                gap,
                edge_associator_gap,
                chiral_gap,
                trial_index,
            )
            break
    if witness is None:
        raise AssertionError("failed to locate octonion path-bracketing witness")
    edges, signal, left, mixed, gap, associator_gap, chirality_gap, trial_index = witness

    permutation = find_basis_automorphism()
    mapped_edges = [apply_unsigned_permutation(edge, permutation) for edge in edges]
    mapped_signal = apply_unsigned_permutation(signal, permutation)
    mapped_left = cayley_dickson_multiply(
        mapped_edges[2],
        cayley_dickson_multiply(mapped_edges[1], cayley_dickson_multiply(mapped_edges[0], mapped_signal)),
    )
    mapped_mixed = cayley_dickson_multiply(
        cayley_dickson_multiply(mapped_edges[2], mapped_edges[1]),
        cayley_dickson_multiply(mapped_edges[0], mapped_signal),
    )
    mapped_gap = norm_squared(subtract(mapped_left, mapped_mixed))
    automorphism_exact = True
    for left_index in range(dimension):
        for right_index in range(dimension):
            a = basis(dimension, left_index)
            b = basis(dimension, right_index)
            if apply_unsigned_permutation(cayley_dickson_multiply(a, b), permutation) != cayley_dickson_multiply(
                apply_unsigned_permutation(a, permutation),
                apply_unsigned_permutation(b, permutation),
            ):
                automorphism_exact = False
                break

    result = {
        "deterministic_integer_witness_trial": trial_index,
        "edge_vectors": edges,
        "signal_vector": signal,
        "path_bracketing_gap_squared": gap,
        "single_edge_bracketing_gap_squared": Fraction(0),
        "edge_associator_gap_squared": associator_gap,
        "left_right_chirality_gap_squared": chirality_gap,
        "nonidentity_basis_automorphism": permutation,
        "automorphism_exact_on_full_basis_table": automorphism_exact,
        "bracketing_gap_automorphism_invariant": mapped_gap == gap,
        "all_pass": (
            gap > 0
            and associator_gap > 0
            and chirality_gap > 0
            and automorphism_exact
            and mapped_gap == gap
        ),
        "claim_ceiling": "exact bracket, chirality, and octonion basis-automorphism witnesses only",
    }
    return result


def run_all() -> dict[str, Any]:
    spinor = spinor_memory_report()
    spinor["all_pass"] = (
        spinor["spinor_lift_retains_density_erased_loop_parity"]
        and spinor["sheet_selective_retention"]
    )
    hopf = division_ladder_report()
    octonion = octonion_network_report()
    return {
        "schema": "ratchet.pack182.finite-algebra.v1",
        "spinor_memory": spinor,
        "division_hopf_ladder": hopf,
        "octonion_network": octonion,
        "all_pass": spinor["all_pass"] and hopf["all_pass"] and octonion["all_pass"],
        "numpy_imported_or_executed": False,
        "claim_ceiling": "finite exact/analytic source-mathematics replay; no carrier or physics admission",
    }


if __name__ == "__main__":
    import json

    from common import encode

    print(json.dumps(encode(run_all()), indent=2, sort_keys=True))
