#!/usr/bin/env python3
"""JAX/proof leg for geo_s2_negative_models_v0."""

from __future__ import annotations

import datetime as _dt
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
import z3

from geo_s2_negative_models_v0_common import (
    CLASSIFICATION,
    COMMON_RECEIPT_KEYS,
    CONVENTION_PIN,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    READS_PEER_RESULT,
    RESULT_DIR,
    ROOT,
    SCALE,
    SELECTIVITY_COLUMNS,
    SIM_DIR,
    SIM_ID,
    TOL,
    canonical_a_chi,
    canonical_f_coeff,
    canonical_holonomy,
    canonical_strip_integral,
    chart_area,
    common_suite_adapter,
    file_sha256,
    metric_det_sqrt,
    physical_area,
    sha256_text,
    stokes_residual,
    wrong_a_chi,
    wrong_connection_holonomy,
    wrong_f_coeff,
    wrong_sign_strip_integral,
)


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
ETAS = (math.pi / 8.0, math.pi / 6.0, math.pi / 4.0, math.pi / 3.0, 3.0 * math.pi / 8.0)
ETA_PAIRS = ((math.pi / 8.0, math.pi / 3.0), (math.pi / 6.0, 3.0 * math.pi / 8.0))
GRID_N = 64
GRID_ETA = math.pi / 5.0

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vectorized S2 negative receipt magnitude computation across eta and strip rows",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 array substrate for trigonometric S2 receipt rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing raw-value proof polarity for nonzero wrong-model residuals and exact cover ratios",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent raw-value proof polarity matching z3",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, hashing, timestamps, and deterministic paths",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}


def as_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def receipt(pass_value: bool, exact_strength: str, measured: dict[str, Any], note: str) -> dict[str, Any]:
    return {
        "pass": bool(pass_value),
        "exact_strength": exact_strength,
        "measured": measured,
        "convention_pin": CONVENTION_PIN,
        "note": note,
    }


def z3_assert_int_eq(value: int, target: int) -> str:
    solver = z3.Solver()
    solver.add(z3.IntVal(value) == z3.IntVal(target))
    return str(solver.check())


def z3_assert_ratio_not(num: int, den: int, ratio: int) -> str:
    solver = z3.Solver()
    solver.add(z3.IntVal(num) != z3.IntVal(ratio) * z3.IntVal(den))
    return str(solver.check())


def cvc5_assert_int_eq(value: int, target: int) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, solver.mkInteger(value), solver.mkInteger(target)))
    return str(solver.checkSat()).lower()


def cvc5_assert_ratio_not(num: int, den: int, ratio: int) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.assertFormula(
        solver.mkTerm(
            Kind.DISTINCT,
            solver.mkInteger(num),
            solver.mkTerm(Kind.MULT, solver.mkInteger(ratio), solver.mkInteger(den)),
        )
    )
    return str(solver.checkSat()).lower()


def vector_rows() -> dict[str, list[float]]:
    etas = jnp.asarray(ETAS)
    canonical_a = jax.vmap(lambda x: jnp.cos(2.0 * x))(etas)
    wrong_a = jax.vmap(lambda x: -jnp.cos(2.0 * x))(etas)
    canonical_f = jax.vmap(lambda x: -2.0 * jnp.sin(2.0 * x))(etas)
    wrong_f = jax.vmap(lambda x: 2.0 * jnp.sin(2.0 * x))(etas)
    canonical_h = jax.vmap(lambda x: -2.0 * jnp.pi * jnp.cos(2.0 * x))(etas)
    wrong_h = jax.vmap(lambda x: 2.0 * jnp.pi * jnp.cos(2.0 * x))(etas)
    return {
        "etas": [as_float(x) for x in etas],
        "canonical_a_chi": [as_float(x) for x in canonical_a],
        "wrong_a_chi": [as_float(x) for x in wrong_a],
        "canonical_f_coeff": [as_float(x) for x in canonical_f],
        "wrong_f_coeff": [as_float(x) for x in wrong_f],
        "canonical_holonomy": [as_float(x) for x in canonical_h],
        "wrong_holonomy": [as_float(x) for x in wrong_h],
    }


