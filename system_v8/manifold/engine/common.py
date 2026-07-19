#!/usr/bin/env python3
"""Shared deterministic utilities for the Pack 182 finite mathematics."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable


def encode(value: Any) -> Any:
    if isinstance(value, complex):
        return {"re": value.real, "im": value.imag}
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator}
    if isinstance(value, tuple):
        return [encode(item) for item in value]
    if isinstance(value, list):
        return [encode(item) for item in value]
    if isinstance(value, set) or isinstance(value, frozenset):
        return [encode(item) for item in sorted(value)]
    if isinstance(value, dict):
        return {str(key): encode(item) for key, item in sorted(value.items(), key=lambda row: str(row[0]))}
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(encode(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return "sha256:" + hasher.hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    payload = f"blob {len(data)}\0".encode("ascii") + data
    return hashlib.sha1(payload).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(encode(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def max_abs_matrix(matrix: Iterable[Iterable[complex]]) -> float:
    return max((abs(value) for row in matrix for value in row), default=0.0)


def matrix_subtract(left: list[list[complex]], right: list[list[complex]]) -> list[list[complex]]:
    return [
        [left[row][column] - right[row][column] for column in range(len(left[row]))]
        for row in range(len(left))
    ]


def matrix_multiply(left: list[list[complex]], right: list[list[complex]]) -> list[list[complex]]:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("matrix dimensions do not compose")
    return [
        [sum(left[i][k] * right[k][j] for k in range(len(right))) for j in range(len(right[0]))]
        for i in range(len(left))
    ]


def matrix_dagger(matrix: list[list[complex]]) -> list[list[complex]]:
    return [[matrix[row][column].conjugate() for row in range(len(matrix))] for column in range(len(matrix[0]))]


def matrix_inverse(matrix: list[list[complex]], tolerance: float = 1e-13) -> list[list[complex]]:
    """Gauss-Jordan inverse with deterministic maximum-pivot selection."""
    size = len(matrix)
    if not size or any(len(row) != size for row in matrix):
        raise ValueError("inverse requires a nonempty square matrix")
    augmented = [
        [complex(value) for value in row]
        + [complex(int(i == j)) for j in range(size)]
        for i, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= tolerance:
            raise ValueError("matrix is singular at declared tolerance")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if abs(factor) <= tolerance:
                continue
            augmented[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]
    return [row[size:] for row in augmented]


def submatrix(matrix: list[list[complex]], rows: list[int], columns: list[int]) -> list[list[complex]]:
    return [[matrix[row][column] for column in columns] for row in rows]


def schur_complement(
    matrix: list[list[complex]],
    keep: list[int],
    eliminate: list[int],
) -> list[list[complex]]:
    if set(keep) & set(eliminate) or sorted(keep + eliminate) != list(range(len(matrix))):
        raise ValueError("keep/eliminate must partition the matrix")
    a = submatrix(matrix, keep, keep)
    if not eliminate:
        return a
    b = submatrix(matrix, keep, eliminate)
    c = submatrix(matrix, eliminate, keep)
    d = submatrix(matrix, eliminate, eliminate)
    correction = matrix_multiply(matrix_multiply(b, matrix_inverse(d)), c)
    return matrix_subtract(a, correction)


def trace(matrix: list[list[complex]]) -> complex:
    return sum(matrix[index][index] for index in range(len(matrix)))
