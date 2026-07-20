#!/usr/bin/env python3
"""Loop-3 senses iteration 2: a quantum-readout-fed slow memory.

The candidate state is ``Z_t = (rho_fast, m_slow, ...)``.  ``rho_fast`` is
rebuilt from the initial two-qubit density on every view.  ``m_slow`` is a
finite Bayesian posterior over public rule/initial-word hypotheses.  Its only
value-bearing input is the 15-Pauli readout of ``rho_fast``; observation masks
select which candidate emission is compared, but raw visible values and
withheld targets never enter the posterior update directly.

This is a refuse-to-reuse, diagnostic-only probe.  Checks may fail.  The
classical loop-2 twin is imported unchanged, and no outcome permits promotion.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np


REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = REPO / "system_v8" / "loop3_senses"
SOURCE = HERE / "senses_v2_slow_memory.py"
OUTDIR = HERE / "results" / "senses_v2_slow_memory"
RECEIPT_PATH = OUTDIR / "receipt.json"
TRAJECTORY_PATH = OUTDIR / "state_trajectories.json"
EVENTS = (
    REPO
    / "system_v8"
    / "loop2_world"
    / "results"
    / "world_source"
    / "events_dynamics_on.jsonl"
)
WORLD_RECEIPT = (
    REPO / "system_v8" / "loop2_world" / "results" / "world_source" / "receipt.json"
)
LOOP2_SOURCE = REPO / "system_v8" / "loop2_world" / "perception_intelligence_v0.py"
LOOP2_RECEIPT = (
    REPO / "system_v8" / "loop2_world" / "results" / "intelligence" / "receipt.json"
)
STAGE64 = REPO / "system_v8" / "nested_manifold" / "results" / "stage64" / "receipt.json"
VISIBILITY_SOURCE = HERE / "visibility_sanity_gate.py"
PARENT_SOURCE = HERE / "loop2_retest_fixed_senses.py"
PARENT_RECEIPT = HERE / "results" / "loop2_retest_fixed_senses" / "receipt.json"
FOUNDATION_CARD = HERE / "LOOP3_FOUNDATION_CARD.md"
OBJECT_CARD = HERE / "senses_v2_slow_memory_v43_card.json"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")

SEED = 20260719
N_BITS = 8
N_VIEWS = 6
N_BOOTSTRAPS = 5000
N_PERMUTATIONS = 200
MI_BINS = 5
MIN_MEMORY_FREE_PERCENT = 25
LIKELIHOOD_SIGMA_MULTIPLIER = 0.5
CLASSIFICATION = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing finite Bayesian posterior, density/readout algebra, "
            "ridge readout, object-block bootstrap, mutual information, and "
            "permutation controls"
        ),
    },
    "scipy.linalg.expm": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing through visibility_sanity_gate.load_stage_channels, "
            "which constructs every quantum measurement channel"
        ),
    },
    "torch": {
        "tried": False,
        "used": False,
        "reason": (
            "not scoped: this diagnostic isolates a slow classical register "
            "beside the exact diagnosed NumPy/SciPy two-qubit readout path"
        ),
    },
    "qutip": {
        "tried": False,
        "used": False,
        "reason": "not scoped: no second quantum runtime or carrier comparison is attempted",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy.linalg.expm": "load_bearing",
    "torch": None,
    "qutip": None,
}


class SlowMemoryError(RuntimeError):
    """Input, provenance, memory, or runtime error that must fail closed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def memory_free_percent() -> int:
    process = subprocess.run(
        ["memory_pressure"], capture_output=True, text=True, check=True
    )
    match = re.search(
        r"System-wide memory free percentage:\s*(\d+)%", process.stdout
    )
    if match is None:
        raise SlowMemoryError("memory_pressure did not report a free percentage")
    return int(match.group(1))


def refuse_to_reuse() -> None:
    if OUTDIR.exists():
        raise SlowMemoryError(f"REFUSE-TO-REUSE: outdir already exists: {OUTDIR}")


def write_fatal_receipt(message: str, memory_percent: int | None) -> None:
    receipt = {
        "schema": "loop3_senses/senses_v2_slow_memory/receipt_v1",
        "sim_id": "senses_v2_slow_memory",
        "version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "runtime": {
            "python": sys.executable,
            "required_python": str(SIM_PY),
            "memory_free_percent": memory_percent,
            "minimum_required_percent": MIN_MEMORY_FREE_PERCENT,
            "torch_used": False,
            "qutip_used": False,
        },
        "checks": {"fatal_preflight_or_runtime": False},
        "all_pass": False,
        "fatal_error": message,
        "divergence_log": [
            {
                "comparison": "requested slow-memory diagnostic versus fatal state",
                "status": "not_completed",
                "reason": message,
            }
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "fatal fail-closed diagnostic; no senses or promotion claim",
    }
    with RECEIPT_PATH.open("x") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)


