#!/usr/bin/env python3
"""Fail-closed independent validator for the free-length schedule selector."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from jax import config

config.update("jax_enable_x64", True)
import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
SPEC_HASH_PATH = HERE / "spec.sha256"
PREREG_PATH = HERE / "preregistration_receipt.json"
OBJECT_CARD_PATH = HERE / "wizard_v4_3_object_card.json"
PRODUCER_PATH = HERE / "free_length_dual_ratchet_schedule_selector_v0_jax.py"
SCHEDULE_PATH = (
    REPO
    / "system_v7/constraint_core/reference_docs/engine_math/source_schedule_tables"
    / "engine_16_source_stage_slots.json"
)
CORRECTION_PATH = (
    REPO
    / "system_v7/constraint_core/corrections"
    / "ENGINE_SOURCE_SLOT_SEMANTIC_CORRECTION_2026-07-09.md"
)
RESULTS = HERE / "results"
CATALOG_PATH = RESULTS / "candidate_catalog.json"
SUMMARY_PATH = RESULTS / "free_length_dual_ratchet_schedule_selector_v0_results.json"
RAW_PATH = RESULTS / "free_length_dual_ratchet_schedule_selector_v0_raw_scores.json"
RERUN_SUMMARY_PATH = RESULTS / "free_length_dual_ratchet_schedule_selector_v0_rerun_results.json"
RERUN_RAW_PATH = RESULTS / "free_length_dual_ratchet_schedule_selector_v0_rerun_raw_scores.json"

SIM_ID = "free_length_dual_ratchet_schedule_selector_v0"
OPS = ("Ti", "Te", "Fi", "Fe")
ENGINES = ("Type1_left", "Type2_right")
TERRAIN_INDEX = {
    "Se-in": 0,
    "Ne-in": 1,
    "Ni-in": 2,
    "Si-in": 3,
    "Se-out": 4,
    "Si-out": 5,
    "Ni-out": 6,
    "Ne-out": 7,
}

CATALOG_KEYS = {
    "schema",
    "sim_id",
    "spec_sha256",
    "alphabet",
    "equivalence_relation",
    "metadata",
    "candidates",
}
CANDIDATE_KEYS = {
    "index",
    "cycle_id",
    "length",
    "operator_indices",
    "primitive_period",
    "distinct_phase_count",
    "evaluated_phase_count",
    "distinct_phase_indices_sha256",
    "unique_operator_count",
    "uses_all_four_exactly_once",
}
RAW_KEYS = {
    "schema",
    "sim_id",
    "spec_sha256",
    "candidate_catalog_sha256",
    "candidate_axis_count",
    "scenario_axis_count",
    "engine_axis",
    "arrays",
    "control_combined_score_arrays",
}
ARRAY_KEYS = {"dtype", "shape", "encoding", "sha256", "data"}
PREREG_KEYS = {
    "schema",
    "sim_id",
    "preregistered_date",
    "classification",
    "promotion_allowed",
    "formal_admission_allowed",
    "stage_movement_allowed",
    "spec_path",
    "spec_sha256",
    "object_card_path",
    "object_card_sha256",
    "source_schedule_sha256",
    "semantic_correction_sha256",
    "files_present_at_freeze",
    "observed_result_files_present_at_freeze",
    "observed_results_run_before_freeze",
    "freeze_rule",
    "maximum_possible_claim_ceiling",
    "blocked_consumers",
}
SUMMARY_KEYS = {
    "schema",
    "sim_id",
    "classification",
    "promotion_allowed",
    "formal_admission_allowed",
    "stage_movement_allowed",
    "sim_execution_kind",
    "engine_mode",
    "preregistration",
    "source_hashes",
    "candidate_catalog_sha256",
    "raw_scores_sha256",
    "candidate_space",
    "scenario_manifest",
    "source_slot_rows",
    "scenario_results",
    "aggregate_winners",
    "qualifying_counts",
    "physical_preconditions",
    "controls",
    "scientific_signal",
    "scientific_signal_pass",
    "physical_preconditions_pass",
    "gating_controls_pass",
    "scientific_pass",
    "scientific_verdict",
    "execution_checks",
    "execution_complete",
    "artifact_validity_claimed_by_producer",
    "artifact_validity_requires_independent_validator",
    "accepted_scientific_ceiling",
    "classification",
    "promotion_allowed",
    "formal_admission_allowed",
    "stage_movement_allowed",
    "claim_ceiling",
    "eligible_consumers",
    "blocked_consumers",
    "roles",
    "jax",
    "package_fingerprint",
    "TOOL_MANIFEST",
    "TOOL_INTEGRATION_DEPTH",
    "tool_calls",
}
SCENARIO_KEYS = {"scenario_index", "scenario_id", "perturbation_id", "seed", "radius"}
SCENARIO_RESULT_KEYS = SCENARIO_KEYS | {"engines"}
ENGINE_ROW_KEYS = {
    "winner_cycle_ids",
    "winner_count",
    "unique_winner",
    "best_score",
    "top_two_margin",
    "raw_top_two_margin",
    "tie_tolerance",
    "winner_lengths",
    "winner_primitive_periods",
    "winner_mean_absolute_entropy_movement",
    "geometry_only_winner_cycle_ids",
    "geometry_only_winner_count",
    "geometry_only_winner_ids_sha256",
    "entropy_only_winner_cycle_ids",
    "entropy_only_winner_count",
    "entropy_only_winner_ids_sha256",
    "pareto_cycle_ids",
    "pareto_cycle_count",
    "pareto_cycle_ids_sha256",
    "component_sets_compacted",
    "top_k",
    "best_qualifying_primitive_length4_score",
    "best_nonqualifying_score",
    "qualifying_advantage_margin",
    "score_vector_sha256",
}
TOP_K_KEYS = {
    "cycle_id",
    "length",
    "primitive_period",
    "score",
    "geometry_loss",
    "entropy_loss",
    "mean_absolute_entropy_movement",
}

BOOLEAN_KEYS = {
    "pass",
    "gating",
    "ran",
    "x64",
    "reads_peer_result",
    "tried",
    "used",
    "unique_winner",
    "uses_all_four_exactly_once",
    "component_sets_compacted",
    "winner_sets_stable",
    "score_function_accepts_native_metadata",
    "anchor_winners_changed",
    "immutable_v0",
    "observed_results_run_before_freeze",
    "artifact_validity_claimed_by_producer",
    "artifact_validity_requires_independent_validator",
    "execution_complete",
    "scientific_signal_pass",
    "physical_preconditions_pass",
    "gating_controls_pass",
    "scientific_pass",
    "promotion_allowed",
    "formal_admission_allowed",
    "stage_movement_allowed",
}


class ValidationError(RuntimeError):
    """Raised on the first packet-integrity failure."""


@dataclass(frozen=True)
class Candidate:
    index: int
    cycle_id: str
    length: int
    word: tuple[int, ...]
    primitive_period: int
    distinct_phases: tuple[tuple[int, ...], ...]
    unique_operator_count: int
    uses_all_four_exactly_once: bool


@dataclass
class Packet:
    spec: dict[str, Any]
    prereg: dict[str, Any]
    schedule: list[dict[str, Any]]
    catalog: dict[str, Any]
    summary: dict[str, Any]
    raw: dict[str, Any]
    rerun_summary: dict[str, Any]
    rerun_raw: dict[str, Any]


@dataclass
class ValidationContext:
    packet: Packet
    candidates: list[Candidate]
    main_arrays: dict[str, np.ndarray]
    control_arrays: dict[str, np.ndarray]


def fail(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"JSON: duplicate key {key!r}")
        result[key] = value
    return result


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValidationError(f"JSON: nonfinite number {value!r}")
    return parsed


def strict_json_load(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_pairs_no_duplicates,
            parse_float=_finite_float,
            parse_constant=lambda value: fail("JSON", f"nonfinite constant {value!r}"),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: unreadable strict JSON: {exc}") from exc


def exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(path, "must be an object")
    actual = set(value)
    if actual != expected:
        fail(path, f"closed schema keys differ; missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    return value


def strict_int(value: Any, path: str, *, minimum: int | None = None) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        fail(path, "must be an integer, not a boolean or coercible value")
    if minimum is not None and value < minimum:
        fail(path, f"must be >= {minimum}")
    return value


def strict_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        fail(path, "must be a JSON boolean")
    return value


def finite_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(path, "must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        fail(path, "must be finite")
    return result


def verify_boolean_types(value: Any, path: str = "$" ) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in BOOLEAN_KEYS or (key.endswith("_pass") and not key.endswith("_pass_rule")):
                strict_bool(item, child)
            verify_boolean_types(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            verify_boolean_types(item, f"{path}[{index}]")


def close_enough(actual: Any, expected: Any, path: str, *, atol: float = 2.0e-14) -> None:
    if isinstance(expected, bool):
        if actual is not expected:
            fail(path, f"expected boolean {expected}, got {actual!r}")
    elif isinstance(expected, float):
        number = finite_number(actual, path)
        if not math.isclose(number, expected, rel_tol=0.0, abs_tol=atol):
            fail(path, f"expected {expected!r}, got {number!r}")
    elif isinstance(expected, dict):
        exact_keys(actual, set(expected), path)
        for key, item in expected.items():
            close_enough(actual[key], item, f"{path}.{key}", atol=atol)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            fail(path, f"expected list length {len(expected)}, got {type(actual).__name__}")
        for index, item in enumerate(expected):
            close_enough(actual[index], item, f"{path}[{index}]", atol=atol)
    elif actual != expected or type(actual) is not type(expected):
        fail(path, f"expected {expected!r} ({type(expected).__name__}), got {actual!r}")


def canonical_rotation(word: Sequence[int]) -> tuple[int, ...]:
    value = tuple(int(item) for item in word)
    return min(value[offset:] + value[:offset] for offset in range(len(value)))


def distinct_rotations(word: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    value = tuple(int(item) for item in word)
    return tuple(sorted({value[offset:] + value[:offset] for offset in range(len(value))}))


def primitive_period(word: Sequence[int]) -> int:
    value = tuple(word)
    for period in range(1, len(value) + 1):
        if len(value) % period == 0 and all(value[index] == value[index % period] for index in range(len(value))):
            return period
    raise AssertionError("unreachable")


def build_expected_catalog(spec: dict[str, Any]) -> tuple[dict[str, Any], list[Candidate]]:
    candidates: list[Candidate] = []
    rooted_counts: dict[int, int] = {}
    necklace_counts: Counter[int] = Counter()
    l4_exact = 0
    l4_other = 0
    for raw_length in spec["candidate_space"]["lengths"]:
        length = strict_int(raw_length, "spec.candidate_space.lengths[]", minimum=1)
        rooted_counts[length] = len(OPS) ** length
        for rooted in itertools.product(range(len(OPS)), repeat=length):
            canonical = canonical_rotation(rooted)
            if rooted != canonical:
                continue
            phases = distinct_rotations(canonical)
            exact_four = length == 4 and Counter(canonical) == Counter(range(4))
            candidate = Candidate(
                index=len(candidates),
                cycle_id=f"L{length}:" + ">".join(OPS[item] for item in canonical),
                length=length,
                word=canonical,
                primitive_period=primitive_period(canonical),
                distinct_phases=phases,
                unique_operator_count=len(set(canonical)),
                uses_all_four_exactly_once=exact_four,
            )
            candidates.append(candidate)
            necklace_counts[length] += 1
            if length == 4:
                l4_exact += int(exact_four)
                l4_other += int(not exact_four)

    checks = {
        "rooted_counts_match_spec": {str(k): v for k, v in rooted_counts.items()}
        == spec["candidate_space"]["rooted_word_counts_by_length"],
        "rooted_total_matches_spec": sum(rooted_counts.values())
        == spec["candidate_space"]["rooted_word_count_total"],
        "necklace_counts_match_spec": {str(k): v for k, v in sorted(necklace_counts.items())}
        == spec["candidate_space"]["oriented_necklace_counts_by_length"],
        "necklace_total_matches_spec": len(candidates)
        == spec["candidate_space"]["oriented_necklace_count_total"],
        "all_rooted_words_mapped": True,
        "length4_exact_one_each_count_matches": l4_exact
        == spec["candidate_space"]["length4_necklace_exactly_one_each"],
        "length4_other_count_matches": l4_other == spec["candidate_space"]["length4_necklace_other"],
        "repetition_present": any(c.unique_operator_count < c.length for c in candidates),
        "operator_omission_present": any(c.unique_operator_count < 4 for c in candidates),
        "cyclic_phase_evaluation_count_matches_spec": sum(c.length for c in candidates)
        == spec["candidate_space"]["cyclic_phase_evaluation_count_total"],
        "reversal_not_quotiented": any(
            canonical_rotation(tuple(reversed(c.word))) != c.word for c in candidates
        ),
    }
    if not all(checks.values()):
        fail("catalog", f"spec combinatorics are internally inconsistent: {checks}")
    metadata = {
        "rooted_word_counts_by_length": {str(key): value for key, value in rooted_counts.items()},
        "oriented_necklace_counts_by_length": {
            str(key): value for key, value in sorted(necklace_counts.items())
        },
        "rooted_word_count_total": sum(rooted_counts.values()),
        "oriented_necklace_count_total": len(candidates),
        "cyclic_phase_evaluation_count_total": sum(c.length for c in candidates),
        "length4_necklace_exactly_one_each": l4_exact,
        "length4_necklace_other": l4_other,
        "checks": checks,
    }
    payload = {
        "schema": f"codex_ratchet.{SIM_ID}.candidate_catalog.v1",
        "sim_id": SIM_ID,
        "spec_sha256": sha256(SPEC_PATH),
        "alphabet": list(OPS),
        "equivalence_relation": "cyclic_rotation_only_reversal_distinct",
        "metadata": metadata,
        "candidates": [
            {
                "index": c.index,
                "cycle_id": c.cycle_id,
                "length": c.length,
                "operator_indices": list(c.word),
                "primitive_period": c.primitive_period,
                "distinct_phase_count": len(c.distinct_phases),
                "evaluated_phase_count": c.length,
                "distinct_phase_indices_sha256": sha256_bytes(
                    np.asarray(c.distinct_phases, dtype=np.int8).tobytes(order="C")
                ),
                "unique_operator_count": c.unique_operator_count,
                "uses_all_four_exactly_once": c.uses_all_four_exactly_once,
            }
            for c in candidates
        ],
    }
    return payload, candidates


def verify_catalog(catalog: dict[str, Any], spec: dict[str, Any]) -> list[Candidate]:
    exact_keys(catalog, CATALOG_KEYS, "catalog")
    if not isinstance(catalog.get("candidates"), list):
        fail("catalog.candidates", "must be a list")
    for index, row in enumerate(catalog["candidates"]):
        exact_keys(row, CANDIDATE_KEYS, f"catalog.candidates[{index}]")
        strict_int(row["index"], f"catalog.candidates[{index}].index", minimum=0)
        strict_bool(
            row["uses_all_four_exactly_once"],
            f"catalog.candidates[{index}].uses_all_four_exactly_once",
        )
    expected, candidates = build_expected_catalog(spec)
    close_enough(catalog, expected, "catalog", atol=0.0)
    return candidates


def decode_array(value: Any, expected_shape: tuple[int, ...], path: str) -> np.ndarray:
    descriptor = exact_keys(value, ARRAY_KEYS, path)
    if descriptor["dtype"] != "<f8" or descriptor["encoding"] != "base64":
        fail(path, "only base64 C-contiguous little-endian float64 is accepted")
    if not isinstance(descriptor["shape"], list):
        fail(f"{path}.shape", "must be a list")
    shape = tuple(strict_int(item, f"{path}.shape[]", minimum=0) for item in descriptor["shape"])
    if shape != expected_shape:
        fail(f"{path}.shape", f"expected {expected_shape}, got {shape}")
    data = descriptor["data"]
    if not isinstance(data, str):
        fail(f"{path}.data", "must be a base64 string")
    try:
        payload = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValidationError(f"{path}.data: invalid base64: {exc}") from exc
    expected_bytes = math.prod(expected_shape) * 8
    if len(payload) != expected_bytes:
        fail(f"{path}.data", f"expected {expected_bytes} decoded bytes, got {len(payload)}")
    if not isinstance(descriptor["sha256"], str) or sha256_bytes(payload) != descriptor["sha256"]:
        fail(f"{path}.sha256", "decoded array hash mismatch")
    array = np.frombuffer(payload, dtype="<f8").reshape(expected_shape)
    if not np.all(np.isfinite(array)):
        fail(path, "decoded array contains nonfinite values")
    return array


def verify_raw(raw: dict[str, Any], spec: dict[str, Any], catalog_hash: str) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    exact_keys(raw, RAW_KEYS, "raw")
    candidate_count = strict_int(raw["candidate_axis_count"], "raw.candidate_axis_count", minimum=1)
    scenario_count = strict_int(raw["scenario_axis_count"], "raw.scenario_axis_count", minimum=1)
    expected_candidate_count = spec["candidate_space"]["oriented_necklace_count_total"]
    expected_scenario_count = spec["scenario_grid"]["scenario_count_per_engine"]
    if candidate_count != expected_candidate_count or scenario_count != expected_scenario_count:
        fail("raw", "axis counts do not match the frozen spec")
    if raw["schema"] != f"codex_ratchet.{SIM_ID}.raw_scores.v1" or raw["sim_id"] != SIM_ID:
        fail("raw", "schema or sim_id mismatch")
    if raw["spec_sha256"] != sha256(SPEC_PATH) or raw["candidate_catalog_sha256"] != catalog_hash:
        fail("raw", "spec/catalog cross-binding mismatch")
    if raw["engine_axis"] != list(ENGINES):
        fail("raw.engine_axis", f"expected {list(ENGINES)}")
    expected_main = {
        "combined_score",
        "geometry_loss",
        "entropy_loss",
        "mean_absolute_entropy_movement",
    }
    expected_controls = {
        "axis6_sign_scramble",
        "commuting_leg_substitution",
        "fixed_per_beat_exposure",
        "loop_role_swap",
        "operator_identity_erasure",
        "operator_label_permutation",
    }
    exact_keys(raw["arrays"], expected_main, "raw.arrays")
    exact_keys(raw["control_combined_score_arrays"], expected_controls, "raw.controls")
    main_shape = (scenario_count, len(ENGINES), candidate_count)
    anchor_count = spec["controls"]["anchor_scenarios"]["required_frequency_count"]
    control_shape = (strict_int(anchor_count, "spec.controls.anchor.required_frequency_count"), len(ENGINES), candidate_count)
    main = {
        key: decode_array(raw["arrays"][key], main_shape, f"raw.arrays.{key}")
        for key in sorted(expected_main)
    }
    controls = {
        key: decode_array(
            raw["control_combined_score_arrays"][key], control_shape, f"raw.controls.{key}"
        )
        for key in sorted(expected_controls)
    }
    return main, controls


def complexity_vector(candidates: Sequence[Candidate], spec: dict[str, Any]) -> np.ndarray:
    bits = {int(key): int(value) for key, value in spec["complexity_rule"]["description_bits_by_length"].items()}
    minimum = min(bits.values())
    maximum = max(bits.values())
    coefficient = float(spec["complexity_rule"]["coefficient"])
    return np.asarray(
        [coefficient * (bits[c.length] - minimum) / (maximum - minimum) for c in candidates],
        dtype=np.float64,
    )


def verify_score_semantics(main: dict[str, np.ndarray], candidates: Sequence[Candidate], spec: dict[str, Any]) -> None:
    geometry = main["geometry_loss"]
    entropy = main["entropy_loss"]
    movement = main["mean_absolute_entropy_movement"]
    combined = main["combined_score"]
    expected = np.maximum(geometry, entropy) + complexity_vector(candidates, spec)[None, None, :]
    if not np.allclose(combined, expected, rtol=0.0, atol=3.0e-15):
        fail("raw.arrays.combined_score", "does not recompute as max(geometry, entropy) + frozen complexity")
    if np.min(geometry) < -1.0e-12 or np.max(geometry) > 1.0 + 1.0e-12:
        fail("raw.arrays.geometry_loss", "falls outside the frozen normalized objective range")
    if np.min(entropy) < -1.0e-12 or np.max(entropy) > 1.0 + 1.0e-12:
        fail("raw.arrays.entropy_loss", "falls outside the frozen normalized objective range")
    if np.min(movement) < 0.0:
        fail("raw.arrays.mean_absolute_entropy_movement", "contains negative absolute movement")


def expected_scenarios(spec: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for perturbation in spec["scenario_grid"]["perturbations"]:
        for seed in spec["scenario_grid"]["probe_seeds"]:
            for radius in spec["scenario_grid"]["probe_radii"]:
                rows.append(
                    {
                        "scenario_index": len(rows),
                        "scenario_id": f"{perturbation['id']}/seed={seed}/radius={radius}",
                        "perturbation_id": perturbation["id"],
                        "seed": seed,
                        "radius": radius,
                    }
                )
    return rows


def rank(values: np.ndarray, spec: dict[str, Any]) -> dict[str, Any]:
    best = float(np.min(values))
    tolerance = float(spec["selection_rule"]["tie_absolute_tolerance"]) + float(
        spec["selection_rule"]["tie_relative_tolerance"]
    ) * abs(best)
    winners = np.flatnonzero(values <= best + tolerance).tolist()
    order = np.argsort(values, kind="stable")
    raw_margin = float(values[order[1]] - values[order[0]])
    return {
        "best_score": best,
        "winner_indices": winners,
        "order": order,
        "top_two_margin": raw_margin if len(winners) == 1 else 0.0,
        "raw_top_two_margin": raw_margin,
        "tie_tolerance": tolerance,
    }


def pareto_indices(geometry: np.ndarray, entropy: np.ndarray) -> list[int]:
    order = np.lexsort((np.arange(len(geometry)), entropy, geometry))
    frontier: list[int] = []
    best_entropy = math.inf
    for index in order:
        current = float(entropy[index])
        if current < best_entropy - 1.0e-15:
            frontier.append(int(index))
            best_entropy = current
    return frontier


def expected_engine_row(
    combined: np.ndarray,
    geometry: np.ndarray,
    entropy: np.ndarray,
    movement: np.ndarray,
    candidates: Sequence[Candidate],
    spec: dict[str, Any],
) -> dict[str, Any]:
    combined_rank = rank(combined, spec)
    geometry_rank = rank(geometry, spec)
    entropy_rank = rank(entropy, spec)
    winners = combined_rank["winner_indices"]
    winner_ids = [candidates[index].cycle_id for index in winners]
    geometry_ids = [candidates[index].cycle_id for index in geometry_rank["winner_indices"]]
    entropy_ids = [candidates[index].cycle_id for index in entropy_rank["winner_indices"]]
    pareto_ids = [candidates[index].cycle_id for index in pareto_indices(geometry, entropy)]
    valid = np.asarray([c.length == 4 and c.primitive_period == 4 for c in candidates], dtype=bool)
    top_k = int(spec["selection_rule"]["top_k_reported_per_scenario"])
    order = combined_rank["order"]
    return {
        "winner_cycle_ids": winner_ids,
        "winner_count": len(winners),
        "unique_winner": len(winners) == 1,
        "best_score": combined_rank["best_score"],
        "top_two_margin": combined_rank["top_two_margin"],
        "raw_top_two_margin": combined_rank["raw_top_two_margin"],
        "tie_tolerance": combined_rank["tie_tolerance"],
        "winner_lengths": sorted({candidates[index].length for index in winners}),
        "winner_primitive_periods": sorted({candidates[index].primitive_period for index in winners}),
        "winner_mean_absolute_entropy_movement": {
            candidates[index].cycle_id: float(movement[index]) for index in winners
        },
        "geometry_only_winner_cycle_ids": geometry_ids,
        "geometry_only_winner_count": len(geometry_ids),
        "geometry_only_winner_ids_sha256": sha256_bytes(canonical_json_bytes(geometry_ids)),
        "entropy_only_winner_cycle_ids": entropy_ids,
        "entropy_only_winner_count": len(entropy_ids),
        "entropy_only_winner_ids_sha256": sha256_bytes(canonical_json_bytes(entropy_ids)),
        "pareto_cycle_ids": pareto_ids,
        "pareto_cycle_count": len(pareto_ids),
        "pareto_cycle_ids_sha256": sha256_bytes(canonical_json_bytes(pareto_ids)),
        "component_sets_compacted": False,
        "top_k": [
            {
                "cycle_id": candidates[index].cycle_id,
                "length": candidates[index].length,
                "primitive_period": candidates[index].primitive_period,
                "score": float(combined[index]),
                "geometry_loss": float(geometry[index]),
                "entropy_loss": float(entropy[index]),
                "mean_absolute_entropy_movement": float(movement[index]),
            }
            for index in order[:top_k]
        ],
        "best_qualifying_primitive_length4_score": float(np.min(combined[valid])),
        "best_nonqualifying_score": float(np.min(combined[~valid])),
        "qualifying_advantage_margin": float(np.min(combined[~valid]) - np.min(combined[valid])),
        "score_vector_sha256": sha256_bytes(np.asarray(combined, dtype="<f8").tobytes(order="C")),
    }


def recompute_main_summary(
    main: dict[str, np.ndarray], candidates: Sequence[Candidate], spec: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, int]]]:
    scenarios = expected_scenarios(spec)
    rows: list[dict[str, Any]] = []
    all_winners = {engine: Counter() for engine in ENGINES}
    unique_winners = {engine: Counter() for engine in ENGINES}
    geometry_winners = {engine: Counter() for engine in ENGINES}
    entropy_winners = {engine: Counter() for engine in ENGINES}
    qualifying = {engine: defaultdict(int) for engine in ENGINES}
    delta = float(spec["selection_rule"]["scientific_margin_delta"])
    for scenario_index, scenario in enumerate(scenarios):
        engines: dict[str, Any] = {}
        for engine_index, engine in enumerate(ENGINES):
            row = expected_engine_row(
                main["combined_score"][scenario_index, engine_index],
                main["geometry_loss"][scenario_index, engine_index],
                main["entropy_loss"][scenario_index, engine_index],
                main["mean_absolute_entropy_movement"][scenario_index, engine_index],
                candidates,
                spec,
            )
            engines[engine] = row
            for cycle_id in row["winner_cycle_ids"]:
                all_winners[engine][cycle_id] += 1
            if row["unique_winner"]:
                cycle_id = row["winner_cycle_ids"][0]
                unique_winners[engine][cycle_id] += 1
                candidate = candidates[next(i for i, c in enumerate(candidates) if c.cycle_id == cycle_id)]
                if candidate.length == 4 and candidate.primitive_period == 4 and row["top_two_margin"] > delta:
                    qualifying[engine][cycle_id] += 1
            for cycle_id in row["geometry_only_winner_cycle_ids"]:
                geometry_winners[engine][cycle_id] += 1
            for cycle_id in row["entropy_only_winner_cycle_ids"]:
                entropy_winners[engine][cycle_id] += 1
        rows.append({**scenario, "engines": engines})
    aggregate = {
        engine: {
            "all_winner_counts": dict(sorted(all_winners[engine].items())),
            "unique_winner_counts": dict(sorted(unique_winners[engine].items())),
            "qualifying_unique_primitive_length4_counts": dict(sorted(qualifying[engine].items())),
            "geometry_only_winner_counts": dict(sorted(geometry_winners[engine].items())),
            "entropy_only_winner_counts": dict(sorted(entropy_winners[engine].items())),
            "all_observed_winner_cycle_ids": sorted(all_winners[engine]),
        }
        for engine in ENGINES
    }
    plain = {engine: dict(sorted(qualifying[engine].items())) for engine in ENGINES}
    return rows, aggregate, plain


def shared_signal(counts: dict[str, dict[str, int]], required: int) -> dict[str, Any]:
    shared = sorted(
        cycle_id
        for cycle_id in set(counts[ENGINES[0]]) & set(counts[ENGINES[1]])
        if counts[ENGINES[0]][cycle_id] >= required and counts[ENGINES[1]][cycle_id] >= required
    )
    return {
        "required_count_per_engine": required,
        "shared_qualifying_cycle_ids": shared,
        "pass": len(shared) == 1,
    }


def verify_main_summary(
    summary: dict[str, Any], main: dict[str, np.ndarray], candidates: Sequence[Candidate], spec: dict[str, Any]
) -> dict[str, Any]:
    exact_keys(summary, SUMMARY_KEYS, "summary")
    if summary["scenario_manifest"] != expected_scenarios(spec):
        fail("summary.scenario_manifest", "does not match the frozen scenario Cartesian product and order")
    expected_rows, aggregate, qualifying = recompute_main_summary(main, candidates, spec)
    if not isinstance(summary["scenario_results"], list) or len(summary["scenario_results"]) != len(expected_rows):
        fail("summary.scenario_results", "scenario coverage is incomplete")
    for index, expected in enumerate(expected_rows):
        observed = summary["scenario_results"][index]
        exact_keys(observed, SCENARIO_RESULT_KEYS, f"summary.scenario_results[{index}]")
        exact_keys(observed["engines"], set(ENGINES), f"summary.scenario_results[{index}].engines")
        for engine in ENGINES:
            exact_keys(observed["engines"][engine], ENGINE_ROW_KEYS, f"summary.scenario_results[{index}].engines.{engine}")
            for top_index, top_row in enumerate(observed["engines"][engine]["top_k"]):
                exact_keys(top_row, TOP_K_KEYS, f"summary.scenario_results[{index}].engines.{engine}.top_k[{top_index}]")
        close_enough(observed, expected, f"summary.scenario_results[{index}]")
    close_enough(summary["aggregate_winners"], aggregate, "summary.aggregate_winners")
    close_enough(summary["qualifying_counts"], qualifying, "summary.qualifying_counts")
    signal = shared_signal(qualifying, int(spec["scientific_pass_rule"]["required_scenarios_per_engine"]))
    close_enough(summary["scientific_signal"], signal, "summary.scientific_signal")
    if summary["scientific_signal_pass"] is not signal["pass"]:
        fail("summary.scientific_signal_pass", "does not recompute from raw score frequencies")
    return signal


def _control_manifest(kind: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    radius = float(spec["controls"]["anchor_scenarios"]["radius"])
    return [
        {
            "scenario_index": index,
            "scenario_id": f"control/{kind}/seed={seed}/radius={radius}",
            "perturbation_id": kind,
            "seed": int(seed),
            "radius": radius,
        }
        for index, seed in enumerate(spec["controls"]["anchor_scenarios"]["seeds"])
    ]


def _control_counts(
    values: np.ndarray,
    candidates: Sequence[Candidate],
    spec: dict[str, Any],
    observed_rows: list[dict[str, Any]],
    path: str,
) -> dict[str, dict[str, int]]:
    counts = {engine: defaultdict(int) for engine in ENGINES}
    manifest = _control_manifest(path.rsplit(".", 1)[-1], spec)
    valid = np.asarray([c.length == 4 and c.primitive_period == 4 for c in candidates], dtype=bool)
    if not isinstance(observed_rows, list) or len(observed_rows) != len(manifest):
        fail(f"{path}.scenario_rows", "anchor scenario coverage mismatch")
    for scenario_index, expected_scenario in enumerate(manifest):
        observed = observed_rows[scenario_index]
        exact_keys(observed, SCENARIO_RESULT_KEYS, f"{path}.scenario_rows[{scenario_index}]")
        for key, item in expected_scenario.items():
            close_enough(observed[key], item, f"{path}.scenario_rows[{scenario_index}].{key}")
        exact_keys(observed["engines"], set(ENGINES), f"{path}.scenario_rows[{scenario_index}].engines")
        for engine_index, engine in enumerate(ENGINES):
            row = observed["engines"][engine]
            exact_keys(row, ENGINE_ROW_KEYS, f"{path}.scenario_rows[{scenario_index}].engines.{engine}")
            current = values[scenario_index, engine_index]
            ranked = rank(current, spec)
            winners = ranked["winner_indices"]
            winner_ids = [candidates[index].cycle_id for index in winners]
            checks = {
                "winner_cycle_ids": winner_ids,
                "winner_count": len(winners),
                "unique_winner": len(winners) == 1,
                "best_score": ranked["best_score"],
                "top_two_margin": ranked["top_two_margin"],
                "raw_top_two_margin": ranked["raw_top_two_margin"],
                "tie_tolerance": ranked["tie_tolerance"],
                "winner_lengths": sorted({candidates[index].length for index in winners}),
                "winner_primitive_periods": sorted({candidates[index].primitive_period for index in winners}),
                "best_qualifying_primitive_length4_score": float(np.min(current[valid])),
                "best_nonqualifying_score": float(np.min(current[~valid])),
                "qualifying_advantage_margin": float(np.min(current[~valid]) - np.min(current[valid])),
                "score_vector_sha256": sha256_bytes(np.asarray(current, dtype="<f8").tobytes(order="C")),
            }
            for key, item in checks.items():
                close_enough(row[key], item, f"{path}.scenario_rows[{scenario_index}].engines.{engine}.{key}")
            if len(winners) == 1:
                candidate = candidates[winners[0]]
                if candidate.length == 4 and candidate.primitive_period == 4 and ranked["top_two_margin"] > float(spec["selection_rule"]["scientific_margin_delta"]):
                    counts[engine][candidate.cycle_id] += 1
    return {engine: dict(counts[engine]) for engine in ENGINES}


def verify_controls(
    summary: dict[str, Any],
    main: dict[str, np.ndarray],
    controls: dict[str, np.ndarray],
    candidates: Sequence[Candidate],
    spec: dict[str, Any],
) -> bool:
    reported = summary["controls"]
    expected_keys = {
        "axis6_sign_scramble",
        "commuting_leg_substitution",
        "operator_identity_erasure",
        "operator_label_permutation",
        "loop_role_swap",
        "fixed_per_beat_exposure",
        "candidate_enumeration_shuffle",
        "native_metadata_erasure",
        "gating_control_ids",
        "all_gating_controls_pass",
    }
    exact_keys(reported, expected_keys, "summary.controls")
    signals: dict[str, dict[str, Any]] = {}
    required = int(spec["controls"]["anchor_scenarios"]["required_frequency_count"])
    for kind in (
        "axis6_sign_scramble",
        "commuting_leg_substitution",
        "operator_identity_erasure",
        "operator_label_permutation",
        "loop_role_swap",
        "fixed_per_beat_exposure",
    ):
        counts = _control_counts(
            controls[kind], candidates, spec, reported[kind]["scenario_rows"], f"summary.controls.{kind}"
        )
        signals[kind] = shared_signal(counts, required)
        close_enough(reported[kind]["signal"], signals[kind], f"summary.controls.{kind}.signal")

    expected_simple = {
        "axis6_sign_scramble": not signals["axis6_sign_scramble"]["pass"],
        "loop_role_swap": not signals["loop_role_swap"]["pass"],
    }
    for kind, expected in expected_simple.items():
        if reported[kind]["pass"] is not expected:
            fail(f"summary.controls.{kind}.pass", "does not recompute from the raw control signal")

    zero_tolerance = float(spec["physical_preconditions"]["commutator_zero_tolerance"])
    commuting_expected = finite_number(
        reported["commuting_leg_substitution"]["maximum_affine_commutator_norm"],
        "summary.controls.commuting_leg_substitution.maximum_affine_commutator_norm",
    ) <= zero_tolerance
    if reported["commuting_leg_substitution"]["physical_gate_pass"] is not (not commuting_expected):
        fail("summary.controls.commuting_leg_substitution.physical_gate_pass", "has wrong polarity")
    if reported["commuting_leg_substitution"]["pass"] is not commuting_expected:
        fail("summary.controls.commuting_leg_substitution.pass", "does not recompute from the threshold")

    lengths = np.asarray([candidate.length for candidate in candidates])
    spread = max(
        float(np.max(values) - np.min(values))
        for scenario in controls["operator_identity_erasure"]
        for values_by_engine in scenario
        for length in spec["candidate_space"]["lengths"]
        for values in [values_by_engine[lengths == int(length)]]
    )
    close_enough(
        reported["operator_identity_erasure"]["maximum_within_length_score_spread"],
        spread,
        "summary.controls.operator_identity_erasure.maximum_within_length_score_spread",
    )
    identity_expected = spread <= zero_tolerance and not signals["operator_identity_erasure"]["pass"]
    if reported["operator_identity_erasure"]["pass"] is not identity_expected:
        fail("summary.controls.operator_identity_erasure.pass", "does not recompute from raw spread and signal")

    lookup = {(candidate.length, candidate.word): candidate.index for candidate in candidates}
    permutation = spec["controls"]["operator_label_permutation"]["index_permutation"]
    mapped = [
        lookup[(candidate.length, canonical_rotation(tuple(permutation[item] for item in candidate.word)))]
        for candidate in candidates
    ]
    if reported["operator_label_permutation"]["candidate_index_map"] != mapped:
        fail("summary.controls.operator_label_permutation.candidate_index_map", "does not independently map the catalog")
    anchor_indices = [
        index
        for index, scenario in enumerate(expected_scenarios(spec))
        if scenario["perturbation_id"] == "baseline"
        and scenario["radius"] == float(spec["controls"]["anchor_scenarios"]["radius"])
    ]
    expected_permuted = main["combined_score"][anchor_indices][:, :, mapped]
    permutation_error = float(np.max(np.abs(controls["operator_label_permutation"] - expected_permuted)))
    close_enough(
        reported["operator_label_permutation"]["maximum_score_equivariance_error"],
        permutation_error,
        "summary.controls.operator_label_permutation.maximum_score_equivariance_error",
    )
    permutation_expected = permutation_error <= zero_tolerance
    if reported["operator_label_permutation"]["pass"] is not permutation_expected:
        fail("summary.controls.operator_label_permutation.pass", "does not recompute from raw equivariance")

    main_anchor_winners = [
        [rank(main["combined_score"][index, engine], spec)["winner_indices"] for engine in range(2)]
        for index in anchor_indices
    ]
    fixed_winners = [
        [rank(controls["fixed_per_beat_exposure"][scenario, engine], spec)["winner_indices"] for engine in range(2)]
        for scenario in range(required)
    ]
    if reported["fixed_per_beat_exposure"]["gating"] is not False:
        fail("summary.controls.fixed_per_beat_exposure.gating", "sensitivity control must remain non-gating")
    if reported["fixed_per_beat_exposure"]["anchor_winners_changed"] is not (main_anchor_winners != fixed_winners):
        fail("summary.controls.fixed_per_beat_exposure.anchor_winners_changed", "does not recompute")

    expected_shuffle_rows = []
    combined = main["combined_score"]
    for seed in spec["controls"]["candidate_enumeration_shuffle"]["seeds"]:
        permutation_indices = np.random.default_rng(int(seed)).permutation(len(candidates))
        stable = True
        maximum_best = 0.0
        maximum_margin = 0.0
        for scenario in range(combined.shape[0]):
            for engine in range(combined.shape[1]):
                reference = rank(combined[scenario, engine], spec)
                shuffled = rank(combined[scenario, engine, permutation_indices], spec)
                mapped_winners = sorted(int(permutation_indices[index]) for index in shuffled["winner_indices"])
                stable = stable and mapped_winners == sorted(reference["winner_indices"])
                maximum_best = max(maximum_best, abs(shuffled["best_score"] - reference["best_score"]))
                maximum_margin = max(maximum_margin, abs(shuffled["top_two_margin"] - reference["top_two_margin"]))
        expected_shuffle_rows.append(
            {
                "seed": int(seed),
                "winner_sets_stable": stable,
                "maximum_best_score_error": maximum_best,
                "maximum_margin_error": maximum_margin,
            }
        )
    close_enough(
        reported["candidate_enumeration_shuffle"]["rows"],
        expected_shuffle_rows,
        "summary.controls.candidate_enumeration_shuffle.rows",
    )
    shuffle_pass = all(
        row["winner_sets_stable"]
        and row["maximum_best_score_error"] <= 1.0e-15
        and row["maximum_margin_error"] <= 1.0e-15
        for row in expected_shuffle_rows
    )
    if reported["candidate_enumeration_shuffle"]["pass"] is not shuffle_pass:
        fail("summary.controls.candidate_enumeration_shuffle.pass", "does not recompute")

    score_hash = sha256_bytes(np.asarray(combined, dtype="<f8").tobytes(order="C"))
    native = reported["native_metadata_erasure"]
    expected_native = {
        "score_function_accepts_native_metadata": False,
        "score_hash_before": score_hash,
        "score_hash_after": score_hash,
        "pass": True,
    }
    close_enough(native, expected_native, "summary.controls.native_metadata_erasure")
    gating = [
        "axis6_sign_scramble",
        "commuting_leg_substitution",
        "operator_label_permutation",
        "operator_identity_erasure",
        "candidate_enumeration_shuffle",
        "loop_role_swap",
        "native_metadata_erasure",
    ]
    if reported["gating_control_ids"] != gating:
        fail("summary.controls.gating_control_ids", "frozen gating-control set or order changed")
    recomputed = all(strict_bool(reported[key]["pass"], f"summary.controls.{key}.pass") for key in gating)
    if reported["all_gating_controls_pass"] is not recomputed:
        fail("summary.controls.all_gating_controls_pass", "does not recompute from every gating control")
    if summary["gating_controls_pass"] is not recomputed:
        fail("summary.gating_controls_pass", "does not cross-bind the controls summary")
    return recomputed


def homogeneous(matrix: np.ndarray, offset: np.ndarray) -> np.ndarray:
    value = np.eye(4, dtype=np.float64)
    value[:3, :3] = matrix
    value[:3, 3] = offset
    return value


def affine_choi(matrix: np.ndarray, offset: np.ndarray) -> np.ndarray:
    pauli = np.asarray(
        [
            [[0.0, 1.0], [1.0, 0.0]],
            [[0.0, -1.0j], [1.0j, 0.0]],
            [[1.0, 0.0], [0.0, -1.0]],
        ],
        dtype=np.complex128,
    )
    identity = np.eye(2, dtype=np.complex128)

    def apply(value: np.ndarray) -> np.ndarray:
        trace = np.trace(value)
        coordinates = np.asarray([np.trace(value @ sigma) for sigma in pauli], dtype=np.complex128)
        moved = matrix @ coordinates + offset * trace
        return 0.5 * (trace * identity + sum(moved[index] * pauli[index] for index in range(3)))

    choi = np.zeros((4, 4), dtype=np.complex128)
    for row in range(2):
        for column in range(2):
            unit = np.zeros((2, 2), dtype=np.complex128)
            unit[row, column] = 1.0
            choi[row * 2 : (row + 1) * 2, column * 2 : (column + 1) * 2] = apply(unit)
    return 0.5 * (choi + choi.conj().T)


def density(vector: np.ndarray) -> np.ndarray:
    x, y, z = vector
    return 0.5 * np.asarray([[1.0 + z, x - 1.0j * y], [x + 1.0j * y, 1.0 - z]], dtype=np.complex128)


def spectral_relative_entropy(vector: np.ndarray, reference: np.ndarray) -> float:
    rho = density(vector)
    sigma = density(reference)
    rho_values, rho_vectors = np.linalg.eigh(rho)
    sigma_values, sigma_vectors = np.linalg.eigh(sigma)
    rho_log = (rho_vectors * np.log(np.clip(rho_values.real, 1.0e-12, 1.0))) @ rho_vectors.conj().T
    sigma_log = (sigma_vectors * np.log(np.clip(sigma_values.real, 1.0e-12, 1.0))) @ sigma_vectors.conj().T
    return max(float(np.trace(rho @ (rho_log - sigma_log)).real), 0.0)


def von_neumann_entropy(vector: np.ndarray) -> float:
    radius = min(float(np.linalg.norm(vector)), 1.0 - 1.0e-12)
    values = np.asarray(((1.0 + radius) / 2.0, (1.0 - radius) / 2.0))
    return float(-np.sum(values * np.log(np.clip(values, 1.0e-12, 1.0))))


def anchor_probes(spec: dict[str, Any]) -> np.ndarray:
    seed = int(spec["controls"]["anchor_scenarios"]["seeds"][0])
    count = int(spec["scenario_grid"]["base_probe_count"])
    values = jax.random.normal(jax.random.PRNGKey(seed), (count, 3), dtype=jnp.float64)
    directions = values / jnp.linalg.vector_norm(values, axis=1, keepdims=True)
    base = directions * float(spec["controls"]["anchor_scenarios"]["radius"])
    return np.asarray(jax.device_get(jnp.concatenate((base, -base), axis=0)), dtype=np.float64)


def signed_affines(
    terrain_matrices: np.ndarray,
    terrain_offsets: np.ndarray,
    operator_matrices: np.ndarray,
    operator_offsets: np.ndarray,
    schedule: Sequence[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray]:
    matrices = np.empty((16, 4, 3, 3), dtype=np.float64)
    offsets = np.empty((16, 4, 3), dtype=np.float64)
    for slot, row in enumerate(schedule):
        terrain = TERRAIN_INDEX[row["terrain"]]
        tm, tb = terrain_matrices[terrain], terrain_offsets[terrain]
        for operator in range(4):
            om, ob = operator_matrices[operator], operator_offsets[operator]
            if row["axis6_sign"] == "up":
                matrices[slot, operator] = tm @ om
                offsets[slot, operator] = tm @ ob + tb
            else:
                matrices[slot, operator] = om @ tm
                offsets[slot, operator] = om @ tb + ob
    return matrices, offsets


def verify_physical(summary: dict[str, Any], schedule: list[dict[str, Any]], spec: dict[str, Any]) -> bool:
    physical = exact_keys(summary["physical_preconditions"], {"pass", "perturbations"}, "summary.physical_preconditions")
    rows = physical["perturbations"]
    if not isinstance(rows, list) or len(rows) != len(spec["scenario_grid"]["perturbations"]):
        fail("summary.physical_preconditions.perturbations", "must cover every frozen perturbation")
    probes = anchor_probes(spec)
    thresholds = spec["physical_preconditions"]
    reference_epsilon = float(spec["physical_carrier"]["relative_entropy_reference_epsilon"])
    expected_perturbations = [item["id"] for item in spec["scenario_grid"]["perturbations"]]
    pass_values: list[bool] = []
    for row_index, row in enumerate(rows):
        path = f"summary.physical_preconditions.perturbations[{row_index}]"
        exact_keys(row, {"perturbation_id", "checks", "pass", "measured", "carrier", "commutator_rows", "entropy_movement_rows"}, path)
        if row["perturbation_id"] != expected_perturbations[row_index]:
            fail(f"{path}.perturbation_id", "perturbation order/id mismatch")
        carrier = exact_keys(
            row["carrier"],
            {"terrain_matrices", "terrain_offsets", "operator_matrices", "operator_offsets", "fixed_points"},
            f"{path}.carrier",
        )
        terrain_matrices = np.asarray(carrier["terrain_matrices"], dtype=np.float64)
        terrain_offsets = np.asarray(carrier["terrain_offsets"], dtype=np.float64)
        operator_matrices = np.asarray(carrier["operator_matrices"], dtype=np.float64)
        operator_offsets = np.asarray(carrier["operator_offsets"], dtype=np.float64)
        fixed_points = np.asarray(carrier["fixed_points"], dtype=np.float64)
        expected_shapes = ((8, 3, 3), (8, 3), (4, 3, 3), (4, 3), (8, 3))
        arrays = (terrain_matrices, terrain_offsets, operator_matrices, operator_offsets, fixed_points)
        if tuple(array.shape for array in arrays) != expected_shapes or not all(np.all(np.isfinite(array)) for array in arrays):
            fail(f"{path}.carrier", "carrier arrays have wrong shapes or nonfinite values")
        solve_residual = np.max(
            np.abs(np.einsum("nij,nj->ni", np.eye(3)[None, :, :] - terrain_matrices, fixed_points) - terrain_offsets)
        )
        if solve_residual > 2.0e-14:
            fail(f"{path}.carrier.fixed_points", f"linear fixed-point residual too large: {solve_residual}")

        commutator_rows = []
        for slot, source_row in enumerate(schedule):
            terrain = TERRAIN_INDEX[source_row["terrain"]]
            th = homogeneous(terrain_matrices[terrain], terrain_offsets[terrain])
            for operator, operator_name in enumerate(OPS):
                oh = homogeneous(operator_matrices[operator], operator_offsets[operator])
                commutator_rows.append(
                    {
                        "slot_id": source_row["slot_id"],
                        "operator": operator_name,
                        "affine_commutator_norm": float(np.linalg.norm(th @ oh - oh @ th)),
                    }
                )
        close_enough(row["commutator_rows"], commutator_rows, f"{path}.commutator_rows")
        commutators = np.asarray([item["affine_commutator_norm"] for item in commutator_rows])

        actual_matrices, actual_offsets = signed_affines(
            terrain_matrices, terrain_offsets, operator_matrices, operator_offsets, schedule
        )
        entropy_rows = []
        per_slot = defaultdict(list)
        for slot, source_row in enumerate(schedule):
            if "inductive" not in source_row["loop"]:
                continue
            reference = fixed_points[TERRAIN_INDEX[source_row["terrain"]]] * (1.0 - reference_epsilon)
            for operator, operator_name in enumerate(OPS):
                outputs = probes @ actual_matrices[slot, operator].T + actual_offsets[slot, operator]
                before = [spectral_relative_entropy(vector, reference) for vector in probes]
                after = [spectral_relative_entropy(vector, reference) for vector in outputs]
                mean_delta = float(np.mean(np.abs(np.asarray(after) - np.asarray(before))))
                per_slot[source_row["slot_id"]].append(mean_delta)
                entropy_rows.append(
                    {
                        "slot_id": source_row["slot_id"],
                        "engine": source_row["engine"],
                        "loop": source_row["loop"],
                        "operator": operator_name,
                        "axis6_sign": source_row["axis6_sign"],
                        "d_before": before,
                        "d_after": after,
                        "mean_absolute_delta": mean_delta,
                    }
                )
        close_enough(row["entropy_movement_rows"], entropy_rows, f"{path}.entropy_movement_rows", atol=5.0e-14)
        per_slot_means = {key: float(np.mean(value)) for key, value in per_slot.items()}

        choi_minimum = min(
            float(np.min(np.linalg.eigvalsh(affine_choi(matrix, offset))).real)
            for matrix, offset in itertools.chain(
                zip(operator_matrices, operator_offsets), zip(terrain_matrices, terrain_offsets)
            )
        )
        isometry = [float(np.linalg.norm(matrix.T @ matrix - np.eye(3))) for matrix in operator_matrices]
        direct_entropy = {}
        for operator, name in enumerate(OPS[:2]):
            outputs = probes @ operator_matrices[operator].T + operator_offsets[operator]
            direct_entropy[name] = float(
                np.mean([abs(von_neumann_entropy(output) - von_neumann_entropy(probe)) for probe, output in zip(probes, outputs)])
            )
        maximum_radius = max(
            float(np.max(np.linalg.norm(probes @ actual_matrices[slot, operator].T + actual_offsets[slot, operator], axis=1)))
            for slot in range(16)
            for operator in range(4)
        )
        measured = {
            "minimum_choi_eigenvalue": choi_minimum,
            "maximum_affine_commutator_norm": float(np.max(commutators)),
            "minimum_affine_commutator_norm": float(np.min(commutators)),
            "mean_affine_commutator_norm": float(np.mean(commutators)),
            "noncommuting_fraction": float(np.mean(commutators >= float(thresholds["minimum_affine_commutator_norm"]))),
            "minimum_entropy_side_slot_mean_absolute_delta": min(per_slot_means.values()),
            "maximum_signed_output_bloch_radius": maximum_radius,
            "operator_isometry_residuals": dict(zip(OPS, isometry)),
            "direct_dephasing_entropy_changes": direct_entropy,
        }
        close_enough(row["measured"], measured, f"{path}.measured", atol=8.0e-14)
        checks = {
            "all_affine_values_finite": True,
            "cptp_choi_within_tolerance": choi_minimum >= float(thresholds["minimum_choi_eigenvalue_tolerance"]),
            "main_legs_genuinely_noncommuting": float(np.max(commutators)) >= float(thresholds["minimum_affine_commutator_norm"]),
            "noncommuting_fraction_pass": measured["noncommuting_fraction"] >= float(thresholds["minimum_noncommuting_slot_operator_fraction"]),
            "every_entropy_side_slot_moves_relative_entropy": measured["minimum_entropy_side_slot_mean_absolute_delta"] >= float(thresholds["minimum_entropy_side_mean_absolute_relative_entropy_movement"]),
            "dephasing_operators_are_nonunitary": min(isometry[:2]) >= float(thresholds["minimum_dephasing_isometry_residual"]),
            "dephasing_operators_change_state_entropy": min(direct_entropy.values()) >= float(thresholds["minimum_dephasing_direct_entropy_change"]),
            "signed_outputs_stay_in_bloch_ball": maximum_radius <= float(thresholds["maximum_bloch_radius_tolerance"]),
        }
        close_enough(row["checks"], checks, f"{path}.checks")
        row_pass = all(checks.values())
        if row["pass"] is not row_pass:
            fail(f"{path}.pass", "does not recompute from independent physical checks")
        pass_values.append(row_pass)
    recomputed = all(pass_values)
    if physical["pass"] is not recomputed or summary["physical_preconditions_pass"] is not recomputed:
        fail("summary.physical_preconditions_pass", "does not recompute across all perturbations")
    return recomputed


def verify_source_and_hash_locks(packet: Packet) -> None:
    exact_keys(packet.prereg, PREREG_KEYS, "prereg")
    if packet.prereg["schema"] != f"codex_ratchet.{SIM_ID}.preregistration.v1":
        fail("prereg.schema", "schema mismatch")
    if packet.prereg["sim_id"] != SIM_ID:
        fail("prereg.sim_id", "sim_id mismatch")
    spec_hash = sha256(SPEC_PATH)
    if packet.prereg["spec_sha256"] != spec_hash:
        fail("prereg.spec_sha256", "frozen spec hash mismatch")
    detached = SPEC_HASH_PATH.read_text(encoding="utf-8").split()
    if detached != [spec_hash, "spec.json"]:
        fail("spec.sha256", "detached frozen hash file is malformed or stale")
    locks = {
        "object_card_sha256": OBJECT_CARD_PATH,
        "source_schedule_sha256": SCHEDULE_PATH,
        "semantic_correction_sha256": CORRECTION_PATH,
    }
    for key, path in locks.items():
        if packet.prereg[key] != sha256(path):
            fail(f"prereg.{key}", f"frozen source hash mismatch for {relative(path)}")
    if packet.prereg["files_present_at_freeze"] != ["spec.json", "wizard_v4_3_object_card.json"]:
        fail("prereg.files_present_at_freeze", "freeze surface changed")
    if packet.prereg["observed_result_files_present_at_freeze"] != []:
        fail("prereg.observed_result_files_present_at_freeze", "must remain empty")
    if packet.prereg["observed_results_run_before_freeze"] is not False:
        fail("prereg.observed_results_run_before_freeze", "must be strictly false")

    expected_sources = {
        relative(SPEC_PATH): sha256(SPEC_PATH),
        relative(SPEC_HASH_PATH): sha256(SPEC_HASH_PATH),
        relative(PREREG_PATH): sha256(PREREG_PATH),
        relative(PRODUCER_PATH): sha256(PRODUCER_PATH),
        relative(SCHEDULE_PATH): sha256(SCHEDULE_PATH),
        relative(CORRECTION_PATH): sha256(CORRECTION_PATH),
    }
    close_enough(packet.summary["source_hashes"], expected_sources, "summary.source_hashes")
    close_enough(packet.rerun_summary["source_hashes"], expected_sources, "rerun_summary.source_hashes")


def verify_source_schedule(summary: dict[str, Any], schedule: list[dict[str, Any]]) -> None:
    if not isinstance(schedule, list) or len(schedule) != 16:
        fail("source_schedule", "must contain exactly 16 rows")
    if len({row.get("slot_id") for row in schedule}) != 16:
        fail("source_schedule", "slot IDs must be unique")
    if Counter(row.get("engine") for row in schedule) != Counter({ENGINES[0]: 8, ENGINES[1]: 8}):
        fail("source_schedule", "must contain eight slots per engine")
    expected = [
        {
            "slot_id": row["slot_id"],
            "engine": row["engine"],
            "loop": row["loop"],
            "step": row["step"],
            "terrain": row["terrain"],
            "axis6_sign": row["axis6_sign"],
            "canonical_operator_metadata_only": row["canonical_operator"],
            "beat_sign_template_Lmax8": [row["axis6_sign"]] * 8,
        }
        for row in schedule
    ]
    close_enough(summary["source_slot_rows"], expected, "summary.source_slot_rows")


def verify_ceilings_and_verdict(
    summary: dict[str, Any], spec: dict[str, Any], prereg: dict[str, Any], signal: dict[str, Any], physical_pass: bool, controls_pass: bool
) -> None:
    for name, value in (("spec", spec), ("prereg", prereg), ("summary", summary)):
        if value["classification"] != "scratch_diagnostic":
            fail(f"{name}.classification", "must remain scratch_diagnostic")
        for key in ("promotion_allowed", "formal_admission_allowed", "stage_movement_allowed"):
            if strict_bool(value[key], f"{name}.{key}") is not False:
                fail(f"{name}.{key}", "blocked ceiling must remain false")
    if summary["claim_ceiling"] != spec["claim_ceiling"]:
        fail("summary.claim_ceiling", "does not match the frozen claim ceiling")
    if summary["blocked_consumers"] != spec["blocked_consumers"]:
        fail("summary.blocked_consumers", "blocked consumers were removed, reordered, or changed")
    if summary["artifact_validity_claimed_by_producer"] is not False:
        fail("summary.artifact_validity_claimed_by_producer", "producer may not self-validate")
    if summary["artifact_validity_requires_independent_validator"] is not True:
        fail("summary.artifact_validity_requires_independent_validator", "independent gate must remain required")
    scientific_pass = bool(signal["pass"] and physical_pass and controls_pass)
    if summary["scientific_pass"] is not scientific_pass:
        fail("summary.scientific_pass", "does not recompute from signal, physical, and control gates")
    verdict = (
        spec["scientific_pass_rule"]["green_ceiling"]
        if scientific_pass
        else spec["scientific_pass_rule"]["red_verdict"]
    )
    if summary["scientific_verdict"] != verdict:
        fail("summary.scientific_verdict", "does not recompute from the frozen scientific pass rule")
    accepted = (
        "four_selected_under_declared_source_operator_family_only"
        if scientific_pass
        else "free_length_search_completed_scientific_RED"
    )
    if summary["accepted_scientific_ceiling"] != accepted:
        fail("summary.accepted_scientific_ceiling", "does not match the recomputed verdict")


def verify_execution_checks(summary: dict[str, Any], candidates: Sequence[Candidate], spec: dict[str, Any]) -> None:
    expected = {
        "spec_hash_matches_preregistration": True,
        "candidate_space_checks_pass": all(summary["candidate_space"]["checks"].values()),
        "scenario_count_matches_spec": len(summary["scenario_manifest"]) == spec["scenario_grid"]["scenario_count_per_engine"],
        "engine_count_matches_spec": len(ENGINES) == spec["scenario_grid"]["engine_count"],
        "candidate_count_matches_spec": len(candidates) == spec["candidate_space"]["oriented_necklace_count_total"],
        "all_scores_finite": True,
        "all_source_slots_present": len(summary["source_slot_rows"]) == 16 and len({row["slot_id"] for row in summary["source_slot_rows"]}) == 16,
        "all_sign_templates_constant": all(len(set(row["beat_sign_template_Lmax8"])) == 1 for row in summary["source_slot_rows"]),
        "native_metadata_off_score_path": True,
        "no_learned_lane": spec["controls"]["learned_lane_used"] is False,
    }
    close_enough(summary["execution_checks"], expected, "summary.execution_checks")
    if summary["execution_complete"] is not all(expected.values()):
        fail("summary.execution_complete", "does not recompute from execution checks")


def load_packet() -> Packet:
    values = {
        "spec": strict_json_load(SPEC_PATH),
        "prereg": strict_json_load(PREREG_PATH),
        "schedule": strict_json_load(SCHEDULE_PATH),
        "catalog": strict_json_load(CATALOG_PATH),
        "summary": strict_json_load(SUMMARY_PATH),
        "raw": strict_json_load(RAW_PATH),
        "rerun_summary": strict_json_load(RERUN_SUMMARY_PATH),
        "rerun_raw": strict_json_load(RERUN_RAW_PATH),
    }
    for key in ("spec", "prereg", "catalog", "summary", "raw", "rerun_summary", "rerun_raw"):
        if not isinstance(values[key], dict):
            fail(key, "top-level JSON must be an object")
    return Packet(**values)


def validate_packet(packet: Packet | None = None) -> ValidationContext:
    packet = packet or load_packet()
    for name, value in vars(packet).items():
        verify_boolean_types(value, name)
    verify_source_and_hash_locks(packet)
    verify_source_schedule(packet.summary, packet.schedule)
    candidates = verify_catalog(packet.catalog, packet.spec)
    catalog_hash = sha256(CATALOG_PATH)
    main, controls = verify_raw(packet.raw, packet.spec, catalog_hash)
    verify_score_semantics(main, candidates, packet.spec)
    if SUMMARY_PATH.read_bytes() != RERUN_SUMMARY_PATH.read_bytes():
        fail("determinism.summary", "primary and rerun summaries are not byte-identical")
    if RAW_PATH.read_bytes() != RERUN_RAW_PATH.read_bytes():
        fail("determinism.raw", "primary and rerun raw-score receipts are not byte-identical")
    if packet.rerun_summary != packet.summary or packet.rerun_raw != packet.raw:
        fail("determinism", "parsed rerun receipts differ from primary receipts")
    if packet.summary["candidate_catalog_sha256"] != catalog_hash:
        fail("summary.candidate_catalog_sha256", "catalog file hash mismatch")
    if packet.summary["raw_scores_sha256"] != sha256(RAW_PATH):
        fail("summary.raw_scores_sha256", "raw file hash mismatch")
    signal = verify_main_summary(packet.summary, main, candidates, packet.spec)
    physical_pass = verify_physical(packet.summary, packet.schedule, packet.spec)
    controls_pass = verify_controls(packet.summary, main, controls, candidates, packet.spec)
    verify_execution_checks(packet.summary, candidates, packet.spec)
    verify_ceilings_and_verdict(
        packet.summary, packet.spec, packet.prereg, signal, physical_pass, controls_pass
    )
    return ValidationContext(packet, candidates, main, controls)


def receipt(context: ValidationContext) -> dict[str, Any]:
    summary = context.packet.summary
    return {
        "schema": f"codex_ratchet.{SIM_ID}.independent_validation.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "artifact_validation_all_pass": True,
        "scientific_pass": summary["scientific_pass"],
        "scientific_verdict": summary["scientific_verdict"],
        "accepted_scientific_ceiling": summary["accepted_scientific_ceiling"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "candidate_count": len(context.candidates),
        "scenario_count_per_engine": context.main_arrays["combined_score"].shape[0],
        "engine_count": context.main_arrays["combined_score"].shape[1],
        "checks": {
            "frozen_hashes_and_sources": True,
            "closed_schemas_and_strict_types": True,
            "candidate_combinatorics_and_catalog": True,
            "raw_base64_shapes_and_hashes": True,
            "summary_raw_catalog_cross_binding": True,
            "physical_preconditions_recomputed": True,
            "gating_controls_recomputed": True,
            "scientific_verdict_recomputed": True,
            "deterministic_rerun_byte_identity": True,
            "blocked_claim_ceiling_preserved": True,
        },
        "source_hashes": {
            relative(Path(__file__)): sha256(Path(__file__)),
            relative(SPEC_PATH): sha256(SPEC_PATH),
            relative(PRODUCER_PATH): sha256(PRODUCER_PATH),
            relative(CATALOG_PATH): sha256(CATALOG_PATH),
            relative(SUMMARY_PATH): sha256(SUMMARY_PATH),
            relative(RAW_PATH): sha256(RAW_PATH),
        },
        "blocked_consumers": context.packet.spec["blocked_consumers"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit the validation receipt on one line",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = receipt(validate_packet())
    except ValidationError as exc:
        print(
            json.dumps(
                {
                    "schema": f"codex_ratchet.{SIM_ID}.independent_validation.v1",
                    "sim_id": SIM_ID,
                    "artifact_validation_all_pass": False,
                    "error": str(exc),
                },
                indent=None if args.compact else 2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
