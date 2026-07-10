#!/usr/bin/env python3
"""Build the source-faithful trajectory contract and run canonical PyDMD."""

from __future__ import annotations

import importlib.metadata
import json
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from pydmd import BOPDMD, HankelDMD

from contract_utils import gate_lane, load_json, sha256, summarize_classifier, write_json


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
STAGE_MOVEMENT_ALLOWED = False
TOOL_MANIFEST = {
    "PyDMD": {
        "used": True,
        "reason": "BOPDMD and HankelDMD directional propagators are the only PyDMD-lane classification features.",
    },
    "numpy": {
        "used": True,
        "reason": "Builds the finite trajectory fixture, exact permutation controls, and classifier arithmetic.",
    },
    "stage_interior_source_channels": {
        "used": True,
        "reason": "Imports the cited terrain and operator channels used to generate every trajectory.",
        "role_source": "upstream",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "PyDMD": "load_bearing",
    "numpy": "supportive",
    "stage_interior_source_channels": "load_bearing",
}

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
CONTRACT_PATH = HERE / "artifacts" / "trajectory_contract_v1.npz"
MANIFEST_PATH = HERE / "artifacts" / "trajectory_contract_v1.json"
RECEIPT_PATH = HERE / "receipts" / "pydmd_receipt.json"
LAUNCHER_PATH = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")


@dataclass(frozen=True)
class Slot:
    slot_id: str
    step: int
    terrain: int
    axis6_sign: str
    native_operator: str


def load_stage_base(path: Path) -> Any:
    module_dir = path.parent
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))
    import stage_interior_architecture_tournament_sim as stage_base

    return stage_base


def affine_from_channel(stage_base: Any, channel: Any) -> tuple[np.ndarray, np.ndarray]:
    zero = stage_base.bloch(channel(stage_base.dm(np.zeros(3))))
    columns = []
    for index in range(3):
        basis = np.zeros(3)
        basis[index] = 1.0
        columns.append(stage_base.bloch(channel(stage_base.dm(basis))) - zero)
    return np.column_stack(columns), zero


def load_fixture(spec: dict[str, Any]) -> tuple[list[Slot], dict[int, Any], dict[str, Any]]:
    stage_base = load_stage_base(REPO / spec["source_channel"])
    schedule = load_json(REPO / spec["source_schedule"])
    slots = [
        Slot(
            slot_id=row["slot_id"],
            step=int(row["step"]),
            terrain=stage_base.TERRAIN_INDEX[row["terrain"]],
            axis6_sign=row["axis6_sign"],
            native_operator=row["canonical_operator"],
        )
        for row in schedule
        if row["engine"] == spec["engine"]
    ]
    if len(slots) != 8 or len({slot.slot_id for slot in slots}) != 8:
        raise ValueError("expected exactly eight unique Type2_right source slots")
    terrains = {
        index: affine_from_channel(
            stage_base,
            lambda rho, index=index: stage_base.flow_terrain(index, rho),
        )
        for index in sorted({slot.terrain for slot in slots})
    }
    operators = {
        name: affine_from_channel(stage_base, stage_base.op(name))
        for name in ("Ti", "Te", "Fi", "Fe")
    }
    return slots, terrains, operators


def pooled_source_weights(spec: dict[str, Any]) -> np.ndarray:
    result = load_json(REPO / spec["source_learning_result"])
    candidates = {tuple(order) for order in spec["candidate_orders"]}
    rows = [
        np.asarray(row["learned_weights_native_first"], dtype=float)
        for row in result["runs"]
        if row["engine"] == spec["engine"] and tuple(row["cycle"]) in candidates
    ]
    expected = len(candidates) * len(result["engine_method_policy"]) + 2
    if len(rows) != 6:
        raise ValueError(f"expected six source weight rows for the two candidates, found {len(rows)}")
    pooled = np.mean(np.stack(rows), axis=0)
    if pooled.shape != (4,) or not np.all((pooled > 0.0) & (pooled <= 1.0)):
        raise ValueError("invalid pooled four-position source weights")
    return pooled


