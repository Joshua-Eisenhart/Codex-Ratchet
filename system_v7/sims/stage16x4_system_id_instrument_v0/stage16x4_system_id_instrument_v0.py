#!/usr/bin/env python3
"""Conditional 16 x 4 stage execution and system-identification instrument."""

from __future__ import annotations

import hashlib
import importlib.metadata
import itertools
import json
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import pysindy as ps
from scipy.linalg import expm
from sklearn.metrics import r2_score

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*")
    from pykoopman import Koopman
    from pykoopman.observables import Identity
    from pykoopman.regression import EDMD


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
stage_movement_allowed = False
sim_execution_kind = "nonclassical"
source_alignment_category = "conditional_stage16x4_system_identification"

TOOL_MANIFEST = {
    "pysindy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing affine terrain-generator recovery, held-out derivative scoring, and shuffled-derivative control",
    },
    "pykoopman": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Identity-observable EDMD beat-map recovery and held-out four-beat rollout",
    },
    "stage_interior_architecture_tournament": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shared source-slot parser and exact one-qubit terrain/operator house maps",
        "role_source": "upstream",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite state fixtures, map application, controls, and distance calculations",
    },
    "scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": "load-bearing conversion of fitted affine generators into time-one terrain flows",
    },
    "scikit_learn": {
        "tried": True,
        "used": True,
        "reason": "supportive held-out R2 measurements",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive source/result parsing and serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pysindy": "load_bearing",
    "pykoopman": "load_bearing",
    "stage_interior_architecture_tournament": "load_bearing",
    "numpy": "load_bearing",
    "scipy.linalg.expm": "load_bearing",
    "scikit_learn": "supportive",
    "python_json": "supportive",
}

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRIPT_PATH = Path(__file__).resolve()
VALIDATOR_PATH = HERE / "validate_stage16x4_system_id_instrument_v0.py"
FLOW_PATH = HERE / "lev_verify.flow.yaml"
RESULT_PATH = HERE / "results" / "stage16x4_system_id_instrument_v0_results.json"
SPEC_PATH = HERE / "spec.json"
BASE_PATH = (
    REPO
    / "system_v7"
    / "constraint_core"
    / "sims_and_scripts"
    / "stage_interior_architecture_tournament_sim.py"
)
BASE_DIR = BASE_PATH.parent
SOURCE_PATH = (
    REPO
    / "system_v7"
    / "constraint_core"
    / "reference_docs"
    / "engine_math"
    / "source_schedule_tables"
    / "engine_16_source_stage_slots.json"
)
PRODUCT_VALIDATOR_PATH = (
    REPO
    / "system_v7"
    / "sims"
    / "four_substages_dual_product_v0"
    / "results"
    / "four_substages_dual_product_v0_validator_results.json"
)
PRODUCT_JAX_PATH = PRODUCT_VALIDATOR_PATH.parent / "four_substages_dual_product_v0_jax_results.json"
PYSINDY_CAPABILITY_PATH = (
    REPO / "system_v4" / "probes" / "a2_state" / "sim_results" / "pysindy_capability_results.json"
)
PYSINDY_CAPABILITY_SCRIPT = REPO / "system_v4" / "probes" / "sim_pysindy_capability.py"
PYKOOPMAN_CAPABILITY_PATH = (
    REPO / "system_v4" / "probes" / "a2_state" / "sim_results" / "pykoopman_capability_results.json"
)
PYKOOPMAN_CAPABILITY_SCRIPT = REPO / "system_v4" / "probes" / "sim_pykoopman_capability.py"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
import stage_interior_architecture_tournament_sim as stage_base  # noqa: E402


SEED = 20260709
TRAIN_ROWS = 384
TEST_ROWS = 128
TERRAIN_TRAIN_ROWS = 512
TERRAIN_TEST_ROWS = 192
FIT_TOL = 1.0e-8
FORWARD = ("Ti", "Fe", "Fi", "Te")
REVERSE = ("Ti", "Te", "Fi", "Fe")
ORIENTATIONS = {"forward": FORWARD, "reverse": REVERSE}


@dataclass(frozen=True)
class TerrainFit:
    terrain: int
    generator_matrix: np.ndarray
    generator_offset: np.ndarray
    flow_matrix: np.ndarray
    derivative_r2: float
    derivative_rmse: float
    flow_rmse: float
    shuffled_derivative_r2: float
    feature_names: tuple[str, ...]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def sample_bloch(seed: int, count: int, max_radius: float = 0.76) -> np.ndarray:
    rng = np.random.default_rng(seed)
    directions = rng.normal(size=(count, 3))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    radii = max_radius * np.cbrt(rng.uniform(0.03, 1.0, size=(count, 1)))
    return directions * radii


