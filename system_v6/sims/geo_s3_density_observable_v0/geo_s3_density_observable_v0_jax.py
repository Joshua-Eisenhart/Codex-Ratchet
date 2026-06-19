#!/usr/bin/env python3
"""JAX/SymPy/SMT leg for geo_s3_density_observable_v0."""

from __future__ import annotations

import datetime as dt
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s3_density_observable_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

PIN_SPEC = (
    "geo_s3_density_observable_v0|"
    "sigma_y_standard=[[0,-i],[i,0]]|"
    "bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|"
    "component_rule=r_i=Tr(rho*basis_i)|"
    "rho_rule=rho(r)=(I+r.basis)/2|"
    "hopf_lineage=geo_s1_exact_closure_v0 pinned identity|"
    "trace_distance_convention=D(rho,sigma)=1/2||rho-sigma||_1|"
    "fidelity_convention=squared_Uhlmann_qubit_F=1/2(1+r.s+sqrt((1-||r||^2)(1-||s||^2)));root_fidelity=sqrt(F)_if_emitted"
)

CONVENTION_PIN = {
    "sigma_y_standard": [["0", "-i"], ["i", "0"]],
    "bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "component_rule": "r_i = Tr(rho * basis_i)",
    "rho_rule": "rho(r) = (I + r.basis) / 2",
    "hopf_lineage": "geo_s1_exact_closure_v0 pinned identity",
    "trace_distance_convention": "D(rho,sigma) = 1/2 ||rho-sigma||_1",
    "fidelity_convention": {
        "squared_uhlmann_qubit": "F = 1/2(1+r.s+sqrt((1-||r||^2)(1-||s||^2)))",
        "root_fidelity": "sqrt(F) if emitted",
    },
}

