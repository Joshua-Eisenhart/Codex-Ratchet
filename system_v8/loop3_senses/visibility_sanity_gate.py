#!/usr/bin/env python3
"""Fail-closed loop-3 visibility sanity gate (foundation correction 1 only).

The gate reads the exact loop-2 world-source event log and diagnoses the
observation-conditioning -> density-update -> Pauli-readout path ported by
``system_v8/loop2_world/perception_intelligence_v0.py``.  It performs no
carrier comparison.  G5 only computes whether a later comparison is eligible.

Default output:
  system_v8/loop3_senses/results/visibility_sanity_gate_v3/receipt.json

The output directory is refuse-to-reuse.  If the original run is red, a
single targeted repair may be rerun with ``--fix-v1``; that receipt is written
under the original output directory at ``fix_v1/receipt.json`` and never
overwrites the original failure.

Run with:
  /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
    system_v8/loop3_senses/visibility_sanity_gate.py

Claim ceiling: scratch diagnostic; promotion_allowed=false; no carrier,
scaling, bridge, axis, manifold, physics, or formal-admission claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable

import numpy as np
from scipy.linalg import expm


REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = REPO / "system_v8" / "loop3_senses"
CARD = HERE / "LOOP3_FOUNDATION_CARD.md"
EVENTS = REPO / "system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl"
WORLD_RECEIPT = REPO / "system_v8/loop2_world/results/world_source/receipt.json"
ENGINE_INTERFACE = REPO / "system_v8/loop2_world/perception_intelligence_v0.py"
STAGE64 = REPO / "system_v8/nested_manifold/results/stage64/receipt.json"
DEFAULT_OUTDIR = HERE / "results" / "visibility_sanity_gate_v3"
SUPERSEDED_RECEIPTS = (
    (
        HERE / "results" / "visibility_sanity_gate" / "receipt.json",
        "pre-audit G3 averaged across k and allowed early information to hide late reconvergence",
    ),
    (
        HERE / "results" / "visibility_sanity_gate_v1" / "receipt.json",
        "v1 G3 used a disclosed factorized bit proxy rather than the card's joint object variable O",
    ),
    (
        HERE / "results" / "visibility_sanity_gate_v1" / "fix_v1" / "receipt.json",
        "v1 fix reran the disclosed factorized bit proxy; v2 replaces it with categorical full-word Holevo information",
    ),
    (
        HERE / "results" / "visibility_sanity_gate_v2" / "receipt.json",
        "v2 original used a composite explanatory status instead of the exact public status label runs",
    ),
    (
        HERE / "results" / "visibility_sanity_gate_v2" / "fix_v1" / "receipt.json",
        "v2 fix is mathematically accepted but superseded so both final receipts share the corrected exact-label source hash",
    ),
)

SEED = 20260719
N_BITS = 8
N_VIEWS = 6
N_OBJECTS = 64
N_TRAIN = 44
N_LABEL_PERMUTATIONS = 200
N_SIGN_FLIPS = 5000
MIN_MEMORY_FREE_PERCENT = 25

CLASSIFICATION = "diagnostic_only"
TOOL_INTEGRATION_DEPTH = "load_bearing"
TOOL_MANIFEST = {
    "numpy": (
        "load_bearing: event tensors, density-matrix algebra, exact Pauli "
        "expectations, ridge probes, permutation controls, and gate booleans"
    ),
    "scipy.linalg.expm": (
        "load_bearing: exact port of the loop-2 GKSL/unitary stage-channel "
        "construction; changing these channels changes G2-G4"
    ),
    "torch": "not_scoped: the diagnosed loop-2 QIT interface is NumPy/SciPy",
    "qutip": "not_scoped: no second QIT runtime is needed for correction 1",
}

FIX_CHOICES = ("none", "encoder_raw", "encoder_channel", "update_residual", "readout_quadratic")


class GateInputError(RuntimeError):
    """Raised when the exact owner inputs cannot support a valid gate run."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def memory_free_percent() -> int:
    proc = subprocess.run(
        ["memory_pressure"], capture_output=True, text=True, check=True
    )
    match = re.search(r"System-wide memory free percentage:\s*(\d+)%", proc.stdout)
    if match is None:
        raise GateInputError("memory_pressure did not report a free percentage")
    return int(match.group(1))


def refuse_to_reuse(outdir: Path) -> None:
    if outdir.exists():
        raise SystemExit(f"REFUSE-TO-REUSE: output dir already exists: {outdir}")
    outdir.mkdir(parents=True, exist_ok=False)


def predicates_from_event(event: dict[str, Any]) -> dict[str, str]:
    try:
        operations = event["payload"]["operations"]
        if len(operations) != 1:
            raise GateInputError("each event must contain exactly one operation")
        entity = operations[0]["payload"]
        claims = entity["claims"]
    except (KeyError, TypeError) as exc:
        raise GateInputError(f"event schema path missing: {exc}") from exc
    predicates = {str(item["predicate"]): str(item["object"]) for item in claims}
    required = {
        "has_object_id",
        "view_index",
        "probe_position",
        "probe_outcome",
        "occluded",
    }
    missing = required - predicates.keys()
    if missing:
        raise GateInputError(f"event is missing predicates: {sorted(missing)}")
    return predicates


def parse_event_log(path: Path) -> tuple[dict[str, dict[int, dict[int, str]]], dict[str, Any]]:
    log: dict[str, dict[int, dict[int, str]]] = {}
    forbidden = ("latent_word", "rule_id", "hidden_state", "rule_taps")
    line_count = 0
    with path.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            line_count += 1
            lowered = line.lower()
            leak = next((term for term in forbidden if term in lowered), None)
            if leak is not None:
                raise GateInputError(f"hidden-field leak {leak!r} on line {line_number}")
            event = json.loads(line)
            if event.get("type") != "graph.operations_applied" or event.get("schema_version") != 1:
                raise GateInputError(f"top-level schema mismatch on line {line_number}")
            predicates = predicates_from_event(event)
            object_id = predicates["has_object_id"]
            view = int(predicates["view_index"])
            position = int(predicates["probe_position"])
            outcome = predicates["probe_outcome"]
            if outcome not in {"0", "1", "withheld"}:
                raise GateInputError(f"invalid probe outcome {outcome!r} on line {line_number}")
            expected_occluded = "true" if outcome == "withheld" else "false"
            if predicates["occluded"].lower() != expected_occluded:
                raise GateInputError(f"occlusion flag disagrees with outcome on line {line_number}")
            slots = log.setdefault(object_id, {}).setdefault(view, {})
            if position in slots:
                raise GateInputError(
                    f"duplicate object/view/position slot {object_id}/{view}/{position}"
                )
            slots[position] = outcome

    expected_lines = N_OBJECTS * N_VIEWS * N_BITS
    if line_count != expected_lines:
        raise GateInputError(f"expected {expected_lines} events, found {line_count}")
    if len(log) != N_OBJECTS:
        raise GateInputError(f"expected {N_OBJECTS} objects, found {len(log)}")
    for object_id, views in log.items():
        if set(views) != set(range(N_VIEWS)):
            raise GateInputError(f"{object_id} does not contain all views")
        for view, slots in views.items():
            if set(slots) != set(range(N_BITS)):
                raise GateInputError(f"{object_id}/view{view} does not contain all positions")
    return log, {"events_validated": line_count, "hidden_field_leaks": 0}