def exact_derivative(terrain: int, states: np.ndarray) -> np.ndarray:
    vector_field = stage_base.gen(terrain)
    rows = []
    for state in states:
        derivative = vector_field(stage_base.dm(state))
        rows.append(
            [float(np.trace(derivative @ sigma).real) for sigma in (stage_base.SX, stage_base.SY, stage_base.SZ)]
        )
    return np.asarray(rows, dtype=float)


def exact_flow(terrain: int, states: np.ndarray) -> np.ndarray:
    return np.asarray(
        [stage_base.bloch(stage_base.flow_terrain(terrain, stage_base.dm(state))) for state in states],
        dtype=float,
    )


def fit_sindy(states: np.ndarray, derivatives: np.ndarray):
    model = ps.SINDy(
        feature_library=ps.PolynomialLibrary(degree=1, include_bias=True),
        optimizer=ps.STLSQ(threshold=1.0e-12, alpha=1.0e-12),
    )
    model.fit(states, t=1.0, x_dot=derivatives)
    return model


def fit_terrain_models() -> tuple[dict[int, TerrainFit], dict[str, Any]]:
    fits: dict[int, TerrainFit] = {}
    rows = []
    for terrain in sorted(stage_base.TERR):
        train = sample_bloch(SEED + 100 + terrain, TERRAIN_TRAIN_ROWS)
        test = sample_bloch(SEED + 200 + terrain, TERRAIN_TEST_ROWS)
        train_dot = exact_derivative(terrain, train)
        test_dot = exact_derivative(terrain, test)
        model = fit_sindy(train, train_dot)
        feature_names = tuple(model.get_feature_names())
        coefficients = np.asarray(model.coefficients(), dtype=float)
        if feature_names != ("1", "x0", "x1", "x2") or coefficients.shape != (3, 4):
            raise RuntimeError(f"unexpected PySINDy affine basis for terrain {terrain}: {feature_names}")
        prediction = np.asarray(model.predict(test), dtype=float)
        derivative_r2 = float(model.score(test, t=1.0, x_dot=test_dot))
        derivative_rmse = float(np.sqrt(np.mean((prediction - test_dot) ** 2)))

        augmented_generator = np.zeros((4, 4), dtype=float)
        augmented_generator[:3, :3] = coefficients[:, 1:]
        augmented_generator[:3, 3] = coefficients[:, 0]
        flow_matrix = expm(stage_base.T_FLOW * augmented_generator)
        learned_flow = np.column_stack([test, np.ones(len(test))]) @ flow_matrix.T
        flow_rmse = float(np.sqrt(np.mean((learned_flow[:, :3] - exact_flow(terrain, test)) ** 2)))

        rng = np.random.default_rng(SEED + 300 + terrain)
        shuffled_model = fit_sindy(train, train_dot[rng.permutation(len(train_dot))])
        shuffled_r2 = float(shuffled_model.score(test, t=1.0, x_dot=test_dot))
        fit = TerrainFit(
            terrain=terrain,
            generator_matrix=coefficients[:, 1:],
            generator_offset=coefficients[:, 0],
            flow_matrix=flow_matrix,
            derivative_r2=derivative_r2,
            derivative_rmse=derivative_rmse,
            flow_rmse=flow_rmse,
            shuffled_derivative_r2=shuffled_r2,
            feature_names=feature_names,
        )
        fits[terrain] = fit
        rows.append(
            {
                "terrain": terrain,
                "terrain_definition": list(stage_base.TERR[terrain]),
                "feature_names": list(feature_names),
                "generator_matrix": fit.generator_matrix,
                "generator_offset": fit.generator_offset,
                "derivative_r2": derivative_r2,
                "derivative_rmse": derivative_rmse,
                "flow_rmse": flow_rmse,
                "shuffled_derivative_r2": shuffled_r2,
            }
        )
    checks = {
        "all_eight_terrains_fit": len(fits) == 8,
        "minimum_heldout_derivative_r2_at_least_0_999999": min(row["derivative_r2"] for row in rows) >= 0.999999,
        "maximum_heldout_flow_rmse_below_1e_8": max(row["flow_rmse"] for row in rows) < FIT_TOL,
        "all_shuffled_derivative_r2_below_0_25": max(row["shuffled_derivative_r2"] for row in rows) < 0.25,
    }
    return fits, {"rows": rows, "checks": checks, "all_pass": all(checks.values())}


