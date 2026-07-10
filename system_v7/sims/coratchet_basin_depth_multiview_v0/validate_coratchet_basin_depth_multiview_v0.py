#!/usr/bin/env python3
"""Independent fail-closed gate for the co-ratchet multiview result packet."""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    import numpy as np
except ImportError as exc:  # The gate still emits a blocked JSON receipt.
    np = None  # type: ignore[assignment]
    NUMPY_IMPORT_ERROR: ImportError | None = exc
else:
    NUMPY_IMPORT_ERROR = None


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = ROOT / "system_v7/sims/coratchet_basin_depth_multiview_v0"
RESULTS = HERE / "results"
SPEC_PATH = HERE / "spec.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
JAX_SOURCE_PATH = HERE / "run_jax.py"
JULIA_SOURCE_PATH = HERE / "run_julia.jl"
JAX_RESULT_PATH = RESULTS / "coratchet_basin_depth_multiview_v0_jax_results.json"
JULIA_RESULT_PATH = RESULTS / "coratchet_basin_depth_multiview_v0_julia_results.json"
OUTPUT_PATH = RESULTS / "coratchet_basin_depth_multiview_v0_validation.json"
CANONICAL_SOURCE_PATH = (
    ROOT / "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py"
)
FABLE_DIR = (
    ROOT
    / "system_v7/control/model_lane_receipts/coratchet_basin_multiview_20260710"
)
FABLE_RESULT_PATH = FABLE_DIR / (
    "20260710T091245Z-fable-medium-coratchet-basin-prereg-audit-97bf48b6f1f7.json"
)
FABLE_RECEIPT_PATH = FABLE_DIR / (
    "20260710T091245Z-fable-medium-coratchet-basin-prereg-audit-97bf48b6f1f7.receipt.json"
)

SIM_ID = "coratchet_basin_depth_multiview_v0"
CLASSIFICATION = "scratch_diagnostic"
PREREG_VERDICT = "LOCAL_OR_FRAGILE_INSTALLED_BASIN_ONLY"
ACCEPTED_LABEL = "INSTALLED_GLOBAL_ATTRACTING_FIXED_POINTS_GENERIC_ORDER_NOT_SELECTED"
BLOCKED_LABEL = "BLOCKED_NO_CROSS_RUNTIME_GLOBAL_CONTRACTION"
PARITY_TOL = 2.0e-12
SCHEDULE_TIE_TOL = 1.0e-10
FIXED_TOL = 1.0e-9
CONTRACTION_TOL = 1.0e-8
CONVERGENCE_TOL = 1.0e-8
MONOTONIC_TOL = 1.0e-9
COVARIANCE_TOL = 1.0e-9

FROZEN_HASHES = {
    SPEC_PATH: "f370aeb1366f30857c89d5ab9c94af54aea6f40fb8db6309776a5c0fa79dacb7",
    PREREG_PATH: "cb5e4f552ebc51684ab5a081b399025324e49efc75d841598e0cb3e6586a177c",
    JAX_SOURCE_PATH: "bff791a3c74fbb4deb6a11b0647e950a50bdf18346a0a27667ea9a2e24fdae4f",
    JULIA_SOURCE_PATH: "9da7708a6d3a53543b1cd015ccd9b633a9c81446f7f641946d76298346992c97",
    JAX_RESULT_PATH: "ab4710fe9b032d0052422072445f343b70e39dc58c905a3206f76ed0dbe5a8a7",
    JULIA_RESULT_PATH: "8b8a21b31907e900886c840062c89c1fd7bb219d6365e439aaa2bb5063ee5cda",
    CANONICAL_SOURCE_PATH: "0b8df7def1c274cf118995663abd9ec95886197d1dfb01de4519c19ca9351f83",
    FABLE_RESULT_PATH: "bdb44e5eb6fc3aa014c09bdc33736e331fdb21220adf510e7f602b39497be1d2",
    FABLE_RECEIPT_PATH: "3d20868deeaafe5b21df4c017b41602ca99fac06485752e69acabf8e2f3f0154",
}

SPEC_KEYS = {
    "schema",
    "sim_id",
    "created_at",
    "classification",
    "promotion_allowed",
    "formal_admission_allowed",
    "engine_contract",
    "bounded_claim",
    "claim_ceiling",
    "blocked_consumers",
    "carrier",
    "ordered_source_slots",
    "parameter_grid",
    "perspectives",
    "preregistered_tests",
    "verdict_rule",
}
PREREG_KEYS = {
    "schema",
    "sim_id",
    "registered_before_builder_source",
    "registered_at",
    "spec_path",
    "spec_sha256",
    "classification",
    "promotion_allowed",
    "formal_admission_allowed",
    "controller_note",
}
JAX_TOP_KEYS = {
    "TOOL_INTEGRATION_DEPTH",
    "TOOL_MANIFEST",
    "aligned_packages_load_bearing",
    "all_pass",
    "blocked_consumers",
    "claim_ceiling",
    "claim_path_tools",
    "classification",
    "controls",
    "determinism",
    "eligible_consumers",
    "engine",
    "engine_contract",
    "engines",
    "formal_admission_allowed",
    "functions_called",
    "packages_used",
    "positive_negative_boundary_demotion_receipts",
    "preregistered_tests",
    "promotion_allowed",
    "ran",
    "reads_peer_result",
    "result_integrity",
    "rich_package_parity_microcheck",
    "runtime",
    "schema",
    "scientific_verdict",
    "sim_id",
    "source_and_spec_binding",
    "source_semantics",
    "stage_maps",
    "stage_movement_allowed",
    "tool_calls",
}
JULIA_TOP_KEYS = {
    "TOOL_INTEGRATION_DEPTH",
    "TOOL_MANIFEST",
    "blocked_consumers",
    "carrier",
    "claim_ceiling",
    "classification",
    "divergence_log",
    "engine",
    "engine_results",
    "environment",
    "formal_admission_allowed",
    "generated_at",
    "hashes",
    "input_provenance",
    "ordered_source_slots",
    "promotion_allowed",
    "reads_peer_result",
    "result_path",
    "schema",
    "semantic_role",
    "sim_id",
    "test_summary",
    "tool_integration_depth",
    "tool_manifest",
    "type_difference_control",
    "verdict",
    "verdict_scope",
}
ENGINE_NAMES = ("Type1_left", "Type2_right")
NOMINAL_TEST_KEYS = {
    "T1_unique_full_rank_fixed_point",
    "T2_strict_transverse_contraction",
    "T3_global_sampled_convergence",
    "T4_relative_entropy_pawl",
    "T5_depth_matches_spectral_prediction",
}
SHORT_TEST_KEYS = {"T1", "T2", "T3", "T4", "T5", "T6", "T7", "T9", "T10", "T11"}


class ValidationError(RuntimeError):
    pass


@dataclass
class Packet:
    spec: dict[str, Any]
    prereg: dict[str, Any]
    jax: dict[str, Any]
    julia: dict[str, Any]
    fable_result: dict[str, Any]
    fable_receipt: dict[str, Any]