def phase_cycle(order: Sequence[str], native: str) -> tuple[str, ...]:
    index = order.index(native)
    return tuple(order[index:]) + tuple(order[:index])


def apply_affine(channel: tuple[np.ndarray, np.ndarray], vector: np.ndarray) -> np.ndarray:
    matrix, offset = channel
    return matrix @ vector + offset


def run_trajectory(
    initial: np.ndarray,
    order: Sequence[str],
    weights: np.ndarray,
    slots: Sequence[Slot],
    terrains: dict[int, Any],
    operators: dict[str, Any],
    repetitions: int,
) -> np.ndarray:
    value = initial.copy()
    trajectory = [value.copy()]
    for _ in range(repetitions):
        for slot in slots:
            for position, operator_name in enumerate(phase_cycle(order, slot.native_operator)):
                if slot.axis6_sign == "up":
                    moved = apply_affine(terrains[slot.terrain], apply_affine(operators[operator_name], value))
                elif slot.axis6_sign == "down":
                    moved = apply_affine(operators[operator_name], apply_affine(terrains[slot.terrain], value))
                else:
                    raise ValueError(slot.axis6_sign)
                value = (1.0 - weights[position]) * value + weights[position] * moved
                trajectory.append(value.copy())
    return np.asarray(trajectory, dtype=np.float64)


def make_split(
    seeds: Sequence[int],
    spec: dict[str, Any],
    fixture: tuple[list[Slot], dict[int, Any], dict[str, Any]],
    weights: np.ndarray,
) -> np.ndarray:
    slots, terrains, operators = fixture
    shape = (len(spec["candidate_orders"]), len(seeds), spec["probes_per_seed"])
    output = []
    radii = spec["probe_radii"]
    for order_index, order in enumerate(spec["candidate_orders"]):
        order_rows = []
        for seed in seeds:
            rng = np.random.default_rng(seed)
            seed_rows = []
            for probe_index in range(spec["probes_per_seed"]):
                initial = rng.normal(size=3)
                initial /= np.linalg.norm(initial)
                initial *= radii[probe_index % len(radii)]
                seed_rows.append(
                    run_trajectory(
                        initial,
                        order,
                        weights,
                        slots,
                        terrains,
                        operators,
                        spec["schedule_repetitions"],
                    )
                )
            order_rows.append(seed_rows)
        output.append(order_rows)
    array = np.asarray(output, dtype=np.float64)
    if array.shape[:3] != shape or array.shape[-1] != 3:
        raise ValueError(f"unexpected trajectory shape {array.shape}")
    return array


def control_indices(spec: dict[str, Any], trajectory_length: int) -> np.ndarray:
    shape = (len(spec["heldout_seeds"]), spec["probes_per_seed"], 3, trajectory_length)
    result = np.empty(shape, dtype=np.int64)
    block_size = spec["control_block_size"]
    if trajectory_length % block_size != 1:
        raise ValueError("trajectory length minus initial state must divide into exact control blocks")
    for seed_index, seed in enumerate(spec["heldout_seeds"]):
        for probe_index in range(spec["probes_per_seed"]):
            rng = np.random.default_rng(seed + 1009 * (probe_index + 1))
            result[seed_index, probe_index, 0] = rng.permutation(trajectory_length)
            tail = np.arange(1, trajectory_length).reshape(-1, block_size)
            within_block = np.stack([rng.permutation(block) for block in tail])
            result[seed_index, probe_index, 1] = np.concatenate(
                ([0], within_block.reshape(-1))
            )
            result[seed_index, probe_index, 2] = np.arange(trajectory_length - 1, -1, -1)
    return result


