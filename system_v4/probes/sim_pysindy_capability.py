#!/usr/bin/env python3
"""Bounded PySINDy function receipt for affine continuous-time generators."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path

import numpy as np


classification = "tool_lego_fit_probe"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "pysindy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PolynomialLibrary and STLSQ recovery of an affine vector field with a shuffled-derivative falsifier",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic fixtures, coefficient comparison, and held-out error calculation",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pysindy": "load_bearing",
    "numpy": "supportive",
    "python_json": "supportive",
}

HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "a2_state" / "sim_results" / "pysindy_capability_results.json"


def fit_affine(x: np.ndarray, x_dot: np.ndarray):
    import pysindy as ps

    model = ps.SINDy(
        feature_library=ps.PolynomialLibrary(degree=1, include_bias=True),
        optimizer=ps.STLSQ(threshold=1.0e-12, alpha=1.0e-12),
    )
    model.fit(x, t=1.0, x_dot=x_dot)
    return model


def main() -> int:
    rng = np.random.default_rng(20260709)
    matrix = np.array(
        [[-0.24, 0.11, 0.00], [0.00, -0.31, 0.17], [0.06, 0.00, -0.43]],
        dtype=float,
    )
    offset = np.array([0.12, -0.07, 0.03], dtype=float)
    x_train = rng.uniform(-0.9, 0.9, size=(512, 3))
    x_test = rng.uniform(-0.9, 0.9, size=(192, 3))
    train_derivative = x_train @ matrix.T + offset
    test_derivative = x_test @ matrix.T + offset

    model = fit_affine(x_train, train_derivative)
    prediction = np.asarray(model.predict(x_test), dtype=float)
    coefficients = np.asarray(model.coefficients(), dtype=float)
    expected_coefficients = np.column_stack([offset, matrix])
    feature_names = list(model.get_feature_names())
    heldout_rmse = float(np.sqrt(np.mean((prediction - test_derivative) ** 2)))
    heldout_r2 = float(model.score(x_test, t=1.0, x_dot=test_derivative))
    coefficient_max_error = float(np.max(np.abs(coefficients - expected_coefficients)))

    shuffled = fit_affine(x_train, train_derivative[rng.permutation(len(x_train))])
    shuffled_r2 = float(shuffled.score(x_test, t=1.0, x_dot=test_derivative))

    zero_x = rng.uniform(-0.9, 0.9, size=(128, 3))
    zero_model = fit_affine(zero_x, np.zeros_like(zero_x))
    zero_prediction = np.asarray(zero_model.predict(zero_x), dtype=float)
    zero_max_abs = float(np.max(np.abs(zero_prediction)))

    positive = {
        "feature_order_is_affine": feature_names == ["1", "x0", "x1", "x2"],
        "heldout_r2_at_least_0_999999": heldout_r2 >= 0.999999,
        "heldout_rmse_below_1e_10": heldout_rmse < 1.0e-10,
        "coefficients_match_generator_below_1e_10": coefficient_max_error < 1.0e-10,
    }
    negative = {
        "shuffled_derivative_r2_below_0_25": shuffled_r2 < 0.25,
        "real_fit_beats_shuffle_by_0_70": heldout_r2 - shuffled_r2 > 0.70,
    }
    boundary = {
        "zero_generator_stays_zero_below_1e_12": zero_max_abs < 1.0e-12,
    }
    all_pass = bool(all(positive.values()) and all(negative.values()) and all(boundary.values()))

    result = {
        "name": "sim_pysindy_capability",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "sim_execution_kind": sim_execution_kind,
        "package": {
            "name": "pysindy",
            "version": importlib.metadata.version("pysindy"),
            "functions_exercised": [
                "pysindy.SINDy.fit",
                "pysindy.SINDy.predict",
                "pysindy.SINDy.score",
                "pysindy.SINDy.coefficients",
                "pysindy.PolynomialLibrary(degree=1, include_bias=True)",
                "pysindy.STLSQ",
            ],
        },
        "fixture": {
            "generator_matrix": matrix.tolist(),
            "generator_offset": offset.tolist(),
            "train_rows": len(x_train),
            "heldout_rows": len(x_test),
            "feature_names": feature_names,
        },
        "measurements": {
            "heldout_r2": heldout_r2,
            "heldout_rmse": heldout_rmse,
            "coefficient_max_abs_error": coefficient_max_error,
            "shuffled_derivative_r2": shuffled_r2,
            "zero_generator_max_abs_prediction": zero_max_abs,
            "coefficients": coefficients.tolist(),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "positive_all_pass": all(positive.values()),
            "negative_all_pass": all(negative.values()),
            "boundary_all_pass": all(boundary.values()),
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "Function-level PySINDy affine-generator receipt only. It does not identify a QIT engine, derive four substages, establish perception or object formation, or admit Axis0, manifold, entropy, or physics claims.",
        "demotion_condition": "Demote if exact affine recovery fails, held-out prediction fails, or shuffled derivatives are not rejected.",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))
    print(f"result={RESULT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