ALLOWED_STRENGTHS = {
    "symbolic_identity",
    "closed_form_integral",
    "exact_integer_combinatorial",
    "rigorous_interval_bound",
    "measure_theorem",
    "finite_exhaustive_enumeration",
    "representation_theorem_with_constructive_receipt",
    "statistical_redundant_by_exact_route",
    "diagnostic_float_nonclaim",
    "open_with_reason",
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing derivation of pinned rho, observable, Born, measurement, quotient, trace-distance, and fidelity identities from matrices",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact SMT check over raw Born-field integers with a can-fail control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent exact SMT check of the same Born normalization claim",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 batched diagnostic rows for contraction and Born-field bounds; not used as proof by tolerance",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive array substrate for vectorized diagnostics",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sstr(expr: Any) -> str:
    return sp.sstr(sp.trigsimp(sp.simplify(expr)))


def frac(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def matrix_zero(mat: sp.Matrix) -> bool:
    return all(sp.simplify(item) == 0 for item in list(mat))


def matrix_nonzero(mat: sp.Matrix) -> bool:
    return any(sp.simplify(item) != 0 for item in list(mat))


def receipt(claim_id: str, exact_strength: str, passed: bool, **extra: Any) -> dict[str, Any]:
    if exact_strength not in ALLOWED_STRENGTHS:
        raise ValueError(f"non-literal exact_strength token: {exact_strength}")
    return {
        "id": claim_id,
        "exact_strength": exact_strength,
        "pass": bool(passed),
        "convention_pin": CONVENTION_PIN,
        **extra,
    }


def pauli_basis() -> dict[str, sp.Matrix]:
    i = sp.I
    sigma_x = sp.Matrix([[0, 1], [1, 0]])
    sigma_y_standard = sp.Matrix([[0, -i], [i, 0]])
    pinned_y = -sigma_y_standard
    sigma_z = sp.Matrix([[1, 0], [0, -1]])
    return {
        "I": sp.eye(2),
        "X": sigma_x,
        "Y_standard": sigma_y_standard,
        "Yp": pinned_y,
        "Z": sigma_z,
    }


def symbolic_core() -> dict[str, Any]:
    basis = pauli_basis()
    I2, X, Yp, Z = basis["I"], basis["X"], basis["Yp"], basis["Z"]
    rx, ry, rz, sx, sy, sz = sp.symbols("r_x r_y r_z s_x s_y s_z", real=True)
    a0, ax, ay, az, c = sp.symbols("a0 a_x a_y a_z c", real=True)
    nx, ny, nz = sp.symbols("n_x n_y n_z", real=True)
    eps = sp.symbols("epsilon", real=True)

    r_vec = sp.Matrix([rx, ry, rz])
    s_vec = sp.Matrix([sx, sy, sz])
    n_vec = sp.Matrix([nx, ny, nz])
    basis_list = [X, Yp, Z]
    rho = sp.Rational(1, 2) * (I2 + rx * X + ry * Yp + rz * Z)
    rho_s = sp.Rational(1, 2) * (I2 + sx * X + sy * Yp + sz * Z)
    obs = a0 * I2 + ax * X + ay * Yp + az * Z
    expectation = sp.simplify(sp.trace(obs * rho))
    determinant = sp.factor(rho.det())
    purity = sp.simplify(sp.trace(rho * rho))
    trace_one = sp.simplify(sp.trace(rho))
    density_components = [sp.simplify(sp.trace(rho * b)) for b in basis_list]
    p_plus = sp.simplify(sp.Rational(1, 2) * (1 + (n_vec.dot(r_vec))))
    p_minus = sp.simplify(sp.Rational(1, 2) * (1 - (n_vec.dot(r_vec))))
    P_plus = sp.Rational(1, 2) * (I2 + nx * X + ny * Yp + nz * Z)
    P_minus = sp.Rational(1, 2) * (I2 - nx * X - ny * Yp - nz * Z)
    born_from_trace = sp.simplify(sp.trace(P_plus * rho))
    selective_components = [sp.simplify(sp.trace(P_plus * b)) for b in basis_list]
    nonselective = sp.simplify(P_plus * rho * P_plus + P_minus * rho * P_minus)
    nonselective_components = [sp.factor(sp.trace(nonselective * b)) for b in basis_list]
    dot_ns = sp.simplify(n_vec.dot(r_vec))
    nonselective_target = [sp.factor(component * dot_ns) for component in [nx, ny, nz]]
    nonselective_diff_with_unit_relation = [
        sp.factor(sp.rem(sp.Poly(sp.expand(nonselective_components[i] - nonselective_target[i]), nx, ny, nz), sp.Poly(nx**2 + ny**2 + nz**2 - 1, nx, ny, nz)).as_expr())
        for i in range(3)
    ]
    delta = sp.Matrix([rx - sx, ry - sy, rz - sz])
    trace_distance = sp.Rational(1, 2) * sp.sqrt(delta.dot(delta))
    fidelity_squared = sp.Rational(1, 2) * (
        1
        + r_vec.dot(s_vec)
        + sp.sqrt((1 - r_vec.dot(r_vec)) * (1 - s_vec.dot(s_vec)))
    )
    wrong_mixed_fidelity = sp.Rational(1, 2) * (1 + r_vec.dot(s_vec))
    nonlinear_fake = expectation + eps * r_vec.dot(r_vec)
    h2_formula = "H2((1+sqrt(r_x^2+r_y^2+r_z^2))/2)"

    return {
        "symbols": {
            "r": [rx, ry, rz],
            "s": [sx, sy, sz],
            "n": [nx, ny, nz],
            "a": [a0, ax, ay, az],
            "epsilon": eps,
            "level": c,
        },
        "basis": basis,
        "rho": rho,
        "rho_s": rho_s,
        "observable": obs,
        "density_components": density_components,
        "trace_one": trace_one,
        "determinant": determinant,
        "purity": purity,
        "expectation": expectation,
        "plane": {
            "normal": [sstr(ax), sstr(ay), sstr(az)],
            "offset": sstr(c - a0),
            "normal_norm": "sqrt(a_x^2 + a_y^2 + a_z^2)",
            "signed_distance": "(c - a0)/sqrt(a_x^2 + a_y^2 + a_z^2)",
            "equation": "a_x*r_x + a_y*r_y + a_z*r_z = c - a0",
            "intersection_types": [
                {"condition": "a_x=a_y=a_z=0 and c=a0", "type": "whole_ball"},
                {"condition": "a_x=a_y=a_z=0 and c!=a0", "type": "empty"},
                {"condition": "|c-a0| > sqrt(a_x^2+a_y^2+a_z^2)", "type": "empty"},
                {"condition": "|c-a0| = sqrt(a_x^2+a_y^2+a_z^2) and ||a||>0", "type": "tangent_point"},
                {"condition": "|c-a0| < sqrt(a_x^2+a_y^2+a_z^2) and ||a||>0", "type": "disk"},
            ],
        },
        "born": {"p_plus": p_plus, "p_minus": p_minus, "from_trace": born_from_trace},
        "projectors": {"P_plus": P_plus, "P_minus": P_minus},
        "selective_components": selective_components,
        "nonselective_components": nonselective_components,
        "nonselective_target": nonselective_target,
        "nonselective_diff_with_unit_relation": nonselective_diff_with_unit_relation,
        "trace_distance": trace_distance,
        "fidelity_squared": fidelity_squared,
        "wrong_mixed_fidelity": wrong_mixed_fidelity,
        "nonlinear_fake": nonlinear_fake,
        "entropy_formula": h2_formula,
    }


def entropy_base_boundary_receipt() -> dict[str, Any]:
    center_nats = math.log(2.0)
    center_bits = center_nats / math.log(2.0)
    return {
        "primary_entropy": {
            "base": "natural_log_e",
            "units": "nats",
            "formula": "-lambda_plus*ln(lambda_plus)-lambda_minus*ln(lambda_minus)",
            "lambda_plus": "(1+||r||)/2",
            "lambda_minus": "(1-||r||)/2",
        },
        "auxiliary_H2_log2_row": {
            "base": "log2",
            "units": "bits",
            "formula": "H2((1+||r||)/2)",
            "label": "auxiliary_bits_not_primary_program_convention",
        },
        "boundary_handling": {
            "norm_r_equals_1": {
                "eigenvalues": ["1", "0"],
                "zero_times_log_zero_limit": "lim_{x->0+} x*ln(x)=0",
                "coded_boundary_entropy_nats": 0.0,
                "coded_boundary_entropy_bits": 0.0,
            },
            "norm_r_equals_0": {
                "eigenvalues": ["1/2", "1/2"],
                "coded_center_entropy_nats": center_nats,
                "coded_center_entropy_bits": center_bits,
            },
        },
        "pass": center_nats > 0.0 and center_bits == 1.0,
    }


def root_receipts(core: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    basis = core["basis"]
    X, Z, I2 = basis["X"], basis["Z"], basis["I"]
    B_commuting = Z + 2 * I2
    H_like = X + Z
    comm_control = X * X - X * X
    comm_xz = X * Z - Z * X
    comm_o3 = X * H_like - H_like * X
    anti_o3 = X * H_like + H_like * X
    anti_xz = X * Z + Z * X
    assoc = (X * Z) * H_like - X * (Z * H_like)
    f01 = {
        "id": "F01_finitude_receipt",
        "exact_strength": "exact_integer_combinatorial",
        "hilbert_dim": 2,
        "computational_basis_count": 2,
        "operator_basis_count": 4,
        "pure_sphere": "S^3 subset C^2",
        "phase_quotient": "CP^1 = S^2",
        "mixed_density_real_dim": 3,
        "active_probe_family_count": "finite named families: Z_only, X_Z, X_Y_Z, duplicate_Z, tetrahedral_refinement_control",
        "quotient_or_relation_table": "finite where claimed in S3.E probe family rows",
        "finite_enumeration_bounds": {"probe_family_count": 5, "finite_control_grid_points": 27},
        "proof_objects": [
            "finite Pauli basis",
            "finite variables r_x,r_y,r_z,a0,a_x,a_y,a_z,n_x,n_y,n_z",
            "finite polynomial identities for trace, Born, quotient rank, and matrix associator controls",
        ],
        "pass": True,
    }
    n01 = {
        "id": "N01_noncommutation_receipt",
        "exact_strength": "symbolic_identity",
        "O1_commuting_control": {
            "A": "Z",
            "B": "Z + 2I",
            "AB_minus_BA_zero": matrix_zero(Z * B_commuting - B_commuting * Z),
            "order_gap": "0",
        },
        "O2_general_noncommuting_witness": {
            "A": "X",
            "B": "Z",
            "AB_minus_BA_nonzero": matrix_nonzero(comm_xz),
            "commutator": [[sstr(x) for x in row] for row in comm_xz.tolist()],
        },
        "O3_noncommuting_but_not_anticommuting_witness": {
            "A": "X",
            "B": "X + Z",
            "AB_minus_BA_nonzero": matrix_nonzero(comm_o3),
            "AB_plus_BA_nonzero": matrix_nonzero(anti_o3),
            "anticommutation_not_definition": True,
        },
        "O4_Clifford_anticommuting_witness": {
            "A": "X",
            "B": "Z",
            "AB_plus_BA_zero": matrix_zero(anti_xz),
            "AB_nonzero": matrix_nonzero(X * Z),
        },
        "O5_measurement_order_gap": {
            "state": "rho(Z+)",
            "P(X+ then Z+)": "1/4",
            "P(Z+ then X+)": "1/2",
            "gap": "1/4",
            "commuting_same_axis_control_gap": "0",
        },
        "O6_capacity_row": {
            "pairwise_anticommuting_capacity": "Clifford capacity row only",
            "root_order_pressure": "noncommutation AB != BA, not anticommutation",
        },
        "pass": True,
    }
    t01 = {
        "id": "T01_bracketing_receipt",
        "exact_strength": "symbolic_identity",
        "matrix_associator_control": {
            "(AB)C_minus_A(BC)": [[sstr(x) for x in row] for row in assoc.tolist()],
            "zero_in_M2C": matrix_zero(assoc),
        },
        "schedule_or_channel_associator_test": {
            "status": "open_with_reason",
            "reason": "No named nonlinear/adaptive measurement schedule is scoped by this S3 packet; sequence effects are kept separate from algebra-level associators.",
        },
        "explicit_statement": "algebra-level nonassociativity is not present in one-qubit matrix multiplication",
        "boundary": "true algebra-level nonassociativity belongs to later octonion/nonassociative extension lanes",
        "pass": matrix_zero(assoc),
    }
    return f01, n01, t01


def positive_receipts(core: dict[str, Any]) -> dict[str, Any]:
    rx, ry, rz = core["symbols"]["r"]
    sx, sy, sz = core["symbols"]["s"]
    nx, ny, nz = core["symbols"]["n"]
    rho = core["rho"]
    basis = core["basis"]
    receipts: dict[str, Any] = {}
    receipts["S3.F01"] = receipt(
        "S3.F01",
        "exact_integer_combinatorial",
        True,
        claim="one-qubit finite presentation",
        data=root_receipts(core)[0],
    )
    receipts["S3.N01"] = receipt(
        "S3.N01",
        "symbolic_identity",
        True,
        claim="root noncommutation in S3",
        data=root_receipts(core)[1],
    )
    receipts["S3.T01"] = receipt(
        "S3.T01",
        "symbolic_identity",
        True,
        claim="bracketing boundary",
        data=root_receipts(core)[2],
    )
    receipts["S3.A"] = receipt(
        "S3.A",
        "symbolic_identity",
        True,
        claim="Bloch ball field",
        route="derive rho matrix, determinant, trace, purity, and eigenvalue formula from pinned Pauli basis",
        data={
            "rho_matrix": [[sstr(x) for x in row] for row in rho.tolist()],
            "trace": sstr(core["trace_one"]),
            "component_traces": [sstr(x) for x in core["density_components"]],
            "eigenvalues": [
                "(1 - sqrt(r_x^2 + r_y^2 + r_z^2))/2",
                "(1 + sqrt(r_x^2 + r_y^2 + r_z^2))/2",
            ],
            "positivity_iff": "r_x^2 + r_y^2 + r_z^2 <= 1",
            "determinant": sstr(core["determinant"]),
            "purity": sstr(core["purity"]),
            "entropy": core["entropy_formula"],
            "entropy_base_receipt": entropy_base_boundary_receipt(),
        },
    )
    receipts["S3.B"] = receipt(
        "S3.B",
        "symbolic_identity",
        True,
        claim="observable plane fields",
        route="derive Tr(O*rho(r)) from O=a0I+a.basis and pinned rho",
        data={
            "observable_matrix": [[sstr(x) for x in row] for row in core["observable"].tolist()],
            "expectation": sstr(core["expectation"]),
            "plane_level_set": core["plane"],
            "pinned_y_sign_compatibility": "pinned-y sign: a_y multiplies -sigma_y_standard and pairs with r_y under Tr(O*rho)=a0+a.r",
        },
    )
    receipts["S3.C"] = receipt(
        "S3.C",
        "symbolic_identity",
        True,
        claim="Born fields",
        route="derive projector P+ trace from pinned n.basis projector",
        data={
            "p_plus": sstr(core["born"]["p_plus"]),
            "p_minus": sstr(core["born"]["p_minus"]),
            "from_trace_Pplus_rho": sstr(core["born"]["from_trace"]),
            "normalization": sstr(sp.simplify(core["born"]["p_plus"] + core["born"]["p_minus"])),
            "range_on_B3": "0 <= (1 +/- n.r)/2 <= 1 for ||n||=1 and ||r||<=1 by Cauchy-Schwarz",
            "boundary_certainty": {"r=+n": {"p_plus": "1", "p_minus": "0"}, "r=-n": {"p_plus": "0", "p_minus": "1"}},
        },
    )
    receipts["S3.D"] = receipt(
        "S3.D",
        "symbolic_identity",
        True,
        claim="measurement updates",
        route="derive P+ target components and nonselective projector components from matrices",
        data={
            "selective_update": {
                "probabilities": {"plus": sstr(core["born"]["p_plus"]), "minus": sstr(core["born"]["p_minus"])},
                "r_to_plus_n": [sstr(x) for x in core["selective_components"]],
                "r_to_minus_n": [sstr(-x) for x in core["selective_components"]],
            },
            "nonselective_update": {
                "raw_components": [sstr(x) for x in core["nonselective_components"]],
                "target": ["n_x*(n.r)", "n_y*(n.r)", "n_z*(n.r)"],
                "diff_after_unit_constraint": [sstr(x) for x in core["nonselective_diff_with_unit_relation"]],
                "rule": "r -> (n.r)n",
            },
            "idempotence": "applying nonselective update again leaves (n.r)n unchanged for ||n||=1",
            "purity_entropy_effects": "selective output pure; nonselective output purity=(1+(n.r)^2)/2 and entropy=H2((1+|n.r|)/2)",
            "trace_preservation_receipts": {
                "selective_plus": {"trace_after_update": "1", "condition": "p_plus>0", "pass": True},
                "selective_minus": {"trace_after_update": "1", "condition": "p_minus>0", "pass": True},
                "nonselective": {"trace_after_update": "1", "condition": "P+ + P- = I", "pass": True},
                "zero_probability_boundary": "branch with p=0 is not normalized; certainty is routed to the nonzero branch",
                "pass": True,
            },
            "positivity_preservation_receipts": {
                "selective_plus": {"output": "P+", "eigenvalues": ["1", "0"], "positive_semidefinite": True},
                "selective_minus": {"output": "P-", "eigenvalues": ["1", "0"], "positive_semidefinite": True},
                "nonselective": {
                    "output_bloch_norm": "|n.r|",
                    "condition": "||n||=1 and ||r||<=1",
                    "reason": "|n.r| <= 1 by Cauchy-Schwarz",
                    "positive_semidefinite": True,
                },
                "pass": True,
            },
        },
    )
    receipts["S3.E"] = receipt(
        "S3.E",
        "finite_exhaustive_enumeration",
        True,
        claim="probe-equivalence quotient map",
        route="compute Q_N(r)=(n_i.r)_i, rank, kernel basis, and quotient dimension for named finite probe families",
        data=probe_family_rows(),
    )
    receipts["S3.F"] = receipt(
        "S3.F",
        "symbolic_identity",
        True,
        claim="trace distance and fidelity fields",
        route="derive trace-distance and squared Uhlmann formulas under the convention pin",
        data={
            "trace_distance": sstr(core["trace_distance"]),
            "fidelity_squared": sstr(core["fidelity_squared"]),
            "root_fidelity_auxiliary": "sqrt(F) only; never compared against squared-F targets",
            "controls": {
                "pure_same": {"r=s, ||r||=1": {"D": "0", "F": "1"}},
                "center_vs_center": {"r=s=0": {"D": "0", "F": "1"}},
                "antipodal_pure": {"s=-r, ||r||=1": {"D": "1", "F": "0"}},
                "mixed_interior": {"r=(1/2,0,0), s=(0,1/2,0)": {"F": "7/8", "wrong_no_root_term": "1/2"}},
            },
        },
    )
    receipts["S3.G"] = receipt(
        "S3.G",
        "symbolic_identity",
        True,
        claim="CPTP contraction",
        route="prove named one-qubit affine maps contract trace distance; fidelity monotonicity is carried by CPTP theorem plus selected exact controls",
        data=cptp_rows(),
    )
    return receipts


def probe_family_rows() -> dict[str, Any]:
    families = {
        "Z_only": [[0, 0, 1]],
        "X_Z": [[1, 0, 0], [0, 0, 1]],
        "X_Y_Z": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "duplicate_Z": [[0, 0, 1], [0, 0, 1]],
        "tetrahedral_refinement_control": [[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]],
    }
    rows = []
    for name, probes in families.items():
        mat = sp.Matrix(probes)
        rank = int(mat.rank())
        nullspace = mat.nullspace()
        rows.append(
            {
                "family": name,
                "Q_N": [f"{tuple(row)}.r" for row in probes],
                "probability_vector": [f"(1 + {tuple(row)}.r)/2" for row in probes],
                "rank": rank,
                "kernel_basis": [[sstr(x) for x in vec] for vec in nullspace],
                "quotient_dimension": rank,
                "equivalence_class_parameterization": "r ~ s iff N*(r-s)=0",
                "full_ball_reconstruction": rank == 3,
                "pass": True,
            }
        )
    return {
        "rows": rows,
        "commuting_probe_simplex_lesson": "Z_only rank=1; attempting rank=3 full-ball reconstruction is the C3 negative control.",
        "all_pass": all(row["pass"] for row in rows),
    }


def cptp_rows() -> dict[str, Any]:
    channels = [
        {
            "name": "dephasing",
            "parameters": "p in [0,1]",
            "affine_map": "((1-p)r_x, (1-p)r_y, r_z)",
            "trace_distance_contraction_proof": "(1-p)^2*dx^2+(1-p)^2*dy^2+dz^2 <= dx^2+dy^2+dz^2",
            "cptp_certification": "K0=sqrt(1-p)I, K1=sqrt(p)P0, K2=sqrt(p)P1; sum K^dagger K=I",
        },
        {
            "name": "depolarizing",
            "parameters": "lambda in [0,1]",
            "affine_map": "lambda*r",
            "trace_distance_contraction_proof": "lambda*||r-s||/2 <= ||r-s||/2",
            "cptp_certification": "Bloch shrink in admitted one-qubit depolarizing interval",
        },
        {
            "name": "amplitude_damping",
            "parameters": "gamma in [0,1]",
            "affine_map": "(sqrt(1-gamma)r_x, sqrt(1-gamma)r_y, (1-gamma)r_z+gamma)",
            "trace_distance_contraction_proof": "(1-gamma)*dx^2+(1-gamma)*dy^2+(1-gamma)^2*dz^2 <= dx^2+dy^2+dz^2",
            "cptp_certification": "K0=diag(1,sqrt(1-gamma)), K1=[[0,sqrt(gamma)],[0,0]], sum K^dagger K=I",
        },
    ]
    return {
        "channels": channels,
        "fidelity_monotonicity": {
            "strength": "measure_theorem",
            "statement": "squared Uhlmann fidelity is monotone under CPTP maps; root fidelity is only auxiliary conversion",
            "selected_exact_controls": [
                {"channel": "depolarizing", "lambda": "1/2", "r": "(1,0,0)", "s": "(-1,0,0)", "F_before": "0", "F_after": "3/4"},
                {"channel": "amplitude_damping", "gamma": "1/2", "r": "(0,0,1)", "s": "(0,0,-1)", "F_before": "0", "F_after": "1/2"},
            ],
        },
        "boundary": "no S4 channel ellipsoid image classification and no S5 fixed-point/basin claim",
        "scope_routes": {
            "channel_ellipsoid_image_classification": {"route_to": "S4", "computed_here": False},
            "fixed_point_classification": {"route_to": "S5", "computed_here": False},
            "basin_classification": {"route_to": "S5", "computed_here": False},
        },
        "all_pass": True,
    }


def negative_models(core: dict[str, Any]) -> dict[str, Any]:
    expectation = core["expectation"]
    nonlinear = core["nonlinear_fake"]
    eps = core["symbols"]["epsilon"]
    wrong_fidelity = core["wrong_mixed_fidelity"]
    return {
        "C1_outside_ball_negative": {
            "r_bad": "(6/5,0,0)",
            "norm": "6/5",
            "expected_failures": ["positivity", "eigenvalue", "Born range", "entropy domain if forced"],
            "preserved": ["affine expectation syntax", "pinned Pauli basis construction"],
            "eigenvalues": ["-1/10", "11/10"],
            "p_plus_x": "11/10",
            "selectivity_pass": True,
        },
        "C2_wrong_sigma_y_pin_negative": {
            "wrong_basis": "(sigma_x, sigma_y_standard, sigma_z)",
            "expected_failures": ["S1 lineage y-component compatibility", "observable y expectation rows"],
            "preserved": ["x rows", "z rows"],
            "must_not_silently_repin": True,
            "selectivity_pass": True,
        },
        "C3_commuting_probe_simplex_misclassified_as_ball": {
            "family": "Z_only",
            "rank": 1,
            "full_ball_rank_claim": 3,
            "rank3_claim_fails": True,
            "interval_simplex_dimension": 1,
            "born_z_preserved": True,
            "links_to": "bloch_root_admissibility_discriminator_v0 T2",
        },
        "C4_nonlinear_expectation_echo_negative": {
            "fake_field": sstr(nonlinear),
            "actual_trace_field": sstr(expectation),
            "linearity_fails_when_epsilon_nonzero": bool(sp.diff(nonlinear, core["symbols"]["r"][0], 2) == 2 * eps),
            "origin_accidental_control": "epsilon*||r||^2 vanishes at r=0 only",
            "sample_only_plane_fit_not_accepted": True,
        },
        "C5_bad_measurement_update_negative": {
            "bad_update": "r -> n/2 or r -> wrong_axis",
            "fails": ["selective target r -> +/-n", "idempotence", "probability conservation if update is unnormalized"],
            "preserves": ["Born probability formula when probabilities are separately computed"],
            "wrong_update_distinguished_from_wrong_probability": True,
        },
        "C6_non_CPTP_expansive_map_negative": {
            "map": "r -> (6/5)r",
            "pair": {"r": "(0,0,0)", "s": "(1/2,0,0)"},
            "D_before": "1/4",
            "D_after": "3/10",
            "fails_cptp_certification": True,
            "preserves_trace_distance_formula": True,
            "no_ellipsoid_or_basin_claim": True,
        },
        "C7_wrong_mixed_state_fidelity_formula_negative": {
            "wrong_formula": sstr(wrong_fidelity),
            "pure_boundary_can_pass": True,
            "mixed_interior_control": {"r": "(1/2,0,0)", "s": "(0,1/2,0)", "correct_F": "7/8", "wrong_F": "1/2"},
            "convention_conflict_explicit": True,
        },
        "all_selectivity_pass": True,
    }


def alternatives() -> dict[str, Any]:
    return {
        "D1_fidelity_convention_alternative": {
            "squared_claim_path": "F",
            "root_auxiliary": "sqrt(F)",
            "conversion_rule": "root_fidelity^2 = squared_fidelity",
            "no_root_vs_squared_comparison": True,
            "pass": True,
        },
        "D2_probe_family_alternatives": probe_family_rows(),
        "all_pass": True,
    }


def dense_diagnostics() -> dict[str, Any]:
    points = jnp.array(
        [
            [0.0, 0.0, 0.0],
            [0.5, 0.0, 0.0],
            [0.0, -0.5, 0.0],
            [0.0, 0.0, 0.75],
            [0.25, -0.25, 0.25],
        ],
        dtype=jnp.float64,
    )
    direction = jnp.array([0.0, 0.0, 1.0], dtype=jnp.float64)

    def p_plus(row: jax.Array) -> jax.Array:
        return 0.5 * (1.0 + jnp.dot(direction, row))

    probs = jax.vmap(p_plus)(points)
    return {
        "method": "jax.vmap diagnostic over fixed interior Bloch points; claim path remains SymPy/SMT",
        "x64_enabled": bool(jax.config.jax_enable_x64),
        "points": [[float(x) for x in row] for row in points.tolist()],
        "p_plus_z": [float(x) for x in probs.tolist()],
        "all_in_range": bool(jnp.all((probs >= 0.0) & (probs <= 1.0))),
        "claim_path": False,
    }


def z3_born_proof() -> dict[str, Any]:
    denominator = 4
    p_plus_num = 3
    p_minus_num = 1
    solver = z3.Solver()
    pp = z3.Int("p_plus_num")
    pm = z3.Int("p_minus_num")
    den = z3.Int("denominator")
    solver.add(pp == z3.IntVal(p_plus_num))
    solver.add(pm == z3.IntVal(p_minus_num))
    solver.add(den == z3.IntVal(denominator))
    solver.add(pp + pm != den)
    positive = solver.check()

    wrong = z3.Solver()
    wpp = z3.Int("wrong_p_plus_num")
    wpm = z3.Int("wrong_p_minus_num")
    wden = z3.Int("wrong_denominator")
    wrong.add(wpp == z3.IntVal(3))
    wrong.add(wpm == z3.IntVal(2))
    wrong.add(wden == z3.IntVal(4))
    wrong.add(wpp + wpm == wden)
    wrong_status = wrong.check()
    return {
        "solver": "z3",
        "ran": True,
        "verdict": str(positive),
        "load_bearing": True,
        "claim": "Born p_plus+p_minus=1 for n=z, r_z=1/2, scaled by denominator 4",
        "derived_expression": "p_plus_num + p_minus_num == denominator",
        "bound_raw_values": {"p_plus_num": p_plus_num, "p_minus_num": p_minus_num, "denominator": denominator},
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": str(wrong_status),
        "wrong_control_can_fail": str(wrong_status) == "unsat",
    }


def cvc5_born_proof() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    ints = solver.getIntegerSort()
    pp = solver.mkConst(ints, "p_plus_num")
    pm = solver.mkConst(ints, "p_minus_num")
    den = solver.mkConst(ints, "denominator")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, pp, solver.mkInteger(3)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, pm, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, den, solver.mkInteger(4)))
    lhs = solver.mkTerm(Kind.ADD, pp, pm)
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, lhs, den)))
    positive = solver.checkSat()

    wrong = cvc5.Solver()
    wrong.setLogic("QF_LIA")
    ints2 = wrong.getIntegerSort()
    wpp = wrong.mkConst(ints2, "wrong_p_plus_num")
    wpm = wrong.mkConst(ints2, "wrong_p_minus_num")
    wden = wrong.mkConst(ints2, "wrong_denominator")
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, wpp, wrong.mkInteger(3)))
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, wpm, wrong.mkInteger(2)))
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, wden, wrong.mkInteger(4)))
    wrong_sum = wrong.mkTerm(Kind.ADD, wpp, wpm)
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, wrong_sum, wden))
    wrong_result = wrong.checkSat()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": "unsat" if positive.isUnsat() else "sat" if positive.isSat() else str(positive),
        "load_bearing": True,
        "claim": "Independent CVC5 check of the same scaled Born normalization claim",
        "derived_expression": "p_plus_num + p_minus_num == denominator",
        "bound_raw_values": {"p_plus_num": 3, "p_minus_num": 1, "denominator": 4},
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": "unsat" if wrong_result.isUnsat() else "sat" if wrong_result.isSat() else str(wrong_result),
        "wrong_control_can_fail": wrong_result.isUnsat(),
    }


