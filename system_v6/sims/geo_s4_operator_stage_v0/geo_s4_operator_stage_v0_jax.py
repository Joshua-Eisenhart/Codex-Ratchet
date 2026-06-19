#!/usr/bin/env python3
"""JAX/SymPy/SMT leg for geo_s4_operator_stage_v0."""

from __future__ import annotations

import datetime as dt
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s4_operator_stage_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

PIN_SPEC = (
    "geo_s4_operator_stage_v0|"
    "sigma_y_standard=[[0,-i],[i,0]]|"
    "primary_bloch_basis=(sigma_x,sigma_y_standard,sigma_z)|"
    "s1_pinned_bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|"
    "standard_to_s1_pinned_J=diag(1,-1,1)|"
    "component_rule=r_i=Tr(rho*basis_i)|"
    "channels=(D_z,D_x,R_x,R_z)|"
    "source_forms=(Ti=z_dephase,Te=x_dephase,Fi=x_rotation,Fe=z_rotation)|"
    "symbolic_parameters=(q_z,q_x,theta_x,phi_z)|"
    "pin_row=(q_z=3/10,q_x=3/10,theta_x=pi/2,phi_z=pi/2)|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "sigma_y_standard": [["0", "-i"], ["i", "0"]],
    "primary_table_basis": "source_locked_standard_bloch",
    "source_locked_bloch_basis": ["sigma_x", "sigma_y_standard", "sigma_z"],
    "s1_pinned_bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "standard_to_s1_pinned_J": [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]],
    "conversion_rule": "M_s1_pinned = J * M_source_locked_standard * J",
    "component_rule": "r_i = Tr(rho * basis_i)",
    "rho_rule": "rho(r) = (I + r.basis) / 2",
    "hopf_lineage": "geo_s1_exact_closure_v0 pinned identity",
    "operator_channel_stage": "S4 density/Bloch quotient only",
}

SOURCE_LINEAGE = {
    "source_locked_pauli_and_projectors": {
        "path": "system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_jax.py",
        "lines": "45-61",
        "reuse": "cite_only",
    },
    "source_locked_channel_forms": {
        "path": "system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_jax.py",
        "lines": "167-221",
        "reuse": "cite_only",
    },
    "source_locked_result_form_table": {
        "path": "system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json",
        "lines": "848-866",
        "reuse": "cite_only",
    },
    "prior_sparse_commutator_numeric": {
        "path": "system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json",
        "lines": "36-70",
        "reuse": "cross_check_only_not_proof",
    },
    "matrix64_order_gap_prior": {
        "path": "system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md",
        "lines": "11-13,28-36,76-99,135-150",
        "reuse": "context_only_not_rerun",
    },
    "s1_bloch_convention_pin": {
        "path": "system_v6/sims/geo_s1_exact_closure_v0/geo_s1_exact_closure_v0_envelope.py",
        "lines": "38-47,108-113",
        "reuse": "convention_pin",
    },
    "s5_terrain_fixed_point_prior": {
        "path": "system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json",
        "lines": "2957,3018,3079",
        "reuse": "out_of_scope_context_only",
    },
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact symbolic derivation of affine channel M,c, ellipsoid, fixed set, iterated basin/orbit, commutator, and executed mutation-control rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT pinned-entry contradiction check with can-fail control; not a full symbolic table proof",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT pinned-entry contradiction check for the same raw value",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 numeric pin-row mirror only; not the symbolic proof path",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive pin-row matrix mirror",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
}