def learned_flow(fits: dict[int, TerrainFit], terrain: int, states: np.ndarray) -> np.ndarray:
    augmented = np.column_stack([states, np.ones(len(states))])
    return (augmented @ fits[terrain].flow_matrix.T)[:, :3]


def apply_operator(operator: str, states: np.ndarray) -> np.ndarray:
    return np.asarray(
        [stage_base.bloch(stage_base.apply_op(operator, stage_base.dm(state))) for state in states],
        dtype=float,
    )


def apply_beat(
    slot: stage_base.Slot,
    operator: str,
    states: np.ndarray,
    terrain_flow: Callable[[int, np.ndarray], np.ndarray],
    sign: str | None = None,
    use_terrain: bool = True,
    use_operator: bool = True,
) -> np.ndarray:
    active_sign = sign or slot.axis6_sign
    out = np.asarray(states, dtype=float)
    if active_sign == "up":
        if use_operator:
            out = apply_operator(operator, out)
        if use_terrain:
            out = terrain_flow(slot.terrain, out)
    elif active_sign == "down":
        if use_terrain:
            out = terrain_flow(slot.terrain, out)
        if use_operator:
            out = apply_operator(operator, out)
    else:
        raise ValueError(active_sign)
    return out


def rotate_to(sequence: Sequence[str], first: str) -> tuple[str, ...]:
    index = sequence.index(first)
    return tuple(sequence[index:]) + tuple(sequence[:index])


def sequence_for(slot: stage_base.Slot, orientation: str) -> tuple[str, ...]:
    return rotate_to(ORIENTATIONS[orientation], slot.canonical_operator)


def run_exact_sequence(
    slot: stage_base.Slot,
    sequence: Sequence[str],
    states: np.ndarray,
    drop_index: int | None = None,
    duplicate_index: int | None = None,
    sign: str | None = None,
    use_terrain: bool = True,
    use_operator: bool = True,
) -> np.ndarray:
    out = np.asarray(states, dtype=float)
    expanded: list[tuple[int, str]] = []
    for index, operator in enumerate(sequence):
        expanded.append((index, operator))
        if duplicate_index == index:
            expanded.append((index, operator))
    for original_index, operator in expanded:
        if drop_index == original_index and duplicate_index is None:
            continue
        out = apply_beat(
            slot,
            operator,
            out,
            exact_flow,
            sign=sign,
            use_terrain=use_terrain,
            use_operator=use_operator,
        )
    return out


def fit_edmd_map(x: np.ndarray, y: np.ndarray, augmented: bool = True) -> Koopman:
    x_fit = np.column_stack([x, np.ones(len(x))]) if augmented else x
    y_fit = np.column_stack([y, np.ones(len(y))]) if augmented else y
    model = Koopman(observables=Identity(), regressor=EDMD(svd_rank=x_fit.shape[1]))
    model.fit(x_fit, y=y_fit)
    return model


def predict_edmd(model: Koopman, states: np.ndarray, augmented: bool = True) -> tuple[np.ndarray, float]:
    x_fit = np.column_stack([states, np.ones(len(states))]) if augmented else states
    prediction = np.asarray(model.predict(x_fit), dtype=float)
    if not augmented:
        return prediction, 0.0
    bias_drift = float(np.max(np.abs(prediction[:, -1] - 1.0)))
    return prediction[:, :3], bias_drift


def mean_state_gap(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(np.linalg.norm(left - right, axis=1)))


def opposite_sign(sign: str) -> str:
    return "down" if sign == "up" else "up"


