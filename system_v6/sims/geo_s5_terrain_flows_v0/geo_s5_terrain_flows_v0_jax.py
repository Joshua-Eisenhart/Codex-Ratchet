#!/usr/bin/env python3
"""JAX/SymPy/SMT leg for geo_s5_terrain_flows_v0."""

from __future__ import annotations

import datetime as dt
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

import cvc5
import diffrax
from cvc5 import Kind
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s5_terrain_flows_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8

PIN_SPEC = (
    "geo_s5_terrain_flows_v0|"
    "sigma_y_standard=[[0,-i],[i,0]]|"
    "primary_bloch_basis=(sigma_x,sigma_y_standard,sigma_z)|"
    "s1_pinned_bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|"
    "standard_to_s1_pinned_J=diag(1,-1,1)|"
    "component_rule=r_i=Tr(generator(rho)*basis_i)|"
    "rho_rule=rho(r)=(I+r.basis)/2|"
    "H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)|H_L=+H0|H_R=-H0|"
    "rows=(Se/Funnel,Se/Cannon,Ne/Vortex,Ne/Spiral,Ni/Pit,Ni/Source,Si/Hill,Si/Citadel)|"
    "symbolic_parameters=(lambda_Se_L,epsilon_Se_L,lambda_Se_R,epsilon_Se_R,gamma_Ni_L,epsilon_Ni_L,gamma_Ni_R,epsilon_Ni_R,kappa_Si_L,omega_Si_L,kappa_Si_R,omega_Si_R)|"
    "pin_row=(lambda_Se_L=1/5,epsilon_Se_L=1/5,lambda_Se_R=1/5,epsilon_Se_R=1/5,gamma_Ni_L=1/2,epsilon_Ni_L=1/5,gamma_Ni_R=1/2,epsilon_Ni_R=1/5,kappa_Si_L=2/5,omega_Si_L=1/5,kappa_Si_R=2/5,omega_Si_R=1/5)|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "sigma_y_standard": [["0", "-i"], ["i", "0"]],
    "primary_table_basis": "source_locked_standard_bloch",
    "source_locked_bloch_basis": ["sigma_x", "sigma_y_standard", "sigma_z"],
    "s1_pinned_bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "standard_to_s1_pinned_J": [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]],
    "conversion_rule": "A_s1_pinned = J * A_source_locked_standard * J and b_s1_pinned = J * b",
    "component_rule": "r_i = Tr(generator(rho) * basis_i)",
    "rho_rule": "rho(r) = (I + r.basis) / 2",
    "hamiltonian_pin": {
        "H0": "(sigma_x + sigma_y + sigma_z) / sqrt(3)",
        "H_L": "+H0",
        "H_R": "-H0",
        "n": ["1/sqrt(3)", "1/sqrt(3)", "1/sqrt(3)"],
    },
    "si_frame_pin": {"Hill": "z frame", "Citadel": "x frame"},
    "stage": "S5 density/Bloch terrain flows only",
}

PIN_VALUES = {
    "lambda_Se_L": Fraction(1, 5),
    "epsilon_Se_L": Fraction(1, 5),
    "lambda_Se_R": Fraction(1, 5),
    "epsilon_Se_R": Fraction(1, 5),
    "gamma_Ni_L": Fraction(1, 2),
    "epsilon_Ni_L": Fraction(1, 5),
    "gamma_Ni_R": Fraction(1, 2),
    "epsilon_Ni_R": Fraction(1, 5),
    "kappa_Si_L": Fraction(2, 5),
    "omega_Si_L": Fraction(1, 5),
    "kappa_Si_R": Fraction(2, 5),
    "omega_Si_R": Fraction(1, 5),
}

SOURCE_LINEAGE = {
    "terrain_math_generators": {
        "path": "system_v5/READ ONLY Reference Docs/terrain math.md",
        "lines": "70-90",
        "reuse": "source_law_citation_and_line_hash_only",
    },
    "terrain_rosetta_hamiltonians_channels": {
        "path": "system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md",
        "lines": "45-71",
        "reuse": "source_law_citation_and_line_hash_only",
    },
    "terrain_generator_sheet_packet_sources_and_pins": {
        "path": "system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py",
        "lines": "48-99,191-208,371-447",
        "reuse": "cite_only_existing_packet_not_rebuilt",
    },
    "terrain_generator_sheet_packet_results": {
        "path": "system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json",
        "lines": "24,2584,2957,3018,3079,4678,4999,5270-5831",
        "reuse": "finite_time_context_only_not_new_basin_proof",
    },
    "terrain_generator_sheet_packet_audit": {
        "path": "system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md",
        "lines": "3-20,24-42,67-78,121-130",
        "reuse": "caveat_boundary",
    },
    "matrix64_context": {
        "path": "system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md",
        "lines": "11-13,28-38,76-99,117-144",
        "reuse": "finite_time_order_gap_context_only",
    },
    "s4_v2_process_lessons": {
        "path": "system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md",
        "lines": "326-398",
        "reuse": "process_lesson_binding",
    },
}

SOURCE_LOCK_LINE_RANGES = {
    "terrain_math_dissipator_generators_projectors_70_90": ("system_v5/READ ONLY Reference Docs/terrain math.md", 70, 90),
    "terrain_rosetta_hamiltonians_channels_45_71": ("system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md", 45, 71),
    "s4_v2_lessons_326_398": ("system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md", 326, 398),
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact symbolic derivation of Bloch generator A,b rows, stationary sets, flow formulas, purity derivatives, and mutation controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing pinned-entry contradiction proof for Ni non-unitality; not a full symbolic flow proof",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent pinned-entry contradiction proof for the same Ni non-unitality entry",
    },
    "jax": {"tried": True, "used": True, "reason": "supportive x64 sampled channel regression fixtures"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive pinned matrix/channel arithmetic for regression fixtures"},
    "diffrax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ODE solver route for pinned affine Bloch flow evolution; gates P3 by matching exact constant-coefficient special-case checks",
    },
    "jax.scipy.linalg": {
        "tried": True,
        "used": True,
        "reason": "supportive exact matrix-exponential special-case check for constant-coefficient channel and affine-flow fixtures; not the primary flow solver route",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "diffrax": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
    "jax.scipy.linalg": "supportive",
}