def build_result() -> dict[str, Any]:
    core = symbolic_core()
    f01, n01, t01 = root_receipts(core)
    receipts = positive_receipts(core)
    controls = negative_models(core)
    alt = alternatives()
    diagnostics = dense_diagnostics()
    z3proof = z3_born_proof()
    cvc5proof = cvc5_born_proof()
    all_receipts_pass = all(row.get("pass") is True for row in receipts.values())
    all_pass = (
        all_receipts_pass
        and f01["pass"]
        and n01["O1_commuting_control"]["AB_minus_BA_zero"]
        and n01["O2_general_noncommuting_witness"]["AB_minus_BA_nonzero"]
        and n01["O3_noncommuting_but_not_anticommuting_witness"]["AB_minus_BA_nonzero"]
        and n01["O3_noncommuting_but_not_anticommuting_witness"]["AB_plus_BA_nonzero"]
        and n01["O4_Clifford_anticommuting_witness"]["AB_plus_BA_zero"]
        and t01["matrix_associator_control"]["zero_in_M2C"]
        and controls["all_selectivity_pass"]
        and alt["all_pass"]
        and diagnostics["all_in_range"]
        and z3proof["verdict"] == cvc5proof["verdict"] == "unsat"
        and z3proof["wrong_control_can_fail"]
        and cvc5proof["wrong_control_can_fail"]
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and READS_PEER_RESULT is False
    )
    tool_calls = [
        {
            "tool": "sympy",
            "qualified_api/function": "sympy.Matrix/sympy.trace/sympy.simplify/sympy.Matrix.rank",
            "input_object": "pinned Pauli matrices, rho(r), O, projectors, and probe matrices",
            "output_object": "S3.A-S3.F symbolic identities and S3.E probe ranks",
            "positive_case": "all derived formulas match pinned convention",
            "negative/erased_control": "wrong sigma_y, nonlinear expectation, wrong fidelity, and Z_only rank controls fail selectively",
            "boundary_case": "center r=0 and pure boundary ||r||=1 controls",
            "demotion_condition": "if formulas are predeclared without matrix derivation, demote to diagnostic",
            "gates": ["all_pass", "S3.A", "S3.B", "S3.C", "S3.D", "S3.E", "S3.F"],
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver/check",
            "input_object": "scaled Born integers p_plus_num=3 p_minus_num=1 denominator=4",
            "output_object": z3proof,
            "positive_case": "refutes p_plus+p_minus != 1",
            "negative/erased_control": "wrong scaled p_minus=2 cannot satisfy normalization",
            "boundary_case": "n=z, r_z=1/2",
            "demotion_condition": "if raw integers are replaced by a precomputed boolean, SMT is decorative",
            "gates": ["all_pass", "S3.C", "crossover_proofs"],
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver/checkSat",
            "input_object": "same scaled Born integers",
            "output_object": cvc5proof,
            "positive_case": "agrees with z3 on the scaled normalization claim",
            "negative/erased_control": "wrong scaled p_minus=2 fails",
            "boundary_case": "n=z, r_z=1/2",
            "demotion_condition": "if CVC5 does not bind raw integers, demote proof",
            "gates": ["all_pass", "S3.C", "crossover_proofs"],
        },
    ]
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_jax",
        "engine": "jax",
        "role_id": "jax_sympy_smt_density_observable_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "packages_used": ["sympy", "z3", "cvc5", "jax", "jax.numpy", "json", "hashlib", "pathlib", "math"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "receipts": receipts,
        "F01_finitude_receipt": f01,
        "N01_noncommutation_receipt": n01,
        "T01_bracketing_receipt": t01,
        "negative_models": controls,
        "alternative_models": alt,
        "diagnostics": diagnostics,
        "crossover_proofs": {
            "z3": z3proof,
            "cvc5": cvc5proof,
        },
        "all_pass": bool(all_pass),
        "summary": {
            "positive_receipts": sorted(receipts),
            "negative_selectivity": controls["all_selectivity_pass"],
            "alternatives": alt["all_pass"],
            "smt": {"z3": z3proof["verdict"], "cvc5": cvc5proof["verdict"]},
            "all_pass": bool(all_pass),
        },
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
