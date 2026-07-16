#!/usr/bin/env python3
"""Cross-validate the Julia-owned octonion convention without claiming a Julia run."""

from __future__ import annotations

import argparse
import os
import json
import math
import random
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT.parent
ARTIFACTS = ROOT / "artifacts"
TABLE = ARTIFACTS / "octonion_multiplication_table.tsv"
FANO = ((1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5))


def mul_basis(i: int, j: int) -> tuple[int, int]:
    if i == 0:
        return 1, j
    if j == 0:
        return 1, i
    if i == j:
        return -1, 0
    for a, b, c in FANO:
        for u, v, w in ((a, b, c), (b, c, a), (c, a, b)):
            if (i, j) == (u, v):
                return 1, w
            if (i, j) == (v, u):
                return -1, w
    raise ValueError((i, j))


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b)]


def sub(a: list[float], b: list[float]) -> list[float]:
    return [x - y for x, y in zip(a, b)]


def mul(a: list[float], b: list[float]) -> list[float]:
    out = [0.0] * 8
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            sign, k = mul_basis(i, j)
            out[k] += sign * x * y
    return out


def norm(a: list[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def associator(a: list[float], b: list[float], c: list[float]) -> list[float]:
    return sub(mul(mul(a, b), c), mul(a, mul(b, c)))


def bracket(a: list[float], b: list[float]) -> list[float]:
    return sub(mul(a, b), mul(b, a))


def jacobi(a: list[float], b: list[float], c: list[float]) -> list[float]:
    return add(add(bracket(bracket(a, b), c), bracket(bracket(b, c), a)), bracket(bracket(c, a), b))


def basis(i: int) -> list[float]:
    out = [0.0] * 8
    out[i] = 1.0
    return out


def write_table() -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    rows = ["left\tright\tsign\tresult"]
    for i in range(8):
        for j in range(8):
            sign, k = mul_basis(i, j)
            rows.append(f"e{i}\te{j}\t{sign}\te{k}")
    TABLE.write_text("\n".join(rows) + "\n", encoding="utf-8")


def read_table() -> dict[tuple[int, int], tuple[int, int]]:
    rows = TABLE.read_text(encoding="utf-8").splitlines()
    if not rows or rows[0] != "left\tright\tsign\tresult":
        raise ValueError("bad multiplication-table header")
    out = {}
    for row in rows[1:]:
        left, right, sign, result = row.split("\t")
        out[(int(left[1:]), int(right[1:]))] = (int(sign), int(result[1:]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-julia", action="store_true", help="execute Julia export first when Julia is available")
    args = parser.parse_args()

    julia = shutil.which("julia") or (
        "/opt/homebrew/bin/julia" if os.path.exists("/opt/homebrew/bin/julia") else None
    )
    # 2026-07-11: auto-detect the runtime — honesty is environment-relative. When Julia
    # exists, the executed replay is the honest state; when absent, the blocked status is.
    # Only trigger the export when no executed receipt exists yet: the receipt carries a
    # timestamp, so an unconditional replay would rewrite bytes on every validate call and
    # permanently break manifest stability.
    _receipt_path = ROOT / "artifacts" / "julia_export_receipt.toml"
    _already_executed = _receipt_path.exists() and "JULIA_EXPORT_EXECUTED" in _receipt_path.read_text()
    if julia and not args.run_julia and not _already_executed:
        args.run_julia = True
    elif _already_executed and not args.run_julia:
        julia = julia  # validate existing artifacts without rewriting them
    julia_run = None
    if args.run_julia:
        if not julia:
            print("FAIL --run-julia requested but Julia runtime is absent")
            return 1
        completed = subprocess.run(
            [julia, f"--project={ROOT}", str(ROOT / "scripts" / "export_canon.jl")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        julia_run = {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
        if completed.returncode:
            print(completed.stderr or completed.stdout)
            return completed.returncode
    elif not TABLE.exists():
        write_table()

    table = read_table()
    table_exact = len(table) == 64 and all(table[(i, j)] == mul_basis(i, j) for i in range(8) for j in range(8))
    identity_exact = all(table[(0, i)] == (1, i) and table[(i, 0)] == (1, i) for i in range(8))
    imaginary_squares_exact = all(table[(i, i)] == (-1, 0) for i in range(1, 8))
    imaginary_anticommutation_exact = all(
        table[(i, j)] == (-table[(j, i)][0], table[(j, i)][1])
        for i in range(1, 8) for j in range(1, 8) if i != j
    )

    witness = associator(basis(1), basis(2), basis(4))
    witness_exact = witness == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]

    rng = random.Random(13107)
    max_norm_composition = 0.0
    max_left_alt = 0.0
    max_right_alt = 0.0
    max_malcev = 0.0
    max_jacobi = 0.0
    for _ in range(128):
        x = [rng.uniform(-1.0, 1.0) for _ in range(8)]
        y = [rng.uniform(-1.0, 1.0) for _ in range(8)]
        z = [rng.uniform(-1.0, 1.0) for _ in range(8)]
        max_norm_composition = max(max_norm_composition, abs(norm(mul(x, y)) - norm(x) * norm(y)))
        max_left_alt = max(max_left_alt, norm(associator(x, x, y)))
        max_right_alt = max(max_right_alt, norm(associator(y, x, x)))
        jxyz = jacobi(x, y, z)
        max_jacobi = max(max_jacobi, norm(jxyz))
        # Malcev identity: J(x,y,[x,z]) = [J(x,y,z),x]
        malcev = sub(jacobi(x, y, bracket(x, z)), bracket(jxyz, x))
        max_malcev = max(max_malcev, norm(malcev))

    receipt_path = BUNDLE / "sims_and_scripts" / "j3o_bloch_body_entropy_pawl_sim_results.json"
    source_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    source_fano = tuple(tuple(row) for row in source_receipt["octonion_verification"]["fano_cycles"])
    source_terms = source_receipt["octonion_verification"]["basis_associator_e1_e2_e4_terms"]
    receipt_crosscheck = source_fano == FANO and source_terms == [{"basis_index": 7, "coefficient": 2.0, "label": "e7"}]

    tolerance = 2e-12
    checks = {
        "multiplication_table_64_entries_exact": table_exact,
        "identity_exact": identity_exact,
        "imaginary_squares_minus_one_exact": imaginary_squares_exact,
        "imaginary_anticommutation_exact": imaginary_anticommutation_exact,
        "associator_e1_e2_e4_equals_2e7_exact": witness_exact,
        "norm_composition_seeded": max_norm_composition < tolerance,
        "left_alternativity_seeded": max_left_alt < tolerance,
        "right_alternativity_seeded": max_right_alt < tolerance,
        "malcev_identity_seeded": max_malcev < tolerance,
        "non_lie_jacobi_witness_present": max_jacobi > 1.0,
        "existing_science_receipt_same_fano_and_associator": receipt_crosscheck,
    }
    all_pass = all(checks.values())
    status = "JULIA_EXPORT_EXECUTED_AND_CROSS_VALIDATED" if julia_run is not None else "JULIA_SOURCE_AUTHORED__PYTHON_MIRROR_CROSS_VALIDATED__LOCAL_JULIA_REPLAY_BLOCKED_RUNTIME_ABSENT" if julia is None else "JULIA_SOURCE_AUTHORED__PYTHON_MIRROR_CROSS_VALIDATED__JULIA_REPLAY_NOT_REQUESTED" if not (ROOT / "artifacts" / "julia_export_receipt.toml").exists() or "JULIA_EXPORT_EXECUTED" not in (ROOT / "artifacts" / "julia_export_receipt.toml").read_text() else "JULIA_EXPORT_PREVIOUSLY_EXECUTED_ARTIFACTS_VALIDATED"
    receipt = {
        "schema": "ratchet.julia-canon-cross-validation.v1",
        "status": status,
        "source_owner": "julia_canon/src/ExceptionalAlgebraCanon.jl",
        "julia_runtime_path": julia,
        "julia_run": julia_run,
        "checks": checks,
        "metrics": {
            "max_norm_composition_residual_128": max_norm_composition,
            "max_left_alternativity_residual_128": max_left_alt,
            "max_right_alternativity_residual_128": max_right_alt,
            "max_malcev_identity_residual_128": max_malcev,
            "max_non_lie_jacobi_norm_128": max_jacobi,
            "associator_e1_e2_e4": witness,
        },
        "all_pass": all_pass,
        "ratchet_admission": False,
        "claim_ceiling": "Cross-validates the owned finite algebra convention. It does not prove Albert spectral results or admit the exceptional branch.",
    }
    (ARTIFACTS / "python_cross_validation_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if not all_pass:
        for name, passed in checks.items():
            if not passed:
                print(f"FAIL {name}")
        return 1
    print("PASS exceptional canon Python cross-validation")
    print(status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
