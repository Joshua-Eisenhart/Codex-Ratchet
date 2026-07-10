#!/usr/bin/env python3
"""Independent exact-rational implementation of the local J3(O) formulas."""

from __future__ import annotations

from fractions import Fraction
from typing import Iterable, Sequence


Q = Fraction
Oct = tuple[Q, ...]
Albert = tuple[Q, ...]
Matrix = tuple[tuple[Oct, ...], ...]

FANO = (
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
)


def q(value: str | int | Q) -> Q:
    return value if isinstance(value, Q) else Q(value)


def qstr(value: Q) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def qlist(values: Iterable[Q]) -> list[str]:
    return [qstr(value) for value in values]


def parse_qlist(values: Sequence[str]) -> Albert:
    return tuple(q(value) for value in values)


def _product_table() -> dict[tuple[int, int], tuple[int, int]]:
    table: dict[tuple[int, int], tuple[int, int]] = {}
    for index in range(8):
        table[(0, index)] = (1, index)
        table[(index, 0)] = (1, index)
    for index in range(1, 8):
        table[(index, index)] = (-1, 0)
    for i, j, k in FANO:
        for a, b, c, sign in (
            (i, j, k, 1),
            (j, k, i, 1),
            (k, i, j, 1),
            (j, i, k, -1),
            (k, j, i, -1),
            (i, k, j, -1),
        ):
            table[(a, b)] = (sign, c)
    return table


OCT_PRODUCT = _product_table()
OCT_ZERO: Oct = (Q(0),) * 8


def oct_add(left: Oct, right: Oct) -> Oct:
    return tuple(a + b for a, b in zip(left, right))


def oct_scale(value: Oct, scalar: Q) -> Oct:
    return tuple(scalar * component for component in value)


def oct_conjugate(value: Oct) -> Oct:
    return (value[0],) + tuple(-component for component in value[1:])


def oct_multiply(left: Oct, right: Oct, *, corrupt: bool = False) -> Oct:
    out = [Q(0) for _ in range(8)]
    for i, left_value in enumerate(left):
        if left_value == 0:
            continue
        for j, right_value in enumerate(right):
            if right_value == 0:
                continue
            sign, target = OCT_PRODUCT[(i, j)]
            if corrupt and (i, j) == (1, 2):
                sign = -sign
            out[target] += sign * left_value * right_value
    return tuple(out)


def oct_norm2(value: Oct) -> Q:
    return sum((component * component for component in value), Q(0))


def from_coords(values: Sequence[Q]) -> Matrix:
    if len(values) != 27:
        raise ValueError(f"expected 27 Albert coordinates, got {len(values)}")
    coords = tuple(q(value) for value in values)
    diagonal = coords[:3]
    x01 = coords[3:11]
    x02 = coords[11:19]
    x12 = coords[19:27]

    def scalar(value: Q) -> Oct:
        return (value,) + (Q(0),) * 7

    return (
        (scalar(diagonal[0]), x01, x02),
        (oct_conjugate(x01), scalar(diagonal[1]), x12),
        (oct_conjugate(x02), oct_conjugate(x12), scalar(diagonal[2])),
    )


def to_coords(matrix: Matrix) -> Albert:
    return (
        matrix[0][0][0],
        matrix[1][1][0],
        matrix[2][2][0],
        *matrix[0][1],
        *matrix[0][2],
        *matrix[1][2],
    )


def matrix_add(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(oct_add(left[i][j], right[i][j]) for j in range(3))
        for i in range(3)
    )


def matrix_scale(value: Matrix, scalar: Q) -> Matrix:
    return tuple(
        tuple(oct_scale(value[i][j], scalar) for j in range(3))
        for i in range(3)
    )


def matrix_multiply(left: Matrix, right: Matrix, *, corrupt: bool = False) -> Matrix:
    rows: list[tuple[Oct, ...]] = []
    for i in range(3):
        row: list[Oct] = []
        for k in range(3):
            value = OCT_ZERO
            for j in range(3):
                value = oct_add(value, oct_multiply(left[i][j], right[j][k], corrupt=corrupt))
            row.append(value)
        rows.append(tuple(row))
    return tuple(rows)


