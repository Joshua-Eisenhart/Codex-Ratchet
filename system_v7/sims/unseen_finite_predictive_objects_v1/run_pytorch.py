#!/usr/bin/env python3
"""Sealed PyTorch learner for unseen_finite_predictive_objects_v1.

The preflight path is deliberately train/validation-only. Test views and the
sealed result are reachable only from ``--sealed-test`` after a future seal
receipt binds both owned source files and the frozen inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Sequence

import torch
from torch import Tensor, nn
from torch.func import jacrev


HERE = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
SPEC_PATH = HERE / "spec.json"
MANIFEST_PATH = HERE / "object_manifest.json"
RESULT_PATH = HERE / "results" / "pytorch_result.json"
SEAL_RECEIPT_PATH = HERE / "seal_receipt.json"
RECOMPUTE_PATH = HERE / "recompute_metrics.py"

SIM_ID = "unseen_finite_predictive_objects_v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"
TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing GRU/DeepSets training, prediction, retrieval, controls, and frozen raw outputs",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "supportive temporal Jacobian diagnostic; never a primary or validity gate",
    },
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func": "supportive"}
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
        "full_observation_horizon_matched_partner",
    }
)
HORIZONS = (3, 4, 5, 6, 7, 8)
SEGMENT_LENGTHS = tuple(range(1, 9))
SEGMENTS = tuple(2**length for length in SEGMENT_LENGTHS)
TARGET_COORDINATES = sum(SEGMENTS)
ARM_NAMES = (
    "full",
    "temporal_shuffle",
    "histogram",
    "fixed_deranged",
    "optimizer_erased",
    "architecture_only",
)


def arm_seed_plan(spec: dict[str, Any]) -> dict[str, tuple[int, ...]]:
    seeds = tuple(int(value) for value in spec["view_process"]["model_seeds"])
    return {
        "full": seeds,
        "temporal_shuffle": seeds,
        "histogram": seeds,
        "fixed_deranged": (seeds[0],),
        "optimizer_erased": seeds,
        "architecture_only": seeds,
    }


class RunnerError(RuntimeError):
    """A fail-closed runner or contract error."""


def reject_json_constant(token: str) -> None:
    raise RunnerError(f"non-finite JSON constant: {token}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RunnerError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RunnerError(f"missing JSON input: {path}")
    value = json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=reject_json_constant,
        object_pairs_hook=reject_duplicate_keys,
    )
    if not isinstance(value, dict):
        raise RunnerError(f"expected one JSON object in {path}")
    assert_finite_json(value, str(path))
    return value


def assert_finite_json(value: Any, path: str = "value") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise RunnerError(f"non-finite value at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            assert_finite_json(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_finite_json(child, f"{path}[{index}]")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def stable_seed(*parts: object) -> int:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)


def json_ready(value: Any) -> Any:
    if isinstance(value, Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, (float, int, str, bool)) or value is None:
        return value
    raise TypeError(f"cannot serialize {type(value).__name__}")


def assert_model_visible_schema(batch: dict[str, Tensor]) -> None:
    keys = frozenset(batch)
    if keys != MODEL_VISIBLE_FIELDS or keys.intersection(MODEL_FORBIDDEN_FIELDS):
        raise RunnerError(
            f"model-visible schema mismatch: got {sorted(keys)}"
        )
    tokens = batch["corrupted_binary_tokens"]
    erasure = batch["erasure_mask"]
    boundary = batch["trajectory_boundary"]
    if tokens.ndim != 3 or tokens.shape != erasure.shape or tokens.shape != boundary.shape:
        raise RunnerError("visible tensors have inconsistent shapes")
    if tokens.dtype != torch.long or erasure.dtype != torch.bool or boundary.dtype != torch.bool:
        raise RunnerError("visible tensor dtypes do not match the contract")
    if not bool(torch.all((tokens == 0) | (tokens == 1))):
        raise RunnerError("visible tokens are not binary")
    if not bool(torch.all(boundary[..., 0])) or bool(torch.any(boundary[..., 1:])):
        raise RunnerError("trajectory boundary must mark only position zero")


def word_probability(machine: list[list[int]], start: int, word: Sequence[int]) -> Fraction:
    state = start
    probability = Fraction(1)
    for bit in word:
        next_zero, next_one, p_one = machine[state]
        probability *= Fraction(p_one if bit else 8 - p_one, 8)
        state = next_one if bit else next_zero
    return probability


def exact_signature_fractions(machine: list[list[int]], max_length: int = 8) -> list[list[Fraction]]:
    segments: list[list[Fraction]] = []
    for length in range(1, max_length + 1):
        segment = [
            sum(
                (word_probability(machine, state, tuple((index >> (length - pos - 1)) & 1 for pos in range(length)))
                 for state in range(4)),
                Fraction(0),
            ) / 4
            for index in range(2**length)
        ]
        if sum(segment, Fraction(0)) != 1:
            raise RunnerError("exact predictive segment is not normalized")
        segments.append(segment)
    return segments


def signature_tensor(machine: list[list[int]]) -> Tensor:
    values = [float(item) for segment in exact_signature_fractions(machine) for item in segment]
    return torch.tensor(values, dtype=torch.float32)


def exact_train_mean(manifest: dict[str, Any]) -> list[list[Fraction]]:
    train = [exact_signature_fractions(row["machine"]) for row in manifest["splits"]["train"]]
    return [
        [
            sum((signature[length][coordinate] for signature in train), Fraction(0)) / len(train)
            for coordinate in range(2 ** (length + 1))
        ]
        for length in range(8)
    ]


def fractions_to_tensor(segments: list[list[Fraction]]) -> Tensor:
    return torch.tensor(
        [float(value) for segment in segments for value in segment], dtype=torch.float32
    )


@dataclass(frozen=True)
class ViewRecord:
    visible: dict[str, Tensor]
    target: Tensor
    object_index: int
    view_index: int
    machine_sha256: str
    split: str


def simulate_view(
    machine: list[list[int]],
    split: str,
    machine_hash: str,
    view_index: int,
    seed_domain: str,
) -> dict[str, Tensor]:
    tokens = torch.empty((16, 12), dtype=torch.long)
    erasure = torch.empty((16, 12), dtype=torch.bool)
    boundary = torch.zeros((16, 12), dtype=torch.bool)
    boundary[:, 0] = True
    for trajectory_index in range(16):
        generator = torch.Generator(device="cpu")
        generator.manual_seed(
            stable_seed(
                seed_domain,
                machine_hash,
                split,
                view_index,
                trajectory_index,
                "channel",
            )
        )
        state = int(torch.randint(0, 4, (), generator=generator).item())
        for step in range(12):
            next_zero, next_one, p_one = machine[state]
            emitted = int(torch.rand((), generator=generator).item() < p_one / 8.0)
            state = next_one if emitted else next_zero
            erased = bool(torch.rand((), generator=generator).item() < 0.35)
            substituted = not erased and bool(torch.rand((), generator=generator).item() < 0.10)
            tokens[trajectory_index, step] = 0 if erased else emitted ^ substituted
            erasure[trajectory_index, step] = erased
    visible = {
        "corrupted_binary_tokens": tokens,
        "erasure_mask": erasure,
        "trajectory_boundary": boundary,
    }
    assert_model_visible_schema({key: value.unsqueeze(0) for key, value in visible.items()})
    return visible


def build_records(
    manifest: dict[str, Any], seed_domain: str, allowed_splits: Sequence[str]
) -> dict[str, list[ViewRecord]]:
    view_counts = {"train": 4, "validation": 4, "test": 8}
    records: dict[str, list[ViewRecord]] = {}
    for split in allowed_splits:
        if split == "test" and "test" not in allowed_splits:
            raise RunnerError("preflight attempted to open the test split")
        rows = manifest["splits"][split]
        split_records: list[ViewRecord] = []
        for object_index, row in enumerate(rows):
            target = signature_tensor(row["machine"])
            for view_index in range(view_counts[split]):
                split_records.append(
                    ViewRecord(
                        visible=simulate_view(
                            row["machine"], split, row["machine_sha256"], view_index, seed_domain
                        ),
                        target=target,
                        object_index=object_index,
                        view_index=view_index,
                        machine_sha256=row["machine_sha256"],
                        split=split,
                    )
                )
        records[split] = split_records
    return records


def validate_inputs(spec: dict[str, Any], manifest: dict[str, Any], include_test: bool) -> None:
    if spec.get("schema") != "codex_ratchet.unseen_finite_predictive_objects_v1.spec.v1":
        raise RunnerError("unexpected v1 spec schema")
    if manifest.get("schema") != "codex_ratchet.unseen_finite_predictive_objects_v1.object_manifest.v1":
        raise RunnerError("unexpected v1 manifest schema")
    if spec.get("sim_id") != SIM_ID or manifest.get("sim_id") != SIM_ID:
        raise RunnerError("sim_id binding mismatch")
    if manifest.get("spec_sha256") != sha256_file(SPEC_PATH):
        raise RunnerError("manifest/spec hash binding mismatch")
    if manifest.get("split_counts") != {"train": 128, "validation": 32, "test": 32}:
        raise RunnerError("frozen split count mismatch")
    expected_counts = {"train": 128, "validation": 32}
    if include_test:
        expected_counts["test"] = 32
    for split, count in expected_counts.items():
        if len(manifest["splits"][split]) != count:
            raise RunnerError(f"{split} manifest count mismatch")
    if spec["view_process"]["model_visible_fields"] != sorted(MODEL_VISIBLE_FIELDS):
        raise RunnerError("model-visible field binding mismatch")
    if spec["view_process"]["seed_domain"] != "ufpo-v1|view|split|machine-hash|view-index|trajectory-index|channel":
        raise RunnerError("view seed-domain binding mismatch")
    if spec["engine_contract"]["mode"] != "all_three_full_sims":
        raise RunnerError("engine mode binding mismatch")
    if spec["accepted_green_ceiling"] != "BOUNDED_SUPERVISED_MULTI_VIEW_PREDICTIVE_RETRIEVAL_ON_UNSEEN_FOUR_STATE_OBJECTS_UNDER_FROZEN_LOSSY_VIEWS":
        raise RunnerError("green claim ceiling binding mismatch")
    if set(spec["controls"]) != {"train_mean", "order2_laplace", "histogram", "temporal_shuffle", "optimizer_erased", "architecture_only", "deranged"}:
        raise RunnerError("control set drift")
    if TARGET_COORDINATES != spec["object_family"]["target_signature_coordinate_count"]:
        raise RunnerError("target coordinate count drift")
    if tuple(spec["view_process"]["model_seeds"]) != (2701, 2702, 2703):
        raise RunnerError("model seed drift")
    if spec["learner"]["epochs"] != 16 or spec["learner"]["learning_rate"] != 0.0003 or spec["learner"]["weight_decay"] != 0.0001:
        raise RunnerError("learner protocol drift")
    gates = spec["metrics_and_gates"]
    if "loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min" not in gates:
        raise RunnerError("retrieval gain gate field drift")
    if "full_observation_horizon_matched_own_target_prediction" not in gates:
        raise RunnerError("matched-pair gate field drift")
    if include_test and not manifest.get("test_pairing", {}).get("pairs"):
        raise RunnerError("missing frozen test pairing")


def collate_visible(records: Sequence[ViewRecord], device: torch.device) -> dict[str, Tensor]:
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
    denominator = torch.full(tokens.shape[:2], tokens.shape[-1], dtype=torch.float32, device=tokens.device)
    zero = ((tokens == 0) & valid).sum(dim=-1) / denominator
    one = ((tokens == 1) & valid).sum(dim=-1) / denominator
    missing = erased.sum(dim=-1) / denominator
    return torch.stack([zero, one, missing], dim=-1).flatten(start_dim=1)


class HistogramModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(48, 96), nn.GELU(), nn.Linear(96, 96), nn.GELU()
        )
        self.decoder = PredictiveDecoder()

    def forward(self, visible: dict[str, Tensor]) -> tuple[Tensor, Tensor]:
        embedding = self.encoder(histogram_features(visible))
        return embedding, self.decoder(embedding)


def model_for_arm(arm: str) -> nn.Module:
    return HistogramModel() if arm == "histogram" else GRUDeepSets()


def contrastive_loss(embedding: Tensor, source_objects: Tensor, positive_objects: Tensor) -> Tensor:
    normalized = nn.functional.normalize(embedding, dim=-1)
    similarity = normalized @ normalized.T / 0.1
    diagonal = torch.eye(similarity.shape[0], dtype=torch.bool, device=similarity.device)
    candidate_mask = ~diagonal
    positive_mask = (source_objects.unsqueeze(0) == positive_objects.unsqueeze(1)) & candidate_mask
    if not bool(torch.all(positive_mask.any(dim=1))):
        raise RunnerError("InfoNCE batch has an object without a positive view")
    denominator = torch.logsumexp(similarity.masked_fill(~candidate_mask, -torch.inf), dim=1)
    numerator = torch.logsumexp(similarity.masked_fill(~positive_mask, -torch.inf), dim=1)
    return (denominator - numerator).mean()


def predictive_cross_entropy(logits: Tensor, target: Tensor) -> Tensor:
    losses = []
    for target_segment, log_probability in zip(
        target.split(SEGMENTS, dim=-1), segment_log_probabilities(logits), strict=True
    ):
        losses.append(-(target_segment * log_probability).sum(dim=-1).mean())
    return torch.stack(losses).mean()


def shuffled_visible(visible: dict[str, Tensor], records: Sequence[ViewRecord], seed: int) -> dict[str, Tensor]:
    shuffled = {key: value.clone() for key, value in visible.items()}
    for batch_index, record in enumerate(records):
        for trajectory_index in range(16):
            generator = torch.Generator(device="cpu")
            generator.manual_seed(
                stable_seed("ufpo-v1|temporal-shuffle", seed, record.machine_sha256, record.split, record.view_index, trajectory_index)
            )
            permutation = torch.randperm(12, generator=generator).to(visible["corrupted_binary_tokens"].device)
            for key in ("corrupted_binary_tokens", "erasure_mask"):
                shuffled[key][batch_index, trajectory_index] = visible[key][batch_index, trajectory_index, permutation]
    assert_model_visible_schema(shuffled)
    return shuffled


def object_batches(records: Sequence[ViewRecord], objects_per_batch: int = 32) -> Iterable[list[ViewRecord]]:
    by_object: dict[int, list[ViewRecord]] = {}
    for record in records:
        by_object.setdefault(record.object_index, []).append(record)
    object_ids = sorted(by_object)
    for start in range(0, len(object_ids), objects_per_batch):
        selected = object_ids[start : start + objects_per_batch]
        yield [record for object_id in selected for record in by_object[object_id]]


def deranged_indices(source_objects: Tensor, object_count: int) -> Tensor:
    if object_count % 2:
        raise RunnerError("adjacent derangement requires an even object count")
    return source_objects ^ 1


def train_arm(
    arm: str,
    seed: int,
    train_records: list[ViewRecord],
    targets_by_object: Tensor,
    device: torch.device,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
) -> tuple[nn.Module, dict[str, Any]]:
    torch.manual_seed(seed)
    random.seed(seed)
    if device.type == "mps":
        torch.mps.manual_seed(seed)
    model = model_for_arm(arm).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=0.0 if arm == "optimizer_erased" else learning_rate, weight_decay=weight_decay
    )
    loss_trace: list[float] = []
    update_steps = 0
    if arm != "architecture_only":
        model.train()
        for _epoch in range(epochs):
            epoch_losses: list[float] = []
            for batch_records in object_batches(train_records):
                visible = collate_visible(batch_records, device)
                if arm == "temporal_shuffle":
                    visible = shuffled_visible(visible, batch_records, seed)
                source_objects = torch.tensor([record.object_index for record in batch_records], dtype=torch.long, device=device)
                if arm == "fixed_deranged":
                    positive_objects = deranged_indices(source_objects, len(targets_by_object))
                    target = targets_by_object.to(device)[positive_objects]
                else:
                    positive_objects = source_objects
                    target = torch.stack([record.target for record in batch_records]).to(device)
                optimizer.zero_grad(set_to_none=True)
                embedding, logits = model(visible)
                loss = predictive_cross_entropy(logits, target) + contrastive_loss(embedding, source_objects, positive_objects)
                loss.backward()
                optimizer.step()
                epoch_losses.append(float(loss.detach().cpu()))
                update_steps += 1
            loss_trace.append(sum(epoch_losses) / len(epoch_losses))
    return model, {
        "epochs_budgeted": epochs,
        "epochs_with_gradient_steps": 0 if arm == "architecture_only" else epochs,
        "optimizer": "AdamW",
        "learning_rate": 0.0 if arm == "optimizer_erased" else learning_rate,
        "weight_decay": weight_decay,
        "update_steps": update_steps,
        "epoch_loss": loss_trace,
        "checkpoint_scored": epochs,
    }


def predict_records(
    model: nn.Module, records: Sequence[ViewRecord], device: torch.device, arm: str, seed: int
) -> tuple[Tensor, Tensor, Tensor]:
    embeddings: list[Tensor] = []
    predictions: list[Tensor] = []
    labels: list[int] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(records), 64):
            batch_records = list(records[start : start + 64])
            visible = collate_visible(batch_records, device)
            if arm == "temporal_shuffle":
                visible = shuffled_visible(visible, batch_records, seed)
            embedding, logits = model(visible)
            embeddings.append(nn.functional.normalize(embedding, dim=-1).cpu())
            predictions.append(torch.cat(segment_probabilities(logits), dim=-1).cpu())
            labels.extend(record.object_index for record in batch_records)
    return torch.cat(embeddings), torch.cat(predictions), torch.tensor(labels, dtype=torch.long)


def js_by_segment(predictions: Tensor, targets: Tensor) -> Tensor:
    values: list[Tensor] = []
    for predicted, target in zip(predictions.split(SEGMENTS, dim=-1), targets.split(SEGMENTS, dim=-1), strict=True):
        midpoint = 0.5 * (predicted + target)
        left = 0.5 * (predicted * (predicted.clamp_min(1e-12).log() - midpoint.clamp_min(1e-12).log())).sum(dim=-1)
        right = 0.5 * (target * (target.clamp_min(1e-12).log() - midpoint.clamp_min(1e-12).log())).sum(dim=-1)
        values.append(left + right)
    return torch.stack(values, dim=-1)


def target_rows(records: Sequence[ViewRecord]) -> Tensor:
    return torch.stack([record.target for record in records])


def retrieval(embeddings: Tensor, labels: Tensor) -> tuple[Tensor, Tensor]:
    similarity = embeddings @ embeddings.T
    similarity.fill_diagonal_(-torch.inf)
    neighbors = similarity.argmax(dim=1)
    correct = labels[neighbors] == labels
    return neighbors, correct


def per_object_mean(values: Tensor, labels: Tensor, object_count: int) -> Tensor:
    return torch.stack([values[labels == index].mean(dim=0) for index in range(object_count)])


def view_output_rows(
    embeddings: Tensor,
    predictions: Tensor,
    labels: Tensor,
    js_values: Tensor,
    neighbors: Tensor,
    retrieval_correct: Tensor,
    records: Sequence[ViewRecord],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    split_predictions = predictions.split(SEGMENTS, dim=-1)
    for index, record in enumerate(records):
        rows.append(
            {
                "view_index": index,
                "object_label": int(labels[index]),
                "controller_only_label": True,
                "normalized_embedding": embeddings[index].tolist(),
                "segmented_prediction": [segment[index].tolist() for segment in split_predictions],
                "prediction_coordinate_count": TARGET_COORDINATES,
                "per_horizon_js": {str(horizon): float(js_values[index, horizon - 1]) for horizon in HORIZONS},
                "retrieval_neighbor_index": int(neighbors[index]),
                "retrieval_correct": bool(retrieval_correct[index]),
                "machine_sha256_controller_only": record.machine_sha256,
            }
        )
    return rows


def baseline_view_rows(
    predictions: Tensor,
    labels: Tensor,
    targets: Tensor,
    records: Sequence[ViewRecord],
    embedding_kind: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    embeddings = torch.ones((len(records), 1), dtype=torch.float32)
    js_values = js_by_segment(predictions, targets)
    neighbors, correct = retrieval(embeddings, labels)
    rows = view_output_rows(embeddings, predictions, labels, js_values, neighbors, correct, records)
    for row in rows:
        row["embedding_kind"] = embedding_kind
    return rows, metric_summary(predictions, embeddings, labels, targets, records, js_values, neighbors, correct)


def laplace1_order2(visible: dict[str, Tensor]) -> Tensor:
    assert_model_visible_schema(visible)
    counts = torch.ones((4, 2), dtype=torch.float64)
    initial = torch.ones((4,), dtype=torch.float64)
    tokens = visible["corrupted_binary_tokens"].cpu()
    erased = visible["erasure_mask"].cpu()
    for trajectory in range(tokens.shape[0]):
        values = tokens[trajectory].tolist()
        missing = erased[trajectory].tolist()
        valid_positions = [index for index in range(12) if not missing[index]]
        if len(valid_positions) >= 2:
            initial[values[valid_positions[0]] * 2 + values[valid_positions[1]]] += 1.0
        for position in range(2, len(valid_positions)):
            a, b, c = (values[valid_positions[position - offset]] for offset in (2, 1, 0))
            counts[a * 2 + b, c] += 1.0
    initial /= initial.sum()
    transition = counts / counts.sum(dim=-1, keepdim=True)
    distributions: list[Tensor] = []
    for length in range(1, 9):
        probabilities = []
        for word_index in range(2**length):
            word = [(word_index >> (length - pos - 1)) & 1 for pos in range(length)]
            if length == 1:
                probability = initial.view(2, 2).sum(dim=1)[word[0]]
            else:
                probability = initial[word[0] * 2 + word[1]]
                for pos in range(2, length):
                    probability = probability * transition[word[pos - 2] * 2 + word[pos - 1], word[pos]]
            probabilities.append(probability)
        segment = torch.stack(probabilities).to(dtype=torch.float32)
        segment /= segment.sum()
        distributions.append(segment)
    return torch.cat(distributions)


def metric_summary(
    predictions: Tensor,
    embeddings: Tensor,
    labels: Tensor,
    targets: Tensor,
    records: Sequence[ViewRecord],
    js_values: Tensor | None = None,
    neighbors: Tensor | None = None,
    correct: Tensor | None = None,
) -> dict[str, Any]:
    if js_values is None:
        js_values = js_by_segment(predictions, targets)
    if neighbors is None or correct is None:
        neighbors, correct = retrieval(embeddings, labels)
    object_js = per_object_mean(js_values[:, [h - 1 for h in HORIZONS]], labels, 32)
    return {
        "view_count": len(records),
        "object_count": len(set(labels.tolist())),
        "loo_same_object_retrieval": float(correct.float().mean()),
        "per_horizon_predictive_js_mean": {str(h): float(object_js[:, i].mean()) for i, h in enumerate(HORIZONS)},
        "per_horizon_predictive_js_max": {str(h): float(object_js[:, i].max()) for i, h in enumerate(HORIZONS)},
        "per_object_predictive_js": object_js.tolist(),
        "retrieval_neighbor_indices": neighbors.tolist(),
        "retrieval_correct": correct.tolist(),
    }


def temporal_jacrev_receipt(model: nn.Module, record: ViewRecord, device: torch.device) -> dict[str, Any]:
    if not isinstance(model, GRUDeepSets):
        return {"passed": False, "role": "supportive_only", "reason": "histogram has no temporal GRU"}
    model.eval()
    visible = collate_visible([record], device)
    base = model.continuous_inputs(visible).detach()
    direction = torch.zeros((26,), dtype=base.dtype, device=device)
    direction[0] = 1.0
    amplitudes = torch.zeros((12,), dtype=base.dtype, device=device)

    def response(time_amplitude: Tensor, feature_direction: Tensor) -> Tensor:
        perturbation = time_amplitude.view(1, 1, 12, 1) * feature_direction.view(1, 1, 1, 26)
        return model.encode_continuous(base + perturbation).squeeze(0)

    jacobian = jacrev(lambda values: response(values, direction))(amplitudes)
    erased = jacrev(lambda values: response(values, torch.zeros_like(direction)))(amplitudes)
    with torch.no_grad():
        boundary_difference = float((response(amplitudes, direction) - model.encode_continuous(base).squeeze(0)).abs().max().cpu())
    positive_l1 = float(jacobian.abs().sum().detach().cpu())
    erased_l1 = float(erased.abs().sum().detach().cpu())
    finite = bool(torch.isfinite(jacobian).all())
    return {
        "tool": "torch.func",
        "qualified_api": "torch.func.jacrev",
        "role": "supportive_only",
        "input_object": "validation view continuous time-amplitude vector",
        "output_object": "96_by_12 temporal-sensitivity Jacobian",
        "positive_jacobian_l1": positive_l1,
        "erased_jacobian_l1": erased_l1,
        "zero_amplitude_max_abs_difference": boundary_difference,
        "passed": finite and positive_l1 > 1e-8 and erased_l1 == 0.0 and boundary_difference < 1e-6,
    }


def add_baseline_comparisons(metrics: dict[str, Any], baseline_metrics: dict[str, dict[str, Any]]) -> None:
    learned = metrics["per_object_predictive_js"]
    comparisons: list[dict[str, Any]] = []
    for object_index, learned_row in enumerate(learned):
        comparisons.append(
            {
                "object_index": object_index,
                "learned_per_horizon_js": {str(h): learned_row[i] for i, h in enumerate(HORIZONS)},
                "baselines": {
                    name: {
                        "baseline_per_horizon_js": {
                            str(h): baseline["per_object_predictive_js"][object_index][i]
                            for i, h in enumerate(HORIZONS)
                        },
                        "baseline_minus_learned": {
                            str(h): baseline["per_object_predictive_js"][object_index][i] - learned_row[i]
                            for i, h in enumerate(HORIZONS)
                        },
                    }
                    for name, baseline in baseline_metrics.items()
                },
            }
        )
    metrics["per_object_baseline_comparisons"] = comparisons


def matched_pair_decisions(
    manifest: dict[str, Any], records: Sequence[ViewRecord], predictions: Tensor
) -> list[dict[str, Any]]:
    target_by_object = torch.stack([record.target for record in records[::8]])
    labels = torch.tensor([record.object_index for record in records], dtype=torch.long)
    js = js_by_segment(predictions, torch.stack([target_by_object[int(label)] for label in labels]))
    hash_to_object = {row["machine_sha256"]: index for index, row in enumerate(manifest["splits"]["test"])}
    object_js = per_object_mean(js[:, [h - 1 for h in HORIZONS]], labels, 32)
    decisions: list[dict[str, Any]] = []
    for pair_index, pair in enumerate(manifest["test_pairing"]["pairs"]):
        left = hash_to_object[pair["left_machine_sha256"]]
        right = hash_to_object[pair["right_machine_sha256"]]
        left_own = object_js[left]
        left_partner = object_js[right]
        right_own = object_js[right]
        right_partner = object_js[left]
        left_better = bool(left_own.mean() < left_partner.mean())
        right_better = bool(right_own.mean() < right_partner.mean())
        decisions.append(
            {
                "pair_index": pair_index,
                "left_object_index": left,
                "right_object_index": right,
                "left_own_target_prediction": left_better,
                "right_own_target_prediction": right_better,
                "both_members_own_target_prediction": left_better and right_better,
                "left_own_vs_partner_js": {str(h): [float(left_own[i]), float(left_partner[i])] for i, h in enumerate(HORIZONS)},
                "right_own_vs_partner_js": {str(h): [float(right_own[i]), float(right_partner[i])] for i, h in enumerate(HORIZONS)},
            }
        )
    if len(decisions) != 16:
        raise RunnerError("frozen pairing must produce exactly 16 decisions")
    return decisions


def evaluate_gates(
    arm_results: dict[str, dict[str, dict[str, Any]]],
    baseline_results: dict[str, dict[str, Any]],
    pair_decisions: dict[str, list[dict[str, Any]]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    gates_by_seed: dict[str, Any] = {}
    gate_spec = spec["metrics_and_gates"]
    retrieval_min = float(gate_spec["loo_same_object_retrieval_min"])
    retrieval_gain_min = float(gate_spec["loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min"])
    predictive_spec = {
        name: (float(values["max"]), int(values["wins"]))
        for name, values in gate_spec["predictive_js"].items()
        if isinstance(values, dict)
    }
    for seed in arm_seed_plan(spec)["full"]:
        full = arm_results["full"][str(seed)]["metrics"]
        histogram = arm_results["histogram"][str(seed)]["metrics"]
        temporal = arm_results["temporal_shuffle"][str(seed)]["metrics"]
        seed_gates: dict[str, Any] = {
            "loo_same_object_retrieval_min": full["loo_same_object_retrieval"] >= retrieval_min,
            "loo_retrieval_gain_over_each_of_histogram_and_temporal_min": {
                "histogram": full["loo_same_object_retrieval"] - histogram["loo_same_object_retrieval"] >= retrieval_gain_min,
                "temporal_shuffle": full["loo_same_object_retrieval"] - temporal["loo_same_object_retrieval"] >= retrieval_gain_min,
            },
            "own_target_prediction": sum(item["both_members_own_target_prediction"] for item in pair_decisions[str(seed)]) >= int(gate_spec["full_observation_horizon_matched_own_target_prediction"]["both_members_own_target_min"]),
        }
        predictive_gates: dict[str, Any] = {}
        for baseline_name, (maximum, wins_min) in predictive_spec.items():
            arm_name = "temporal_shuffle" if baseline_name == "temporal" else baseline_name
            baseline = baseline_results[str(seed)] if baseline_name in {"train_mean", "order2_laplace"} else arm_results[arm_name][str(seed)]
            baseline_metrics = baseline["metrics"]
            full_wins: dict[str, int] = {}
            horizon_ok: dict[str, bool] = {}
            baseline_max_ok: dict[str, bool] = {}
            for horizon in HORIZONS:
                key = str(horizon)
                full_rows = full["per_object_predictive_js"]
                baseline_rows = baseline_metrics["per_object_predictive_js"]
                wins = sum(full_rows[index][horizon - 3] < baseline_rows[index][horizon - 3] for index in range(32))
                full_wins[key] = wins
                horizon_ok[key] = wins >= wins_min
                baseline_max_ok[key] = max(row[horizon - 3] for row in baseline_rows) <= maximum
            predictive_gates[baseline_name] = {
                "wins_by_horizon": full_wins,
                "wins_min": wins_min,
                "baseline_max_by_horizon_within_spec": baseline_max_ok,
                "all_horizons_win_gate": all(horizon_ok.values()),
                "all_horizons_baseline_max_gate": all(baseline_max_ok.values()),
            }
        seed_gates["predictive_js"] = predictive_gates
        seed_gates["primary_pass"] = all(
            [
                seed_gates["loo_same_object_retrieval_min"],
                all(seed_gates["loo_retrieval_gain_over_each_of_histogram_and_temporal_min"].values()),
                seed_gates["own_target_prediction"],
                all(item["all_horizons_win_gate"] and item["all_horizons_baseline_max_gate"] for item in predictive_gates.values()),
            ]
        )
        gates_by_seed[str(seed)] = seed_gates
    return {
        "thresholds_from_spec": {
            "loo_same_object_retrieval_min": retrieval_min,
            "loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min": retrieval_gain_min,
            "own_target_prediction": gate_spec["full_observation_horizon_matched_own_target_prediction"],
            "predictive_js": predictive_spec,
        },
        "by_seed": gates_by_seed,
        "all_primary_gates_every_seed": all(item["primary_pass"] for item in gates_by_seed.values()),
        "temporal_jacrev_supportive_only": True,
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(json_ready(payload), handle, indent=2, sort_keys=True, allow_nan=False)
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


def clean_tracked_source() -> bool:
    relative_paths = [
        str(SOURCE_PATH.relative_to(HERE.parents[2])),
        str(RECOMPUTE_PATH.relative_to(HERE.parents[2])),
    ]
    for relative in relative_paths:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative],
            cwd=HERE.parents[2], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if tracked.returncode != 0:
            return False
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", relative],
            cwd=HERE.parents[2], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False,
        )
        if status.returncode != 0 or status.stdout.strip():
            return False
    return True


def validate_seal_receipt(spec_hash: str, manifest_hash: str) -> dict[str, Any]:
    receipt = load_json(SEAL_RECEIPT_PATH)
    required = {
        "schema", "sim_id", "seal_status", "learner_source_sealed",
        "source_sha256", "spec_sha256", "object_manifest_sha256",
        "recompute_metrics_sha256",
    }
    if not required.issubset(receipt):
        raise RunnerError("seal receipt is missing a required hash binding")
    if receipt["schema"] != "codex_ratchet.unseen_finite_predictive_objects_v1.seal_receipt.v1":
        raise RunnerError("unexpected seal receipt schema")
    if receipt["sim_id"] != SIM_ID or receipt["seal_status"] != "sealed" or receipt["learner_source_sealed"] is not True:
        raise RunnerError("seal receipt does not declare the accepted v1 learner seal")
    if receipt["source_sha256"] != sha256_file(SOURCE_PATH) or receipt["spec_sha256"] != spec_hash or receipt["object_manifest_sha256"] != manifest_hash:
        raise RunnerError("seal receipt hash binding mismatch")
    if receipt["recompute_metrics_sha256"] != sha256_file(RECOMPUTE_PATH):
        raise RunnerError("seal receipt recompute source hash mismatch")
    return receipt


def run_preflight(spec: dict[str, Any], manifest: dict[str, Any], requested_device: str) -> dict[str, Any]:
    device = choose_device(requested_device)
    torch.use_deterministic_algorithms(True, warn_only=False)
    validation_summary: dict[str, Any] = {}
    seed_plan = arm_seed_plan(spec)
    model_seeds = tuple(int(value) for value in spec["view_process"]["model_seeds"])
    learner = spec["learner"]
    records = build_records(manifest, spec["view_process"]["seed_domain"], ("train", "validation"))
    train_targets = torch.stack([records["train"][index * 4].target for index in range(128)])
    for seed in model_seeds:
        for arm in ARM_NAMES:
            if seed not in seed_plan[arm]:
                continue
            model, training = train_arm(arm, seed, records["train"], train_targets, device, learner["epochs"], learner["learning_rate"], learner["weight_decay"])
            embeddings, predictions, labels = predict_records(model, records["validation"], device, arm, seed)
            targets = target_rows(records["validation"])
            metrics = metric_summary(predictions, embeddings, labels, targets, records["validation"])
            validation_summary[f"{arm}:{seed}"] = {
                "training": training,
                "validation_view_count": metrics["view_count"],
                "validation_retrieval": metrics["loo_same_object_retrieval"],
                "validation_predictive_js": metrics["per_horizon_predictive_js_mean"],
            }
            del model
    return {
        "mode": "preflight",
        "test_views_opened": False,
        "test_views_generated": False,
        "result_written": False,
        "source_sha256": sha256_file(SOURCE_PATH),
        "spec_sha256": sha256_file(SPEC_PATH),
        "object_manifest_sha256": sha256_file(MANIFEST_PATH),
        "validation": validation_summary,
        "device": str(device),
    }


def run_sealed_test(spec: dict[str, Any], manifest: dict[str, Any], requested_device: str) -> dict[str, Any]:
    spec_hash = sha256_file(SPEC_PATH)
    manifest_hash = sha256_file(MANIFEST_PATH)
    if not clean_tracked_source():
        raise RunnerError("sealed-test requires clean tracked run_pytorch.py and recompute_metrics.py")
    seal_receipt = validate_seal_receipt(spec_hash, manifest_hash)
    if RESULT_PATH.exists():
        raise RunnerError(f"sealed result already exists; refusing overwrite: {RESULT_PATH}")
    device = choose_device(requested_device)
    torch.use_deterministic_algorithms(True, warn_only=False)
    arm_results: dict[str, dict[str, dict[str, Any]]] = {arm: {} for arm in ARM_NAMES}
    baseline_results: dict[str, dict[str, Any]] = {}
    pair_decisions: dict[str, list[dict[str, Any]]] = {}
    jacrev_receipts: dict[str, Any] = {}
    seed_plan = arm_seed_plan(spec)
    model_seeds = tuple(int(value) for value in spec["view_process"]["model_seeds"])
    learner = spec["learner"]
    records = build_records(manifest, spec["view_process"]["seed_domain"], ("train", "validation", "test"))
    train_targets = torch.stack([records["train"][index * 4].target for index in range(128)])
    for seed in model_seeds:
        test_records = records["test"]
        test_targets = target_rows(test_records)
        train_mean_prediction = fractions_to_tensor(exact_train_mean(manifest)).expand(len(test_records), -1)
        mean_rows, mean_metrics = baseline_view_rows(
            train_mean_prediction,
            torch.tensor([record.object_index for record in test_records]),
            test_targets,
            test_records,
            "constant_exact_train_mean",
        )
        laplace_predictions = torch.stack([laplace1_order2(record.visible) for record in test_records])
        laplace_rows, laplace_metrics = baseline_view_rows(
            laplace_predictions,
            torch.tensor([record.object_index for record in test_records]),
            test_targets,
            test_records,
            "per_visible_view_laplace1_order2",
        )
        baseline_results[str(seed)] = {
            "train_mean": {"metrics": mean_metrics, "raw_outputs": mean_rows},
            "order2_laplace": {"metrics": laplace_metrics, "raw_outputs": laplace_rows},
        }
        for arm in ARM_NAMES:
            if seed not in seed_plan[arm]:
                continue
            started = time.perf_counter()
            model, training = train_arm(arm, seed, records["train"], train_targets, device, learner["epochs"], learner["learning_rate"], learner["weight_decay"])
            embeddings, predictions, labels = predict_records(model, test_records, device, arm, seed)
            js_values = js_by_segment(predictions, test_targets)
            neighbors, correct = retrieval(embeddings, labels)
            metrics = metric_summary(predictions, embeddings, labels, test_targets, test_records, js_values, neighbors, correct)
            if arm == "full":
                jacrev_receipts[str(seed)] = temporal_jacrev_receipt(model, records["validation"][0], device)
            rows = view_output_rows(embeddings, predictions, labels, js_values, neighbors, correct, test_records)
            arm_results[arm][str(seed)] = {
                "training": training,
                "metrics": metrics,
                "raw_outputs": rows,
                "runtime_seconds": time.perf_counter() - started,
            }
            if arm == "full":
                pair_decisions[str(seed)] = matched_pair_decisions(manifest, test_records, predictions)
            del model
            if device.type == "mps":
                torch.mps.empty_cache()
            elif device.type == "cuda":
                torch.cuda.empty_cache()
    baseline_by_seed = {
        seed: {name: value["metrics"] for name, value in rows.items()}
        for seed, rows in baseline_results.items()
    }
    for arm in ARM_NAMES:
        for seed, row in arm_results[arm].items():
            add_baseline_comparisons(row["metrics"], {
                "train_mean": baseline_by_seed[seed]["train_mean"],
                "order2_laplace": baseline_by_seed[seed]["order2_laplace"],
                "histogram": arm_results["histogram"][seed]["metrics"] if arm != "histogram" and seed in arm_results["histogram"] else row["metrics"],
                "temporal_shuffle": arm_results["temporal_shuffle"][seed]["metrics"] if arm != "temporal_shuffle" and seed in arm_results["temporal_shuffle"] else row["metrics"],
            })
    gates = evaluate_gates(arm_results, {
        seed: {name: rows[name] for name in ("train_mean", "order2_laplace")} for seed, rows in baseline_results.items()
    }, pair_decisions, spec)
    raw_payload = {
        "arm_results": {arm: {seed: row["raw_outputs"] for seed, row in rows.items()} for arm, rows in arm_results.items()},
        "baseline_results": {seed: {name: row["raw_outputs"] for name, row in rows.items()} for seed, rows in baseline_results.items()},
    }
    result = {
        "schema": "codex_ratchet.unseen_finite_predictive_objects_v1.pytorch_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_sha256": sha256_file(SOURCE_PATH),
        "recompute_metrics_sha256": sha256_file(RECOMPUTE_PATH),
        "spec_sha256": spec_hash,
        "object_manifest_sha256": manifest_hash,
        "seal_receipt_sha256": sha256_file(SEAL_RECEIPT_PATH),
        "seal_receipt_schema": seal_receipt["schema"],
        "model_visible_schema": sorted(MODEL_VISIBLE_FIELDS),
        "model_forbidden_schema": sorted(MODEL_FORBIDDEN_FIELDS),
        "schema_assertion_enforced_before_every_model_call": True,
        "model_call_schema_only_visible_tensors": True,
        "reads_peer_result": False,
        "numpy_imported": False,
        "forbidden_metrics": ["K", "ARI", "Bcubed"],
        "protocol": {
            "trajectories_per_view": 16,
            "trajectory_length": 12,
            "views_per_split": {"train": 4, "validation": 4, "test": 8},
            "model_seeds": list(model_seeds),
            "epochs": learner["epochs"],
            "learning_rate": learner["learning_rate"],
            "weight_decay": learner["weight_decay"],
            "checkpoint_policy": "epoch 16 only; no early stopping or test-aware selection",
            "arms": list(ARM_NAMES),
            "arm_seed_plan": {arm: list(seeds) for arm, seeds in seed_plan.items()},
            "fixed_derangement": "object_index XOR 1 within each even-sized object batch for targets and contrastive positives",
            "temporal_shuffle": "fixed joint token/mask permutation per trajectory; boundary remains first",
        },
        "module_contract": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "semantic_owner": "independent exact finite predictive-equivalence verification",
            "jacrev_role": "supportive_only; excluded from all_pass",
            "test_labels": "controller_only; never training or threshold selection",
            "preflight_test_boundary": "preflight refuses test views and result output",
            "sealed_test_boundary": "future seal receipt plus clean tracked owned sources required",
            "mode": "all_three",
            "engine_contract_mode": spec["engine_contract"]["mode"],
        },
        "architecture": {
            "token_embedding_width": 24,
            "bidirectional_gru_layers": 2,
            "gru_hidden_width": 64,
            "deepsets_pool": "mean over 16 independently encoded trajectories",
            "view_embedding_width": 96,
            "decoder_segments": list(SEGMENTS),
            "prediction_coordinate_count": TARGET_COORDINATES,
        },
        "arm_results": arm_results,
        "baseline_results": baseline_results,
        "matched_pair_decisions": pair_decisions,
        "torch_func_jacrev_supportive": jacrev_receipts,
        "gates": gates,
        "all_pass": gates["all_primary_gates_every_seed"],
        "accepted_ceiling": spec["accepted_green_ceiling"] if gates["all_primary_gates_every_seed"] else spec["accepted_red_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
        "raw_outputs_sha256": sha256_json(raw_payload),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": os.sys.version, "torch": torch.__version__, "device": str(device)},
    }
    if RESULT_PATH.exists():
        raise RunnerError("sealed result appeared during run; refusing overwrite")
    atomic_write_json(RESULT_PATH, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--sealed-test", action="store_true")
    parser.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    args = parser.parse_args()
    spec = load_json(SPEC_PATH)
    manifest = load_json(MANIFEST_PATH)
    validate_inputs(spec, manifest, include_test=args.sealed_test)
    if args.preflight:
        output = run_preflight(spec, manifest, args.device)
    else:
        output = run_sealed_test(spec, manifest, args.device)
    print(json.dumps(json_ready(output), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