def fail(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("JSON", f"duplicate key {key!r}")
        result[key] = value
    return result


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        fail("JSON", f"nonfinite number {value!r}")
    return result


def strict_json_load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_pairs_no_duplicates,
            parse_float=_finite_float,
            parse_constant=lambda value: fail("JSON", f"nonfinite constant {value!r}"),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: unreadable strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        fail(str(path), "top level must be an object")
    return value


def strict_write_json(path: Path, value: dict[str, Any]) -> None:
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(path, "must be an object")
    actual = set(value)
    if actual != expected:
        fail(
            path,
            f"closed schema keys differ; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}",
        )
    return value


def strict_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        fail(path, "must be a JSON boolean")
    return value


def strict_int(value: Any, path: str, minimum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        fail(path, "must be an integer")
    if minimum is not None and value < minimum:
        fail(path, f"must be >= {minimum}")
    return value


def number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(path, "must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        fail(path, "must be finite")
    return result


def require(condition: bool, path: str, message: str) -> None:
    if not condition:
        fail(path, message)


def close(actual: Any, expected: Any, path: str, tolerance: float = PARITY_TOL) -> None:
    if isinstance(expected, bool):
        if actual is not expected:
            fail(path, f"expected {expected}, got {actual!r}")
        return
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        observed = number(actual, path)
        if not math.isclose(observed, float(expected), rel_tol=0.0, abs_tol=tolerance):
            fail(path, f"expected {expected!r}, got {observed!r}")
        return
    if actual != expected:
        fail(path, f"expected {expected!r}, got {actual!r}")


def finite_array(value: Any, shape: tuple[int, ...], path: str) -> np.ndarray:
    try:
        result = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{path}: not a numeric array: {exc}") from exc
    if result.shape != shape:
        fail(path, f"expected shape {shape}, got {result.shape}")
    if not np.all(np.isfinite(result)):
        fail(path, "contains nonfinite values")
    return result


def complex_value(value: Any, path: str) -> complex:
    if not isinstance(value, dict):
        fail(path, "complex value must be an object")
    keys = set(value)
    if keys == {"real", "imag"}:
        return complex(number(value["real"], f"{path}.real"), number(value["imag"], f"{path}.imag"))
    if keys == {"re", "im"}:
        return complex(number(value["re"], f"{path}.re"), number(value["im"], f"{path}.im"))
    fail(path, f"closed complex schema mismatch: {sorted(keys)}")


def complex_matrix(value: Any, path: str) -> np.ndarray:
    if not isinstance(value, list) or len(value) != 2:
        fail(path, "must be a 2x2 complex matrix")
    rows = []
    for row_index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != 2:
            fail(f"{path}[{row_index}]", "must contain two entries")
        rows.append(
            [complex_value(item, f"{path}[{row_index}][{column}]") for column, item in enumerate(row)]
        )
    return np.asarray(rows, dtype=np.complex128)


def complex_vector(value: Any, path: str) -> np.ndarray:
    if not isinstance(value, list) or len(value) != 4:
        fail(path, "must contain four complex eigenvalues")
    return np.asarray([complex_value(item, f"{path}[{index}]") for index, item in enumerate(value)])


def multiset_error(left: np.ndarray, right: np.ndarray) -> float:
    return min(
        max(abs(left[index] - right[target]) for index, target in enumerate(order))
        for order in itertools.permutations(range(4))
    )


def triplet_multiset_error(left: np.ndarray, right: np.ndarray) -> float:
    return min(
        max(abs(left[index] - right[target]) for index, target in enumerate(order))
        for order in itertools.permutations(range(3))
    )


def transverse_spectrum(values: np.ndarray, path: str) -> np.ndarray:
    fixed_index = int(np.argmin(np.abs(values - 1.0)))
    require(abs(values[fixed_index] - 1.0) <= FIXED_TOL, path, "has no fixed eigenvalue near one")
    return np.delete(values, fixed_index)


def load_packet() -> Packet:
    return Packet(
        spec=strict_json_load(SPEC_PATH),
        prereg=strict_json_load(PREREG_PATH),
        jax=strict_json_load(JAX_RESULT_PATH),
        julia=strict_json_load(JULIA_RESULT_PATH),
        fable_result=strict_json_load(FABLE_RESULT_PATH),
        fable_receipt=strict_json_load(FABLE_RECEIPT_PATH),
    )


def verify_hashes(packet: Packet) -> dict[str, str]:
    observed = {relative(path): sha256(path) for path in FROZEN_HASHES}
    for path, expected in FROZEN_HASHES.items():
        close(observed[relative(path)], expected, f"hashes.{relative(path)}")

    close(packet.prereg["spec_sha256"], observed[relative(SPEC_PATH)], "prereg.spec_sha256")
    binding = exact_keys(
        packet.jax["source_and_spec_binding"],
        {"checks", "expected_hashes", "hashes", "pass"},
        "jax.source_and_spec_binding",
    )
    exact_keys(
        binding["hashes"],
        {
            relative(CANONICAL_SOURCE_PATH),
            relative(PREREG_PATH),
            relative(JAX_SOURCE_PATH),
            relative(SPEC_PATH),
        },
        "jax.source_and_spec_binding.hashes",
    )
    for path in (CANONICAL_SOURCE_PATH, PREREG_PATH, JAX_SOURCE_PATH, SPEC_PATH):
        close(
            binding["hashes"][relative(path)],
            observed[relative(path)],
            f"jax.source_and_spec_binding.hashes.{relative(path)}",
        )
    expected_hashes = exact_keys(
        binding["expected_hashes"],
        {
            "git_show_HEAD:system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
            relative(PREREG_PATH),
            relative(SPEC_PATH),
        },
        "jax.source_and_spec_binding.expected_hashes",
    )
    close(
        expected_hashes["git_show_HEAD:system_v5/ops/formal_scouts/canonical_qit_engine_specs.py"],
        observed[relative(CANONICAL_SOURCE_PATH)],
        "jax.source_and_spec_binding.expected_hashes.canonical",
    )
    close(expected_hashes[relative(PREREG_PATH)], observed[relative(PREREG_PATH)], "jax.expected.prereg")
    close(expected_hashes[relative(SPEC_PATH)], observed[relative(SPEC_PATH)], "jax.expected.spec")
    require(strict_bool(binding["pass"], "jax.source_and_spec_binding.pass"), "jax.source_and_spec_binding.pass", "must pass")

    julia_hashes = exact_keys(
        packet.julia["hashes"],
        {"spec_sha256", "canonical_semantics_sha256", "run_julia_sha256"},
        "julia.hashes",
    )
    close(julia_hashes["spec_sha256"], observed[relative(SPEC_PATH)], "julia.hashes.spec_sha256")
    close(
        julia_hashes["canonical_semantics_sha256"],
        observed[relative(CANONICAL_SOURCE_PATH)],
        "julia.hashes.canonical_semantics_sha256",
    )
    close(julia_hashes["run_julia_sha256"], observed[relative(JULIA_SOURCE_PATH)], "julia.hashes.run_julia_sha256")
    return observed


def verify_schemas_and_ceilings(packet: Packet) -> None:
    spec = exact_keys(packet.spec, SPEC_KEYS, "spec")
    prereg = exact_keys(packet.prereg, PREREG_KEYS, "prereg")
    jax = exact_keys(packet.jax, JAX_TOP_KEYS, "jax")
    julia = exact_keys(packet.julia, JULIA_TOP_KEYS, "julia")

    exact_keys(jax["engines"], set(ENGINE_NAMES), "jax.engines")
    exact_keys(jax["stage_maps"], set(ENGINE_NAMES), "jax.stage_maps")
    exact_keys(jax["controls"], {"commuting_fixed_manifold", "type_difference"}, "jax.controls")
    exact_keys(julia["engine_results"], set(ENGINE_NAMES), "julia.engine_results")
    for engine in ENGINE_NAMES:
        exact_keys(
            jax["engines"][engine],
            {"basis_covariance", "bloch_affine_readout", "nominal", "parameter_robustness", "random_primitive_controls", "schedule_atlas", "unitary_no_attraction_control"},
            f"jax.engines.{engine}",
        )
        exact_keys(
            julia["engine_results"][engine],
            {"basis_covariance", "bloch_ball_affine_readout", "commuting_fixed_manifold_control", "cycle_physicality", "effective_parameters", "genericity_kill_control", "nominal_analysis", "nominal_tests", "parameter_robustness", "schedule_sensitivity_atlas", "semantic_definition", "stage_receipts", "terrain_steadystate_receipts", "unitary_no_attraction_control"},
            f"julia.engine_results.{engine}",
        )

    exact_keys(
        spec["carrier"],
        {"state_space", "terrain_maps", "operator_maps", "axis6_rule"},
        "spec.carrier",
    )
    exact_keys(spec["carrier"]["operator_maps"], {"Ti", "Te", "Fi", "Fe"}, "spec.carrier.operator_maps")
    parameter_grid = exact_keys(
        spec["parameter_grid"],
        {"engine_types", "lindblad_duration", "operator_angles", "dephase_strengths", "perturbation_multipliers", "horizons", "initial_state_count", "random_control_count", "schedule_controls"},
        "spec.parameter_grid",
    )
    close(parameter_grid["engine_types"], list(ENGINE_NAMES), "spec.parameter_grid.engine_types")
    close(parameter_grid["perturbation_multipliers"], [0.9, 1.0, 1.1], "spec.parameter_grid.perturbation_multipliers")
    close(parameter_grid["horizons"], [16, 32, 64, 128, 256], "spec.parameter_grid.horizons")
    close(parameter_grid["initial_state_count"], 1024, "spec.parameter_grid.initial_state_count")
    close(parameter_grid["random_control_count"], 64, "spec.parameter_grid.random_control_count")
    exact_keys(parameter_grid["operator_angles"], {"Fi", "Fe"}, "spec.parameter_grid.operator_angles")
    exact_keys(parameter_grid["dephase_strengths"], {"Ti", "Te"}, "spec.parameter_grid.dephase_strengths")
    exact_keys(spec["preregistered_tests"], {f"T{index}_{name}" for index, name in (
        (1, "unique_full_rank_fixed_point"),
        (2, "strict_transverse_contraction"),
        (3, "global_sampled_convergence"),
        (4, "relative_entropy_pawl"),
        (5, "depth_matches_spectral_prediction"),
        (6, "parameter_robustness"),
        (7, "basis_covariance"),
        (8, "schedule_sensitivity"),
        (9, "genericity_kill_control"),
        (10, "unitary_no-attraction_control"),
        (11, "commuting_fixed_manifold_control"),
        (12, "type_difference"),
    )}, "spec.preregistered_tests")
    exact_keys(
        spec["verdict_rule"],
        {"REAL_DISTINCTIVE_INSTALLED_BASINS", "REAL_BUT_GENERIC_INSTALLED_BASINS", "LOCAL_OR_FRAGILE_INSTALLED_BASIN_ONLY", "NO_REAL_ATTRACTOR_BASIN_IN_THIS_MAP"},
        "spec.verdict_rule",
    )

    close(spec["schema"], "codex_ratchet.sim_spec.v1", "spec.schema")
    close(prereg["schema"], "codex_ratchet.preregistration_receipt.v1", "prereg.schema")
    close(jax["schema"], f"codex_ratchet.{SIM_ID}.jax_result.v1", "jax.schema")
    close(julia["schema"], "codex_ratchet.sim_result.v1", "julia.schema")
    for name, value in (("spec", spec), ("prereg", prereg), ("jax", jax), ("julia", julia)):
        close(value["sim_id"], SIM_ID, f"{name}.sim_id")
        close(value["classification"], CLASSIFICATION, f"{name}.classification")
        require(strict_bool(value["promotion_allowed"], f"{name}.promotion_allowed") is False, f"{name}.promotion_allowed", "must remain false")
        require(strict_bool(value["formal_admission_allowed"], f"{name}.formal_admission_allowed") is False, f"{name}.formal_admission_allowed", "must remain false")

    engine_contract = exact_keys(
        spec["engine_contract"],
        {"mode", "lanes", "semantic_owner", "pytorch_status"},
        "spec.engine_contract",
    )
    close(engine_contract["mode"], "julia_canon_jax_workhorse", "spec.engine_contract.mode")
    close(engine_contract["lanes"], ["julia", "jax"], "spec.engine_contract.lanes")
    close(engine_contract["semantic_owner"], "julia", "spec.engine_contract.semantic_owner")
    close(jax["engine_contract"], engine_contract, "jax.engine_contract")
    close(jax["engine"], "jax", "jax.engine")
    close(julia["engine"], "julia", "julia.engine")
    require(strict_bool(jax["stage_movement_allowed"], "jax.stage_movement_allowed") is False, "jax.stage_movement_allowed", "must remain false")
    require(strict_bool(jax["reads_peer_result"], "jax.reads_peer_result") is False, "jax.reads_peer_result", "must remain false")
    require(strict_bool(julia["reads_peer_result"], "julia.reads_peer_result") is False, "julia.reads_peer_result", "must remain false")
    require(strict_bool(jax["ran"], "jax.ran"), "jax.ran", "must be true")

    close(prereg["classification"], spec["classification"], "prereg.classification")
    require(strict_bool(prereg["registered_before_builder_source"], "prereg.registered_before_builder_source"), "prereg.registered_before_builder_source", "must remain true")
    close(prereg["spec_path"], relative(SPEC_PATH), "prereg.spec_path")
    close(jax["claim_ceiling"], spec["claim_ceiling"], "jax.claim_ceiling")
    close(julia["claim_ceiling"], spec["claim_ceiling"], "julia.claim_ceiling")
    close(jax["blocked_consumers"], spec["blocked_consumers"], "jax.blocked_consumers")
    close(julia["blocked_consumers"], spec["blocked_consumers"], "julia.blocked_consumers")
    close(jax["scientific_verdict"], PREREG_VERDICT, "jax.scientific_verdict")
    close(julia["verdict"], PREREG_VERDICT, "julia.verdict")
    close(
        julia["verdict_scope"],
        "installed finite CPTP cycles only; no derivation, canonicity, Axis0, perception, object, ontology, mesh, business, or physics promotion",
        "julia.verdict_scope",
    )
    require(strict_bool(jax["all_pass"], "jax.all_pass") is False, "jax.all_pass", "the prereg result must remain LOCAL_OR_FRAGILE, not self-promoted")
    result_integrity = exact_keys(
        jax["result_integrity"],
        {"all_32_stage_maps_cptp", "both_cycle_maps_cptp", "dynamiqs_gating_parity", "exactly_1024_initial_states", "jax_x64", "pass", "source_and_spec_hashes"},
        "jax.result_integrity",
    )
    for key, value in result_integrity.items():
        require(strict_bool(value, f"jax.result_integrity.{key}"), f"jax.result_integrity.{key}", "must be true")
    preregistered = exact_keys(
        jax["preregistered_tests"],
        {"T1_unique_full_rank_fixed_point", "T2_strict_transverse_contraction", "T3_global_sampled_convergence", "T4_relative_entropy_pawl", "T5_depth_matches_spectral_prediction", "T6_parameter_robustness", "T7_basis_covariance", "T8_schedule_sensitivity", "T9_genericity_kill_control", "T10_unitary_no_attraction_control", "T11_commuting_fixed_manifold_control", "T12_type_difference"},
        "jax.preregistered_tests",
    )
    exact_keys(
        preregistered["T8_schedule_sensitivity"],
        {"atlas_reported_for_both_types", "binary_scientific_pass_assigned", "status"},
        "jax.preregistered_tests.T8_schedule_sensitivity",
    )
    test_summary = exact_keys(julia["test_summary"], {"T1_T7_T9_T12", "T8_schedule_sensitivity"}, "julia.test_summary")
    exact_keys(test_summary["T1_T7_T9_T12"], set(ENGINE_NAMES), "julia.test_summary.T1_T7_T9_T12")

    require(packet.fable_result.get("type") == "result", "fable.type", "unexpected model-lane artifact")
    require(packet.fable_result.get("subtype") == "success", "fable.subtype", "audit did not succeed")
    require(packet.fable_result.get("is_error") is False, "fable.is_error", "audit is marked errored")
    audit_text = packet.fable_result.get("result")
    require(isinstance(audit_text, str), "fable.result", "must be text")
    for phrase in (
        "cannot legitimately earn \"DISTINCTIVE\"",
        "strict contraction with a unique fixed point",
        "drop \"basin depth\"",
    ):
        require(phrase in audit_text, "fable.result", f"missing bound audit conclusion {phrase!r}")
    require(packet.fable_receipt.get("returncode") == 0, "fable_receipt.returncode", "audit process failed")
    require(packet.fable_receipt.get("timed_out") is False, "fable_receipt.timed_out", "audit timed out")


def expected_slot_metadata(tokens: list[str]) -> list[dict[str, str]]:
    result = []
    for index, token in enumerate(tokens):
        operator_first = index % 2 == 0
        if operator_first:
            operator, terrain = token[:2], token[2:]
        else:
            terrain, operator = token[:2], token[2:]
        result.append(
            {
                "token": token,
                "operator": operator,
                "terrain": terrain,
                "precedence": "operator_first" if operator_first else "terrain_first",
                "axis6": "up" if operator_first else "down",
                "formula": f"T_{terrain} o {operator}" if operator_first else f"{operator} o T_{terrain}",
            }
        )
    return result


def verify_slots(packet: Packet) -> dict[str, Any]:
    tokens = packet.spec["ordered_source_slots"]
    require(isinstance(tokens, list) and len(tokens) == 16 and len(set(tokens)) == 16, "spec.ordered_source_slots", "must be 16 unique tokens")
    close(packet.julia["ordered_source_slots"], tokens, "julia.ordered_source_slots")
    metadata = expected_slot_metadata(tokens)
    maximum_choi_gap = 0.0
    maximum_trace_gap = 0.0
    for engine in ENGINE_NAMES:
        jax_group = exact_keys(
            packet.jax["stage_maps"][engine],
            {"stage_count", "all_stage_maps_cptp", "minimum_stage_choi_eigenvalue", "maximum_stage_trace_preservation_residual", "rows"},
            f"jax.stage_maps.{engine}",
        )
        julia_rows = packet.julia["engine_results"][engine]["stage_receipts"]
        strict_int(jax_group["stage_count"], f"jax.stage_maps.{engine}.stage_count")
        require(jax_group["stage_count"] == 16, f"jax.stage_maps.{engine}.stage_count", "must be 16")
        require(isinstance(jax_group["rows"], list) and len(jax_group["rows"]) == 16, f"jax.stage_maps.{engine}.rows", "must contain 16 rows")
        require(isinstance(julia_rows, list) and len(julia_rows) == 16, f"julia.engine_results.{engine}.stage_receipts", "must contain 16 rows")
        for index, expected in enumerate(metadata):
            jpath = f"jax.stage_maps.{engine}.rows[{index}]"
            upath = f"julia.engine_results.{engine}.stage_receipts[{index}]"
            jrow = exact_keys(
                jax_group["rows"][index],
                {"axis6_action_side", "axis6_token_precedence", "closure_type", "composition_precedence", "cptp", "native_formula", "operator", "operator_formula_unchanged_by_axis6", "terrain_family", "token"},
                jpath,
            )
            urow = exact_keys(
                julia_rows[index],
                {"axis6_action_side", "axis6_token_precedence", "native_formula", "operator", "operator_closure_type", "physicality", "slot", "terrain", "terrain_closure_type", "token"},
                upath,
            )
            for key, jkey, ukey in (
                ("token", "token", "token"),
                ("operator", "operator", "operator"),
                ("terrain", "terrain_family", "terrain"),
                ("axis6", "axis6_token_precedence", "axis6_token_precedence"),
                ("formula", "native_formula", "native_formula"),
            ):
                close(jrow[jkey], expected[key], f"{jpath}.{jkey}")
                close(urow[ukey], expected[key], f"{upath}.{ukey}")
            close(jrow["composition_precedence"], expected["precedence"], f"{jpath}.composition_precedence")
            close(urow["slot"], index + 1, f"{upath}.slot")
            require(strict_bool(jrow["operator_formula_unchanged_by_axis6"], f"{jpath}.operator_formula_unchanged_by_axis6"), f"{jpath}.operator_formula_unchanged_by_axis6", "must be true")
            jcptp = exact_keys(jrow["cptp"], {"minimum_choi_eigenvalue", "pass", "trace_preservation_residual"}, f"{jpath}.cptp")
            ucptp = exact_keys(urow["physicality"], {"choi_minimum_eigenvalue", "trace_preservation_residual"}, f"{upath}.physicality")
            require(strict_bool(jcptp["pass"], f"{jpath}.cptp.pass"), f"{jpath}.cptp.pass", "must pass")
            jchoi = number(jcptp["minimum_choi_eigenvalue"], f"{jpath}.cptp.minimum_choi_eigenvalue")
            uchoi = number(ucptp["choi_minimum_eigenvalue"], f"{upath}.physicality.choi_minimum_eigenvalue")
            jtrace = number(jcptp["trace_preservation_residual"], f"{jpath}.cptp.trace_preservation_residual")
            utrace = number(ucptp["trace_preservation_residual"], f"{upath}.physicality.trace_preservation_residual")
            require(jchoi >= -2.0e-10 and uchoi >= -2.0e-10, jpath, "stage is not CP within tolerance")
            require(jtrace <= 2.0e-10 and utrace <= 2.0e-10, jpath, "stage is not trace preserving within tolerance")
            maximum_choi_gap = max(maximum_choi_gap, abs(jchoi - uchoi))
            maximum_trace_gap = max(maximum_trace_gap, abs(jtrace - utrace))
        require(strict_bool(jax_group["all_stage_maps_cptp"], f"jax.stage_maps.{engine}.all_stage_maps_cptp"), f"jax.stage_maps.{engine}.all_stage_maps_cptp", "must pass")
    require(maximum_choi_gap <= PARITY_TOL, "parity.slots.choi", f"maximum gap {maximum_choi_gap}")
    require(maximum_trace_gap <= PARITY_TOL, "parity.slots.trace", f"maximum gap {maximum_trace_gap}")
    return {"slot_count_per_engine": 16, "maximum_choi_gap": maximum_choi_gap, "maximum_trace_preservation_gap": maximum_trace_gap, "pass": True}


def affine_payload(value: Any, path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    row = exact_keys(value, {"linear_matrix", "offset", "singular_values", "trace_distance_contraction_coefficient"}, path)
    matrix = finite_array(row["linear_matrix"], (3, 3), f"{path}.linear_matrix")
    offset = finite_array(row["offset"], (3,), f"{path}.offset")
    reported_singular = finite_array(row["singular_values"], (3,), f"{path}.singular_values")
    recomputed_singular = np.linalg.svd(matrix, compute_uv=False)
    error = float(np.max(np.abs(reported_singular - recomputed_singular)))
    require(error <= PARITY_TOL, f"{path}.singular_values", f"do not recompute from M; error={error}")
    coefficient = number(row["trace_distance_contraction_coefficient"], f"{path}.trace_distance_contraction_coefficient")
    close(coefficient, float(recomputed_singular[0]), f"{path}.trace_distance_contraction_coefficient")
    return matrix, offset, recomputed_singular, coefficient


def verify_affine(packet: Packet) -> tuple[dict[str, Any], bool]:
    rows: dict[str, Any] = {}
    all_strict = True
    for engine in ENGINE_NAMES:
        jax_values = affine_payload(packet.jax["engines"][engine]["bloch_affine_readout"], f"jax.engines.{engine}.bloch_affine_readout")
        julia_values = affine_payload(packet.julia["engine_results"][engine]["bloch_ball_affine_readout"], f"julia.engine_results.{engine}.bloch_ball_affine_readout")
        matrix_gap = float(np.max(np.abs(jax_values[0] - julia_values[0])))
        offset_gap = float(np.max(np.abs(jax_values[1] - julia_values[1])))
        singular_gap = float(np.max(np.abs(jax_values[2] - julia_values[2])))
        coefficient_gap = abs(jax_values[3] - julia_values[3])
        require(max(matrix_gap, offset_gap, singular_gap, coefficient_gap) <= PARITY_TOL, f"parity.affine.{engine}", "Julia/JAX affine data disagree")
        strict = jax_values[3] < 1.0 and julia_values[3] < 1.0
        all_strict = all_strict and strict
        rows[engine] = {
            "jax_coefficient": jax_values[3],
            "julia_coefficient": julia_values[3],
            "maximum_matrix_gap": matrix_gap,
            "maximum_offset_gap": offset_gap,
            "maximum_singular_value_gap": singular_gap,
            "strictly_below_one": strict,
        }
    return {"engines": rows, "both_coefficients_strictly_below_one": all_strict, "pass": all_strict}, all_strict


def verify_spectrum(
    values: np.ndarray,
    reported_subdominant: Any,
    reported_gap: Any,
    reported_multiplicity: Any,
    path: str,
) -> tuple[float, float, int]:
    moduli = sorted((abs(value) for value in values), reverse=True)
    subdominant = float(moduli[1])
    gap = 1.0 - subdominant
    multiplicity = sum(abs(value - 1.0) <= FIXED_TOL for value in values)
    close(reported_subdominant, subdominant, f"{path}.subdominant")
    close(reported_gap, gap, f"{path}.gap")
    close(reported_multiplicity, multiplicity, f"{path}.multiplicity")
    return subdominant, gap, multiplicity


def verify_fixed_state(value: Any, reported_minimum: Any, path: str) -> tuple[np.ndarray, float]:
    matrix = complex_matrix(value, path)
    hermitian_error = float(np.max(np.abs(matrix - matrix.conj().T)))
    trace_error = abs(np.trace(matrix) - 1.0)
    require(hermitian_error <= PARITY_TOL, path, f"not Hermitian; error={hermitian_error}")
    require(trace_error <= PARITY_TOL, path, f"trace is not one; error={trace_error}")
    minimum = float(np.min(np.linalg.eigvalsh(matrix)))
    close(reported_minimum, minimum, f"{path}.minimum_eigenvalue")
    require(minimum > FIXED_TOL, path, "fixed state is not full rank")
    return matrix, minimum


def verify_jax_nominal(value: Any, path: str, maximum_horizon: int) -> dict[str, Any]:
    row = exact_keys(
        value,
        {"bures_distance_profile", "cycle_cptp", "epsilon_depth", "fixed_state", "horizons", "maximum_bures_increase", "maximum_ume_increase", "spectrum", "tests", "trace_distance_profile", "trajectory_count", "umegaki_relative_entropy_profile"},
        path,
    )
    spectrum = exact_keys(row["spectrum"], {"contraction_gap", "eigenvalues", "fixed_point_multiplicity", "fixed_point_residual", "minimum_fixed_state_eigenvalue", "subdominant_eigenvalue_modulus"}, f"{path}.spectrum")
    values = complex_vector(spectrum["eigenvalues"], f"{path}.spectrum.eigenvalues")
    subdominant, gap, multiplicity = verify_spectrum(values, spectrum["subdominant_eigenvalue_modulus"], spectrum["contraction_gap"], spectrum["fixed_point_multiplicity"], f"{path}.spectrum")
    fixed, minimum = verify_fixed_state(row["fixed_state"], spectrum["minimum_fixed_state_eigenvalue"], f"{path}.fixed_state")
    close(row["horizons"], [16, 32, 64, 128, 256], f"{path}.horizons")
    close(row["trajectory_count"], 1024, f"{path}.trajectory_count")
    for profile_name in ("trace_distance_profile", "umegaki_relative_entropy_profile", "bures_distance_profile"):
        profile = exact_keys(row[profile_name], {"16", "32", "64", "128", "256"}, f"{path}.{profile_name}")
        for horizon, profile_row in profile.items():
            exact_keys(profile_row, {"maximum", "mean"}, f"{path}.{profile_name}.{horizon}")
            number(profile_row["maximum"], f"{path}.{profile_name}.{horizon}.maximum")
            number(profile_row["mean"], f"{path}.{profile_name}.{horizon}.mean")
    epsilon = exact_keys(row["epsilon_depth"], {"epsilon", "factor", "observed", "spectral_prediction"}, f"{path}.epsilon_depth")
    observed = strict_int(epsilon["observed"], f"{path}.epsilon_depth.observed", 1)
    predicted = strict_int(epsilon["spectral_prediction"], f"{path}.epsilon_depth.spectral_prediction", 1)
    depth_factor = max(observed, predicted) / min(observed, predicted)
    close(epsilon["factor"], depth_factor, f"{path}.epsilon_depth.factor")
    close(epsilon["epsilon"], CONVERGENCE_TOL, f"{path}.epsilon_depth.epsilon")
    tests = {
        "T1_unique_full_rank_fixed_point": multiplicity == 1 and minimum > FIXED_TOL,
        "T2_strict_transverse_contraction": subdominant < 1.0 - CONTRACTION_TOL,
        "T3_global_sampled_convergence": number(row["trace_distance_profile"][str(maximum_horizon)]["maximum"], f"{path}.trace_distance_profile.{maximum_horizon}.maximum") < CONVERGENCE_TOL,
        "T4_relative_entropy_pawl": number(row["maximum_ume_increase"], f"{path}.maximum_ume_increase") <= MONOTONIC_TOL,
        "T5_depth_matches_spectral_prediction": depth_factor <= 4.0,
    }
    exact_keys(row["tests"], NOMINAL_TEST_KEYS, f"{path}.tests")
    close(row["tests"], tests, f"{path}.tests")
    return {"fixed": fixed, "spectrum": values, "subdominant": subdominant, "gap": gap, "tests": tests}


def verify_julia_nominal(value: Any, path: str, maximum_horizon: int) -> dict[str, Any]:
    row = exact_keys(
        value,
        {"contraction_gap", "fixed_point_multiplicity", "fixed_point_residual", "fixed_state", "fixed_state_minimum_eigenvalue", "liouville_spectrum", "maximum_relative_entropy_increase", "maximum_trace_distance_profile_by_cycle", "observed_epsilon_depth", "observed_to_predicted_depth_factor", "sampled_horizon_readouts", "spectral_predicted_depth", "subdominant_eigenvalue_modulus", "tests"},
        path,
    )
    values = complex_vector(row["liouville_spectrum"], f"{path}.liouville_spectrum")
    subdominant, gap, multiplicity = verify_spectrum(values, row["subdominant_eigenvalue_modulus"], row["contraction_gap"], row["fixed_point_multiplicity"], path)
    fixed, minimum = verify_fixed_state(row["fixed_state"], row["fixed_state_minimum_eigenvalue"], f"{path}.fixed_state")
    horizons = row["sampled_horizon_readouts"]
    require(isinstance(horizons, list) and len(horizons) == 5, f"{path}.sampled_horizon_readouts", "must contain five horizons")
    horizon_map: dict[int, dict[str, Any]] = {}
    for index, item in enumerate(horizons):
        item = exact_keys(item, {"horizon_cycles", "maximum_bures_distance", "maximum_relative_entropy_nats", "maximum_trace_distance"}, f"{path}.sampled_horizon_readouts[{index}]")
        horizon_map[strict_int(item["horizon_cycles"], f"{path}.sampled_horizon_readouts[{index}].horizon_cycles", 1)] = item
    close(sorted(horizon_map), [16, 32, 64, 128, 256], f"{path}.sampled_horizon_readouts.horizons")
    observed = strict_int(row["observed_epsilon_depth"], f"{path}.observed_epsilon_depth", 1)
    predicted = strict_int(row["spectral_predicted_depth"], f"{path}.spectral_predicted_depth", 1)
    depth_factor = max(observed, predicted) / min(observed, predicted)
    close(row["observed_to_predicted_depth_factor"], depth_factor, f"{path}.observed_to_predicted_depth_factor")
    tests = {
        "T1_unique_full_rank_fixed_point": multiplicity == 1 and minimum > FIXED_TOL,
        "T2_strict_transverse_contraction": subdominant < 1.0 - CONTRACTION_TOL,
        "T3_global_sampled_convergence": number(horizon_map[maximum_horizon]["maximum_trace_distance"], f"{path}.horizon.{maximum_horizon}.maximum_trace_distance") < CONVERGENCE_TOL,
        "T4_relative_entropy_pawl": number(row["maximum_relative_entropy_increase"], f"{path}.maximum_relative_entropy_increase") <= MONOTONIC_TOL,
        "T5_depth_matches_spectral_prediction": depth_factor <= 4.0,
    }
    exact_keys(row["tests"], NOMINAL_TEST_KEYS, f"{path}.tests")
    close(row["tests"], tests, f"{path}.tests")
    return {"fixed": fixed, "spectrum": values, "subdominant": subdominant, "gap": gap, "tests": tests}


def verify_nominal(packet: Packet) -> tuple[dict[str, Any], dict[str, dict[str, dict[str, bool]]]]:
    maximum_horizon = max(packet.spec["parameter_grid"]["horizons"])
    details: dict[str, Any] = {}
    tests: dict[str, dict[str, dict[str, bool]]] = {"jax": {}, "julia": {}}
    for engine in ENGINE_NAMES:
        jax = verify_jax_nominal(packet.jax["engines"][engine]["nominal"], f"jax.engines.{engine}.nominal", maximum_horizon)
        julia = verify_julia_nominal(packet.julia["engine_results"][engine]["nominal_analysis"], f"julia.engine_results.{engine}.nominal_analysis", maximum_horizon)
        fixed_gap = float(np.max(np.abs(jax["fixed"] - julia["fixed"])))
        spectrum_gap = multiset_error(jax["spectrum"], julia["spectrum"])
        contraction_gap = abs(jax["gap"] - julia["gap"])
        require(max(fixed_gap, spectrum_gap, contraction_gap) <= PARITY_TOL, f"parity.nominal.{engine}", "fixed state, spectrum, or gap disagree")
        close(jax["tests"], julia["tests"], f"parity.nominal.{engine}.tests")

        jax_affine = packet.jax["engines"][engine]["bloch_affine_readout"]
        julia_affine = packet.julia["engine_results"][engine]["bloch_ball_affine_readout"]
        matrix = finite_array(jax_affine["linear_matrix"], (3, 3), f"jax.engines.{engine}.bloch_affine_readout.linear_matrix")
        offset = finite_array(jax_affine["offset"], (3,), f"jax.engines.{engine}.bloch_affine_readout.offset")
        fixed_bloch = np.linalg.solve(np.eye(3) - matrix, offset)
        jax_fixed_bloch = np.asarray(
            [
                2.0 * jax["fixed"][0, 1].real,
                -2.0 * jax["fixed"][0, 1].imag,
                (jax["fixed"][0, 0] - jax["fixed"][1, 1]).real,
            ]
        )
        julia_fixed_bloch = np.asarray(
            [
                2.0 * julia["fixed"][0, 1].real,
                -2.0 * julia["fixed"][0, 1].imag,
                (julia["fixed"][0, 0] - julia["fixed"][1, 1]).real,
            ]
        )
        fixed_equation_error = max(
            float(np.max(np.abs(fixed_bloch - jax_fixed_bloch))),
            float(np.max(np.abs(fixed_bloch - julia_fixed_bloch))),
        )
        require(fixed_equation_error <= PARITY_TOL, f"parity.nominal.{engine}.fixed_equation", f"(I-M)r=c reconstruction error {fixed_equation_error}")
        affine_spectrum_gap = triplet_multiset_error(
            np.linalg.eigvals(matrix), transverse_spectrum(jax["spectrum"], f"jax.engines.{engine}.nominal.spectrum")
        )
        julia_affine_gap = float(
            np.max(
                np.abs(
                    finite_array(julia_affine["linear_matrix"], (3, 3), f"julia.engine_results.{engine}.bloch_ball_affine_readout.linear_matrix")
                    - matrix
                )
            )
        )
        require(affine_spectrum_gap <= PARITY_TOL, f"parity.nominal.{engine}.affine_spectrum", f"eig(M) does not match transverse Liouville spectrum; gap={affine_spectrum_gap}")
        require(julia_affine_gap <= PARITY_TOL, f"parity.nominal.{engine}.julia_affine", f"Julia M gap={julia_affine_gap}")
        tests["jax"][engine] = jax["tests"]
        tests["julia"][engine] = julia["tests"]
        details[engine] = {"maximum_fixed_state_gap": fixed_gap, "fixed_equation_error": fixed_equation_error, "spectrum_multiset_gap": spectrum_gap, "affine_transverse_spectrum_gap": affine_spectrum_gap, "contraction_gap_difference": contraction_gap, "tests_match": True}
    return {"engines": details, "pass": True}, tests


def schedule_rank(gaps: dict[str, float], native_name: str = "native") -> dict[str, Any]:
    native = gaps[native_name]
    better = sum(value > native + SCHEDULE_TIE_TOL for value in gaps.values())
    tied = sum(abs(value - native) <= SCHEDULE_TIE_TOL for value in gaps.values())
    worse = len(gaps) - better - tied
    return {
        "native_contraction_gap": native,
        "schedule_count": len(gaps),
        "strictly_better_count": better,
        "tied_count": tied,
        "strictly_worse_count": worse,
        "descending_rank_best": better + 1,
        "descending_rank_worst": better + tied,
        "midrank_percentile": (worse + 0.5 * tied) / len(gaps),
        "native_order_selected": better == 0 and tied == 1,
    }


def verify_schedules(packet: Packet) -> tuple[dict[str, Any], bool]:
    tokens = packet.spec["ordered_source_slots"]
    details: dict[str, Any] = {}
    all_not_selected = True
    for engine in ENGINE_NAMES:
        runtime_rows: dict[str, Any] = {}
        jax_atlas = exact_keys(packet.jax["engines"][engine]["schedule_atlas"], {"interpretation", "schedule_count", "schedules"}, f"jax.engines.{engine}.schedule_atlas")
        jax_schedules = jax_atlas["schedules"]
        require(isinstance(jax_schedules, dict), f"jax.engines.{engine}.schedule_atlas.schedules", "must be an object")
        expected_jax_names = {"native", "reverse"} | {f"cyclic_shift_{index}" for index in range(1, 16)} | {f"seeded_permutation_{index:02d}" for index in range(16)}
        exact_keys(jax_schedules, expected_jax_names, f"jax.engines.{engine}.schedule_atlas.schedules")
        close(jax_atlas["schedule_count"], 33, f"jax.engines.{engine}.schedule_atlas.schedule_count")
        jax_gaps: dict[str, float] = {}
        for name, item in jax_schedules.items():
            path = f"jax.engines.{engine}.schedule_atlas.schedules.{name}"
            item = exact_keys(item, {"contraction_gap", "fixed_point_multiplicity", "fixed_state", "maximum_trace_distance_by_horizon", "order_indices", "ordered_tokens", "subdominant_eigenvalue_modulus"}, path)
            order = item["order_indices"]
            require(isinstance(order, list) and sorted(order) == list(range(16)), f"{path}.order_indices", "must be an exact permutation of the same 16 channels")
            close(item["ordered_tokens"], [tokens[index] for index in order], f"{path}.ordered_tokens")
            subdominant = number(item["subdominant_eigenvalue_modulus"], f"{path}.subdominant_eigenvalue_modulus")
            gap = number(item["contraction_gap"], f"{path}.contraction_gap")
            close(gap, 1.0 - subdominant, f"{path}.contraction_gap")
            close(item["fixed_point_multiplicity"], 1, f"{path}.fixed_point_multiplicity")
            jax_gaps[name] = gap
        runtime_rows["jax"] = schedule_rank(jax_gaps)

        julia_atlas = exact_keys(packet.julia["engine_results"][engine]["schedule_sensitivity_atlas"], {"controls", "interpretation"}, f"julia.engine_results.{engine}.schedule_sensitivity_atlas")
        controls = julia_atlas["controls"]
        require(isinstance(controls, list) and len(controls) == 33, f"julia.engine_results.{engine}.schedule_sensitivity_atlas.controls", "must contain 33 controls")
        expected_julia_names = {"native", "reverse"} | {f"cyclic_shift_{index}" for index in range(1, 16)} | {f"seeded_permutation_{index}" for index in range(1, 17)}
        julia_gaps: dict[str, float] = {}
        for index, item in enumerate(controls):
            path = f"julia.engine_results.{engine}.schedule_sensitivity_atlas.controls[{index}]"
            item = exact_keys(item, {"control", "metrics", "slot_order", "token_order"}, path)
            name = item["control"]
            require(isinstance(name, str) and name not in julia_gaps, f"{path}.control", "must be a unique string")
            order = item["slot_order"]
            require(isinstance(order, list) and sorted(order) == list(range(1, 17)), f"{path}.slot_order", "must be an exact permutation of the same 16 channels")
            close(item["token_order"], [tokens[slot - 1] for slot in order], f"{path}.token_order")
            metrics = exact_keys(item["metrics"], {"contraction_gap", "cycle_physicality", "fixed_point_multiplicity", "fixed_point_trace_distance_from_native", "subdominant_eigenvalue_modulus"}, f"{path}.metrics")
            subdominant = number(metrics["subdominant_eigenvalue_modulus"], f"{path}.metrics.subdominant_eigenvalue_modulus")
            gap = number(metrics["contraction_gap"], f"{path}.metrics.contraction_gap")
            close(gap, 1.0 - subdominant, f"{path}.metrics.contraction_gap")
            close(metrics["fixed_point_multiplicity"], 1, f"{path}.metrics.fixed_point_multiplicity")
            julia_gaps[name] = gap
        close(set(julia_gaps), expected_julia_names, f"julia.engine_results.{engine}.schedule_names")
        runtime_rows["julia"] = schedule_rank(julia_gaps)
        close(runtime_rows["jax"]["native_contraction_gap"], runtime_rows["julia"]["native_contraction_gap"], f"parity.schedule.{engine}.native_gap")
        not_selected = not runtime_rows["jax"]["native_order_selected"] and not runtime_rows["julia"]["native_order_selected"] and runtime_rows["jax"]["strictly_better_count"] > 0 and runtime_rows["julia"]["strictly_better_count"] > 0
        all_not_selected = all_not_selected and not_selected
        runtime_rows["native_not_selected_in_either_atlas"] = not_selected
        details[engine] = runtime_rows
    return {"engines": details, "native_order_not_selected": all_not_selected, "pass": all_not_selected}, all_not_selected


def verify_robustness(packet: Packet) -> tuple[dict[str, Any], dict[str, dict[str, bool]]]:
    details: dict[str, Any] = {}
    passes: dict[str, dict[str, bool]] = {"jax": {}, "julia": {}}
    for engine in ENGINE_NAMES:
        jax = exact_keys(packet.jax["engines"][engine]["parameter_robustness"], {"multipliers", "pass"}, f"jax.engines.{engine}.parameter_robustness")
        jax_rows = exact_keys(jax["multipliers"], {"0.9", "1.0", "1.1"}, f"jax.engines.{engine}.parameter_robustness.multipliers")
        julia = exact_keys(packet.julia["engine_results"][engine]["parameter_robustness"], {"multiplier_rule", "passed", "rows"}, f"julia.engine_results.{engine}.parameter_robustness")
        require(isinstance(julia["rows"], list) and len(julia["rows"]) == 3, f"julia.engine_results.{engine}.parameter_robustness.rows", "must contain three multipliers")
        julia_rows = {f"{number(row.get('multiplier'), 'julia.robustness.multiplier'):.1f}": row for row in julia["rows"]}
        exact_keys(julia_rows, {"0.9", "1.0", "1.1"}, f"julia.engine_results.{engine}.parameter_robustness.rows_by_multiplier")
        maximum_gap = 0.0
        row_passes = []
        for multiplier in ("0.9", "1.0", "1.1"):
            jpath = f"jax.engines.{engine}.parameter_robustness.multipliers.{multiplier}"
            upath = f"julia.engine_results.{engine}.parameter_robustness.{multiplier}"
            jrow = exact_keys(jax_rows[multiplier], {"fixed_point_trace_distance_from_nominal", "retains_T1_T4", "spectrum", "tests"}, jpath)
            urow = exact_keys(julia_rows[multiplier], {"T1_T4_passed", "analysis", "effective_parameters", "fixed_point_drift_below_0_2", "fixed_point_trace_distance_from_nominal", "multiplier"}, upath)
            exact_keys(jrow["tests"], NOMINAL_TEST_KEYS, f"{jpath}.tests")
            julia_analysis = verify_julia_nominal(urow["analysis"], f"{upath}.analysis", 256)
            close(jrow["tests"], julia_analysis["tests"], f"parity.robustness.{engine}.{multiplier}.tests")
            retained = all(jrow["tests"][name] for name in (
                "T1_unique_full_rank_fixed_point",
                "T2_strict_transverse_contraction",
                "T3_global_sampled_convergence",
                "T4_relative_entropy_pawl",
            ))
            close(jrow["retains_T1_T4"], retained, f"{jpath}.retains_T1_T4")
            close(urow["T1_T4_passed"], retained, f"{upath}.T1_T4_passed")
            jdrift = number(jrow["fixed_point_trace_distance_from_nominal"], f"{jpath}.fixed_point_trace_distance_from_nominal")
            udrift = number(urow["fixed_point_trace_distance_from_nominal"], f"{upath}.fixed_point_trace_distance_from_nominal")
            maximum_gap = max(maximum_gap, abs(jdrift - udrift))
            close(urow["fixed_point_drift_below_0_2"], udrift < 0.2, f"{upath}.fixed_point_drift_below_0_2")
            jspectrum = exact_keys(jrow["spectrum"], {"contraction_gap", "eigenvalues", "fixed_point_multiplicity", "fixed_point_residual", "minimum_fixed_state_eigenvalue", "subdominant_eigenvalue_modulus"}, f"{jpath}.spectrum")
            jvalues = complex_vector(jspectrum["eigenvalues"], f"{jpath}.spectrum.eigenvalues")
            verify_spectrum(jvalues, jspectrum["subdominant_eigenvalue_modulus"], jspectrum["contraction_gap"], jspectrum["fixed_point_multiplicity"], f"{jpath}.spectrum")
            spectrum_gap = multiset_error(jvalues, julia_analysis["spectrum"])
            maximum_gap = max(maximum_gap, spectrum_gap)
            row_passes.append(retained and jdrift < 0.2 and udrift < 0.2)
        require(maximum_gap <= PARITY_TOL, f"parity.robustness.{engine}", f"maximum gap {maximum_gap}")
        recomputed_pass = all(row_passes)
        close(jax["pass"], recomputed_pass, f"jax.engines.{engine}.parameter_robustness.pass")
        close(julia["passed"], recomputed_pass, f"julia.engine_results.{engine}.parameter_robustness.passed")
        passes["jax"][engine] = recomputed_pass
        passes["julia"][engine] = recomputed_pass
        details[engine] = {"maximum_cross_runtime_gap": maximum_gap, "multipliers": [0.9, 1.0, 1.1], "pass": recomputed_pass}
    return {"engines": details, "pass": all(item["pass"] for item in details.values())}, passes


def linear_quantile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def verify_genericity(packet: Packet) -> tuple[dict[str, Any], dict[str, dict[str, bool]]]:
    details: dict[str, Any] = {}
    passes: dict[str, dict[str, bool]] = {"jax": {}, "julia": {}}
    for engine in ENGINE_NAMES:
        jpath = f"jax.engines.{engine}.random_primitive_controls"
        jax = exact_keys(packet.jax["engines"][engine]["random_primitive_controls"], {"control_count", "control_gap_percentile_95", "controls_valid", "matching_rule", "native_contraction_gap", "native_exceeds_control_percentile_95", "rows", "seed"}, jpath)
        close(jax["control_count"], 64, f"{jpath}.control_count")
        require(isinstance(jax["rows"], list) and len(jax["rows"]) == 64, f"{jpath}.rows", "must contain 64 controls")
        jax_gaps = []
        valid_rows = []
        for index, item in enumerate(jax["rows"]):
            path = f"{jpath}.rows[{index}]"
            item = exact_keys(item, {"contraction_gap", "control_index", "cycle_cptp", "maximum_stage_identity_distance_mismatch", "minimum_fixed_state_eigenvalue", "primitive", "subdominant_eigenvalue_modulus"}, path)
            close(item["control_index"], index, f"{path}.control_index")
            subdominant = number(item["subdominant_eigenvalue_modulus"], f"{path}.subdominant_eigenvalue_modulus")
            gap = number(item["contraction_gap"], f"{path}.contraction_gap")
            close(gap, 1.0 - subdominant, f"{path}.contraction_gap")
            cptp = exact_keys(item["cycle_cptp"], {"minimum_choi_eigenvalue", "pass", "trace_preservation_residual"}, f"{path}.cycle_cptp")
            primitive = strict_int(item["control_index"], f"{path}.control_index") == index and number(item["minimum_fixed_state_eigenvalue"], f"{path}.minimum_fixed_state_eigenvalue") > FIXED_TOL and subdominant < 1.0 - CONTRACTION_TOL and strict_bool(cptp["pass"], f"{path}.cycle_cptp.pass")
            close(item["primitive"], primitive, f"{path}.primitive")
            mismatch = number(item["maximum_stage_identity_distance_mismatch"], f"{path}.maximum_stage_identity_distance_mismatch")
            valid_rows.append(primitive and mismatch <= 1.0e-10)
            jax_gaps.append(gap)
        jax_percentile = linear_quantile(jax_gaps, 0.95)
        close(jax["control_gap_percentile_95"], jax_percentile, f"{jpath}.control_gap_percentile_95")
        controls_valid = all(valid_rows)
        close(jax["controls_valid"], controls_valid, f"{jpath}.controls_valid")
        jax_pass = controls_valid and number(jax["native_contraction_gap"], f"{jpath}.native_contraction_gap") > jax_percentile
        close(jax["native_exceeds_control_percentile_95"], jax_pass, f"{jpath}.native_exceeds_control_percentile_95")

        upath = f"julia.engine_results.{engine}.genericity_kill_control"
        julia = exact_keys(packet.julia["engine_results"][engine]["genericity_kill_control"], {"contraction_gaps", "control_family", "count", "matching_rule", "native_contraction_gap", "passed", "percentile_95"}, upath)
        close(julia["count"], 64, f"{upath}.count")
        require(isinstance(julia["contraction_gaps"], list) and len(julia["contraction_gaps"]) == 64, f"{upath}.contraction_gaps", "must contain 64 controls")
        julia_gaps = [number(value, f"{upath}.contraction_gaps[{index}]") for index, value in enumerate(julia["contraction_gaps"])]
        julia_percentile = sorted(julia_gaps)[math.ceil(0.95 * len(julia_gaps)) - 1]
        close(julia["percentile_95"], julia_percentile, f"{upath}.percentile_95")
        julia_pass = number(julia["native_contraction_gap"], f"{upath}.native_contraction_gap") > julia_percentile
        close(julia["passed"], julia_pass, f"{upath}.passed")
        close(jax["native_contraction_gap"], packet.jax["engines"][engine]["nominal"]["spectrum"]["contraction_gap"], f"{jpath}.native_contraction_gap")
        close(julia["native_contraction_gap"], packet.julia["engine_results"][engine]["nominal_analysis"]["contraction_gap"], f"{upath}.native_contraction_gap")
        require(not jax_pass and not julia_pass, f"genericity.{engine}", "genericity failure must be preserved; this is not distinctive")
        passes["jax"][engine] = jax_pass
        passes["julia"][engine] = julia_pass
        details[engine] = {"jax_percentile_95": jax_percentile, "julia_percentile_95": julia_percentile, "jax_failed": not jax_pass, "julia_failed": not julia_pass}
    return {"engines": details, "genericity_failed_in_both_runtimes": True, "pass": True}, passes


def verify_sanity_controls(packet: Packet, nominal_tests: dict[str, dict[str, dict[str, bool]]]) -> tuple[dict[str, Any], dict[str, dict[str, dict[str, bool]]]]:
    details: dict[str, Any] = {}
    values: dict[str, dict[str, dict[str, bool]]] = {"jax": {}, "julia": {}}
    for engine in ENGINE_NAMES:
        jbasis = exact_keys(packet.jax["engines"][engine]["basis_covariance"], {"maximum_gap", "pass", "transforms"}, f"jax.engines.{engine}.basis_covariance")
        exact_keys(jbasis["transforms"], {"I", "X", "Y", "Z"}, f"jax.engines.{engine}.basis_covariance.transforms")
        jmax = 0.0
        for name, row in jbasis["transforms"].items():
            row = exact_keys(row, {"bures_trajectory_gap", "spectrum_multiset_gap", "state_trajectory_covariance_residual", "trace_distance_trajectory_gap", "umegaki_trajectory_gap"}, f"jax.engines.{engine}.basis_covariance.transforms.{name}")
            jmax = max(jmax, *(number(item, f"jax.engines.{engine}.basis_covariance.transforms.{name}.{key}") for key, item in row.items()))
        close(jbasis["maximum_gap"], jmax, f"jax.engines.{engine}.basis_covariance.maximum_gap")
        jt7 = jmax <= COVARIANCE_TOL
        close(jbasis["pass"], jt7, f"jax.engines.{engine}.basis_covariance.pass")

        ubasis = exact_keys(packet.julia["engine_results"][engine]["basis_covariance"], {"passed", "tolerance", "transforms"}, f"julia.engine_results.{engine}.basis_covariance")
        close(ubasis["tolerance"], COVARIANCE_TOL, f"julia.engine_results.{engine}.basis_covariance.tolerance")
        require(isinstance(ubasis["transforms"], list) and len(ubasis["transforms"]) == 4, f"julia.engine_results.{engine}.basis_covariance.transforms", "must contain four transforms")
        julia_transform_passes = []
        for index, row in enumerate(ubasis["transforms"]):
            path = f"julia.engine_results.{engine}.basis_covariance.transforms[{index}]"
            row = exact_keys(row, {"basis_transform", "errors", "passed"}, path)
            errors = exact_keys(row["errors"], {"bures_horizons", "fixed_state_trace_distance", "relative_entropy_horizons", "spectrum_multiset", "trace_distance_trajectory"}, f"{path}.errors")
            passed = max(number(item, f"{path}.errors.{key}") for key, item in errors.items()) <= COVARIANCE_TOL
            close(row["passed"], passed, f"{path}.passed")
            julia_transform_passes.append(passed)
        ut7 = all(julia_transform_passes)
        close(ubasis["passed"], ut7, f"julia.engine_results.{engine}.basis_covariance.passed")

        junitary = exact_keys(packet.jax["engines"][engine]["unitary_no_attraction_control"], {"all_stages_cptp", "erasure", "fixed_point_multiplicity", "ordered_tokens", "pass", "strict_attraction_destroyed", "subdominant_eigenvalue_modulus"}, f"jax.engines.{engine}.unitary_no_attraction_control")
        jt10 = number(junitary["subdominant_eigenvalue_modulus"], f"jax.engines.{engine}.unitary.subdominant") >= 1.0 - CONTRACTION_TOL or strict_int(junitary["fixed_point_multiplicity"], f"jax.engines.{engine}.unitary.multiplicity") != 1
        close(junitary["strict_attraction_destroyed"], jt10, f"jax.engines.{engine}.unitary.strict_attraction_destroyed")
        close(junitary["pass"], jt10, f"jax.engines.{engine}.unitary.pass")
        uunitary = exact_keys(packet.julia["engine_results"][engine]["unitary_no_attraction_control"], {"erasure_rule", "fixed_point_multiplicity", "passed", "strict_attraction_destroyed", "subdominant_eigenvalue_modulus"}, f"julia.engine_results.{engine}.unitary_no_attraction_control")
        ut10 = number(uunitary["subdominant_eigenvalue_modulus"], f"julia.engine_results.{engine}.unitary.subdominant") >= 1.0 - CONTRACTION_TOL or strict_int(uunitary["fixed_point_multiplicity"], f"julia.engine_results.{engine}.unitary.multiplicity") != 1
        close(uunitary["strict_attraction_destroyed"], ut10, f"julia.engine_results.{engine}.unitary.strict_attraction_destroyed")
        close(uunitary["passed"], ut10, f"julia.engine_results.{engine}.unitary.passed")

        jcommuting = exact_keys(
            packet.jax["controls"]["commuting_fixed_manifold"],
            {"construction", "cycle_cptp", "fixed_manifold_retained", "fixed_point_multiplicity", "pass", "subdominant_eigenvalue_modulus"},
            "jax.controls.commuting_fixed_manifold",
        )
        ucommuting = exact_keys(packet.julia["engine_results"][engine]["commuting_fixed_manifold_control"], {"control_rule", "fixed_point_multiplicity", "nonunique_fixed_manifold_retained", "passed", "subdominant_eigenvalue_modulus"}, f"julia.engine_results.{engine}.commuting_fixed_manifold_control")
        jt11 = strict_int(jcommuting["fixed_point_multiplicity"], "jax.controls.commuting_fixed_manifold.fixed_point_multiplicity") >= 2
        ut11 = strict_int(ucommuting["fixed_point_multiplicity"], f"julia.engine_results.{engine}.commuting.multiplicity") >= 2
        close(jcommuting["pass"], jt11, "jax.controls.commuting_fixed_manifold.pass")
        close(ucommuting["passed"], ut11, f"julia.engine_results.{engine}.commuting.passed")
        close(ucommuting["nonunique_fixed_manifold_retained"], ut11, f"julia.engine_results.{engine}.commuting.nonunique_fixed_manifold_retained")
        values["jax"][engine] = {"T4": nominal_tests["jax"][engine]["T4_relative_entropy_pawl"], "T7": jt7, "T10": jt10, "T11": jt11}
        values["julia"][engine] = {"T4": nominal_tests["julia"][engine]["T4_relative_entropy_pawl"], "T7": ut7, "T10": ut10, "T11": ut11}
        details[engine] = {
            "T4_relative_entropy": {"classification": "sanity_only", "jax": values["jax"][engine]["T4"], "julia": values["julia"][engine]["T4"]},
            "T7_basis_covariance": {"classification": "sanity_only", "jax": jt7, "julia": ut7, "cross_runtime_disagreement_is_non_scientific": jt7 != ut7},
            "T10_unitary_no_attraction": {"classification": "sanity_only", "jax": jt10, "julia": ut10},
            "T11_commuting_fixed_manifold": {"classification": "sanity_only", "jax": jt11, "julia": ut11},
        }
    return {"engines": details, "scientific_selection_evidence": False, "implementation_sanity_only": True, "pass": True}, values


def verify_type_difference(packet: Packet) -> bool:
    jax = exact_keys(packet.jax["controls"]["type_difference"], {"fixed_point_trace_distance", "maximum_depth_profile_gap", "pass", "threshold"}, "jax.controls.type_difference")
    julia = exact_keys(packet.julia["type_difference_control"], {"fixed_point_trace_distance", "maximum_depth_profile_difference", "passed", "threshold"}, "julia.type_difference_control")
    close(jax["threshold"], 1.0e-6, "jax.controls.type_difference.threshold")
    close(julia["threshold"], 1.0e-6, "julia.type_difference_control.threshold")
    close(jax["fixed_point_trace_distance"], julia["fixed_point_trace_distance"], "parity.type_difference.fixed_point_trace_distance")
    jpass = max(number(jax["fixed_point_trace_distance"], "jax.type_difference.fixed"), number(jax["maximum_depth_profile_gap"], "jax.type_difference.depth")) > 1.0e-6
    upass = max(number(julia["fixed_point_trace_distance"], "julia.type_difference.fixed"), number(julia["maximum_depth_profile_difference"], "julia.type_difference.depth")) > 1.0e-6
    close(jax["pass"], jpass, "jax.controls.type_difference.pass")
    close(julia["passed"], upass, "julia.type_difference_control.passed")
    require(jpass == upass, "parity.type_difference", "test outcomes disagree")
    return jpass


def verify_test_projection(
    packet: Packet,
    nominal: dict[str, dict[str, dict[str, bool]]],
    robustness: dict[str, dict[str, bool]],
    genericity: dict[str, dict[str, bool]],
    sanity: dict[str, dict[str, dict[str, bool]]],
) -> dict[str, Any]:
    t12 = verify_type_difference(packet)
    overall: dict[str, dict[str, bool]] = {}
    for runtime in ("jax", "julia"):
        overall[runtime] = {
            "T1": all(nominal[runtime][engine]["T1_unique_full_rank_fixed_point"] for engine in ENGINE_NAMES),
            "T2": all(nominal[runtime][engine]["T2_strict_transverse_contraction"] for engine in ENGINE_NAMES),
            "T3": all(nominal[runtime][engine]["T3_global_sampled_convergence"] for engine in ENGINE_NAMES),
            "T4": all(sanity[runtime][engine]["T4"] for engine in ENGINE_NAMES),
            "T5": all(nominal[runtime][engine]["T5_depth_matches_spectral_prediction"] for engine in ENGINE_NAMES),
            "T6": all(robustness[runtime].values()),
            "T7": all(sanity[runtime][engine]["T7"] for engine in ENGINE_NAMES),
            "T9": all(genericity[runtime].values()),
            "T10": all(sanity[runtime][engine]["T10"] for engine in ENGINE_NAMES),
            "T11": all(sanity[runtime][engine]["T11"] for engine in ENGINE_NAMES),
            "T12": t12,
        }
    close(overall["jax"], overall["julia"], "parity.tests.overall")

    reported_jax = packet.jax["preregistered_tests"]
    jax_projection = {
        "T1": reported_jax["T1_unique_full_rank_fixed_point"],
        "T2": reported_jax["T2_strict_transverse_contraction"],
        "T3": reported_jax["T3_global_sampled_convergence"],
        "T4": reported_jax["T4_relative_entropy_pawl"],
        "T5": reported_jax["T5_depth_matches_spectral_prediction"],
        "T6": reported_jax["T6_parameter_robustness"],
        "T7": reported_jax["T7_basis_covariance"],
        "T9": reported_jax["T9_genericity_kill_control"],
        "T10": reported_jax["T10_unitary_no_attraction_control"],
        "T11": reported_jax["T11_commuting_fixed_manifold_control"],
        "T12": reported_jax["T12_type_difference"],
    }
    close(jax_projection, overall["jax"], "jax.preregistered_tests.projection")
    for engine in ENGINE_NAMES:
        julia_reported = packet.julia["test_summary"]["T1_T7_T9_T12"][engine]
        exact_keys(julia_reported, SHORT_TEST_KEYS | {"T12"}, f"julia.test_summary.{engine}")
        close(julia_reported, {**overall["julia"], "T7": sanity["julia"][engine]["T7"]}, f"julia.test_summary.{engine}")
        nested_reported = packet.julia["engine_results"][engine]["nominal_tests"]
        exact_keys(nested_reported, SHORT_TEST_KEYS | {"T12"}, f"julia.engine_results.{engine}.nominal_tests")
        nested_expected = {
            "T1": nominal["julia"][engine]["T1_unique_full_rank_fixed_point"],
            "T2": nominal["julia"][engine]["T2_strict_transverse_contraction"],
            "T3": nominal["julia"][engine]["T3_global_sampled_convergence"],
            "T4": sanity["julia"][engine]["T4"],
            "T5": nominal["julia"][engine]["T5_depth_matches_spectral_prediction"],
            "T6": robustness["julia"][engine],
            "T7": sanity["julia"][engine]["T7"],
            "T9": genericity["julia"][engine],
            "T10": sanity["julia"][engine]["T10"],
            "T11": sanity["julia"][engine]["T11"],
            "T12": t12,
        }
        close(nested_reported, nested_expected, f"julia.engine_results.{engine}.nominal_tests")
    return {"jax": overall["jax"], "julia": overall["julia"], "all_overall_test_booleans_match": True, "pass": True}


def validate_payloads(packet: Packet, *, enforce_hashes: bool) -> dict[str, Any]:
    if NUMPY_IMPORT_ERROR is not None:
        fail("runtime.numpy", f"required independent linear algebra unavailable: {NUMPY_IMPORT_ERROR}")
    verify_schemas_and_ceilings(packet)
    hashes = verify_hashes(packet) if enforce_hashes else {}
    slots = verify_slots(packet)
    affine, globally_contracting = verify_affine(packet)
    require(globally_contracting, "global_contraction", "global strict Bloch contraction coefficients must both be <1")
    nominal_receipt, nominal_tests = verify_nominal(packet)
    schedules, native_not_selected = verify_schedules(packet)
    require(native_not_selected, "schedule_atlas", "native order must not be selected by the exact same-channel atlas")
    robustness_receipt, robustness = verify_robustness(packet)
    genericity_receipt, genericity = verify_genericity(packet)
    sanity_receipt, sanity = verify_sanity_controls(packet, nominal_tests)
    tests = verify_test_projection(packet, nominal_tests, robustness, genericity, sanity)
    parity_pass = all(
        receipt["pass"]
        for receipt in (slots, affine, nominal_receipt, schedules, robustness_receipt, genericity_receipt, sanity_receipt, tests)
    )
    accepted = ACCEPTED_LABEL if globally_contracting and parity_pass else BLOCKED_LABEL
    return {
        "hashes": hashes,
        "slots": slots,
        "affine_contraction": affine,
        "nominal_cross_runtime_parity": nominal_receipt,
        "schedule_atlas_rank": schedules,
        "parameter_robustness": robustness_receipt,
        "genericity": genericity_receipt,
        "sanity_only_tests": sanity_receipt,
        "test_projection": tests,
        "cross_runtime_parity_pass": parity_pass,
        "accepted_scientific_label": accepted,
    }


def run_mutation_self_tests(packet: Packet) -> dict[str, Any]:
    cases = []

    def rejected(name: str, mutate: Callable[[Packet], None], expected_fragment: str) -> None:
        candidate = copy.deepcopy(packet)
        mutate(candidate)
        error = ""
        try:
            validate_payloads(candidate, enforce_hashes=False)
        except ValidationError as exc:
            error = str(exc)
        cases.append(
            {
                "name": name,
                "expected_error_fragment": expected_fragment,
                "observed_error": error,
                "validator_rejected": bool(error),
                "pass": bool(error) and expected_fragment in error,
            }
        )

    rejected(
        "result_alteration",
        lambda candidate: candidate.jax["engines"]["Type1_left"]["bloch_affine_readout"]["linear_matrix"][0].__setitem__(0, candidate.jax["engines"]["Type1_left"]["bloch_affine_readout"]["linear_matrix"][0][0] + 0.01),
        "singular_values",
    )
    rejected(
        "ceiling_removal",
        lambda candidate: candidate.jax.pop("claim_ceiling"),
        "closed schema keys differ",
    )

    def make_noncontractive(candidate: Packet) -> None:
        for engine in ENGINE_NAMES:
            for affine in (
                candidate.jax["engines"][engine]["bloch_affine_readout"],
                candidate.julia["engine_results"][engine]["bloch_ball_affine_readout"],
            ):
                matrix = np.asarray(affine["linear_matrix"], dtype=np.float64) * 3.0
                singular = np.linalg.svd(matrix, compute_uv=False)
                affine["linear_matrix"] = matrix.tolist()
                affine["singular_values"] = singular.tolist()
                affine["trace_distance_contraction_coefficient"] = float(singular[0])

    rejected("affine_coefficient_above_one", make_noncontractive, "global strict Bloch contraction")
    return {
        "schema": f"codex_ratchet.{SIM_ID}.mutation_self_tests.v1",
        "kind": "in_memory_result_corruption",
        "cases": cases,
        "case_count": len(cases),
        "all_pass": all(case["pass"] for case in cases),
    }


def success_receipt(packet: Packet) -> dict[str, Any]:
    validation = validate_payloads(packet, enforce_hashes=True)
    mutation_tests = run_mutation_self_tests(packet)
    require(mutation_tests["all_pass"], "mutation_self_tests", "one or more corruptions escaped rejection")
    return {
        "schema": f"codex_ratchet.{SIM_ID}.independent_validation.v1",
        "sim_id": SIM_ID,
        "validator_role": "independent_mechanical_gatekeeper",
        "classification": CLASSIFICATION,
        "artifact_validation_all_pass": True,
        "accepted_scientific_label": validation["accepted_scientific_label"],
        "preregistered_result_preserved": PREREG_VERDICT,
        "posthoc_interpretation": "The installed Type1 and Type2 affine qubit channels are independently cross-runtime-matched global contractions with unique full-rank fixed points; the native order is not selected and genericity fails.",
        "claim_ceiling": packet.spec["claim_ceiling"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "claim_rejections": {
            "ratchet_selected": True,
            "distinctive": True,
            "co_ratchet": True,
            "basin_depth": True,
            "axis0": True,
            "engine_result": True,
            "perception": True,
            "canonical": True,
        },
        "checks": validation,
        "mutation_self_tests": mutation_tests,
        "source_result_and_receipt_hashes": validation["hashes"],
        "validator_source_sha256": sha256(Path(__file__)),
        "blocked_consumers": packet.spec["blocked_consumers"],
    }


def failure_receipt(error: ValidationError) -> dict[str, Any]:
    observed_hashes: dict[str, str | None] = {}
    for path in FROZEN_HASHES:
        try:
            observed_hashes[relative(path)] = sha256(path)
        except OSError:
            observed_hashes[relative(path)] = None
    return {
        "schema": f"codex_ratchet.{SIM_ID}.independent_validation.v1",
        "sim_id": SIM_ID,
        "validator_role": "independent_mechanical_gatekeeper",
        "classification": CLASSIFICATION,
        "artifact_validation_all_pass": False,
        "accepted_scientific_label": BLOCKED_LABEL,
        "preregistered_result_preserved": PREREG_VERDICT,
        "claim_ceiling": "No scientific result is accepted after a mechanical validation failure.",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "error": str(error),
        "observed_hashes": observed_hashes,
        "mutation_self_tests": "not_run_or_not_accepted_after_base_validation_failure",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        receipt = success_receipt(load_packet())
    except ValidationError as exc:
        receipt = failure_receipt(exc)
    except Exception as exc:
        receipt = failure_receipt(
            ValidationError(f"unexpected validator error {type(exc).__name__}: {exc}")
        )
    strict_write_json(args.output, receipt)
    print(
        json.dumps(
            {
                "artifact_validation_all_pass": receipt["artifact_validation_all_pass"],
                "accepted_scientific_label": receipt["accepted_scientific_label"],
                "output": str(args.output),
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0 if receipt["artifact_validation_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