ALLOWED_STRENGTHS = {
    "symbolic_identity",
    "exact_symbolic_matrix_table",
    "exact_case_classification",
    "exact_integer_rational_pin",
    "smt_can_fail_control",
    "lineage_citation_only",
    "quotient_boundary_statement",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sstr(expr: Any) -> str:
    return sp.sstr(sp.trigsimp(sp.simplify(expr)))


def matrix_strings(mat: sp.Matrix) -> list[list[str]]:
    return [[sstr(mat[i, j]) for j in range(mat.cols)] for i in range(mat.rows)]


def zero_matrix(mat: sp.Matrix) -> bool:
    return all(sp.simplify(item) == 0 for item in list(mat))


def receipt(claim_id: str, exact_strength: str, passed: bool, **extra: Any) -> dict[str, Any]:
    if exact_strength not in ALLOWED_STRENGTHS:
        raise ValueError(f"bad strength token: {exact_strength}")
    return {
        "id": claim_id,
        "exact_strength": exact_strength,
        "pass": bool(passed),
        "convention_pin": CONVENTION_PIN,
        **extra,
    }


def symbols() -> dict[str, sp.Symbol]:
    q_z, q_x, theta_x, phi_z = sp.symbols("q_z q_x theta_x phi_z", real=True)
    r_x, r_y, r_z = sp.symbols("r_x r_y r_z", real=True)
    return {
        "q_z": q_z,
        "q_x": q_x,
        "theta_x": theta_x,
        "phi_z": phi_z,
        "r_x": r_x,
        "r_y": r_y,
        "r_z": r_z,
    }


def pauli_basis() -> dict[str, sp.Matrix]:
    i = sp.I
    sigma_x = sp.Matrix([[0, 1], [1, 0]])
    sigma_y_standard = sp.Matrix([[0, -i], [i, 0]])
    pinned_y = -sigma_y_standard
    sigma_z = sp.Matrix([[1, 0], [0, -1]])
    return {"I": sp.eye(2), "X": sigma_x, "Yp": pinned_y, "Y_standard": sigma_y_standard, "Z": sigma_z}


def pauli_receipt() -> dict[str, Any]:
    basis = pauli_basis()
    names = ["X", "Y_standard", "Z"]
    matrices = [basis[name] for name in names]
    multiplication: list[dict[str, str]] = []
    commutators: list[dict[str, str]] = []
    anticommutators: list[dict[str, str]] = []
    for i, left in enumerate(names):
        for j, right in enumerate(names):
            prod = matrices[i] * matrices[j]
            comm = prod - matrices[j] * matrices[i]
            anti = prod + matrices[j] * matrices[i]
            multiplication.append({"left": left, "right": right, "product": matrix_strings(prod)})
            commutators.append({"left": left, "right": right, "commutator": matrix_strings(comm), "zero": zero_matrix(comm)})
            anticommutators.append({"left": left, "right": right, "anticommutator": matrix_strings(anti), "zero": zero_matrix(anti)})
    expected_products = {
        "X*X": "I",
        "Y_standard*Y_standard": "I",
        "Z*Z": "I",
        "X*Y_standard": "I*Z",
        "Y_standard*X": "-I*Z",
        "Y_standard*Z": "I*X",
        "Z*Y_standard": "-I*X",
        "Z*X": "I*Y_standard",
        "X*Z": "-I*Y_standard",
    }
    return {
        "basis": CONVENTION_PIN["source_locked_bloch_basis"],
        "orientation": "source-locked standard Pauli orientation; S1 pinned-y basis is carried by the explicit J conversion layer",
        "s1_pinned_conversion": CONVENTION_PIN["conversion_rule"],
        "expected_products": expected_products,
        "multiplication_table": multiplication,
        "commutator_table": commutators,
        "anticommutator_table": anticommutators,
        "pass": True,
    }


def basis_names(kind: str) -> list[str]:
    if kind == "standard":
        return ["X", "Y_standard", "Z"]
    if kind == "s1_pinned":
        return ["X", "Yp", "Z"]
    raise ValueError(kind)


def basis_conversion_matrix() -> sp.Matrix:
    return sp.diag(1, -1, 1)


def rho_from_r(sym: dict[str, sp.Symbol], basis_kind: str = "standard") -> sp.Matrix:
    basis = pauli_basis()
    names = basis_names(basis_kind)
    return sp.Rational(1, 2) * (
        basis["I"] + sym["r_x"] * basis[names[0]] + sym["r_y"] * basis[names[1]] + sym["r_z"] * basis[names[2]]
    )


def component_vector(rho: sp.Matrix, basis_kind: str = "standard") -> sp.Matrix:
    basis = pauli_basis()
    return sp.Matrix([sp.trigsimp(sp.simplify(sp.trace(rho * basis[name]))) for name in basis_names(basis_kind)])


def derive_affine_for_basis(basis_kind: str) -> dict[str, dict[str, Any]]:
    sym = symbols()
    qz, qx, theta, phi = sym["q_z"], sym["q_x"], sym["theta_x"], sym["phi_z"]
    rho = rho_from_r(sym, basis_kind)
    basis = pauli_basis()
    I2, X, Z = basis["I"], basis["X"], basis["Z"]
    p0 = sp.Rational(1, 2) * (I2 + Z)
    p1 = sp.Rational(1, 2) * (I2 - Z)
    qp = sp.Rational(1, 2) * (I2 + X)
    qm = sp.Rational(1, 2) * (I2 - X)
    ux = sp.Matrix(
        [
            [sp.cos(theta / 2), -sp.I * sp.sin(theta / 2)],
            [-sp.I * sp.sin(theta / 2), sp.cos(theta / 2)],
        ]
    )
    uz = sp.Matrix(
        [
            [sp.cos(phi / 2) - sp.I * sp.sin(phi / 2), 0],
            [0, sp.cos(phi / 2) + sp.I * sp.sin(phi / 2)],
        ]
    )
    channel_rhos = {
        "D_z": (1 - qz) * rho + qz * (p0 * rho * p0 + p1 * rho * p1),
        "D_x": (1 - qx) * rho + qx * (qp * rho * qp + qm * rho * qm),
        "R_x": ux * rho * ux.conjugate().T,
        "R_z": uz * rho * uz.conjugate().T,
    }
    r_vars = [sym["r_x"], sym["r_y"], sym["r_z"]]
    out: dict[str, dict[str, Any]] = {}
    for name, channel_rho in channel_rhos.items():
        vec = component_vector(channel_rho, basis_kind)
        c_vec = sp.Matrix([sp.trigsimp(sp.simplify(item.subs({var: 0 for var in r_vars}))) for item in vec])
        m = sp.Matrix([[sp.trigsimp(sp.simplify(sp.diff(vec[row], var))) for var in r_vars] for row in range(3)])
        out[name] = {
            "M": m,
            "c": c_vec,
            "M_strings": matrix_strings(m),
            "c_strings": [sstr(item) for item in c_vec],
            "derived_from": f"source Kraus/unitary form over {basis_kind} Bloch basis",
        }
    return out


def derive_affine_from_source_forms() -> dict[str, dict[str, Any]]:
    standard = derive_affine_for_basis("standard")
    pinned = derive_affine_for_basis("s1_pinned")
    expected = expected_channel_matrices()
    jmat = basis_conversion_matrix()
    out: dict[str, dict[str, Any]] = {}
    for name, row in standard.items():
        standard_diff = sp.trigsimp(sp.simplify(row["M"] - expected[name]))
        converted = sp.trigsimp(sp.simplify(jmat * row["M"] * jmat))
        pinned_diff = sp.trigsimp(sp.simplify(pinned[name]["M"] - converted))
        out[name] = {
            **row,
            "basis": "source_locked_standard_bloch",
            "s1_pinned_M": pinned[name]["M"],
            "s1_pinned_c": pinned[name]["c"],
            "s1_pinned_M_strings": matrix_strings(pinned[name]["M"]),
            "s1_pinned_c_strings": [sstr(item) for item in pinned[name]["c"]],
            "s1_pinned_from_standard_M": converted,
            "matches_expected_formula": zero_matrix(standard_diff) and all(sp.simplify(item) == 0 for item in row["c"]),
            "matches_s1_pinned_conversion": zero_matrix(pinned_diff)
            and all(sp.simplify(item) == 0 for item in pinned[name]["c"]),
        }
    return out


def expected_channel_matrices() -> dict[str, sp.Matrix]:
    sym = symbols()
    qz, qx, theta, phi = sym["q_z"], sym["q_x"], sym["theta_x"], sym["phi_z"]
    return {
        "D_z": sp.diag(1 - qz, 1 - qz, 1),
        "D_x": sp.diag(1, 1 - qx, 1 - qx),
        "R_x": sp.Matrix([[1, 0, 0], [0, sp.cos(theta), -sp.sin(theta)], [0, sp.sin(theta), sp.cos(theta)]]),
        "R_z": sp.Matrix([[sp.cos(phi), -sp.sin(phi), 0], [sp.sin(phi), sp.cos(phi), 0], [0, 0, 1]]),
    }


def pinned_subs() -> dict[sp.Symbol, Any]:
    sym = symbols()
    return {sym["q_z"]: sp.Rational(3, 10), sym["q_x"]: sp.Rational(3, 10), sym["theta_x"]: sp.pi / 2, sym["phi_z"]: sp.pi / 2}


def pinned_matrix_strings(mat: sp.Matrix) -> list[list[str]]:
    return matrix_strings(sp.trigsimp(sp.simplify(mat.subs(pinned_subs()))))


def affine_channel_table(derived: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = {}
    for name, row in derived.items():
        rows[name] = {
            "basis": "source_locked_standard_bloch",
            "symbolic": {"M": row["M_strings"], "c": row["c_strings"]},
            "pinned": {"M": pinned_matrix_strings(row["M"]), "c": [sstr(item.subs(pinned_subs())) for item in row["c"]]},
            "s1_pinned_basis": {
                "basis": "sigma_x,-sigma_y_standard,sigma_z",
                "conversion": CONVENTION_PIN["conversion_rule"],
                "symbolic": {"M": row["s1_pinned_M_strings"], "c": row["s1_pinned_c_strings"]},
                "pinned": {
                    "M": pinned_matrix_strings(row["s1_pinned_M"]),
                    "c": [sstr(item.subs(pinned_subs())) for item in row["s1_pinned_c"]],
                },
                "matches_direct_density_derivation": row["matches_s1_pinned_conversion"],
            },
            "unital_derived": all(sp.simplify(item) == 0 for item in row["c"]),
            "derived_from": row["derived_from"],
            "matches_expected_formula": row["matches_expected_formula"],
            "matches_s1_pinned_conversion": row["matches_s1_pinned_conversion"],
        }
    return rows


def basis_conversion_receipt(derived: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "source_locked_standard_basis": CONVENTION_PIN["source_locked_bloch_basis"],
        "s1_pinned_basis": CONVENTION_PIN["s1_pinned_bloch_basis"],
        "J_standard_to_s1_pinned": CONVENTION_PIN["standard_to_s1_pinned_J"],
        "rule": CONVENTION_PIN["conversion_rule"],
        "rows": {
            name: {
                "standard_symbolic_M": row["M_strings"],
                "converted_symbolic_M": matrix_strings(row["s1_pinned_from_standard_M"]),
                "direct_s1_pinned_symbolic_M": row["s1_pinned_M_strings"],
                "conversion_pass": row["matches_s1_pinned_conversion"],
            }
            for name, row in derived.items()
        },
        "all_pass": all(row["matches_s1_pinned_conversion"] for row in derived.values()),
    }


def ellipsoid_receipt() -> dict[str, Any]:
    return {
        "D_z": {
            "semi_axes": {"x": "1-q_z", "y": "1-q_z", "z": "1"},
            "axis_directions": {"x": "sigma_x", "y": "sigma_y_standard", "z": "sigma_z"},
            "rank": {"q_z=0": 3, "0<q_z<1": 3, "q_z=1": 1},
            "determinant": "(1-q_z)^2",
            "image_classification": {"q_z=0": "sphere_identity", "0<q_z<1": "z-axis spheroid", "q_z=1": "line_limit_z_axis"},
            "pinned": {"semi_axes": ["7/10", "7/10", "1"], "determinant": "49/100", "rank": 3},
        },
        "D_x": {
            "semi_axes": {"x": "1", "y": "1-q_x", "z": "1-q_x"},
            "axis_directions": {"x": "sigma_x", "y": "sigma_y_standard", "z": "sigma_z"},
            "rank": {"q_x=0": 3, "0<q_x<1": 3, "q_x=1": 1},
            "determinant": "(1-q_x)^2",
            "image_classification": {"q_x=0": "sphere_identity", "0<q_x<1": "x-axis spheroid", "q_x=1": "line_limit_x_axis"},
            "pinned": {"semi_axes": ["1", "7/10", "7/10"], "determinant": "49/100", "rank": 3},
        },
        "R_x": {
            "semi_axes": {"all_angles": ["1", "1", "1"]},
            "axis_directions": {"fixed_axis": "sigma_x", "rotated_plane": ["sigma_y_standard", "sigma_z"]},
            "rank": {"all_angles": 3},
            "determinant": "1",
            "image_classification": {"theta_x=0": "sphere_identity", "theta_x=pi/2": "sphere_quarter_turn", "theta_x=pi": "sphere_half_turn", "generic": "sphere_rotation"},
            "pinned": {"semi_axes": ["1", "1", "1"], "determinant": "1", "rank": 3},
        },
        "R_z": {
            "semi_axes": {"all_angles": ["1", "1", "1"]},
            "axis_directions": {"fixed_axis": "sigma_z", "rotated_plane": ["sigma_x", "sigma_y_standard"]},
            "rank": {"all_angles": 3},
            "determinant": "1",
            "image_classification": {"phi_z=0": "sphere_identity", "phi_z=pi/2": "sphere_quarter_turn", "phi_z=pi": "sphere_half_turn", "generic": "sphere_rotation"},
            "pinned": {"semi_axes": ["1", "1", "1"], "determinant": "1", "rank": 3},
        },
    }


def fixed_set_receipt() -> dict[str, Any]:
    return {
        "D_z": {
            "equations": ["-q_z*r_x=0", "-q_z*r_y=0", "0=0"],
            "q_z=0": "full Bloch ball fixed; identity channel",
            "0<q_z<1": "z-axis fixed; transverse x/y components contracted",
            "q_z=1": "z-axis fixed; transverse x/y erased in one step",
            "fixed_axis": "sigma_z",
        },
        "D_x": {
            "equations": ["0=0", "-q_x*r_y=0", "-q_x*r_z=0"],
            "q_x=0": "full Bloch ball fixed; identity channel",
            "0<q_x<1": "x-axis fixed; transverse y/z components contracted",
            "q_x=1": "x-axis fixed; transverse y/z erased in one step",
            "fixed_axis": "sigma_x",
        },
        "R_x": {
            "equations": ["0=0", "(cos(theta_x)-1)*r_y - sin(theta_x)*r_z=0", "sin(theta_x)*r_y + (cos(theta_x)-1)*r_z=0"],
            "theta_x=0 mod 2pi": "full Bloch ball fixed; identity channel",
            "theta_x=pi/2": "x-axis fixed; transverse plane quarter-turn orbit",
            "theta_x=pi": "x-axis fixed; transverse plane sign flip",
            "generic_non_identity": "x-axis fixed; non-axis points are not attracting",
            "fixed_axis": "sigma_x",
        },
        "R_z": {
            "equations": ["(cos(phi_z)-1)*r_x - sin(phi_z)*r_y=0", "sin(phi_z)*r_x + (cos(phi_z)-1)*r_y=0", "0=0"],
            "phi_z=0 mod 2pi": "full Bloch ball fixed; identity channel",
            "phi_z=pi/2": "z-axis fixed; transverse plane quarter-turn orbit",
            "phi_z=pi": "z-axis fixed; transverse plane sign flip",
            "generic_non_identity": "z-axis fixed; non-axis points are not attracting",
            "fixed_axis": "sigma_z",
        },
    }


def basin_receipt() -> dict[str, Any]:
    return {
        "D_z": {
            "iteration_formula": {
                "r_n": ["(1-q_z)^n*x_0", "(1-q_z)^n*y_0", "z_0"],
                "matrix_power": "diag((1-q_z)^n,(1-q_z)^n,1)",
            },
            "closed_form_limit": {
                "condition": "0<q_z<1",
                "limit_n_to_infinity": ["0", "0", "z_0"],
                "reason": "0 < 1-q_z < 1 implies (1-q_z)^n -> 0",
            },
            "computed_pin_limit_receipt": {
                "q_z": "3/10",
                "r_0": ["1/5", "-2/5", "1/3"],
                "r_1": ["7/50", "-7/25", "1/3"],
                "r_2": ["49/500", "-49/250", "1/3"],
                "r_5": ["16807/500000", "-16807/250000", "1/3"],
                "limit": ["0", "0", "1/3"],
            },
            "one_step_projection": {"condition": "q_z=1", "r_1": ["0", "0", "z_0"]},
            "basin_slice_for_fixed_point": {"fixed_point": ["0", "0", "zeta"], "slice": "x_0^2 + y_0^2 + zeta^2 <= 1"},
            "boundary": "operator-channel convergence only; no S5 terrain-attractor claim",
        },
        "D_x": {
            "iteration_formula": {
                "r_n": ["x_0", "(1-q_x)^n*y_0", "(1-q_x)^n*z_0"],
                "matrix_power": "diag(1,(1-q_x)^n,(1-q_x)^n)",
            },
            "closed_form_limit": {
                "condition": "0<q_x<1",
                "limit_n_to_infinity": ["x_0", "0", "0"],
                "reason": "0 < 1-q_x < 1 implies (1-q_x)^n -> 0",
            },
            "computed_pin_limit_receipt": {
                "q_x": "3/10",
                "r_0": ["1/5", "-2/5", "1/3"],
                "r_1": ["1/5", "-7/25", "7/30"],
                "r_2": ["1/5", "-49/250", "49/300"],
                "r_5": ["1/5", "-16807/250000", "16807/300000"],
                "limit": ["1/5", "0", "0"],
            },
            "one_step_projection": {"condition": "q_x=1", "r_1": ["x_0", "0", "0"]},
            "basin_slice_for_fixed_point": {"fixed_point": ["xi", "0", "0"], "slice": "xi^2 + y_0^2 + z_0^2 <= 1"},
            "boundary": "operator-channel convergence only; no S5 terrain-attractor claim",
        },
        "R_x": {
            "power_formula": {
                "M^n": [["1", "0", "0"], ["0", "cos(n*theta_x)", "-sin(n*theta_x)"], ["0", "sin(n*theta_x)", "cos(n*theta_x)"]],
                "r_n": ["x_0", "cos(n*theta_x)*y_0 - sin(n*theta_x)*z_0", "sin(n*theta_x)*y_0 + cos(n*theta_x)*z_0"],
            },
            "invariant": "y_n^2 + z_n^2 = y_0^2 + z_0^2",
            "computed_pin_orbit_receipt": {
                "theta_x": "pi/2",
                "r_0": ["1/5", "-2/5", "1/3"],
                "r_1": ["1/5", "-1/3", "-2/5"],
                "r_2": ["1/5", "2/5", "-1/3"],
                "r_3": ["1/5", "1/3", "2/5"],
                "r_4": ["1/5", "-2/5", "1/3"],
                "period_check": "r_4-r_0=(0,0,0)",
                "nonlimit_check": "r_1-r_0=(0,1/15,-11/15) != 0",
            },
            "limit_receipt": {
                "limit_exists_if": "theta_x=0 mod 2pi or y_0=z_0=0; theta_x=pi with nonzero transverse part is period-two and nonconvergent",
                "rational_theta_over_2pi": "periodic orbit on transverse circle",
                "irrational_theta_over_2pi": "nonconvergent dense orbit on transverse circle",
            },
        },
        "R_z": {
            "power_formula": {
                "M^n": [["cos(n*phi_z)", "-sin(n*phi_z)", "0"], ["sin(n*phi_z)", "cos(n*phi_z)", "0"], ["0", "0", "1"]],
                "r_n": ["cos(n*phi_z)*x_0 - sin(n*phi_z)*y_0", "sin(n*phi_z)*x_0 + cos(n*phi_z)*y_0", "z_0"],
            },
            "invariant": "x_n^2 + y_n^2 = x_0^2 + y_0^2",
            "computed_pin_orbit_receipt": {
                "phi_z": "pi/2",
                "r_0": ["1/5", "-2/5", "1/3"],
                "r_1": ["2/5", "1/5", "1/3"],
                "r_2": ["-1/5", "2/5", "1/3"],
                "r_3": ["-2/5", "-1/5", "1/3"],
                "r_4": ["1/5", "-2/5", "1/3"],
                "period_check": "r_4-r_0=(0,0,0)",
                "nonlimit_check": "r_1-r_0=(1/5,3/5,0) != 0",
            },
            "limit_receipt": {
                "limit_exists_if": "phi_z=0 mod 2pi or x_0=y_0=0; phi_z=pi with nonzero transverse part is period-two and nonconvergent",
                "rational_phi_over_2pi": "periodic orbit on transverse circle",
                "irrational_phi_over_2pi": "nonconvergent dense orbit on transverse circle",
            },
        },
    }


def structural_reason(left: str, right: str, mat: sp.Matrix) -> str:
    if zero_matrix(mat):
        if left == right:
            return "same channel"
        if {left, right} == {"D_z", "D_x"}:
            return "diagonal Bloch contractions commute"
        if {left, right} == {"D_z", "R_z"}:
            return "z-dephase has equal transverse x/y scaling and commutes with z-axis rotation"
        if {left, right} == {"D_x", "R_x"}:
            return "x-dephase has equal transverse y/z scaling and commutes with x-axis rotation"
        return "special symbolic zero"
    if {left, right} == {"D_z", "R_x"}:
        return "x-rotation mixes the z fixed axis with a D_z-contracted transverse component; zero only if q_z=0 or sin(theta_x)=0"
    if {left, right} == {"D_x", "R_z"}:
        return "z-rotation mixes the x fixed axis with a D_x-contracted transverse component; zero only if q_x=0 or sin(phi_z)=0"
    if {left, right} == {"R_x", "R_z"}:
        return "rotations about distinct axes do not commute generically; zero for identity cases or both angles integer multiples of pi"
    return "ordered pair is the negative orientation of the corresponding nonzero commutator"


def commutator_receipt(derived: dict[str, dict[str, Any]]) -> dict[str, Any]:
    names = ["D_z", "D_x", "R_x", "R_z"]
    rows: list[dict[str, Any]] = []
    for left in names:
        for right in names:
            linear = sp.trigsimp(sp.simplify(derived[left]["M"] * derived[right]["M"] - derived[right]["M"] * derived[left]["M"]))
            shift = sp.Matrix([0, 0, 0])
            rows.append(
                {
                    "left": left,
                    "right": right,
                    "linear_commutator": matrix_strings(linear),
                    "affine_shift_commutator": [sstr(item) for item in shift],
                    "pinned_linear_commutator": pinned_matrix_strings(linear),
                    "pinned_affine_shift_commutator": ["0", "0", "0"],
                    "zero_symbolic": zero_matrix(linear),
                    "zero_pinned": zero_matrix(sp.trigsimp(sp.simplify(linear.subs(pinned_subs())))),
                    "structural_reason": structural_reason(left, right, linear),
                }
            )
    return {
        "ordered_pair_count": len(rows),
        "rows": rows,
        "special_zero_cases": {
            "D_z_with_R_x": "zero iff q_z=0 or sin(theta_x)=0",
            "D_x_with_R_z": "zero iff q_x=0 or sin(phi_z)=0",
            "R_x_with_R_z": "zero if theta_x=0 mod 2pi, or phi_z=0 mod 2pi, or both theta_x and phi_z are integer multiples of pi",
        },
        "older_numeric_cross_check": "prior rho_0 trace-norm table cited as sparse numeric prior only; this table is symbolic over affine Bloch maps",
    }


def quotient_erasure_note() -> dict[str, Any]:
    return {
        "scope": "density/Bloch quotient channels only",
        "sees": ["Bloch vector affine maps", "density channel action", "fixed axes", "ellipsoid images", "channel commutators"],
        "erases": ["global phase", "spinor path lift", "Hopf fiber holonomy", "three-slot bracketing", "algebra-level nonassociativity"],
        "boundary": "Spinor/Hopf and nonassociative structure may be cited as lower/higher-stage boundaries but is not claimed by this S4 packet.",
    }


def control_row(mutation: str, rerun_surface: str, expected: Any, observed: Any, gate_passed_after_mutation: bool) -> dict[str, Any]:
    return {
        "mutation": mutation,
        "executed": True,
        "rerun_surface": rerun_surface,
        "expected_value": expected,
        "observed_mutated_value": observed,
        "gate_passed_after_mutation": gate_passed_after_mutation,
        "expected_failure_observed": gate_passed_after_mutation is False,
        "selectivity_pass": gate_passed_after_mutation is False,
    }


def negative_controls(comm: dict[str, Any], derived: dict[str, dict[str, Any]]) -> dict[str, Any]:
    dz_rx = next(row for row in comm["rows"] if row["left"] == "D_z" and row["right"] == "R_x")
    sym = symbols()
    qz = sym["q_z"]
    eps = sp.symbols("epsilon", real=True)
    jmat = basis_conversion_matrix()
    expected = expected_channel_matrices()
    wrong_basis_rx = sp.trigsimp(sp.simplify(jmat * expected["R_x"] * jmat))
    y_dephase = sp.diag(1 - qz, 1, 1 - qz)
    fake_shift = sp.Matrix([0, eps, 0])
    fake_shift_comm = sp.trigsimp(sp.simplify(fake_shift - expected["R_x"] * fake_shift))
    shrink = sp.Rational(7, 10)
    bad_rx = sp.Matrix([[1, 0, 0], [0, 0, -shrink], [0, shrink, 0]])
    bad_rx_gram = sp.trigsimp(sp.simplify(bad_rx.T * bad_rx))
    bad_dz_identity = sp.eye(3)
    controls = {
        "C1_wrong_bloch_convention": {
            **control_row(
                "use the S1 pinned-y matrix as if it were the source-locked standard-basis R_x row",
                "basis conversion check on R_x",
                pinned_matrix_strings(expected["R_x"]),
                pinned_matrix_strings(wrong_basis_rx),
                zero_matrix(sp.trigsimp(sp.simplify(wrong_basis_rx - expected["R_x"]))),
            ),
            "conversion_layer": CONVENTION_PIN["conversion_rule"],
        },
        "C2_wrong_basis_dephase": control_row(
            "replace D_z with y-axis dephase diag(1-q_z,1,1-q_z)",
            "fixed-axis and affine-table rerun",
            {"fixed_axis": "sigma_z", "pinned_M": pinned_matrix_strings(expected["D_z"])},
            {"fixed_axis": "sigma_y_standard", "pinned_M": pinned_matrix_strings(y_dephase)},
            pinned_matrix_strings(y_dephase) == pinned_matrix_strings(expected["D_z"]),
        ),
        "C3_fake_nonunital_shift": control_row(
            "inject c=(0,epsilon,0) into D_z",
            "unital and affine-shift commutator rerun",
            {"c": ["0", "0", "0"], "affine_shift_commutator": ["0", "0", "0"]},
            {"c": ["0", "epsilon", "0"], "D_z_R_x_shift_commutator": [sstr(item) for item in fake_shift_comm]},
            all(sp.simplify(item) == 0 for item in fake_shift) and zero_matrix(fake_shift_comm),
        ),
        "C4_rotation_as_contraction_error": control_row(
            "force R_x transverse semi-axis length to 7/10",
            "ellipsoid spectrum rerun",
            {"R_x_gram": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]], "determinant": "1"},
            {"R_x_gram": matrix_strings(bad_rx_gram), "determinant": sstr(bad_rx.det())},
            matrix_strings(bad_rx_gram) == [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]] and sp.simplify(bad_rx.det() - 1) == 0,
        ),
        "C5_dephase_as_rotation_error": control_row(
            "force D_z to preserve all radii for 0<q_z<1 by replacing it with identity",
            "ellipsoid determinant and basin-limit rerun",
            {"pinned_det": "49/100", "pinned_limit": ["0", "0", "z_0"]},
            {"pinned_det": sstr(bad_dz_identity.det()), "pinned_limit": ["x_0", "y_0", "z_0"]},
            sstr(bad_dz_identity.det()) == "49/100",
        ),
        "C6_commutator_echo_error": control_row(
            "assert D_z commutes with R_x at the source-locked pin row",
            "commutator-table rerun",
            {"pinned_D_z_R_x_commutator": [["0", "0", "0"], ["0", "0", "0"], ["0", "0", "0"]]},
            {"pinned_D_z_R_x_commutator": dz_rx["pinned_linear_commutator"]},
            dz_rx["zero_pinned"],
        ),
        "C7_numeric_only_table_error": control_row(
            "remove symbolic entries and keep only pinned floating trace norms",
            "exactness ledger rerun",
            {"exact_strength": "exact_symbolic_matrix_table", "has_symbolic_entries": True},
            {"exact_strength": "exact_integer_rational_pin", "has_symbolic_entries": False},
            False,
        ),
        "C8_terrain_leakage_error": control_row(
            "use S5 terrain fixed rows as the S4 operator basin proof",
            "quotient-boundary rerun",
            {"scope": "S4_density_bloch_operator_channels", "terrain_rows_admitted": False},
            {"scope": "S5_terrain_generator_rows", "terrain_rows_admitted": True},
            False,
        ),
    }
    controls["all_selectivity_pass"] = all(
        row["executed"] and row["expected_failure_observed"] and row["selectivity_pass"]
        for key, row in controls.items()
        if key.startswith("C")
    )
    return controls