def spectral_features(trajectory: np.ndarray, delay: int) -> np.ndarray:
    snapshots = trajectory.T
    times = np.arange(snapshots.shape[1], dtype=float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bop = BOPDMD(svd_rank=0, num_trials=0, eig_sort="real").fit(snapshots, times)
        hankel = HankelDMD(
            svd_rank=0,
            exact=True,
            opt=True,
            d=delay,
            reconstruction_method="mean",
        ).fit(snapshots)

    bop_modes = np.asarray(bop.modes, dtype=complex)
    bop_step = bop_modes @ np.diag(np.exp(np.asarray(bop.eigs))) @ np.linalg.pinv(bop_modes)
    hankel_modes = np.asarray(hankel.modes, dtype=complex)
    hankel_step = hankel_modes @ np.diag(np.asarray(hankel.eigs)) @ np.linalg.pinv(hankel_modes)
    bop_reconstruction = np.asarray(bop.reconstructed_data).real
    hankel_reconstruction = np.asarray(hankel.reconstructed_data).real
    length = min(snapshots.shape[1], bop_reconstruction.shape[1], hankel_reconstruction.shape[1])
    errors = [
        float(np.mean((snapshots[:, :length] - bop_reconstruction[:, :length]) ** 2)),
        float(np.mean((snapshots[:, :length] - hankel_reconstruction[:, :length]) ** 2)),
    ]
    return np.concatenate(
        [
            bop_step.real.reshape(-1),
            bop_step.imag.reshape(-1),
            hankel_step.real.reshape(-1),
            hankel_step.imag.reshape(-1),
            np.asarray(errors),
        ]
    ).astype(np.float64)


def fit_centroids(features: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    center = np.mean(features, axis=0)
    scale = np.std(features, axis=0)
    scale[scale < 1.0e-10] = 1.0
    normalized = (features - center) / scale
    centroids = np.stack([np.mean(normalized[labels == label], axis=0) for label in (0, 1)])
    return center, scale, centroids


def distances(features: np.ndarray, center: np.ndarray, scale: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    normalized = (features - center) / scale
    return np.linalg.norm(normalized[:, None, :] - centroids[None, :, :], axis=2)


def flatten_labeled(array: np.ndarray) -> tuple[list[np.ndarray], np.ndarray]:
    trajectories = []
    labels = []
    for label in range(array.shape[0]):
        for seed_index in range(array.shape[1]):
            for probe_index in range(array.shape[2]):
                trajectories.append(array[label, seed_index, probe_index])
                labels.append(label)
    return trajectories, np.asarray(labels, dtype=int)


def evaluate(
    train: np.ndarray,
    heldout: np.ndarray,
    controls: np.ndarray,
    spec: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    train_trajectories, train_labels = flatten_labeled(train)
    train_features = np.stack([spectral_features(row, spec["hankel_delay"]) for row in train_trajectories])
    center, scale, centroids = fit_centroids(train_features, train_labels)
    heldout_trajectories, heldout_labels = flatten_labeled(heldout)
    evaluations: dict[str, Any] = {}

    def one(name: str, transform_index: int | None) -> None:
        rows = []
        cursor = 0
        for label in range(heldout.shape[0]):
            for seed_index in range(heldout.shape[1]):
                for probe_index in range(heldout.shape[2]):
                    row = heldout_trajectories[cursor]
                    if transform_index is not None:
                        row = row[controls[seed_index, probe_index, transform_index]]
                    rows.append(spectral_features(row, spec["hankel_delay"]))
                    cursor += 1
        evaluations[name] = summarize_classifier(
            heldout_labels,
            distances(np.stack(rows), center, scale, centroids),
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
    }
    return evaluations, model


def main() -> int:
    spec = load_json(SPEC_PATH)
    if importlib.metadata.version("pydmd") != "2025.8.1":
        raise RuntimeError("canonical PyDMD 2025.8.1 is required")
    fixture = load_fixture(spec)
    weights = pooled_source_weights(spec)
    train = make_split(spec["train_seeds"], spec, fixture, weights)
    heldout = make_split(spec["heldout_seeds"], spec, fixture, weights)
    controls = control_indices(spec, heldout.shape[-2])

    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        CONTRACT_PATH,
        train_trajectories=train,
        heldout_trajectories=heldout,
        control_indices=controls,
        pooled_weights=weights,
        candidate_orders=np.asarray(spec["candidate_orders"], dtype="U2"),
        train_seeds=np.asarray(spec["train_seeds"], dtype=np.int64),
        heldout_seeds=np.asarray(spec["heldout_seeds"], dtype=np.int64),
    )
    source_paths = [
        SPEC_PATH,
        HERE / "contract_utils.py",
        HERE / "build_contract_and_pydmd.py",
        HERE / "run_deeptime_vamp.py",
        HERE / "assemble_results.py",
        HERE / "validate_stage_interior_spectral_kinetic_discriminator_v0.py",
        HERE / "run_all.sh",
        REPO / spec["source_schedule"],
        REPO / spec["source_channel"],
        REPO / spec["source_learning_result"],
        REPO / spec["source_learning_code"],
    ]
    manifest = {
        "schema": "codex_ratchet.stage_interior_spectral_kinetic_discriminator.contract.v1",
        "sim_id": spec["sim_id"],
        "classification": CLASSIFICATION,
        "npz_path": str(CONTRACT_PATH.relative_to(HERE)),
        "npz_sha256": sha256(CONTRACT_PATH),
        "source_hashes": {
            str(path.relative_to(REPO) if path.is_relative_to(REPO) else path.relative_to(HERE)): sha256(path)
            for path in source_paths
        },
        "array_contract": {
            "train_trajectories": {"shape": list(train.shape), "dtype": str(train.dtype)},
            "heldout_trajectories": {"shape": list(heldout.shape), "dtype": str(heldout.dtype)},
            "control_indices": {"shape": list(controls.shape), "dtype": str(controls.dtype)},
        },
        "candidate_orders": spec["candidate_orders"],
        "weights_policy": "one pooled four-position vector across both candidate orders; order is the only candidate-varying input",
        "pooled_weights": weights.tolist(),
        "control_contract": {
            "temporal_shuffle": "full time-index permutation",
            "block_permutation": f"independent within-block permutation in exact {spec['control_block_size']}-sample blocks after preserving index zero",
            "reversal": "full temporal reversal",
            "marginal_preservation": "each control is an exact row permutation of each held-out trajectory",
        },
    }
    write_json(MANIFEST_PATH, manifest)
    evaluations, model = evaluate(train, heldout, controls, spec)
    gates = gate_lane(spec, evaluations)
    receipt = {
        "schema": "codex_ratchet.stage_interior_spectral_kinetic_discriminator.pydmd_receipt.v1",
        "sim_id": spec["sim_id"],
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "stage_movement_allowed": STAGE_MOVEMENT_ALLOWED,
        "runtime": {
            "launcher": str(LAUNCHER_PATH),
            "launcher_samefile_as_runtime": LAUNCHER_PATH.samefile(sys.executable),
            "resolved_interpreter": sys.executable,
            "python": sys.version.split()[0],
            "pydmd": importlib.metadata.version("pydmd"),
            "numpy": np.__version__,
        },
        "contract": {
            "manifest_path": str(MANIFEST_PATH.relative_to(HERE)),
            "manifest_sha256": sha256(MANIFEST_PATH),
            "npz_path": str(CONTRACT_PATH.relative_to(HERE)),
            "npz_sha256": sha256(CONTRACT_PATH),
        },
        "tool_calls": [
            {
                "tool": "PyDMD",
                "api": "pydmd.BOPDMD.fit(X, t)",
                "role": "claim_load_bearing spectral feature extraction",
            },
            {
                "tool": "PyDMD",
                "api": "pydmd.HankelDMD.fit(X)",
                "role": "claim_load_bearing delay-embedded spectral feature extraction",
            },
        ],
        "tool_integration_depth": {"PyDMD": "claim_load_bearing", "numpy": "control_only"},
        "model": model,
        "evaluations": evaluations,
        "gates": gates,
        "lane_pass": all(gates.values()),
        "demotion_condition": "Any clean gate failure, any noncollapsed control advantage, version/hash mismatch, or bypass of either PyDMD feature extractor demotes this lane to inconclusive.",
        "claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
    }
    write_json(RECEIPT_PATH, receipt)
    print(json.dumps({"receipt": str(RECEIPT_PATH), "lane_pass": receipt["lane_pass"], "gates": gates}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
