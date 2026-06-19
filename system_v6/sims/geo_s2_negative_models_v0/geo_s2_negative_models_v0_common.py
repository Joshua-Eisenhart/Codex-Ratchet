#!/usr/bin/env python3
"""Shared receipt adapter for geo_s2_negative_models_v0."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s2_negative_models_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8
SCALE = 10**6

CONVENTION_PIN = {
    "holonomy_quantity": "accumulated_phi",
    "berry_formula": "not_reported_in_negative_suite; canonical target uses lifted torus-chart cycle h(eta)=-2*pi*cos(2*eta)",
    "phase_domain": "lifted_real",
    "base_loop_count": "chi:0->2pi torus-chart cycle, traverses Hopf base twice because base_angle=2*chi",
    "orientation_and_c1_sign": "displayed F integrates to -4*pi on the double-covered chart; orientation reports c1=1",
}

PIN_SPEC = (
    "geo_s2_negative_models_v0|stage:S2|negative_models:wrong_connection,"
    "broken_stokes,naive_cover_grid|common_adapter:s2_negative_positive_receipt_interface_v1|"
    "classification:scratch_diagnostic|promotion_allowed:false|formal_admission_allowed:false"
)

COMMON_RECEIPT_KEYS = (
    "S2.A_connection_match",
    "S2.F_curvature_derivative_pair",
    "S2.H_horizontal_holonomy",
    "S2.S_stokes_strip",
    "S2.C_chern_normalization",
    "S2.T_local_metric_det",
    "S2.T_physical_area",
    "S2.G_grid_count",
    "S2.G_parity_identification",
)

SELECTIVITY_COLUMNS = (
    "connection_match",
    "curvature_derivative_pair",
    "horizontal_holonomy_target",
    "stokes_consistency",
    "chern_normalization",
    "local_metric_determinant",
    "physical_torus_area",
    "grid_distinct_count",
    "parity_preserving_identification",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_a_chi(eta: float) -> float:
    return math.cos(2.0 * eta)


def canonical_f_coeff(eta: float) -> float:
    return -2.0 * math.sin(2.0 * eta)


def wrong_a_chi(eta: float) -> float:
    return -math.cos(2.0 * eta)


def wrong_f_coeff(eta: float) -> float:
    return 2.0 * math.sin(2.0 * eta)


def horizontal_holonomy_from_a_chi(a_chi: float) -> float:
    return -2.0 * math.pi * a_chi


def canonical_holonomy(eta: float) -> float:
    return horizontal_holonomy_from_a_chi(canonical_a_chi(eta))


def wrong_connection_holonomy(eta: float) -> float:
    return horizontal_holonomy_from_a_chi(wrong_a_chi(eta))


def strip_integral_from_f_coeff(f_coeff_integral_antiderivative_delta: float) -> float:
    return 2.0 * math.pi * f_coeff_integral_antiderivative_delta


def canonical_strip_integral(eta_i: float, eta_j: float) -> float:
    return strip_integral_from_f_coeff(math.cos(2.0 * eta_j) - math.cos(2.0 * eta_i))


def wrong_sign_strip_integral(eta_i: float, eta_j: float) -> float:
    return -canonical_strip_integral(eta_i, eta_j)


def stokes_residual(holonomy_i: float, holonomy_j: float, strip_integral: float) -> float:
    return abs((holonomy_j - holonomy_i) + strip_integral)


def metric_det_sqrt(eta: float) -> float:
    return math.sin(2.0 * eta)


def chart_area(eta: float) -> float:
    return 4.0 * math.pi**2 * metric_det_sqrt(eta)


def physical_area(eta: float) -> float:
    return 2.0 * math.pi**2 * metric_det_sqrt(eta)


def common_suite_adapter(
    model_id: str,
    negative_model: bool,
    receipts: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    missing = [key for key in COMMON_RECEIPT_KEYS if key not in receipts]
    if missing:
        raise ValueError(f"common suite adapter missing receipt keys: {missing}")
    for key in COMMON_RECEIPT_KEYS:
        receipt = receipts[key]
        if not isinstance(receipt, dict):
            raise TypeError(f"{key} receipt must be an object")
        receipt.setdefault("convention_pin", CONVENTION_PIN)
    return {
        "model_id": model_id,
        "negative_model": negative_model,
        "common_suite_adapter": {
            "adapter_id": "s2_negative_positive_receipt_interface_v1",
            "receipt_keys": list(COMMON_RECEIPT_KEYS),
            "selectivity_columns": list(SELECTIVITY_COLUMNS),
            "same_interface_as_positive_control": True,
        },
        **metadata,
        **receipts,
    }