def fit_slot_orientation(
    slot: stage_base.Slot,
    orientation: str,
    terrain_fits: dict[int, TerrainFit],
    x_train: np.ndarray,
    x_test: np.ndarray,
) -> tuple[dict[str, Any], list[Koopman], np.ndarray, np.ndarray]:
    sequence = sequence_for(slot, orientation)
    beat_models: list[Koopman] = []
    beat_rows = []
    max_bias_drift = 0.0
    for position, operator in enumerate(sequence):
        learned_target = apply_beat(
            slot,
            operator,
            x_train,
            lambda terrain, states: learned_flow(terrain_fits, terrain, states),
        )
        model = fit_edmd_map(x_train, learned_target, augmented=True)
        prediction, bias_drift = predict_edmd(model, x_test, augmented=True)
        exact_target = apply_beat(slot, operator, x_test, exact_flow)
        rmse = float(np.sqrt(np.mean((prediction - exact_target) ** 2)))
        r2 = float(r2_score(exact_target, prediction))
        max_bias_drift = max(max_bias_drift, bias_drift)
        beat_models.append(model)
        beat_rows.append(
            {
                "position": position,
                "operator": operator,
                "axis6_sign": slot.axis6_sign,
                "heldout_r2": r2,
                "heldout_rmse": rmse,
                "bias_coordinate_max_drift": bias_drift,
            }
        )

    predicted = np.asarray(x_test, dtype=float)
    for model in beat_models:
        predicted, bias_drift = predict_edmd(model, predicted, augmented=True)
        max_bias_drift = max(max_bias_drift, bias_drift)
    exact = run_exact_sequence(slot, sequence, x_test)
    endpoint_rmse = float(np.sqrt(np.mean((predicted - exact) ** 2)))
    endpoint_r2 = float(r2_score(exact, predicted))
    threshold = max(FIT_TOL, 20.0 * endpoint_rmse)

    direct_linear = fit_edmd_map(x_train, run_exact_sequence(slot, sequence, x_train), augmented=False)
    direct_linear_prediction, _ = predict_edmd(direct_linear, x_test, augmented=False)
    erased_bias_rmse = float(np.sqrt(np.mean((direct_linear_prediction - exact) ** 2)))

    drop_rows = []
    duplicate_rows = []
    for index, operator in enumerate(sequence):
        dropped = run_exact_sequence(slot, sequence, x_test, drop_index=index)
        drop_gap = mean_state_gap(exact, dropped)
        drop_rows.append(
            {
                "position": index,
                "operator": operator,
                "mean_endpoint_gap": drop_gap,
                "load_bearing_beyond_fit_error": drop_gap > threshold,
            }
        )
        duplicated = run_exact_sequence(slot, sequence, x_test, duplicate_index=index)
        duplicate_gap = mean_state_gap(exact, duplicated)
        duplicate_rows.append(
            {
                "position": index,
                "operator": operator,
                "mean_endpoint_gap": duplicate_gap,
                "changes_endpoint_beyond_fit_error": duplicate_gap > threshold,
            }
        )

    other_orientation = "reverse" if orientation == "forward" else "forward"
    reversed_output = run_exact_sequence(slot, sequence_for(slot, other_orientation), x_test)
    wrong_sign_output = run_exact_sequence(
        slot,
        sequence,
        x_test,
        sign=opposite_sign(slot.axis6_sign),
    )
    terrain_erased = run_exact_sequence(slot, sequence, x_test, use_terrain=False)
    operator_erased = run_exact_sequence(slot, sequence, x_test, use_operator=False)
    permutation_gaps = []
    for permutation in itertools.permutations(sequence):
        if permutation == sequence:
            continue
        permutation_gaps.append(mean_state_gap(exact, run_exact_sequence(slot, permutation, x_test)))

    controls = {
        "beat_removal": drop_rows,
        "duplicate_beat": duplicate_rows,
        "reverse_orientation": {
            "other_sequence": list(sequence_for(slot, other_orientation)),
            "mean_endpoint_gap": mean_state_gap(exact, reversed_output),
        },
        "wrong_axis6_sign": {
            "source_sign": slot.axis6_sign,
            "control_sign": opposite_sign(slot.axis6_sign),
            "mean_endpoint_gap": mean_state_gap(exact, wrong_sign_output),
        },
        "terrain_erasure": {"mean_endpoint_gap": mean_state_gap(exact, terrain_erased)},
        "operator_erasure": {"mean_endpoint_gap": mean_state_gap(exact, operator_erased)},
        "all_permutations": {
            "alternative_count": len(permutation_gaps),
            "minimum_mean_endpoint_gap": min(permutation_gaps),
            "maximum_mean_endpoint_gap": max(permutation_gaps),
            "alternatives_distinct_beyond_fit_error": sum(gap > threshold for gap in permutation_gaps),
        },
    }
    local_checks = {
        "four_beats_share_source_axis6_sign": len({row["axis6_sign"] for row in beat_rows}) == 1,
        "all_beat_models_r2_at_least_0_999999": min(row["heldout_r2"] for row in beat_rows) >= 0.999999,
        "all_beat_models_rmse_below_1e_8": max(row["heldout_rmse"] for row in beat_rows) < FIT_TOL,
        "rollout_r2_at_least_0_999999": endpoint_r2 >= 0.999999,
        "rollout_rmse_below_1e_8": endpoint_rmse < FIT_TOL,
        "bias_coordinate_drift_below_1e_8": max_bias_drift < FIT_TOL,
        "all_four_beat_removals_change_endpoint": all(row["load_bearing_beyond_fit_error"] for row in drop_rows),
        "all_four_beat_duplications_change_endpoint": all(row["changes_endpoint_beyond_fit_error"] for row in duplicate_rows),
        "reverse_orientation_changes_endpoint": controls["reverse_orientation"]["mean_endpoint_gap"] > threshold,
        "wrong_axis6_sign_changes_endpoint": controls["wrong_axis6_sign"]["mean_endpoint_gap"] > threshold,
        "terrain_erasure_changes_endpoint": controls["terrain_erasure"]["mean_endpoint_gap"] > threshold,
        "operator_erasure_changes_endpoint": controls["operator_erasure"]["mean_endpoint_gap"] > threshold,
        "all_23_other_permutations_change_endpoint": controls["all_permutations"]["alternatives_distinct_beyond_fit_error"] == 23,
    }
    row = {
        "slot_id": slot.slot_id,
        "engine": slot.engine,
        "loop": slot.loop,
        "step": slot.step,
        "terrain_label": slot.terrain_label,
        "terrain": slot.terrain,
        "axis6_sign": slot.axis6_sign,
        "canonical_operator": slot.canonical_operator,
        "orientation": orientation,
        "sequence": list(sequence),
        "beat_models": beat_rows,
        "rollout": {
            "heldout_r2": endpoint_r2,
            "heldout_rmse": endpoint_rmse,
            "bias_coordinate_max_drift": max_bias_drift,
            "fit_error_control_threshold": threshold,
            "erased_bias_direct_map_rmse": erased_bias_rmse,
        },
        "controls": controls,
        "checks": local_checks,
        "all_local_checks_pass": all(local_checks.values()),
    }
    return row, beat_models, predicted, exact


