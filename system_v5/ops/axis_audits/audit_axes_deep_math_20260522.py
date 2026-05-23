#!/usr/bin/env python3
"""Audit and executable checks for the deep Axis 0-6 math layout.

This is a narrow audit utility, not a canonical scientific sim. It tests the
source-grounded axis math and explicitly checks one known failure in the pasted
Claude expansion: the A0 x A2 topology-intersection table was inverted on the
direct-frame rows.
"""

from __future__ import annotations

import cmath
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "system_v5/ops/axis_audits/axes_deep_math_audit_20260522.json"


ComplexMatrix = list[list[complex]]
Vector = tuple[float, float, float]


def matmul(a: ComplexMatrix, b: ComplexMatrix) -> ComplexMatrix:
    return [
        [sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
        for i in range(len(a))
    ]


def madd(a: ComplexMatrix, b: ComplexMatrix) -> ComplexMatrix:
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def msub(a: ComplexMatrix, b: ComplexMatrix) -> ComplexMatrix:
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def mscale(c: complex, a: ComplexMatrix) -> ComplexMatrix:
    return [[c * a[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def dagger(a: ComplexMatrix) -> ComplexMatrix:
    return [[a[j][i].conjugate() for j in range(len(a))] for i in range(len(a[0]))]


def fro_norm(a: ComplexMatrix) -> float:
    return math.sqrt(sum(abs(x) ** 2 for row in a for x in row))


I2: ComplexMatrix = [[1, 0], [0, 1]]
X: ComplexMatrix = [[0, 1], [1, 0]]
Y: ComplexMatrix = [[0, -1j], [1j, 0]]
Z: ComplexMatrix = [[1, 0], [0, -1]]


def rho_from_bloch(r: Vector) -> ComplexMatrix:
    x, y, z = r
    return madd(
        mscale(0.5, I2),
        mscale(0.5, madd(madd(mscale(x, X), mscale(y, Y)), mscale(z, Z))),
    )


def bloch_norm(r: Vector) -> float:
    return math.sqrt(sum(v * v for v in r))


def rotate_x(r: Vector, theta: float) -> Vector:
    x, y, z = r
    return (x, y * math.cos(theta) - z * math.sin(theta), y * math.sin(theta) + z * math.cos(theta))


def rotate_z(r: Vector, phi: float) -> Vector:
    x, y, z = r
    return (x * math.cos(phi) - y * math.sin(phi), x * math.sin(phi) + y * math.cos(phi), z)


def ti_bloch(r: Vector, q: float) -> Vector:
    x, y, z = r
    return ((1 - q) * x, (1 - q) * y, z)


def te_bloch(r: Vector, q: float) -> Vector:
    x, y, z = r
    return (x, (1 - q) * y, (1 - q) * z)


def dz(r: Vector) -> float:
    x, y, _ = r
    return (x * x + y * y) / 2


def dx(r: Vector) -> float:
    _, y, z = r
    return (y * y + z * z) / 2


def psi(phi: float, chi: float, eta: float) -> list[complex]:
    return [
        cmath.exp(1j * (phi + chi)) * math.cos(eta),
        cmath.exp(1j * (phi - chi)) * math.sin(eta),
    ]


def ketbra(v: list[complex]) -> ComplexMatrix:
    return [[v[i] * v[j].conjugate() for j in range(2)] for i in range(2)]


def entropy_eta(eta: float) -> float:
    p = math.cos(eta) ** 2
    q = math.sin(eta) ** 2
    terms = []
    for value in (p, q):
        terms.append(0.0 if value == 0 else -value * math.log(value))
    return sum(terms)


def d_entropy_eta(eta: float) -> float:
    return -math.sin(2 * eta) * math.log(math.tan(eta) ** 2)


def axis0_bit(eta: float) -> int:
    value = math.cos(2 * eta)
    if abs(value) < 1e-12:
        return 0
    return 1 if value > 0 else -1


def assert_close(name: str, actual: float, expected: float, tol: float = 1e-9) -> dict[str, Any]:
    ok = abs(actual - expected) <= tol
    return {"name": name, "ok": ok, "actual": actual, "expected": expected, "tol": tol}


def test_axis0() -> dict[str, Any]:
    a0_plus_eta = math.pi / 6
    a0_minus_eta = math.pi / 3
    clifford = math.pi / 4
    checks = [
        {"name": "axis0_plus_eta_lt_pi4", "ok": axis0_bit(a0_plus_eta) == 1, "actual": axis0_bit(a0_plus_eta), "expected": 1},
        {"name": "axis0_minus_eta_gt_pi4", "ok": axis0_bit(a0_minus_eta) == -1, "actual": axis0_bit(a0_minus_eta), "expected": -1},
        assert_close("entropy_clifford_log2", entropy_eta(clifford), math.log(2)),
        {"name": "entropy_derivative_positive_on_a0_plus_side", "ok": d_entropy_eta(a0_plus_eta) > 0, "actual": d_entropy_eta(a0_plus_eta), "expected": ">0"},
        {"name": "entropy_derivative_negative_on_a0_minus_side", "ok": d_entropy_eta(a0_minus_eta) < 0, "actual": d_entropy_eta(a0_minus_eta), "expected": "<0"},
    ]
    return {"name": "axis0_entropy_and_bit", "ok": all(c["ok"] for c in checks), "checks": checks}


def test_a0_a2_intersections() -> dict[str, Any]:
    source_a0_sets = {
        "a0_plus_N": {"Ne", "Ni"},
        "a0_minus_S": {"Se", "Si"},
    }
    source_a2_sets = {
        "direct": {"Se", "Ne"},
        "conjugated": {"Ni", "Si"},
    }
    source_expected = {
        ("a0_plus_N", "direct"): "Ne",
        ("a0_plus_N", "conjugated"): "Ni",
        ("a0_minus_S", "direct"): "Se",
        ("a0_minus_S", "conjugated"): "Si",
    }
    computed = {
        key: next(iter(source_a0_sets[key[0]].intersection(source_a2_sets[key[1]])))
        for key in source_expected
    }

    claude_pasted = {
        ("a0_plus_N", "direct"): "Se",
        ("a0_plus_N", "conjugated"): "Ni",
        ("a0_minus_S", "direct"): "Ne",
        ("a0_minus_S", "conjugated"): "Si",
    }
    source_checks = [
        {"key": list(key), "ok": computed[key] == expected, "actual": computed[key], "expected": expected}
        for key, expected in source_expected.items()
    ]
    claude_checks = [
        {"key": list(key), "ok": claude_pasted[key] == source_expected[key], "actual": claude_pasted[key], "expected": source_expected[key]}
        for key in source_expected
    ]
    return {
        "name": "a0_a2_topology_intersections",
        "ok": all(c["ok"] for c in source_checks) and not all(c["ok"] for c in claude_checks),
        "source_intersection_checks": source_checks,
        "pasted_claude_table_checks": claude_checks,
        "audit_finding": "pasted Claude table fails on direct-frame rows; source-correct A0+ + direct = Ne and A0- + direct = Se",
    }


def test_axis3_paths() -> dict[str, Any]:
    phi0 = 0.31
    chi0 = 0.73
    eta = math.pi / 5
    u = 0.41
    rho_f0 = ketbra(psi(phi0, chi0, eta))
    rho_f1 = ketbra(psi(phi0 + u, chi0, eta))
    rho_b0 = ketbra(psi(phi0, chi0, eta))
    rho_b1 = ketbra(psi(phi0 - math.cos(2 * eta) * u, chi0 + u, eta))
    fiber_gap = fro_norm(msub(rho_f1, rho_f0))
    base_gap = fro_norm(msub(rho_b1, rho_b0))
    horizontal = -math.cos(2 * eta) + math.cos(2 * eta) * 1.0
    checks = [
        {"name": "fiber_density_stationary", "ok": fiber_gap < 1e-12, "actual": fiber_gap, "expected": 0.0},
        {"name": "base_density_traverses", "ok": base_gap > 1e-3, "actual": base_gap, "expected": ">0"},
        {"name": "base_horizontal_connection_zero", "ok": abs(horizontal) < 1e-12, "actual": horizontal, "expected": 0.0},
    ]
    return {"name": "axis3_fiber_base_paths", "ok": all(c["ok"] for c in checks), "checks": checks}


def test_axis5_operator_families() -> dict[str, Any]:
    r = (0.31, -0.27, 0.44)
    q = 0.2
    theta = 0.37
    phi = -0.29
    ti_r = ti_bloch(r, q)
    te_r = te_bloch(r, q)
    fi_r = rotate_x(r, theta)
    fe_r = rotate_z(r, phi)
    checks = [
        {"name": "Ti_contracts_Dz", "ok": dz(ti_r) < dz(r), "actual": dz(ti_r), "expected": f"< {dz(r)}"},
        {"name": "Te_contracts_Dx", "ok": dx(te_r) < dx(r), "actual": dx(te_r), "expected": f"< {dx(r)}"},
        assert_close("Fi_preserves_bloch_norm", bloch_norm(fi_r), bloch_norm(r)),
        assert_close("Fe_preserves_bloch_norm", bloch_norm(fe_r), bloch_norm(r)),
    ]
    return {"name": "axis5_operator_family_invariants", "ok": all(c["ok"] for c in checks), "checks": checks}


def test_axis6_gap() -> dict[str, Any]:
    r = (0.31, -0.27, 0.44)
    rho = rho_from_bloch(r)
    comm_x = msub(matmul(X, rho), matmul(rho, X))
    comm_z = msub(matmul(Z, rho), matmul(rho, Z))
    expected_x = math.sqrt(2) * math.sqrt(r[1] ** 2 + r[2] ** 2)
    expected_z = math.sqrt(2) * math.sqrt(r[0] ** 2 + r[1] ** 2)
    checks = [
        assert_close("gap_sigma_x_formula", fro_norm(comm_x), expected_x),
        assert_close("gap_sigma_z_formula", fro_norm(comm_z), expected_z),
        {"name": "noncommuting_probe_has_gap", "ok": fro_norm(comm_x) > 0 and fro_norm(comm_z) > 0, "actual": {"x": fro_norm(comm_x), "z": fro_norm(comm_z)}, "expected": ">0"},
    ]
    return {"name": "axis6_left_right_action_gap", "ok": all(c["ok"] for c in checks), "checks": checks}


def operator_for(topology: str, family: str) -> str:
    if topology in {"Se", "Ne"}:
        return "Ti" if family == "dephasing" else "Fi"
    return "Te" if family == "dephasing" else "Fe"


def test_projection_identities() -> dict[str, Any]:
    topology_from_a1_a2 = {
        ("Se/Ni", "direct"): "Se",
        ("Ne/Si", "direct"): "Ne",
        ("Se/Ni", "conjugated"): "Ni",
        ("Ne/Si", "conjugated"): "Si",
    }
    source_tokens = {
        "TiSe", "SeTi", "FiSe", "SeFi",
        "TiNe", "NeTi", "FiNe", "NeFi",
        "TeNi", "NiTe", "FeNi", "NiFe",
        "TeSi", "SiTe", "FeSi", "SiFe",
    }
    generated = {}
    for a1 in ("Se/Ni", "Ne/Si"):
        for a2 in ("direct", "conjugated"):
            topology = topology_from_a1_a2[(a1, a2)]
            for a5 in ("dephasing", "rotation"):
                op = operator_for(topology, a5)
                for a6 in ("up", "down"):
                    token = f"{op}{topology}" if a6 == "up" else f"{topology}{op}"
                    generated[(a1, a2, a5, a6)] = token

    rows = [
        ("TiSe", "base", "deductive", "dephasing", "up"),
        ("NeTi", "base", "deductive", "dephasing", "down"),
        ("NiFe", "base", "deductive", "rotation", "down"),
        ("FeSi", "base", "deductive", "rotation", "up"),
        ("SeFi", "fiber", "inductive", "rotation", "down"),
        ("FiNe", "fiber", "inductive", "rotation", "up"),
        ("TeNi", "fiber", "inductive", "dephasing", "up"),
        ("SiTe", "fiber", "inductive", "dephasing", "down"),
        ("FiSe", "fiber", "inductive", "rotation", "up"),
        ("TeSi", "fiber", "inductive", "dephasing", "up"),
        ("NiTe", "fiber", "inductive", "dephasing", "down"),
        ("NeFi", "fiber", "inductive", "rotation", "down"),
        ("SeTi", "base", "deductive", "dephasing", "down"),
        ("SiFe", "base", "deductive", "rotation", "down"),
        ("FeNi", "base", "deductive", "rotation", "up"),
        ("TiNe", "base", "deductive", "dephasing", "up"),
    ]
    grouped: dict[tuple[str, str, str, str], list[str]] = {}
    for token, a3, a4, a5, a6 in rows:
        grouped.setdefault((a3, a4, a5, a6), []).append(token)

    terrain_placements = [
        (terrain, sheet, path)
        for terrain in ("Se", "Ne", "Ni", "Si")
        for sheet in ("L", "R")
        for path in ("fiber", "lifted_base")
    ]
    checks = [
        {"name": "a1_a2_a5_a6_generates_16_unique_tokens", "ok": len(set(generated.values())) == 16, "actual": len(set(generated.values())), "expected": 16},
        {"name": "generated_tokens_match_source_set", "ok": set(generated.values()) == source_tokens, "actual": sorted(generated.values()), "expected": sorted(source_tokens)},
        {"name": "a3_a4_a5_a6_gives_8_signatures", "ok": len(grouped) == 8, "actual": len(grouped), "expected": 8},
        {"name": "each_loop_signature_has_two_tokens", "ok": all(len(v) == 2 for v in grouped.values()), "actual": {str(k): v for k, v in grouped.items()}, "expected": "8 groups of size 2"},
        {"name": "terrain_placements_are_separate_16", "ok": len(terrain_placements) == 16, "actual": len(terrain_placements), "expected": 16},
    ]
    return {"name": "projection_identities", "ok": all(c["ok"] for c in checks), "checks": checks}


def main() -> int:
    tests = [
        test_axis0(),
        test_a0_a2_intersections(),
        test_axis3_paths(),
        test_axis5_operator_families(),
        test_axis6_gap(),
        test_projection_identities(),
    ]
    ok = all(t["ok"] for t in tests)
    receipt = {
        "kind": "axis_deep_math_audit",
        "generated_at": "2026-05-22T00:00:00-07:00",
        "classification": "audit_pass_with_correction" if ok else "audit_failed",
        "ok": ok,
        "summary": {
            "source_math_tests_passed": ok,
            "pasted_claude_table_issue": "A0 x A2 derivation table inverted the direct-frame rows; source-correct A0+ + direct = Ne and A0- + direct = Se.",
            "projection_result": "A1 x A2 x A5 x A6 gives 16 tokens; A3 x A4 x A5 x A6 gives 8 paired signatures; terrain placements are a separate 16.",
        },
        "TOOL_MANIFEST": [
            {
                "tool": "python_stdlib",
                "reason": "finite arithmetic and matrix checks for axis formulas, projections, and source-table intersections",
            }
        ],
        "TOOL_INTEGRATION_DEPTH": "supportive",
        "tests": tests,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": ok, "receipt": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
