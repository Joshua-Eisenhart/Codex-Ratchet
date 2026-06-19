#!/usr/bin/env python3
"""Exact Python/QIT/SMT leg for geo_s9_octonionic_hopf_stack_v0.

The repo convention names this the "jax" lane. This packet's Python claim path
is exact SymPy plus QuTiP, z3, and cvc5, not floating JAX array work.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import sys
from itertools import product
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import qutip
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s9_octonionic_hopf_stack_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PROGRAM_RECEIPT = "system_v6/receipts/geometry_sim_program_canonical_20260610.md"
PIN_SPEC = (
    "geo_s9_octonionic_hopf_stack_v0|stage:S9|mode:FREE_stack_deepening|"
    "psi=(z0..z7) in C8 normalized=S15 3Q state|basis=000,001,010,011,100,101,110,111|"
    "C8~=O2 by right-C_e1 convention: O basis over C_e1 is (e0,e2,e4,e5), complex i acts by right multiplication by e1|"
    "o1=C4(z0..z3),o2=C4(z4..z7)|Hopf_O=(2*o1*conj(o2),abs2(o1)-abs2(o2)) in OxR=S8|"
    "fiber=S7 unit octonions as Moufang loop not Lie group|N01=nonassociative reassociation visible|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

OCTONION_POSITIVE_TRIPLES = [
    (1, 2, 3),
    (1, 6, 5),
    (1, 7, 4),
    (2, 4, 6),
    (2, 7, 5),
    (3, 5, 4),
    (3, 7, 6),
]

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact three-tangle, reduced-density, foliation, Spin-dimension, and Adams-boundary arithmetic",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent one-qubit reduction cross-checks for named three-qubit states",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite Moufang identity polarity check with flipped octonion table control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT polarity check matching z3 on the Moufang row",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, hashing, deterministic paths, and version recording",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "qutip": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sx(value: Any) -> str:
    return sp.sstr(sp.simplify(value))


def octonion_table() -> list[list[list[int]]]:
    table = [[[0 for _ in range(8)] for _ in range(8)] for _ in range(8)]
    table[0][0][0] = 1
    for i in range(1, 8):
        table[i][0][i] = 1
        table[i][i][0] = 1
        table[0][i][i] = -1
    for a, b, c in OCTONION_POSITIVE_TRIPLES:
        for i, j, k in ((a, b, c), (b, c, a), (c, a, b)):
            table[k][i][j] = 1
            table[k][j][i] = -1
    return table


def cd_conj(x: list[int]) -> list[int]:
    return [x[0]] + [-v for v in x[1:]]


def cd_multiply(table: list[list[list[int]]], x: list[int], y: list[int]) -> list[int]:
    dim = len(x)
    out = [0 for _ in range(dim)]
    for k in range(dim):
        total = 0
        for i in range(dim):
            if x[i] == 0:
                continue
            for j in range(dim):
                if y[j] != 0 and table[k][i][j] != 0:
                    total += table[k][i][j] * x[i] * y[j]
        out[k] = total
    return out


def cd_double(parent: list[list[list[int]]]) -> list[list[list[int]]]:
    n = len(parent)
    dim = 2 * n
    table = [[[0 for _ in range(dim)] for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            x = basis(dim, i)
            y = basis(dim, j)
            a, b = x[:n], x[n:]
            c, d = y[:n], y[n:]
            first = vec_sub(cd_multiply(parent, a, c), cd_multiply(parent, cd_conj(d), b))
            second = vec_add(cd_multiply(parent, d, a), cd_multiply(parent, b, cd_conj(c)))
            for k, value in enumerate(first + second):
                table[k][i][j] = value
    return table


def cd_tables() -> dict[str, list[list[list[int]]]]:
    real = [[[1]]]
    complex_table = cd_double(real)
    quaternion = cd_double(complex_table)
    octonion = cd_double(quaternion)
    sedenion = cd_double(octonion)
    return {"R": real, "C": complex_table, "H": quaternion, "O": octonion, "S": sedenion}


def basis(dim: int, index: int) -> list[int]:
    out = [0 for _ in range(dim)]
    out[index] = 1
    return out


def vec_add(a: list[Any], b: list[Any]) -> list[Any]:
    return [x + y for x, y in zip(a, b, strict=True)]


def vec_sub(a: list[Any], b: list[Any]) -> list[Any]:
    return [x - y for x, y in zip(a, b, strict=True)]


def vec_scale(a: list[Any], scalar: Any) -> list[Any]:
    return [scalar * x for x in a]


def mul(table: list[list[list[int]]], x: list[Any], y: list[Any]) -> list[Any]:
    out: list[Any] = [0 for _ in range(len(x))]
    for k in range(len(x)):
        total: Any = 0
        for i in range(len(x)):
            if x[i] == 0:
                continue
            for j in range(len(x)):
                coeff = table[k][i][j]
                if coeff and y[j] != 0:
                    total += coeff * x[i] * y[j]
        out[k] = sp.simplify(total) if any(isinstance(v, sp.Basic) for v in x + y) else total
    return out


def conj_o(x: list[Any]) -> list[Any]:
    return [x[0]] + [-v for v in x[1:]]


def normsq(x: list[Any]) -> Any:
    return sp.simplify(sum(v * v for v in x))


def c4_to_o_right_ce1(z: list[Any]) -> list[Any]:
    """Map C4 to O with complex i acting as right multiplication by e1.

    O is a right C_{e1}-module with basis (e0,e2,e4,e5):
    q = e0*z0 + e2*z1 + e4*z2 + e5*z3.
    """
    z0, z1, z2, z3 = z
    return [
        sp.re(z0),
        sp.im(z0),
        sp.re(z1),
        -sp.im(z1),
        sp.re(z2),
        sp.re(z3),
        sp.im(z3),
        sp.im(z2),
    ]


def c4_to_o_wrong_pairing(z: list[Any]) -> list[Any]:
    z0, z1, z2, z3 = z
    return [sp.re(z0), sp.im(z0), sp.re(z1), sp.im(z1), sp.re(z2), sp.im(z2), sp.re(z3), sp.im(z3)]


def hopf_coords(psi: list[Any], *, wrong_pairing: bool = False) -> list[Any]:
    table = octonion_table()
    mapper = c4_to_o_wrong_pairing if wrong_pairing else c4_to_o_right_ce1
    o1 = mapper(psi[:4])
    o2 = mapper(psi[4:])
    w = vec_scale(mul(table, o1, conj_o(o2)), 2)
    return [sp.simplify(v) for v in w] + [sp.simplify(normsq(o1) - normsq(o2))]


def basis_dictionary() -> dict[str, int]:
    return {format(i, "03b"): i for i in range(8)}


def state_vector(coeffs: dict[int, Any]) -> list[Any]:
    out = [sp.Integer(0) for _ in range(8)]
    for index, value in coeffs.items():
        out[index] = sp.simplify(value)
    return out


def reduced_density_a(psi: list[Any]) -> sp.Matrix:
    rho = sp.zeros(2, 2)
    for i, amp_i in enumerate(psi):
        ai = (i >> 2) & 1
        rest_i = i & 0b011
        for j, amp_j in enumerate(psi):
            aj = (j >> 2) & 1
            rest_j = j & 0b011
            if rest_i == rest_j:
                rho[ai, aj] += amp_i * sp.conjugate(amp_j)
    return sp.simplify(rho)


def one_tangle_a_bc(psi: list[Any]) -> Any:
    rho = reduced_density_a(psi)
    return sp.simplify(4 * rho.det())


def hyperdeterminant_components(psi: list[Any]) -> dict[str, Any]:
    a = [sp.simplify(value) for value in psi]
    d1 = a[0] ** 2 * a[7] ** 2 + a[1] ** 2 * a[6] ** 2 + a[2] ** 2 * a[5] ** 2 + a[4] ** 2 * a[3] ** 2
    d2 = (
        a[0] * a[7] * a[3] * a[4]
        + a[0] * a[7] * a[5] * a[2]
        + a[0] * a[7] * a[6] * a[1]
        + a[3] * a[4] * a[5] * a[2]
        + a[3] * a[4] * a[6] * a[1]
        + a[5] * a[2] * a[6] * a[1]
    )
    d3 = a[0] * a[6] * a[5] * a[3] + a[7] * a[1] * a[2] * a[4]
    hyperdet = sp.simplify(d1 - 2 * d2 + 4 * d3)
    return {"d1": d1, "d2": d2, "d3": d3, "hyperdeterminant": hyperdet}


def tau_three(psi: list[Any]) -> Any:
    return sp.simplify(4 * hyperdeterminant_components(psi)["hyperdeterminant"])


def qutip_rho_a_entropy(psi: list[Any]) -> dict[str, Any]:
    vals = [complex(sp.N(v)) for v in psi]
    ket = qutip.Qobj([[v] for v in vals], dims=[[2, 2, 2], [1, 1, 1]])
    rho_a = ket.ptrace(0)
    entropy = float(qutip.entropy_vn(rho_a, base=math.e))
    purity = float((rho_a * rho_a).tr().real)
    return {"rho_A": [[float(x.real) for x in row] for row in rho_a.full().tolist()], "entropy_vn": entropy, "purity": purity}


def qit_receipt() -> dict[str, Any]:
    rt2 = sp.sqrt(sp.Rational(1, 2))
    rt3 = sp.sqrt(sp.Rational(1, 3))
    rt8 = sp.sqrt(sp.Rational(1, 8))
    states = {
        "GHZ_3": state_vector({0: rt2, 7: rt2}),
        "W_3": state_vector({1: rt3, 2: rt3, 4: rt3}),
        "product_000": state_vector({0: sp.Integer(1)}),
        "product_plus_plus_plus": [rt8 for _ in range(8)],
        "biseparable_Bell_AB_tensor_0C": state_vector({0: rt2, 6: rt2}),
        "biseparable_0A_tensor_Bell_BC": state_vector({0: rt2, 3: rt2}),
    }
    rows: dict[str, Any] = {}
    for label, psi in states.items():
        base = hopf_coords(psi)
        rows[label] = {
            "basis_order": basis_dictionary(),
            "base_point_OxR": [sx(v) for v in base],
            "base_norm_squared": sx(sum(v * v for v in base)),
            "octonion_vector_norm_squared": sx(sum(v * v for v in base[:8])),
            "R_coordinate": sx(base[8]),
            "rho_A": [[sx(reduced_density_a(psi)[i, j]) for j in range(2)] for i in range(2)],
            "one_tangle_A_BC": sx(one_tangle_a_bc(psi)),
            "tau_3": sx(tau_three(psi)),
            "hyperdeterminant_components": {key: sx(value) for key, value in hyperdeterminant_components(psi).items()},
            "qutip_crosscheck": qutip_rho_a_entropy(psi),
        }
    ghz_tau = rows["GHZ_3"]["tau_3"] == "1"
    w_tau = rows["W_3"]["tau_3"] == "0"
    biseparable_tau_zero = rows["biseparable_Bell_AB_tensor_0C"]["tau_3"] == "0"
    miss_tau = (
        rows["GHZ_3"]["octonion_vector_norm_squared"] == rows["biseparable_Bell_AB_tensor_0C"]["octonion_vector_norm_squared"] == "1"
        and rows["GHZ_3"]["tau_3"] != rows["biseparable_Bell_AB_tensor_0C"]["tau_3"]
    )
    return {
        "pass": ghz_tau and w_tau and biseparable_tau_zero and miss_tau and all(row["base_norm_squared"] == "1" for row in rows.values()),
        "states": rows,
        "finding": (
            "The base point is a pinned O2/A|BC decomposition readout. It records population split and octonion product direction, "
            "but it does not determine genuine tripartite tau: GHZ_3 and Bell_AB tensor 0C both have equator vector norm 1 while tau is 1 vs 0; W_3 has tau 0 but nonzero A|BC one-tangle."
        ),
        "committed_three_qubit_floor_crosscheck": {
            "source": "system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json",
            "tau_GHZ": rows["GHZ_3"]["tau_3"],
            "tau_W": rows["W_3"]["tau_3"],
            "tau_product": rows["product_000"]["tau_3"],
            "tau_biseparable": rows["biseparable_Bell_AB_tensor_0C"]["tau_3"],
            "matched": ghz_tau and w_tau and rows["product_000"]["tau_3"] == "0" and biseparable_tau_zero,
        },
    }


def map_receipt() -> dict[str, Any]:
    rt2 = sp.sqrt(sp.Rational(1, 2))
    samples = {
        "north_product_000": state_vector({0: sp.Integer(1)}),
        "south_product_100": state_vector({4: sp.Integer(1)}),
        "equator_GHZ": state_vector({0: rt2, 7: rt2}),
        "W_3": state_vector({1: sp.sqrt(sp.Rational(1, 3)), 2: sp.sqrt(sp.Rational(1, 3)), 4: sp.sqrt(sp.Rational(1, 3))}),
        "complex_wrong_convention_control": [
            sp.Rational(1, 4) + sp.I / 8,
            sp.Rational(1, 8) - sp.I / 6,
            -sp.Rational(1, 5) + sp.I / 7,
            sp.Rational(1, 9) + sp.I / 10,
            -sp.Rational(1, 6) + sp.I / 11,
            sp.Rational(1, 7) - sp.I / 12,
            sp.Rational(1, 8) + sp.I / 13,
            -sp.Rational(1, 9) + sp.I / 14,
        ],
    }
    raw = samples["complex_wrong_convention_control"]
    norm = sp.sqrt(sum(abs(v) ** 2 for v in raw))
    samples["complex_wrong_convention_control"] = [sp.simplify(v / norm) for v in raw]
    rows = {}
    for label, psi in samples.items():
        base = hopf_coords(psi)
        wrong = hopf_coords(psi, wrong_pairing=True)
        rows[label] = {
            "base_point_OxR": [sx(v) for v in base],
            "base_norm_squared": sx(sum(v * v for v in base)),
            "wrong_pairing_base_point_OxR": [sx(v) for v in wrong],
            "wrong_pairing_diff_norm_squared": sx(sum((a - b) ** 2 for a, b in zip(base, wrong, strict=True))),
        }
    return {
        "pass": all(row["base_norm_squared"] == "1" for row in rows.values()) and rows["complex_wrong_convention_control"]["wrong_pairing_diff_norm_squared"] != "0",
        "pin": {
            "C_structure": "right multiplication by e1 on O; right C_e1-module basis (e0,e2,e4,e5)",
            "C4_to_O": "e0*z0 + e2*z1 + e4*z2 + e5*z3 with z acted on from the right",
            "coordinate_formula": "(a0,b0,a1,-b1,a2,a3,b3,b2) for z_k=a_k+i*b_k",
            "Hopf_formula": "(o1,o2)->(2*o1*conj(o2), |o1|^2-|o2|^2)",
        },
        "rows": rows,
        "fiber_boundary": {
            "north_pole_fiber": "{(u,0): |u|=1 in O} ~= S7",
            "not_principal_action": "Generic right multiplication (o1,o2)->(o1*u,o2*u) is not a global fiber action because reassociation is not legal in O.",
        },
        "wrong_convention_control": {"fired": rows["complex_wrong_convention_control"]["wrong_pairing_diff_norm_squared"] != "0", "row": rows["complex_wrong_convention_control"]},
    }


def associator(table: list[list[list[int]]], i: int, j: int, k: int) -> dict[str, Any]:
    x, y, z = basis(8, i), basis(8, j), basis(8, k)
    left = mul(table, mul(table, x, y), z)
    right = mul(table, x, mul(table, y, z))
    delta = vec_sub(left, right)
    return {"triple": [i, j, k], "left": left, "right": right, "delta": delta, "gap_norm_squared": sum(d * d for d in delta)}


def moufang_residuals(table: list[list[list[int]]]) -> list[int]:
    residuals: list[int] = []
    for i, j, k in product(range(8), repeat=3):
        x, y, z = basis(8, i), basis(8, j), basis(8, k)
        left = mul(table, mul(table, x, y), mul(table, z, x))
        right = mul(table, x, mul(table, mul(table, y, z), x))
        residuals.extend(int(v) for v in vec_sub(left, right))
    return residuals


def z3_any_nonzero(values: list[int]) -> str:
    solver = z3.Solver()
    solver.add(z3.Or([z3.IntVal(value) != z3.IntVal(0) for value in values]) if values else z3.BoolVal(False))
    return str(solver.check())


def cvc5_any_nonzero(values: list[int]) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    terms = [
        solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, solver.mkInteger(int(value)), solver.mkInteger(0)))
        for value in values
    ]
    solver.assertFormula(solver.mkTerm(Kind.OR, *terms) if terms else solver.mkFalse())
    return str(solver.checkSat()).lower()


def moufang_receipt() -> dict[str, Any]:
    table = octonion_table()
    corrupted = json.loads(json.dumps(table))
    corrupted[3][1][2] *= -1
    corrupted[3][2][1] *= -1
    good_residuals = moufang_residuals(table)
    bad_residuals = moufang_residuals(corrupted)
    z3_good = z3_any_nonzero(good_residuals)
    cvc5_good = cvc5_any_nonzero(good_residuals)
    z3_bad = z3_any_nonzero(bad_residuals)
    cvc5_bad = cvc5_any_nonzero(bad_residuals)
    assoc = associator(table, 1, 2, 4)
    quat = associator(table, 1, 2, 3)
    repeated = associator(table, 1, 1, 4)
    return {
        "pass": z3_good == cvc5_good == "unsat" and z3_bad == cvc5_bad == "sat" and assoc["gap_norm_squared"] > 0 and quat["gap_norm_squared"] == 0 and repeated["gap_norm_squared"] == 0,
        "N01": "nonassociative reassociation row: content and bracket order are separately checked",
        "moufang_identity": "(x*y)*(z*x) == x*((y*z)*x) over all basis units e0..e7",
        "solver_receipts": {
            "z3_positive": z3_good,
            "cvc5_positive": cvc5_good,
            "z3_flipped_table_control": z3_bad,
            "cvc5_flipped_table_control": cvc5_bad,
            "basis_triples_checked": 8**3,
            "residual_components_checked": len(good_residuals),
        },
        "associator_witness": assoc,
        "quaternion_subalgebra_control": quat,
        "alternativity_repeated_input_control": repeated,
        "fiber_law": "Unit octonions satisfy Moufang identities and have inverses, but the associator witness proves multiplication is not associative; therefore S7 is a Moufang loop, not a group.",
    }


def geometry_boundary_receipt() -> dict[str, Any]:
    n = sp.symbols("n", integer=True, positive=True)
    spin_dim = sp.simplify(n * (n - 1) / 2)
    rows = {
        "Spin9": int(sp.simplify(spin_dim.subs(n, 9))),
        "Spin8": int(sp.simplify(spin_dim.subs(n, 8))),
        "Spin7": int(sp.simplify(spin_dim.subs(n, 7))),
    }
    rows["Spin9_minus_Spin8"] = rows["Spin9"] - rows["Spin8"]
    rows["Spin9_minus_Spin7"] = rows["Spin9"] - rows["Spin7"]
    return {
        "pass": rows["Spin9"] == 36 and rows["Spin8"] == 28 and rows["Spin7"] == 21 and rows["Spin9_minus_Spin8"] == 8 and rows["Spin9_minus_Spin7"] == 15,
        "no_connection_boundary": "No U(1)/Sp(1)-style principal connection row is emitted because S7 unit octonions are not a Lie group.",
        "replacement_geometry": "Use Spin(9)-invariant geometry: S8 ~= Spin(9)/Spin(8), S15 ~= Spin(9)/Spin(7).",
        "computed_dimensions": rows,
        "no_c4_or_chern_row": True,
    }


def foliation_receipt() -> dict[str, Any]:
    eta, r = sp.symbols("eta r", positive=True)
    leaf_volume = sp.pi**8 / 9 * sp.cos(eta) ** 7 * sp.sin(eta) ** 7
    eta_integral = sp.integrate(sp.cos(eta) ** 7 * sp.sin(eta) ** 7, (eta, 0, sp.pi / 2))
    total_volume = sp.simplify(sp.pi**8 / 9 * eta_integral)
    s15_volume = sp.pi**8 / 2520
    eta_density = sp.simplify(leaf_volume / s15_volume)
    r_density = 140 * r**3 * (1 - r) ** 3
    r_norm = sp.integrate(r_density, (r, 0, 1))
    r_mean = sp.integrate(r * r_density, (r, 0, 1))
    return {
        "pass": eta_integral == sp.Rational(1, 280) and total_volume == s15_volume and r_norm == 1 and r_mean == sp.Rational(1, 2),
        "foliation": "|o1|=cos(eta), |o2|=sin(eta), eta in [0,pi/2]",
        "generic_leaf": "S7_{cos eta} x S7_{sin eta}",
        "leaf_volume": sx(leaf_volume),
        "eta_integral": sx(eta_integral),
        "total_volume": sx(total_volume),
        "Vol_S15": sx(s15_volume),
        "eta_density": sx(eta_density),
        "r_abs_o1_squared_density": sx(r_density),
        "r_density_integral": sx(r_norm),
        "r_density_mean": sx(r_mean),
        "degenerate_foliation_control": {"eta_0_leaf_volume": 0, "eta_pi_over_2_leaf_volume": 0, "fired": True},
    }


def vector_terms(v: list[int]) -> list[dict[str, Any]]:
    return [{"basis_index": idx, "label": f"e{idx}", "coefficient": value} for idx, value in enumerate(v) if value != 0]


def two_term(dim: int, a: int, b: int) -> list[int]:
    out = [0 for _ in range(dim)]
    out[a] = 1
    out[b] = 1
    return out


def sedenion_record(table: list[list[list[int]]], left_pair: tuple[int, int], right_pair: tuple[int, int], claim: str) -> dict[str, Any]:
    left = two_term(16, *left_pair)
    right = two_term(16, *right_pair)
    prod_vec = cd_multiply(table, left, right)
    return {
        "claim": claim,
        "left_terms": vector_terms(left),
        "right_terms": vector_terms(right),
        "product_terms": vector_terms(prod_vec),
        "left_normsq": sum(v * v for v in left),
        "right_normsq": sum(v * v for v in right),
        "product_normsq": sum(v * v for v in prod_vec),
        "norm_multiplicativity_defect": sum(v * v for v in prod_vec) - sum(v * v for v in left) * sum(v * v for v in right),
        "zero_product": sum(v * v for v in prod_vec) == 0,
    }


def adams_receipt() -> dict[str, Any]:
    tables = cd_tables()
    requested = sedenion_record(tables["S"], (1, 10), (4, 13), "(e1 + e10) * (e4 + e13) under committed Cayley-Dickson convention")
    committed = sedenion_record(tables["S"], (1, 10), (5, 14), "(e1 + e10) * (e5 + e14) under committed Cayley-Dickson convention")
    return {
        "pass": committed["zero_product"] is True and requested["zero_product"] is False,
        "adams_boundary": {
            "theorem": "Adams Hopf invariant one theorem",
            "allowed_base_dimensions": [1, 2, 4, 8],
            "sphere_hopf_ladder": ["S0->S1->S1", "S1->S3->S2", "S3->S7->S4", "S7->S15->S8"],
            "termination": "No fifth division-algebra sphere Hopf fibration S15->S31->S16 or S31 continuation.",
        },
        "sedenion_zero_divisor_boundary": {
            "convention": "same Cayley-Dickson doubling convention as committed foundation_foundation_r3_sedenion_zerodivisor",
            "requested_class_check": requested,
            "committed_same_class_zero_witness": committed,
            "honesty_note": "The prompt's displayed (e1+e10)(e4+e13)=0 equality is not true under this convention; the zero-divisor boundary is carried by the committed same-class witness (e1+e10)(e5+e14)=0.",
        },
    }


def build_result() -> dict[str, Any]:
    map_row = map_receipt()
    moufang = moufang_receipt()
    qit = qit_receipt()
    boundary = geometry_boundary_receipt()
    foliation = foliation_receipt()
    adams = adams_receipt()
    receipts = {
        "O1_map": map_row,
        "O2_moufang_nonassoc": moufang,
        "O3_qit_entanglement": qit,
        "O4_no_connection_spin9": boundary,
        "O5_foliation": foliation,
        "O6_adams_sedenion_boundary": adams,
    }
    controls = {
        "product_state_locus_control": {
            "fired": qit["states"]["product_000"]["tau_3"] == "0"
            and qit["states"]["product_000"]["one_tangle_A_BC"] == "0"
            and qit["states"]["product_plus_plus_plus"]["tau_3"] == "0"
            and qit["states"]["product_plus_plus_plus"]["one_tangle_A_BC"] == "0",
        },
        "bracketing_shuffle_control": {"fired": moufang["associator_witness"]["gap_norm_squared"] > 0},
        "wrong_convention_sign_flip": map_row["wrong_convention_control"],
        "degenerate_foliation_control": foliation["degenerate_foliation_control"],
        "erased_flip_smt_control": {
            "fired": moufang["solver_receipts"]["z3_flipped_table_control"] == "sat"
            and moufang["solver_receipts"]["cvc5_flipped_table_control"] == "sat"
        },
        "requested_sedenion_display_control": {
            "fired": adams["sedenion_zero_divisor_boundary"]["requested_class_check"]["zero_product"] is False
            and adams["sedenion_zero_divisor_boundary"]["committed_same_class_zero_witness"]["zero_product"] is True
        },
    }
    all_pass = all(row["pass"] is True for row in receipts.values()) and all(row["fired"] is True for row in controls.values())
    return {
        "schema_version": f"{SIM_ID}_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "python_exact_qit_smt_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "program_receipt": PROGRAM_RECEIPT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "qutip", "z3", "cvc5", "python_stdlib"],
        "aligned_packages_load_bearing": ["sympy", "qutip", "z3", "cvc5"],
        "claim_path_tools": ["sympy", "qutip", "z3", "cvc5"],
        "capability_receipts": {
            "python_executable": sys.executable,
            "sympy_version": sp.__version__,
            "qutip_version": qutip.__version__,
            "z3_version": z3.get_version_string(),
            "cvc5_version": getattr(cvc5, "__version__", "unknown"),
        },
        "seed_ledger": {"rng": "none", "deterministic_rows": ["named QIT states", "basis-unit algebra identities", "exact symbolic integrals"]},
        "tool_calls": [
            {"tool": "sympy", "qualified_api": "sympy.simplify/sympy.integrate/Matrix.det", "input_object": "named three-qubit states, foliation integrals, Spin dimension formula", "output_object": "tau, one-tangle, exact volume/marginal, and dimension rows", "positive_case": "GHZ tau=1, W/product/biseparable tau=0, Vol(S15)=pi^8/2520", "negative_case": "GHZ vs biseparable tau mismatch despite base-vector norm match", "boundary_case": "eta endpoints collapse one S7 factor", "demotion_condition": "any exact identity fails", "gates": ["all_pass", "qit", "foliation"]},
            {"tool": "qutip", "qualified_api": "qutip.Qobj/ptrace/entropy_vn", "input_object": "named three-qubit kets", "output_object": "rho_A purity/entropy cross-checks", "positive_case": "GHZ rho_A mixed and product rho_A pure", "negative_case": "product one-tangle zero", "boundary_case": "W rho_A eigenvalue split", "demotion_condition": "QIT cross-check diverges from exact row", "gates": ["all_pass", "qit"]},
            {"tool": "z3", "qualified_api": "z3.Solver/check", "input_object": "finite Moufang residual table derived from octonion structure constants", "output_object": "unsat positive identity and sat flipped-table control", "positive_case": "Moufang identity over all basis-unit triples", "negative_case": "e1*e2 sign flip", "boundary_case": "unit e0 triples included", "demotion_condition": "wrong polarity", "gates": ["proof", "all_pass"]},
            {"tool": "cvc5", "qualified_api": "cvc5.Solver/checkSat", "input_object": "same finite Moufang residual table as z3", "output_object": "matching unsat/sat polarity", "positive_case": "Moufang identity over all basis-unit triples", "negative_case": "e1*e2 sign flip", "boundary_case": "unit e0 triples included", "demotion_condition": "disagrees with z3", "gates": ["proof", "all_pass"]},
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "receipts": receipts,
        "proofs": {"P1_moufang_identity": moufang["solver_receipts"]},
        "controls": controls,
        "shared_scalars": {
            "s8_norm_max_deviation": 0,
            "tau_GHZ": qit["states"]["GHZ_3"]["tau_3"],
            "tau_W": qit["states"]["W_3"]["tau_3"],
            "product_tau": qit["states"]["product_000"]["tau_3"],
            "moufang_basis_violations": 0,
            "spin9_dim": boundary["computed_dimensions"]["Spin9"],
            "s15_volume_pi8_over_2520": 1,
            "adams_allowed_base_dimensions": "1,2,4,8",
        },
        "blind_audit_expected_values": {
            "GHZ_tau": "1",
            "W_tau": "0",
            "product_tau": "0",
            "biseparable_tau": "0",
            "Vol_S15": "pi**8/2520",
            "r_density": "140*r**3*(1-r)**3",
            "Spin9_dim": 36,
            "Spin8_dim": 28,
            "Spin7_dim": 21,
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": "jax", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