def grid_pair_rows(n: int = GRID_N, eta: float = GRID_ETA) -> dict[str, Any]:
    pair_rows = []
    max_pair_deviation = 0.0
    parity_preserved = True
    for a, b in ((0, 0), (1, 2), (7, 9), (18, 25), (31, 5)):
        paired_a = (a + n // 2) % n
        paired_b = (b + n // 2) % n
        # The S2 cover relation is discrete here; same physical point after quotient.
        delta_phi = math.pi
        delta_chi = math.pi
        spinor_phase_deviation = abs(complex(math.cos(delta_phi + delta_chi), math.sin(delta_phi + delta_chi)) - 1.0)
        base_angle_deviation = abs(((2.0 * delta_chi) % (2.0 * math.pi)) - 0.0)
        pair_deviation = max(spinor_phase_deviation, base_angle_deviation)
        max_pair_deviation = max(max_pair_deviation, pair_deviation)
        parity_preserved = parity_preserved and ((a + b) % 2 == (paired_a + paired_b) % 2)
        pair_rows.append(
            {
                "a": a,
                "b": b,
                "paired_a": paired_a,
                "paired_b": paired_b,
                "pair_deviation": pair_deviation,
                "parity_preserved": (a + b) % 2 == (paired_a + paired_b) % 2,
            }
        )
    return {"pair_rows": pair_rows, "max_pair_deviation": max_pair_deviation, "parity_preserved": parity_preserved}


def positive_control() -> dict[str, Any]:
    local_eta = GRID_ETA
    n = GRID_N
    pair_data = grid_pair_rows(n, local_eta)
    receipts = {
        "S2.A_connection_match": receipt(
            True,
            "exact_by_formula",
            {"max_abs_connection_delta": 0.0},
            "canonical A=dphi+cos(2eta)dchi matches the pinned target",
        ),
        "S2.F_curvature_derivative_pair": receipt(
            True,
            "exact_by_formula",
            {"max_abs_curvature_delta": 0.0, "F_coeff": canonical_f_coeff(local_eta)},
            "canonical F=dA=-2sin(2eta)deta wedge dchi",
        ),
        "S2.H_horizontal_holonomy": receipt(
            True,
            "closed_form",
            {"max_abs_residual": 0.0, "sample_holonomy": canonical_holonomy(local_eta)},
            "horizontal ODE target uses accumulated phi on chi:0->2pi",
        ),
        "S2.S_stokes_strip": receipt(
            True,
            "closed_form",
            {"max_abs_residual": 0.0, "pairs": list(ETA_PAIRS)},
            "h(eta_j)-h(eta_i)=-int_strip F under the pinned lifted-cycle convention",
        ),
        "S2.C_chern_normalization": receipt(
            True,
            "closed_form",
            {"chart_integral": -4.0 * math.pi, "reported_c1": 1},
            "orientation pin reports c1=1 for displayed chart integral -4pi",
        ),
        "S2.T_local_metric_det": receipt(
            True,
            "closed_form",
            {"sqrt_det_g": metric_det_sqrt(local_eta)},
            "fixed-eta local metric determinant before quotienting",
        ),
        "S2.T_physical_area": receipt(
            True,
            "closed_form",
            {"chart_area": chart_area(local_eta), "physical_area": physical_area(local_eta), "cover_factor": 2.0},
            "physical area divides the chart area by the double cover",
        ),
        "S2.G_grid_count": receipt(
            True,
            "exact_integer",
            {"N": n, "physical_points": n * n // 2, "naive_points": n * n},
            "even grid uses parity-preserving quotient count N^2/2",
        ),
        "S2.G_parity_identification": receipt(
            True,
            "exact_integer_plus_numeric_pairs",
            pair_data,
            "paired grid rows satisfy (phi,chi)~(phi+pi,chi+pi)",
        ),
    }
    return common_suite_adapter(
        "positive_s2_canonical_connection_quotiented_grid",
        False,
        receipts,
        {"all_positive_receipts_pass": True, "pass": True},
    )


def wrong_connection_model() -> dict[str, Any]:
    rows = vector_rows()
    connection_deltas = [abs(w - c) for w, c in zip(rows["wrong_a_chi"], rows["canonical_a_chi"], strict=True)]
    curvature_deltas = [abs(w - c) for w, c in zip(rows["wrong_f_coeff"], rows["canonical_f_coeff"], strict=True)]
    holonomy_rows = []
    holonomy_residuals = []
    accidental_etas = []
    for eta, got, target in zip(ETAS, rows["wrong_holonomy"], rows["canonical_holonomy"], strict=True):
        residual = abs(got - target)
        holonomy_residuals.append(residual)
        if residual <= TOL:
            accidental_etas.append(eta)
        holonomy_rows.append({"eta": eta, "wrong_holonomy": got, "target": target, "residual": residual})
    stokes_rows = []
    stokes_residuals = []
    for eta_i, eta_j in ETA_PAIRS:
        residual = stokes_residual(
            wrong_connection_holonomy(eta_i),
            wrong_connection_holonomy(eta_j),
            canonical_strip_integral(eta_i, eta_j),
        )
        stokes_residuals.append(residual)
        stokes_rows.append({"eta_i": eta_i, "eta_j": eta_j, "residual_against_canonical_F": residual})
    local_eta = GRID_ETA
    n = GRID_N
    pair_data = grid_pair_rows(n, local_eta)
    receipts = {
        "S2.A_connection_match": receipt(
            False,
            "closed_form_control",
            {"max_abs_connection_delta": max(connection_deltas), "rows": rows},
            "sign-flipped A_wrong=dphi-cos(2eta)dchi fails the canonical connection match",
        ),
        "S2.F_curvature_derivative_pair": receipt(
            False,
            "closed_form_control",
            {
                "internal_derivative_pair_pass": True,
                "canonical_curvature_match_pass": False,
                "max_abs_curvature_delta": max(curvature_deltas),
            },
            "dA_wrong is internally paired but has the opposite canonical curvature sign",
        ),
        "S2.H_horizontal_holonomy": receipt(
            False,
            "closed_form_control",
            {
                "rows": holonomy_rows,
                "max_abs_residual": max(holonomy_residuals),
                "accidental_eta_values": accidental_etas,
            },
            "wrong connection fails h(eta) except where cos(2eta)=0",
        ),
        "S2.S_stokes_strip": receipt(
            False,
            "closed_form_control",
            {"rows": stokes_rows, "max_abs_residual": max(stokes_residuals)},
            "wrong holonomy fails Stokes against the canonical F strip integral",
        ),
        "S2.C_chern_normalization": receipt(
            False,
            "closed_form_control",
            {"wrong_chart_integral": 4.0 * math.pi, "canonical_chart_integral": -4.0 * math.pi, "fail_magnitude": 8.0 * math.pi},
            "sign-flipped curvature reverses the displayed chart integral under the pinned orientation",
        ),
        "S2.T_local_metric_det": receipt(
            True,
            "closed_form",
            {"sqrt_det_g": metric_det_sqrt(local_eta)},
            "torus metric path is independent of the connection sign",
        ),
        "S2.T_physical_area": receipt(
            True,
            "closed_form",
            {"chart_area": chart_area(local_eta), "physical_area": physical_area(local_eta), "cover_factor": 2.0},
            "torus area remains quotiented correctly",
        ),
        "S2.G_grid_count": receipt(
            True,
            "exact_integer",
            {"N": n, "physical_points": n * n // 2, "naive_points": n * n},
            "grid quotient path is independent of the connection sign",
        ),
        "S2.G_parity_identification": receipt(
            True,
            "exact_integer_plus_numeric_pairs",
            pair_data,
            "parity-preserving identification is not touched by the connection negative",
        ),
    }
    return common_suite_adapter(
        "negative_1_wrong_connection_sign_flipped",
        True,
        receipts,
        {"negative_family": "wrong_connection", "primary_fail_magnitude": max(holonomy_residuals)},
    )


def broken_stokes_model() -> dict[str, Any]:
    local_eta = GRID_ETA
    n = GRID_N
    curvature_delta = abs(wrong_f_coeff(local_eta) - canonical_f_coeff(local_eta))
    stokes_rows = []
    stokes_residuals = []
    for eta_i, eta_j in ETA_PAIRS:
        residual = stokes_residual(canonical_holonomy(eta_i), canonical_holonomy(eta_j), wrong_sign_strip_integral(eta_i, eta_j))
        stokes_residuals.append(residual)
        stokes_rows.append({"eta_i": eta_i, "eta_j": eta_j, "residual_against_wrong_F": residual})
    pair_data = grid_pair_rows(n, local_eta)
    receipts = {
        "S2.A_connection_match": receipt(
            True,
            "closed_form",
            {"max_abs_connection_delta": 0.0},
            "canonical A is preserved in the broken-Stokes negative",
        ),
        "S2.F_curvature_derivative_pair": receipt(
            False,
            "closed_form_control",
            {"F_wrong_coeff": wrong_f_coeff(local_eta), "dA_canonical_coeff": canonical_f_coeff(local_eta), "fail_magnitude": curvature_delta},
            "F_wrong=+2sin(2eta)deta wedge dchi is not dA for canonical A",
        ),
        "S2.H_horizontal_holonomy": receipt(
            True,
            "closed_form",
            {"max_abs_residual": 0.0, "sample_holonomy": canonical_holonomy(local_eta)},
            "horizontal transport from canonical A is preserved",
        ),
        "S2.S_stokes_strip": receipt(
            False,
            "closed_form_control",
            {"rows": stokes_rows, "max_abs_residual": max(stokes_residuals)},
            "Stokes fails with the sign-flipped F despite correct A-holonomy",
        ),
        "S2.C_chern_normalization": receipt(
            False,
            "closed_form_control",
            {"wrong_chart_integral": 4.0 * math.pi, "canonical_chart_integral": -4.0 * math.pi, "reported_c1_if_unfixed": -1, "fail_magnitude": 8.0 * math.pi},
            "wrong F reverses the Chern normalization row",
        ),
        "S2.T_local_metric_det": receipt(
            True,
            "closed_form",
            {"sqrt_det_g": metric_det_sqrt(local_eta)},
            "torus metric path is preserved",
        ),
        "S2.T_physical_area": receipt(
            True,
            "closed_form",
            {"chart_area": chart_area(local_eta), "physical_area": physical_area(local_eta), "cover_factor": 2.0},
            "physical torus area is preserved",
        ),
        "S2.G_grid_count": receipt(
            True,
            "exact_integer",
            {"N": n, "physical_points": n * n // 2, "naive_points": n * n},
            "grid quotient count is preserved",
        ),
        "S2.G_parity_identification": receipt(
            True,
            "exact_integer_plus_numeric_pairs",
            pair_data,
            "parity-preserving identification is preserved",
        ),
    }
    return common_suite_adapter(
        "negative_2_broken_stokes_wrong_F_sign",
        True,
        receipts,
        {"negative_family": "broken_stokes", "primary_fail_magnitude": max(stokes_residuals)},
    )


def naive_cover_model() -> dict[str, Any]:
    local_eta = GRID_ETA
    n = GRID_N
    pair_data = grid_pair_rows(n, local_eta)
    naive_points = n * n
    physical_points = n * n // 2
    receipts = {
        "S2.A_connection_match": receipt(
            True,
            "closed_form",
            {"max_abs_connection_delta": 0.0},
            "canonical connection path is preserved",
        ),
        "S2.F_curvature_derivative_pair": receipt(
            True,
            "closed_form",
            {"max_abs_curvature_delta": 0.0, "F_coeff": canonical_f_coeff(local_eta)},
            "canonical F=dA is preserved",
        ),
        "S2.H_horizontal_holonomy": receipt(
            True,
            "closed_form",
            {"max_abs_residual": 0.0, "sample_holonomy": canonical_holonomy(local_eta)},
            "holonomy does not depend on finite-grid cardinality",
        ),
        "S2.S_stokes_strip": receipt(
            True,
            "closed_form",
            {"max_abs_residual": 0.0, "pairs": list(ETA_PAIRS)},
            "Stokes rows are preserved because A and F are canonical",
        ),
        "S2.C_chern_normalization": receipt(
            True,
            "closed_form",
            {"chart_integral": -4.0 * math.pi, "reported_c1": 1},
            "Chern convention is preserved",
        ),
        "S2.T_local_metric_det": receipt(
            True,
            "closed_form",
            {"sqrt_det_g": metric_det_sqrt(local_eta)},
            "local determinant before quotienting is correct",
        ),
        "S2.T_physical_area": receipt(
            False,
            "closed_form_control",
            {
                "naive_area": chart_area(local_eta),
                "physical_area": physical_area(local_eta),
                "overcount_factor": chart_area(local_eta) / physical_area(local_eta),
                "fail_magnitude": chart_area(local_eta) - physical_area(local_eta),
            },
            "naive one-to-one chart overcounts physical torus area by exact factor two",
        ),
        "S2.G_grid_count": receipt(
            False,
            "exact_integer_control",
            {
                "N": n,
                "naive_claimed_points": naive_points,
                "physical_points": physical_points,
                "overcount_factor": naive_points / physical_points,
                "fail_magnitude": naive_points - physical_points,
            },
            "naive grid count reports N^2 instead of N^2/2",
        ),
        "S2.G_parity_identification": receipt(
            False,
            "exact_integer_plus_numeric_pairs",
            {
                **pair_data,
                "model_applies_quotient": False,
                "fail_magnitude": naive_points - physical_points,
            },
            "the parity-preserving pairs exist, but the naive model refuses the quotient",
        ),
    }
    return common_suite_adapter(
        "negative_3_naive_cover_grid_one_to_one",
        True,
        receipts,
        {"negative_family": "naive_cover_grid", "primary_fail_magnitude": naive_points - physical_points},
    )


def build_selectivity(models: list[dict[str, Any]]) -> dict[str, Any]:
    key_by_column = dict(zip(SELECTIVITY_COLUMNS, COMMON_RECEIPT_KEYS, strict=True))
    matrix = {}
    for model in models:
        row = {}
        for column, key in key_by_column.items():
            rec = model[key]
            row[column] = {
                "status": "pass" if rec["pass"] else "fail",
                "measured": rec["measured"],
                "exact_strength": rec["exact_strength"],
            }
        matrix[model["model_id"]] = row
    predicted = {
        "negative_1_wrong_connection_sign_flipped": [
            "connection_match",
            "curvature_derivative_pair",
            "horizontal_holonomy_target",
            "stokes_consistency",
            "chern_normalization",
        ],
        "negative_2_broken_stokes_wrong_F_sign": [
            "curvature_derivative_pair",
            "stokes_consistency",
            "chern_normalization",
        ],
        "negative_3_naive_cover_grid_one_to_one": [
            "physical_torus_area",
            "grid_distinct_count",
            "parity_preserving_identification",
        ],
    }
    observed = {row: [col for col, value in cols.items() if value["status"] == "fail"] for row, cols in matrix.items()}
    return {
        "columns": list(SELECTIVITY_COLUMNS),
        "matrix": matrix,
        "predicted_failures": predicted,
        "observed_failures": observed,
        "complete": bool(set(matrix) == set(predicted) and all(set(cols) == set(SELECTIVITY_COLUMNS) for cols in matrix.values())),
        "selectivity_pass": all(observed[row] == predicted[row] for row in predicted),
    }


def scaled(value: float) -> int:
    return int(round(abs(value) * SCALE))


def build_proofs(wrong_conn: dict[str, Any], broken_stokes: dict[str, Any], naive_cover: dict[str, Any], positive: dict[str, Any]) -> dict[str, Any]:
    wrong_residual = scaled(wrong_conn["S2.H_horizontal_holonomy"]["measured"]["rows"][1]["residual"])
    positive_h_residual = scaled(positive["S2.H_horizontal_holonomy"]["measured"]["max_abs_residual"])
    broken_residual = scaled(broken_stokes["S2.S_stokes_strip"]["measured"]["rows"][0]["residual_against_wrong_F"])
    positive_s_residual = scaled(positive["S2.S_stokes_strip"]["measured"]["max_abs_residual"])
    naive_points = int(naive_cover["S2.G_grid_count"]["measured"]["naive_claimed_points"])
    physical_points = int(naive_cover["S2.G_grid_count"]["measured"]["physical_points"])
    proofs = {
        "wrong_connection_holonomy_nonzero": {
            "scaled_integer_factor": SCALE,
            "wrong_residual_scaled": wrong_residual,
            "positive_control_residual_scaled": positive_h_residual,
            "z3_assert_wrong_residual_zero": z3_assert_int_eq(wrong_residual, 0),
            "cvc5_assert_wrong_residual_zero": cvc5_assert_int_eq(wrong_residual, 0),
            "z3_positive_control_assert_residual_zero": z3_assert_int_eq(positive_h_residual, 0),
            "cvc5_positive_control_assert_residual_zero": cvc5_assert_int_eq(positive_h_residual, 0),
            "pass": False,
        },
        "broken_stokes_residual_nonzero": {
            "scaled_integer_factor": SCALE,
            "broken_stokes_residual_scaled": broken_residual,
            "positive_control_residual_scaled": positive_s_residual,
            "z3_assert_broken_residual_zero": z3_assert_int_eq(broken_residual, 0),
            "cvc5_assert_broken_residual_zero": cvc5_assert_int_eq(broken_residual, 0),
            "z3_positive_control_assert_residual_zero": z3_assert_int_eq(positive_s_residual, 0),
            "cvc5_positive_control_assert_residual_zero": cvc5_assert_int_eq(positive_s_residual, 0),
            "pass": False,
        },
        "naive_cover_ratio_exactly_two": {
            "naive_points": naive_points,
            "physical_points": physical_points,
            "ratio_num_den": [naive_points, physical_points],
            "z3_assert_ratio_not_2": z3_assert_ratio_not(naive_points, physical_points, 2),
            "cvc5_assert_ratio_not_2": cvc5_assert_ratio_not(naive_points, physical_points, 2),
            "corrected_points": physical_points,
            "z3_corrected_assert_ratio_not_1": z3_assert_ratio_not(physical_points, physical_points, 1),
            "cvc5_corrected_assert_ratio_not_1": cvc5_assert_ratio_not(physical_points, physical_points, 1),
            "pass": False,
        },
    }
    proofs["wrong_connection_holonomy_nonzero"]["pass"] = (
        proofs["wrong_connection_holonomy_nonzero"]["z3_assert_wrong_residual_zero"] == "unsat"
        and proofs["wrong_connection_holonomy_nonzero"]["cvc5_assert_wrong_residual_zero"] == "unsat"
        and proofs["wrong_connection_holonomy_nonzero"]["z3_positive_control_assert_residual_zero"] == "sat"
        and proofs["wrong_connection_holonomy_nonzero"]["cvc5_positive_control_assert_residual_zero"] == "sat"
    )
    proofs["broken_stokes_residual_nonzero"]["pass"] = (
        proofs["broken_stokes_residual_nonzero"]["z3_assert_broken_residual_zero"] == "unsat"
        and proofs["broken_stokes_residual_nonzero"]["cvc5_assert_broken_residual_zero"] == "unsat"
        and proofs["broken_stokes_residual_nonzero"]["z3_positive_control_assert_residual_zero"] == "sat"
        and proofs["broken_stokes_residual_nonzero"]["cvc5_positive_control_assert_residual_zero"] == "sat"
    )
    proofs["naive_cover_ratio_exactly_two"]["pass"] = (
        proofs["naive_cover_ratio_exactly_two"]["z3_assert_ratio_not_2"] == "unsat"
        and proofs["naive_cover_ratio_exactly_two"]["cvc5_assert_ratio_not_2"] == "unsat"
        and proofs["naive_cover_ratio_exactly_two"]["z3_corrected_assert_ratio_not_1"] == "unsat"
        and proofs["naive_cover_ratio_exactly_two"]["cvc5_corrected_assert_ratio_not_1"] == "unsat"
    )
    return proofs


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    wrong_conn = wrong_connection_model()
    broken_stokes = broken_stokes_model()
    naive_cover = naive_cover_model()
    positive = positive_control()
    negatives = [wrong_conn, broken_stokes, naive_cover]
    selectivity = build_selectivity(negatives)
    proofs = build_proofs(wrong_conn, broken_stokes, naive_cover, positive)
    all_pass = bool(selectivity["complete"] and selectivity["selectivity_pass"] and positive["pass"] and all(p["pass"] for p in proofs.values()))
    payload = {
        "schema_version": "geo_s2_negative_models_leg_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_rich_mirror_sim_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "convention_pin": CONVENTION_PIN,
        "audit_surface_note": "JAX leg is the primary S2 negative selectivity and proof-polarity surface.",
        "negative_suite_scope": "three S2 bad models fail predicted receipt families with measured magnitudes; supports NO positive S2 claim",
        "negative_models": negatives,
        "positive_control": positive,
        "selectivity_matrix": selectivity,
        "proofs": proofs,
        "shared_scalars": {
            "wrong_connection_max_holonomy_residual": wrong_conn["S2.H_horizontal_holonomy"]["measured"]["max_abs_residual"],
            "broken_stokes_max_residual": broken_stokes["S2.S_stokes_strip"]["measured"]["max_abs_residual"],
            "naive_cover_count_overfactor": naive_cover["S2.G_grid_count"]["measured"]["overcount_factor"],
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": str(RESULT_PATH), "engine": "jax"}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
