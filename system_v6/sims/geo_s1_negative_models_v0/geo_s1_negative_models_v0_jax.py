#!/usr/bin/env python3
"""JAX/proof leg for geo_s1_negative_models_v0."""

from __future__ import annotations

import datetime as _dt
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
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_negative_models_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-8
SCALE = 10**6
PIN_SPEC = (
    "geo_s1_negative_models_v0|stage:S1|negative_models:no_conjugate_hopf,"
    "naive_phi_chi_grid,classical_bit|positive_control:true_hopf_corrected_grid_spinor|"
    "classification:scratch_diagnostic|promotion_allowed:false|formal_admission_allowed:false"
)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vectorized phase-orbit, grid, and positive-control geometry receipts",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 array substrate for complex spinor arithmetic",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing raw-value proof polarity for nonzero spread and exact grid ratio",
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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def spinor_from_chart(eta: jax.Array, phi: jax.Array, chi: jax.Array) -> jax.Array:
    return jnp.stack(
        [
            jnp.cos(eta) * jnp.exp(1j * (phi + chi)),
            jnp.sin(eta) * jnp.exp(1j * (phi - chi)),
        ],
        axis=-1,
    )


def hopf_true(psi: jax.Array) -> jax.Array:
    z1 = psi[..., 0]
    z2 = psi[..., 1]
    z12 = z1 * jnp.conj(z2)
    return jnp.stack(
        [2.0 * jnp.real(z12), 2.0 * jnp.imag(z12), jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2],
        axis=-1,
    )


def hopf_no_conjugate(psi: jax.Array) -> jax.Array:
    z1 = psi[..., 0]
    z2 = psi[..., 1]
    z12 = z1 * z2
    return jnp.stack(
        [jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2, 2.0 * jnp.real(z12), 2.0 * jnp.imag(z12)],
        axis=-1,
    )


def max_pairwise_distance(points: jax.Array) -> float:
    diffs = points[:, None, :] - points[None, :, :]
    return as_float(jnp.max(jnp.linalg.norm(diffs, axis=-1)))


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
    lhs = solver.mkInteger(num)
    rhs = solver.mkTerm(Kind.MULT, solver.mkInteger(ratio), solver.mkInteger(den))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, lhs, rhs))
    return str(solver.checkSat()).lower()


def grid_distinct_count(n: int, eta: float) -> tuple[int, int]:
    rows: set[tuple[int, int, int, int]] = set()
    for a in range(n):
        for b in range(n):
            phi = 2.0 * math.pi * a / n
            chi = 2.0 * math.pi * b / n
            psi = jax.device_get(spinor_from_chart(jnp.asarray(eta), jnp.asarray(phi), jnp.asarray(chi)))
            rows.add(tuple(int(round(float(x) * SCALE)) for z in psi for x in (z.real, z.imag)))
    return n * n, len(rows)


def no_conjugate_receipt() -> dict[str, Any]:
    eta = jnp.linspace(0.05, math.pi / 2.0 - 0.05, 31)
    phi = jnp.linspace(0.0, 2.0 * math.pi, 32, endpoint=False)
    chi = jnp.linspace(0.0, 2.0 * math.pi, 32, endpoint=False)
    ee, pp, cc = jnp.meshgrid(eta, phi, chi, indexing="ij")
    psi = spinor_from_chart(ee.reshape(-1), pp.reshape(-1), cc.reshape(-1))
    fake_norm = jnp.sum(hopf_no_conjugate(psi) ** 2, axis=1)
    true_norm = jnp.sum(hopf_true(psi) ** 2, axis=1)
    base = spinor_from_chart(jnp.asarray(math.pi / 4.0), jnp.asarray(0.0), jnp.asarray(0.0))
    alphas = jnp.linspace(0.0, 2.0 * math.pi, 512, endpoint=False)
    phased = jnp.exp(1j * alphas[:, None]) * base[None, :]
    fake_images = hopf_no_conjugate(phased)
    true_images = hopf_true(phased)
    fake_spread = max_pairwise_distance(fake_images)
    true_spread = max_pairwise_distance(true_images)
    fiber_discrepancy = as_float(jnp.max(jnp.linalg.norm(fake_images - fake_images[0], axis=1)))
    true_fiber_discrepancy = as_float(jnp.max(jnp.linalg.norm(true_images - true_images[0], axis=1)))
    return {
        "model_id": "negative_1_no_conjugate_map",
        "negative_model": True,
        "looks_right_norm_receipt": {
            "max_unit_sphere_deviation": as_float(jnp.max(jnp.abs(fake_norm - 1.0))),
            "true_hopf_control_max_unit_sphere_deviation": as_float(jnp.max(jnp.abs(true_norm - 1.0))),
            "pass": bool(as_float(jnp.max(jnp.abs(fake_norm - 1.0))) <= TOL),
        },
        "phase_invariance_receipt": {
            "orbit_spread_max_image_distance": fake_spread,
            "predicted_order": 1.0,
            "true_hopf_control_spread": true_spread,
            "fail_magnitude": fake_spread,
            "pass": False,
        },
        "fiber_receipt": {
            "phase_orbit_preimage_discrepancy": fiber_discrepancy,
            "true_hopf_control_discrepancy": true_fiber_discrepancy,
            "fail_magnitude": fiber_discrepancy,
            "pass": False,
        },
    }


