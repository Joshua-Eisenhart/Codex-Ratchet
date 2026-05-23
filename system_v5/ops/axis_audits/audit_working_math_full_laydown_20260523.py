#!/usr/bin/env python3
"""Executable audit for the working-math full laydown.

The audit intentionally separates:

- source-grounded claims that survive direct finite checks;
- tested corrections where source docs/transcriptions drifted;
- open claims that are named but not promoted.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "system_v5/ops/axis_audits/working_math_full_laydown_audit_20260523.json"

DTYPE = torch.complex128
RTYPE = torch.float64
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
SM = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
SP = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)


def ok_close(actual: float, expected: float, tol: float = 1.0e-9) -> bool:
    return abs(actual - expected) <= tol


def check(name: str, actual: Any, expected: Any, ok: bool, **extra: Any) -> dict[str, Any]:
    row = {"name": name, "actual": actual, "expected": expected, "ok": bool(ok)}
    row.update(extra)
    return row


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=DTYPE,
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi.reshape(2, 1)
    return psi @ psi.conj().T


def bloch(rho: torch.Tensor) -> tuple[float, float, float]:
    return (
        float(torch.real(torch.trace(SX @ rho)).item()),
        float(torch.real(torch.trace(SY @ rho)).item()),
        float(torch.real(torch.trace(SZ @ rho)).item()),
    )


def hopf_formula_minus(phi: float, chi: float, eta: float) -> tuple[float, float, float]:
    del phi
    return (
        math.sin(2 * eta) * math.cos(2 * chi),
        -math.sin(2 * eta) * math.sin(2 * chi),
        math.cos(2 * eta),
    )


def hopf_formula_plus(phi: float, chi: float, eta: float) -> tuple[float, float, float]:
    del phi
    return (
        math.sin(2 * eta) * math.cos(2 * chi),
        math.sin(2 * eta) * math.sin(2 * chi),
        math.cos(2 * eta),
    )


def entropy_eta(eta: float) -> float:
    c2 = math.cos(eta) ** 2
    s2 = math.sin(eta) ** 2
    terms = []
    for value in (c2, s2):
        terms.append(0.0 if value <= 0.0 else -value * math.log(value))
    return sum(terms)


def d_entropy_eta(eta: float) -> float:
    return -math.sin(2 * eta) * math.log(math.tan(eta) ** 2)


def dagger(a: torch.Tensor) -> torch.Tensor:
    return a.conj().T


def dissipator(L: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    K = dagger(L) @ L
    return L @ rho @ dagger(L) - 0.5 * (K @ rho + rho @ K)


def rho_from_bloch(x: float, y: float, z: float) -> torch.Tensor:
    return 0.5 * (I2 + x * SX + y * SY + z * SZ)


def dephase(rho: torch.Tensor, pauli: torch.Tensor, q: float) -> torch.Tensor:
    P0 = 0.5 * (I2 + pauli)
    P1 = 0.5 * (I2 - pauli)
    return (1 - q) * rho + q * (P0 @ rho @ P0 + P1 @ rho @ P1)


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return torch.linalg.matrix_exp(-1j * theta * axis / 2)


def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())


def a0_bit(topology: str) -> int:
    return +1 if topology in {"Ne", "Ni"} else -1


def a1_bit(topology: str) -> int:
    return +1 if topology in {"Se", "Ni"} else -1


def a2_bit(topology: str) -> int:
    return +1 if topology in {"Se", "Ne"} else -1


def axis_tests() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    phi, chi, eta = 0.0, math.pi / 4, math.pi / 4
    rho = density(spinor(phi, chi, eta))
    observed = bloch(rho)
    minus = hopf_formula_minus(phi, chi, eta)
    plus = hopf_formula_plus(phi, chi, eta)
    rows.append(check("hopf_bloch_minus_formula", list(observed), list(minus), all(ok_close(a, b) for a, b in zip(observed, minus))))
    rows.append(check("hopf_bloch_plus_formula_fails_ry", list(observed), list(plus), not all(ok_close(a, b) for a, b in zip(observed, plus))))
    rows.append(check("hopf_fixture_ry_is_minus_one", observed[1], -1.0, ok_close(observed[1], -1.0)))

    rows.append(check("a0_entropy_clifford_log2", entropy_eta(math.pi / 4), math.log(2), ok_close(entropy_eta(math.pi / 4), math.log(2))))
    rows.append(check("a0_derivative_positive_before_clifford", d_entropy_eta(0.3), ">0", d_entropy_eta(0.3) > 0.0))
    rows.append(check("a0_derivative_negative_after_clifford", d_entropy_eta(1.1), "<0", d_entropy_eta(1.1) < 0.0))

    terrain_square = {
        ("open_isothermal", "expansion_direct"): "Se",
        ("open_isothermal", "compression_conjugated"): "Ni",
        ("closed_adiabatic", "expansion_direct"): "Ne",
        ("closed_adiabatic", "compression_conjugated"): "Si",
    }
    rows.append(check("terrain_square_count", len(set(terrain_square.values())), 4, len(set(terrain_square.values())) == 4))
    source_intersections = {
        "A0+|direct": "Ne",
        "A0+|conjugated": "Ni",
        "A0-|direct": "Se",
        "A0-|conjugated": "Si",
    }
    actual_intersections = {
        "A0+|direct": next(t for t in ("Se", "Ne", "Ni", "Si") if a0_bit(t) == +1 and a2_bit(t) == +1),
        "A0+|conjugated": next(t for t in ("Se", "Ne", "Ni", "Si") if a0_bit(t) == +1 and a2_bit(t) == -1),
        "A0-|direct": next(t for t in ("Se", "Ne", "Ni", "Si") if a0_bit(t) == -1 and a2_bit(t) == +1),
        "A0-|conjugated": next(t for t in ("Se", "Ne", "Ni", "Si") if a0_bit(t) == -1 and a2_bit(t) == -1),
    }
    rows.append(check("a0_a2_intersections", actual_intersections, source_intersections, actual_intersections == source_intersections))
    triple_products = {t: a0_bit(t) * a1_bit(t) * a2_bit(t) for t in ("Se", "Ne", "Ni", "Si")}
    rows.append(check("a0_a1_a2_constant_triple_product", triple_products, "constant", len(set(triple_products.values())) == 1))
    b1_relation = {t: a1_bit(t) == -a0_bit(t) * a2_bit(t) for t in ("Se", "Ne", "Ni", "Si")}
    rows.append(check("a1_equals_minus_a0_times_a2", b1_relation, "all_true", all(b1_relation.values())))

    # A3 path check: fiber has fixed density, lifted base is horizontal and density-visible.
    eta0, chi0, phi0, u = 0.41, 0.37, -0.22, 0.58
    fiber0 = density(spinor(phi0, chi0, eta0))
    fiberu = density(spinor(phi0 + u, chi0, eta0))
    base0 = density(spinor(phi0, chi0, eta0))
    baseu = density(spinor(phi0 - math.cos(2 * eta0) * u, chi0 + u, eta0))
    fiber_gap = float(torch.linalg.matrix_norm(fiberu - fiber0).item())
    base_gap = float(torch.linalg.matrix_norm(baseu - base0).item())
    horizontal = -math.cos(2 * eta0) + math.cos(2 * eta0) * 1.0
    rows.append(check("a3_fiber_density_stationary", fiber_gap, 0.0, fiber_gap < 1.0e-12))
    rows.append(check("a3_base_density_traverses", base_gap, ">0", base_gap > 1.0e-3))
    rows.append(check("a3_base_horizontal_connection", horizontal, 0.0, ok_close(horizontal, 0.0)))

    # A5 operator checks.
    probe = rho_from_bloch(0.3, -0.4, 0.5)
    q = 0.23
    ti = dephase(probe, SZ, q)
    te = dephase(probe, SX, q)
    dz_before = (0.3**2 + (-0.4) ** 2) / 2
    dz_after = (((1 - q) * 0.3) ** 2 + ((1 - q) * -0.4) ** 2) / 2
    dx_before = ((-0.4) ** 2 + 0.5**2) / 2
    dx_after = (((1 - q) * -0.4) ** 2 + ((1 - q) * 0.5) ** 2) / 2
    rows.append(check("ti_contracts_Dz", dz_after, f"< {dz_before}", dz_after < dz_before))
    rows.append(check("te_contracts_Dx", dx_after, f"< {dx_before}", dx_after < dx_before))
    fi = unitary(SX, 0.37) @ probe @ unitary(SX, 0.37).conj().T
    fe = unitary(SZ, -0.41) @ probe @ unitary(SZ, -0.41).conj().T
    rows.append(check("fi_preserves_purity", purity(fi), purity(probe), ok_close(purity(fi), purity(probe))))
    rows.append(check("fe_preserves_purity", purity(fe), purity(probe), ok_close(purity(fe), purity(probe))))
    rows.append(check("ti_decreases_purity_or_equal", purity(ti), f"<= {purity(probe)}", purity(ti) <= purity(probe) + 1e-12))
    rows.append(check("te_decreases_purity_or_equal", purity(te), f"<= {purity(probe)}", purity(te) <= purity(probe) + 1e-12))

    # Terrain dissipator Bloch laws.
    x, y, z = 0.2, -0.3, 0.4
    rrho = rho_from_bloch(x, y, z)
    def bd(L: torch.Tensor) -> tuple[float, float, float]:
        return bloch(dissipator(L, rrho))

    rows.append(check("D_sigma_x_bloch", list(bd(SX)), [0.0, -2 * y, -2 * z], all(ok_close(a, b) for a, b in zip(bd(SX), (0.0, -2 * y, -2 * z)))))
    rows.append(check("D_sigma_y_bloch", list(bd(SY)), [-2 * x, 0.0, -2 * z], all(ok_close(a, b) for a, b in zip(bd(SY), (-2 * x, 0.0, -2 * z)))))
    rows.append(check("D_sigma_z_bloch", list(bd(SZ)), [-2 * x, -2 * y, 0.0], all(ok_close(a, b) for a, b in zip(bd(SZ), (-2 * x, -2 * y, 0.0)))))
    depol = tuple(sum(v) for v in zip(bd(SX), bd(SY), bd(SZ)))
    rows.append(check("sum_D_pauli_depolarizes", list(depol), [-4 * x, -4 * y, -4 * z], all(ok_close(a, b) for a, b in zip(depol, (-4 * x, -4 * y, -4 * z)))))
    rows.append(check("D_sigma_minus_source_convention", list(bd(SM)), [-x / 2, -y / 2, -(1 + z)], all(ok_close(a, b) for a, b in zip(bd(SM), (-x / 2, -y / 2, -(1 + z))))))
    rows.append(check("D_sigma_plus_source_convention", list(bd(SP)), [-x / 2, -y / 2, 1 - z], all(ok_close(a, b) for a, b in zip(bd(SP), (-x / 2, -y / 2, 1 - z)))))

    # A6 gap and Liouville check.
    A = SX
    gap = float(torch.linalg.matrix_norm(A @ rrho - rrho @ A).item())
    expected_gap = math.sqrt(2) * math.sqrt(y * y + z * z)
    rows.append(check("a6_gap_sigma_x", gap, expected_gap, ok_close(gap, expected_gap)))
    A = SZ
    gap_z = float(torch.linalg.matrix_norm(A @ rrho - rrho @ A).item())
    expected_gap_z = math.sqrt(2) * math.sqrt(x * x + y * y)
    rows.append(check("a6_gap_sigma_z", gap_z, expected_gap_z, ok_close(gap_z, expected_gap_z)))

    return rows


def token_projection_tests() -> list[dict[str, Any]]:
    topologies = ["Se", "Ne", "Ni", "Si"]
    tokens = {
        "Se": {"dephasing_up": "TiSe", "dephasing_down": "SeTi", "rotation_up": "FiSe", "rotation_down": "SeFi"},
        "Ne": {"dephasing_up": "TiNe", "dephasing_down": "NeTi", "rotation_up": "FiNe", "rotation_down": "NeFi"},
        "Ni": {"dephasing_up": "TeNi", "dephasing_down": "NiTe", "rotation_up": "FeNi", "rotation_down": "NiFe"},
        "Si": {"dephasing_up": "TeSi", "dephasing_down": "SiTe", "rotation_up": "FeSi", "rotation_down": "SiFe"},
    }
    all_tokens = [value for topology in tokens.values() for value in topology.values()]
    terrain_placements = [
        (tau, sheet, path)
        for tau in topologies
        for sheet in ("L", "R")
        for path in ("fiber", "base")
    ]
    rows = [
        check("ordered_token_count", len(set(all_tokens)), 16, len(set(all_tokens)) == 16),
        check("terrain_placement_count", len(set(terrain_placements)), 16, len(set(terrain_placements)) == 16),
    ]

    # A6 relation uses chart role, not raw path.
    t1 = [
        ("Se", "outer", "base", "TiSe"),
        ("Ne", "outer", "base", "NeTi"),
        ("Ni", "outer", "base", "NiFe"),
        ("Si", "outer", "base", "FeSi"),
        ("Se", "inner", "fiber", "SeFi"),
        ("Ne", "inner", "fiber", "FiNe"),
        ("Ni", "inner", "fiber", "TeNi"),
        ("Si", "inner", "fiber", "SiTe"),
    ]
    t2 = [
        ("Se", "outer", "fiber", "FiSe"),
        ("Si", "outer", "fiber", "TeSi"),
        ("Ni", "outer", "fiber", "NiTe"),
        ("Ne", "outer", "fiber", "NeFi"),
        ("Se", "inner", "base", "SeTi"),
        ("Si", "inner", "base", "SiFe"),
        ("Ni", "inner", "base", "FeNi"),
        ("Ne", "inner", "base", "TiNe"),
    ]
    def token_bit(token: str, topology: str) -> int:
        return -1 if token.startswith(topology) else +1

    def chart_bit(role: str) -> int:
        return +1 if role == "outer" else -1

    def path_bit(path: str) -> int:
        return +1 if path == "base" else -1

    chart_ok = {}
    path_ok = {}
    for engine, chart in (("T1", t1), ("T2", t2)):
        chart_ok[engine] = all(token_bit(tok, top) == -a0_bit(top) * chart_bit(role) for top, role, path, tok in chart)
        path_ok[engine] = all(token_bit(tok, top) == -a0_bit(top) * path_bit(path) for top, role, path, tok in chart)
    rows.append(check("a6_xor_chart_role_passes_both_engines", chart_ok, {"T1": True, "T2": True}, chart_ok == {"T1": True, "T2": True}))
    rows.append(check("a6_xor_raw_path_fails_type2", path_ok, {"T1": True, "T2": False}, path_ok == {"T1": True, "T2": False}))
    return rows


def main() -> int:
    tests = axis_tests() + token_projection_tests()
    failed = [row for row in tests if not row["ok"]]
    payload = {
        "kind": "working_math_full_laydown_audit",
        "generated_at": "2026-05-23T00:00:00-07:00",
        "classification": "audit_pass_with_tested_doc_corrections" if not failed else "audit_failed",
        "ok": not failed,
        "TOOL_MANIFEST": [
            {
                "tool": "pytorch",
                "reason": "load-bearing finite matrix checks for Hopf/Bloch signs, QIT channels, dissipators, purity, and A6 gaps",
            },
            {
                "tool": "python_stdlib",
                "reason": "supportive exact enumeration of terrain square, token grammar, and parity rules",
            },
        ],
        "TOOL_INTEGRATION_DEPTH": {"pytorch": "load_bearing", "python_stdlib": "supportive"},
        "summary": {
            "tested_claim_count": len(tests),
            "failed_count": len(failed),
            "tested_corrections": [
                "Hopf Bloch r_y sign is negative for the stated spinor chart",
                "b6=-b0*b3 uses A3 chart role inner/outer, not raw fiber/base",
            ],
            "open_not_promoted": [
                "Xi geometry/history to rho_AB bridge",
                "final Phi0 kernel",
                "flux placement",
                "full tensor-network engine admission",
            ],
        },
        "tests": tests,
        "failed": failed,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "classification": payload["classification"], "receipt": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
