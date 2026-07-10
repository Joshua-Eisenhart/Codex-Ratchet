#!/usr/bin/env python3
"""Frozen PyTorch lane for unseen_finite_predictive_objects_v0.

This runner reads only the preregistered spec and object manifest. It never
reads another engine's result and never exposes manifest identity fields to a
model call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import torch
from torch import Tensor, nn
from torch.func import jacrev


ROOT = Path(__file__).resolve().parent
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"
TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "quarantined v0 pilot learner; no valid result receipt was emitted",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "supportive-only temporal Jacobian in the quarantined v0 pilot",
    },
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func": "supportive"}
V0_PROSPECTIVE_CLAIM_INVALID = True
SPEC_PATH = ROOT / "spec.json"
MANIFEST_PATH = ROOT / "object_manifest.json"
PREREGISTRATION_PATH = ROOT / "preregistration_receipt.json"
RESULT_PATH = ROOT / "results" / "pytorch_result.json"
MODEL_VISIBLE_FIELDS = frozenset(
    {"corrupted_binary_tokens", "erasure_mask", "trajectory_boundary"}
)
MODEL_FORBIDDEN_FIELDS = frozenset(
    {
        "machine_definition",
        "canonical_hash",
        "object_index",
        "state_index",
        "split",
        "view_seed",
        "hard_negative_partner",
        "short_horizon_matched_partner",
    }
)
SEGMENTS = tuple((2**length) for length in range(1, 9))
ARM_NAMES = (
    "full",
    "optimizer_erased",
    "architecture_only",
    "fixed_deranged_labels",
    "temporal_shuffle",
    "marginal_histogram",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_seed(*parts: object) -> int:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (
        2**63 - 1
    )


def json_ready(value: Any) -> Any:
    if isinstance(value, Tensor):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    return value


def assert_model_visible_schema(batch: dict[str, Tensor]) -> None:
    keys = frozenset(batch)
    assert keys == MODEL_VISIBLE_FIELDS, (
        f"model-visible schema mismatch: got {sorted(keys)}, "
        f"expected {sorted(MODEL_VISIBLE_FIELDS)}"
    )
    assert not keys.intersection(MODEL_FORBIDDEN_FIELDS)
    tokens = batch["corrupted_binary_tokens"]
    masks = batch["erasure_mask"]
    boundaries = batch["trajectory_boundary"]
    assert tokens.ndim == 3 and tokens.shape == masks.shape == boundaries.shape
    assert tokens.dtype == torch.long
    assert masks.dtype == torch.bool and boundaries.dtype == torch.bool
    assert bool(torch.all((tokens == 0) | (tokens == 1)))
    assert bool(torch.all(boundaries[..., 0]))
    assert not bool(torch.any(boundaries[..., 1:]))


def exact_predictive_signature(machine: list[list[int]]) -> Tensor:
    segments: list[Tensor] = []
    for length in range(1, 9):
        probabilities: list[float] = []
        for word_index in range(2**length):
            probability = 0.0
            for start_state in range(4):
                state = start_state
                path_probability = 0.25
                for position in range(length):
                    bit = (word_index >> (length - position - 1)) & 1
                    next_zero, next_one, p_one_numerator = machine[state]
                    if bit:
                        path_probability *= p_one_numerator / 8.0
                        state = next_one
                    else:
                        path_probability *= (8 - p_one_numerator) / 8.0
                        state = next_zero
                probability += path_probability
            probabilities.append(probability)
        segment = torch.tensor(probabilities, dtype=torch.float32)
        segment /= segment.sum()
        segments.append(segment)
    return torch.cat(segments)


@dataclass(frozen=True)
class ViewRecord:
    visible: dict[str, Tensor]
    target: Tensor
    object_index: int
    view_index: int
    machine_sha256: str


def simulate_view(
    machine: list[list[int]], split: str, machine_sha256: str, view_index: int
) -> dict[str, Tensor]:
    tokens = torch.empty((8, 128), dtype=torch.long)
    erasure = torch.empty((8, 128), dtype=torch.bool)
    boundary = torch.zeros((8, 128), dtype=torch.bool)
    boundary[:, 0] = True
    for trajectory_index in range(8):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(
            stable_seed(
                "ufpo-v0-view",
                split,
                machine_sha256,
                view_index,
                trajectory_index,
            )
        )
        state = int(torch.randint(0, 4, (), generator=generator).item())
        for step in range(128):
            next_zero, next_one, p_one_numerator = machine[state]
            emitted = int(
                torch.rand((), generator=generator).item()
                < (p_one_numerator / 8.0)
            )
            state = next_one if emitted else next_zero
            erased = bool(torch.rand((), generator=generator).item() < 0.35)
            substituted = (
                not erased
                and bool(torch.rand((), generator=generator).item() < 0.10)
            )
            tokens[trajectory_index, step] = 0 if erased else emitted ^ substituted
            erasure[trajectory_index, step] = erased
    visible = {
        "corrupted_binary_tokens": tokens,
        "erasure_mask": erasure,
        "trajectory_boundary": boundary,
    }
    assert_model_visible_schema({key: value.unsqueeze(0) for key, value in visible.items()})
    return visible


def build_records(manifest: dict[str, Any]) -> dict[str, list[ViewRecord]]:
    views_per_split = {"train": 6, "validation": 8, "test": 8}
    records: dict[str, list[ViewRecord]] = {}
    for split in ("train", "validation", "test"):
        split_records: list[ViewRecord] = []
        for object_index, object_entry in enumerate(manifest["splits"][split]):
            target = exact_predictive_signature(object_entry["machine"])
            for view_index in range(views_per_split[split]):
                split_records.append(
                    ViewRecord(
                        visible=simulate_view(
                            object_entry["machine"],
                            split,
                            object_entry["machine_sha256"],
                            view_index,
                        ),
                        target=target,
                        object_index=object_index,
                        view_index=view_index,
                        machine_sha256=object_entry["machine_sha256"],
                    )
                )
        records[split] = split_records
    return records


def collate_visible(records: list[ViewRecord], device: torch.device) -> dict[str, Tensor]:
    batch = {
        key: torch.stack([record.visible[key] for record in records]).to(device)
        for key in sorted(MODEL_VISIBLE_FIELDS)
    }
    assert_model_visible_schema(batch)
    return batch


def segment_log_probabilities(logits: Tensor) -> list[Tensor]:
    return [segment.log_softmax(dim=-1) for segment in logits.split(SEGMENTS, dim=-1)]


def segment_probabilities(logits: Tensor) -> list[Tensor]:
    return [segment.softmax(dim=-1) for segment in logits.split(SEGMENTS, dim=-1)]


class PredictiveDecoder(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.projections = nn.ModuleList(nn.Linear(96, width) for width in SEGMENTS)

    def forward(self, embedding: Tensor) -> Tensor:
        return torch.cat([projection(embedding) for projection in self.projections], dim=-1)


class GRUDeepSets(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.token_embedding = nn.Embedding(2, 24)
        self.gru = nn.GRU(
            input_size=26,
            hidden_size=64,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
        )
        self.phi = nn.Sequential(nn.Linear(128, 96), nn.GELU())
        self.rho = nn.Sequential(nn.Linear(96, 96), nn.GELU())
        self.decoder = PredictiveDecoder()

    def continuous_inputs(self, visible: dict[str, Tensor]) -> Tensor:
        assert_model_visible_schema(visible)
        token_features = self.token_embedding(visible["corrupted_binary_tokens"])
        return torch.cat(
            [
                token_features,
                visible["erasure_mask"].unsqueeze(-1).to(token_features.dtype),
                visible["trajectory_boundary"].unsqueeze(-1).to(token_features.dtype),
            ],
            dim=-1,
        )

    def encode_continuous(self, inputs: Tensor) -> Tensor:
        batch_size, trajectory_count, length, width = inputs.shape
        flattened = inputs.reshape(batch_size * trajectory_count, length, width)
        _, hidden = self.gru(flattened)
        final = torch.cat([hidden[-2], hidden[-1]], dim=-1)
        trajectory_embeddings = self.phi(final).reshape(batch_size, trajectory_count, 96)
        return self.rho(trajectory_embeddings.mean(dim=1))

    def forward(self, visible: dict[str, Tensor]) -> tuple[Tensor, Tensor]:
        embedding = self.encode_continuous(self.continuous_inputs(visible))
        return embedding, self.decoder(embedding)


def histogram_features(visible: dict[str, Tensor]) -> Tensor:
    assert_model_visible_schema(visible)
    tokens = visible["corrupted_binary_tokens"]
    erased = visible["erasure_mask"]
    valid = ~erased
    denominator = torch.full(
        tokens.shape[:2], tokens.shape[-1], dtype=torch.float32, device=tokens.device
    )
    zero = ((tokens == 0) & valid).sum(dim=-1) / denominator
    one = ((tokens == 1) & valid).sum(dim=-1) / denominator
    missing = erased.sum(dim=-1) / denominator
    return torch.stack([zero, one, missing], dim=-1).flatten(start_dim=1)


class MarginalHistogramMLP(nn.Module):
    def __init__(self, hidden_width: int) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(24, hidden_width),
            nn.GELU(),
            nn.Linear(hidden_width, hidden_width),
            nn.GELU(),
            nn.Linear(hidden_width, 96),
            nn.GELU(),
        )
        self.decoder = PredictiveDecoder()

    def forward(self, visible: dict[str, Tensor]) -> tuple[Tensor, Tensor]:
        embedding = self.encoder(histogram_features(visible))
        return embedding, self.decoder(embedding)


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def matched_histogram_width(target_count: int) -> int:
    best_width = 1
    best_difference = math.inf
    for width in range(32, 768):
        candidate = parameter_count(MarginalHistogramMLP(width))
        difference = abs(candidate - target_count)
        if difference < best_difference:
            best_width = width
            best_difference = difference
    return best_width


def predictive_cross_entropy(logits: Tensor, target: Tensor) -> Tensor:
    target_segments = target.split(SEGMENTS, dim=-1)
    losses = [
        -(target_segment * log_probability).sum(dim=-1).mean()
        for target_segment, log_probability in zip(
            target_segments, segment_log_probabilities(logits), strict=True
        )
    ]
    return torch.stack(losses).mean()


def contrastive_loss(
    embedding: Tensor, source_objects: Tensor, positive_objects: Tensor
) -> Tensor:
    normalized = nn.functional.normalize(embedding, dim=-1)
    similarity = normalized @ normalized.T / 0.1
    diagonal = torch.eye(similarity.shape[0], dtype=torch.bool, device=similarity.device)
    candidate_mask = ~diagonal
    positive_mask = (
        source_objects.unsqueeze(0) == positive_objects.unsqueeze(1)
    ) & candidate_mask
    assert bool(torch.all(positive_mask.any(dim=1)))
    denominator = torch.logsumexp(similarity.masked_fill(~candidate_mask, -torch.inf), dim=1)
    numerator = torch.logsumexp(similarity.masked_fill(~positive_mask, -torch.inf), dim=1)
    return (denominator - numerator).mean()


def shuffled_visible(
    visible: dict[str, Tensor], records: list[ViewRecord], seed: int
) -> dict[str, Tensor]:
    shuffled = {key: value.clone() for key, value in visible.items()}
    for batch_index, record in enumerate(records):
        for trajectory_index in range(8):
            generator = torch.Generator(device="cpu")
            generator.manual_seed(
                stable_seed(
                    "temporal-shuffle",
                    seed,
                    record.machine_sha256,
                    record.view_index,
                    trajectory_index,
                )
            )
            permutation = torch.randperm(128, generator=generator).to(visible["corrupted_binary_tokens"].device)
            for key in ("corrupted_binary_tokens", "erasure_mask"):
                shuffled[key][batch_index, trajectory_index] = visible[key][
                    batch_index, trajectory_index, permutation
                ]
    assert_model_visible_schema(shuffled)
    return shuffled


def iter_object_batches(records: list[ViewRecord], objects_per_batch: int = 32) -> Iterable[list[ViewRecord]]:
    by_object: dict[int, list[ViewRecord]] = {}
    for record in records:
        by_object.setdefault(record.object_index, []).append(record)
    object_ids = sorted(by_object)
    for start in range(0, len(object_ids), objects_per_batch):
        batch_ids = object_ids[start : start + objects_per_batch]
        yield [record for object_id in batch_ids for record in by_object[object_id]]


def train_arm(
    arm: str,
    seed: int,
    train_records: list[ViewRecord],
    targets_by_object: Tensor,
    device: torch.device,
    histogram_width: int,
    epochs: int,
) -> tuple[nn.Module, dict[str, Any]]:
    torch.manual_seed(seed)
    random.seed(seed)
    if device.type == "mps":
        torch.mps.manual_seed(seed)
    model: nn.Module
    if arm == "marginal_histogram":
        model = MarginalHistogramMLP(histogram_width)
    else:
        model = GRUDeepSets()
    model.to(device)
    learning_rate = 0.0 if arm == "optimizer_erased" else 0.0003
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.0001)
    loss_trace: list[float] = []
    update_steps = 0
    if arm != "architecture_only":
        model.train()
        for _epoch in range(epochs):
            epoch_loss = 0.0
            epoch_batches = 0
            for batch_records in iter_object_batches(train_records):
                visible = collate_visible(batch_records, device)
                if arm == "temporal_shuffle":
                    visible = shuffled_visible(visible, batch_records, seed)
                source_objects = torch.tensor(
                    [record.object_index for record in batch_records],
                    dtype=torch.long,
                    device=device,
                )
                if arm == "fixed_deranged_labels":
                    positive_objects = source_objects ^ 1
                    target = targets_by_object.to(device)[positive_objects]
                else:
                    positive_objects = source_objects
                    target = torch.stack([record.target for record in batch_records]).to(device)
                optimizer.zero_grad(set_to_none=True)
                embedding, logits = model(visible)
                loss = predictive_cross_entropy(logits, target) + contrastive_loss(
                    embedding, source_objects, positive_objects
                )
                loss.backward()
                optimizer.step()
                epoch_loss += float(loss.detach().cpu())
                epoch_batches += 1
                update_steps += 1
            loss_trace.append(epoch_loss / epoch_batches)
    else:
        loss_trace = []
    return model, {
        "epochs_budgeted": epochs,
        "epochs_with_gradient_steps": 0 if arm == "architecture_only" else epochs,
        "optimizer": "AdamW",
        "learning_rate": learning_rate,
        "weight_decay": 0.0001,
        "update_steps": update_steps,
        "epoch_loss": loss_trace,
        "checkpoint_scored": epochs,
    }


def predict_records(
    model: nn.Module,
    records: list[ViewRecord],
    device: torch.device,
    arm: str,
    seed: int,
) -> tuple[Tensor, Tensor, Tensor]:
    embeddings: list[Tensor] = []
    predictions: list[Tensor] = []
    labels: list[int] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(records), 64):
            batch_records = records[start : start + 64]
            visible = collate_visible(batch_records, device)
            if arm == "temporal_shuffle":
                visible = shuffled_visible(visible, batch_records, seed)
            embedding, logits = model(visible)
            probabilities = torch.cat(segment_probabilities(logits), dim=-1)
            embeddings.append(embedding.cpu())
            predictions.append(probabilities.cpu())
            labels.extend(record.object_index for record in batch_records)
    return torch.cat(embeddings), torch.cat(predictions), torch.tensor(labels)


def torch_kmeans(points: Tensor, cluster_count: int, seed: int) -> Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(stable_seed("kmeans", seed))
    first = int(torch.randint(0, len(points), (), generator=generator).item())
    centers = [points[first]]
    minimum_distance = torch.full((len(points),), torch.inf)
    for _ in range(1, cluster_count):
        distance = ((points - centers[-1]) ** 2).sum(dim=1)
        minimum_distance = torch.minimum(minimum_distance, distance)
        next_index = int(torch.argmax(minimum_distance).item())
        centers.append(points[next_index])
    center_tensor = torch.stack(centers)
    assignments = torch.zeros(len(points), dtype=torch.long)
    for _ in range(100):
        distance = torch.cdist(points, center_tensor)
        updated = distance.argmin(dim=1)
        if torch.equal(updated, assignments):
            break
        assignments = updated
        new_centers = []
        for cluster in range(cluster_count):
            members = points[assignments == cluster]
            new_centers.append(center_tensor[cluster] if len(members) == 0 else members.mean(dim=0))
        center_tensor = torch.stack(new_centers)
    return assignments


def adjusted_rand_index(labels: Tensor, clusters: Tensor) -> float:
    contingency: dict[tuple[int, int], int] = {}
    label_counts: dict[int, int] = {}
    cluster_counts: dict[int, int] = {}
    for label, cluster in zip(labels.tolist(), clusters.tolist(), strict=True):
        contingency[(label, cluster)] = contingency.get((label, cluster), 0) + 1
        label_counts[label] = label_counts.get(label, 0) + 1
        cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1
    choose_two = lambda count: count * (count - 1) / 2
    index = sum(choose_two(count) for count in contingency.values())
    label_sum = sum(choose_two(count) for count in label_counts.values())
    cluster_sum = sum(choose_two(count) for count in cluster_counts.values())
    total_pairs = choose_two(len(labels))
    expected = label_sum * cluster_sum / total_pairs
    maximum = 0.5 * (label_sum + cluster_sum)
    return 1.0 if maximum == expected else (index - expected) / (maximum - expected)


def bcubed_f1(labels: Tensor, clusters: Tensor) -> float:
    label_counts: dict[int, int] = {}
    cluster_counts: dict[int, int] = {}
    intersections: dict[tuple[int, int], int] = {}
    pairs = list(zip(labels.tolist(), clusters.tolist(), strict=True))
    for label, cluster in pairs:
        label_counts[label] = label_counts.get(label, 0) + 1
        cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1
        intersections[(label, cluster)] = intersections.get((label, cluster), 0) + 1
    precision = sum(
        intersections[(label, cluster)] / cluster_counts[cluster]
        for label, cluster in pairs
    ) / len(pairs)
    recall = sum(
        intersections[(label, cluster)] / label_counts[label]
        for label, cluster in pairs
    ) / len(pairs)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def segmented_js(prediction: Tensor, target: Tensor) -> Tensor:
    values = []
    for predicted_segment, target_segment in zip(
        prediction.split(SEGMENTS, dim=-1), target.split(SEGMENTS, dim=-1), strict=True
    ):
        midpoint = 0.5 * (predicted_segment + target_segment)
        predicted_kl = (
            predicted_segment
            * (predicted_segment.clamp_min(1e-12).log() - midpoint.clamp_min(1e-12).log())
        ).sum(dim=-1)
        target_kl = (
            target_segment
            * (target_segment.clamp_min(1e-12).log() - midpoint.clamp_min(1e-12).log())
        ).sum(dim=-1)
        values.append(0.5 * (predicted_kl + target_kl))
    return torch.stack(values, dim=-1).mean(dim=-1)


def score_predictions(
    embeddings: Tensor,
    predictions: Tensor,
    labels: Tensor,
    test_records: list[ViewRecord],
    hard_negative_pairs: list[list[str]],
    seed: int,
) -> dict[str, Any]:
    clusters = torch_kmeans(embeddings, 32, seed)
    targets = torch.stack([record.target for record in test_records])
    predictive_js = segmented_js(predictions, targets)
    hash_to_index = {
        record.machine_sha256: record.object_index for record in test_records
    }
    target_by_object = torch.stack(
        [next(record.target for record in test_records if record.object_index == index) for index in range(32)]
    )
    preference_checks: list[bool] = []
    for first_hash, second_hash in hard_negative_pairs:
        first_index = hash_to_index[first_hash]
        second_index = hash_to_index[second_hash]
        for own_index, partner_index in ((first_index, second_index), (second_index, first_index)):
            own_predictions = predictions[labels == own_index]
            own_target = target_by_object[own_index].expand_as(own_predictions)
            partner_target = target_by_object[partner_index].expand_as(own_predictions)
            preference_checks.extend(
                (
                    segmented_js(own_predictions, own_target)
                    < segmented_js(own_predictions, partner_target)
                ).tolist()
            )
    return {
        "test_object_count": len(set(labels.tolist())),
        "test_view_count": len(labels),
        "ari": adjusted_rand_index(labels, clusters),
        "bcubed_f1": bcubed_f1(labels, clusters),
        "predictive_js": float(predictive_js.mean()),
        "hard_negative_own_target_preference": sum(preference_checks)
        / len(preference_checks),
        "hard_negative_comparison_count": len(preference_checks),
        "frozen_outputs": {
            "cluster_assignments": clusters.tolist(),
            "object_labels": labels.tolist(),
        },
    }


def temporal_sensitivity_receipt(
    model: nn.Module, record: ViewRecord, device: torch.device
) -> dict[str, Any]:
    if not isinstance(model, GRUDeepSets):
        raise TypeError("torch.func receipt requires the frozen GRUDeepSets model")
    model.eval()
    visible = collate_visible([record], device)
    base = model.continuous_inputs(visible).detach()
    direction = torch.zeros((26,), dtype=base.dtype, device=device)
    direction[0] = 1.0
    alpha = torch.zeros((128,), dtype=base.dtype, device=device)

    def response(time_amplitude: Tensor, feature_direction: Tensor) -> Tensor:
        perturbation = time_amplitude.view(1, 1, 128, 1) * feature_direction.view(1, 1, 1, 26)
        return model.encode_continuous(base + perturbation).squeeze(0)

    jacobian = jacrev(lambda amplitudes: response(amplitudes, direction))(alpha)
    erased_jacobian = jacrev(
        lambda amplitudes: response(amplitudes, torch.zeros_like(direction))
    )(alpha)
    with torch.no_grad():
        boundary_difference = float(
            (response(alpha, direction) - model.encode_continuous(base).squeeze(0)).abs().max().cpu()
        )
    column_norms = torch.linalg.vector_norm(jacobian, dim=0)
    positive_l1 = float(jacobian.abs().sum().detach().cpu())
    erased_l1 = float(erased_jacobian.abs().sum().detach().cpu())
    finite = bool(torch.isfinite(jacobian).all())
    passed = finite and positive_l1 > 1e-8 and erased_l1 == 0.0 and boundary_difference < 1e-6
    return {
        "tool": "torch.func",
        "qualified_api": "torch.func.jacrev",
        "role": "load_bearing",
        "input_object": "first sealed test view continuous time-amplitude vector",
        "output_object": "96_by_128 temporal-sensitivity Jacobian",
        "positive_case": {
            "finite": finite,
            "jacobian_l1": positive_l1,
            "time_column_norm_std": float(column_norms.std().detach().cpu()),
        },
        "negative_erased_control": {"jacobian_l1": erased_l1, "expected": 0.0},
        "boundary_case": {
            "zero_amplitude_embedding_max_abs_difference": boundary_difference,
            "max_allowed": 1e-6,
        },
        "demotion_condition": "result_valid is false if the positive Jacobian is nonfinite/zero, the erased direction is nonzero, or zero amplitude changes the embedding",
        "gates": ["result_valid", "all_pass"],
        "passed": passed,
    }


def median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else 0.5 * (ordered[middle - 1] + ordered[middle])


def evaluate_gates(
    arm_results: dict[str, dict[str, dict[str, Any]]],
    temporal_receipts: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    seeds = sorted(arm_results["full"])
    thresholds = {
        "ari_min": 0.35,
        "bcubed_f1_min": 0.55,
        "predictive_js_max": 0.14,
        "hard_negative_own_target_preference_min": 0.75,
        "median_ari_gain_over_each_control_min": 0.20,
        "median_predictive_js_improvement_over_each_control_min": 0.03,
    }
    control_names = [name for name in ARM_NAMES if name != "full"]
    deltas: dict[str, Any] = {}
    control_gates: dict[str, bool] = {}
    for control in control_names:
        ari_gains = [
            arm_results["full"][seed]["metrics"]["ari"]
            - arm_results[control][seed]["metrics"]["ari"]
            for seed in seeds
        ]
        js_improvements = [
            arm_results[control][seed]["metrics"]["predictive_js"]
            - arm_results["full"][seed]["metrics"]["predictive_js"]
            for seed in seeds
        ]
        deltas[control] = {
            "every_seed_ari_gain": dict(zip(seeds, ari_gains, strict=True)),
            "median_ari_gain": median(ari_gains),
            "every_seed_predictive_js_improvement": dict(
                zip(seeds, js_improvements, strict=True)
            ),
            "median_predictive_js_improvement": median(js_improvements),
        }
        control_fails_primary = all(
            (
                arm_results[control][seed]["metrics"]["ari"] < thresholds["ari_min"]
                or arm_results[control][seed]["metrics"]["bcubed_f1"]
                < thresholds["bcubed_f1_min"]
                or arm_results[control][seed]["metrics"]["predictive_js"]
                > thresholds["predictive_js_max"]
                or arm_results[control][seed]["metrics"]["hard_negative_own_target_preference"]
                < thresholds["hard_negative_own_target_preference_min"]
            )
            for seed in seeds
        )
        control_gates[control] = (
            deltas[control]["median_ari_gain"]
            >= thresholds["median_ari_gain_over_each_control_min"]
            and deltas[control]["median_predictive_js_improvement"]
            >= thresholds["median_predictive_js_improvement_over_each_control_min"]
            and control_fails_primary
        )
        deltas[control]["every_seed_fails_at_least_one_primary_threshold"] = control_fails_primary
    every_seed_primary = all(
        result["metrics"]["ari"] >= thresholds["ari_min"]
        and result["metrics"]["bcubed_f1"] >= thresholds["bcubed_f1_min"]
        and result["metrics"]["predictive_js"] <= thresholds["predictive_js_max"]
        and result["metrics"]["hard_negative_own_target_preference"]
        >= thresholds["hard_negative_own_target_preference_min"]
        for result in arm_results["full"].values()
    )
    gates = {
        "all_32_sealed_test_objects_scored_every_arm_seed": all(
            result["metrics"]["test_object_count"] == 32
            for arms in arm_results.values()
            for result in arms.values()
        ),
        "every_seed_primary_thresholds": every_seed_primary,
        "control_delta_and_failure_gates": control_gates,
        "torch_func_temporal_sensitivity_every_seed": all(
            receipt["passed"] for receipt in temporal_receipts.values()
        ),
    }
    all_pass = (
        gates["all_32_sealed_test_objects_scored_every_arm_seed"]
        and gates["every_seed_primary_thresholds"]
        and all(control_gates.values())
        and gates["torch_func_temporal_sensitivity_every_seed"]
    )
    return deltas, {"thresholds": thresholds, "gates": gates}, all_pass


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(json_ready(payload), handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def choose_device(requested: str) -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def run(smoke: bool, requested_device: str) -> dict[str, Any]:
    started_wall = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    with SPEC_PATH.open(encoding="utf-8") as handle:
        spec = json.load(handle)
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    with PREREGISTRATION_PATH.open(encoding="utf-8") as handle:
        preregistration = json.load(handle)
    assert preregistration["spec_sha256"] == sha256_file(SPEC_PATH)
    assert preregistration["object_manifest_sha256"] == sha256_file(MANIFEST_PATH)
    assert manifest["spec_sha256"] in {
        preregistration["spec_sha256"],
        preregistration.get("original_frozen_spec_sha256"),
    }
    assert spec["frozen_splits"]["model_seeds"] == [1701, 1702, 1703]
    assert spec["view_process"]["model_visible_fields"] == sorted(MODEL_VISIBLE_FIELDS)
    assert frozenset(spec["view_process"]["model_forbidden_fields"]).issubset(
        MODEL_FORBIDDEN_FIELDS
    )
    assert len(manifest["splits"]["test"]) == 32
    records = build_records(manifest)
    device = choose_device(requested_device)
    torch.use_deterministic_algorithms(True, warn_only=True)
    reference_model = GRUDeepSets()
    reference_parameter_count = parameter_count(reference_model)
    histogram_width = matched_histogram_width(reference_parameter_count)
    histogram_parameter_count = parameter_count(MarginalHistogramMLP(histogram_width))
    seeds = [1701] if smoke else [1701, 1702, 1703]
    arms = ["full"] if smoke else list(ARM_NAMES)
    epochs = 1 if smoke else 32
    train_records = records["train"][: 16 * 6] if smoke else records["train"]
    test_records = records["test"][: 4 * 8] if smoke else records["test"]
    train_targets = torch.stack(
        [
            next(record.target for record in records["train"] if record.object_index == index)
            for index in range(128)
        ]
    )
    arm_results: dict[str, dict[str, dict[str, Any]]] = {arm: {} for arm in arms}
    temporal_receipts: dict[str, dict[str, Any]] = {}
    for arm in arms:
        for seed in seeds:
            arm_started = time.perf_counter()
            model, training = train_arm(
                arm,
                seed,
                train_records,
                train_targets,
                device,
                histogram_width,
                epochs,
            )
            embeddings, predictions, labels = predict_records(
                model, test_records, device, arm, seed
            )
            if smoke:
                metrics = {
                    "test_object_count": len(set(labels.tolist())),
                    "test_view_count": len(labels),
                    "finite_embeddings": bool(torch.isfinite(embeddings).all()),
                    "finite_predictions": bool(torch.isfinite(predictions).all()),
                }
            else:
                metrics = score_predictions(
                    embeddings,
                    predictions,
                    labels,
                    test_records,
                    manifest["hard_negative_test_pairs"],
                    seed,
                )
            arm_results[arm][str(seed)] = {
                "training": training,
                "metrics": metrics,
                "runtime_seconds": time.perf_counter() - arm_started,
            }
            if arm == "full":
                temporal_receipts[str(seed)] = temporal_sensitivity_receipt(
                    model, test_records[0], device
                )
            print(
                json.dumps(
                    {
                        "progress": f"{arm}:{seed}",
                        "runtime_seconds": arm_results[arm][str(seed)][
                            "runtime_seconds"
                        ],
                        "metrics": metrics,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            del model
            if device.type == "mps":
                torch.mps.empty_cache()
            elif device.type == "cuda":
                torch.cuda.empty_cache()
    if smoke:
        return {
            "smoke": True,
            "writes_result": False,
            "device": str(device),
            "arm_results": arm_results,
            "torch_func_receipts": temporal_receipts,
            "runtime_seconds": time.perf_counter() - started_wall,
        }
    deltas, gate_report, metric_gates_pass = evaluate_gates(
        arm_results, temporal_receipts
    )
    all_pass = False
    completed_at = datetime.now(timezone.utc).isoformat()
    result = {
        "schema": "codex_ratchet.unseen_finite_predictive_objects_v0.pytorch_result.v1",
        "sim_id": spec["sim_id"],
        "engine": "pytorch",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "v0_prospective_claim_invalid": V0_PROSPECTIVE_CLAIM_INVALID,
        "metric_gates_pass_without_provenance_audit": metric_gates_pass,
        "preregistration_commit": "44d733e48",
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_file(Path(__file__).resolve()),
        "spec_sha256": sha256_file(SPEC_PATH),
        "object_manifest_sha256": sha256_file(MANIFEST_PATH),
        "preregistration_receipt_sha256": sha256_file(PREREGISTRATION_PATH),
        "preregistration_schema": preregistration["schema"],
        "reads_peer_result": False,
        "numpy_imported": False,
        "sklearn_used": False,
        "model_visible_schema": sorted(MODEL_VISIBLE_FIELDS),
        "model_forbidden_schema": sorted(MODEL_FORBIDDEN_FIELDS),
        "schema_assertion_enforced_before_every_model_call": True,
        "data_receipt": {
            "trajectory_generation": "independent SHA-256-derived torch.Generator subtree per split/object/view/trajectory",
            "split_view_counts": {key: len(value) for key, value in records.items()},
            "test_objects_scored": 32,
            "test_views_scored_per_object": 8,
            "test_replacement_after_results": False,
        },
        "architecture": {
            "token_embedding_width": 24,
            "bidirectional_gru_layers": 2,
            "gru_hidden_width": 64,
            "deepsets_pool": "mean over 8 independently encoded trajectories",
            "view_embedding_width": 96,
            "decoder_segments": list(SEGMENTS),
            "gru_deepsets_parameter_count": reference_parameter_count,
            "marginal_histogram_hidden_width": histogram_width,
            "marginal_histogram_parameter_count": histogram_parameter_count,
            "parameter_count_relative_difference": abs(
                histogram_parameter_count - reference_parameter_count
            )
            / reference_parameter_count,
        },
        "protocol": {
            "model_seeds": seeds,
            "epochs": 32,
            "checkpoint_policy": "epoch 32 only",
            "arms": list(ARM_NAMES),
            "same_frozen_splits": True,
            "same_batch_partition": True,
            "optimizer_erased_executes_full_forward_backward_budget": True,
            "architecture_only_has_no_optimizer_updates": True,
            "fixed_derangement": "xor-1 adjacent-object involution for targets and cross-object positives",
            "temporal_shuffle": "fixed joint token/mask permutation per trajectory; boundary remains first",
            "marginal_histogram": "per-trajectory zero/one/erasure frequencies only",
        },
        "arm_results": arm_results,
        "control_deltas": deltas,
        "torch_func_temporal_sensitivity": temporal_receipts,
        "tool_calls": [
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.jacrev",
                "input_object": "sealed test view time-amplitude vector",
                "output_object": "temporal-sensitivity Jacobian",
                "positive_case": "nonzero finite Jacobian",
                "negative/erased_control": "zero feature direction gives zero Jacobian",
                "boundary_case": "zero amplitude reproduces unperturbed embedding",
                "demotion_condition": "any per-seed torch.func receipt fails",
                "gates": ["result_valid", "all_pass"],
            }
        ],
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "gate_report": gate_report,
        "result_valid": all(
            receipt["passed"] for receipt in temporal_receipts.values()
        ),
        "all_pass": all_pass,
        "accepted_ceiling": spec["accepted_red_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
        "started_at": started_at,
        "completed_at": completed_at,
        "runtime_seconds": time.perf_counter() - started_wall,
        "runtime": {
            "python": os.sys.version,
            "torch": torch.__version__,
            "device": str(device),
        },
    }
    atomic_write_json(RESULT_PATH, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="one-arm diagnostic; never writes the sealed result",
    )
    parser.add_argument(
        "--device", choices=("auto", "cpu", "mps", "cuda"), default="auto"
    )
    arguments = parser.parse_args()
    result = run(arguments.smoke, arguments.device)
    if arguments.smoke:
        print(json.dumps(json_ready(result), indent=2, sort_keys=True))
    else:
        print(
            json.dumps(
                {
                    "result_path": str(RESULT_PATH),
                    "all_pass": result["all_pass"],
                    "accepted_ceiling": result["accepted_ceiling"],
                    "runtime_seconds": result["runtime_seconds"],
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
