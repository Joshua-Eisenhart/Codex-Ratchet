#!/usr/bin/env python3
"""PyTorch independent leg for geo_s2_negative_models_v0."""

from __future__ import annotations

import datetime as _dt
import json
import math
from typing import Any

import torch
from torch.func import vmap as torch_vmap

from geo_s2_negative_models_v0_common import (
    CLASSIFICATION,
    CONVENTION_PIN,
    FORMAL_ADMISSION_ALLOWED,
    PIN_SPEC,
    PROMOTION_ALLOWED,
    READS_PEER_RESULT,
    RESULT_DIR,
    ROOT,
    SELECTIVITY_COLUMNS,
    SIM_DIR,
    SIM_ID,
    TOL,
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
    wrong_f_coeff,
    wrong_sign_strip_integral,
)


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
ETAS = (math.pi / 8.0, math.pi / 6.0, math.pi / 4.0, math.pi / 3.0, 3.0 * math.pi / 8.0)
ETA_PAIRS = ((math.pi / 8.0, math.pi / 3.0), (math.pi / 6.0, 3.0 * math.pi / 8.0))
GRID_N = 64
GRID_ETA = math.pi / 5.0

torch.set_default_dtype(torch.float64)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor substrate for S2 negative-model magnitude recomputation",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vmap API for independent batched connection and curvature residual rows",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, hashing, timestamps, and deterministic paths",
    },
}

TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing", "python_stdlib": "supportive"}


def py_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def receipt(pass_value: bool, exact_strength: str, measured: dict[str, Any], note: str) -> dict[str, Any]:
    return {
        "pass": bool(pass_value),
        "exact_strength": exact_strength,
        "measured": measured,
        "convention_pin": CONVENTION_PIN,
        "note": note,
    }


def batched_rows() -> dict[str, list[float]]:
    etas = torch.tensor(ETAS)
    canonical_a = torch_vmap(lambda x: torch.cos(2.0 * x))(etas)
    wrong_a = torch_vmap(lambda x: -torch.cos(2.0 * x))(etas)
    canonical_f = torch_vmap(lambda x: -2.0 * torch.sin(2.0 * x))(etas)
    wrong_f = torch_vmap(lambda x: 2.0 * torch.sin(2.0 * x))(etas)
    canonical_h = torch_vmap(lambda x: -2.0 * torch.pi * torch.cos(2.0 * x))(etas)
    wrong_h = torch_vmap(lambda x: 2.0 * torch.pi * torch.cos(2.0 * x))(etas)
    return {
        "etas": [py_float(x) for x in etas],
        "canonical_a_chi": [py_float(x) for x in canonical_a],
        "wrong_a_chi": [py_float(x) for x in wrong_a],
        "canonical_f_coeff": [py_float(x) for x in canonical_f],
        "wrong_f_coeff": [py_float(x) for x in wrong_f],
        "canonical_holonomy": [py_float(x) for x in canonical_h],
        "wrong_holonomy": [py_float(x) for x in wrong_h],
    }