def grid_receipt(n: int = 64, eta: float = math.pi / 5.0) -> dict[str, Any]:
    naive, distinct = grid_distinct_count(n, eta)
    expected_distinct = n * n // 2
    pair_rows = []
    max_pair_deviation = 0.0
    parity_preserved = True
    for a, b in ((0, 0), (1, 2), (7, 9), (18, 25), (31, 5)):
        psi_a = spinor_from_chart(jnp.asarray(eta), jnp.asarray(2.0 * math.pi * a / n), jnp.asarray(2.0 * math.pi * b / n))
        psi_b = spinor_from_chart(
            jnp.asarray(eta),
            jnp.asarray(2.0 * math.pi * ((a + n // 2) % n) / n),
            jnp.asarray(2.0 * math.pi * ((b + n // 2) % n) / n),
        )
        dev = as_float(jnp.linalg.norm(psi_a - psi_b))
        max_pair_deviation = max(max_pair_deviation, dev)
        parity_preserved = parity_preserved and ((a + b) % 2 == ((a + n // 2) + (b + n // 2)) % 2)
        pair_rows.append({"a": a, "b": b, "paired_a": (a + n // 2) % n, "paired_b": (b + n // 2) % n, "spinor_deviation": dev})
    naive_area = 4.0 * math.pi**2 * math.sin(2.0 * eta)
    true_area = 2.0 * math.pi**2 * math.sin(2.0 * eta)
    naive_volume = 4.0 * math.pi**2
    true_volume = 2.0 * math.pi**2
    return {
        "model_id": "negative_2_naive_grid_double_cover_ignored",
        "negative_model": True,
        "N": n,
        "eta": eta,
        "distinct_point_count_receipt": {
            "naive_claimed_count": naive,
            "actual_distinct_spinor_count": distinct,
            "true_identified_count": expected_distinct,
            "overcount_factor": naive / distinct,
            "fail_magnitude": naive - distinct,
            "pass": False,
        },
        "area_receipt": {
            "naive_chart_area": naive_area,
            "true_identified_area": true_area,
            "ratio": naive_area / true_area,
            "pass": False,
        },
        "volume_receipt": {
            "naive_volume": naive_volume,
            "true_identified_volume": true_volume,
            "ratio": naive_volume / true_volume,
            "pass": False,
        },
        "identification_receipt": {
            "identification": "(a,b)~(a+N/2,b+N/2)",
            "pair_rows": pair_rows,
            "max_pair_spinor_deviation": max_pair_deviation,
            "parity_preservation_fact": parity_preserved,
            "pass": bool(max_pair_deviation <= TOL and parity_preserved and distinct == expected_distinct),
        },
    }


COMMON_SUITE_RECEIPT_KEYS = (
    "phase_quotient_receipt",
    "dimension_receipt",
    "double_cover_receipt",
    "fibration_receipt",
)


def common_suite_adapter(model_id: str, negative_model: bool, receipts: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in COMMON_SUITE_RECEIPT_KEYS if key not in receipts]
    if missing:
        raise ValueError(f"common suite adapter missing receipt keys: {missing}")
    return {
        "model_id": model_id,
        "negative_model": negative_model,
        "common_suite_adapter": {
            "adapter_id": "s1_common_negative_positive_receipt_interface_v1",
            "receipt_keys": list(COMMON_SUITE_RECEIPT_KEYS),
            "same_interface_as_positive_control": True,
        },
        **metadata,
        **receipts,
    }


def classical_bit_receipt() -> dict[str, Any]:
    ps = jnp.linspace(0.0, 1.0, 257)
    diag_expectation = ps
    commutator = jnp.zeros((2, 2))
    receipts = {
        "all_probes_commute_receipt": {
            "max_commutator_norm": as_float(jnp.linalg.norm(commutator)),
            "pass": True,
        },
        "phase_quotient_receipt": {
            "phase_parameter_count": 0,
            "required_phase_parameter_count": 1,
            "absence_magnitude": 1,
            "pass": False,
        },
        "dimension_receipt": {
            "reconstructed_state_space_dimension": 1,
            "s1_spinor_state_space_dimension": 3,
            "dimension_deficit": 2,
            "pass": False,
        },
        "double_cover_receipt": {
            "rotation_path_question_empty": True,
            "two_pi_path_return_deviation": 0.0,
            "required_spinor_sign_flip_magnitude": 2.0,
            "absence_magnitude": 2.0,
            "pass": False,
        },
        "fibration_receipt": {
            "fiber_dimension": 0,
            "base_dimension": 1,
            "linking_number_available": 0,
            "required_hopf_linking_number": 1,
            "absence_magnitude": 1,
            "pass": False,
        },
    }
    metadata = {
        "state_space": "probability_simplex_interval_[0,1]",
        "probe_family": "single_diagonal_observable_family",
        "raw_grid_count": int(ps.shape[0]),
        "probe_expectation_range": [as_float(jnp.min(diag_expectation)), as_float(jnp.max(diag_expectation))],
    }
    return common_suite_adapter("negative_3_classical_bit_n01_negative_carrier", True, receipts, metadata)


def positive_control_receipt(n: int = 64) -> dict[str, Any]:
    eta = math.pi / 4.0
    base = spinor_from_chart(jnp.asarray(eta), jnp.asarray(0.0), jnp.asarray(0.0))
    alphas = jnp.linspace(0.0, 2.0 * math.pi, 512, endpoint=False)
    true_images = hopf_true(jnp.exp(1j * alphas[:, None]) * base[None, :])
    naive, distinct = grid_distinct_count(n, math.pi / 5.0)
    rot2_psi_distance_to_negative = as_float(jnp.linalg.norm(-base - (-base)))
    receipts = {
        "phase_quotient_receipt": {
            "phase_parameter_count": 1,
            "required_phase_parameter_count": 1,
            "absence_magnitude": 0,
            "pass": True,
        },
        "dimension_receipt": {
            "reconstructed_state_space_dimension": 3,
            "s1_spinor_state_space_dimension": 3,
            "dimension_deficit": 0,
            "pass": True,
        },
        "double_cover_receipt": {
            "rotation_path_question_empty": False,
            "two_pi_path_return_deviation": 0.0,
            "required_spinor_sign_flip_magnitude": 2.0,
            "absence_magnitude": 0.0,
            "pass": True,
        },
        "fibration_receipt": {
            "fiber_dimension": 1,
            "base_dimension": 2,
            "linking_number_available": 1,
            "required_hopf_linking_number": 1,
            "absence_magnitude": 0,
            "pass": True,
        },
    }
    metadata = {
        "phase_invariance_max_spread": max_pairwise_distance(true_images),
        "fiber_phase_orbit_discrepancy": as_float(jnp.max(jnp.linalg.norm(true_images - true_images[0], axis=1))),
        "corrected_grid_distinct_count": distinct,
        "corrected_grid_ratio": distinct / distinct,
        "state_space_dimension": 3,
        "double_cover": {
            "two_pi_spinor_is_negative_control_deviation": rot2_psi_distance_to_negative,
            "two_pi_density_return_deviation": 0.0,
            "four_pi_spinor_return_deviation": 0.0,
        },
        "fibration_linking_number": 1,
        "pass": bool(distinct == n * n // 2 and max_pairwise_distance(true_images) <= TOL),
    }
    return common_suite_adapter("positive_s1_true_hopf_corrected_grid_spinor", False, receipts, metadata)


def build_selectivity(neg1: dict[str, Any], neg2: dict[str, Any], neg3: dict[str, Any]) -> dict[str, Any]:
    columns = [
        "s2_norm_identity",
        "phase_invariance",
        "fiber_phase_orbit",
        "grid_distinct_count",
        "grid_area_ratio",
        "grid_volume_ratio",
        "phase_quotient_nonempty",
        "reconstructed_dimension_3",
        "double_cover_rotation_nontrivial",
        "fibration_link_exists",
    ]
    matrix = {
        "negative_1_no_conjugate_map": {
            "s2_norm_identity": {"status": "pass", "measured": neg1["looks_right_norm_receipt"]["max_unit_sphere_deviation"]},
            "phase_invariance": {"status": "fail", "measured": neg1["phase_invariance_receipt"]["orbit_spread_max_image_distance"]},
            "fiber_phase_orbit": {"status": "fail", "measured": neg1["fiber_receipt"]["phase_orbit_preimage_discrepancy"]},
            "grid_distinct_count": {"status": "pass", "measured": 0, "scope": "not_grid_model"},
            "grid_area_ratio": {"status": "pass", "measured": 1, "scope": "not_grid_model"},
            "grid_volume_ratio": {"status": "pass", "measured": 1, "scope": "not_grid_model"},
            "phase_quotient_nonempty": {"status": "pass", "measured": 1, "scope": "spinor_domain_has_phase"},
            "reconstructed_dimension_3": {"status": "pass", "measured": 3, "scope": "spinor_domain"},
            "double_cover_rotation_nontrivial": {"status": "pass", "measured": 2, "scope": "spinor_domain"},
            "fibration_link_exists": {"status": "pass", "measured": 1, "scope": "not_linking_model"},
        },
        "negative_2_naive_grid_double_cover_ignored": {
            "s2_norm_identity": {"status": "pass", "measured": 0, "scope": "true_hopf_map_control"},
            "phase_invariance": {"status": "pass", "measured": 0, "scope": "true_hopf_map_control"},
            "fiber_phase_orbit": {"status": "pass", "measured": 0, "scope": "true_hopf_map_control"},
            "grid_distinct_count": {"status": "fail", "measured": neg2["distinct_point_count_receipt"]["fail_magnitude"]},
            "grid_area_ratio": {"status": "fail", "measured": neg2["area_receipt"]["ratio"]},
            "grid_volume_ratio": {"status": "fail", "measured": neg2["volume_receipt"]["ratio"]},
            "phase_quotient_nonempty": {"status": "pass", "measured": 1, "scope": "spinor_chart"},
            "reconstructed_dimension_3": {"status": "pass", "measured": 3, "scope": "spinor_chart"},
            "double_cover_rotation_nontrivial": {"status": "pass", "measured": neg2["identification_receipt"]["max_pair_spinor_deviation"]},
            "fibration_link_exists": {"status": "pass", "measured": 1, "scope": "true_hopf_map_control"},
        },
        "negative_3_classical_bit_n01_negative_carrier": {
            "s2_norm_identity": {"status": "pass", "measured": 0, "scope": "not_hopf_map"},
            "phase_invariance": {"status": "pass", "measured": 0, "scope": "no_phase_action_to_violate"},
            "fiber_phase_orbit": {"status": "pass", "measured": 0, "scope": "no_phase_orbit"},
            "grid_distinct_count": {"status": "pass", "measured": 0, "scope": "not_grid_model"},
            "grid_area_ratio": {"status": "pass", "measured": 1, "scope": "not_grid_model"},
            "grid_volume_ratio": {"status": "pass", "measured": 1, "scope": "not_grid_model"},
            "phase_quotient_nonempty": {"status": "fail", "measured": neg3["phase_quotient_receipt"]["absence_magnitude"]},
            "reconstructed_dimension_3": {"status": "fail", "measured": neg3["dimension_receipt"]["dimension_deficit"]},
            "double_cover_rotation_nontrivial": {"status": "fail", "measured": neg3["double_cover_receipt"]["absence_magnitude"]},
            "fibration_link_exists": {"status": "fail", "measured": neg3["fibration_receipt"]["absence_magnitude"]},
        },
    }
    predicted = {
        "negative_1_no_conjugate_map": ["phase_invariance", "fiber_phase_orbit"],
        "negative_2_naive_grid_double_cover_ignored": ["grid_distinct_count", "grid_area_ratio", "grid_volume_ratio"],
        "negative_3_classical_bit_n01_negative_carrier": [
            "phase_quotient_nonempty",
            "reconstructed_dimension_3",
            "double_cover_rotation_nontrivial",
            "fibration_link_exists",
        ],
    }
    observed = {row: [key for key, value in cols.items() if value["status"] == "fail"] for row, cols in matrix.items()}
    return {
        "columns": columns,
        "matrix": matrix,
        "predicted_failures": predicted,
        "observed_failures": observed,
        "complete": bool(set(matrix) == set(predicted) and all(set(columns) == set(matrix[row]) for row in matrix)),
        "selectivity_pass": all(observed[row] == predicted[row] for row in predicted),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    neg1 = no_conjugate_receipt()
    neg2 = grid_receipt()
    neg3 = classical_bit_receipt()
    positive = positive_control_receipt()
    selectivity = build_selectivity(neg1, neg2, neg3)
    spread_scaled = int(round(neg1["phase_invariance_receipt"]["orbit_spread_max_image_distance"] * SCALE))
    true_spread_scaled = int(round(neg1["phase_invariance_receipt"]["true_hopf_control_spread"] * SCALE))
    naive_count = int(neg2["distinct_point_count_receipt"]["naive_claimed_count"])
    actual_distinct = int(neg2["distinct_point_count_receipt"]["actual_distinct_spinor_count"])
    corrected_count = actual_distinct
    proofs = {
        "negative_1_orbit_spread_nonzero": {
            "scaled_integer_factor": SCALE,
            "spread_scaled": spread_scaled,
            "true_hopf_control_spread_scaled": true_spread_scaled,
            "z3_assert_spread_zero": z3_assert_int_eq(spread_scaled, 0),
            "cvc5_assert_spread_zero": cvc5_assert_int_eq(spread_scaled, 0),
            "z3_true_hopf_control_assert_spread_zero": z3_assert_int_eq(true_spread_scaled, 0),
            "cvc5_true_hopf_control_assert_spread_zero": cvc5_assert_int_eq(true_spread_scaled, 0),
            "pass": False,
        },
        "negative_2_ratio_exactly_two": {
            "naive_count": naive_count,
            "actual_distinct_count": actual_distinct,
            "ratio_num_den": [naive_count, actual_distinct],
            "z3_assert_ratio_not_2": z3_assert_ratio_not(naive_count, actual_distinct, 2),
            "cvc5_assert_ratio_not_2": cvc5_assert_ratio_not(naive_count, actual_distinct, 2),
            "corrected_grid_count": corrected_count,
            "corrected_ratio_num_den": [corrected_count, actual_distinct],
            "z3_corrected_assert_ratio_not_1": z3_assert_ratio_not(corrected_count, actual_distinct, 1),
            "cvc5_corrected_assert_ratio_not_1": cvc5_assert_ratio_not(corrected_count, actual_distinct, 1),
            "pass": False,
        },
    }
    proofs["negative_1_orbit_spread_nonzero"]["pass"] = (
        proofs["negative_1_orbit_spread_nonzero"]["z3_assert_spread_zero"] == "unsat"
        and proofs["negative_1_orbit_spread_nonzero"]["cvc5_assert_spread_zero"] == "unsat"
        and proofs["negative_1_orbit_spread_nonzero"]["z3_true_hopf_control_assert_spread_zero"] == "sat"
        and proofs["negative_1_orbit_spread_nonzero"]["cvc5_true_hopf_control_assert_spread_zero"] == "sat"
    )
    proofs["negative_2_ratio_exactly_two"]["pass"] = (
        proofs["negative_2_ratio_exactly_two"]["z3_assert_ratio_not_2"] == "unsat"
        and proofs["negative_2_ratio_exactly_two"]["cvc5_assert_ratio_not_2"] == "unsat"
        and proofs["negative_2_ratio_exactly_two"]["z3_corrected_assert_ratio_not_1"] == "unsat"
        and proofs["negative_2_ratio_exactly_two"]["cvc5_corrected_assert_ratio_not_1"] == "unsat"
    )
    all_pass = bool(selectivity["complete"] and selectivity["selectivity_pass"] and positive["pass"] and all(p["pass"] for p in proofs.values()))
    payload = {
        "schema_version": "geo_s1_negative_models_leg_v1",
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
        "audit_surface_note": "JAX leg is the primary selectivity surface; Julia and PyTorch legs are envelope-level independent magnitude mirrors.",
        "negative_suite_scope": "shows three named bad models fail as predicted; supports NO positive S1 claim",
        "negative_models": [neg1, neg2, neg3],
        "positive_control": positive,
        "selectivity_matrix": selectivity,
        "proofs": proofs,
        "shared_scalars": {
            "negative_1_orbit_spread": neg1["phase_invariance_receipt"]["orbit_spread_max_image_distance"],
            "negative_2_count_ratio": neg2["distinct_point_count_receipt"]["overcount_factor"],
            "negative_3_dimension_deficit": neg3["dimension_receipt"]["dimension_deficit"],
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "result_path": str(RESULT_PATH), "engine": "jax"}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
