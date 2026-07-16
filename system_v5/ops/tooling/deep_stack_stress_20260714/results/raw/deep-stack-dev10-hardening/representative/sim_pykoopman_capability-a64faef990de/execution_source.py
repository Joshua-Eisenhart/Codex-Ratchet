#!/usr/bin/env python3
"""Bounded PyKoopman EDMD receipt using an explicit affine bias coordinate."""

from __future__ import annotations

import importlib.metadata
import json
import warnings
from pathlib import Path

import numpy as np
from packaging.requirements import Requirement
from sklearn.metrics import r2_score


classification = "tool_lego_fit_probe"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "pykoopman": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Koopman plus Identity plus EDMD fit/predict receipt for a held-out affine discrete map",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic affine fixtures and error calculations",
    },
    "scikit_learn": {
        "tried": True,
        "used": True,
        "reason": "supportive held-out R2 calculation",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pykoopman": "load_bearing",
    "numpy": "supportive",
    "scikit_learn": "supportive",
    "python_json": "supportive",
}

HERE = Path(__file__).resolve().parent
RESULT_PATH = HERE / "a2_state" / "sim_results" / "pykoopman_capability_results.json"


def fit_edmd(x: np.ndarray, y: np.ndarray, augmented: bool):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from pykoopman import Koopman
        from pykoopman.observables import Identity
        from pykoopman.regression import EDMD

        x_fit = np.column_stack([x, np.ones(len(x))]) if augmented else x
        y_fit = np.column_stack([y, np.ones(len(y))]) if augmented else y
        model = Koopman(observables=Identity(), regressor=EDMD(svd_rank=x_fit.shape[1]))
        model.fit(x_fit, y=y_fit)
    return model, [str(item.message) for item in caught]


def distribution_contract() -> dict:
    actual = {}
    for name in ("numpy", "scipy", "scikit-learn", "pydmd", "torch", "lightning"):
        try:
            actual[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual[name] = None

    mismatches = []
    relevant_requirements = []
    for raw in importlib.metadata.requires("pykoopman") or []:
        requirement = Requirement(raw)
        if requirement.name.lower() not in actual:
            continue
        version = actual[requirement.name.lower()]
        relevant_requirements.append(raw)
        if version is None or (requirement.specifier and version not in requirement.specifier):
            mismatches.append({"requirement": raw, "actual": version})
    return {
        "actual_versions": actual,
        "relevant_declared_requirements": relevant_requirements,
        "mismatches": mismatches,
        "clean": not mismatches,
    }


def main() -> int:
    rng = np.random.default_rng(20260709)
    matrix = np.array(
        [[0.88, 0.12, 0.00], [-0.04, 0.79, 0.18], [0.07, 0.00, 0.73]],
        dtype=float,
    )
    offset = np.array([0.31, -0.22, 0.14], dtype=float)
    x_train = rng.uniform(-0.8, 0.8, size=(512, 3))
    x_test = rng.uniform(-0.8, 0.8, size=(192, 3))
    y_train = x_train @ matrix.T + offset
    y_test = x_test @ matrix.T + offset

    affine_model, import_warnings = fit_edmd(x_train, y_train, augmented=True)
    z_test = np.column_stack([x_test, np.ones(len(x_test))])
    affine_prediction = np.asarray(affine_model.predict(z_test), dtype=float)
    affine_rmse = float(np.sqrt(np.mean((affine_prediction[:, :3] - y_test) ** 2)))
    affine_r2 = float(r2_score(y_test, affine_prediction[:, :3]))
    bias_drift = float(np.max(np.abs(affine_prediction[:, -1] - 1.0)))

    linear_model, _ = fit_edmd(x_train, y_train, augmented=False)
    linear_prediction = np.asarray(linear_model.predict(x_test), dtype=float)
    linear_rmse = float(np.sqrt(np.mean((linear_prediction - y_test) ** 2)))

    zero = np.zeros((128, 3), dtype=float)
    identity_model, _ = fit_edmd(x_train, x_train, augmented=True)
    identity_prediction = np.asarray(
        identity_model.predict(np.column_stack([zero, np.ones(len(zero))])),
        dtype=float,
    )
    identity_max_error = float(
        np.max(np.abs(identity_prediction - np.column_stack([zero, np.ones(len(zero))])))
    )
    package_contract = distribution_contract()

    positive = {
        "heldout_r2_at_least_0_999999": affine_r2 >= 0.999999,
        "heldout_rmse_below_1e_10": affine_rmse < 1.0e-10,
        "bias_coordinate_drift_below_1e_10": bias_drift < 1.0e-10,
    }
    negative = {
        "erasing_bias_coordinate_increases_error": linear_rmse > affine_rmse + 1.0e-3,
        "erased_bias_rmse_above_0_05": linear_rmse > 0.05,
    }
    boundary = {
        "identity_map_max_error_below_1e_10": identity_max_error < 1.0e-10,
    }
    core_all_pass = bool(all(positive.values()) and all(negative.values()) and all(boundary.values()))

    result = {
        "name": "sim_pykoopman_capability",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "sim_execution_kind": sim_execution_kind,
        "scope": "PyKoopman 1.2.1 Identity-observable EDMD core only",
        "package": {
            "name": "pykoopman",
            "version": importlib.metadata.version("pykoopman"),
            "functions_exercised": [
                "pykoopman.Koopman.fit",
                "pykoopman.Koopman.predict",
                "pykoopman.observables.Identity",
                "pykoopman.regression.EDMD",
            ],
            "root_import_warnings": import_warnings,
            "distribution_contract": package_contract,
            "full_distribution_admitted": False,
            "quarantined_surfaces": [
                "Polynomial observable under the canonical scikit-learn version",
                "NNDMD and the Torch/Lightning neural path",
                "documentation and development dependencies bundled as runtime requirements",
            ],
        },
        "fixture": {
            "map_matrix": matrix.tolist(),
            "map_offset": offset.tolist(),
            "train_rows": len(x_train),
            "heldout_rows": len(x_test),
            "bias_coordinate": "explicit fourth coordinate fixed to one",
        },
        "measurements": {
            "affine_heldout_r2": affine_r2,
            "affine_heldout_rmse": affine_rmse,
            "bias_coordinate_max_drift": bias_drift,
            "erased_bias_heldout_rmse": linear_rmse,
            "identity_map_max_error": identity_max_error,
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "bounded_edmd_core_all_pass": core_all_pass,
            "package_distribution_contract_clean": package_contract["clean"],
            "full_distribution_admitted": False,
            "all_pass": core_all_pass,
        },
        "all_pass": core_all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "Function-level PyKoopman Identity plus EDMD receipt only. The package distribution and neural path remain quarantined. This does not derive four beats, establish a QIT engine, prove useful work, perception, object formation, Axis0, manifold, entropy, or physics claims.",
        "demotion_condition": "Demote the EDMD core if held-out affine recovery fails, the bias coordinate drifts, or the erased-bias control is not worse. Keep the full package quarantined until its declared dependency stack and neural path pass separately.",
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))
    print(f"result={RESULT_PATH}")
    return 0 if core_all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
