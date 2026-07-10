#!/usr/bin/env python3
"""Run isolated deeptime linear VAMP without reading PyDMD outputs."""

from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from deeptime.decomposition import VAMP

from contract_utils import gate_lane, load_json, sha256, summarize_classifier, verify_contract, write_json


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
stage_movement_allowed = False
TOOL_MANIFEST = {
    "deeptime": {
        "used": True,
        "reason": "Linear VAMP directed lag covariance and Koopman coefficients are the only VAMP-lane classification features.",
    },
    "numpy": {
        "used": True,
        "reason": "Reads the hashed numeric contract and performs bounded classifier arithmetic.",
    },
}
TOOL_INTEGRATION_DEPTH = {"deeptime": "load_bearing", "numpy": "supportive"}


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"
CONTRACT_PATH = HERE / "artifacts" / "trajectory_contract_v1.npz"
MANIFEST_PATH = HERE / "artifacts" / "trajectory_contract_v1.json"
RECEIPT_PATH = HERE / "receipts" / "deeptime_vamp_receipt.json"
LAUNCHER_PATH = Path(
    "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/deeptime-0.4.5-py313/bin/python"
)


def vamp_features(trajectory: np.ndarray, lagtime: int) -> np.ndarray:
    model = VAMP(lagtime=lagtime, dim=None, scaling=None).fit_fetch(trajectory)
    singular = np.asarray(model.singular_values, dtype=float)
    koopman_in_observable_basis = (
        np.asarray(model.instantaneous_coefficients)
        @ np.diag(singular)
        @ np.asarray(model.timelagged_coefficients).T
    )
    directed_lag_covariance = np.asarray(model.cov.cov_0t, dtype=float)
    return np.concatenate(
        [koopman_in_observable_basis.reshape(-1), directed_lag_covariance.reshape(-1)]
    ).astype(np.float64)


def flatten_labeled(array: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
    rows = []
    labels = []
    for label in range(array.shape[0]):
        for seed_index in range(array.shape[1]):
            for probe_index in range(array.shape[2]):
                rows.append(array[label, seed_index, probe_index])
                labels.append(label)
    return rows, np.asarray(labels, dtype=int)


def fit_centroids(features: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    center = np.mean(features, axis=0)
    scale = np.std(features, axis=0)
    scale[scale < 1.0e-10] = 1.0
    normalized = (features - center) / scale
    centroids = np.stack([np.mean(normalized[labels == label], axis=0) for label in (0, 1)])
    return center, scale, centroids


def classifier_distances(
    features: np.ndarray,
    center: np.ndarray,
    scale: np.ndarray,
    centroids: np.ndarray,
) -> np.ndarray:
    normalized = (features - center) / scale
    return np.linalg.norm(normalized[:, None, :] - centroids[None, :, :], axis=2)


def evaluate(data: Any, spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    train = data["train_trajectories"]
    heldout = data["heldout_trajectories"]
    controls = data["control_indices"]
    train_rows, train_labels = flatten_labeled(train)
    train_features = np.stack([vamp_features(row, spec["vamp_lagtime"]) for row in train_rows])
    center, scale, centroids = fit_centroids(train_features, train_labels)
    heldout_rows, heldout_labels = flatten_labeled(heldout)
    evaluations: dict[str, Any] = {}

    def one(name: str, transform_index: int | None) -> None:
        rows = []
        cursor = 0
        for label in range(heldout.shape[0]):
            for seed_index in range(heldout.shape[1]):
                for probe_index in range(heldout.shape[2]):
                    row = heldout_rows[cursor]
                    if transform_index is not None:
                        row = row[controls[seed_index, probe_index, transform_index]]
                    rows.append(vamp_features(row, spec["vamp_lagtime"]))
                    cursor += 1
        evaluations[name] = summarize_classifier(
            heldout_labels,
            classifier_distances(np.stack(rows), center, scale, centroids),
        )

    one("clean", None)
    one("temporal_shuffle", 0)
    one("block_permutation", 1)
    one("reversal", 2)
    model = {
        "feature_count": int(train_features.shape[1]),
        "train_sample_count": int(train_features.shape[0]),
        "normalization_center": center.tolist(),
        "normalization_scale": scale.tolist(),
        "centroids": centroids.tolist(),
        "latent_dimension_policy": "VAMP dim=None; no four-state latent dimension is requested or imposed",
    }
    return evaluations, model


def main() -> int:
    spec = load_json(SPEC_PATH)
    version = importlib.metadata.version("deeptime")
    if version != "0.4.5":
        raise RuntimeError("isolated deeptime 0.4.5 is required")
    manifest = verify_contract(MANIFEST_PATH, CONTRACT_PATH)
    with np.load(CONTRACT_PATH, allow_pickle=False) as data:
        evaluations, model = evaluate(data, spec)
    gates = gate_lane(spec, evaluations)
    receipt = {
        "schema": "codex_ratchet.stage_interior_spectral_kinetic_discriminator.deeptime_receipt.v1",
        "sim_id": spec["sim_id"],
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "runtime": {
            "launcher": str(LAUNCHER_PATH),
            "launcher_samefile_as_runtime": LAUNCHER_PATH.samefile(sys.executable),
            "resolved_interpreter": sys.executable,
            "python": sys.version.split()[0],
            "deeptime": version,
            "numpy": np.__version__,
        },
        "contract": {
            "manifest_path": str(MANIFEST_PATH.relative_to(HERE)),
            "manifest_sha256": sha256(MANIFEST_PATH),
            "npz_path": str(CONTRACT_PATH.relative_to(HERE)),
            "npz_sha256": manifest["npz_sha256"],
        },
        "input_isolation": {
            "reads_pydmd_receipt": False,
            "reads_assembled_result": False,
            "shared_input_only": "hashed JSON/NPZ trajectory contract",
        },
        "tool_calls": [
            {
                "tool": "deeptime",
                "api": "deeptime.decomposition.VAMP(lagtime=1, dim=None, scaling=None).fit_fetch(trajectory)",
                "role": "claim_load_bearing linear kinetic feature extraction",
            }
        ],
        "tool_integration_depth": {"deeptime": "claim_load_bearing", "numpy": "control_only"},
        "model": model,
        "evaluations": evaluations,
        "gates": gates,
        "lane_pass": all(gates.values()),
        "demotion_condition": "Any clean gate failure, any noncollapsed control advantage, version/hash mismatch, fixed four-state latent request, or VAMP bypass demotes this lane to inconclusive.",
        "claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
    }
    write_json(RECEIPT_PATH, receipt)
    print(json.dumps({"receipt": str(RECEIPT_PATH), "lane_pass": receipt["lane_pass"], "gates": gates}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
