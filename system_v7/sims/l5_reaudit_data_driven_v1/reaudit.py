#!/usr/bin/env python3
"""Finite, fit-only L5 model comparison frozen by card.md.

The script reads only the copied nine-row JSON input.  It appends one canonical
JSON record per execution and prints a deterministic heldout RMSE table.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np


HERE = Path(__file__).resolve().parent
CARD_PATH = HERE / "card.md"
DATA_PATH = HERE / "manifold_L5_nested_shells_schmidt_strata_sim_results.json"
RESULTS_PATH = HERE / "results_v1.json"
EXPECTED_DATA_SHA256 = "ba96e5888e42851798925572b238d564ca0c1797b07362c4c876a97e4af04116"
OUTPUT_FIELDS = ("shell_radius", "marg_entropy_bits", "purity", "negativity")
CANDIDATE_ORDER = (
    "k_nearest_neighbor_lookup",
    "polynomial_degree3",
    "monotone_piecewise_linear",
    "scalar_stratum",
    "nested_shell_structured",
    "constant_mean_baseline",
    "deliberate_high_degree_overfit",
)
PRIMARY_SEED = 0
STABILITY_SEEDS = (0, 1, 2)
FIT_COUNT = 6
NUMERICAL_TOLERANCE = 1.0e-12
EQUIVALENCE_TOLERANCE = 1.0e-2
OVERFIT_GAIN = 1000.0
LABEL_ERASURE_SEED_BASE = 913
SIM_STACK_PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
classification = "scratch_diagnostic"
SIM_EXECUTION_KIND = "classical"
METADATA_REVISION = "post_freeze_transitive_scan_repair_v3"

TOOL_MANIFEST = {
    "numpy": {
        "used": True,
        "reason": "load-bearing finite least-squares, isotonic, interpolation, prediction, and RMSE calculations",
    },
    "python_stdlib": {
        "used": True,
        "reason": "load-bearing seeded split, source hashing, AST leakage gate, canonical JSON, and append-only write",
    },
    "scipy": {
        "used": False,
        "reason": "not needed; the frozen candidates use only NumPy and explicit deterministic algorithms",
    },
    "old_l5_generator_or_reaudit": {
        "used": False,
        "reason": "forbidden leakage surface; only the copied finite JSON rows are read",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "python_stdlib": None,
    "scipy": None,
    "old_l5_generator_or_reaudit": None,
}

# CANDIDATE_IMPLEMENTATION_START
def _as_float_array(values: Any) -> np.ndarray:
    return np.asarray(values, dtype=np.float64)


def _normalizer(values: np.ndarray) -> tuple[float, float]:
    minimum = float(np.min(values))
    span = float(np.max(values) - minimum)
    if span <= 0.0:
        span = 1.0
    return minimum, span


def _power_design(normalized: np.ndarray, degree: int) -> np.ndarray:
    return np.column_stack([normalized**power for power in range(degree + 1)])


def _fit_power(inputs: np.ndarray, targets: np.ndarray, degree: int) -> dict[str, Any]:
    minimum, span = _normalizer(inputs)
    normalized = (inputs - minimum) / span
    design = _power_design(normalized, degree)
    coefficients = np.linalg.lstsq(design, targets, rcond=None)[0]
    return {
        "minimum": minimum,
        "span": span,
        "degree": degree,
        "coefficients": _as_float_array(coefficients),
    }


def _predict_power(model: dict[str, Any], inputs: np.ndarray) -> np.ndarray:
    normalized = (inputs - float(model["minimum"])) / float(model["span"])
    design = _power_design(normalized, int(model["degree"]))
    return design @ _as_float_array(model["coefficients"])


def _pava(values: np.ndarray, increasing: bool) -> np.ndarray:
    work = _as_float_array(values)
    if not increasing:
        work = -work
    block_values: list[float] = []
    block_weights: list[int] = []
    for value in work:
        block_values.append(float(value))
        block_weights.append(1)
        while len(block_values) >= 2 and block_values[-2] > block_values[-1]:
            left_value = block_values[-2]
            right_value = block_values[-1]
            left_weight = block_weights[-2]
            right_weight = block_weights[-1]
            merged_weight = left_weight + right_weight
            merged_value = (
                left_value * left_weight + right_value * right_weight
            ) / merged_weight
            block_values[-2:] = [merged_value]
            block_weights[-2:] = [merged_weight]
    expanded = np.concatenate(
        [np.full(weight, value, dtype=np.float64) for value, weight in zip(block_values, block_weights)]
    )
    return expanded if increasing else -expanded


def _linear_interpolate_extrapolate(
    knots_x: np.ndarray, knots_y: np.ndarray, query: np.ndarray
) -> np.ndarray:
    result = np.interp(query, knots_x, knots_y)
    left_mask = query < knots_x[0]
    right_mask = query > knots_x[-1]
    left_slope = (knots_y[1] - knots_y[0]) / (knots_x[1] - knots_x[0])
    right_slope = (knots_y[-1] - knots_y[-2]) / (knots_x[-1] - knots_x[-2])
    result[left_mask] = knots_y[0] + left_slope * (query[left_mask] - knots_x[0])
    result[right_mask] = knots_y[-1] + right_slope * (query[right_mask] - knots_x[-1])
    return result


def _bernstein_design(normalized: np.ndarray) -> np.ndarray:
    one_minus = 1.0 - normalized
    return np.column_stack(
        [
            one_minus**3,
            3.0 * normalized * one_minus**2,
            3.0 * normalized**2 * one_minus,
            normalized**3,
        ]
    )


def _fit_scalar_maps(scalar: np.ndarray, targets: np.ndarray) -> list[dict[str, Any]]:
    return [_fit_power(scalar, targets[:, column], 3) for column in range(1, targets.shape[1])]


def _predict_scalar_maps(
    scalar_prediction: np.ndarray, maps: list[dict[str, Any]]
) -> np.ndarray:
    other_predictions = [_predict_power(model, scalar_prediction) for model in maps]
    return np.column_stack([scalar_prediction, *other_predictions])


def fit_k_nearest_neighbor_lookup(
    fit_angles: np.ndarray, fit_targets: np.ndarray, fit_indices: np.ndarray
) -> dict[str, Any]:
    return {
        "kind": "k_nearest_neighbor_lookup",
        "fit_angles": fit_angles.copy(),
        "fit_targets": fit_targets.copy(),
        "fit_indices": fit_indices.copy(),
        "k": 2,
        "fitted_parameters": {"lookup_readouts": fit_targets.copy()},
    }


def fit_polynomial_degree3(
    fit_angles: np.ndarray, fit_targets: np.ndarray, fit_indices: np.ndarray
) -> dict[str, Any]:
    del fit_indices
    polynomials = [_fit_power(fit_angles, fit_targets[:, column], 3) for column in range(fit_targets.shape[1])]
    return {
        "kind": "polynomial_degree3",
        "polynomials": polynomials,
        "fitted_parameters": {
            f"readout_{column}_coefficients": model["coefficients"]
            for column, model in enumerate(polynomials)
        },
    }


def fit_monotone_piecewise_linear(
    fit_angles: np.ndarray, fit_targets: np.ndarray, fit_indices: np.ndarray
) -> dict[str, Any]:
    del fit_indices
    order = np.argsort(fit_angles, kind="stable")
    knots_x = fit_angles[order]
    ordered_targets = fit_targets[order]
    fitted_columns = []
    directions = []
    centered_x = knots_x - np.mean(knots_x)
    for column in range(ordered_targets.shape[1]):
        values = ordered_targets[:, column]
        covariance = float(np.dot(centered_x, values - np.mean(values)))
        increasing = covariance >= 0.0
        fitted_columns.append(_pava(values, increasing=increasing))
        directions.append("increasing" if increasing else "decreasing")
    fitted_knots = np.column_stack(fitted_columns)
    return {
        "kind": "monotone_piecewise_linear",
        "knots_x": knots_x,
        "knots_y": fitted_knots,
        "directions": directions,
        "fitted_parameters": {"isotonic_knot_readouts": fitted_knots},
    }


def fit_scalar_stratum(
    fit_angles: np.ndarray, fit_targets: np.ndarray, fit_indices: np.ndarray
) -> dict[str, Any]:
    del fit_indices
    radius_model = _fit_power(fit_angles, fit_targets[:, 0], 3)
    readout_maps = _fit_scalar_maps(fit_targets[:, 0], fit_targets)
    parameters: dict[str, np.ndarray] = {"radius_coefficients": radius_model["coefficients"]}
    parameters.update(
        {
            f"scalar_map_{column}_coefficients": model["coefficients"]
            for column, model in enumerate(readout_maps, start=1)
        }
    )
    return {
        "kind": "scalar_stratum",
        "radius_model": radius_model,
        "readout_maps": readout_maps,
        "fitted_parameters": parameters,
    }


def fit_nested_shell_structured(
    fit_angles: np.ndarray, fit_targets: np.ndarray, fit_indices: np.ndarray
) -> dict[str, Any]:
    del fit_indices
    minimum, span = _normalizer(fit_angles)
    normalized = (fit_angles - minimum) / span
    design = _bernstein_design(normalized)
    unconstrained = np.linalg.lstsq(design, fit_targets[:, 0], rcond=None)[0]
    centered_x = fit_angles - np.mean(fit_angles)
    centered_radius = fit_targets[:, 0] - np.mean(fit_targets[:, 0])
    increasing = float(np.dot(centered_x, centered_radius)) >= 0.0
    ordered_controls = _pava(unconstrained, increasing=increasing)
    readout_maps = _fit_scalar_maps(fit_targets[:, 0], fit_targets)
    parameters: dict[str, np.ndarray] = {"ordered_radius_controls": ordered_controls}
    parameters.update(
        {
            f"scalar_map_{column}_coefficients": model["coefficients"]
            for column, model in enumerate(readout_maps, start=1)
        }
    )
    return {
        "kind": "nested_shell_structured",
        "minimum": minimum,
        "span": span,
        "unconstrained_controls": unconstrained,
        "ordered_controls": ordered_controls,
        "direction": "increasing" if increasing else "decreasing",
        "readout_maps": readout_maps,
        "fitted_parameters": parameters,
    }


def fit_constant_mean_baseline(
    fit_angles: np.ndarray, fit_targets: np.ndarray, fit_indices: np.ndarray
) -> dict[str, Any]:
    del fit_angles, fit_indices
    means = np.mean(fit_targets, axis=0)
    return {
        "kind": "constant_mean_baseline",
        "means": means,
        "fitted_parameters": {"readout_means": means},
    }


def fit_deliberate_high_degree_overfit(
    fit_angles: np.ndarray, fit_targets: np.ndarray, fit_indices: np.ndarray
) -> dict[str, Any]:
    del fit_indices
    order = np.argsort(fit_angles, kind="stable")
    knots_x = fit_angles[order]
    knots_y = fit_targets[order]
    weights = np.empty(len(knots_x), dtype=np.float64)
    for index, value in enumerate(knots_x):
        differences = value - np.delete(knots_x, index)
        weights[index] = 1.0 / float(np.prod(differences))
    span = float(knots_x[-1] - knots_x[0])
    if span <= 0.0:
        span = 1.0
    amplitudes = OVERFIT_GAIN * np.ptp(knots_y, axis=0)
    return {
        "kind": "deliberate_high_degree_overfit",
        "knots_x": knots_x,
        "knots_y": knots_y,
        "weights": weights,
        "span": span,
        "amplitudes": amplitudes,
        "degree": len(knots_x),
        "fitted_parameters": {
            "interpolated_readouts": knots_y,
            "nullspace_amplitudes": amplitudes,
        },
    }


def predict_model(model: dict[str, Any], angles: np.ndarray) -> np.ndarray:
    query = _as_float_array(angles).reshape(-1)
    kind = str(model["kind"])
    if kind == "k_nearest_neighbor_lookup":
        rows = []
        for value in query:
            distances = np.abs(model["fit_angles"] - value)
            order = np.lexsort((model["fit_indices"], distances))
            rows.append(np.mean(model["fit_targets"][order[: int(model["k"])]], axis=0))
        return np.vstack(rows)
    if kind == "polynomial_degree3":
        return np.column_stack([_predict_power(poly, query) for poly in model["polynomials"]])
    if kind == "monotone_piecewise_linear":
        return np.column_stack(
            [
                _linear_interpolate_extrapolate(model["knots_x"], model["knots_y"][:, column], query)
                for column in range(model["knots_y"].shape[1])
            ]
        )
    if kind == "scalar_stratum":
        scalar_prediction = _predict_power(model["radius_model"], query)
        return _predict_scalar_maps(scalar_prediction, model["readout_maps"])
    if kind == "nested_shell_structured":
        normalized = (query - float(model["minimum"])) / float(model["span"])
        scalar_prediction = _bernstein_design(normalized) @ model["ordered_controls"]
        return _predict_scalar_maps(scalar_prediction, model["readout_maps"])
    if kind == "constant_mean_baseline":
        return np.repeat(model["means"][None, :], len(query), axis=0)
    if kind == "deliberate_high_degree_overfit":
        rows = []
        for value in query:
            differences = value - model["knots_x"]
            exact = np.flatnonzero(np.abs(differences) <= np.finfo(np.float64).eps)
            if len(exact):
                base = model["knots_y"][int(exact[0])].copy()
            else:
                ratios = model["weights"] / differences
                base = (ratios @ model["knots_y"]) / np.sum(ratios)
            nullspace = float(np.prod(differences / float(model["span"])))
            rows.append(base + nullspace * model["amplitudes"])
        return np.vstack(rows)
    raise AssertionError(f"unknown candidate kind: {kind}")
# CANDIDATE_IMPLEMENTATION_END


CANDIDATE_FITTERS: dict[str, Callable[[np.ndarray, np.ndarray, np.ndarray], dict[str, Any]]] = {
    "k_nearest_neighbor_lookup": fit_k_nearest_neighbor_lookup,
    "polynomial_degree3": fit_polynomial_degree3,
    "monotone_piecewise_linear": fit_monotone_piecewise_linear,
    "scalar_stratum": fit_scalar_stratum,
    "nested_shell_structured": fit_nested_shell_structured,
    "constant_mean_baseline": fit_constant_mean_baseline,
    "deliberate_high_degree_overfit": fit_deliberate_high_degree_overfit,
}

CANDIDATE_ASSUMPTIONS = {
    "k_nearest_neighbor_lookup": {"finite_fit_table", "angle_metric", "two_neighbor_average"},
    "polynomial_degree3": {"angle_coordinate", "independent_cubic_readouts"},
    "monotone_piecewise_linear": {"ordered_angle_knots", "monotone_readouts", "piecewise_linearity"},
    "scalar_stratum": {
        "angle_coordinate",
        "one_scalar_stratum",
        "cubic_scalar_fit",
        "scalar_readout_maps",
    },
    "nested_shell_structured": {
        "angle_coordinate",
        "one_scalar_stratum",
        "cubic_scalar_fit",
        "scalar_readout_maps",
        "monotone_nested_radius",
        "bernstein_control_shells",
    },
    "constant_mean_baseline": {"constant_readout"},
    "deliberate_high_degree_overfit": {
        "finite_fit_table",
        "degree_six_interpolation",
        "fit_nullspace_amplification",
    },
}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_candidate_source_clean() -> dict[str, Any]:
    source = Path(__file__).read_text(encoding="utf-8")
    start_marker = "# CANDIDATE_IMPLEMENTATION_" + "START"
    end_marker = "# CANDIDATE_IMPLEMENTATION_" + "END"
    start = source.index(start_marker) + len(start_marker)
    end = source.index(end_marker)
    block = source[start:end]
    normalized = re.sub(r"\s+", "", block.lower())
    banned_token = "cos" + "(2"
    if banned_token in normalized:
        raise AssertionError("candidate implementation contains banned closed-form token")
    tree = ast.parse(block)
    banned_names = {"truth", "generator", "heldout", "all_rows", "source_sweep"}
    banned_calls = {"sin", "cos", "tan", "asin", "acos", "atan", "open", "load", "loads"}
    defined_helpers = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    safe_builtin_calls = {
        "AssertionError",
        "enumerate",
        "float",
        "int",
        "len",
        "list",
        "range",
        "str",
        "zip",
    }
    safe_method_calls = {"append", "copy", "reshape", "update"}
    found_names = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id in banned_names})
    found_calls = []
    escaped_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        name = function.id if isinstance(function, ast.Name) else function.attr if isinstance(function, ast.Attribute) else ""
        if name in banned_calls:
            found_calls.append(name)
        if isinstance(function, ast.Name):
            if name not in defined_helpers and name not in safe_builtin_calls:
                escaped_calls.append(name)
        elif isinstance(function, ast.Attribute):
            root: ast.AST = function
            while isinstance(root, ast.Attribute):
                root = root.value
            root_name = root.id if isinstance(root, ast.Name) else ""
            if root_name != "np" and function.attr not in safe_method_calls:
                escaped_calls.append(f"{root_name or '<expression>'}.{function.attr}")
        else:
            escaped_calls.append(type(function).__name__)
    if found_names or found_calls or escaped_calls:
        raise AssertionError(
            "candidate source leakage gate failed: "
            f"names={found_names}, calls={sorted(found_calls)}, escaped={sorted(set(escaped_calls))}"
        )
    return {
        "block_sha256": hashlib.sha256(block.encode("utf-8")).hexdigest(),
        "exact_banned_token_absent": True,
        "trigonometric_calls_absent": True,
        "leakage_names_absent": True,
        "file_io_calls_absent": True,
        "transitive_helpers_inside_scanned_block": True,
        "external_call_whitelist_enforced": True,
        "defined_helper_count": len(defined_helpers),
    }


def load_rows() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    actual_hash = sha256_path(DATA_PATH)
    if actual_hash != EXPECTED_DATA_SHA256:
        raise AssertionError(f"copied data hash mismatch: {actual_hash}")
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    rows = payload.get("dual_ratchet_sweep")
    if not isinstance(rows, list) or len(rows) != 9:
        raise AssertionError("expected exactly nine finite sweep rows")
    required = {"a", *OUTPUT_FIELDS}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not required.issubset(row):
            raise AssertionError(f"row {index} lacks required finite fields")
        if not all(isinstance(row[field], (int, float)) for field in required):
            raise AssertionError(f"row {index} contains nonnumeric data")
    indices = np.arange(len(rows), dtype=np.int64)
    angles = _as_float_array([row["a"] for row in rows])
    targets = _as_float_array([[row[field] for field in OUTPUT_FIELDS] for row in rows])
    if not np.all(np.isfinite(angles)) or not np.all(np.isfinite(targets)):
        raise AssertionError("finite sweep contains nonfinite values")
    return indices, angles, targets


def split_indices(row_count: int, seed: int) -> tuple[np.ndarray, np.ndarray, list[int]]:
    shuffled = list(range(row_count))
    random.Random(seed).shuffle(shuffled)
    fit = np.asarray(sorted(shuffled[:FIT_COUNT]), dtype=np.int64)
    heldout = np.asarray(sorted(shuffled[FIT_COUNT:]), dtype=np.int64)
    if len(set(fit.tolist()) & set(heldout.tolist())):
        raise AssertionError("fit and heldout overlap")
    return fit, heldout, shuffled


def pooled_rmse(predicted: np.ndarray, observed: np.ndarray) -> float:
    return float(np.sqrt(np.mean((predicted - observed) ** 2)))


def metric_record(predicted: np.ndarray, observed: np.ndarray) -> dict[str, Any]:
    errors = predicted - observed
    return {
        "pooled_rmse": float(np.sqrt(np.mean(errors**2))),
        "per_readout_rmse": {
            field: float(np.sqrt(np.mean(errors[:, column] ** 2)))
            for column, field in enumerate(OUTPUT_FIELDS)
        },
    }


def parameter_count(model: dict[str, Any]) -> int:
    return int(sum(_as_float_array(values).size for values in model["fitted_parameters"].values()))


def serializable_parameters(model: dict[str, Any]) -> dict[str, Any]:
    return {
        name: _as_float_array(values).tolist()
        for name, values in sorted(model["fitted_parameters"].items())
    }


def model_receipt(model: dict[str, Any]) -> dict[str, Any]:
    name = str(model["kind"])
    receipt: dict[str, Any] = {
        "candidate": name,
        "fit_only": True,
        "predictor_input": ["a"],
        "assumptions": sorted(CANDIDATE_ASSUMPTIONS[name]),
        "fitted_parameter_count": parameter_count(model),
        "fitted_parameters": serializable_parameters(model),
    }
    if name == "monotone_piecewise_linear":
        receipt["learned_directions"] = list(model["directions"])
    if name == "nested_shell_structured":
        receipt["learned_direction"] = model["direction"]
        receipt["unconstrained_controls"] = model["unconstrained_controls"].tolist()
    if name == "deliberate_high_degree_overfit":
        receipt["degree"] = int(model["degree"])
        receipt["gain"] = OVERFIT_GAIN
    return receipt


def fit_all(
    fit_angles: np.ndarray, fit_targets: np.ndarray, fit_indices: np.ndarray
) -> dict[str, dict[str, Any]]:
    return {
        name: CANDIDATE_FITTERS[name](fit_angles.copy(), fit_targets.copy(), fit_indices.copy())
        for name in CANDIDATE_ORDER
    }


def inference_interface_check(
    models: dict[str, dict[str, Any]], probe_angles: np.ndarray
) -> bool:
    parameter_names = list(inspect.signature(predict_model).parameters)
    if parameter_names != ["model", "angles"]:
        return False
    for name in CANDIDATE_ORDER:
        prediction = predict_model(models[name], probe_angles.copy())
        if prediction.shape != (len(probe_angles), len(OUTPUT_FIELDS)):
            return False
        if not np.all(np.isfinite(prediction)):
            return False
    return True


def compare_primary_models(metrics: dict[str, dict[str, Any]]) -> str:
    scalar = float(metrics["scalar_stratum"]["heldout"]["pooled_rmse"])
    nested = float(metrics["nested_shell_structured"]["heldout"]["pooled_rmse"])
    delta = scalar - nested
    if delta > EQUIVALENCE_TOLERANCE:
        return "NESTED_SHELL_BEATS_SCALAR"
    if -delta > EQUIVALENCE_TOLERANCE:
        return "SCALAR_BEATS_NESTED_SHELL"
    return "INDISTINGUISHABLE_WITHIN_FROZEN_TOLERANCE"


def project_nested_to_scalar(model: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    controls = _as_float_array(model["ordered_controls"])
    c0, c1, c2, c3 = [float(value) for value in controls]
    power_coefficients = np.asarray(
        [
            c0,
            3.0 * (c1 - c0),
            3.0 * (c0 - 2.0 * c1 + c2),
            -c0 + 3.0 * c1 - 3.0 * c2 + c3,
        ],
        dtype=np.float64,
    )
    radius_model = {
        "minimum": float(model["minimum"]),
        "span": float(model["span"]),
        "degree": 3,
        "coefficients": power_coefficients,
    }
    parameters: dict[str, np.ndarray] = {"radius_coefficients": power_coefficients}
    parameters.update(
        {
            f"scalar_map_{column}_coefficients": readout_map["coefficients"]
            for column, readout_map in enumerate(model["readout_maps"], start=1)
        }
    )
    projected = {
        "kind": "scalar_stratum",
        "radius_model": radius_model,
        "readout_maps": copy.deepcopy(model["readout_maps"]),
        "fitted_parameters": parameters,
    }
    return projected, ["monotone_nested_radius", "bernstein_control_shells"]


def weakness_witness(
    nested: dict[str, Any], separately_fit_scalar: dict[str, Any], fit_angles: np.ndarray, heldout_angles: np.ndarray
) -> dict[str, Any]:
    projected, dropped = project_nested_to_scalar(nested)
    nested_fit = predict_model(nested, fit_angles)
    nested_heldout = predict_model(nested, heldout_angles)
    projected_fit = predict_model(projected, fit_angles)
    projected_heldout = predict_model(projected, heldout_angles)
    source_count = parameter_count(nested)
    target_count = parameter_count(projected)
    source_assumptions = set(CANDIDATE_ASSUMPTIONS["nested_shell_structured"])
    target_assumptions = set(CANDIDATE_ASSUMPTIONS["scalar_stratum"])
    fit_projection_rmse = pooled_rmse(projected_fit, nested_fit)
    heldout_projection_rmse = pooled_rmse(projected_heldout, nested_heldout)
    witnessed = (
        target_count <= source_count
        and target_assumptions < source_assumptions
        and fit_projection_rmse <= NUMERICAL_TOLERANCE
        and heldout_projection_rmse <= NUMERICAL_TOLERANCE
    )
    return {
        "source": "nested_shell_structured",
        "target": "scalar_stratum_representation",
        "projection": "cubic Bernstein controls converted to cubic power basis; monotone constraints dropped",
        "dropped_assumptions": dropped,
        "source_parameter_count": source_count,
        "target_parameter_count": target_count,
        "parameter_count_delta": target_count - source_count,
        "parameter_relation": "equal" if target_count == source_count else "reduced",
        "source_assumptions": sorted(source_assumptions),
        "target_assumptions": sorted(target_assumptions),
        "strict_assumption_subset_computed": target_assumptions < source_assumptions,
        "fit_projection_rmse": fit_projection_rmse,
        "heldout_projection_rmse": heldout_projection_rmse,
        "separately_fit_scalar_vs_projected_fit_rmse": pooled_rmse(
            predict_model(separately_fit_scalar, fit_angles), projected_fit
        ),
        "separately_fit_scalar_vs_projected_heldout_rmse": pooled_rmse(
            predict_model(separately_fit_scalar, heldout_angles), projected_heldout
        ),
        "witnessed": bool(witnessed),
    }


def execute_seed(
    seed: int, indices: np.ndarray, angles: np.ndarray, targets: np.ndarray
) -> dict[str, Any]:
    fit_indices, heldout_indices, shuffled = split_indices(len(indices), seed)
    fit_angles = angles[fit_indices]
    fit_targets = targets[fit_indices]
    heldout_angles = angles[heldout_indices]
    heldout_targets = targets[heldout_indices]
    models = fit_all(fit_angles, fit_targets, fit_indices)

    metrics: dict[str, dict[str, Any]] = {}
    for name in CANDIDATE_ORDER:
        fit_prediction = predict_model(models[name], fit_angles)
        heldout_prediction = predict_model(models[name], heldout_angles)
        metrics[name] = {
            "fit": metric_record(fit_prediction, fit_targets),
            "heldout": metric_record(heldout_prediction, heldout_targets),
        }

    erased_targets = fit_targets.copy()
    erased_order = list(range(len(erased_targets)))
    random.Random(LABEL_ERASURE_SEED_BASE + seed).shuffle(erased_order)
    erased_targets = erased_targets[np.asarray(erased_order, dtype=np.int64)]
    erased_models = fit_all(fit_angles, erased_targets, fit_indices)
    erased_metrics = {
        name: metric_record(predict_model(erased_models[name], heldout_angles), heldout_targets)
        for name in CANDIDATE_ORDER
    }
    erasure_deltas = {
        name: float(erased_metrics[name]["pooled_rmse"] - metrics[name]["heldout"]["pooled_rmse"])
        for name in CANDIDATE_ORDER
    }

    regular_names = CANDIDATE_ORDER[:5]
    best_regular_heldout = min(float(metrics[name]["heldout"]["pooled_rmse"]) for name in regular_names)
    best_any_fit = min(float(metrics[name]["fit"]["pooled_rmse"]) for name in CANDIDATE_ORDER)
    overfit_fit = float(metrics["deliberate_high_degree_overfit"]["fit"]["pooled_rmse"])
    overfit_heldout = float(metrics["deliberate_high_degree_overfit"]["heldout"]["pooled_rmse"])
    mean_heldout = float(metrics["constant_mean_baseline"]["heldout"]["pooled_rmse"])
    mean_erased = float(erased_metrics["constant_mean_baseline"]["pooled_rmse"])
    controls = {
        "scalar_label_erasure_degrades": erasure_deltas["scalar_stratum"] > EQUIVALENCE_TOLERANCE,
        "nested_label_erasure_degrades": erasure_deltas["nested_shell_structured"] > EQUIVALENCE_TOLERANCE,
        "mean_label_permutation_invariant": abs(mean_erased - mean_heldout) <= NUMERICAL_TOLERANCE,
        "overfit_fit_rank_one": overfit_fit <= best_any_fit + NUMERICAL_TOLERANCE,
        "overfit_fit_near_zero": overfit_fit <= NUMERICAL_TOLERANCE,
        "overfit_loses_heldout": overfit_heldout - best_regular_heldout > EQUIVALENCE_TOLERANCE,
        "mean_baseline_loses": mean_heldout - best_regular_heldout > EQUIVALENCE_TOLERANCE,
        "inference_angle_only": inference_interface_check(models, heldout_angles),
    }
    verdict = compare_primary_models(metrics)
    witness = weakness_witness(
        models["nested_shell_structured"],
        models["scalar_stratum"],
        fit_angles,
        heldout_angles,
    )
    controls["weakness_projection_witnessed"] = bool(witness["witnessed"])
    return {
        "seed": seed,
        "rng": "random.Random(seed).shuffle",
        "shuffled_source_indices": shuffled,
        "fit_source_indices": fit_indices.tolist(),
        "heldout_source_indices": heldout_indices.tolist(),
        "metrics": metrics,
        "model_receipts": {name: model_receipt(models[name]) for name in CANDIDATE_ORDER},
        "label_erasure": {
            "seed": LABEL_ERASURE_SEED_BASE + seed,
            "fit_label_permutation": erased_order,
            "heldout_metrics": erased_metrics,
            "pooled_rmse_degradation": erasure_deltas,
        },
        "weakness_witness": witness,
        "controls": controls,
        "controls_pass": all(controls.values()),
        "verdict": verdict,
    }


def build_result() -> dict[str, Any]:
    source_scan = assert_candidate_source_clean()
    indices, angles, targets = load_rows()
    seed_runs = [execute_seed(seed, indices, angles, targets) for seed in STABILITY_SEEDS]
    verdicts = [run["verdict"] for run in seed_runs]
    split_stable = len(set(verdicts)) == 1
    all_seed_controls_pass = all(bool(run["controls_pass"]) for run in seed_runs)
    overall_pass = split_stable and all_seed_controls_pass
    return {
        "schema_version": "l5_reaudit_data_driven_result_v1",
        "sim_id": "l5_reaudit_data_driven_v1",
        "version": 1,
        "classification": classification,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "accepted_status_ceiling": "passes local rerun" if overall_pass else "runs",
        "scientific_question": "Does the fitted monotone nested-radius surrogate beat the fitted scalar-stratum model on finite heldout rows, or are they practically indistinguishable?",
        "claim_ceiling": "finite copied-row model comparison only; fresh audit, manifold admission, and restoration of the withdrawn L5 claim remain blocked",
        "blocked_consumers": [
            "fresh audit verdict",
            "manifold layer admission",
            "formal proof or generator identification",
            "restoration of the withdrawn L5 demotion claim",
        ],
        "engine_contract": {
            "mode": "classical_numpy_finite_fit_heldout",
            "interpreter": SIM_STACK_PYTHON,
            "command": f"{SIM_STACK_PYTHON} system_v7/sims/l5_reaudit_data_driven_v1/reaudit.py",
            "predictor_input_fields": ["a"],
            "prediction_fields": list(OUTPUT_FIELDS),
            "cross_runtime_claim": False,
        },
        "source": {
            "copied_path": DATA_PATH.name,
            "sha256": sha256_path(DATA_PATH),
            "source_row_surface": "dual_ratchet_sweep",
            "row_count": len(indices),
            "read_only_source_reference": "system_v7/constraint_core/sims_and_scripts/manifold_L5_nested_shells_schmidt_strata_sim_results.json",
            "old_reaudit_imported": False,
            "source_generator_imported": False,
        },
        "card": {"path": CARD_PATH.name, "sha256": sha256_path(CARD_PATH), "declared_before_run": True},
        "frozen_rules": {
            "primary_seed": PRIMARY_SEED,
            "stability_seeds": list(STABILITY_SEEDS),
            "fit_count": FIT_COUNT,
            "heldout_count": len(indices) - FIT_COUNT,
            "split_algorithm": "random.Random(seed).shuffle; first six fit; remaining three heldout; partitions sorted by source index",
            "pooled_rmse": "unweighted RMSE over heldout rows and four readouts",
            "numerical_tolerance": NUMERICAL_TOLERANCE,
            "practical_equivalence_tolerance": EQUIVALENCE_TOLERANCE,
            "overfit_gain": OVERFIT_GAIN,
        },
        "candidate_source_scan": source_scan,
        "candidate_order": list(CANDIDATE_ORDER),
        "seed_runs": seed_runs,
        "split_stability": {
            "verdicts": verdicts,
            "passed": split_stable,
        },
        "controls_pass": all_seed_controls_pass,
        "overall_pass": overall_pass,
        "verdict": verdicts[0] if split_stable else "SPLIT_UNSTABLE",
        "status": "FROZEN_BUILD_CONTROLS_PASS" if overall_pass else "FROZEN_BUILD_RED__FRESH_AUDIT_BLOCKED",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [
            "classical finite diagnostic only",
            "nine rows and three heldout rows per seed give low statistical power",
            "nested candidate is a monotone radius surrogate, not topology or full shell geometry",
            "no cross-runtime, formal proof, or scientific manifold admission claim",
            "fresh-context semantic audit intentionally not run in this build",
        ],
        "append_receipt": {
            "format": "canonical JSON Lines in results_v1.json",
            "append_only": True,
            "volatile_fields": False,
            "expected_repeated_run_records_byte_identical": True,
        },
        "metadata_revision": METADATA_REVISION,
    }


def canonical_line(record: dict[str, Any]) -> bytes:
    return (
        json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def scientific_payload(record: dict[str, Any]) -> dict[str, Any]:
    ignored = {
        "TOOL_MANIFEST",
        "TOOL_INTEGRATION_DEPTH",
        "candidate_source_scan",
        "metadata_revision",
    }
    return {key: value for key, value in record.items() if key not in ignored}


def validate_existing_records(expected_record: dict[str, Any]) -> int:
    if not RESULTS_PATH.exists():
        return 0
    count = 0
    with RESULTS_PATH.open("rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise RuntimeError(f"refusing to append after malformed result line {line_number}") from error
            if not isinstance(record, dict):
                raise RuntimeError(f"result line {line_number} is not a JSON object")
            if canonical_line(record) != line:
                raise RuntimeError(f"result line {line_number} is not canonical")
            if scientific_payload(record) != scientific_payload(expected_record):
                raise RuntimeError(f"result line {line_number} differs in scientific payload")
            count += 1
    return count


def append_record(record: dict[str, Any]) -> None:
    encoded = canonical_line(record)
    validate_existing_records(record)
    descriptor = os.open(RESULTS_PATH, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        written = 0
        while written < len(encoded):
            count = os.write(descriptor, encoded[written:])
            if count <= 0:
                raise RuntimeError("append-only result write stopped early")
            written += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def print_summary(record: dict[str, Any]) -> None:
    primary = next(run for run in record["seed_runs"] if run["seed"] == PRIMARY_SEED)
    print("L5 data-driven re-audit v1 — primary heldout RMSE (seed 0)")
    print(f"{'candidate':38s} {'fit_rmse':>14s} {'heldout_rmse':>14s}")
    for name in CANDIDATE_ORDER:
        fit_value = primary["metrics"][name]["fit"]["pooled_rmse"]
        heldout_value = primary["metrics"][name]["heldout"]["pooled_rmse"]
        print(f"{name:38s} {fit_value:14.10g} {heldout_value:14.10g}")
    print("seed verdicts")
    for run in record["seed_runs"]:
        print(f"seed {run['seed']}: {run['verdict']}")
    print(f"split_stable: {record['split_stability']['passed']}")
    print(f"controls_pass: {record['controls_pass']}")
    print(f"verdict: {record['verdict']}")
    print(f"status: {record['status']}")
    print(f"appended: {RESULTS_PATH}")


def main() -> int:
    first = build_result()
    second = build_result()
    if canonical_line(first) != canonical_line(second):
        raise AssertionError("two in-process result builds are not byte-identical")
    append_record(first)
    print_summary(first)
    return 0 if first["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