def recover_full_views(
    log: dict[str, dict[int, dict[int, str]]],
    rule_family: dict[int, tuple[int, ...]],
) -> tuple[dict[str, list[tuple[int, ...]]], dict[str, Any]]:
    def step(bits: tuple[int, ...], rule_index: int) -> tuple[int, ...]:
        taps = rule_family[rule_index]
        return tuple(
            sum(bits[(position + offset) % N_BITS] for offset in taps) % 2
            for position in range(N_BITS)
        )

    def trajectory(word: int, rule_index: int) -> list[tuple[int, ...]]:
        bits = tuple((word >> position) & 1 for position in range(N_BITS))
        result = [bits]
        for _ in range(N_VIEWS - 1):
            result.append(step(result[-1], rule_index))
        return result

    hidden_space = [
        (word, rule_index)
        for word in range(2**N_BITS)
        for rule_index in sorted(rule_family)
    ]
    trajectories = {hidden: trajectory(*hidden) for hidden in hidden_space}
    full_views: dict[str, list[tuple[int, ...]]] = {}
    survivor_counts: dict[str, int] = {}
    for object_id in sorted(log):
        survivors = []
        for hidden in hidden_space:
            candidate = trajectories[hidden]
            if all(
                log[object_id][view][position] == "withheld"
                or int(log[object_id][view][position]) == candidate[view][position]
                for view in range(N_VIEWS)
                for position in range(N_BITS)
            ):
                survivors.append(hidden)
        survivor_counts[object_id] = len(survivors)
        if len(survivors) != 1:
            raise GateInputError(
                f"{object_id} has {len(survivors)} joint survivors; full visibility target unavailable"
            )
        full_views[object_id] = trajectories[survivors[0]]
    return full_views, {
        "candidate_space_size": len(hidden_space),
        "objects_uniquely_recovered": sum(count == 1 for count in survivor_counts.values()),
        "joint_survivor_min": min(survivor_counts.values()),
        "joint_survivor_max": max(survivor_counts.values()),
        "ground_truth_source": "exhaustive consistency over public rule family and visible events only",
    }


def train_test_objects(object_ids: list[str]) -> tuple[list[str], list[str]]:
    rng = np.random.default_rng(SEED)
    permutation = rng.permutation(len(object_ids))
    train = [object_ids[index] for index in permutation[:N_TRAIN]]
    test = [object_ids[index] for index in permutation[N_TRAIN:]]
    return train, test


def raw_view_features(
    log: dict[str, dict[int, dict[int, str]]],
    object_id: str,
    view: int,
    *,
    expanded: bool,
) -> np.ndarray:
    signed = np.zeros(N_BITS, dtype=float)
    visible = np.zeros(N_BITS, dtype=float)
    for position in range(N_BITS):
        outcome = log[object_id][view][position]
        if outcome != "withheld":
            signed[position] = 2.0 * int(outcome) - 1.0
            visible[position] = 1.0
    base = np.concatenate([signed, visible])
    if not expanded:
        return base
    interactions = np.array(
        [signed[left] * signed[right] for left in range(N_BITS) for right in range(left + 1, N_BITS)]
    )
    view_one_hot = np.eye(N_VIEWS, dtype=float)[view]
    return np.concatenate([base, interactions, view_one_hot])