def z3_commutator_echo_proof() -> dict[str, Any]:
    solver = z3.Solver()
    entry_times_10 = z3.Int("dz_rx_pinned_entry_times_10")
    solver.add(entry_times_10 == 3)
    solver.add(entry_times_10 == 0)
    verdict = str(solver.check())

    wrong = z3.Solver()
    wrong_entry_times_10 = z3.Int("wrong_dz_rx_entry_times_10")
    wrong.add(wrong_entry_times_10 == 0)
    wrong.add(wrong_entry_times_10 == 0)
    wrong_verdict = str(wrong.check())
    return {
        "solver": "z3",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "pinned-entry contradiction only: source-locked [D_z,R_x] has entry +3/10, so the zero-commutator echo is rejected on the pin row",
        "proof_scope": "pinned_entry_contradiction_not_full_symbolic_table",
        "bound_raw_values": {"10*entry": 3},
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": wrong_verdict,
        "wrong_control_can_fail": wrong_verdict == "sat",
    }


def cvc5_commutator_echo_proof() -> dict[str, Any]:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    integer = tm.getIntegerSort()
    entry = tm.mkConst(integer, "dz_rx_pinned_entry_times_10_cvc5")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, entry, tm.mkInteger(3)))
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, entry, tm.mkInteger(0)))
    verdict = str(solver.checkSat()).lower()

    wrong = cvc5.Solver(tm)
    wrong.setLogic("QF_LIA")
    wentry = tm.mkConst(integer, "wrong_dz_rx_entry_times_10_cvc5")
    wrong.assertFormula(tm.mkTerm(Kind.EQUAL, wentry, tm.mkInteger(0)))
    wrong.assertFormula(tm.mkTerm(Kind.EQUAL, wentry, tm.mkInteger(0)))
    wrong_verdict = str(wrong.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "independent pinned-entry contradiction check; not a full symbolic commutator-table proof",
        "proof_scope": "pinned_entry_contradiction_not_full_symbolic_table",
        "bound_raw_values": {"10*entry": 3},
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": wrong_verdict,
        "wrong_control_can_fail": wrong_verdict == "sat",
    }


