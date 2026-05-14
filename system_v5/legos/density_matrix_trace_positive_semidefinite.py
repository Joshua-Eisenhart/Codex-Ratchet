#!/usr/bin/env python3
"""Finite density matrix trace, Hermitian, and positive-semidefinite lego."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "density_matrix_trace_positive_semidefinite_results.json"

NAME = "density_matrix_trace_positive_semidefinite"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite density-matrix validity lego only: verifies Hermitian, trace-one, "
    "positive-semidefinite constraints and nearby invalid controls. It does "
    "not admit a manifold, layer order, physical bridge, or target-system claim."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex matrix algebra and eigenvalue checks",
    }
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}


def density_validity(matrix: np.ndarray, tol: float = 1e-10) -> dict[str, Any]:
    hermitian_error = float(np.linalg.norm(matrix - matrix.conj().T))
    trace_value = complex(np.trace(matrix))
    hermitian_part = (matrix + matrix.conj().T) / 2.0
    eigenvalues = np.linalg.eigvalsh(hermitian_part)
    min_eigenvalue = float(np.min(eigenvalues))
    return {
        "hermitian_error": hermitian_error,
        "trace_real": trace_value.real,
        "trace_imag": trace_value.imag,
        "min_eigenvalue": min_eigenvalue,
        "eigenvalues": [float(value) for value in eigenvalues],
        "pass": (
            hermitian_error < tol
            and abs(trace_value.real - 1.0) < tol
            and abs(trace_value.imag) < tol
            and min_eigenvalue >= -tol
        ),
    }


def main() -> dict[str, Any]:
    started = time.time()
    psi = np.array([1.0 + 0.0j, 1.0j], dtype=np.complex128) / np.sqrt(2.0)
    pure_density = np.outer(psi, psi.conj())
    mixed_density = np.diag([0.25, 0.75]).astype(np.complex128)
    non_hermitian = np.array([[0.5, 0.5], [0.0, 0.5]], dtype=np.complex128)
    wrong_trace = np.diag([0.5, 0.75]).astype(np.complex128)
    negative_eigenvalue = np.diag([1.2, -0.2]).astype(np.complex128)

    positive = {
        "pure_state_density_is_valid": density_validity(pure_density),
        "mixed_diagonal_density_is_valid": density_validity(mixed_density),
    }
    graveyards = {
        "non_hermitian_matrix_rejected": {
            "validity": density_validity(non_hermitian),
            "pass": not density_validity(non_hermitian)["pass"],
        },
        "wrong_trace_matrix_rejected": {
            "validity": density_validity(wrong_trace),
            "pass": not density_validity(wrong_trace)["pass"],
        },
        "negative_eigenvalue_matrix_rejected": {
            "validity": density_validity(negative_eigenvalue),
            "pass": not density_validity(negative_eigenvalue)["pass"],
        },
    }
    boundary = {
        "zero_eigenvalue_boundary_admitted": {
            "validity": density_validity(np.diag([1.0, 0.0]).astype(np.complex128)),
            "pass": density_validity(np.diag([1.0, 0.0]).astype(np.complex128))["pass"],
        }
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "observable": [
            "Hermitian error",
            "trace real and imaginary parts",
            "minimum eigenvalue",
        ],
        "predicate": "finite complex matrix is Hermitian, trace one, and positive semidefinite",
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": 3, "passed": sum(1 for row in graveyards.values() if row["pass"])},
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