def build_hypotheses(
    rule_family: dict[int, tuple[int, ...]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    words = []
    rules = []
    trajectories = []
    for word in range(2**N_BITS):
        initial = tuple((word >> position) & 1 for position in range(N_BITS))
        for rule in sorted(rule_family):
            views = [initial]
            taps = rule_family[rule]
            for _ in range(N_VIEWS - 1):
                previous = views[-1]
                views.append(
                    tuple(
                        sum(
                            previous[(position + offset) % N_BITS]
                            for offset in taps
                        )
                        % 2
                        for position in range(N_BITS)
                    )
                )
            words.append(word)
            rules.append(rule)
            trajectories.append(views)
    return (
        np.asarray(words, dtype=np.int16),
        np.asarray(rules, dtype=np.int8),
        np.asarray(trajectories, dtype=np.int8),
    )


def mask_integer(mask: tuple[bool, ...]) -> int:
    return sum((1 << position) for position, visible in enumerate(mask) if visible)


def density_payload(density: np.ndarray) -> list[list[list[float]]]:
    return [
        [[float(value.real), float(value.imag)] for value in row]
        for row in density
    ]


class QuantumReadoutBayes:
    """Finite Bayes register whose evidence is a quantum-readout vector."""

    def __init__(
        self,
        channels: dict[tuple[int, int], np.ndarray],
        visibility: Any,
        words: np.ndarray,
        rules: np.ndarray,
        trajectories: np.ndarray,
    ) -> None:
        self.channels = channels
        self.visibility = visibility
        self.words = words
        self.rules = rules
        self.trajectories = trajectories
        self.n_hypotheses = int(trajectories.shape[0])
        self.rule_values = sorted(int(value) for value in np.unique(rules))
        self._reset_candidate_cache: dict[tuple[int, int], np.ndarray] = {}
        self._broken_candidate_cache: dict[tuple[int, ...], list[np.ndarray]] = {}
        self.sigma = float("nan")

    def readout(self, density: np.ndarray) -> np.ndarray:
        return self.visibility.pauli_features(density, quadratic=False)

    def apply_values(
        self,
        density: np.ndarray,
        values: tuple[int | None, ...],
    ) -> np.ndarray:
        vector = self.visibility.vec(density)
        for position, value in enumerate(values):
            if value is not None:
                vector = self.channels[(position, int(value))] @ vector
        return self.visibility.unvec(vector)

    def actual_density(
        self,
        start: np.ndarray,
        getter: Callable[[int, int], str | None],
        view: int,
        *,
        frozen: bool,
    ) -> np.ndarray:
        values = tuple(
            None
            if getter(view, position) is None
            else (0 if frozen else int(getter(view, position)))
            for position in range(N_BITS)
        )
        return self.apply_values(start, values)

    def features_from_vectors(self, vectors: np.ndarray) -> np.ndarray:
        # visibility.vec uses Fortran order.  Reindex every row into C order so
        # batched 4x4 matrices preserve that exact convention.
        reorder = np.arange(16).reshape(4, 4, order="F").reshape(-1)
        densities = vectors[:, reorder].reshape(-1, 4, 4)
        operators = np.asarray(self.visibility.PAULIS2)
        return np.real(np.einsum("aij,hji->ha", operators, densities))

    def reset_candidate_readouts(
        self, view: int, mask: tuple[bool, ...]
    ) -> np.ndarray:
        key = (view, mask_integer(mask))
        cached = self._reset_candidate_cache.get(key)
        if cached is not None:
            return cached
        vectors = np.repeat(
            self.visibility.vec(self.visibility.RHO0)[None, :],
            self.n_hypotheses,
            axis=0,
        )
        for position, visible in enumerate(mask):
            if not visible:
                continue
            candidate_bits = self.trajectories[:, view, position]
            for bit in (0, 1):
                selected = candidate_bits == bit
                vectors[selected] = vectors[selected] @ self.channels[(position, bit)].T
        result = self.features_from_vectors(vectors)
        self._reset_candidate_cache[key] = result
        return result

    def broken_candidate_readouts(
        self, masks: tuple[tuple[bool, ...], ...]
    ) -> list[np.ndarray]:
        key = tuple(mask_integer(mask) for mask in masks)
        cached = self._broken_candidate_cache.get(key)
        if cached is not None:
            return cached
        vectors = np.repeat(
            self.visibility.vec(self.visibility.RHO0)[None, :],
            self.n_hypotheses,
            axis=0,
        )
        result = []
        for view, mask in enumerate(masks):
            for position, visible in enumerate(mask):
                if not visible:
                    continue
                candidate_bits = self.trajectories[:, view, position]
                for bit in (0, 1):
                    selected = candidate_bits == bit
                    vectors[selected] = (
                        vectors[selected] @ self.channels[(position, bit)].T
                    )
            result.append(self.features_from_vectors(vectors))
        self._broken_candidate_cache[key] = result
        return result

    def calibrate_sigma(
        self, masks_by_view: dict[int, set[tuple[bool, ...]]]
    ) -> dict[str, Any]:
        nearest = []
        unique_readout_counts = []
        for view in range(N_VIEWS):
            for mask in sorted(masks_by_view.get(view, set())):
                readouts = self.reset_candidate_readouts(view, mask)
                unique = np.unique(np.round(readouts, decimals=12), axis=0)
                unique_readout_counts.append(int(len(unique)))
                if len(unique) < 2:
                    continue
                squared = np.sum(
                    (unique[:, None, :] - unique[None, :, :]) ** 2, axis=2
                )
                squared[squared < 1e-24] = np.inf
                finite_nearest = np.sqrt(np.min(squared, axis=1))
                nearest.extend(float(value) for value in finite_nearest if np.isfinite(value))
        if not nearest:
            raise SlowMemoryError("quantum readout calibration found no distinct emissions")
        median_nearest = float(np.median(nearest))
        self.sigma = max(1e-9, LIKELIHOOD_SIGMA_MULTIPLIER * median_nearest)
        return {
            "calibration_uses_labels": False,
            "calibration_source": "median nearest-neighbor separation among finite candidate Pauli readouts",
            "sigma_multiplier": LIKELIHOOD_SIGMA_MULTIPLIER,
            "median_nearest_readout_distance": median_nearest,
            "sigma": self.sigma,
            "mask_view_pairs": sum(len(value) for value in masks_by_view.values()),
            "minimum_unique_readouts": min(unique_readout_counts),
            "maximum_unique_readouts": max(unique_readout_counts),
        }

    def posterior_summary(self, posterior: np.ndarray, view: int) -> np.ndarray:
        bit_marginals = posterior @ self.trajectories[:, view, :]
        rule_marginals = np.array(
            [float(np.sum(posterior[self.rules == rule])) for rule in self.rule_values]
        )
        positive = posterior[posterior > 0]
        entropy = float(-np.sum(positive * np.log2(positive)))
        normalized_entropy = entropy / math.log2(self.n_hypotheses)
        maximum = float(np.max(posterior))
        effective_fraction = float(1.0 / np.sum(posterior**2) / self.n_hypotheses)
        return np.concatenate(
            [bit_marginals, rule_marginals, [normalized_entropy, maximum, effective_fraction]]
        )

    def update_posterior(
        self,
        prior: np.ndarray,
        quantum_readout: np.ndarray,
        candidate_readouts: np.ndarray,
    ) -> np.ndarray:
        """Update m_slow from readouts only; no getter, value, or oracle enters."""
        squared_distance = np.sum(
            (candidate_readouts - quantum_readout[None, :]) ** 2, axis=1
        )
        log_posterior = np.log(np.maximum(prior, np.finfo(float).tiny))
        log_posterior += -0.5 * squared_distance / (self.sigma**2)
        maximum = float(np.max(log_posterior))
        posterior = np.exp(log_posterior - maximum)
        posterior /= np.sum(posterior)
        return posterior

    def episode(
        self,
        getter: Callable[[int, int], str | None],
        *,
        last_view: int = N_VIEWS - 1,
        update_mode: str = "reset_fast",
        frozen_actual: bool = False,
        reset_slow_each_view: bool = False,
        keep_posteriors: bool = False,
    ) -> list[dict[str, Any]]:
        if update_mode not in {"reset_fast", "original_broken"}:
            raise ValueError(f"unknown update_mode: {update_mode}")
        if not np.isfinite(self.sigma):
            raise SlowMemoryError("likelihood sigma must be calibrated before episodes")
        masks = tuple(
            tuple(getter(view, position) is not None for position in range(N_BITS))
            for view in range(last_view + 1)
        )
        if update_mode == "reset_fast":
            candidate_readouts = [
                self.reset_candidate_readouts(view, mask)
                for view, mask in enumerate(masks)
            ]
        else:
            candidate_readouts = self.broken_candidate_readouts(masks)

        posterior = np.full(self.n_hypotheses, 1.0 / self.n_hypotheses)
        persistent_density = self.visibility.RHO0.copy()
        states = []
        for view, mask in enumerate(masks):
            start = (
                self.visibility.RHO0
                if update_mode == "reset_fast"
                else persistent_density
            )
            density = self.actual_density(
                start, getter, view, frozen=frozen_actual
            )
            if update_mode == "original_broken":
                persistent_density = density
            quantum_readout = self.readout(density)
            if reset_slow_each_view:
                posterior = np.full(
                    self.n_hypotheses, 1.0 / self.n_hypotheses
                )
            posterior = self.update_posterior(
                posterior, quantum_readout, candidate_readouts[view]
            )
            slow_summary = self.posterior_summary(posterior, view)
            states.append(
                {
                    "view": view,
                    "mask": mask,
                    "rho_fast": density,
                    "quantum_readout": quantum_readout,
                    "m_slow_summary": slow_summary,
                    "joint_feature": np.concatenate([quantum_readout, slow_summary]),
                    "posterior": posterior.copy() if keep_posteriors else None,
                    "posterior_sum": float(np.sum(posterior)),
                }
            )
        return states


def empirical_mutual_information(
    beliefs: np.ndarray,
    bits: np.ndarray,
    *,
    bins: int,
    fixed_edges: np.ndarray | None = None,
) -> float:
    if len(beliefs) != len(bits) or len(bits) == 0:
        raise ValueError("mutual-information inputs must be nonempty and aligned")
    if len(np.unique(bits)) < 2:
        return 0.0
    edges = (
        np.unique(fixed_edges)
        if fixed_edges is not None
        else np.unique(np.quantile(beliefs, np.linspace(0.0, 1.0, bins + 1)))
    )
    if len(edges) < 3:
        return 0.0
    assigned = np.digitize(beliefs, edges[1:-1], right=True)
    total = float(len(bits))
    information = 0.0
    for bucket in range(len(edges) - 1):
        for bit in (0, 1):
            joint_count = int(np.sum((assigned == bucket) & (bits == bit)))
            if joint_count == 0:
                continue
            bucket_count = int(np.sum(assigned == bucket))
            bit_count = int(np.sum(bits == bit))
            joint = joint_count / total
            information += joint * math.log2(
                joint / ((bucket_count / total) * (bit_count / total))
            )
    return float(information)


def fit_mutual_information_edges(
    state_map: dict[str, list[dict[str, Any]]],
    train_slots: list[tuple[str, int, int]],
) -> dict[int, np.ndarray]:
    edges = {}
    for position in range(N_BITS):
        beliefs = np.array(
            [
                state_map[object_id][view]["m_slow_summary"][position]
                for object_id, view, query_position in train_slots
                if query_position == position
            ],
            dtype=float,
        )
        edges[position] = np.unique(
            np.quantile(beliefs, np.linspace(0.0, 1.0, MI_BINS + 1))
        )
    return edges


def persistence_mutual_information(
    state_map: dict[str, list[dict[str, Any]]],
    slots: list[tuple[str, int, int]],
    oracle: dict[str, list[tuple[int, ...]]],
    edges_by_position: dict[int, np.ndarray],
    *,
    permutation_rng: np.random.Generator | None = None,
) -> tuple[float, list[float]]:
    values = []
    for position in range(N_BITS):
        instances = [
            (object_id, view)
            for object_id, view, query_position in slots
            if query_position == position
        ]
        if len(instances) < 20:
            continue
        beliefs = np.array(
            [
                state_map[object_id][view]["m_slow_summary"][position]
                for object_id, view in instances
            ],
            dtype=float,
        )
        bits = np.array(
            [oracle[object_id][view][position] for object_id, view in instances],
            dtype=int,
        )
        if permutation_rng is not None:
            bits = permutation_rng.permutation(bits)
        values.append(
            empirical_mutual_information(
                beliefs,
                bits,
                bins=MI_BINS,
                fixed_edges=edges_by_position[position],
            )
        )
    return float(np.mean(values)), values


def bootstrap_accuracy_bundle(
    slots: list[tuple[str, int, int]],
    test_objects: list[str],
    correctness: dict[str, dict[tuple[str, int, int], bool]],
) -> dict[str, Any]:
    indices_by_object = {
        object_id: np.array(
            [index for index, slot in enumerate(slots) if slot[0] == object_id],
            dtype=int,
        )
        for object_id in test_objects
    }
    arrays = {
        name: np.array([values[slot] for slot in slots], dtype=bool)
        for name, values in correctness.items()
    }

    def metrics(indices: np.ndarray) -> dict[str, float]:
        candidate = float(np.mean(arrays["candidate"][indices]))
        twin = float(np.mean(arrays["twin"][indices]))
        chance = float(np.mean(arrays["chance"][indices]))
        reset = float(np.mean(arrays["slow_reset"][indices]))
        return {
            "candidate_accuracy": candidate,
            "twin_accuracy": twin,
            "chance_accuracy": chance,
            "slow_reset_accuracy": reset,
            "candidate_minus_twin": candidate - twin,
            "candidate_minus_chance": candidate - chance,
            "candidate_minus_slow_reset": candidate - reset,
        }

    all_indices = np.arange(len(slots), dtype=int)
    observed = metrics(all_indices)
    samples: dict[str, list[float]] = {key: [] for key in observed}
    rng = np.random.default_rng(SEED + 151)
    for _ in range(N_BOOTSTRAPS):
        sampled_objects = rng.choice(
            test_objects, size=len(test_objects), replace=True
        )
        sampled_indices = np.concatenate(
            [indices_by_object[object_id] for object_id in sampled_objects]
        )
        values = metrics(sampled_indices)
        for key, value in values.items():
            samples[key].append(value)
    return {
        "bootstrap_unit": "held-out object; all occluded slots stay together",
        "confidence_level": 0.95,
        "draws": N_BOOTSTRAPS,
        "seed": SEED + 151,
        "metrics": {
            key: {
                "estimate": value,
                "ci95": [
                    float(np.quantile(samples[key], 0.025)),
                    float(np.quantile(samples[key], 0.975)),
                ],
            }
            for key, value in observed.items()
        },
    }


def stage_cptp_summary(
    channels: dict[tuple[int, int], np.ndarray], visibility: Any
) -> dict[str, Any]:
    certificates = {}
    for (position, bit), channel in sorted(channels.items()):
        minimum, trace_deviation = visibility.choi_cptp(channel)
        certificates[f"position_{position}_bit_{bit}"] = {
            "choi_min_eigenvalue": minimum,
            "trace_preserving_deviation": trace_deviation,
        }
    return {
        "channel_count": len(certificates),
        "minimum_choi_eigenvalue": min(
            item["choi_min_eigenvalue"] for item in certificates.values()
        ),
        "maximum_trace_preserving_deviation": max(
            item["trace_preserving_deviation"] for item in certificates.values()
        ),
        "pass": all(
            item["choi_min_eigenvalue"] > -1e-9
            and item["trace_preserving_deviation"] < 1e-9
            for item in certificates.values()
        ),
        "certificates": certificates,
    }


def state_map_feature_hash(state_map: dict[str, list[dict[str, Any]]]) -> str:
    payload = {
        object_id: [
            [float(value) for value in state["joint_feature"]]
            for state in states
        ]
        for object_id, states in sorted(state_map.items())
    }
    return sha256_json(payload)


def run(memory_percent: int) -> dict[str, Any]:
    # These modules are imported only after the memory and interpreter gates.
    # Both are the exact parent path: NumPy/SciPy, never torch or qutip.
    sys.path.insert(0, str(REPO))
    from system_v8.loop3_senses import loop2_retest_fixed_senses as parent
    from system_v8.loop3_senses import visibility_sanity_gate as visibility

    tracked_inputs = [
        EVENTS,
        WORLD_RECEIPT,
        LOOP2_SOURCE,
        LOOP2_RECEIPT,
        STAGE64,
        VISIBILITY_SOURCE,
        PARENT_SOURCE,
        PARENT_RECEIPT,
        FOUNDATION_CARD,
        OBJECT_CARD,
        SOURCE,
    ]
    input_hashes_start = {str(path): sha256_file(path) for path in tracked_inputs}

    with WORLD_RECEIPT.open() as handle:
        world_receipt = json.load(handle)
    with PARENT_RECEIPT.open() as handle:
        parent_receipt = json.load(handle)
    with LOOP2_RECEIPT.open() as handle:
        original_receipt = json.load(handle)
    with STAGE64.open() as handle:
        stage_receipt = json.load(handle)

    rule_family = {
        int(key): tuple(int(offset) for offset in offsets)
        for key, offsets in world_receipt["parameters"]["rule_family"].items()
    }
    log, schema_metrics = visibility.parse_event_log(EVENTS)
    full_views, recovery_metrics = visibility.recover_full_views(log, rule_family)
    object_ids = sorted(log)
    train_objects, test_objects = visibility.train_test_objects(object_ids)
    train_object_set = set(train_objects)
    test_object_set = set(test_objects)
    channels, _ = visibility.load_stage_channels(
        stage_receipt, encoder_channel_fix=False
    )
    words, rules, hypotheses = build_hypotheses(rule_family)
    engine = QuantumReadoutBayes(
        channels, visibility, words, rules, hypotheses
    )

    def log_getter(object_id: str) -> Callable[[int, int], str | None]:
        return lambda view, position: (
            None
            if log[object_id][view][position] == "withheld"
            else log[object_id][view][position]
        )

    def full_getter(object_id: str) -> Callable[[int, int], str]:
        return lambda view, position: str(full_views[object_id][view][position])

    masks_by_view: dict[int, set[tuple[bool, ...]]] = {
        view: set() for view in range(N_VIEWS)
    }
    for object_id in object_ids:
        getter = log_getter(object_id)
        for view in range(N_VIEWS):
            masks_by_view[view].add(
                tuple(getter(view, position) is not None for position in range(N_BITS))
            )
    for view in range(N_VIEWS):
        masks_by_view[view].add(tuple(True for _ in range(N_BITS)))
        for position in range(N_BITS):
            masks_by_view[view].add(
                tuple(index != position for index in range(N_BITS))
            )
    likelihood_calibration = engine.calibrate_sigma(masks_by_view)

    main_states = {
        object_id: engine.episode(log_getter(object_id), keep_posteriors=True)
        for object_id in object_ids
    }
    broken_states = {
        object_id: engine.episode(
            log_getter(object_id),
            update_mode="original_broken",
            keep_posteriors=False,
        )
        for object_id in object_ids
    }
    frozen_states = {
        object_id: engine.episode(
            log_getter(object_id), frozen_actual=True, keep_posteriors=False
        )
        for object_id in object_ids
    }
    slow_reset_states = {
        object_id: engine.episode(
            log_getter(object_id),
            reset_slow_each_view=True,
            keep_posteriors=False,
        )
        for object_id in object_ids
    }
    full_states = {
        object_id: engine.episode(full_getter(object_id), keep_posteriors=False)
        for object_id in object_ids
    }

    slots = [
        (object_id, view, position)
        for object_id in object_ids
        for view in range(N_VIEWS)
        for position in range(N_BITS)
        if log[object_id][view][position] == "withheld"
    ]
    train_slots = [slot for slot in slots if slot[0] in train_object_set]
    test_slots = [slot for slot in slots if slot[0] in test_object_set]

    def truth(slot: tuple[str, int, int]) -> int:
        object_id, view, position = slot
        return int(full_views[object_id][view][position])

    train_bits = np.array([truth(slot) for slot in train_slots])
    pooled_majority = int(train_bits.mean() >= 0.5)
    position_majority = {}
    for position in range(N_BITS):
        bits = [truth(slot) for slot in train_slots if slot[2] == position]
        position_majority[position] = (
            int(np.mean(bits) >= 0.5) if bits else pooled_majority
        )
    pooled_train_accuracy = float(
        np.mean([truth(slot) == pooled_majority for slot in train_slots])
    )
    position_train_accuracy = float(
        np.mean(
            [truth(slot) == position_majority[slot[2]] for slot in train_slots]
        )
    )
    use_position_majority = position_train_accuracy > pooled_train_accuracy
    computed_baseline = float(
        np.mean(
            [
                truth(slot)
                == (
                    position_majority[slot[2]]
                    if use_position_majority
                    else pooled_majority
                )
                for slot in test_slots
            ]
        )
    )

    main_feature = lambda slot: main_states[slot[0]][slot[1]]["joint_feature"]
    broken_feature = lambda slot: broken_states[slot[0]][slot[1]]["joint_feature"]
    frozen_feature = lambda slot: frozen_states[slot[0]][slot[1]]["joint_feature"]
    slow_reset_feature = lambda slot: slow_reset_states[slot[0]][slot[1]][
        "joint_feature"
    ]
    main_accuracy, main_predictions, main_correct = parent.decode_per_position(
        main_feature, train_slots, test_slots, truth, pooled_majority
    )
    broken_accuracy, _, broken_correct = parent.decode_per_position(
        broken_feature, train_slots, test_slots, truth, pooled_majority
    )
    frozen_accuracy, _, frozen_correct = parent.decode_per_position(
        frozen_feature, train_slots, test_slots, truth, pooled_majority
    )
    slow_reset_accuracy, _, slow_reset_correct = parent.decode_per_position(
        slow_reset_feature, train_slots, test_slots, truth, pooled_majority
    )

    twin_feature = lambda slot: parent.twin_features(
        log_getter(slot[0]), slot[1], slot[2], rule_family
    )
    twin_accuracy, twin_predictions, twin_correct, twin_tree = parent.twin_run(
        twin_feature, train_slots, test_slots, truth
    )
    twin_nodes, twin_depth = parent.tree_size(twin_tree)
    twin_feature_schema = sorted(twin_feature(train_slots[0]))
    twin_feature_fingerprint = sha256_json(
        [
            {"slot": slot, "features": twin_feature(slot)}
            for slot in train_slots + test_slots
        ]
    )
    twin_prediction_fingerprint = sha256_json(
        [
            {"slot": slot, "prediction": twin_predictions[slot]}
            for slot in test_slots
        ]
    )
    complementarity = parent.bootstrap_complementarity(
        test_slots, main_correct, twin_correct, test_objects
    )
    episodes = parent.episode_table(
        test_slots, main_correct, twin_correct, test_objects
    )

    chance_correct = {
        slot: truth(slot)
        == (
            position_majority[slot[2]]
            if use_position_majority
            else pooled_majority
        )
        for slot in test_slots
    }
    accuracy_bootstrap = bootstrap_accuracy_bundle(
        test_slots,
        test_objects,
        {
            "candidate": main_correct,
            "twin": twin_correct,
            "chance": chance_correct,
            "slow_reset": slow_reset_correct,
        },
    )

    main_mi_edges = fit_mutual_information_edges(main_states, train_slots)
    broken_mi_edges = fit_mutual_information_edges(broken_states, train_slots)
    frozen_mi_edges = fit_mutual_information_edges(frozen_states, train_slots)
    slow_reset_mi_edges = fit_mutual_information_edges(
        slow_reset_states, train_slots
    )
    main_mi, main_mi_by_position = persistence_mutual_information(
        main_states, test_slots, full_views, main_mi_edges
    )
    broken_mi, broken_mi_by_position = persistence_mutual_information(
        broken_states, test_slots, full_views, broken_mi_edges
    )
    frozen_mi, frozen_mi_by_position = persistence_mutual_information(
        frozen_states, test_slots, full_views, frozen_mi_edges
    )
    slow_reset_mi, slow_reset_mi_by_position = persistence_mutual_information(
        slow_reset_states, test_slots, full_views, slow_reset_mi_edges
    )
    main_mi_rng = np.random.default_rng(SEED + 401)
    broken_mi_rng = np.random.default_rng(SEED + 402)
    frozen_mi_rng = np.random.default_rng(SEED + 403)
    main_mi_null = np.array(
        [
            persistence_mutual_information(
                main_states,
                test_slots,
                full_views,
                main_mi_edges,
                permutation_rng=main_mi_rng,
            )[0]
            for _ in range(N_PERMUTATIONS)
        ]
    )
    broken_mi_null = np.array(
        [
            persistence_mutual_information(
                broken_states,
                test_slots,
                full_views,
                broken_mi_edges,
                permutation_rng=broken_mi_rng,
            )[0]
            for _ in range(N_PERMUTATIONS)
        ]
    )
    frozen_mi_null = np.array(
        [
            persistence_mutual_information(
                frozen_states,
                test_slots,
                full_views,
                frozen_mi_edges,
                permutation_rng=frozen_mi_rng,
            )[0]
            for _ in range(N_PERMUTATIONS)
        ]
    )

    full_context_main: dict[tuple[str, int, int], np.ndarray] = {}
    full_context_broken: dict[tuple[str, int, int], np.ndarray] = {}
    full_context_main_states: dict[tuple[str, int, int], dict[str, Any]] = {}
    for slot in train_slots + test_slots:
        object_id, query_view, query_position = slot

        def query_getter(view: int, position: int) -> str | None:
            if view == query_view and position == query_position:
                return None
            return str(full_views[object_id][view][position])

        candidate_state = engine.episode(
            query_getter, last_view=query_view, keep_posteriors=False
        )[-1]
        broken_state = engine.episode(
            query_getter,
            last_view=query_view,
            update_mode="original_broken",
            keep_posteriors=False,
        )[-1]
        full_context_main[slot] = candidate_state["joint_feature"]
        full_context_broken[slot] = broken_state["joint_feature"]
        full_context_main_states[slot] = candidate_state

    full_context_accuracy, _, full_context_correct = parent.decode_per_position(
        lambda slot: full_context_main[slot],
        train_slots,
        test_slots,
        truth,
        pooled_majority,
    )
    full_context_broken_accuracy, _, full_context_broken_correct = (
        parent.decode_per_position(
            lambda slot: full_context_broken[slot],
            train_slots,
            test_slots,
            truth,
            pooled_majority,
        )
    )
    full_context_per_view = []
    for view in range(N_VIEWS):
        view_slots = [slot for slot in test_slots if slot[1] == view]
        view_baseline = float(
            np.mean(
                [
                    truth(slot)
                    == (
                        position_majority[slot[2]]
                        if use_position_majority
                        else pooled_majority
                    )
                    for slot in view_slots
                ]
            )
        )
        candidate_accuracy = float(
            np.mean([full_context_correct[slot] for slot in view_slots])
        )
        broken_view_accuracy = float(
            np.mean([full_context_broken_correct[slot] for slot in view_slots])
        )
        full_context_per_view.append(
            {
                "k": view,
                "test_slots": len(view_slots),
                "candidate_accuracy": candidate_accuracy,
                "original_broken_accuracy": broken_view_accuracy,
                "computed_chance_accuracy": view_baseline,
                "candidate_margin": candidate_accuracy - view_baseline,
                "candidate_pass": bool(candidate_accuracy > view_baseline),
            }
        )

    def full_visibility_metrics() -> dict[str, Any]:
        feature = lambda object_id, view: full_states[object_id][view]["joint_feature"]
        accuracy, baseline, _, _ = visibility.bitwise_probe(
            feature, full_views, train_objects, test_objects
        )
        per_view = []
        for view in range(N_VIEWS):
            view_accuracy, view_baseline, _, _ = visibility.bitwise_probe_at_view(
                feature, full_views, train_objects, test_objects, view
            )
            per_view.append(
                {
                    "k": view,
                    "held_out_accuracy": view_accuracy,
                    "computed_chance_accuracy": view_baseline,
                    "margin": view_accuracy - view_baseline,
                    "pass": bool(view_accuracy > view_baseline),
                }
            )
        return {
            "accuracy_type": "current-world-state bitwise accuracy",
            "full_visibility": True,
            "readout": "joint 15-Pauli rho_fast features plus m_slow marginals with object-disjoint per-bit ridge",
            "held_out_accuracy": accuracy,
            "computed_chance_accuracy": baseline,
            "margin": accuracy - baseline,
            "per_k": per_view,
            "all_k_beat_chance": bool(all(item["pass"] for item in per_view)),
        }

    full_visibility = full_visibility_metrics()

    shuffle_rng = np.random.default_rng(SEED + 31)
    shuffled_engine_accuracy = []
    shuffled_twin_accuracy = []
    shuffled_union_accuracy = []
    for _ in range(N_PERMUTATIONS):
        label_map = {}
        for position in range(N_BITS):
            position_slots = [slot for slot in train_slots if slot[2] == position]
            labels = np.array([truth(slot) for slot in position_slots], dtype=int)
            for slot, label in zip(position_slots, shuffle_rng.permutation(labels)):
                label_map[slot] = int(label)
        engine_accuracy, _, engine_correct = parent.decode_per_position(
            main_feature,
            train_slots,
            test_slots,
            truth,
            pooled_majority,
            train_label_map=label_map,
        )
        twin_null_accuracy, _, twin_null_correct, _ = parent.twin_run(
            twin_feature,
            train_slots,
            test_slots,
            truth,
            train_label_map=label_map,
        )
        shuffled_engine_accuracy.append(engine_accuracy)
        shuffled_twin_accuracy.append(twin_null_accuracy)
        shuffled_union_accuracy.append(
            float(
                np.mean(
                    [engine_correct[slot] or twin_null_correct[slot] for slot in test_slots]
                )
            )
        )
    shuffled_engine_accuracy = np.asarray(shuffled_engine_accuracy)
    shuffled_twin_accuracy = np.asarray(shuffled_twin_accuracy)
    shuffled_union_accuracy = np.asarray(shuffled_union_accuracy)
    engine_null_p95 = float(np.quantile(shuffled_engine_accuracy, 0.95))
    twin_null_p95 = float(np.quantile(shuffled_twin_accuracy, 0.95))
    union_null_p95 = float(np.quantile(shuffled_union_accuracy, 0.95))
    union_accuracy = complementarity["metrics"]["union_accuracy"]["estimate"]

    # Leak counterfactual: hidden evaluation targets are flipped but the main
    # engine is rerun from the unchanged masked log.  A separate deliberately
    # unmasked sentinel proves that the test would notice target access.
    counterfactual_full_views = {
        object_id: [
            tuple(
                1 - int(bit)
                if log[object_id][view][position] == "withheld"
                else int(bit)
                for position, bit in enumerate(full_views[object_id][view])
            )
            for view in range(N_VIEWS)
        ]
        for object_id in object_ids
    }
    counterfactual_states = {
        object_id: engine.episode(log_getter(object_id), keep_posteriors=False)
        for object_id in reversed(object_ids)
    }
    candidate_feature_hash = state_map_feature_hash(main_states)
    counterfactual_feature_hash = state_map_feature_hash(counterfactual_states)
    counterfactual_truth_hash_differs = sha256_json(full_views) != sha256_json(
        counterfactual_full_views
    )
    target_flip_rho_max_delta = 0.0
    target_flip_slow_max_delta = 0.0
    target_flip_joint_max_delta = 0.0
    for object_id in object_ids:
        for original, counterfactual in zip(
            main_states[object_id], counterfactual_states[object_id]
        ):
            target_flip_rho_max_delta = max(
                target_flip_rho_max_delta,
                float(np.max(np.abs(original["rho_fast"] - counterfactual["rho_fast"]))),
            )
            target_flip_slow_max_delta = max(
                target_flip_slow_max_delta,
                float(
                    np.max(
                        np.abs(
                            original["m_slow_summary"]
                            - counterfactual["m_slow_summary"]
                        )
                    )
                ),
            )
            target_flip_joint_max_delta = max(
                target_flip_joint_max_delta,
                float(
                    np.max(
                        np.abs(
                            original["joint_feature"]
                            - counterfactual["joint_feature"]
                        )
                    )
                ),
            )

    prefix_max_delta = 0.0
    for object_id in object_ids:
        ordinary_getter = log_getter(object_id)
        for cutoff in range(N_VIEWS):

            def prefix_getter(view: int, position: int, cutoff: int = cutoff) -> str | None:
                if view > cutoff:
                    raise SlowMemoryError("causal-prefix probe accessed a future view")
                return ordinary_getter(view, position)

            prefix_state = engine.episode(
                prefix_getter, last_view=cutoff, keep_posteriors=False
            )[-1]
            prefix_max_delta = max(
                prefix_max_delta,
                float(
                    np.max(
                        np.abs(
                            prefix_state["joint_feature"]
                            - main_states[object_id][cutoff]["joint_feature"]
                        )
                    )
                ),
            )

    sentinel_changed = 0
    sentinel_slow_changed = 0
    sentinel_fast_max_delta = 0.0
    sentinel_slow_max_delta = 0.0
    sentinel_joint_max_delta = 0.0
    for slot in test_slots:
        object_id, query_view, query_position = slot
        ordinary = main_states[object_id][query_view]["joint_feature"]

        def leaked_getter(view: int, position: int) -> str | None:
            if view == query_view and position == query_position:
                return str(full_views[object_id][view][position])
            return log_getter(object_id)(view, position)

        leaked_state = engine.episode(
            leaked_getter, last_view=query_view, keep_posteriors=False
        )[-1]
        fast_delta = float(
            np.max(
                np.abs(
                    leaked_state["quantum_readout"]
                    - main_states[object_id][query_view]["quantum_readout"]
                )
            )
        )
        slow_delta = float(
            np.max(
                np.abs(
                    leaked_state["m_slow_summary"]
                    - main_states[object_id][query_view]["m_slow_summary"]
                )
            )
        )
        joint_delta = float(
            np.max(np.abs(leaked_state["joint_feature"] - ordinary))
        )
        sentinel_fast_max_delta = max(sentinel_fast_max_delta, fast_delta)
        sentinel_slow_max_delta = max(sentinel_slow_max_delta, slow_delta)
        sentinel_joint_max_delta = max(sentinel_joint_max_delta, joint_delta)
        sentinel_changed += int(joint_delta > 1e-12)
        sentinel_slow_changed += int(slow_delta > 1e-12)

    physicality = {
        "candidate_reset_fast": visibility.physicality(
            [state["rho_fast"] for states in main_states.values() for state in states]
        ),
        "frozen_reset_fast": visibility.physicality(
            [state["rho_fast"] for states in frozen_states.values() for state in states]
        ),
        "original_broken_fast": visibility.physicality(
            [state["rho_fast"] for states in broken_states.values() for state in states]
        ),
        "full_visibility_reset_fast": visibility.physicality(
            [state["rho_fast"] for states in full_states.values() for state in states]
        ),
        "target_masked_full_context_reset_fast": visibility.physicality(
            [state["rho_fast"] for state in full_context_main_states.values()]
        ),
    }
    cptp = stage_cptp_summary(channels, visibility)

    rho_reset_replay_max = 0.0
    bayes_replay_max = 0.0
    posterior_minimum = 1.0
    persistence_register_delta = 0.0
    for object_id in object_ids:
        getter = log_getter(object_id)
        replay_posterior = np.full(
            engine.n_hypotheses, 1.0 / engine.n_hypotheses
        )
        for view, state in enumerate(main_states[object_id]):
            replay_density = engine.actual_density(
                visibility.RHO0, getter, view, frozen=False
            )
            rho_reset_replay_max = max(
                rho_reset_replay_max,
                float(np.max(np.abs(replay_density - state["rho_fast"]))),
            )
            mask = tuple(bool(value) for value in state["mask"])
            replay_posterior = engine.update_posterior(
                replay_posterior,
                state["quantum_readout"],
                engine.reset_candidate_readouts(view, mask),
            )
            bayes_replay_max = max(
                bayes_replay_max,
                float(np.max(np.abs(replay_posterior - state["posterior"]))),
            )
            posterior_minimum = min(
                posterior_minimum, float(np.min(state["posterior"]))
            )
            if view > 0:
                persistence_register_delta = max(
                    persistence_register_delta,
                    float(
                        np.max(
                            np.abs(
                                state["m_slow_summary"]
                                - slow_reset_states[object_id][view]["m_slow_summary"]
                            )
                        )
                    ),
                )

    masked_hypothesis_readout_max_delta = 0.0
    discriminating_readouts: tuple[
        np.ndarray, np.ndarray, np.ndarray, np.ndarray
    ] | None = None
    for view in range(N_VIEWS):
        for mask in masks_by_view[view]:
            candidate_readouts = engine.reset_candidate_readouts(view, mask)
            groups: dict[tuple[int, ...], list[int]] = {}
            visible_positions = [
                position for position, visible in enumerate(mask) if visible
            ]
            for index in range(engine.n_hypotheses):
                visible_values = tuple(
                    int(hypotheses[index, view, position])
                    for position in visible_positions
                )
                groups.setdefault(visible_values, []).append(index)
            for indices in groups.values():
                if len(indices) > 1:
                    masked_hypothesis_readout_max_delta = max(
                        masked_hypothesis_readout_max_delta,
                        float(
                            np.max(
                                np.abs(
                                    candidate_readouts[indices]
                                    - candidate_readouts[indices[0]]
                                )
                            )
                        ),
                    )
            if discriminating_readouts is None:
                unique = np.unique(np.round(candidate_readouts, 12), axis=0)
                if len(unique) >= 2:
                    prior = np.full(
                        engine.n_hypotheses, 1.0 / engine.n_hypotheses
                    )
                    discriminating_readouts = (
                        prior,
                        unique[0],
                        unique[-1],
                        candidate_readouts,
                    )

    if discriminating_readouts is None:
        raise SlowMemoryError("no discriminating Pauli fixture for updater control")
    updater_prior, updater_q_a, updater_q_b, fixture_candidates = (
        discriminating_readouts
    )
    updater_a = engine.update_posterior(
        updater_prior, updater_q_a, fixture_candidates
    )
    updater_a_repeat = engine.update_posterior(
        updater_prior, updater_q_a, fixture_candidates
    )
    updater_b = engine.update_posterior(
        updater_prior, updater_q_b, fixture_candidates
    )
    updater_repeat_max_delta = float(np.max(np.abs(updater_a - updater_a_repeat)))
    updater_discriminating_total_variation = float(
        0.5 * np.sum(np.abs(updater_a - updater_b))
    )

    trajectory_receipt = {
        "schema": "loop3_senses/senses_v2_slow_memory/state_trajectories_v1",
        "matrix_encoding": "each complex entry is [real, imaginary]",
        "m_slow_definition": "normalized posterior over (initial_word, public_rule) hypotheses",
        "hypothesis_order": [
            {"index": index, "initial_word": int(word), "rule": int(rule)}
            for index, (word, rule) in enumerate(zip(words, rules))
        ],
        "object_order": object_ids,
        "view_order": list(range(N_VIEWS)),
        "candidate_reset_fast": {
            object_id: [
                {
                    "view": int(state["view"]),
                    "mask": [bool(value) for value in state["mask"]],
                    "rho_fast": density_payload(state["rho_fast"]),
                    "quantum_readout": [float(value) for value in state["quantum_readout"]],
                    "m_slow_summary": [float(value) for value in state["m_slow_summary"]],
                    "m_slow_posterior": [float(value) for value in state["posterior"]],
                    "posterior_sum": state["posterior_sum"],
                }
                for state in states
            ]
            for object_id, states in sorted(main_states.items())
        },
    }
    with TRAJECTORY_PATH.open("x") as handle:
        json.dump(trajectory_receipt, handle, separators=(",", ":"), allow_nan=False)

    input_hashes_end = {str(path): sha256_file(path) for path in tracked_inputs}
    parent_results = parent_receipt["results"]
    parent_split = parent_receipt["protocol"]["split"]
    original_split = original_receipt["protocol"]["split"]
    split_matches_parent = (
        train_objects == parent_split["train_objects"]
        and test_objects == parent_split["test_objects"]
    )
    split_matches_original = (
        set(train_objects) == set(original_split["train_objects"])
        and set(test_objects) == set(original_split["test_objects"])
    )
    parent_context_matches = {
        "parent_promotion_is_false": parent_receipt.get("promotion_allowed") is False,
        "parent_fixed_occluded_accuracy_matches_context": abs(
            parent_results["fixed_engine"]["occluded_accuracy"] - 0.5131195335276968
        )
        < 1e-12,
        "parent_fixed_holevo_below_null": (
            parent_results["fixed_engine"]["belief_persistence_holevo_bits"]
            < parent_results["fixed_engine"]["holevo_permutation_null_p95_bits"]
        ),
        "parent_full_context_accuracy_matches_context": abs(
            parent_results["full_visibility_real_task"]["fixed_held_out_accuracy"]
            - 0.60932944606414
        )
        < 1e-12,
    }

    strongest_engine_control = max(computed_baseline, engine_null_p95)
    accuracy_ci = accuracy_bootstrap["metrics"]["candidate_accuracy"]["ci95"]
    chance_delta_ci = accuracy_bootstrap["metrics"]["candidate_minus_chance"][
        "ci95"
    ]
    slow_reset_delta_ci = accuracy_bootstrap["metrics"][
        "candidate_minus_slow_reset"
    ]["ci95"]
    main_mi_null_p95 = float(np.quantile(main_mi_null, 0.95))
    frozen_mi_null_p95 = float(np.quantile(frozen_mi_null, 0.95))
    all_posteriors_normalized = all(
        abs(state["posterior_sum"] - 1.0) < 1e-12
        for states in main_states.values()
        for state in states
    )
    integrity_checks = {
        **parent_context_matches,
        "canonical_interpreter": SIM_PY.resolve() == Path(sys.executable).resolve(),
        "memory_free_above_25_percent_before_heavy_imports": memory_percent > MIN_MEMORY_FREE_PERCENT,
        "torch_not_imported": "torch" not in sys.modules,
        "qutip_not_imported": "qutip" not in sys.modules,
        "ground_truth_recovered_from_visible_probes_only_for_evaluation": recovery_metrics["objects_uniquely_recovered"] == len(object_ids),
        "split_matches_parent_retest": split_matches_parent,
        "split_matches_original_loop2": split_matches_original,
        "object_split_is_disjoint": not bool(train_object_set & test_object_set),
        "occluded_slot_counts_match_parent": len(train_slots) == 782 and len(test_slots) == 343,
        "occluded_targets_remain_masked_in_main_getter": all(
            log_getter(slot[0])(slot[1], slot[2]) is None
            for slot in train_slots + test_slots
        ),
        "twin_features_unchanged_by_source_reuse": abs(
            twin_accuracy - parent_results["twin"]["occluded_accuracy"]
        )
        < 1e-15
        and twin_nodes == parent_results["twin"]["tree_nodes"]
        and twin_depth == parent_results["twin"]["tree_depth"],
        "rho_fast_resets_from_initial_density_each_view": rho_reset_replay_max < 1e-12,
        "m_slow_resets_between_objects": candidate_feature_hash
        == counterfactual_feature_hash,
        "m_slow_posterior_normalized_and_nonnegative": all_posteriors_normalized
        and posterior_minimum >= 0.0,
        "m_slow_bayes_replay_matches": bayes_replay_max < 1e-12,
        "m_slow_update_consumes_quantum_readouts_not_raw_values": updater_repeat_max_delta
        < 1e-15
        and updater_discriminating_total_variation > 1e-8,
        "hypothesis_likelihoods_ignore_withheld_values": masked_hypothesis_readout_max_delta
        < 1e-12,
        "likelihood_scale_is_unsupervised_and_positive": (
            likelihood_calibration["calibration_uses_labels"] is False
            and likelihood_calibration["sigma"] > 0
        ),
        "input_hashes_unchanged_during_run": input_hashes_start == input_hashes_end,
        "all_density_lanes_physical": all(
            value["pass"] for value in physicality.values()
        ),
        "measurement_channels_cptp": cptp["pass"],
        "original_broken_update_comparison_lane_executed": len(broken_states)
        == len(object_ids),
        "slow_reset_ablation_has_same_feature_dimension": len(
            main_states[object_ids[0]][0]["joint_feature"]
        )
        == len(slow_reset_states[object_ids[0]][0]["joint_feature"]),
        "hidden_target_flip_changes_truth_oracle": counterfactual_truth_hash_differs,
        "hidden_target_flip_leaves_rho_fast_identical": target_flip_rho_max_delta
        < 1e-12,
        "hidden_target_flip_leaves_m_slow_identical": target_flip_slow_max_delta
        < 1e-12,
        "hidden_target_flip_leaves_joint_features_identical": target_flip_joint_max_delta
        < 1e-12,
        "causal_prefix_is_future_invariant": prefix_max_delta < 1e-12,
        "deliberately_unmasked_leak_sentinel_changes_fast_and_slow": sentinel_changed
        == len(test_slots)
        and sentinel_slow_changed == len(test_slots)
        and sentinel_fast_max_delta > 1e-8
        and sentinel_slow_max_delta > 1e-8,
        "bootstrap_sample_size_adequate": len(test_slots) >= 100
        and len(test_objects) == 20,
        "trajectory_artifact_written": TRAJECTORY_PATH.exists(),
        "promotion_allowed_is_false": promotion_allowed is False,
        "formal_admission_allowed_is_false": formal_admission_allowed is False,
    }
    scientific_checks = {
        "candidate_occluded_accuracy_above_chance_and_shuffled_p95": main_accuracy > strongest_engine_control,
        "candidate_accuracy_bootstrap_lower_above_chance": chance_delta_ci[0] > 0.0,
        "belief_persistence_mutual_information_above_permutation_null": main_mi > main_mi_null_p95,
        "persistent_slow_memory_beats_same_feature_reset_ablation": slow_reset_delta_ci[0]
        > 0.0
        and main_mi > slow_reset_mi
        and persistence_register_delta > 1e-8,
        "full_context_target_masked_overall_above_chance": full_context_accuracy > computed_baseline,
        "full_context_target_masked_all_k_beat_chance": all(
            item["candidate_pass"] for item in full_context_per_view
        ),
        "full_visibility_replication_all_k_beat_chance": full_visibility["all_k_beat_chance"],
        "frozen_control_does_not_pass": (
            frozen_accuracy <= computed_baseline + 0.03
            and frozen_mi <= frozen_mi_null_p95
        ),
        "shuffled_label_control_is_below_candidate": main_accuracy > engine_null_p95,
    }
    integrity_pass = bool(all(integrity_checks.values()))
    scientific_pass = bool(all(scientific_checks.values()))
    checks = {**integrity_checks, **scientific_checks}
    all_pass = bool(integrity_pass and scientific_pass)

    at_least_one_lane_above_random = (
        main_accuracy > max(computed_baseline, engine_null_p95)
        or twin_accuracy > max(computed_baseline, twin_null_p95)
    )
    union_above_joint_null = union_accuracy > union_null_p95
    both_random_confound_excluded = bool(
        at_least_one_lane_above_random and union_above_joint_null
    )
    useful_complementarity_eligible = bool(
        main_accuracy > max(computed_baseline, engine_null_p95)
        and twin_accuracy > max(computed_baseline, twin_null_p95)
        and union_above_joint_null
    )
    if useful_complementarity_eligible:
        phi = complementarity["metrics"]["phi"]["estimate"]
        if complementarity["metrics"]["union_gain_over_best"]["estimate"] <= 0:
            coupling = "redundant"
        elif phi is not None and phi < -0.2:
            coupling = "complementary_with_above_random_guard"
        else:
            coupling = "partially_independent_with_above_random_guard"
    else:
        coupling = (
            "ineligible_both_random_confound"
            if not both_random_confound_excluded
            else "ineligible_one_lane_not_above_matched_control"
        )

    findings = [
        (
            f"Slow-memory occluded accuracy {main_accuracy:.4f}, twin {twin_accuracy:.4f}, "
            f"computed chance {computed_baseline:.4f}, shuffled-engine p95 {engine_null_p95:.4f}."
        ),
        (
            f"I(O;m_slow) {main_mi:.6f} bits versus permutation p95 "
            f"{main_mi_null_p95:.6f}; frozen {frozen_mi:.6f}; broken {broken_mi:.6f}."
        ),
        (
            f"Full-context target-masked accuracy {full_context_accuracy:.4f} versus chance "
            f"{computed_baseline:.4f}; every-k pass={all(item['candidate_pass'] for item in full_context_per_view)}."
        ),
        (
            f"Frozen accuracy {frozen_accuracy:.4f}; original-broken-with-slow-memory accuracy "
            f"{broken_accuracy:.4f}."
        ),
        (
            f"Leak counterfactual invariant={candidate_feature_hash == counterfactual_feature_hash}; "
            f"positive sentinel changed {sentinel_changed}/{len(test_slots)} features "
            f"(joint max delta {sentinel_joint_max_delta:.6g})."
        ),
    ]
    if twin_accuracy >= main_accuracy:
        findings.append(
            "HONEST NEGATIVE KEPT: the unchanged classical twin matches or beats the slow-memory candidate on the held-out occluded task."
        )
    if main_mi <= main_mi_null_p95:
        findings.append(
            "HONEST NEGATIVE KEPT: slow-register mutual information does not exceed its permutation null."
        )
    if not all_pass:
        findings.append(
            "HONEST NEGATIVE KEPT: at least one fail-closed check is red; the diagnostic is retained without promotion."
        )

    split_fingerprint = sha256_json(
        {
            "seed": SEED,
            "train_objects": train_objects,
            "test_objects": test_objects,
            "train_slots": train_slots,
            "test_slots": test_slots,
        }
    )
    prediction_fingerprint = sha256_json(
        [
            {
                "slot": slot,
                "truth": truth(slot),
                "slow_memory": main_predictions[slot],
                "twin": twin_predictions[slot],
            }
            for slot in test_slots
        ]
    )
    receipt = {
        "schema": "loop3_senses/senses_v2_slow_memory/receipt_v1",
        "sim_id": "senses_v2_slow_memory",
        "version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": CLASSIFICATION,
        "promotion_status": "diagnostic_only",
        "card_authority": str(FOUNDATION_CARD),
        "object_preservation_card": str(OBJECT_CARD),
        "runtime": {
            "python": sys.executable,
            "python_version": sys.version.split()[0],
            "required_python": str(SIM_PY),
            "memory_free_percent": memory_percent,
            "minimum_required_percent": MIN_MEMORY_FREE_PERCENT,
            "memory_gate_checked_before_heavy_imports": True,
            "torch_used": False,
            "qutip_used": False,
            "one_heavy_runtime_at_a_time": True,
        },
        "inputs": {
            "world_events": str(EVENTS),
            "world_events_sha256": sha256_file(EVENTS),
            "world_receipt": str(WORLD_RECEIPT),
            "world_receipt_sha256": sha256_file(WORLD_RECEIPT),
            "loop2_source": str(LOOP2_SOURCE),
            "loop2_source_sha256": sha256_file(LOOP2_SOURCE),
            "loop2_receipt": str(LOOP2_RECEIPT),
            "loop2_receipt_sha256": sha256_file(LOOP2_RECEIPT),
            "stage64_receipt": str(STAGE64),
            "stage64_receipt_sha256": sha256_file(STAGE64),
            "visibility_source": str(VISIBILITY_SOURCE),
            "visibility_source_sha256": sha256_file(VISIBILITY_SOURCE),
            "parent_retest_source": str(PARENT_SOURCE),
            "parent_retest_source_sha256": sha256_file(PARENT_SOURCE),
            "parent_retest_receipt": str(PARENT_RECEIPT),
            "parent_retest_receipt_sha256": sha256_file(PARENT_RECEIPT),
            "foundation_card": str(FOUNDATION_CARD),
            "foundation_card_sha256": sha256_file(FOUNDATION_CARD),
            "object_preservation_card": str(OBJECT_CARD),
            "object_preservation_card_sha256": sha256_file(OBJECT_CARD),
            "source": str(SOURCE),
            "source_sha256": sha256_file(SOURCE),
            "start_hashes": input_hashes_start,
            "end_hashes": input_hashes_end,
            "schema_metrics": schema_metrics,
            "ground_truth_recovery_for_evaluation_only": recovery_metrics,
        },
        "protocol": {
            "task": "after visible probes of views 0..v, predict each occluded current-world bit at view v",
            "seed": SEED,
            "split": {
                "train_objects": train_objects,
                "test_objects": test_objects,
                "train_count": len(train_objects),
                "test_count": len(test_objects),
                "train_slots": len(train_slots),
                "test_slots": len(test_slots),
                "object_disjoint": not bool(train_object_set & test_object_set),
                "fingerprint_sha256": split_fingerprint,
            },
            "state": "Z_t=(rho_fast,m_slow); rho_fast resets from rho_initial each view; m_slow persists across views and resets between object episodes",
            "slow_memory": {
                "register": "normalized posterior over 256 initial words x 4 public rules",
                "hypothesis_count": int(len(hypotheses)),
                "update": "posterior_h <- posterior_h * exp(-||q_actual-q_h||^2/(2*sigma^2)); normalize",
                "actual_evidence": "15 Pauli expectations of rho_fast after visible probes only",
                "mask_role": "selects the candidate quantum emission surface; carries no bit value",
                "raw_visible_values_enter_posterior_directly": False,
                "recovered_hidden_targets_enter_main_posterior": False,
                "likelihood_calibration": likelihood_calibration,
            },
            "joint_readout": "15 rho_fast Pauli features plus 8 current-bit marginals, 4 rule marginals, normalized entropy, maximum mass, and effective-support fraction from m_slow; same per-position ridge protocol",
            "twin": "exact imported loop-2 ID3 categorical features and hyperparameters; no slow-memory feature added",
            "bootstrap": complementarity["bootstrap_unit"],
            "mutual_information": f"held-out position-wise empirical I(O;m_slow), where O is the current queried hidden bit and the register statistic is its m_slow posterior marginal; {MI_BINS} unsupervised quantile-bin edges are frozen from train objects and the mean is taken over positions",
            "ground_truth_boundary": "full_views is evaluation oracle only in the main occluded lane; the main getter returns None for every queried withheld target",
        },
        "results": {
            "computed_baseline": computed_baseline,
            "slow_memory_engine": {
                "occluded_accuracy": main_accuracy,
                "occluded_accuracy_ci95_object_bootstrap": accuracy_ci,
                "belief_persistence_mutual_information_bits": main_mi,
                "mutual_information_by_position_bits": [float(value) for value in main_mi_by_position],
                "mutual_information_O_definition": "current queried hidden bit at a held-out occluded slot",
                "mutual_information_register_statistic": "m_slow posterior marginal for that current bit and position",
                "mutual_information_sample_unit": "held-out occluded slot, stratified by position; quantile edges frozen from train objects",
                "mutual_information_permutation_scheme": "held-out hidden labels permuted within target position; m_slow values and train-fitted bin edges fixed",
                "mutual_information_permutation_draws": N_PERMUTATIONS,
                "mutual_information_permutation_seed": SEED + 401,
                "mutual_information_permutation_null_mean_bits": float(main_mi_null.mean()),
                "mutual_information_permutation_null_p95_bits": main_mi_null_p95,
                "mutual_information_monte_carlo_pvalue": float(
                    (1 + np.sum(main_mi_null >= main_mi)) / (N_PERMUTATIONS + 1)
                ),
            },
            "accuracy_object_bootstrap": accuracy_bootstrap,
            "twin": {
                "occluded_accuracy": twin_accuracy,
                "occluded_accuracy_ci95_object_bootstrap": accuracy_bootstrap["metrics"]["twin_accuracy"]["ci95"],
                "tree_nodes": twin_nodes,
                "tree_depth": twin_depth,
                "features_unchanged": True,
                "feature_schema": twin_feature_schema,
                "feature_fingerprint_sha256": twin_feature_fingerprint,
                "prediction_fingerprint_sha256": twin_prediction_fingerprint,
            },
            "complementarity": {
                **complementarity,
                "coupling_class": coupling,
                "both_random_confound_excluded": both_random_confound_excluded,
                "at_least_one_lane_above_random": bool(at_least_one_lane_above_random),
                "union_above_joint_shuffled_null": bool(union_above_joint_null),
                "useful_complementarity_eligible": useful_complementarity_eligible,
                "synergy_supported": False,
                "synergy_boundary": "oracle union coverage only; no learned joint engine-twin combiner",
            },
            "prediction_fingerprint_sha256": prediction_fingerprint,
            "episode_level_table": episodes,
            "full_context_target_masked": {
                "accuracy_type": "occluded current-world bit with all prior views and all non-target current-view bits visible",
                "queried_target_remains_masked": True,
                "candidate_held_out_accuracy": full_context_accuracy,
                "original_broken_held_out_accuracy": full_context_broken_accuracy,
                "computed_chance_accuracy": computed_baseline,
                "candidate_margin": full_context_accuracy - computed_baseline,
                "per_k": full_context_per_view,
                "all_k_beat_chance": bool(
                    all(item["candidate_pass"] for item in full_context_per_view)
                ),
            },
            "visibility_gate_G4_replication": full_visibility,
            "controls": {
                "frozen_quantum_readout": {
                    "occluded_accuracy": frozen_accuracy,
                    "belief_persistence_mutual_information_bits": frozen_mi,
                    "mutual_information_by_position_bits": [float(value) for value in frozen_mi_by_position],
                    "mutual_information_permutation_null_mean_bits": float(frozen_mi_null.mean()),
                    "mutual_information_permutation_null_p95_bits": frozen_mi_null_p95,
                    "scope": "actual visible outcomes forced to zero before the quantum readout; masks and candidate emission model unchanged",
                },
                "m_slow_reset_each_view": {
                    "occluded_accuracy": slow_reset_accuracy,
                    "belief_persistence_mutual_information_bits": slow_reset_mi,
                    "mutual_information_by_position_bits": [float(value) for value in slow_reset_mi_by_position],
                    "feature_dimension": len(
                        slow_reset_states[object_ids[0]][0]["joint_feature"]
                    ),
                    "scope": "same rho_fast, joint feature dimension, split, ridge readout, and refit; only m_slow is reset to uniform before every view",
                },
                "original_broken_update_with_slow_memory": {
                    "occluded_accuracy": broken_accuracy,
                    "belief_persistence_mutual_information_bits": broken_mi,
                    "mutual_information_by_position_bits": [float(value) for value in broken_mi_by_position],
                    "mutual_information_permutation_null_mean_bits": float(broken_mi_null.mean()),
                    "mutual_information_permutation_null_p95_bits": float(np.quantile(broken_mi_null, 0.95)),
                    "scope": "rho_fast and candidate emissions recur instead of resetting; the same m_slow update and decoder are used",
                },
                "shuffled_training_labels": {
                    "draws": N_PERMUTATIONS,
                    "seed": SEED + 31,
                    "paired_engine_twin_label_map": True,
                    "engine_accuracy_mean": float(shuffled_engine_accuracy.mean()),
                    "engine_accuracy_p95": engine_null_p95,
                    "engine_monte_carlo_pvalue": float(
                        (1 + np.sum(shuffled_engine_accuracy >= main_accuracy))
                        / (N_PERMUTATIONS + 1)
                    ),
                    "twin_accuracy_mean": float(shuffled_twin_accuracy.mean()),
                    "twin_accuracy_p95": twin_null_p95,
                    "union_accuracy_mean": float(shuffled_union_accuracy.mean()),
                    "union_accuracy_p95": union_null_p95,
                    "shuffle_scope": "training labels permuted within target position; both decoders refit; held-out labels unchanged",
                },
                "leak_counterfactual": {
                    "evaluation_only_hidden_targets_flipped": True,
                    "original_truth_sha256": sha256_json(full_views),
                    "flipped_truth_sha256": sha256_json(counterfactual_full_views),
                    "candidate_feature_sha256": candidate_feature_hash,
                    "counterfactual_candidate_feature_sha256": counterfactual_feature_hash,
                    "candidate_features_identical": candidate_feature_hash == counterfactual_feature_hash,
                    "rho_fast_max_abs_delta": target_flip_rho_max_delta,
                    "m_slow_max_abs_delta": target_flip_slow_max_delta,
                    "joint_feature_max_abs_delta": target_flip_joint_max_delta,
                    "causal_prefix_max_abs_delta": prefix_max_delta,
                    "positive_unmask_sentinel_changed_count": sentinel_changed,
                    "positive_unmask_sentinel_slow_changed_count": sentinel_slow_changed,
                    "positive_unmask_sentinel_total": len(test_slots),
                    "positive_unmask_sentinel_fast_max_delta": sentinel_fast_max_delta,
                    "positive_unmask_sentinel_slow_max_delta": sentinel_slow_max_delta,
                    "positive_unmask_sentinel_joint_max_delta": sentinel_joint_max_delta,
                },
            },
            "physicality": physicality,
            "measurement_channel_cptp": cptp,
            "state_trajectories": {
                "path": str(TRAJECTORY_PATH),
                "sha256": sha256_file(TRAJECTORY_PATH),
                "candidate_lane_contains_full_m_slow_posterior": True,
            },
            "replay_and_boundary_residuals": {
                "rho_fast_reset_replay_max_abs": rho_reset_replay_max,
                "m_slow_bayes_replay_max_abs": bayes_replay_max,
                "posterior_minimum": posterior_minimum,
                "masked_hypothesis_readout_max_abs": masked_hypothesis_readout_max_delta,
                "readout_updater_repeat_max_abs": updater_repeat_max_delta,
                "readout_updater_discriminating_total_variation": updater_discriminating_total_variation,
                "persistent_vs_reset_register_max_abs": persistence_register_delta,
            },
        },
        "integrity_checks": integrity_checks,
        "scientific_checks": scientific_checks,
        "integrity_pass": integrity_pass,
        "scientific_pass": scientific_pass,
        "checks": checks,
        "all_pass": all_pass,
        "findings": findings,
        "divergence_log": [
            {
                "comparison": "slow memory versus parent fixed-fast-only retest",
                "occluded_accuracy_delta": main_accuracy - parent_results["fixed_engine"]["occluded_accuracy"],
                "belief_metric_note": "I(O;m_slow) and Holevo(O;rho_fast) are different metrics and are not subtracted",
            },
            {
                "comparison": "reset-fast slow memory versus original-broken-fast slow memory",
                "occluded_accuracy_delta": main_accuracy - broken_accuracy,
                "mutual_information_delta_bits": main_mi - broken_mi,
                "full_context_accuracy_delta": full_context_accuracy - full_context_broken_accuracy,
            },
            {
                "comparison": "slow memory versus unchanged classical twin",
                "occluded_accuracy_delta": main_accuracy - twin_accuracy,
                "union_gain_over_best": complementarity["metrics"]["union_gain_over_best"]["estimate"],
            },
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "carrier_comparison_executed": False,
        "blocked_consumers": [
            "carrier promotion or scaling",
            "loop-3 carrier tournament",
            "quantum-memory proof from a classical register",
            "bridge, axis, manifold, physics, or scientific admission",
            "reuse of this result directory",
        ],
        "accepted_status_label": (
            "passes local rerun"
            if all_pass
            else "exists"
        ),
        "claim_ceiling": (
            "passes one local bounded quantum-readout-fed slow-memory diagnostic; no carrier comparison, scaling, promotion, or admission"
            if all_pass
            else "fresh diagnostic artifacts exist and retain one or more red checks; no senses pass, carrier comparison, scaling, promotion, or admission"
        ),
        "receipt_path": str(RECEIPT_PATH),
    }
    return receipt


def main() -> int:
    try:
        refuse_to_reuse()
    except SlowMemoryError as error:
        print(str(error), file=sys.stderr)
        return 2

    memory_percent: int | None = None
    try:
        memory_percent = memory_free_percent()
        if memory_percent <= MIN_MEMORY_FREE_PERCENT:
            raise SlowMemoryError(
                f"memory free percentage {memory_percent}% is not > {MIN_MEMORY_FREE_PERCENT}%"
            )
        if SIM_PY.resolve() != Path(sys.executable).resolve():
            raise SlowMemoryError(
                f"wrong interpreter: {sys.executable}; required realpath {SIM_PY.resolve()}"
            )
        required = [
            EVENTS,
            WORLD_RECEIPT,
            LOOP2_SOURCE,
            LOOP2_RECEIPT,
            STAGE64,
            VISIBILITY_SOURCE,
            PARENT_SOURCE,
            PARENT_RECEIPT,
            FOUNDATION_CARD,
            OBJECT_CARD,
            SOURCE,
        ]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise SlowMemoryError(f"missing required inputs: {missing}")
    except (OSError, subprocess.CalledProcessError, SlowMemoryError) as error:
        print(f"FATAL PRE-WRITE: {type(error).__name__}: {error}", file=sys.stderr)
        return 2

    OUTDIR.mkdir(parents=True, exist_ok=False)
    try:
        receipt = run(memory_percent)
    except Exception as error:
        write_fatal_receipt(f"{type(error).__name__}: {error}", memory_percent)
        print(f"FATAL: {type(error).__name__}: {error}", file=sys.stderr)
        print(f"fatal receipt written: {RECEIPT_PATH}", file=sys.stderr)
        return 1

    with RECEIPT_PATH.open("x") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)
    print(f"receipt written: {RECEIPT_PATH}")
    print(
        json.dumps(
            {
                "all_pass": receipt["all_pass"],
                "failed_checks": [
                    key for key, value in receipt["checks"].items() if not value
                ],
                "findings": receipt["findings"],
                "promotion_allowed": receipt["promotion_allowed"],
                "claim_ceiling": receipt["claim_ceiling"],
            },
            indent=2,
        )
    )
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