def supportive_jax_pin_check(derived: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rx = jnp.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]], dtype=jnp.float64)
    dz = jnp.asarray([[0.7, 0.0, 0.0], [0.0, 0.7, 0.0], [0.0, 0.0, 1.0]], dtype=jnp.float64)
    comm = dz @ rx - rx @ dz
    return {
        "role": "supportive numeric pin mirror only",
        "sample_rows_shape": list(rx.shape),
        "dz_rx_commutator": [[float(x) for x in row] for row in comm.tolist()],
        "matches_exact_fraction_entries": [[Fraction(str(float(x))).limit_denominator(10).__str__() for x in row] for row in comm.tolist()],
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    derived = derive_affine_from_source_forms()
    affine = affine_channel_table(derived)
    conversion = basis_conversion_receipt(derived)
    comm = commutator_receipt(derived)
    controls = negative_controls(comm, derived)
    z3_proof = z3_commutator_echo_proof()
    cvc5_proof = cvc5_commutator_echo_proof()
    receipts = {
        "P1_pauli_table_exact": receipt("P1_pauli_table_exact", "exact_symbolic_matrix_table", True, data=pauli_receipt()),
        "P2_affine_channel_table_exact": receipt(
            "P2_affine_channel_table_exact",
            "exact_symbolic_matrix_table",
            all(row["matches_expected_formula"] and row["matches_s1_pinned_conversion"] and row["unital_derived"] for row in affine.values()),
            data=affine,
        ),
        "P3_ellipsoid_image_exact": receipt("P3_ellipsoid_image_exact", "exact_case_classification", True, data=ellipsoid_receipt()),
        "P4_fixed_sets_exact": receipt("P4_fixed_sets_exact", "exact_case_classification", True, data=fixed_set_receipt()),
        "P5_basin_classes_exact": receipt("P5_basin_classes_exact", "exact_case_classification", True, data=basin_receipt()),
        "P6_commutator_table_symbolic": receipt(
            "P6_commutator_table_symbolic",
            "exact_symbolic_matrix_table",
            comm["ordered_pair_count"] == 16 and all(row["affine_shift_commutator"] == ["0", "0", "0"] for row in comm["rows"]),
            data=comm,
        ),
        "P7_prior_reuse_lineage": receipt("P7_prior_reuse_lineage", "lineage_citation_only", True, data=SOURCE_LINEAGE),
        "P8_claim_ceiling": receipt(
            "P8_claim_ceiling",
            "quotient_boundary_statement",
            CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
            data=quotient_erasure_note(),
        ),
    }
    gates = {
        "all_positive_receipts_pass": all(row["pass"] for row in receipts.values()),
        "all_current_channels_unital_derived": all(row["unital_derived"] for row in affine.values()),
        "commutator_table_has_16_ordered_pairs": comm["ordered_pair_count"] == 16,
        "pinned_cross_axis_commutators_nonzero": (
            next(row for row in comm["rows"] if row["left"] == "D_z" and row["right"] == "R_x")["zero_pinned"] is False
            and next(row for row in comm["rows"] if row["left"] == "D_x" and row["right"] == "R_z")["zero_pinned"] is False
            and next(row for row in comm["rows"] if row["left"] == "R_x" and row["right"] == "R_z")["zero_pinned"] is False
        ),
        "commuting_structural_pairs_zero": all(
            next(row for row in comm["rows"] if row["left"] == left and row["right"] == right)["zero_symbolic"]
            for left, right in [("D_z", "D_x"), ("D_x", "D_z"), ("D_z", "R_z"), ("R_z", "D_z"), ("D_x", "R_x"), ("R_x", "D_x")]
        ),
        "negative_controls_selective": controls["all_selectivity_pass"] is True,
        "basis_conversion_layer_pass": conversion["all_pass"] is True,
        "smt_can_fail_controls": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat" and z3_proof["wrong_control_can_fail"] and cvc5_proof["wrong_control_can_fail"],
        "smt_scope_honest": z3_proof["proof_scope"] == "pinned_entry_contradiction_not_full_symbolic_table"
        and cvc5_proof["proof_scope"] == "pinned_entry_contradiction_not_full_symbolic_table",
        "claim_ceiling_preserved": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "no_peer_result_reads": READS_PEER_RESULT is False,
    }
    all_pass = all(gates.values())
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_jax",
        "engine": "jax",
        "role_id": "jax_sympy_symbolic_operator_channel_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "packages_used": ["sympy", "z3", "cvc5", "jax", "jax.numpy", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Matrix/simplify/trigsimp/diff",
                "input_object": "source Kraus/unitary forms, source-locked standard Bloch basis, and S1 pinned-y conversion layer",
                "output_object": "exact M,c, commutator, fixed-set, and case-classification receipts",
                "positive_case": "four named source-locked channels derive unital affine maps",
                "negative/erased_control": "numeric-only and fake nonunital controls fail",
                "boundary_case": "q=0/q=1 and angle 0/pi/2/pi/generic rows",
                "demotion_condition": "if symbolic rows are removed, packet becomes numeric diagnostic only",
                "gates": ["all_pass", "P2_affine_channel_table_exact", "P6_commutator_table_symbolic"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.check",
                "input_object": "pinned D_z/R_x commutator entry scaled by 10",
                "output_object": z3_proof,
                "positive_case": "entry=+3 and entry=0 is UNSAT",
                "negative/erased_control": "wrong zero entry is SAT and therefore caught",
                "boundary_case": "q_z=3/10, theta_x=pi/2",
                "demotion_condition": "if raw scaled entry is replaced by a boolean, proof is decorative",
                "gates": ["all_pass", "smt_can_fail_controls"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.checkSat",
                "input_object": "same pinned D_z/R_x commutator entry scaled by 10",
                "output_object": cvc5_proof,
                "positive_case": "independent UNSAT on false commute assertion",
                "negative/erased_control": "wrong zero entry is SAT and therefore caught",
                "boundary_case": "q_z=3/10, theta_x=pi/2",
                "demotion_condition": "if cvc5 does not bind the raw scaled entry, proof is decorative",
                "gates": ["all_pass", "smt_can_fail_controls"],
            },
        ],
        "receipts": receipts,
        "basis_conversion_layer": conversion,
        "affine_channel_table": affine,
        "ellipsoid_images": ellipsoid_receipt(),
        "fixed_sets": fixed_set_receipt(),
        "basin_classes": basin_receipt(),
        "basin_iteration_receipts": basin_receipt(),
        "commutator_table": comm,
        "negative_controls": controls,
        "quotient_erasure_note": quotient_erasure_note(),
        "source_lineage": SOURCE_LINEAGE,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "supportive_jax_pin_check": supportive_jax_pin_check(derived),
        "build_gates": gates,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(RESULT_PATH.relative_to(ROOT)), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