def jordan(left: Albert, right: Albert, *, corrupt: bool = False) -> Albert:
    left_matrix = from_coords(left)
    right_matrix = from_coords(right)
    symmetrized = matrix_add(
        matrix_multiply(left_matrix, right_matrix, corrupt=corrupt),
        matrix_multiply(right_matrix, left_matrix, corrupt=corrupt),
    )
    return to_coords(matrix_scale(symmetrized, Q(1, 2)))


def add(left: Albert, right: Albert) -> Albert:
    return tuple(a + b for a, b in zip(left, right))


def subtract(left: Albert, right: Albert) -> Albert:
    return tuple(a - b for a, b in zip(left, right))


def scale(value: Albert, scalar: Q) -> Albert:
    return tuple(scalar * component for component in value)


def zero() -> Albert:
    return (Q(0),) * 27


def unit() -> Albert:
    return (Q(1), Q(1), Q(1)) + (Q(0),) * 24


def trace(value: Albert) -> Q:
    return value[0] + value[1] + value[2]


def sigma2(value: Albert) -> Q:
    d0, d1, d2 = value[:3]
    x01, x02, x12 = value[3:11], value[11:19], value[19:27]
    return d0 * d1 + d0 * d2 + d1 * d2 - oct_norm2(x01) - oct_norm2(x02) - oct_norm2(x12)


def determinant(value: Albert, *, corrupt: bool = False) -> Q:
    d0, d1, d2 = value[:3]
    x01, x02, x12 = value[3:11], value[11:19], value[19:27]
    triple = oct_multiply(
        oct_multiply(x01, x12, corrupt=corrupt),
        oct_conjugate(x02),
        corrupt=corrupt,
    )[0]
    return (
        d0 * d1 * d2
        + 2 * triple
        - d0 * oct_norm2(x12)
        - d1 * oct_norm2(x02)
        - d2 * oct_norm2(x01)
    )


def minimal_polynomial(value: Albert, *, corrupt: bool = False) -> tuple[Q, Q, Q, Q]:
    return (-determinant(value, corrupt=corrupt), sigma2(value), -trace(value), Q(1))


def quadratic(left: Albert, right: Albert, *, corrupt: bool = False) -> Albert:
    left_squared = jordan(left, left, corrupt=corrupt)
    nested = jordan(left, jordan(left, right, corrupt=corrupt), corrupt=corrupt)
    return subtract(scale(nested, Q(2)), jordan(left_squared, right, corrupt=corrupt))


def polynomial_value(coefficients: Sequence[Q], value: Albert, *, corrupt: bool = False) -> Albert:
    result = zero()
    power = unit()
    for coefficient in coefficients:
        result = add(result, scale(power, coefficient))
        power = jordan(power, value, corrupt=corrupt)
    return result


def seeded_vectors(seed: int) -> tuple[Albert, Albert, Albert]:
    state = seed
    denominators = (1, 2, 3, 5, 7)

    def next_state() -> int:
        nonlocal state
        state = (1103515245 * state + 12345) % 2147483648
        return state

    def next_rational() -> Q:
        numerator = next_state() % 9 - 4
        denominator = denominators[next_state() % 5]
        return Q(numerator, denominator)

    vectors = tuple(tuple(next_rational() for _ in range(27)) for _ in range(3))
    return vectors  # type: ignore[return-value]


def kill_vectors() -> tuple[Albert, Albert, Albert]:
    left = [Q(0) for _ in range(27)]
    right = [Q(0) for _ in range(27)]
    probe = [Q(0) for _ in range(27)]
    left[4] = Q(1)   # x01 = local e1
    right[21] = Q(1)  # x12 = local e2
    probe[0] = Q(1)
    return tuple(left), tuple(right), tuple(probe)