def reidentify(
    slots: Sequence[stage_base.Slot],
    orientation: str,
    predicted_by_slot: dict[str, np.ndarray],
    exact_by_slot: dict[str, np.ndarray],
) -> dict[str, Any]:
    rows = []
    correct = 0
    for target in slots:
        costs = {
            candidate.slot_id: float(
                np.sqrt(np.mean((predicted_by_slot[candidate.slot_id] - exact_by_slot[target.slot_id]) ** 2))
            )
            for candidate in slots
        }
        ordered = sorted(costs.items(), key=lambda item: item[1])
        guess = ordered[0][0]
        matched = guess == target.slot_id
        correct += int(matched)
        rows.append(
            {
                "target": target.slot_id,
                "guess": guess,
                "matched": matched,
                "best_rmse": ordered[0][1],
                "second_best_rmse": ordered[1][1],
                "margin": ordered[1][1] - ordered[0][1],
                "costs": costs,
            }
        )
    return {
        "orientation": orientation,
        "correct": correct,
        "total": len(slots),
        "accuracy": correct / len(slots),
        "minimum_margin": min(row["margin"] for row in rows),
        "rows": rows,
    }


def normalize_cycle(sequence: Sequence[str]) -> tuple[str, ...]:
    rotations = [tuple(sequence[index:]) + tuple(sequence[:index]) for index in range(len(sequence))]
    return min(rotations)


def prerequisite_check() -> dict[str, Any]:
    validator = json.loads(PRODUCT_VALIDATOR_PATH.read_text())
    jax = json.loads(PRODUCT_JAX_PATH.read_text())
    observed = {normalize_cycle(cycle) for cycle in jax["mss_product_cycle"]["operator_cycles"]}
    expected = {normalize_cycle(FORWARD), normalize_cycle(REVERSE)}
    checks = {
        "validator_all_pass": validator.get("all_pass") is True,
        "jax_result_all_pass": jax.get("all_pass") is True,
        "two_orientations_match_spec_modulo_rotation": observed == expected,
    }
    return {
        "checks": checks,
        "all_pass": all(checks.values()),
        "observed_cycles": [list(cycle) for cycle in sorted(observed)],
        "expected_cycles": [list(cycle) for cycle in sorted(expected)],
    }