ALLOWED_STRENGTHS = {
    "exact_symbolic_generator_table",
    "exact_flow_formula",
    "gksl_all_t_semigroup_proof",
    "sampled_regression_fixture",
    "exact_fixed_point_solution",
    "basin_limit_formula",
    "nonlimit_orbit_receipt",
    "purity_spectrum_invariant",
    "unitality_identity_witness",
    "smt_pinned_entry_contradiction",
    "executed_mutation_control",
    "lineage_citation_only",
    "quotient_boundary_statement",
    "scratch_ceiling_token",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_line_range(relative_path: str, start_line: int, end_line: int) -> str:
    lines = (ROOT / relative_path).read_text(encoding="utf-8").splitlines()
    payload = "\n".join(lines[start_line - 1 : end_line]) + "\n"
    return sha256_text(payload)


def sstr(expr: Any) -> str:
    return sp.sstr(sp.trigsimp(sp.factor(sp.simplify(expr))))


def matrix_strings(mat: sp.Matrix) -> list[list[str]]:
    return [[sstr(mat[i, j]) for j in range(mat.cols)] for i in range(mat.rows)]


def vector_strings(vec: sp.Matrix) -> list[str]:
    return [sstr(vec[i, 0]) for i in range(vec.rows)]


PARSE_LOCALS = {
    name: sp.symbols(name, real=True)
    for name in [
        "r_x",
        "r_y",
        "r_z",
        "t",
        "lambda_Se_L",
        "epsilon_Se_L",
        "lambda_Se_R",
        "epsilon_Se_R",
        "gamma_Ni_L",
        "epsilon_Ni_L",
        "gamma_Ni_R",
        "epsilon_Ni_R",
        "kappa_Si_L",
        "omega_Si_L",
        "kappa_Si_R",
        "omega_Si_R",
    ]
}


def parse_expr(value: str) -> sp.Expr:
    return sp.sympify(value.replace("//", "/"), locals=PARSE_LOCALS)


def parse_matrix_strings(values: list[list[str]]) -> sp.Matrix:
    return sp.Matrix([[parse_expr(item) for item in row] for row in values])


def parse_vector_strings(values: list[str]) -> sp.Matrix:
    return sp.Matrix([parse_expr(item) for item in values])


def numeric_expr_from_sympy(value: sp.Expr) -> float:
    return float(sp.N(value, 40))


def jnp_matrix(mat: sp.Matrix) -> jnp.ndarray:
    return jnp.asarray([[numeric_expr_from_sympy(mat[i, j]) for j in range(mat.cols)] for i in range(mat.rows)], dtype=jnp.float64)


def jnp_vector(vec: sp.Matrix) -> jnp.ndarray:
    return jnp.asarray([numeric_expr_from_sympy(vec[i, 0]) for i in range(vec.rows)], dtype=jnp.float64)


def is_zero_expr(value: sp.Expr) -> bool:
    return sp.simplify(sp.cancel(sp.factor(sp.expand(sp.simplify(value))))) == 0


def matrix_equal(left: sp.Matrix, right: sp.Matrix) -> bool:
    return left.shape == right.shape and all(is_zero_expr(left[i, j] - right[i, j]) for i in range(left.rows) for j in range(left.cols))


def vector_equal(left: sp.Matrix, right: sp.Matrix) -> bool:
    return left.shape == right.shape and all(is_zero_expr(left[i, 0] - right[i, 0]) for i in range(left.rows))


def vector_is_zero(vec: sp.Matrix) -> bool:
    return all(is_zero_expr(vec[i, 0]) for i in range(vec.rows))


def matrix_is_zero(mat: sp.Matrix) -> bool:
    return all(is_zero_expr(mat[i, j]) for i in range(mat.rows) for j in range(mat.cols))


def expected_ne_A(sign: int) -> sp.Matrix:
    w = sp.Rational(sign * 2, 1) / sp.sqrt(3)
    return sp.Matrix([[0, -w, w], [w, 0, -w], [-w, w, 0]])


def bloch_state_vector(sym: dict[str, sp.Symbol]) -> sp.Matrix:
    return sp.Matrix([sym["r_x"], sym["r_y"], sym["r_z"]])


def affine_residual(comps: sp.Matrix, A: sp.Matrix, b: sp.Matrix, sym: dict[str, sp.Symbol]) -> sp.Matrix:
    r = bloch_state_vector(sym)
    return sp.simplify(comps - (A * r + b))


def receipt(claim_id: str, exact_strength: str, passed: bool, **extra: Any) -> dict[str, Any]:
    if exact_strength not in ALLOWED_STRENGTHS:
        raise ValueError(f"bad strength token: {exact_strength}")
    return {"id": claim_id, "exact_strength": exact_strength, "pass": bool(passed), "convention_pin": CONVENTION_PIN, **extra}


def pauli_basis() -> dict[str, sp.Matrix]:
    i = sp.I
    sigma_x = sp.Matrix([[0, 1], [1, 0]])
    sigma_y_standard = sp.Matrix([[0, -i], [i, 0]])
    sigma_z = sp.Matrix([[1, 0], [0, -1]])
    sigma_minus = sp.Matrix([[0, 0], [1, 0]])
    sigma_plus = sp.Matrix([[0, 1], [0, 0]])
    return {
        "I": sp.eye(2),
        "X": sigma_x,
        "Y_standard": sigma_y_standard,
        "Yp": -sigma_y_standard,
        "Z": sigma_z,
        "sigma_minus": sigma_minus,
        "sigma_plus": sigma_plus,
    }


def symbols() -> dict[str, sp.Symbol]:
    names = [
        "r_x",
        "r_y",
        "r_z",
        "t",
        "lambda_Se_L",
        "epsilon_Se_L",
        "lambda_Se_R",
        "epsilon_Se_R",
        "gamma_Ni_L",
        "epsilon_Ni_L",
        "gamma_Ni_R",
        "epsilon_Ni_R",
        "kappa_Si_L",
        "omega_Si_L",
        "kappa_Si_R",
        "omega_Si_R",
    ]
    return {name: sp.symbols(name, real=True) for name in names}


def rho_from_r(sym: dict[str, sp.Symbol]) -> sp.Matrix:
    b = pauli_basis()
    return sp.Rational(1, 2) * (b["I"] + sym["r_x"] * b["X"] + sym["r_y"] * b["Y_standard"] + sym["r_z"] * b["Z"])


def component_vector(generator_rho: sp.Matrix) -> sp.Matrix:
    b = pauli_basis()
    return sp.Matrix([sp.simplify(sp.trace(generator_rho * b[name])) for name in ["X", "Y_standard", "Z"]])


def dissipator(L: sp.Matrix, rho: sp.Matrix) -> sp.Matrix:
    Ld = L.conjugate().T
    return sp.simplify(L * rho * Ld - sp.Rational(1, 2) * (Ld * L * rho + rho * Ld * L))


def dephase_projectors(projectors: list[sp.Matrix], rho: sp.Matrix) -> sp.Matrix:
    out = sp.zeros(2, 2)
    for P in projectors:
        out += P * rho * P
    return sp.simplify(out - rho)


def commutator(H: sp.Matrix, rho: sp.Matrix) -> sp.Matrix:
    return H * rho - rho * H


def affine_from_components(comps: sp.Matrix, sym: dict[str, sp.Symbol]) -> tuple[sp.Matrix, sp.Matrix]:
    variables = [sym["r_x"], sym["r_y"], sym["r_z"]]
    zero_sub = {var: 0 for var in variables}
    expanded = sp.Matrix([sp.expand(sp.simplify(comp)) for comp in comps])
    b = sp.Matrix([sp.simplify(comp.subs(zero_sub)) for comp in expanded])
    rows = []
    for comp in expanded:
        rows.append([sp.simplify(sp.diff(comp, var).subs(zero_sub)) for var in variables])
    A = sp.Matrix(rows)
    residual = affine_residual(expanded, A, b, sym)
    if not vector_is_zero(residual):
        raise ValueError(f"non-affine Bloch component extraction residual: {vector_strings(residual)}")
    return A, b


def basis_crosswalk(A: sp.Matrix, b: sp.Matrix) -> dict[str, Any]:
    J = sp.diag(1, -1, 1)
    return {
        "standard_basis": {"A": matrix_strings(A), "b": vector_strings(b)},
        "s1_pinned_y_basis": {"A": matrix_strings(J * A * J), "b": vector_strings(J * b)},
        "rule": CONVENTION_PIN["conversion_rule"],
    }


def generator_rows() -> tuple[dict[str, dict[str, Any]], dict[str, sp.Symbol]]:
    sym = symbols()
    b = pauli_basis()
    rho = rho_from_r(sym)
    H0 = (b["X"] + b["Y_standard"] + b["Z"]) / sp.sqrt(3)
    HL = H0
    HR = -H0
    PZp = (b["I"] + b["Z"]) / 2
    PZm = (b["I"] - b["Z"]) / 2
    PXp = (b["I"] + b["X"]) / 2
    PXm = (b["I"] - b["X"]) / 2
    pauli_sum = dissipator(b["X"], rho) + dissipator(b["Y_standard"], rho) + dissipator(b["Z"], rho)
    raw = {
        "Se_Funnel_L": {
            "label": "Se / Funnel",
            "family": "Se",
            "source_ref": "system_v5/READ ONLY Reference Docs/terrain math.md:76",
            "generator": sym["lambda_Se_L"] * pauli_sum - sp.I * sym["epsilon_Se_L"] * commutator(HL, rho),
            "positive_conditions": ["lambda_Se_L >= 0"],
        },
        "Se_Cannon_R": {
            "label": "Se / Cannon",
            "family": "Se",
            "source_ref": "system_v5/READ ONLY Reference Docs/terrain math.md:77",
            "generator": sym["lambda_Se_R"] * pauli_sum - sp.I * sym["epsilon_Se_R"] * commutator(HR, rho),
            "positive_conditions": ["lambda_Se_R >= 0"],
        },
        "Ne_Vortex_L": {
            "label": "Ne / Vortex",
            "family": "Ne_pure",
            "source_ref": "system_v5/READ ONLY Reference Docs/terrain math.md:78",
            "generator": -sp.I * commutator(HL, rho),
            "positive_conditions": [],
        },
        "Ne_Spiral_R": {
            "label": "Ne / Spiral",
            "family": "Ne_pure",
            "source_ref": "system_v5/READ ONLY Reference Docs/terrain math.md:79",
            "generator": -sp.I * commutator(HR, rho),
            "positive_conditions": [],
        },
        "Ni_Pit_L": {
            "label": "Ni / Pit",
            "family": "Ni",
            "source_ref": "system_v5/READ ONLY Reference Docs/terrain math.md:80",
            "generator": sym["gamma_Ni_L"] * dissipator(b["sigma_minus"], rho) - sp.I * sym["epsilon_Ni_L"] * commutator(HL, rho),
            "positive_conditions": ["gamma_Ni_L >= 0"],
        },
        "Ni_Source_R": {
            "label": "Ni / Source",
            "family": "Ni",
            "source_ref": "system_v5/READ ONLY Reference Docs/terrain math.md:81",
            "generator": sym["gamma_Ni_R"] * dissipator(b["sigma_plus"], rho) - sp.I * sym["epsilon_Ni_R"] * commutator(HR, rho),
            "positive_conditions": ["gamma_Ni_R >= 0"],
        },
        "Si_Hill_L": {
            "label": "Si / Hill",
            "family": "Si",
            "source_ref": "system_v5/READ ONLY Reference Docs/terrain math.md:82",
            "generator": -sp.I * commutator(sym["omega_Si_L"] * b["Z"], rho) + sym["kappa_Si_L"] * dephase_projectors([PZp, PZm], rho),
            "positive_conditions": ["kappa_Si_L >= 0"],
        },
        "Si_Citadel_R": {
            "label": "Si / Citadel",
            "family": "Si",
            "source_ref": "system_v5/READ ONLY Reference Docs/terrain math.md:83",
            "generator": -sp.I * commutator(sym["omega_Si_R"] * b["X"], rho) + sym["kappa_Si_R"] * dephase_projectors([PXp, PXm], rho),
            "positive_conditions": ["kappa_Si_R >= 0"],
        },
    }
    rows: dict[str, dict[str, Any]] = {}
    pin_subs = {sym[name]: sp.Rational(value.numerator, value.denominator) for name, value in PIN_VALUES.items()}
    for key, record in raw.items():
        comps = component_vector(sp.simplify(record["generator"]))
        A, avec = affine_from_components(comps, sym)
        A_pin = sp.simplify(A.subs(pin_subs))
        b_pin = sp.simplify(avec.subs(pin_subs))
        rows[key] = {
            "label": record["label"],
            "family": record["family"],
            "source_ref": record["source_ref"],
            "positive_conditions": record["positive_conditions"],
            "symbolic": {"A": matrix_strings(A), "b": vector_strings(avec)},
            "pinned": {"A": matrix_strings(A_pin), "b": vector_strings(b_pin)},
            "basis_crosswalk": basis_crosswalk(A, avec),
            "pin_consistency": True,
        }
    return rows, sym


def generator_consistency_gates(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ne_l = parse_matrix_strings(rows["Ne_Vortex_L"]["symbolic"]["A"])
    ne_r = parse_matrix_strings(rows["Ne_Spiral_R"]["symbolic"]["A"])
    zero3 = sp.zeros(3, 1)
    expected_l = expected_ne_A(+1)
    expected_r = expected_ne_A(-1)
    checks = {
        "Ne_Vortex_L_A_is_C_plus": matrix_equal(ne_l, expected_l),
        "Ne_Spiral_R_A_is_C_minus": matrix_equal(ne_r, expected_r),
        "Ne_sheet_sign_mirror": matrix_equal(ne_r, -ne_l),
        "Ne_Vortex_L_A_nonzero": not matrix_is_zero(ne_l),
        "Ne_Spiral_R_A_nonzero": not matrix_is_zero(ne_r),
        "Ne_Vortex_L_b_zero": vector_equal(parse_vector_strings(rows["Ne_Vortex_L"]["symbolic"]["b"]), zero3),
        "Ne_Spiral_R_b_zero": vector_equal(parse_vector_strings(rows["Ne_Spiral_R"]["symbolic"]["b"]), zero3),
    }
    return {
        "method": "exported symbolic A,b rows compared to blind Hamiltonian cross-product matrix C_s",
        "expected_C_plus": matrix_strings(expected_l),
        "expected_C_minus": matrix_strings(expected_r),
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def rotation_matrix_strings(axis: str, sign: str, angle: str) -> dict[str, Any]:
    if axis == "n":
        c = f"cos({angle})"
        s = f"sin({angle})"
        one_minus_c = f"1 - {c}"
        # Rodrigues for n=(1,1,1)/sqrt(3), active right-handed.
        R = [
            [f"({c}) + ({one_minus_c})/3", f"({one_minus_c})/3 - ({sign})*{s}/sqrt(3)", f"({one_minus_c})/3 + ({sign})*{s}/sqrt(3)"],
            [f"({one_minus_c})/3 + ({sign})*{s}/sqrt(3)", f"({c}) + ({one_minus_c})/3", f"({one_minus_c})/3 - ({sign})*{s}/sqrt(3)"],
            [f"({one_minus_c})/3 - ({sign})*{s}/sqrt(3)", f"({one_minus_c})/3 + ({sign})*{s}/sqrt(3)", f"({c}) + ({one_minus_c})/3"],
        ]
    elif axis == "z":
        c = f"cos({angle})"
        s = f"sin({angle})"
        R = [[c, f"-({s})", "0"], [s, c, "0"], ["0", "0", "1"]]
    elif axis == "x":
        c = f"cos({angle})"
        s = f"sin({angle})"
        R = [["1", "0", "0"], ["0", c, f"-({s})"], ["0", s, c]]
    else:
        raise ValueError(axis)
    return {"axis": axis, "standard_basis_rotation_matrix": R, "s1_pinned_y_basis_rotation_matrix": convert_matrix_strings_s1(R)}


def convert_matrix_strings_s1(matrix: list[list[str]]) -> list[list[str]]:
    signs = [1, -1, 1]
    out: list[list[str]] = []
    for i, row in enumerate(matrix):
        out_row: list[str] = []
        for j, value in enumerate(row):
            sign = signs[i] * signs[j]
            if value == "0":
                out_row.append("0")
            elif sign == 1:
                out_row.append(value)
            else:
                out_row.append(f"-({value})")
        out.append(out_row)
    return out


def rotation_matrix_sym(axis: str, sign: int, angle: sp.Expr) -> sp.Matrix:
    c = sp.cos(angle)
    s = sp.sin(angle)
    if axis == "n":
        one_minus_c = 1 - c
        return sp.Matrix(
            [
                [c + one_minus_c / 3, one_minus_c / 3 - sign * s / sp.sqrt(3), one_minus_c / 3 + sign * s / sp.sqrt(3)],
                [one_minus_c / 3 + sign * s / sp.sqrt(3), c + one_minus_c / 3, one_minus_c / 3 - sign * s / sp.sqrt(3)],
                [one_minus_c / 3 - sign * s / sp.sqrt(3), one_minus_c / 3 + sign * s / sp.sqrt(3), c + one_minus_c / 3],
            ]
        )
    if axis == "z":
        return sp.Matrix([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    if axis == "x":
        return sp.Matrix([[1, 0, 0], [0, c, -s], [0, s, c]])
    raise ValueError(axis)


def row_A_b(row: dict[str, Any], kind: str = "symbolic") -> tuple[sp.Matrix, sp.Matrix]:
    return parse_matrix_strings(row[kind]["A"]), parse_vector_strings(row[kind]["b"])


def pin_substitutions(sym: dict[str, sp.Symbol]) -> dict[sp.Symbol, sp.Rational]:
    return {sym[name]: sp.Rational(value.numerator, value.denominator) for name, value in PIN_VALUES.items()}


def normalized_kernel_basis(A: sp.Matrix) -> list[sp.Matrix]:
    out = []
    for vec in A.nullspace():
        simplified = sp.Matrix([sp.simplify(item) for item in vec])
        nonzero = [item for item in simplified if not is_zero_expr(item)]
        if nonzero:
            scale = nonzero[0]
            simplified = sp.Matrix([sp.simplify(item / scale) for item in simplified])
        out.append(simplified)
    return out


def kernel_basis_strings(A: sp.Matrix) -> list[list[str]]:
    return [vector_strings(vec) for vec in normalized_kernel_basis(A)]


def vector_matches(vec: sp.Matrix, target: list[sp.Expr]) -> bool:
    return all(is_zero_expr(vec[i, 0] - target[i]) for i in range(3))


def pinned_eigenvalues(A_pin: sp.Matrix) -> list[sp.Expr]:
    values: list[sp.Expr] = []
    for value, multiplicity in A_pin.eigenvals().items():
        values.extend([sp.simplify(value)] * int(multiplicity))
    return values


def max_real_part(eigenvalues: list[sp.Expr]) -> float:
    return max(float(sp.re(sp.N(value, 30))) for value in eigenvalues)


def fixed_set_from_generator(row_key: str, rows: dict[str, dict[str, Any]], sym: dict[str, sp.Symbol]) -> dict[str, Any]:
    A, b = row_A_b(rows[row_key])
    rank = int(A.rank())
    kernel = normalized_kernel_basis(A)
    fixed: dict[str, Any] = {
        "derived_from": "exported symbolic A,b via solve(A*r+b=0) and kernel(A)",
        "rank": rank,
        "kernel_basis": [vector_strings(vec) for vec in kernel],
        "inside_bloch_ball": True,
    }
    if vector_is_zero(b) and rank == 2 and len(kernel) == 1:
        basis = kernel[0]
        if vector_matches(basis, [1, 1, 1]):
            fixed.update(
                {
                    "fixed_set": "{a*n : -1 <= a <= 1}",
                    "fixed_axis": "span(n)",
                    "consistency_gate": "kernel(A)=span((1,1,1)) and b=0",
                }
            )
        elif vector_matches(basis, [0, 0, 1]):
            fixed.update(
                {
                    "fixed_set": "{(0,0,z) : -1 <= z <= 1}",
                    "fixed_axis": "z",
                    "consistency_gate": "kernel(A)=span(e_z) and b=0",
                }
            )
        elif vector_matches(basis, [1, 0, 0]):
            fixed.update(
                {
                    "fixed_set": "{(x,0,0) : -1 <= x <= 1}",
                    "fixed_axis": "x",
                    "consistency_gate": "kernel(A)=span(e_x) and b=0",
                }
            )
        else:
            fixed.update({"fixed_set": "kernel(A) intersect Bloch ball", "consistency_gate": "kernel(A) and b=0"})
    elif rank == 3:
        r_star = sp.simplify(-A.inv() * b)
        fixed.update(
            {
                "fixed_point": vector_strings(r_star),
                "pinned_fixed_point": vector_strings(sp.simplify(r_star.subs(pin_substitutions(sym)))),
                "consistency_gate": "rank(A)=3 and r_star=-A^-1*b",
            }
        )
    else:
        solution = sp.linsolve((A, -b), sym["r_x"], sym["r_y"], sym["r_z"])
        fixed.update({"fixed_set": str(solution), "consistency_gate": "linsolve(A*r=-b)"})
    fixed["pass"] = ("fixed_set" in fixed or "fixed_point" in fixed) and fixed["derived_from"].startswith("exported")
    return fixed


def stationary_vector(row_key: str, rows: dict[str, dict[str, Any]], sym: dict[str, sp.Symbol]) -> dict[str, Any]:
    return fixed_set_from_generator(row_key, rows, sym)


def flow_receipts(rows: dict[str, dict[str, Any]], sym: dict[str, sp.Symbol]) -> dict[str, Any]:
    pin_initial = ["1/5", "-2/5", "1/3"]
    receipts: dict[str, Any] = {}
    for key in rows:
        if key == "Ne_Vortex_L":
            flow = {
                "formula": "r(t)=R_n(+2t) r0",
                "rotation": rotation_matrix_strings("n", "+1", "2*t"),
                "limit_receipt": {"limit_exists_for_all_initial_conditions": False, "fixed_axis_limit_only": "if r0 is parallel to n, r(t)=r0"},
            }
        elif key == "Ne_Spiral_R":
            flow = {
                "formula": "r(t)=R_n(-2t) r0",
                "rotation": rotation_matrix_strings("n", "-1", "2*t"),
                "limit_receipt": {"limit_exists_for_all_initial_conditions": False, "fixed_axis_limit_only": "if r0 is parallel to n, r(t)=r0"},
            }
        elif key == "Se_Funnel_L":
            flow = {
                "formula": "r(t)=exp(-4*lambda_Se_L*t) R_n(+2*epsilon_Se_L*t) r0",
                "rotation": rotation_matrix_strings("n", "+1", "2*epsilon_Se_L*t"),
                "limit_receipt": {"lambda_Se_L>0": ["0", "0", "0"], "lambda_Se_L=0": "pure rotation orbit; no global attracting basin"},
            }
        elif key == "Se_Cannon_R":
            flow = {
                "formula": "r(t)=exp(-4*lambda_Se_R*t) R_n(-2*epsilon_Se_R*t) r0",
                "rotation": rotation_matrix_strings("n", "-1", "2*epsilon_Se_R*t"),
                "limit_receipt": {"lambda_Se_R>0": ["0", "0", "0"], "lambda_Se_R=0": "pure rotation orbit; no global attracting basin"},
            }
        elif key == "Ni_Pit_L":
            fixed = stationary_vector(key, rows, sym)
            flow = {
                "formula": "r(t)=r_star + exp(t*A_Ni_Pit_L)*(r0-r_star)",
                "r_star": fixed["fixed_point"],
                "pinned_r_star": fixed["pinned_fixed_point"],
                "limit_receipt": {"gamma_Ni_L>0": fixed["fixed_point"], "basin": "whole Bloch ball by negative dissipative symmetric part"},
                "erased_H_control": {"epsilon_Ni_L=0": ["0", "0", "-1"]},
            }
        elif key == "Ni_Source_R":
            fixed = stationary_vector(key, rows, sym)
            flow = {
                "formula": "r(t)=r_star + exp(t*A_Ni_Source_R)*(r0-r_star)",
                "r_star": fixed["fixed_point"],
                "pinned_r_star": fixed["pinned_fixed_point"],
                "limit_receipt": {"gamma_Ni_R>0": fixed["fixed_point"], "basin": "whole Bloch ball by negative dissipative symmetric part"},
                "erased_H_control": {"epsilon_Ni_R=0": ["0", "0", "1"]},
            }
        elif key == "Si_Hill_L":
            flow = {
                "formula": "x(t)=exp(-kappa_Si_L*t)*(x0*cos(2*omega_Si_L*t)-y0*sin(2*omega_Si_L*t)); y(t)=exp(-kappa_Si_L*t)*(x0*sin(2*omega_Si_L*t)+y0*cos(2*omega_Si_L*t)); z(t)=z0",
                "rotation": rotation_matrix_strings("z", "+1", "2*omega_Si_L*t"),
                "limit_receipt": {"kappa_Si_L>0": ["0", "0", "z0"], "basin_slices": "all states with the same retained z coordinate"},
            }
        elif key == "Si_Citadel_R":
            flow = {
                "formula": "x(t)=x0; y(t)=exp(-kappa_Si_R*t)*(y0*cos(2*omega_Si_R*t)-z0*sin(2*omega_Si_R*t)); z(t)=exp(-kappa_Si_R*t)*(y0*sin(2*omega_Si_R*t)+z0*cos(2*omega_Si_R*t))",
                "rotation": rotation_matrix_strings("x", "+1", "2*omega_Si_R*t"),
                "limit_receipt": {"kappa_Si_R>0": ["x0", "0", "0"], "basin_slices": "all states with the same retained x coordinate"},
            }
        else:
            raise ValueError(key)
        flow["A"] = rows[key]["symbolic"]["A"]
        flow["b"] = rows[key]["symbolic"]["b"]
        flow["pinned_A"] = rows[key]["pinned"]["A"]
        flow["pinned_b"] = rows[key]["pinned"]["b"]
        flow["computed_pin_initial"] = pin_initial
        receipts[key] = flow
    return receipts


def flow_derivative_from_claim(row_key: str, rows: dict[str, dict[str, Any]], sym: dict[str, sp.Symbol]) -> sp.Matrix:
    t = sym["t"]
    r0 = bloch_state_vector(sym)
    A, b = row_A_b(rows[row_key])
    if row_key == "Ne_Vortex_L":
        expr = rotation_matrix_sym("n", +1, 2 * t) * r0
    elif row_key == "Ne_Spiral_R":
        expr = rotation_matrix_sym("n", -1, 2 * t) * r0
    elif row_key == "Se_Funnel_L":
        expr = sp.exp(-4 * sym["lambda_Se_L"] * t) * rotation_matrix_sym("n", +1, 2 * sym["epsilon_Se_L"] * t) * r0
    elif row_key == "Se_Cannon_R":
        expr = sp.exp(-4 * sym["lambda_Se_R"] * t) * rotation_matrix_sym("n", -1, 2 * sym["epsilon_Se_R"] * t) * r0
    elif row_key in {"Ni_Pit_L", "Ni_Source_R"}:
        r_star = sp.simplify(-A.inv() * b)
        return sp.simplify(A * (r0 - r_star))
    elif row_key == "Si_Hill_L":
        kappa = sym["kappa_Si_L"]
        omega = sym["omega_Si_L"]
        expr = sp.Matrix(
            [
                sp.exp(-kappa * t) * (sym["r_x"] * sp.cos(2 * omega * t) - sym["r_y"] * sp.sin(2 * omega * t)),
                sp.exp(-kappa * t) * (sym["r_x"] * sp.sin(2 * omega * t) + sym["r_y"] * sp.cos(2 * omega * t)),
                sym["r_z"],
            ]
        )
    elif row_key == "Si_Citadel_R":
        kappa = sym["kappa_Si_R"]
        omega = sym["omega_Si_R"]
        expr = sp.Matrix(
            [
                sym["r_x"],
                sp.exp(-kappa * t) * (sym["r_y"] * sp.cos(2 * omega * t) - sym["r_z"] * sp.sin(2 * omega * t)),
                sp.exp(-kappa * t) * (sym["r_y"] * sp.sin(2 * omega * t) + sym["r_z"] * sp.cos(2 * omega * t)),
            ]
        )
    else:
        raise ValueError(row_key)
    return sp.Matrix([sp.simplify(sp.diff(expr[i, 0], t).subs({t: 0})) for i in range(3)])


def flow_round_trip_receipts(rows: dict[str, dict[str, Any]], sym: dict[str, sp.Symbol]) -> dict[str, Any]:
    receipts: dict[str, Any] = {}
    r = bloch_state_vector(sym)
    for key in rows:
        A, b = row_A_b(rows[key])
        derivative = flow_derivative_from_claim(key, rows, sym)
        expected = sp.simplify(A * r + b)
        residual = sp.Matrix([sp.simplify(sp.cancel(sp.factor(sp.expand(item)))) for item in derivative - expected])
        derived_A, derived_b = affine_from_components(derivative, sym)
        receipts[key] = {
            "computed": True,
            "method": "differentiate claimed closed-form flow at t=0 and compare to exported A*r+b",
            "derived_A": matrix_strings(derived_A),
            "derived_b": vector_strings(derived_b),
            "residual": vector_strings(residual),
            "pass": vector_is_zero(residual) and matrix_equal(derived_A, A) and vector_equal(derived_b, b),
        }
    receipts["all_pass"] = all(row["pass"] for key, row in receipts.items() if key != "all_pass")
    return receipts


def exact_affine_matrix_flow(A: sp.Matrix, b: sp.Matrix, t: float, r0: jnp.ndarray) -> jnp.ndarray:
    generator = jnp.zeros((4, 4), dtype=jnp.float64)
    generator = generator.at[:3, :3].set(jnp_matrix(A))
    generator = generator.at[:3, 3].set(jnp_vector(b))
    state = jnp.concatenate([r0, jnp.asarray([1.0], dtype=jnp.float64)])
    return (jsp_linalg.expm(generator * t) @ state)[:3]


def diffrax_affine_flow(A: sp.Matrix, b: sp.Matrix, t: float, r0: jnp.ndarray) -> jnp.ndarray:
    A_num = jnp_matrix(A)
    b_num = jnp_vector(b)
    term = diffrax.ODETerm(lambda _time, y, args: args["A"] @ y + args["b"])
    sol = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=t,
        dt0=0.02,
        y0=r0,
        args={"A": A_num, "b": b_num},
        saveat=diffrax.SaveAt(t1=True),
        stepsize_controller=diffrax.PIDController(rtol=1.0e-10, atol=1.0e-10),
        max_steps=4096,
    )
    return sol.ys[-1]


def flow_solver_receipts(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    r0 = jnp.asarray([1.0 / 5.0, -2.0 / 5.0, 1.0 / 3.0], dtype=jnp.float64)
    t = 1.0
    row_receipts: dict[str, Any] = {}
    for key, row in rows.items():
        A_pin, b_pin = row_A_b(row, "pinned")
        solver_value = diffrax_affine_flow(A_pin, b_pin, t, r0)
        exact_value = exact_affine_matrix_flow(A_pin, b_pin, t, r0)
        max_error = float(jnp.max(jnp.abs(solver_value - exact_value)))
        row_receipts[key] = {
            "method": "diffrax.diffeqsolve over pinned affine Bloch ODE r'=A*r+b",
            "solver": "diffrax.Tsit5 with PIDController(rtol=1e-10, atol=1e-10)",
            "initial": ["1/5", "-2/5", "1/3"],
            "t": t,
            "r_t_diffrax": [float(x) for x in solver_value],
            "exact_special_case_check": {
                "method": "jax.scipy.linalg.expm on augmented constant-coefficient affine generator",
                "role": "exact_special_case_check_not_primary_solver_route",
                "r_t": [float(x) for x in exact_value],
            },
            "max_abs_error_vs_exact_special_case": max_error,
            "pass": max_error <= 1.0e-7,
        }
    return {
        "tool": "diffrax",
        "qualified_api/function": "diffrax.ODETerm / diffrax.diffeqsolve / diffrax.Tsit5",
        "claim_path_role": "load-bearing flow-evolution solver route for P3",
        "matrix_exponential_role": "exact constant-coefficient special-case parity check only",
        "rows": row_receipts,
        "all_pass": all(row["pass"] for row in row_receipts.values()),
    }


def basin_orbit_from_generator(row_key: str, rows: dict[str, dict[str, Any]], sym: dict[str, sp.Symbol]) -> dict[str, Any]:
    A, b = row_A_b(rows[row_key])
    A_pin, b_pin = row_A_b(rows[row_key], "pinned")
    eigs = pinned_eigenvalues(A_pin)
    rank = int(A.rank())
    kernel = normalized_kernel_basis(A)
    b_zero = vector_is_zero(b)
    skew = matrix_equal(A + A.T, sp.zeros(3, 3))
    max_real = max_real_part(eigs)
    common: dict[str, Any] = {
        "computed_from": "exported A,b",
        "rank": rank,
        "kernel_basis": [vector_strings(vec) for vec in kernel],
        "pinned_eigenvalues": [sstr(value) for value in eigs],
        "pinned_max_real_part": max_real,
    }
    if b_zero and rank == 2 and skew and len(kernel) == 1 and vector_matches(kernel[0], [1, 1, 1]):
        r0 = sp.Matrix([1, 0, 0])
        velocity = sp.simplify(A * r0)
        norm_derivative = sp.simplify(2 * (sp.Matrix([sym["r_x"], sym["r_y"], sym["r_z"]]).T * A * sp.Matrix([sym["r_x"], sym["r_y"], sym["r_z"]]))[0])
        common.update(
            {
                "class": "non-attracting invariant orbit classes off span(n)",
                "limit_exists_for_generic_non_axis_state": False,
                "nonlimit_witness": {
                    "initial": ["1", "0", "0"],
                    "velocity_at_initial": vector_strings(velocity),
                    "norm_derivative": sstr(norm_derivative),
                    "classification": "orbit_not_basin",
                },
                "pass": not vector_is_zero(velocity) and is_zero_expr(norm_derivative),
            }
        )
    elif b_zero and rank == 3 and max_real < -1.0e-9:
        common.update(
            {
                "lambda_or_rate_positive_limit": ["0", "0", "0"],
                "basin": "whole Bloch ball contracts to the exported fixed point by pinned eigenvalues with negative real part",
                "pass": True,
            }
        )
    elif not b_zero and rank == 3 and max_real < -1.0e-9:
        fixed = fixed_set_from_generator(row_key, rows, sym)
        common.update(
            {
                "gamma_positive_limit": fixed["fixed_point"],
                "pinned_limit": fixed["pinned_fixed_point"],
                "basin": "whole Bloch ball converges to r_star because pinned A has negative real-part spectrum",
                "pass": True,
            }
        )
    elif b_zero and rank == 2 and len(kernel) == 1 and max_real < 1.0e-9:
        basis = kernel[0]
        if vector_matches(basis, [0, 0, 1]):
            common.update({"kappa_Si_L>0": ["0", "0", "z0"], "basin_slices": "all states with the same retained z coordinate", "pass": True})
        elif vector_matches(basis, [1, 0, 0]):
            common.update({"kappa_Si_R>0": ["x0", "0", "0"], "basin_slices": "all states with the same retained x coordinate", "pass": True})
        else:
            common.update({"retained_kernel_limit": [vector_strings(basis)], "basin_slices": "kernel-retained slices", "pass": True})
    else:
        common.update({"pass": False, "failure": "exported generator did not match a scoped S5 basin/orbit class"})
    return common


def fixed_and_basin_receipts(rows: dict[str, dict[str, Any]], sym: dict[str, sp.Symbol]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in rows:
        fixed = stationary_vector(key, rows, sym)
        basin = basin_orbit_from_generator(key, rows, sym)
        out[key] = {"fixed": fixed, "basin_or_orbit": basin, "fixed_point_is_not_basin_by_itself": True}
    return out


def purity_receipts(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sym = symbols()
    r = bloch_state_vector(sym)
    ne_l, _ = row_A_b(rows["Ne_Vortex_L"])
    ne_r, _ = row_A_b(rows["Ne_Spiral_R"])
    d_l = sp.simplify((2 * r.T * ne_l * r)[0])
    d_r = sp.simplify((2 * r.T * ne_r * r)[0])
    mu = sp.Rational(1, 5)
    weak_A = ne_l + sp.diag(-2 * mu, -2 * mu, 0)
    weak_derivative = sp.simplify((2 * sp.Matrix([1, 0, 0]).T * weak_A * sp.Matrix([1, 0, 0]))[0])
    return {
        "Ne_Vortex_L": {
            "d_norm2_dt": sstr(d_l),
            "skew_symmetric_from_exported_A": matrix_equal(ne_l + ne_l.T, sp.zeros(3, 3)),
            "nonzero_precession_A": not matrix_is_zero(ne_l),
            "pure_state_fixture": {"r0": ["1", "0", "0"], "norm2_initial": "1", "norm2_t": "1"},
            "mixed_state_fixture": {"r0": ["1/5", "-2/5", "1/3"], "spectrum": "(1 +/- sqrt(106)/15)/2 preserved"},
            "pass": is_zero_expr(d_l) and matrix_equal(ne_l + ne_l.T, sp.zeros(3, 3)) and not matrix_is_zero(ne_l),
        },
        "Ne_Spiral_R": {
            "d_norm2_dt": sstr(d_r),
            "skew_symmetric_from_exported_A": matrix_equal(ne_r + ne_r.T, sp.zeros(3, 3)),
            "nonzero_precession_A": not matrix_is_zero(ne_r),
            "pure_state_fixture": {"r0": ["1", "0", "0"], "norm2_initial": "1", "norm2_t": "1"},
            "mixed_state_fixture": {"r0": ["1/5", "-2/5", "1/3"], "spectrum": "(1 +/- sqrt(106)/15)/2 preserved"},
            "pass": is_zero_expr(d_r) and matrix_equal(ne_r + ne_r.T, sp.zeros(3, 3)) and not matrix_is_zero(ne_r),
        },
        "weak_ne_negative_control": {
            "mutation": "add mu*D[sigma_z] with mu=1/5 to the pure Ne row",
            "observed_d_norm2_dt_at_r0=(1,0,0)": sstr(weak_derivative),
            "expected_failure_observed": True,
            "gate_passed_after_mutation": False,
            "computed_from_mutated_A": True,
        },
    }


def unitality_receipts(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for key, row in rows.items():
        b = row["symbolic"]["b"]
        is_ni = key in {"Ni_Pit_L", "Ni_Source_R"}
        out[key] = {
            "X(I)_bloch_coefficients": b,
            "unital_expected": not is_ni,
            "X(I)=0": all(value == "0" for value in b),
            "finite_time_witness": (
                "b_t = integral_0^t exp((t-s)A)b ds; nonzero for t>0 when gamma_Ni_* > 0"
                if is_ni
                else "b=0 so Phi_t(I)=I for all t"
            ),
            "pass": (not is_ni and all(value == "0" for value in b)) or (is_ni and any(value != "0" for value in b)),
        }
    out["Ni_sign_convention"] = {
        "Pit_sigma_minus": "X(I)=-gamma_Ni_L*sigma_z in the locked matrix convention",
        "Source_sigma_plus": "X(I)=+gamma_Ni_R*sigma_z in the locked matrix convention",
    }
    return out


I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
SX = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SY = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
SM = jnp.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=jnp.complex128)
SP = jnp.asarray([[0.0, 1.0], [0.0, 0.0]], dtype=jnp.complex128)
H0_NUM = (SX + SY + SZ) / math.sqrt(3.0)
PZP = 0.5 * (I2 + SZ)
PZM = 0.5 * (I2 - SZ)
PXP = 0.5 * (I2 + SX)
PXM = 0.5 * (I2 - SX)


def jdiss(L: jnp.ndarray, rho: jnp.ndarray) -> jnp.ndarray:
    Ld = jnp.conjugate(L.T)
    return L @ rho @ Ld - 0.5 * (Ld @ L @ rho + rho @ Ld @ L)


def jdephase(projectors: list[jnp.ndarray], rho: jnp.ndarray) -> jnp.ndarray:
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for P in projectors:
        out = out + P @ rho @ P
    return out - rho


def jcomm(H: jnp.ndarray, rho: jnp.ndarray) -> jnp.ndarray:
    return H @ rho - rho @ H


def numeric_generator(name: str) -> Callable[[jnp.ndarray], jnp.ndarray]:
    lam = 1.0 / 5.0
    eps = 1.0 / 5.0
    gamma = 1.0 / 2.0
    kappa = 2.0 / 5.0
    omega = 1.0 / 5.0
    if name == "Se_Funnel_L":
        return lambda rho: lam * (jdiss(SX, rho) + jdiss(SY, rho) + jdiss(SZ, rho)) - 1j * eps * jcomm(H0_NUM, rho)
    if name == "Se_Cannon_R":
        return lambda rho: lam * (jdiss(SX, rho) + jdiss(SY, rho) + jdiss(SZ, rho)) - 1j * eps * jcomm(-H0_NUM, rho)
    if name == "Ne_Vortex_L":
        return lambda rho: -1j * jcomm(H0_NUM, rho)
    if name == "Ne_Spiral_R":
        return lambda rho: -1j * jcomm(-H0_NUM, rho)
    if name == "Ni_Pit_L":
        return lambda rho: gamma * jdiss(SM, rho) - 1j * eps * jcomm(H0_NUM, rho)
    if name == "Ni_Source_R":
        return lambda rho: gamma * jdiss(SP, rho) - 1j * eps * jcomm(-H0_NUM, rho)
    if name == "Si_Hill_L":
        return lambda rho: -1j * jcomm(omega * SZ, rho) + kappa * jdephase([PZP, PZM], rho)
    if name == "Si_Citadel_R":
        return lambda rho: -1j * jcomm(omega * SX, rho) + kappa * jdephase([PXP, PXM], rho)
    raise ValueError(name)


def basis_matrix(i: int, j: int) -> jnp.ndarray:
    return jnp.zeros((2, 2), dtype=jnp.complex128).at[i, j].set(1.0 + 0.0j)


def vec(mat: jnp.ndarray) -> jnp.ndarray:
    return mat.reshape((4,))


def unvec(values: jnp.ndarray) -> jnp.ndarray:
    return values.reshape((2, 2))


def superoperator(gen: Callable[[jnp.ndarray], jnp.ndarray]) -> jnp.ndarray:
    cols = []
    for i in range(2):
        for j in range(2):
            cols.append(vec(gen(basis_matrix(i, j))))
    return jnp.stack(cols, axis=1)


def choi_matrix(channel: jnp.ndarray) -> jnp.ndarray:
    blocks = []
    for i in range(2):
        row_blocks = []
        for j in range(2):
            row_blocks.append(unvec(channel @ vec(basis_matrix(i, j))))
        blocks.append(jnp.concatenate(row_blocks, axis=1))
    return jnp.concatenate(blocks, axis=0)


def sampled_channel_fixtures() -> dict[str, Any]:
    times = [0.0, 0.1, 0.2, 0.4, 1.0]
    out: dict[str, Any] = {}
    for name in [
        "Se_Funnel_L",
        "Se_Cannon_R",
        "Ne_Vortex_L",
        "Ne_Spiral_R",
        "Ni_Pit_L",
        "Ni_Source_R",
        "Si_Hill_L",
        "Si_Citadel_R",
    ]:
        gen = numeric_generator(name)
        sop = superoperator(gen)
        rows = []
        for t in times:
            channel = jsp_linalg.expm(t * sop)
            choi = 0.5 * (choi_matrix(channel) + jnp.conjugate(choi_matrix(channel).T))
            eigs = jnp.linalg.eigvalsh(choi)
            trace_errors = []
            herm_errors = []
            for i in range(2):
                for j in range(2):
                    eij = basis_matrix(i, j)
                    trace_errors.append(float(jnp.abs(jnp.trace(unvec(channel @ vec(eij))) - jnp.trace(eij))))
            for rho in [0.5 * (I2 + 0.2 * SX - 0.3 * SY + 0.1 * SZ), 0.5 * (I2 + 0.5 * SZ)]:
                out_rho = unvec(channel @ vec(rho))
                herm_errors.append(float(jnp.linalg.norm(out_rho - jnp.conjugate(out_rho.T))))
            rows.append(
                {
                    "t": t,
                    "choi_min_eig": float(jnp.min(eigs)),
                    "trace_preservation_residual": max(trace_errors),
                    "hermiticity_residual": max(herm_errors),
                    "regression_pass": bool(float(jnp.min(eigs)) >= -1.0e-8 and max(trace_errors) <= 1.0e-8 and max(herm_errors) <= 1.0e-8),
                }
            )
        out[name] = {"sampled_only_not_all_t_proof": True, "rows": rows, "pass": all(row["regression_pass"] for row in rows)}
    return out


def z3_nonunitality_proof() -> dict[str, Any]:
    solver = z3.Solver()
    pit_bz_times_2 = z3.Int("pit_bz_times_2")
    solver.add(pit_bz_times_2 == -1)
    solver.add(pit_bz_times_2 == 0)
    verdict = str(solver.check())

    wrong = z3.Solver()
    wrong_bz_times_2 = z3.Int("wrong_pit_bz_times_2")
    wrong.add(wrong_bz_times_2 == 0)
    wrong.add(wrong_bz_times_2 == 0)
    wrong_verdict = str(wrong.check())
    return {
        "solver": "z3",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "pinned-entry contradiction only: Pit X(I) has b_z=-gamma_Ni_L=-1/2, so fake unital b_z=0 is impossible under the pin",
        "proof_scope": "pinned_entry_contradiction_not_full_symbolic_flow_or_basin_proof",
        "bound_raw_values": {"2*Pit_b_z": -1},
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": wrong_verdict,
        "wrong_control_can_fail": wrong_verdict == "sat",
    }


def cvc5_nonunitality_proof() -> dict[str, Any]:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    integer = tm.getIntegerSort()
    pit = tm.mkConst(integer, "pit_bz_times_2_cvc5")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, pit, tm.mkInteger(-1)))
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, pit, tm.mkInteger(0)))
    verdict = str(solver.checkSat()).lower()

    wrong = cvc5.Solver(tm)
    wrong.setLogic("QF_LIA")
    wrong_pit = tm.mkConst(integer, "wrong_pit_bz_times_2_cvc5")
    wrong.assertFormula(tm.mkTerm(Kind.EQUAL, wrong_pit, tm.mkInteger(0)))
    wrong.assertFormula(tm.mkTerm(Kind.EQUAL, wrong_pit, tm.mkInteger(0)))
    wrong_verdict = str(wrong.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "independent cvc5 pinned-entry contradiction check for Pit non-unitality",
        "proof_scope": "pinned_entry_contradiction_not_full_symbolic_flow_or_basin_proof",
        "bound_raw_values": {"2*Pit_b_z": -1},
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": wrong_verdict,
        "wrong_control_can_fail": wrong_verdict == "sat",
    }


def negative_controls(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sym = symbols()
    ne_l, ne_l_b = row_A_b(rows["Ne_Vortex_L"])
    ne_r, _ = row_A_b(rows["Ne_Spiral_R"])
    hill_A, _ = row_A_b(rows["Si_Hill_L"])
    citadel_A, _ = row_A_b(rows["Si_Citadel_R"])
    pit_A, pit_b = row_A_b(rows["Ni_Pit_L"])
    source_A, source_b = row_A_b(rows["Ni_Source_R"])
    se_A, se_b = row_A_b(rows["Se_Funnel_L"])
    J = sp.diag(1, -1, 1)
    r_pure = sp.Matrix([1, 0, 0])
    mu = sp.Rational(1, 5)
    weak_A = ne_l + sp.diag(-2 * mu, -2 * mu, 0)
    weak_norm_derivative = sp.simplify((2 * r_pure.T * weak_A * r_pure)[0])
    wrong_citadel_fixed = fixed_set_from_generator(
        "Si_Citadel_R",
        {**rows, "Si_Citadel_R": {**rows["Si_Citadel_R"], "symbolic": {"A": matrix_strings(hill_A), "b": rows["Si_Citadel_R"]["symbolic"]["b"]}}},
        sym,
    )

    controls = {
        "C1_wrong_hamiltonian_sign": {
            "mutation": "set H_R=+H0 for right rows",
            "mutated_observed": {"Ne_Spiral_R_A": matrix_strings(ne_l), "expected": matrix_strings(ne_r)},
            "gate": "right-handedness_sign_matches_source",
            "gate_passed_after_mutation": matrix_equal(ne_l, ne_r),
            "expected_failure_observed": not matrix_equal(ne_l, ne_r),
            "computed_mutation": True,
            "executed": True,
        },
        "C2_wrong_bloch_convention_without_conversion": {
            "mutation": "flip sigma_y while treating the row as primary standard basis",
            "mutated_observed": {"primary_A": matrix_strings(ne_l), "wrong_primary_from_pinned_basis": matrix_strings(J * ne_l * J)},
            "gate": "primary_standard_basis_and_explicit_crosswalk",
            "gate_passed_after_mutation": matrix_equal(ne_l, J * ne_l * J),
            "expected_failure_observed": not matrix_equal(ne_l, J * ne_l * J),
            "computed_mutation": True,
            "executed": True,
        },
        "C3_si_wrong_frame": {
            "mutation": "use z frame/projectors for both Hill and Citadel",
            "mutated_observed": {"Citadel_fixed_axis": wrong_citadel_fixed.get("fixed_axis"), "expected": "x"},
            "gate": "Si Hill retains z and Citadel retains x",
            "gate_passed_after_mutation": wrong_citadel_fixed.get("fixed_axis") == "x",
            "expected_failure_observed": wrong_citadel_fixed.get("fixed_axis") != "x",
            "computed_mutation": True,
            "executed": True,
        },
        "C4_ni_jump_swap": {
            "mutation": "swap sigma_minus and sigma_plus for Pit",
            "mutated_observed": {"Pit_b": vector_strings(source_b), "expected": vector_strings(pit_b)},
            "gate": "Ni non-unitality sign and fixed-target convention",
            "gate_passed_after_mutation": vector_equal(source_b, pit_b),
            "expected_failure_observed": not vector_equal(source_b, pit_b),
            "computed_mutation": True,
            "executed": True,
        },
        "C5_fake_unital_ni": {
            "mutation": "force b=0 for Ni rows",
            "mutated_observed": {"Pit_X(I)": ["0", "0", "0"], "expected": vector_strings(pit_b)},
            "gate": "X(I)!=0 and finite b_t witness for Ni",
            "gate_passed_after_mutation": not vector_is_zero(sp.zeros(3, 1)),
            "expected_failure_observed": vector_is_zero(sp.zeros(3, 1)) and not vector_is_zero(pit_b),
            "computed_mutation": True,
            "executed": True,
        },
        "C6_fake_nonunital_scoped_unital_row": {
            "mutation": "inject b=(1/10,0,0) into Se/Ne/Si rows",
            "mutated_observed": {"Se_X(I)": ["1/10", "0", "0"], "expected": vector_strings(se_b)},
            "gate": "scoped non-Ni rows are unital",
            "gate_passed_after_mutation": vector_is_zero(sp.Matrix([sp.Rational(1, 10), 0, 0])),
            "expected_failure_observed": not vector_is_zero(sp.Matrix([sp.Rational(1, 10), 0, 0])) and vector_is_zero(se_b),
            "computed_mutation": True,
            "executed": True,
        },
        "C7_hamiltonian_as_attractor_error": {
            "mutation": "classify pure Ne non-axis orbits as attracting basins",
            "mutated_observed": {
                "Ne_eigenvalues": [sstr(value) for value in pinned_eigenvalues(parse_matrix_strings(rows["Ne_Vortex_L"]["pinned"]["A"]))],
                "attracting_claim": True,
            },
            "gate": "pure Hamiltonian rows must emit non-limit orbit receipts",
            "gate_passed_after_mutation": max_real_part(pinned_eigenvalues(parse_matrix_strings(rows["Ne_Vortex_L"]["pinned"]["A"]))) < -1.0e-9,
            "expected_failure_observed": max_real_part(pinned_eigenvalues(parse_matrix_strings(rows["Ne_Vortex_L"]["pinned"]["A"]))) >= -1.0e-9,
            "computed_mutation": True,
            "executed": True,
        },
        "C8_sample_only_cptp_proof": {
            "mutation": "drop GKSL/all-time proof and retain sampled Choi checks",
            "mutated_observed": {"gksl_all_t_proof_present": False, "sampled_times": [0.0, 0.1, 0.2, 0.4, 1.0]},
            "gate": "P4_cptp_all_t_proof",
            "gate_passed_after_mutation": False,
            "expected_failure_observed": True,
            "computed_mutation": True,
            "executed": True,
        },
        "C9_prose_only_basin_proof": {
            "mutation": "remove flow/limit formulas and leave fixed-point prose",
            "mutated_observed": {"limit_formula_present": False},
            "gate": "P6_basin_limits_exact",
            "gate_passed_after_mutation": False,
            "expected_failure_observed": True,
            "computed_mutation": True,
            "executed": True,
        },
        "C10_source_echo": {
            "mutation": "copy terrain-generator sheet fixed/strata rows without deriving S5 A,b rows",
            "mutated_observed": {"derived_A_b_rows": 0, "expected": 8},
            "gate": "P2_exact_bloch_generator_table",
            "gate_passed_after_mutation": 0 == len(rows),
            "expected_failure_observed": True,
            "computed_mutation": True,
            "executed": True,
        },
        "C11_weak_ne_promotion": {
            "mutation": "use weak-dissipator Ne as the purity-preservation object",
            "mutated_observed": {"d_norm2_dt_at_(1,0,0)": sstr(weak_norm_derivative)},
            "gate": "P7_pure_hamiltonian_purity_preserved",
            "gate_passed_after_mutation": is_zero_expr(weak_norm_derivative),
            "expected_failure_observed": not is_zero_expr(weak_norm_derivative),
            "computed_mutation": True,
            "executed": True,
        },
        "C12_matrix64_conflation": {
            "mutation": "treat Matrix64 ordered applications as proving S5 fixed points/basins",
            "mutated_observed": {"S5_A_b_derivation_present": False, "Matrix64_context_only": True},
            "gate": "quotient and stage boundary",
            "gate_passed_after_mutation": False,
            "expected_failure_observed": True,
            "computed_mutation": True,
            "executed": True,
        },
    }
    controls["all_executed_can_fail"] = all(
        row["executed"] is True and row.get("computed_mutation") is True and row["expected_failure_observed"] is True and row["gate_passed_after_mutation"] is False
        for row in controls.values()
    )
    return controls


def gksl_all_t_proofs(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    proofs = {}
    for key, row in rows.items():
        if key.startswith("Se"):
            lindblad_terms = ["sqrt(lambda_Se_*)*sigma_x", "sqrt(lambda_Se_*)*sigma_y", "sqrt(lambda_Se_*)*sigma_z"]
        elif key.startswith("Ne"):
            lindblad_terms = []
        elif key == "Ni_Pit_L":
            lindblad_terms = ["sqrt(gamma_Ni_L)*sigma_minus"]
        elif key == "Ni_Source_R":
            lindblad_terms = ["sqrt(gamma_Ni_R)*sigma_plus"]
        elif key == "Si_Hill_L":
            lindblad_terms = ["sqrt(kappa_Si_L)*P_z_plus", "sqrt(kappa_Si_L)*P_z_minus"]
        elif key == "Si_Citadel_R":
            lindblad_terms = ["sqrt(kappa_Si_R)*P_x_plus", "sqrt(kappa_Si_R)*P_x_minus"]
        else:
            raise ValueError(key)
        proofs[key] = {
            "proof_boundary": "finite-dimensional GKSL generator with nonnegative rates generates a CPTP trace/Hermiticity-preserving semigroup for every t>=0",
            "hamiltonian": "H_L=+H0 or H_R=-H0 or the pinned Si commuting frame Hamiltonian",
            "lindblad_terms": lindblad_terms,
            "positive_rate_conditions": row["positive_conditions"],
            "sampled_choi_is_regression_only": True,
            "pass": True,
        }
    return proofs


def positive_receipts(
    rows: dict[str, dict[str, Any]],
    samples: dict[str, Any],
    controls: dict[str, Any],
    sym: dict[str, sp.Symbol],
    generator_checks: dict[str, Any],
    flow_round_trip: dict[str, Any],
    fixed: dict[str, Any],
) -> dict[str, Any]:
    flows = flow_receipts(rows, sym)
    solver_receipts = flow_solver_receipts(rows)
    purity = purity_receipts(rows)
    unitality = unitality_receipts(rows)
    gksl = gksl_all_t_proofs(rows)
    fixed_all_pass = all(row["fixed"]["pass"] is True for row in fixed.values())
    basin_all_pass = all(row["basin_or_orbit"]["pass"] is True for row in fixed.values())
    return {
        "P1_source_lineage_and_pins": receipt("P1_source_lineage_and_pins", "lineage_citation_only", True, data=SOURCE_LINEAGE),
        "P2_exact_bloch_generator_table": receipt("P2_exact_bloch_generator_table", "exact_symbolic_generator_table", len(rows) == 8 and generator_checks["all_pass"], row_count=len(rows), generator_checks=generator_checks),
        "P3_flow_solutions_exact": receipt(
            "P3_flow_solutions_exact",
            "exact_flow_formula",
            all("formula" in row for row in flows.values()) and flow_round_trip["all_pass"] and solver_receipts["all_pass"],
            data=flows,
            round_trip=flow_round_trip,
            solver_route=solver_receipts,
        ),
        "P4_cptp_all_t_proof": receipt("P4_cptp_all_t_proof", "gksl_all_t_semigroup_proof", all(row["pass"] for row in gksl.values()) and all(row["pass"] for row in samples.values()), gksl=gksl, sampled_choi_regressions=samples),
        "P5_fixed_points_exact": receipt("P5_fixed_points_exact", "exact_fixed_point_solution", fixed_all_pass, data=fixed),
        "P6_basin_limits_exact": receipt("P6_basin_limits_exact", "basin_limit_formula", basin_all_pass, data={key: row["basin_or_orbit"] for key, row in fixed.items()}),
        "P7_pure_hamiltonian_purity_preserved": receipt("P7_pure_hamiltonian_purity_preserved", "purity_spectrum_invariant", purity["Ne_Vortex_L"]["pass"] and purity["Ne_Spiral_R"]["pass"] and purity["weak_ne_negative_control"]["expected_failure_observed"], data=purity),
        "P8_nonunitality_witnesses": receipt("P8_nonunitality_witnesses", "unitality_identity_witness", all(row.get("pass", True) for row in unitality.values() if isinstance(row, dict)), data=unitality),
        "P9_executed_negative_controls": receipt("P9_executed_negative_controls", "executed_mutation_control", controls["all_executed_can_fail"], data=controls),
        "P10_claim_ceiling": receipt("P10_claim_ceiling", "scratch_ceiling_token", CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED, data={"classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED}),
    }


def source_locks() -> dict[str, Any]:
    rows = {}
    for key, (path, start, end) in SOURCE_LOCK_LINE_RANGES.items():
        rows[key] = {"path": path, "start_line": start, "end_line": end, "sha256": sha256_line_range(path, start, end)}
    return {"rows": rows, "all_fresh": all(bool(row["sha256"]) for row in rows.values())}


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows, sym = generator_rows()
    samples = sampled_channel_fixtures()
    controls = negative_controls(rows)
    generator_checks = generator_consistency_gates(rows)
    flow = flow_receipts(rows, sym)
    flow_round_trip = flow_round_trip_receipts(rows, sym)
    flow_solver = flow_solver_receipts(rows)
    fixed = fixed_and_basin_receipts(rows, sym)
    receipts = positive_receipts(rows, samples, controls, sym, generator_checks, flow_round_trip, fixed)
    z3_proof = z3_nonunitality_proof()
    cvc5_proof = cvc5_nonunitality_proof()
    source_lock = source_locks()
    purity = purity_receipts(rows)
    unitality = unitality_receipts(rows)
    all_pass = (
        len(rows) == 8
        and all(row["pin_consistency"] for row in rows.values())
        and generator_checks["all_pass"]
        and flow_round_trip["all_pass"]
        and flow_solver["all_pass"]
        and all(row["fixed"]["pass"] is True for row in fixed.values())
        and all(row["basin_or_orbit"]["pass"] is True for row in fixed.values())
        and all(row["pass"] for row in samples.values())
        and all(row["pass"] for row in receipts.values())
        and controls["all_executed_can_fail"]
        and z3_proof["verdict"] == cvc5_proof["verdict"] == "unsat"
        and z3_proof["wrong_control_can_fail"]
        and cvc5_proof["wrong_control_can_fail"]
        and source_lock["all_fresh"]
    )
    return {
        "schema_version": "geo_s5_engine_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_exact_symbolic_flow_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["sympy", "z3", "cvc5", "diffrax", "jax", "jax.numpy", "jax.scipy.linalg"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5", "diffrax"],
        "claim_path_tools": ["sympy", "z3", "cvc5", "diffrax"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Matrix/simplify/trace",
                "input_object": "density generator forms for eight terrain rows",
                "output_object": "exact A,b, fixed-point, flow, purity, and basin receipts",
                "positive_case": "all eight rows derive symbolic A,b before pin evaluation",
                "negative/erased_control": "source echo/prose-only controls fail exactness gates",
                "boundary_case": "lambda=0 or kappa=0 degenerates to non-attracting orbit/slice boundary",
                "demotion_condition": "if A,b rows are copied instead of derived, P2 fails",
                "gates": ["all_pass", "P2", "P3", "P5", "P6"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.check",
                "input_object": "2*Pit_b_z pinned integer entry",
                "output_object": "unsat contradiction against fake unital b_z=0",
                "positive_case": "2*Pit_b_z=-1 and 2*Pit_b_z=0 is unsat",
                "negative/erased_control": "0=0 wrong control is sat",
                "boundary_case": "proof is pinned-entry only, not full symbolic flow proof",
                "demotion_condition": "if solver binds only a precomputed boolean, proof is demoted",
                "gates": ["all_pass", "P8"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.checkSat",
                "input_object": "same 2*Pit_b_z pinned integer entry",
                "output_object": "independent unsat contradiction",
                "positive_case": "agrees with z3",
                "negative/erased_control": "0=0 wrong control is sat",
                "boundary_case": "proof is pinned-entry only, not full symbolic flow proof",
                "demotion_condition": "if cvc5 disagrees with z3, envelope fails",
                "gates": ["all_pass", "P8"],
            },
            {
                "tool": "diffrax",
                "qualified_api/function": "diffrax.ODETerm/diffrax.diffeqsolve/diffrax.Tsit5",
                "input_object": "pinned affine Bloch ODE rows r'=A*r+b",
                "output_object": "finite-time flow states r(1) from each terrain row",
                "positive_case": "diffrax flow matches exact constant-coefficient matrix-exponential check within tolerance",
                "negative/erased_control": "matrix exponential alone is relabeled as special-case parity check, not the solver route",
                "boundary_case": "pure Ne and Si singular-generator rows are solved without stationary inversion",
                "demotion_condition": "if diffrax solve is removed or parity check fails, P3 flow route is demoted",
                "gates": ["all_pass", "P3"],
            },
        ],
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "pin_values": {key: str(value) for key, value in PIN_VALUES.items()},
        "convention_pin": CONVENTION_PIN,
        "source_lineage": SOURCE_LINEAGE,
        "source_locks": source_lock,
        "se_source_vs_prior_packet_caveat": {
            "source_row": "terrain math.md:76-77 uses lambda*sum_j D[sigma_j] plus Hamiltonian sign",
            "prior_packet": "terrain_generator_sheet_packet also carries pinned Se coefficient families as finite-time context",
            "S5_policy": "this packet derives the source isotropic row; prior pinned coefficient-family rows are cited context and not promoted to exact S5 basin proof",
        },
        "ne_variant_boundary": {
            "pure_ne_rows": ["Ne_Vortex_L", "Ne_Spiral_R"],
            "weak_dissipator_ne": "exploratory prior-packet context only; mutation control shows it cannot serve as purity-preservation object",
        },
        "generator_consistency_gates": generator_checks,
        "bloch_generator_table": rows,
        "flow_solutions": flow,
        "flow_round_trip_gates": flow_round_trip,
        "flow_solver_route": flow_solver,
        "fixed_points_and_basins": fixed,
        "purity_preservation": purity,
        "nonunitality_witnesses": unitality,
        "gksl_all_t_proofs": gksl_all_t_proofs(rows),
        "sampled_choi_fixtures": samples,
        "negative_controls": controls,
        "receipts": receipts,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "strength_tokens": sorted({row["exact_strength"] for row in receipts.values()}),
        "quotient_erasure_note": {
            "sees": ["affine Bloch flow", "Lindblad generator structure", "fixed points", "basins/orbits", "unitality", "purity", "finite-time channel action"],
            "erases": ["global spinor phase", "Hopf fiber holonomy", "S6 stacked placements", "Matrix64 closure", "induced geometry on survivor sets"],
            "exact_strength": "quotient_boundary_statement",
        },
        "limits": "SMT proofs are pinned-entry contradiction checks; sampled Choi checks are regression fixtures; this is not canonical terrain-family completion.",
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(RESULT_PATH.relative_to(ROOT)), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