def standardize(
    train: np.ndarray, test: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    mean = train.mean(axis=0)
    scale = train.std(axis=0)
    scale[scale < 1e-12] = 1.0
    return (train - mean) / scale, (test - mean) / scale


def ridge_predict(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    *,
    regularization: float = 1e-3,
) -> np.ndarray:
    train_z, test_z = standardize(train_x, test_x)
    train_aug = np.hstack([train_z, np.ones((train_z.shape[0], 1))])
    test_aug = np.hstack([test_z, np.ones((test_z.shape[0], 1))])
    penalty = regularization * np.eye(train_aug.shape[1])
    penalty[-1, -1] = 0.0
    weights = np.linalg.solve(
        train_aug.T @ train_aug + penalty,
        train_aug.T @ (2.0 * train_y.astype(float) - 1.0),
    )
    return test_aug @ weights >= 0.0


def bitwise_probe(
    feature_of: Callable[[str, int], np.ndarray],
    full_views: dict[str, list[tuple[int, ...]]],
    train_objects: list[str],
    test_objects: list[str],
    *,
    shuffled_train_labels: np.random.Generator | None = None,
) -> tuple[float, float, dict[str, np.ndarray], dict[str, np.ndarray]]:
    train_samples = [(object_id, view) for object_id in train_objects for view in range(N_VIEWS)]
    test_samples = [(object_id, view) for object_id in test_objects for view in range(N_VIEWS)]
    train_x = np.stack([feature_of(*sample) for sample in train_samples])
    test_x = np.stack([feature_of(*sample) for sample in test_samples])
    predictions = np.zeros((len(test_samples), N_BITS), dtype=bool)
    truths = np.array([full_views[object_id][view] for object_id, view in test_samples], dtype=bool)
    baselines = np.zeros_like(truths)
    for position in range(N_BITS):
        train_y = np.array(
            [full_views[object_id][view][position] for object_id, view in train_samples],
            dtype=bool,
        )
        fit_y = train_y.copy()
        if shuffled_train_labels is not None:
            fit_y = shuffled_train_labels.permutation(fit_y)
        predictions[:, position] = ridge_predict(train_x, fit_y, test_x)
        majority = bool(train_y.mean() >= 0.5)
        baselines[:, position] = majority
    accuracy = float(np.mean(predictions == truths))
    baseline_accuracy = float(np.mean(baselines == truths))
    prediction_by_object = {
        object_id: predictions[index * N_VIEWS : (index + 1) * N_VIEWS]
        for index, object_id in enumerate(test_objects)
    }
    baseline_by_object = {
        object_id: baselines[index * N_VIEWS : (index + 1) * N_VIEWS]
        for index, object_id in enumerate(test_objects)
    }
    truth_by_object = {
        object_id: truths[index * N_VIEWS : (index + 1) * N_VIEWS]
        for index, object_id in enumerate(test_objects)
    }
    return accuracy, baseline_accuracy, prediction_by_object, {
        "baseline": baseline_by_object,
        "truth": truth_by_object,
    }


def bitwise_probe_at_view(
    feature_of: Callable[[str, int], np.ndarray],
    full_views: dict[str, list[tuple[int, ...]]],
    train_objects: list[str],
    test_objects: list[str],
    view: int,
) -> tuple[float, float, dict[str, np.ndarray], dict[str, np.ndarray]]:
    train_x = np.stack([feature_of(object_id, view) for object_id in train_objects])
    test_x = np.stack([feature_of(object_id, view) for object_id in test_objects])
    truths = np.array([full_views[object_id][view] for object_id in test_objects], dtype=bool)
    predictions = np.zeros_like(truths)
    baselines = np.zeros_like(truths)
    for position in range(N_BITS):
        train_y = np.array(
            [full_views[object_id][view][position] for object_id in train_objects],
            dtype=bool,
        )
        predictions[:, position] = ridge_predict(train_x, train_y, test_x)
        baselines[:, position] = bool(train_y.mean() >= 0.5)
    prediction_by_object = {
        object_id: predictions[index : index + 1]
        for index, object_id in enumerate(test_objects)
    }
    baseline_by_object = {
        object_id: baselines[index : index + 1]
        for index, object_id in enumerate(test_objects)
    }
    truth_by_object = {
        object_id: truths[index : index + 1]
        for index, object_id in enumerate(test_objects)
    }
    return (
        float(np.mean(predictions == truths)),
        float(np.mean(baselines == truths)),
        prediction_by_object,
        {"baseline": baseline_by_object, "truth": truth_by_object},
    )


I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
PAULI1 = {"x": SX, "y": SY, "z": SZ}
RHO0 = np.zeros((4, 4), dtype=complex)
RHO0[0, 0] = 1.0


def kron(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.kron(left, right)


def vec(density: np.ndarray) -> np.ndarray:
    return density.reshape(-1, order="F")


def unvec(vector: np.ndarray) -> np.ndarray:
    return vector.reshape(4, 4, order="F")


def dissipator_superop(operator: np.ndarray) -> np.ndarray:
    product = operator.conj().T @ operator
    identity = np.eye(4, dtype=complex)
    return (
        kron(operator.conj(), operator)
        - 0.5 * kron(identity, product)
        - 0.5 * kron(product.T, identity)
    )


def unitary_superop(unitary: np.ndarray) -> np.ndarray:
    return kron(unitary.conj(), unitary)


def load_stage_channels(
    stage_receipt: dict[str, Any], *, encoder_channel_fix: bool
) -> tuple[dict[tuple[int, int], np.ndarray], list[dict[str, Any]]]:
    operating_pairs = stage_receipt["data"]["operating_pairs"]
    commutator_norms = stage_receipt["data"]["k1_commutator_norms"]
    stages = []
    for family in range(4):
        for orientation in (+1, -1):
            stage_id = f"family_{family}|L|f{'+' if orientation > 0 else '-'}1"
            pair = operating_pairs[stage_id]
            stages.append(
                {
                    "stage_id": stage_id,
                    "orientation": orientation,
                    "dissipator_axis": pair.split("|")[0][-1],
                    "hamiltonian_axis": pair.split("|")[1][-1],
                    "kappa": commutator_norms[stage_id][pair],
                }
            )

    dt, coupling, gamma0, dissipative_time = 0.5, 0.7, 0.05, 0.5
    channels: dict[tuple[int, int], np.ndarray] = {}
    for position, stage in enumerate(stages):
        for bit in (0, 1):
            hamiltonian_pauli = PAULI1[stage["hamiltonian_axis"]]
            dissipator_pauli = PAULI1[stage["dissipator_axis"]]
            theta = stage["kappa"] * dt * (2 * bit - 1)
            local_hamiltonian = (
                kron(hamiltonian_pauli, I2) if bit == 0 else kron(I2, hamiltonian_pauli)
            )
            unitary = expm(-1j * theta * local_hamiltonian) @ expm(
                -1j * coupling * kron(hamiltonian_pauli, hamiltonian_pauli)
            )
            lindblad = math.sqrt(gamma0 * (1 + 2 * bit)) * kron(dissipator_pauli, I2)
            unitary_channel = unitary_superop(unitary)
            dissipative_channel = expm(dissipative_time * dissipator_superop(lindblad))
            channel = (
                dissipative_channel @ unitary_channel
                if stage["orientation"] > 0
                else unitary_channel @ dissipative_channel
            )
            if encoder_channel_fix:
                # Minimal candidate for a collapsed outcome branch: append a
                # weak, explicit sign-conditioned rotation without replacing
                # the existing stage channel.
                observation_axis = kron(SZ, I2) if position % 2 == 0 else kron(I2, SZ)
                observation_unitary = expm(-1j * 0.125 * (2 * bit - 1) * observation_axis)
                channel = unitary_superop(observation_unitary) @ channel
            channels[(position, bit)] = channel
    return channels, stages


def apply_view(
    density: np.ndarray,
    bits: tuple[int, ...],
    channels: dict[tuple[int, int], np.ndarray],
) -> np.ndarray:
    result = density.copy()
    for position, bit in enumerate(bits):
        result = unvec(channels[(position, int(bit))] @ vec(result))
    return result


def density_trajectories(
    full_views: dict[str, list[tuple[int, ...]]],
    channels: dict[tuple[int, int], np.ndarray],
    *,
    update_residual_fix: bool,
) -> tuple[dict[str, list[np.ndarray]], dict[tuple[str, int], np.ndarray]]:
    trajectories: dict[str, list[np.ndarray]] = {}
    single_view_states: dict[tuple[str, int], np.ndarray] = {}
    for object_id in sorted(full_views):
        density = RHO0.copy()
        trajectories[object_id] = []
        for view, bits in enumerate(full_views[object_id]):
            view_local = apply_view(RHO0, bits, channels)
            single_view_states[(object_id, view)] = view_local
            persistent = apply_view(density, bits, channels)
            if update_residual_fix:
                # Minimal candidate for recurrent reconvergence: retain an
                # equal view-local residual computed by the existing update.
                density = 0.5 * persistent + 0.5 * view_local
            else:
                density = persistent
            trajectories[object_id].append(density.copy())
    return trajectories, single_view_states


def view_superoperator(
    bits: tuple[int, ...], channels: dict[tuple[int, int], np.ndarray]
) -> np.ndarray:
    result = np.eye(16, dtype=complex)
    for position, bit in enumerate(bits):
        result = channels[(position, int(bit))] @ result
    return result


def residual_update_superoperator(
    bits: tuple[int, ...], channels: dict[tuple[int, int], np.ndarray]
) -> np.ndarray:
    persistent = view_superoperator(bits, channels)
    view_local = apply_view(RHO0, bits, channels)
    replacement = np.outer(vec(view_local), vec(np.eye(4, dtype=complex)).conj())
    return 0.5 * persistent + 0.5 * replacement


def choi_cptp(channel: np.ndarray) -> tuple[float, float]:
    dimension = 4
    choi = np.zeros((dimension * dimension, dimension * dimension), dtype=complex)
    for row in range(dimension):
        for column in range(dimension):
            basis = np.zeros((dimension, dimension), dtype=complex)
            basis[row, column] = 1.0
            choi += kron(basis, unvec(channel @ vec(basis)))
    choi = 0.5 * (choi + choi.conj().T)
    min_eigenvalue = float(np.min(np.linalg.eigvalsh(choi)))
    trace_preserving = np.einsum("ikjk->ij", choi.reshape(dimension, dimension, dimension, dimension))
    return min_eigenvalue, float(np.max(np.abs(trace_preserving - np.eye(dimension))))


def physicality(states: list[np.ndarray]) -> dict[str, Any]:
    max_trace_deviation = 0.0
    max_hermiticity_deviation = 0.0
    min_eigenvalue = float("inf")
    violations = 0
    for density in states:
        trace_deviation = float(abs(np.trace(density) - 1.0))
        hermiticity_deviation = float(np.max(np.abs(density - density.conj().T)))
        state_min_eigenvalue = float(
            np.min(np.linalg.eigvalsh(0.5 * (density + density.conj().T)))
        )
        max_trace_deviation = max(max_trace_deviation, trace_deviation)
        max_hermiticity_deviation = max(max_hermiticity_deviation, hermiticity_deviation)
        min_eigenvalue = min(min_eigenvalue, state_min_eigenvalue)
        if not (
            trace_deviation < 1e-9
            and hermiticity_deviation < 1e-9
            and state_min_eigenvalue > -1e-10
        ):
            violations += 1
    return {
        "pass": violations == 0,
        "states_checked": len(states),
        "violations": violations,
        "max_trace_deviation": max_trace_deviation,
        "max_hermiticity_deviation": max_hermiticity_deviation,
        "min_eigenvalue": min_eigenvalue,
    }


def von_neumann_entropy(density: np.ndarray) -> float:
    eigenvalues = np.linalg.eigvalsh(0.5 * (density + density.conj().T))
    eigenvalues = eigenvalues[eigenvalues > 1e-14]
    return float(-np.sum(eigenvalues * np.log2(eigenvalues)))


def binary_holevo(states: list[np.ndarray], labels: np.ndarray) -> float:
    positives = int(labels.sum())
    count = len(labels)
    if positives == 0 or positives == count:
        return 0.0
    positive_density = sum(state for state, label in zip(states, labels) if label) / positives
    negative_density = sum(state for state, label in zip(states, labels) if not label) / (count - positives)
    positive_weight = positives / count
    average = positive_weight * positive_density + (1.0 - positive_weight) * negative_density
    return (
        von_neumann_entropy(average)
        - positive_weight * von_neumann_entropy(positive_density)
        - (1.0 - positive_weight) * von_neumann_entropy(negative_density)
    )


def categorical_holevo(states: list[np.ndarray], labels: np.ndarray) -> float:
    """Holevo chi for a repeated categorical object variable.

    Labels are the full current eight-bit words.  Repeated words provide
    non-singleton classes, so shuffling labels changes the class-conditional
    densities instead of leaving a unique-ID ensemble invariant.
    """
    count = len(labels)
    average = sum(states) / count
    value = von_neumann_entropy(average)
    for label in np.unique(labels):
        indices = np.flatnonzero(labels == label)
        conditional = sum(states[index] for index in indices) / len(indices)
        value -= (len(indices) / count) * von_neumann_entropy(conditional)
    return float(value)


PAULIS2 = [
    kron(left, right)
    for left_name, left in (("i", I2), ("x", SX), ("y", SY), ("z", SZ))
    for right_name, right in (("i", I2), ("x", SX), ("y", SY), ("z", SZ))
    if not (left_name == "i" and right_name == "i")
]


def pauli_features(density: np.ndarray, *, quadratic: bool) -> np.ndarray:
    linear = np.array(
        [float(np.real(np.trace(operator @ density))) for operator in PAULIS2],
        dtype=float,
    )
    if not quadratic:
        return linear
    interactions = np.array(
        [linear[left] * linear[right] for left in range(len(linear)) for right in range(left, len(linear))]
    )
    return np.concatenate([linear, interactions])


def object_block_sign_flip_pvalue(
    predictions: dict[str, np.ndarray],
    baseline: dict[str, np.ndarray],
    truths: dict[str, np.ndarray],
) -> tuple[float, list[float]]:
    differences = []
    for object_id in sorted(predictions):
        probe_correct = np.mean(predictions[object_id] == truths[object_id])
        baseline_correct = np.mean(baseline[object_id] == truths[object_id])
        differences.append(float(probe_correct - baseline_correct))
    observed = float(np.mean(differences))
    rng = np.random.default_rng(SEED + 31)
    null = np.empty(N_SIGN_FLIPS, dtype=float)
    differences_array = np.asarray(differences)
    for index in range(N_SIGN_FLIPS):
        signs = rng.choice(np.array([-1.0, 1.0]), size=len(differences))
        null[index] = float(np.mean(signs * differences_array))
    pvalue = float((1 + np.sum(null >= observed - 1e-15)) / (N_SIGN_FLIPS + 1))
    return pvalue, differences


def gate_diagnosis(checks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    failed = [gate for gate in ("G1", "G2", "G3", "G4", "G5") if not checks[gate]["pass"]]
    if not failed:
        return {
            "status": "no_failure",
            "first_failed_gate": None,
            "broken_component": None,
            "minimal_fix_candidate": None,
            "fix_v1_command": None,
        }
    first = failed[0]
    if first == "G1":
        component = "encoder_conditioning"
        fix = "expand the raw encoder with pairwise signed-bit interactions and an explicit view one-hot"
        mode = "encoder_raw"
    elif first == "G2" and checks["G2"]["metrics"]["min_channel_branch_frobenius"] <= 1e-8:
        component = "encoder_conditioning"
        fix = "append one weak explicit sign-conditioned Z rotation to each existing outcome branch"
        mode = "encoder_channel"
    elif first in {"G2", "G3"}:
        component = "update"
        fix = "add a 0.5 view-local residual from the existing update to the persistent density after each view"
        mode = "update_residual"
    else:
        component = "readout"
        fix = "augment the informationally complete 15-Pauli readout with fixed quadratic Pauli interactions"
        mode = "readout_quadratic"
    return {
        "status": "failure_diagnosed",
        "failed_gates": failed,
        "first_failed_gate": first,
        "broken_component": component,
        "minimal_fix_candidate": fix,
        "fix_v1_mode": mode,
        "fix_v1_command": (
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
            f"{HERE / 'visibility_sanity_gate.py'} --fix-v1 {mode}"
        ),
    }


def fatal_receipt(
    *,
    outdir: Path,
    fix_mode: str,
    memory_percent: int | None,
    error: Exception,
) -> dict[str, Any]:
    checks = {
        gate: {
            "pass": False,
            "criterion": "input/runtime precondition must succeed before gate evaluation",
            "metrics": {"fatal_error": f"{type(error).__name__}: {error}"},
        }
        for gate in ("G1", "G2", "G3", "G4", "G5")
    }
    return {
        "schema": "loop3_senses/visibility_sanity_gate/receipt_v1",
        "sim_id": "visibility_sanity_gate",
        "run_kind": "original" if fix_mode == "none" else "fix_v1",
        "fix_v1_mode": fix_mode,
        "classification": CLASSIFICATION,
        "runtime": {
            "python": sys.executable,
            "memory_free_percent": memory_percent,
            "minimum_required_percent": MIN_MEMORY_FREE_PERCENT,
        },
        "checks": checks,
        "check_bools": {gate: False for gate in checks},
        "all_pass": False,
        "findings": [f"FATAL INPUT/RUNTIME FAILURE: {type(error).__name__}: {error}"],
        "diagnosis": {
            "status": "failure_diagnosed",
            "first_failed_gate": "G1",
            "broken_component": "encoder_conditioning",
            "minimal_fix_candidate": "repair the named input/runtime precondition before altering the QIT path",
        },
        "carrier_comparison_eligible": False,
        "carrier_comparison_executed": False,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "fatal fail-closed diagnostic only; no visibility or carrier claim",
        "receipt_path": str(outdir / "receipt.json"),
    }


def run_gate(*, outdir: Path, fix_mode: str, memory_percent: int) -> dict[str, Any]:
    with WORLD_RECEIPT.open() as handle:
        world_receipt = json.load(handle)
    rule_family = {
        int(key): tuple(int(offset) for offset in offsets)
        for key, offsets in world_receipt["parameters"]["rule_family"].items()
    }
    log, schema_metrics = parse_event_log(EVENTS)
    full_views, recovery_metrics = recover_full_views(log, rule_family)
    object_ids = sorted(log)
    train_objects, test_objects = train_test_objects(object_ids)

    # G1: raw partial views must carry held-out bitwise object-state signal.
    expanded_raw = fix_mode == "encoder_raw"
    raw_feature = lambda object_id, view: raw_view_features(
        log, object_id, view, expanded=expanded_raw
    )
    raw_accuracy, raw_baseline, _, _ = bitwise_probe(
        raw_feature, full_views, train_objects, test_objects
    )
    g1_rng = np.random.default_rng(SEED + 11)
    raw_null = np.array(
        [
            bitwise_probe(
                raw_feature,
                full_views,
                train_objects,
                test_objects,
                shuffled_train_labels=g1_rng,
            )[0]
            for _ in range(N_LABEL_PERMUTATIONS)
        ]
    )
    raw_null_p95 = float(np.quantile(raw_null, 0.95))
    g1_pass = bool(raw_accuracy > max(raw_baseline, raw_null_p95) + 0.02)

    with STAGE64.open() as handle:
        stage_receipt = json.load(handle)
    channels, stages = load_stage_channels(
        stage_receipt, encoder_channel_fix=fix_mode == "encoder_channel"
    )
    trajectories, single_view_states = density_trajectories(
        full_views,
        channels,
        update_residual_fix=fix_mode == "update_residual",
    )

    # G2: isolate conditioning by starting each view from the same density.
    channel_branch_distances = [
        float(np.linalg.norm(channels[(position, 0)] - channels[(position, 1)]))
        for position in range(N_BITS)
    ]
    counterfactual_branch_distances: dict[int, list[float]] = {
        position: [] for position in range(N_BITS)
    }
    for object_id in object_ids:
        for view in range(N_VIEWS):
            parent = RHO0.copy()
            bits = full_views[object_id][view]
            for position in range(N_BITS):
                child_zero = unvec(channels[(position, 0)] @ vec(parent))
                child_one = unvec(channels[(position, 1)] @ vec(parent))
                counterfactual_branch_distances[position].append(
                    float(np.linalg.norm(child_zero - child_one))
                )
                parent = unvec(channels[(position, int(bits[position]))] @ vec(parent))
    counterfactual_position_medians = {
        position: float(np.median(distances))
        for position, distances in counterfactual_branch_distances.items()
    }
    keys = sorted(single_view_states)
    different_pattern_distances = []
    conditional_to_frozen = []
    frozen_state = apply_view(RHO0, tuple(0 for _ in range(N_BITS)), channels)
    for left_index, left_key in enumerate(keys):
        object_id, view = left_key
        state = single_view_states[left_key]
        conditional_to_frozen.append(float(np.linalg.norm(state - frozen_state)))
        left_bits = full_views[object_id][view]
        for right_key in keys[left_index + 1 :]:
            right_object, right_view = right_key
            if left_bits != full_views[right_object][right_view]:
                different_pattern_distances.append(
                    float(np.linalg.norm(state - single_view_states[right_key]))
                )
    all_states = [
        density
        for object_id in object_ids
        for density in trajectories[object_id]
    ] + list(single_view_states.values())
    physical = physicality(all_states)
    cptp = {
        f"position_{position}_bit_{bit}": {
            "choi_min_eigenvalue": choi_cptp(channel)[0],
            "trace_preserving_deviation": choi_cptp(channel)[1],
        }
        for (position, bit), channel in sorted(channels.items())
    }
    cptp_pass = all(
        item["choi_min_eigenvalue"] > -1e-9
        and item["trace_preserving_deviation"] < 1e-9
        for item in cptp.values()
    )
    residual_cptp: dict[str, dict[str, float]] = {}
    if fix_mode == "update_residual":
        unique_words = sorted(
            {
                tuple(bits)
                for object_id in object_ids
                for bits in full_views[object_id]
            }
        )
        for bits in unique_words:
            certificate = choi_cptp(residual_update_superoperator(bits, channels))
            word = sum(int(bit) << position for position, bit in enumerate(bits))
            residual_cptp[f"word_{word:03d}"] = {
                "choi_min_eigenvalue": certificate[0],
                "trace_preserving_deviation": certificate[1],
            }
    residual_cptp_pass = all(
        item["choi_min_eigenvalue"] > -1e-9
        and item["trace_preserving_deviation"] < 1e-9
        for item in residual_cptp.values()
    )
    median_pattern_distance = float(np.median(different_pattern_distances))
    fraction_separated = float(np.mean(np.asarray(different_pattern_distances) > 1e-8))
    mean_conditional_to_frozen = float(np.mean(conditional_to_frozen))
    deterministic_replay_max = max(
        float(
            np.linalg.norm(
                single_view_states[(object_id, view)]
                - apply_view(RHO0, full_views[object_id][view], channels)
            )
        )
        for object_id, view in keys[:32]
    )
    g2_pass = bool(
        physical["pass"]
        and cptp_pass
        and residual_cptp_pass
        and min(channel_branch_distances) > 1e-8
        and min(counterfactual_position_medians.values()) > 1e-8
        and median_pattern_distance > 1e-6
        and fraction_separated >= 0.95
        and mean_conditional_to_frozen > 1e-6
        and deterministic_replay_max < 1e-12
    )

    # G3: O is the joint current eight-bit word, not a unique simulator ID and
    # not an average of bitwise proxies.  Repeated word classes make the
    # shuffled-label control non-invariant.
    holevo_by_view = []
    labels_by_view: list[np.ndarray] = []
    states_by_view: list[list[np.ndarray]] = []
    class_counts_by_view: list[int] = []
    for view in range(N_VIEWS):
        states = [trajectories[object_id][view] for object_id in object_ids]
        states_by_view.append(states)
        labels = np.array(
            [
                sum(int(bit) << position for position, bit in enumerate(full_views[object_id][view]))
                for object_id in object_ids
            ],
            dtype=int,
        )
        labels_by_view.append(labels)
        class_counts_by_view.append(int(len(np.unique(labels))))
        holevo_by_view.append(categorical_holevo(states, labels))
    holevo_mean = float(np.mean(holevo_by_view))
    g3_rng = np.random.default_rng(SEED + 21)
    holevo_null = np.empty(N_LABEL_PERMUTATIONS, dtype=float)
    holevo_null_by_k = np.empty((N_LABEL_PERMUTATIONS, N_VIEWS), dtype=float)
    for permutation_index in range(N_LABEL_PERMUTATIONS):
        null_values = []
        for view in range(N_VIEWS):
            labels = g3_rng.permutation(labels_by_view[view])
            null_value = categorical_holevo(states_by_view[view], labels)
            null_values.append(null_value)
            holevo_null_by_k[permutation_index, view] = null_value
        holevo_null[permutation_index] = float(np.mean(null_values))
    holevo_null_p95 = float(np.quantile(holevo_null, 0.95))
    holevo_null_p95_by_k = [
        float(np.quantile(holevo_null_by_k[:, view], 0.95))
        for view in range(N_VIEWS)
    ]
    holevo_margin_by_k = [
        real - null_p95
        for real, null_p95 in zip(holevo_by_view, holevo_null_p95_by_k)
    ]
    g3_pass = bool(all(margin > 1e-6 for margin in holevo_margin_by_k))

    # G4: exact 15-Pauli readout, with a fixed quadratic expansion only in the
    # separately receipted readout fix candidate.
    quadratic_readout = fix_mode == "readout_quadratic"
    density_feature = lambda object_id, view: pauli_features(
        trajectories[object_id][view], quadratic=quadratic_readout
    )
    probe_accuracy, probe_baseline, probe_predictions, probe_aux = bitwise_probe(
        density_feature, full_views, train_objects, test_objects
    )
    probe_pvalue, object_differences = object_block_sign_flip_pvalue(
        probe_predictions,
        probe_aux["baseline"],
        probe_aux["truth"],
    )
    probe_by_k = []
    for view in range(N_VIEWS):
        view_accuracy, view_baseline, view_predictions, view_aux = bitwise_probe_at_view(
            density_feature,
            full_views,
            train_objects,
            test_objects,
            view,
        )
        view_pvalue, _ = object_block_sign_flip_pvalue(
            view_predictions,
            view_aux["baseline"],
            view_aux["truth"],
        )
        probe_by_k.append(
            {
                "k": view,
                "held_out_accuracy": view_accuracy,
                "computed_chance_accuracy": view_baseline,
                "margin": view_accuracy - view_baseline,
                "object_block_sign_flip_pvalue_descriptive": view_pvalue,
            }
        )
    g4_pass = bool(
        all(item["held_out_accuracy"] > item["computed_chance_accuracy"] for item in probe_by_k)
    )

    checks: dict[str, dict[str, Any]] = {
        "G1": {
            "name": "raw_views_have_object_predictive_information",
            "pass": g1_pass,
            "criterion": "held-out bitwise accuracy > max(train-selected chance, shuffled-label p95) + 0.02",
            "metrics": {
                "accuracy_type": "current-world-state bitwise accuracy",
                "raw_feature_dimension": int(raw_feature(object_ids[0], 0).shape[0]),
                "held_out_accuracy": raw_accuracy,
                "computed_chance_accuracy": raw_baseline,
                "shuffled_label_mean": float(raw_null.mean()),
                "shuffled_label_p95": raw_null_p95,
                "margin_over_strongest_control": raw_accuracy - max(raw_baseline, raw_null_p95),
                "label_permutations": N_LABEL_PERMUTATIONS,
            },
        },
        "G2": {
            "name": "observation_encoder_alters_density_conditionally",
            "pass": g2_pass,
            "criterion": "physical CPTP states; both outcome branches separate from the same parent at every position; >=95% different views separate; frozen and deterministic controls behave",
            "metrics": {
                "min_channel_branch_frobenius": min(channel_branch_distances),
                "channel_branch_frobenius_by_position": channel_branch_distances,
                "counterfactual_same_parent_median_frobenius_by_position": counterfactual_position_medians,
                "counterfactual_same_parent_min_position_median_frobenius": min(
                    counterfactual_position_medians.values()
                ),
                "different_view_median_density_frobenius": median_pattern_distance,
                "different_view_fraction_above_1e-8": fraction_separated,
                "mean_conditioned_to_all_zero_frozen_frobenius": mean_conditional_to_frozen,
                "deterministic_replay_max_frobenius": deterministic_replay_max,
                "physicality": physical,
                "cptp_pass": cptp_pass,
                "cptp_certificates": cptp,
                "residual_update_cptp_pass": residual_cptp_pass,
                "residual_update_cptp_certificates": residual_cptp,
            },
        },
        "G3": {
            "name": "holevo_object_information_above_shuffled_labels",
            "pass": g3_pass,
            "criterion": "for every k=0..5, categorical chi(full current eight-bit word O; rho_k) > that k's shuffled-label p95 by more than 1e-6 bits",
            "metrics": {
                "object_variable_definition": "categorical full current eight-bit word (0..255); simulator object IDs are excluded",
                "object_classes_by_k": class_counts_by_view,
                "chi_mean_bits": holevo_mean,
                "chi_mean_by_k": holevo_by_view,
                "shuffled_label_mean_bits": float(holevo_null.mean()),
                "shuffled_label_p95_bits": holevo_null_p95,
                "shuffled_label_p95_by_k_bits": holevo_null_p95_by_k,
                "margin_by_k_bits": holevo_margin_by_k,
                "all_k_above_control": g3_pass,
                "label_permutations": N_LABEL_PERMUTATIONS,
            },
        },
        "G4": {
            "name": "simple_density_probe_beats_chance_under_full_visibility",
            "pass": g4_pass,
            "criterion": "at every k=0..5, object-disjoint 15-Pauli ridge bitwise accuracy exceeds that k's train-selected chance; pooled and sign-flip values are descriptive",
            "metrics": {
                "accuracy_type": "current-world-state bitwise accuracy",
                "full_visibility": True,
                "readout": "15 Pauli expectations" + (" plus fixed quadratic interactions" if quadratic_readout else ""),
                "held_out_accuracy": probe_accuracy,
                "computed_chance_accuracy": probe_baseline,
                "margin": probe_accuracy - probe_baseline,
                "object_block_sign_flip_pvalue": probe_pvalue,
                "object_level_accuracy_differences": object_differences,
                "sign_flip_draws": N_SIGN_FLIPS,
                "per_k": probe_by_k,
                "all_k_beat_chance": g4_pass,
            },
        },
        "G5": {
            "name": "carrier_comparison_eligibility_only",
            "pass": False,
            "criterion": "G1-G4 all pass; this correction still performs zero carrier comparisons",
            "metrics": {
                "prerequisite_passes": {},
                "carrier_comparison_executed": False,
            },
        },
    }
    g5_prerequisites = {gate: bool(checks[gate]["pass"]) for gate in ("G1", "G2", "G3", "G4")}
    g5_pass = all(g5_prerequisites.values())
    checks["G5"]["pass"] = g5_pass
    checks["G5"]["metrics"]["prerequisite_passes"] = g5_prerequisites
    checks["G5"]["metrics"]["carrier_comparison_eligible"] = g5_pass

    all_pass = all(bool(checks[gate]["pass"]) for gate in checks)
    diagnosis = gate_diagnosis(checks)
    findings = [
        (
            f"G1 raw partial-view bitwise accuracy {raw_accuracy:.4f} vs computed chance "
            f"{raw_baseline:.4f} and shuffled-label p95 {raw_null_p95:.4f}."
        ),
        (
            f"G2 conditional path: minimum channel-branch distance {min(channel_branch_distances):.6g}; "
            f"different-view median density distance {median_pattern_distance:.6g}; "
            f"{fraction_separated:.3%} of different-view pairs separated above 1e-8."
        ),
        (
            f"G3 per-k chi margins over shuffled-label p95 "
            f"{[round(value, 8) for value in holevo_margin_by_k]}; every-k pass={g3_pass}."
        ),
        (
            f"G4 per-k full-visibility Pauli-probe margins over computed chance "
            f"{[round(item['margin'], 8) for item in probe_by_k]}; every-k pass={g4_pass} "
            f"(pooled accuracy {probe_accuracy:.4f}, pooled chance {probe_baseline:.4f})."
        ),
        (
            f"G5 carrier comparison eligibility={g5_pass}; carrier comparison executed=False."
        ),
    ]
    if diagnosis["status"] == "failure_diagnosed":
        findings.append(
            f"DIAGNOSIS: {diagnosis['first_failed_gate']} maps to {diagnosis['broken_component']}; "
            f"minimal fix candidate: {diagnosis['minimal_fix_candidate']}."
        )
    else:
        if fix_mode == "none":
            findings.append("DIAGNOSIS: no path component failed G1-G5; no fix_v1 run is warranted.")
        else:
            findings.append("DIAGNOSIS: no path component failed the fix_v1 rerun; no further fix is warranted.")

    original_receipt_path = DEFAULT_OUTDIR / "receipt.json"
    parent_receipt = None
    if fix_mode != "none":
        parent_receipt = {
            "path": str(original_receipt_path),
            "sha256": sha256_file(original_receipt_path),
        }

    superseded_receipts = [
        {
            "path": str(path),
            "sha256": sha256_file(path),
            "status": "superseded_retained_unchanged",
            "reason": reason,
        }
        for path, reason in SUPERSEDED_RECEIPTS
        if path.is_file()
    ]

    return {
        "schema": "loop3_senses/visibility_sanity_gate/receipt_v1",
        "sim_id": "visibility_sanity_gate",
        "version": "3.0.0",
        "date": "2026-07-19",
        "run_kind": "original" if fix_mode == "none" else "fix_v1",
        "fix_v1_mode": fix_mode,
        "parent_failure_receipt": parent_receipt,
        "superseded_receipts": superseded_receipts,
        "classification": CLASSIFICATION,
        "promotion_status": "diagnostic_only",
        "card_authority": str(CARD),
        "runtime": {
            "python": sys.executable,
            "python_version": sys.version.split()[0],
            "memory_free_percent": memory_percent,
            "minimum_required_percent": MIN_MEMORY_FREE_PERCENT,
            "torch_used": False,
            "qutip_used": False,
            "one_heavy_runtime_at_a_time": True,
        },
        "inputs": {
            "world_events": str(EVENTS),
            "world_events_sha256": sha256_file(EVENTS),
            "world_receipt": str(WORLD_RECEIPT),
            "world_receipt_sha256": sha256_file(WORLD_RECEIPT),
            "engine_interface": str(ENGINE_INTERFACE),
            "engine_interface_sha256": sha256_file(ENGINE_INTERFACE),
            "visibility_gate_source": str(HERE / "visibility_sanity_gate.py"),
            "visibility_gate_source_sha256": sha256_file(HERE / "visibility_sanity_gate.py"),
            "stage64_receipt": str(STAGE64),
            "stage64_receipt_sha256": sha256_file(STAGE64),
            "foundation_card": str(CARD),
            "foundation_card_sha256": sha256_file(CARD),
            "schema_metrics": schema_metrics,
            "ground_truth_recovery": recovery_metrics,
        },
        "protocol": {
            "scope": "LOOP3_FOUNDATION_CARD correction 1 only",
            "diagnosed_path": {
                "encoder_conditioning": "perception_intelligence_v0.py stage_superops(bit) and probe-position branch selection",
                "update": "perception_intelligence_v0.py run_engine_on_log sequential non-reset density update",
                "readout": "perception_intelligence_v0.py pauli_feats -> per-position ridge",
            },
            "engine_port": "exact NumPy/SciPy port of stage_list, stage_superops, run_engine_on_log full-visibility branch, and pauli_feats",
            "split": {
                "seed": SEED,
                "train_objects": train_objects,
                "test_objects": test_objects,
                "train_count": len(train_objects),
                "test_count": len(test_objects),
                "object_disjoint": not bool(set(train_objects) & set(test_objects)),
            },
            "full_visibility_definition": "all eight current-view bits reconstructed by visible-only joint-survivor consistency, then supplied to the existing outcome-conditioned stage path; the JSONL contains no literal 8/8-visible view",
            "ground_truth_boundary": "reconstructed from all visible events plus the public rule family; no hidden event field is read",
            "fix_boundary": "one structurally local 0.5 convex residual candidate selected from the original diagnosis; no coefficient minimality or optimality claim; no second fix loop",
        },
        "checks": checks,
        "check_bools": {gate: bool(payload["pass"]) for gate, payload in checks.items()},
        "all_pass": bool(all_pass),
        "findings": findings,
        "diagnosis": diagnosis,
        "carrier_comparison_eligible": bool(g5_pass),
        "carrier_comparison_executed": False,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "blocked_consumers": [
            "carrier comparison execution in correction 1",
            "carrier scaling",
            "loop-3 correction 2 or later",
            "bridge, axis, manifold, physics, or scientific promotion",
        ],
        "accepted_status_label": "passes local rerun" if all_pass else "runs",
        "claim_ceiling": (
            "passes local rerun of a bounded diagnostic gate only; no carrier comparison, scaling, promotion, or admission"
            if all_pass
            else "runs and retains a diagnostic failure; no visibility pass, carrier comparison, scaling, promotion, or admission"
        ),
        "receipt_path": str(outdir / "receipt.json"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path)
    parser.add_argument("--fix-v1", choices=FIX_CHOICES, default="none")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fix_mode = str(args.fix_v1)
    outdir = args.outdir
    if outdir is None:
        outdir = DEFAULT_OUTDIR if fix_mode == "none" else DEFAULT_OUTDIR / "fix_v1"
    outdir = outdir.resolve()

    if fix_mode != "none":
        original_receipt_path = DEFAULT_OUTDIR / "receipt.json"
        if not original_receipt_path.is_file():
            raise SystemExit(
                f"FIX-V1 REFUSED: original receipt does not exist: {original_receipt_path}"
            )
        with original_receipt_path.open() as handle:
            original_receipt = json.load(handle)
        if original_receipt.get("all_pass") is not False:
            raise SystemExit("FIX-V1 REFUSED: original receipt is not a retained failure")
        expected_mode = original_receipt.get("diagnosis", {}).get("fix_v1_mode")
        if expected_mode != fix_mode:
            raise SystemExit(
                f"FIX-V1 REFUSED: diagnosis requires {expected_mode!r}, got {fix_mode!r}"
            )

    refuse_to_reuse(outdir)
    memory_percent: int | None = None
    try:
        memory_percent = memory_free_percent()
        if memory_percent <= MIN_MEMORY_FREE_PERCENT:
            raise GateInputError(
                f"memory free {memory_percent}% is not greater than required {MIN_MEMORY_FREE_PERCENT}%"
            )
        receipt = run_gate(outdir=outdir, fix_mode=fix_mode, memory_percent=memory_percent)
    except Exception as error:  # write a fail-closed receipt for auditable input/runtime failures
        receipt = fatal_receipt(
            outdir=outdir,
            fix_mode=fix_mode,
            memory_percent=memory_percent,
            error=error,
        )

    receipt_path = outdir / "receipt.json"
    with receipt_path.open("x") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    print(json.dumps({
        "receipt": str(receipt_path),
        "run_kind": receipt["run_kind"],
        "checks": receipt["check_bools"],
        "all_pass": receipt["all_pass"],
        "diagnosis": receipt["diagnosis"],
        "carrier_comparison_eligible": receipt["carrier_comparison_eligible"],
        "carrier_comparison_executed": receipt["carrier_comparison_executed"],
        "promotion_allowed": receipt["promotion_allowed"],
    }, indent=2))
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