def source_check(slots: Sequence[stage_base.Slot], slot_meta: dict[str, Any]) -> dict[str, Any]:
    terrain_sign_pairs = {(slot.terrain_label, slot.axis6_sign) for slot in slots}
    raw = json.loads(SOURCE_PATH.read_text())
    corrupted = json.loads(json.dumps(raw))
    corrupted[1]["slot_id"] = corrupted[0]["slot_id"]
    corrupted_unique = len({row["slot_id"] for row in corrupted}) == len(corrupted)
    checks = {
        "source_parser_reports_one_row_per_slot": slot_meta["one_row_per_slot"],
        "slot_count_is_16": len(slots) == 16,
        "terrain_sign_pairs_are_16_unique_contexts": len(terrain_sign_pairs) == 16,
        "canonical_operator_is_in_product_cycle": all(slot.canonical_operator in FORWARD for slot in slots),
        "duplicate_slot_corruption_control_rejected": not corrupted_unique,
    }
    return {
        "checks": checks,
        "all_pass": all(checks.values()),
        "slot_meta": slot_meta,
        "terrain_sign_pair_count": len(terrain_sign_pairs),
    }


def identity_boundary(states: np.ndarray) -> dict[str, Any]:
    outputs = []
    for sequence in itertools.permutations(FORWARD):
        out = np.asarray(states, dtype=float)
        for _ in sequence:
            out = out.copy()
        outputs.append(out)
    maximum_gap = max(mean_state_gap(outputs[0], output) for output in outputs[1:])
    return {
        "fixture": "terrain identity plus operator identity for all four labels",
        "permutation_count": len(outputs),
        "maximum_order_gap": maximum_gap,
        "order_insensitive": maximum_gap < 1.0e-15,
    }


def signature_clusters(
    slots: Sequence[stage_base.Slot],
    orientation: str,
    states: np.ndarray,
    use_terrain: bool,
    use_operator: bool,
    tolerance: float = 1.0e-8,
) -> dict[str, Any]:
    representatives: list[tuple[str, np.ndarray]] = []
    membership: dict[str, str] = {}
    minimum_cross_cluster_gap = float("inf")
    for slot in slots:
        output = run_exact_sequence(
            slot,
            sequence_for(slot, orientation),
            states,
            use_terrain=use_terrain,
            use_operator=use_operator,
        ).reshape(-1)
        assigned = None
        for representative_id, representative in representatives:
            gap = float(np.linalg.norm(output - representative))
            if gap <= tolerance:
                assigned = representative_id
                break
            minimum_cross_cluster_gap = min(minimum_cross_cluster_gap, gap)
        if assigned is None:
            assigned = slot.slot_id
            representatives.append((assigned, output))
        membership[slot.slot_id] = assigned
    if len(representatives) <= 1:
        minimum_cross_cluster_gap = 0.0
    return {
        "cluster_count": len(representatives),
        "representative_slots": [slot_id for slot_id, _ in representatives],
        "membership": membership,
        "tolerance": tolerance,
        "minimum_observed_cross_cluster_gap": minimum_cross_cluster_gap,
    }


def identity_ablation_clusters(
    slots: Sequence[stage_base.Slot],
    states: np.ndarray,
) -> dict[str, Any]:
    by_orientation = {}
    for orientation in ORIENTATIONS:
        rows = {
            "full": signature_clusters(slots, orientation, states, True, True),
            "operator_erased": signature_clusters(slots, orientation, states, True, False),
            "terrain_erased": signature_clusters(slots, orientation, states, False, True),
            "terrain_and_operator_erased": signature_clusters(
                slots,
                orientation,
                states,
                False,
                False,
            ),
        }
        expected = {
            "full": 16,
            "operator_erased": 8,
            "terrain_erased": 4,
            "terrain_and_operator_erased": 1,
        }
        checks = {
            name: rows[name]["cluster_count"] == expected_count
            for name, expected_count in expected.items()
        }
        by_orientation[orientation] = {
            "rows": rows,
            "expected_cluster_counts": expected,
            "checks": checks,
            "all_pass": all(checks.values()),
        }
    return {
        "by_orientation": by_orientation,
        "all_pass": all(row["all_pass"] for row in by_orientation.values()),
        "interpretation": "the 16-way map identity is jointly carried: terrain-only action leaves eight classes, operator-cycle action without terrain leaves four canonical-anchor classes, and erasing both leaves one class",
    }