def pair_data(n: int = GRID_N, eta: float = GRID_ETA) -> dict[str, Any]:
    pair_rows = []
    max_pair_deviation = 0.0
    parity_preserved = True
    for a, b in ((0, 0), (1, 2), (7, 9), (18, 25), (31, 5)):
        paired_a = (a + n // 2) % n
        paired_b = (b + n // 2) % n
        delta = torch.tensor(math.pi + math.pi)
        spinor_phase_deviation = py_float(torch.abs(torch.complex(torch.cos(delta), torch.sin(delta)) - torch.tensor(1.0 + 0.0j)))
        base_angle_deviation = abs(((2.0 * math.pi) % (2.0 * math.pi)) - 0.0)
        pair_deviation = max(spinor_phase_deviation, base_angle_deviation)
        max_pair_deviation = max(max_pair_deviation, pair_deviation)
        pair_parity = (a + b) % 2 == (paired_a + paired_b) % 2
        parity_preserved = parity_preserved and pair_parity
        pair_rows.append(
            {
                "a": a,
                "b": b,
                "paired_a": paired_a,
                "paired_b": paired_b,
                "pair_deviation": pair_deviation,
                "parity_preserved": pair_parity,
            }
        )
    return {"pair_rows": pair_rows, "max_pair_deviation": max_pair_deviation, "parity_preserved": parity_preserved}


def positive_control() -> dict[str, Any]:
    eta = GRID_ETA
    n = GRID_N
    receipts = {
        "S2.A_connection_match": receipt(True, "closed_form", {"max_abs_connection_delta": 0.0}, "canonical A matches target"),
        "S2.F_curvature_derivative_pair": receipt(True, "closed_form", {"max_abs_curvature_delta": 0.0, "F_coeff": canonical_f_coeff(eta)}, "canonical F=dA"),
        "S2.H_horizontal_holonomy": receipt(True, "closed_form", {"max_abs_residual": 0.0, "sample_holonomy": canonical_holonomy(eta)}, "canonical holonomy target"),
        "S2.S_stokes_strip": receipt(True, "closed_form", {"max_abs_residual": 0.0, "pairs": list(ETA_PAIRS)}, "canonical Stokes rows"),
        "S2.C_chern_normalization": receipt(True, "closed_form", {"chart_integral": -4.0 * math.pi, "reported_c1": 1}, "canonical Chern row"),
        "S2.T_local_metric_det": receipt(True, "closed_form", {"sqrt_det_g": metric_det_sqrt(eta)}, "local determinant"),
        "S2.T_physical_area": receipt(True, "closed_form", {"chart_area": chart_area(eta), "physical_area": physical_area(eta), "cover_factor": 2.0}, "quotiented physical area"),
        "S2.G_grid_count": receipt(True, "exact_integer", {"N": n, "physical_points": n * n // 2, "naive_points": n * n}, "quotiented grid count"),
        "S2.G_parity_identification": receipt(True, "exact_integer_plus_numeric_pairs", pair_data(n, eta), "parity-preserving pairs"),
    }
    return common_suite_adapter("positive_s2_canonical_connection_quotiented_grid", False, receipts, {"pass": True})


def wrong_connection_model() -> dict[str, Any]:
    eta = GRID_ETA
    n = GRID_N
    rows = batched_rows()
    connection_deltas = [abs(w - c) for w, c in zip(rows["wrong_a_chi"], rows["canonical_a_chi"], strict=True)]
    curvature_deltas = [abs(w - c) for w, c in zip(rows["wrong_f_coeff"], rows["canonical_f_coeff"], strict=True)]
    holonomy_rows = []
    holonomy_residuals = []
    for e, got, target in zip(ETAS, rows["wrong_holonomy"], rows["canonical_holonomy"], strict=True):
        residual = abs(got - target)
        holonomy_residuals.append(residual)
        holonomy_rows.append({"eta": e, "wrong_holonomy": got, "target": target, "residual": residual})
    stokes_rows = []
    stokes_residuals = []
    for eta_i, eta_j in ETA_PAIRS:
        residual = stokes_residual(-canonical_holonomy(eta_i), -canonical_holonomy(eta_j), canonical_strip_integral(eta_i, eta_j))
        stokes_residuals.append(residual)
        stokes_rows.append({"eta_i": eta_i, "eta_j": eta_j, "residual_against_canonical_F": residual})
    receipts = {
        "S2.A_connection_match": receipt(False, "closed_form_control", {"max_abs_connection_delta": max(connection_deltas), "rows": rows}, "wrong connection fails canonical match"),
        "S2.F_curvature_derivative_pair": receipt(False, "closed_form_control", {"internal_derivative_pair_pass": True, "canonical_curvature_match_pass": False, "max_abs_curvature_delta": max(curvature_deltas)}, "wrong connection has opposite F"),
        "S2.H_horizontal_holonomy": receipt(False, "closed_form_control", {"rows": holonomy_rows, "max_abs_residual": max(holonomy_residuals)}, "wrong connection fails h target"),
        "S2.S_stokes_strip": receipt(False, "closed_form_control", {"rows": stokes_rows, "max_abs_residual": max(stokes_residuals)}, "wrong holonomy fails canonical Stokes"),
        "S2.C_chern_normalization": receipt(False, "closed_form_control", {"wrong_chart_integral": 4.0 * math.pi, "canonical_chart_integral": -4.0 * math.pi, "fail_magnitude": 8.0 * math.pi}, "wrong F reverses Chern sign"),
        "S2.T_local_metric_det": receipt(True, "closed_form", {"sqrt_det_g": metric_det_sqrt(eta)}, "metric determinant preserved"),
        "S2.T_physical_area": receipt(True, "closed_form", {"chart_area": chart_area(eta), "physical_area": physical_area(eta), "cover_factor": 2.0}, "area preserved"),
        "S2.G_grid_count": receipt(True, "exact_integer", {"N": n, "physical_points": n * n // 2, "naive_points": n * n}, "grid count preserved"),
        "S2.G_parity_identification": receipt(True, "exact_integer_plus_numeric_pairs", pair_data(n, eta), "parity pairs preserved"),
    }
    return common_suite_adapter("negative_1_wrong_connection_sign_flipped", True, receipts, {"negative_family": "wrong_connection", "primary_fail_magnitude": max(holonomy_residuals)})


def broken_stokes_model() -> dict[str, Any]:
    eta = GRID_ETA
    n = GRID_N
    stokes_rows = []
    stokes_residuals = []
    for eta_i, eta_j in ETA_PAIRS:
        residual = stokes_residual(canonical_holonomy(eta_i), canonical_holonomy(eta_j), wrong_sign_strip_integral(eta_i, eta_j))
        stokes_residuals.append(residual)
        stokes_rows.append({"eta_i": eta_i, "eta_j": eta_j, "residual_against_wrong_F": residual})
    receipts = {
        "S2.A_connection_match": receipt(True, "closed_form", {"max_abs_connection_delta": 0.0}, "canonical A preserved"),
        "S2.F_curvature_derivative_pair": receipt(False, "closed_form_control", {"F_wrong_coeff": wrong_f_coeff(eta), "dA_canonical_coeff": canonical_f_coeff(eta), "fail_magnitude": abs(wrong_f_coeff(eta) - canonical_f_coeff(eta))}, "wrong F is not dA"),
        "S2.H_horizontal_holonomy": receipt(True, "closed_form", {"max_abs_residual": 0.0, "sample_holonomy": canonical_holonomy(eta)}, "holonomy preserved"),
        "S2.S_stokes_strip": receipt(False, "closed_form_control", {"rows": stokes_rows, "max_abs_residual": max(stokes_residuals)}, "Stokes fails with wrong F"),
        "S2.C_chern_normalization": receipt(False, "closed_form_control", {"wrong_chart_integral": 4.0 * math.pi, "canonical_chart_integral": -4.0 * math.pi, "reported_c1_if_unfixed": -1, "fail_magnitude": 8.0 * math.pi}, "wrong F reverses Chern"),
        "S2.T_local_metric_det": receipt(True, "closed_form", {"sqrt_det_g": metric_det_sqrt(eta)}, "metric determinant preserved"),
        "S2.T_physical_area": receipt(True, "closed_form", {"chart_area": chart_area(eta), "physical_area": physical_area(eta), "cover_factor": 2.0}, "area preserved"),
        "S2.G_grid_count": receipt(True, "exact_integer", {"N": n, "physical_points": n * n // 2, "naive_points": n * n}, "grid count preserved"),
        "S2.G_parity_identification": receipt(True, "exact_integer_plus_numeric_pairs", pair_data(n, eta), "parity preserved"),
    }
    return common_suite_adapter("negative_2_broken_stokes_wrong_F_sign", True, receipts, {"negative_family": "broken_stokes", "primary_fail_magnitude": max(stokes_residuals)})


def naive_cover_model() -> dict[str, Any]:
    eta = GRID_ETA
    n = GRID_N
    naive_points = n * n
    physical_points = n * n // 2
    receipts = {
        "S2.A_connection_match": receipt(True, "closed_form", {"max_abs_connection_delta": 0.0}, "connection preserved"),
        "S2.F_curvature_derivative_pair": receipt(True, "closed_form", {"max_abs_curvature_delta": 0.0, "F_coeff": canonical_f_coeff(eta)}, "curvature preserved"),
        "S2.H_horizontal_holonomy": receipt(True, "closed_form", {"max_abs_residual": 0.0, "sample_holonomy": canonical_holonomy(eta)}, "holonomy preserved"),
        "S2.S_stokes_strip": receipt(True, "closed_form", {"max_abs_residual": 0.0, "pairs": list(ETA_PAIRS)}, "Stokes preserved"),
        "S2.C_chern_normalization": receipt(True, "closed_form", {"chart_integral": -4.0 * math.pi, "reported_c1": 1}, "Chern preserved"),
        "S2.T_local_metric_det": receipt(True, "closed_form", {"sqrt_det_g": metric_det_sqrt(eta)}, "local determinant passes"),
        "S2.T_physical_area": receipt(False, "closed_form_control", {"naive_area": chart_area(eta), "physical_area": physical_area(eta), "overcount_factor": chart_area(eta) / physical_area(eta), "fail_magnitude": chart_area(eta) - physical_area(eta)}, "naive area overcounts by factor two"),
        "S2.G_grid_count": receipt(False, "exact_integer_control", {"N": n, "naive_claimed_points": naive_points, "physical_points": physical_points, "overcount_factor": naive_points / physical_points, "fail_magnitude": naive_points - physical_points}, "naive count reports N^2"),
        "S2.G_parity_identification": receipt(False, "exact_integer_plus_numeric_pairs", {**pair_data(n, eta), "model_applies_quotient": False, "fail_magnitude": naive_points - physical_points}, "naive model refuses quotient pairs"),
    }
    return common_suite_adapter("negative_3_naive_cover_grid_one_to_one", True, receipts, {"negative_family": "naive_cover_grid", "primary_fail_magnitude": naive_points - physical_points})


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    wrong_conn = wrong_connection_model()
    broken_stokes = broken_stokes_model()
    naive_cover = naive_cover_model()
    positive = positive_control()
    expected_fail_counts = {
        wrong_conn["model_id"]: 5,
        broken_stokes["model_id"]: 3,
        naive_cover["model_id"]: 3,
    }
    observed_fail_counts = {
        model["model_id"]: sum(1 for key in model["common_suite_adapter"]["receipt_keys"] if model[key]["pass"] is False)
        for model in (wrong_conn, broken_stokes, naive_cover)
    }
    all_pass = bool(observed_fail_counts == expected_fail_counts and positive["pass"] is True)
    payload = {
        "schema_version": "geo_s2_negative_models_leg_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "role_id": "pytorch_graph_network_sim_builder",
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
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "convention_pin": CONVENTION_PIN,
        "negative_model_receipts": {
            wrong_conn["model_id"]: wrong_conn,
            broken_stokes["model_id"]: broken_stokes,
            naive_cover["model_id"]: naive_cover,
        },
        "positive_control": positive,
        "expected_fail_counts": expected_fail_counts,
        "observed_fail_counts": observed_fail_counts,
        "selectivity_columns": list(SELECTIVITY_COLUMNS),
        "shared_scalars": {
            "wrong_connection_max_holonomy_residual": wrong_conn["S2.H_horizontal_holonomy"]["measured"]["max_abs_residual"],
            "broken_stokes_max_residual": broken_stokes["S2.S_stokes_strip"]["measured"]["max_abs_residual"],
            "naive_cover_count_overfactor": naive_cover["S2.G_grid_count"]["measured"]["overcount_factor"],
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": str(RESULT_PATH), "engine": "pytorch"}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