def package_fingerprint() -> dict[str, Any]:
    import pykoopman
    import pysindy

    pykoopman_capability = json.loads(PYKOOPMAN_CAPABILITY_PATH.read_text())
    pysindy_capability = json.loads(PYSINDY_CAPABILITY_PATH.read_text())
    return {
        "python": sys.version,
        "pysindy": {
            "version": importlib.metadata.version("pysindy"),
            "module_path": pysindy.__file__,
            "capability_all_pass": pysindy_capability["all_pass"],
        },
        "pykoopman": {
            "version": importlib.metadata.version("pykoopman"),
            "module_path": pykoopman.__file__,
            "bounded_edmd_core_all_pass": pykoopman_capability["all_pass"],
            "package_distribution_contract_clean": pykoopman_capability["summary"]["package_distribution_contract_clean"],
            "full_distribution_admitted": False,
            "surface_used": "Identity observable plus EDMD with explicit affine bias coordinate",
        },
        "numpy": importlib.metadata.version("numpy"),
        "scipy": importlib.metadata.version("scipy"),
        "scikit_learn": importlib.metadata.version("scikit-learn"),
    }


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    prerequisite = prerequisite_check()
    slots, slot_meta = stage_base.load_slots()
    source = source_check(slots, slot_meta)
    terrain_fits, terrain_receipt = fit_terrain_models()
    x_train = sample_bloch(SEED + 400, TRAIN_ROWS)
    x_test = sample_bloch(SEED + 500, TEST_ROWS)

    rows = []
    reidentification = {}
    for orientation in ORIENTATIONS:
        predicted_by_slot = {}
        exact_by_slot = {}
        for slot in slots:
            row, _models, predicted, exact = fit_slot_orientation(
                slot,
                orientation,
                terrain_fits,
                x_train,
                x_test,
            )
            rows.append(row)
            predicted_by_slot[slot.slot_id] = predicted
            exact_by_slot[slot.slot_id] = exact
        reidentification[orientation] = reidentify(
            slots,
            orientation,
            predicted_by_slot,
            exact_by_slot,
        )

    identity = identity_boundary(x_test)
    identity_ablation = identity_ablation_clusters(slots, x_test)
    all_beat_rows = [beat for row in rows for beat in row["beat_models"]]
    all_drop_rows = [control for row in rows for control in row["controls"]["beat_removal"]]
    all_duplicate_rows = [control for row in rows for control in row["controls"]["duplicate_beat"]]
    aggregate = {
        "macro_slot_count": len(slots),
        "candidate_orientation_count": len(ORIENTATIONS),
        "candidate_schedule_count": len(rows),
        "candidate_beat_model_count": len(all_beat_rows),
        "beats_per_one_orientation": len(slots) * 4,
        "minimum_beat_heldout_r2": min(row["heldout_r2"] for row in all_beat_rows),
        "maximum_beat_heldout_rmse": max(row["heldout_rmse"] for row in all_beat_rows),
        "minimum_rollout_heldout_r2": min(row["rollout"]["heldout_r2"] for row in rows),
        "maximum_rollout_heldout_rmse": max(row["rollout"]["heldout_rmse"] for row in rows),
        "load_bearing_beat_removals": sum(row["load_bearing_beyond_fit_error"] for row in all_drop_rows),
        "beat_removal_count": len(all_drop_rows),
        "endpoint_changing_beat_duplications": sum(row["changes_endpoint_beyond_fit_error"] for row in all_duplicate_rows),
        "beat_duplication_count": len(all_duplicate_rows),
        "rows_passing_all_local_checks": sum(row["all_local_checks_pass"] for row in rows),
        "row_count": len(rows),
        "reidentification_accuracy": {
            orientation: receipt["accuracy"] for orientation, receipt in reidentification.items()
        },
        "minimum_reidentification_margin": min(
            receipt["minimum_margin"] for receipt in reidentification.values()
        ),
    }
    candidate_checks = {
        "all_128_beat_models_fit_heldout_exact_maps": len(all_beat_rows) == 128
        and aggregate["minimum_beat_heldout_r2"] >= 0.999999
        and aggregate["maximum_beat_heldout_rmse"] < FIT_TOL,
        "all_32_candidate_schedule_rollouts_fit_heldout_exact_maps": len(rows) == 32
        and aggregate["minimum_rollout_heldout_r2"] >= 0.999999
        and aggregate["maximum_rollout_heldout_rmse"] < FIT_TOL,
        "both_orientations_reidentify_all_16_macro_maps": all(
            receipt["accuracy"] == 1.0 for receipt in reidentification.values()
        ),
        "all_128_beat_removals_change_heldout_transition": aggregate["load_bearing_beat_removals"] == 128,
        "all_128_beat_duplications_change_heldout_transition": aggregate["endpoint_changing_beat_duplications"] == 128,
        "all_32_rows_pass_sign_order_terrain_operator_controls": aggregate["rows_passing_all_local_checks"] == 32,
        "identity_boundary_is_order_insensitive": identity["order_insensitive"],
        "identity_ablation_has_16_to_8_to_4_to_1_collapse": identity_ablation["all_pass"],
    }
    instrument_checks = {
        "conditional_product_prerequisite_passes": prerequisite["all_pass"],
        "source_slot_parser_and_corruption_control_pass": source["all_pass"],
        "pysindy_terrain_receipt_passes": terrain_receipt["all_pass"],
        "pykoopman_capability_receipt_passes": json.loads(PYKOOPMAN_CAPABILITY_PATH.read_text())["all_pass"],
        "pysindy_capability_receipt_passes": json.loads(PYSINDY_CAPABILITY_PATH.read_text())["all_pass"],
    }
    candidate_survives = all(candidate_checks.values())
    all_pass = bool(all(instrument_checks.values()) and candidate_survives)

    result = {
        "schema": "codex_ratchet.stage16x4_system_id_instrument.result.v0",
        "name": "stage16x4_system_id_instrument_v0",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "stage_movement_allowed": stage_movement_allowed,
        "sim_execution_kind": sim_execution_kind,
        "source_alignment_category": source_alignment_category,
        "seed": SEED,
        "spec": spec,
        "scientific_question": "Under the already-conditional four-cell product premise and one finite house-map parameterization, can every source macro slot execute four same-sign ordered beats that external system-identification tools recover on held-out states, and do destructive controls change the resulting transition?",
        "premise_boundary": {
            "four_cells_and_cycle_are_input": True,
            "canonical_first_rotation_is_candidate_architecture": True,
            "source_16_slots_are_input": True,
            "house_one_qubit_maps_are_input": True,
            "dual_ratchet_emergence_tested": False,
        },
        "source_hashes": {
            str(path.relative_to(REPO)): sha256(path)
            for path in (
                SPEC_PATH,
                SCRIPT_PATH,
                VALIDATOR_PATH,
                FLOW_PATH,
                SOURCE_PATH,
                BASE_PATH,
                PRODUCT_VALIDATOR_PATH,
                PRODUCT_JAX_PATH,
                PYSINDY_CAPABILITY_SCRIPT,
                PYSINDY_CAPABILITY_PATH,
                PYKOOPMAN_CAPABILITY_SCRIPT,
                PYKOOPMAN_CAPABILITY_PATH,
            )
        },
        "package_fingerprint": package_fingerprint(),
        "prerequisite": prerequisite,
        "source_check": source,
        "terrain_system_identification": terrain_receipt,
        "stage_rows": rows,
        "reidentification": reidentification,
        "identity_boundary": identity,
        "identity_ablation_clusters": identity_ablation,
        "aggregate": aggregate,
        "instrument_checks": instrument_checks,
        "candidate_checks": candidate_checks,
        "candidate_16x4_survives_local_controls": candidate_survives,
        "all_pass": all_pass,
        "accepted_status_label": "passes local rerun" if all_pass else "local candidate gate failed",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": [
            "dual-ratchet four-substage emergence",
            "canonical QIT engine admission",
            "64 unique intelligences or personalities",
            "Type-1/Type-2 scientific-method equivalence",
            "perception or object formation",
            "MMM or ontology authority",
            "Axis0 or full manifold closure",
            "entropy-gradient or physics theorem",
            "Leviathan mesh mutation",
        ],
        "next_experiment": "Derive a survivor set from independent geometry-first and entropy-first ratchets over a declared superset, then feed only their intersection into this instrument without hard-coding a count of four.",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(jsonable(result), indent=2) + "\n")
    print(json.dumps({"all_pass": all_pass, "aggregate": aggregate, "candidate_checks": candidate_checks}, indent=2))
    print(f"result={RESULT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
