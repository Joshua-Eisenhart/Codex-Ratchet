#!/usr/bin/env python3
"""PyG learned-proxy lane for held-out ECA behavioral equivalence.

This lane independently constructs its finite labels from the frozen v1 spec.
It never reads Julia or JAX results and never gives learned scores semantic
authority. Rule information reaches the model only through the two successor
edges of each ordered state-pair node.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Iterable, Sequence

import torch
import torch.nn.functional as F
from torch import Tensor, nn
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing


SIM_ID = "finite_probe_behavioral_object_engine_v1"
CLASSIFICATION = "scratch_diagnostic"
HERE = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
SPEC_PATH = HERE / "spec.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
OBJECT_CARD_PATH = HERE / "wizard_v4_3_object_card.json"
RESULT_PATH = HERE / "results" / f"{SIM_ID}_pytorch_results.json"

RING_SIZE = 6
STATE_COUNT = 1 << RING_SIZE
PAIR_COUNT = STATE_COUNT * STATE_COUNT
HIDDEN_DIM = 24
MESSAGE_PASSING_STEPS = 6
LEARNING_RATE = 3.0e-3
WEIGHT_DECAY = 1.0e-5
MAX_EPOCHS = 300
PATIENCE = 30
SEEDS = (730_241, 730_251, 730_261)
CONTROL_SEEDS = SEEDS

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "balanced BCE, autograd, Adam optimization, exact metrics, and raw prediction receipts",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing six-step MessagePassing over rule-dependent ordered-pair successor graphs",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch_geometric": "load_bearing",
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def state_bits(state: int) -> tuple[int, ...]:
    return tuple((state >> site) & 1 for site in range(RING_SIZE))


def bits_state(bits: Iterable[int]) -> int:
    value = 0
    for site, bit in enumerate(bits):
        value |= int(bit) << site
    return value


def rotate_state(state: int, offset: int) -> int:
    bits = state_bits(state)
    return bits_state(bits[(site - offset) % RING_SIZE] for site in range(RING_SIZE))


def probes(state: int) -> tuple[int, int]:
    bits = state_bits(state)
    weight = sum(bits)
    walls = sum(bits[site] != bits[(site + 1) % RING_SIZE] for site in range(RING_SIZE))
    return weight, walls


def eca_step(rule: int, state: int) -> int:
    bits = state_bits(state)
    output = []
    for site in range(RING_SIZE):
        left = bits[(site - 1) % RING_SIZE]
        center = bits[site]
        right = bits[(site + 1) % RING_SIZE]
        neighborhood = (left << 2) | (center << 1) | right
        output.append((rule >> neighborhood) & 1)
    return bits_state(output)


def transition_table(rule: int) -> tuple[int, ...]:
    return tuple(eca_step(rule, state) for state in range(STATE_COUNT))


def canonical_labels(signatures: Sequence[Any]) -> tuple[int, ...]:
    lookup: dict[Any, int] = {}
    labels: list[int] = []
    for signature in signatures:
        if signature not in lookup:
            lookup[signature] = len(lookup)
        labels.append(lookup[signature])
    return tuple(labels)


def refine_labels(
    labels: tuple[int, ...], transition_a: tuple[int, ...], transition_b: tuple[int, ...]
) -> tuple[int, ...]:
    return canonical_labels(
        tuple((labels[state], labels[transition_a[state]], labels[transition_b[state]]) for state in range(STATE_COUNT))
    )


def exact_partition(rule_a: int, rule_b: int) -> dict[str, Any]:
    transition_a = transition_table(rule_a)
    transition_b = transition_table(rule_b)
    depth_labels = [canonical_labels(tuple(probes(state) for state in range(STATE_COUNT)))]
    for _ in range(63):
        refined = refine_labels(depth_labels[-1], transition_a, transition_b)
        depth_labels.append(refined)
        if refined == depth_labels[-2]:
            break
    else:
        raise RuntimeError(f"partition did not stabilize for rules {(rule_a, rule_b)}")
    stable = depth_labels[-1]
    return {
        "rules": [rule_a, rule_b],
        "transition_a": transition_a,
        "transition_b": transition_b,
        "depth_labels": depth_labels,
        "stable_labels": stable,
        "stabilization_depth": len(depth_labels) - 1,
        "class_count": len(set(stable)),
        "partition_sha256": sha256_json(list(stable)),
    }


def same_class_targets(labels: Sequence[int]) -> Tensor:
    label_tensor = torch.tensor(labels, dtype=torch.long)
    return (label_tensor[:, None] == label_tensor[None, :]).reshape(-1)


def pair_index(left: int, right: int) -> int:
    return left * STATE_COUNT + right


def ordered_pair_edges(
    transition_a: Sequence[int], transition_b: Sequence[int], mode: str = "intact"
) -> Tensor:
    if mode == "erased":
        return torch.empty((2, 0), dtype=torch.long)
    current: list[int] = []
    successor: list[int] = []
    for left in range(STATE_COUNT):
        for right in range(STATE_COUNT):
            node = pair_index(left, right)
            current.extend((node, node))
            if mode == "self":
                successor.extend((node, node))
            elif mode == "intact":
                successor.extend(
                    (
                        pair_index(transition_a[left], transition_a[right]),
                        pair_index(transition_b[left], transition_b[right]),
                    )
                )
            else:
                raise ValueError(f"unknown edge mode: {mode}")
    return torch.tensor((current, successor), dtype=torch.long)


def graph_for_partition(
    partition: dict[str, Any], edge_mode: str = "intact", erase_probe: bool = False
) -> Data:
    probe_values = [probes(state) for state in range(STATE_COUNT)]
    feature = torch.tensor(
        [
            0.0 if erase_probe else float(probe_values[left] == probe_values[right])
            for left in range(STATE_COUNT)
            for right in range(STATE_COUNT)
        ],
        dtype=torch.float64,
    ).reshape(PAIR_COUNT, 1)
    return Data(
        x=feature,
        edge_index=ordered_pair_edges(
            partition["transition_a"], partition["transition_b"], edge_mode
        ),
        y=same_class_targets(partition["stable_labels"]).to(dtype=torch.float64),
    )


def reflect_rule(rule: int) -> int:
    reflected = 0
    for left in (0, 1):
        for center in (0, 1):
            for right in (0, 1):
                source = (right << 2) | (center << 1) | left
                target = (left << 2) | (center << 1) | right
                reflected |= ((rule >> source) & 1) << target
    return reflected


def conjugate_rule(rule: int) -> int:
    conjugated = 0
    for left in (0, 1):
        for center in (0, 1):
            for right in (0, 1):
                source = ((1 - left) << 2) | ((1 - center) << 1) | (1 - right)
                target = (left << 2) | (center << 1) | right
                conjugated |= (1 - ((rule >> source) & 1)) << target
    return conjugated


def rule_orbit(rule: int) -> tuple[int, ...]:
    seen = {rule}
    frontier = [rule]
    while frontier:
        current = frontier.pop()
        for candidate in (reflect_rule(current), conjugate_rule(current)):
            if candidate not in seen:
                seen.add(candidate)
                frontier.append(candidate)
    return tuple(sorted(seen))


def ordered_rule_orbits() -> list[tuple[int, ...]]:
    unique = {rule_orbit(rule) for rule in range(256)}
    return sorted(
        unique,
        key=lambda orbit: hashlib.sha256(
            ("ECA6-PRBOG-v1|orbit|" + ",".join(str(value) for value in orbit)).encode("ascii")
        ).hexdigest(),
    )


def validate_frozen_split(spec: dict[str, Any]) -> dict[str, Any]:
    orbits = ordered_rule_orbits()
    rule_to_orbit = {rule: index for index, orbit in enumerate(orbits) for rule in orbit}
    expected_blocks = {
        "train": set(range(0, 60)),
        "validation": set(range(60, 74)),
        "test_primary": set(range(74, 88)),
        "test_structural_holdout": set(range(74, 88)),
    }
    fixtures = spec["fixtures"]
    block_checks: dict[str, bool] = {}
    unique_checks: dict[str, bool] = {}
    for split, expected in expected_blocks.items():
        rules = [rule for pair in fixtures[split] for rule in pair]
        block_checks[split] = all(rule_to_orbit[rule] in expected for rule in rules)
        unique_checks[split] = len(rules) == len(set(rules))
    train_orbits = {rule_to_orbit[rule] for pair in fixtures["train"] for rule in pair}
    held_orbits = {
        rule_to_orbit[rule]
        for split in ("validation", "test_primary", "test_structural_holdout")
        for pair in fixtures[split]
        for rule in pair
    }
    sentinel_rule = next(
        member
        for pair in fixtures["train"]
        for member in rule_orbit(pair[0])
        if member != pair[0]
    )
    injected_held_orbits = held_orbits | {rule_to_orbit[sentinel_rule]}
    injected_overlap = train_orbits & injected_held_orbits
    return {
        "orbit_count": len(orbits),
        "expected_88_orbits": len(orbits) == 88,
        "fixture_rules_in_frozen_orbit_blocks": block_checks,
        "fixture_rules_unique_within_each_split": unique_checks,
        "train_held_orbit_overlap_count": len(train_orbits & held_orbits),
        "no_train_held_orbit_overlap": not bool(train_orbits & held_orbits),
        "injected_symmetry_leakage_sentinel_rule": sentinel_rule,
        "injected_symmetry_leakage_overlap_count": len(injected_overlap),
        "injected_symmetry_leakage_sentinel_detected": bool(injected_overlap),
        "orbit_manifest_sha256": sha256_json([list(orbit) for orbit in orbits]),
    }


class SymmetricSuccessorLayer(MessagePassing):
    """Aggregate the two action successors as an unordered multiset."""

    def __init__(self, width: int) -> None:
        super().__init__(aggr="sum", flow="target_to_source")
        self.update_mlp = nn.Sequential(
            nn.Linear(2 * width, width),
            nn.SiLU(),
            nn.Linear(width, width),
        )
        self.norm = nn.LayerNorm(width)

    def forward(self, x: Tensor, edge_index: Tensor) -> Tensor:
        return self.propagate(edge_index=edge_index, x=x)

    def message(self, x_j: Tensor) -> Tensor:
        return x_j

    def update(self, aggregate: Tensor, x: Tensor) -> Tensor:
        return self.norm(x + self.update_mlp(torch.cat((x, aggregate), dim=-1)))


class BehavioralRelationProxy(nn.Module):
    """One shared refinement operator iterated exactly six times."""

    def __init__(self) -> None:
        super().__init__()
        self.input_projection = nn.Sequential(nn.Linear(1, HIDDEN_DIM), nn.SiLU())
        self.shared_refinement = SymmetricSuccessorLayer(HIDDEN_DIM)
        self.readout = nn.Sequential(
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.SiLU(),
            nn.Linear(HIDDEN_DIM, 1),
        )

    def forward(self, x: Tensor, edge_index: Tensor) -> Tensor:
        hidden = self.input_projection(x)
        for _ in range(MESSAGE_PASSING_STEPS):
            hidden = self.shared_refinement(hidden, edge_index)
        return self.readout(hidden).squeeze(-1)


def configure_determinism(seed: int) -> None:
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass


def balanced_fixture_loss(logits: Tensor, targets: Tensor) -> Tensor:
    positive = targets.to(dtype=torch.bool)
    negative = ~positive
    if not bool(positive.any().item()) or not bool(negative.any().item()):
        raise RuntimeError("fixture lacks a positive or negative relation class")
    pointwise = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    return 0.5 * pointwise[positive].mean() + 0.5 * pointwise[negative].mean()


def confusion(predicted: Tensor, target: Tensor) -> tuple[int, int, int, int]:
    predicted = predicted.to(dtype=torch.bool)
    target = target.to(dtype=torch.bool)
    tp = int((predicted & target).sum().item())
    fp = int((predicted & ~target).sum().item())
    tn = int((~predicted & ~target).sum().item())
    fn = int((~predicted & target).sum().item())
    return tp, fp, tn, fn


def mcc_from_counts(tp: int, fp: int, tn: int, fn: int) -> float:
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return 0.0 if denominator == 0.0 else (tp * tn - fp * fn) / denominator


def metrics_from_predictions(predicted: Tensor, target: Tensor) -> dict[str, Any]:
    tp, fp, tn, fn = confusion(predicted, target)
    positive_recall = tp / (tp + fn) if tp + fn else 0.0
    negative_recall = tn / (tn + fp) if tn + fp else 0.0
    false_positive_rate = fp / (fp + tn) if fp + tn else 0.0
    return {
        "count": tp + fp + tn + fn,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "accuracy": (tp + tn) / (tp + fp + tn + fn),
        "mcc": mcc_from_counts(tp, fp, tn, fn),
        "balanced_accuracy": 0.5 * (positive_recall + negative_recall),
        "positive_recall": positive_recall,
        "negative_recall": negative_recall,
        "false_positive_rate": false_positive_rate,
    }


def average_precision(scores: Tensor, target: Tensor) -> float:
    order = torch.argsort(scores, descending=True, stable=True)
    sorted_target = target[order].to(dtype=torch.float64)
    positives = int(sorted_target.sum().item())
    if positives == 0:
        return 0.0
    cumulative = torch.cumsum(sorted_target, dim=0)
    ranks = torch.arange(1, sorted_target.numel() + 1, dtype=torch.float64)
    return float(((cumulative / ranks) * sorted_target).sum().item() / positives)


def scored_metrics(scores: Tensor, target: Tensor, threshold: float) -> dict[str, Any]:
    result = metrics_from_predictions(scores >= threshold, target)
    ap = average_precision(scores, target)
    prevalence = float(target.to(dtype=torch.float64).mean().item())
    normalized_ap = (ap - prevalence) / (1.0 - prevalence) if prevalence < 1.0 else 0.0
    result.update(
        {
            "threshold": threshold,
            "average_precision": ap,
            "positive_prevalence": prevalence,
            "normalized_average_precision": normalized_ap,
        }
    )
    return result


def macro_metrics(
    score_sets: Sequence[Tensor], target_sets: Sequence[Tensor], threshold: float
) -> dict[str, Any]:
    per_fixture = [
        scored_metrics(scores, targets, threshold)
        for scores, targets in zip(score_sets, target_sets, strict=True)
    ]
    fields = (
        "accuracy",
        "mcc",
        "balanced_accuracy",
        "positive_recall",
        "negative_recall",
        "false_positive_rate",
        "average_precision",
        "normalized_average_precision",
    )
    return {
        f"macro_{field}": sum(float(item[field]) for item in per_fixture) / len(per_fixture)
        for field in fields
    } | {"per_fixture": per_fixture}


def select_macro_mcc_threshold(score_sets: Sequence[Tensor], target_sets: Sequence[Tensor]) -> dict[str, Any]:
    records: list[tuple[float, int, int]] = []
    counts: list[list[int]] = []
    for fixture_index, (scores, targets) in enumerate(zip(score_sets, target_sets, strict=True)):
        score_values = [float(value) for value in scores.tolist()]
        target_values = [int(value) for value in targets.tolist()]
        positives = sum(target_values)
        counts.append([0, 0, len(target_values) - positives, positives])
        records.extend(
            (score, target, fixture_index)
            for score, target in zip(score_values, target_values, strict=True)
        )
    records.sort(key=lambda item: item[0], reverse=True)

    def current_macro_mcc() -> float:
        return sum(mcc_from_counts(*fixture) for fixture in counts) / len(counts)

    best_threshold = math.nextafter(records[0][0], math.inf)
    best_mcc = current_macro_mcc()
    cursor = 0
    while cursor < len(records):
        threshold = records[cursor][0]
        stop = cursor
        while stop < len(records) and records[stop][0] == threshold:
            _, target, fixture_index = records[stop]
            if target:
                counts[fixture_index][0] += 1
                counts[fixture_index][3] -= 1
            else:
                counts[fixture_index][1] += 1
                counts[fixture_index][2] -= 1
            stop += 1
        candidate_mcc = current_macro_mcc()
        if candidate_mcc > best_mcc + 1e-15 or (
            abs(candidate_mcc - best_mcc) <= 1e-15 and threshold > best_threshold
        ):
            best_mcc = candidate_mcc
            best_threshold = threshold
        cursor = stop
    return {"threshold": best_threshold, "validation_macro_mcc": best_mcc}


def shuffled_targets(targets: Tensor, seed: int, fixture_index: int) -> Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed + 10_000 + fixture_index)
    return targets[torch.randperm(targets.numel(), generator=generator)]


def model_state_sha256(state_dict: dict[str, Tensor]) -> str:
    buffer = io.BytesIO()
    torch.save(state_dict, buffer)
    return sha256_bytes(buffer.getvalue())


def predict_model(model: BehavioralRelationProxy, graphs: Sequence[Data]) -> list[Tensor]:
    model.eval()
    with torch.no_grad():
        return [torch.sigmoid(model(graph.x, graph.edge_index)).detach().clone() for graph in graphs]


def train_one_seed(
    seed: int,
    train_graphs: Sequence[Data],
    validation_graphs: Sequence[Data],
    label_mode: str = "exact",
    optimizer_enabled: bool = True,
) -> tuple[dict[str, Tensor], dict[str, Any]]:
    configure_determinism(seed)
    model = BehavioralRelationProxy().to(dtype=torch.float64)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    best_state = copy.deepcopy(model.state_dict())
    best_epoch = 0
    best_selection = {"threshold": 0.5, "validation_macro_mcc": -1.0}
    patience_used = 0
    initial_loss: float | None = None
    final_training_loss: float | None = None
    epochs_completed = 0

    if optimizer_enabled:
        for epoch in range(1, MAX_EPOCHS + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            loss_sum = 0.0
            for fixture_index, graph in enumerate(train_graphs):
                targets = graph.y
                if label_mode == "shuffled":
                    targets = shuffled_targets(targets, seed, fixture_index)
                logits = model(graph.x, graph.edge_index)
                loss = balanced_fixture_loss(logits, targets)
                (loss / len(train_graphs)).backward()
                loss_sum += float(loss.item())
            optimizer.step()
            epochs_completed = epoch
            final_training_loss = loss_sum / len(train_graphs)
            if initial_loss is None:
                initial_loss = final_training_loss

            validation_scores = predict_model(model, validation_graphs)
            selection = select_macro_mcc_threshold(
                validation_scores, [graph.y for graph in validation_graphs]
            )
            if selection["validation_macro_mcc"] > best_selection["validation_macro_mcc"] + 1e-15:
                best_selection = selection
                best_state = copy.deepcopy(model.state_dict())
                best_epoch = epoch
                patience_used = 0
            else:
                patience_used += 1
            if patience_used >= PATIENCE:
                break
    else:
        validation_scores = predict_model(model, validation_graphs)
        best_selection = select_macro_mcc_threshold(
            validation_scores, [graph.y for graph in validation_graphs]
        )

    model.load_state_dict(best_state)
    return best_state, {
        "seed": seed,
        "label_mode": label_mode,
        "optimizer_enabled": optimizer_enabled,
        "epochs_completed": epochs_completed,
        "best_epoch": best_epoch,
        "patience": PATIENCE,
        "bounded_epoch_limit": MAX_EPOCHS,
        "initial_balanced_training_loss": initial_loss,
        "final_balanced_training_loss": final_training_loss,
        "best_validation_macro_mcc": best_selection["validation_macro_mcc"],
        "best_validation_threshold_for_early_stop_only": best_selection["threshold"],
        "checkpoint_sha256": model_state_sha256(best_state),
    }


def evaluate_checkpoints(
    checkpoints: Sequence[dict[str, Tensor]], graphs: Sequence[Data]
) -> tuple[list[list[Tensor]], list[Tensor]]:
    per_seed: list[list[Tensor]] = []
    for checkpoint in checkpoints:
        model = BehavioralRelationProxy().to(dtype=torch.float64)
        model.load_state_dict(checkpoint)
        per_seed.append(predict_model(model, graphs))
    ensemble = [
        torch.stack([seed_scores[index] for seed_scores in per_seed], dim=0).mean(dim=0)
        for index in range(len(graphs))
    ]
    return per_seed, ensemble


def fit_experiment(
    name: str,
    train_graphs: Sequence[Data],
    validation_graphs: Sequence[Data],
    seeds: Sequence[int],
    label_mode: str = "exact",
    optimizer_enabled: bool = True,
) -> dict[str, Any]:
    checkpoints: list[dict[str, Tensor]] = []
    training_receipts: list[dict[str, Any]] = []
    for seed in seeds:
        checkpoint, receipt = train_one_seed(
            seed,
            train_graphs,
            validation_graphs,
            label_mode=label_mode,
            optimizer_enabled=optimizer_enabled,
        )
        checkpoints.append(checkpoint)
        training_receipts.append(receipt)
    validation_per_seed, validation_ensemble = evaluate_checkpoints(checkpoints, validation_graphs)
    selection = select_macro_mcc_threshold(
        validation_ensemble, [graph.y for graph in validation_graphs]
    )
    return {
        "name": name,
        "checkpoints": checkpoints,
        "training_receipts": training_receipts,
        "validation_scores_per_seed": validation_per_seed,
        "validation_ensemble": validation_ensemble,
        "selected_threshold": selection["threshold"],
        "validation_macro_mcc": selection["validation_macro_mcc"],
    }


def evaluate_experiment(
    experiment: dict[str, Any], graphs: Sequence[Data], threshold: float | None = None
) -> dict[str, Any]:
    per_seed, ensemble = evaluate_checkpoints(experiment["checkpoints"], graphs)
    selected_threshold = experiment["selected_threshold"] if threshold is None else threshold
    target_sets = [graph.y for graph in graphs]
    per_seed_metrics = [
        macro_metrics(seed_scores, target_sets, selected_threshold) for seed_scores in per_seed
    ]
    return {
        "scores_per_seed": per_seed,
        "ensemble_scores": ensemble,
        "threshold": selected_threshold,
        "ensemble_metrics": macro_metrics(ensemble, target_sets, selected_threshold),
        "per_seed_metrics": per_seed_metrics,
    }


def hard_baseline_metrics(predictions: Sequence[Tensor], targets: Sequence[Tensor]) -> dict[str, Any]:
    per_fixture = [
        metrics_from_predictions(prediction, target)
        for prediction, target in zip(predictions, targets, strict=True)
    ]
    fields = ("accuracy", "mcc", "balanced_accuracy", "positive_recall", "negative_recall", "false_positive_rate")
    return {
        f"macro_{field}": sum(float(item[field]) for item in per_fixture) / len(per_fixture)
        for field in fields
    } | {"per_fixture": per_fixture}


def rotation_equivalence_targets() -> Tensor:
    return torch.tensor(
        [
            any(rotate_state(left, offset) == right for offset in range(RING_SIZE))
            for left in range(STATE_COUNT)
            for right in range(STATE_COUNT)
        ],
        dtype=torch.bool,
    )


def baseline_suite(
    train_partitions: Sequence[dict[str, Any]],
    validation_partitions: Sequence[dict[str, Any]],
    test_partitions: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    test_targets = [same_class_targets(item["stable_labels"]) for item in test_partitions]
    zeros = [torch.zeros(PAIR_COUNT, dtype=torch.bool) for _ in test_partitions]
    probe_only = same_class_targets(canonical_labels(tuple(probes(state) for state in range(STATE_COUNT))))
    depth_one = [same_class_targets(item["depth_labels"][1]) for item in test_partitions]
    depth_two = [same_class_targets(item["depth_labels"][min(2, len(item["depth_labels"]) - 1)]) for item in test_partitions]
    rotations = rotation_equivalence_targets()

    train_prevalence = torch.stack(
        [same_class_targets(item["stable_labels"]).to(dtype=torch.float64) for item in train_partitions], dim=0
    ).mean(dim=0)
    validation_scores = [train_prevalence for _ in validation_partitions]
    validation_targets = [same_class_targets(item["stable_labels"]) for item in validation_partitions]
    prevalence_selection = select_macro_mcc_threshold(validation_scores, validation_targets)
    prevalence_predictions = [
        train_prevalence >= prevalence_selection["threshold"] for _ in test_partitions
    ]
    return {
        "always_negative": hard_baseline_metrics(zeros, test_targets),
        "probe_only_depth_zero": hard_baseline_metrics([probe_only for _ in test_partitions], test_targets),
        "exact_depth_one": hard_baseline_metrics(depth_one, test_targets),
        "exact_depth_two": hard_baseline_metrics(depth_two, test_targets),
        "cyclic_rotation_equivalence": hard_baseline_metrics([rotations for _ in test_partitions], test_targets),
        "rule_blind_state_pair_prevalence": {
            "validation_selected_threshold": prevalence_selection,
            **hard_baseline_metrics(prevalence_predictions, test_targets),
            "score_sha256": sha256_json([float(value) for value in train_prevalence.tolist()]),
        },
        "exact_stable_refinement_oracle": hard_baseline_metrics(test_targets, test_targets),
        "rule_blind_predictions": {
            "always_negative": zeros,
            "probe_only_depth_zero": [probe_only for _ in test_partitions],
            "cyclic_rotation_equivalence": [rotations for _ in test_partitions],
            "rule_blind_state_pair_prevalence": prevalence_predictions,
        },
    }


def connected_components(relation: Tensor) -> list[int]:
    relation = relation.reshape(STATE_COUNT, STATE_COUNT)
    undirected = relation | relation.T
    labels = [-1] * STATE_COUNT
    component = 0
    for start in range(STATE_COUNT):
        if labels[start] >= 0:
            continue
        labels[start] = component
        frontier = [start]
        while frontier:
            current = frontier.pop()
            for neighbor in torch.nonzero(undirected[current], as_tuple=False).flatten().tolist():
                if labels[neighbor] < 0:
                    labels[neighbor] = component
                    frontier.append(neighbor)
        component += 1
    return labels


def adjusted_rand_index(predicted: Sequence[int], exact: Sequence[int]) -> float:
    contingency: dict[tuple[int, int], int] = {}
    predicted_counts: dict[int, int] = {}
    exact_counts: dict[int, int] = {}
    for left, right in zip(predicted, exact, strict=True):
        contingency[(left, right)] = contingency.get((left, right), 0) + 1
        predicted_counts[left] = predicted_counts.get(left, 0) + 1
        exact_counts[right] = exact_counts.get(right, 0) + 1
    choose2 = lambda value: value * (value - 1) / 2
    index = sum(choose2(value) for value in contingency.values())
    predicted_sum = sum(choose2(value) for value in predicted_counts.values())
    exact_sum = sum(choose2(value) for value in exact_counts.values())
    total = choose2(len(predicted))
    expected = predicted_sum * exact_sum / total if total else 0.0
    maximum = 0.5 * (predicted_sum + exact_sum)
    return 1.0 if maximum == expected else (index - expected) / (maximum - expected)


def normalized_variation_of_information(predicted: Sequence[int], exact: Sequence[int]) -> float:
    count = len(predicted)
    predicted_counts: dict[int, int] = {}
    exact_counts: dict[int, int] = {}
    joint: dict[tuple[int, int], int] = {}
    for left, right in zip(predicted, exact, strict=True):
        predicted_counts[left] = predicted_counts.get(left, 0) + 1
        exact_counts[right] = exact_counts.get(right, 0) + 1
        joint[(left, right)] = joint.get((left, right), 0) + 1
    entropy_predicted = -sum((value / count) * math.log(value / count) for value in predicted_counts.values())
    entropy_exact = -sum((value / count) * math.log(value / count) for value in exact_counts.values())
    mutual_information = 0.0
    for (left, right), value in joint.items():
        probability = value / count
        mutual_information += probability * math.log(
            probability / ((predicted_counts[left] / count) * (exact_counts[right] / count))
        )
    variation = entropy_predicted + entropy_exact - 2.0 * mutual_information
    return variation / math.log(count) if count > 1 else 0.0


def relation_and_partition_metrics(
    scores: Tensor, threshold: float, exact_labels: Sequence[int]
) -> dict[str, Any]:
    relation = (scores >= threshold).reshape(STATE_COUNT, STATE_COUNT)
    reflexivity_violations = int((~torch.diag(relation)).sum().item())
    symmetry_violations = int(torch.triu(relation ^ relation.T, diagonal=1).sum().item())
    transitivity_violations = 0
    for middle in range(STATE_COUNT):
        transitivity_violations += int(
            (relation[:, middle][:, None] & relation[middle, :][None, :] & ~relation).sum().item()
        )
    predicted_labels = connected_components(relation.reshape(-1))
    predicted_counts = [predicted_labels.count(label) for label in sorted(set(predicted_labels))]
    exact_counts = [list(exact_labels).count(label) for label in sorted(set(exact_labels))]
    return {
        "reflexivity_violations": reflexivity_violations,
        "symmetry_violations": symmetry_violations,
        "transitivity_violation_triples": transitivity_violations,
        "relation_laws_pass": reflexivity_violations == symmetry_violations == transitivity_violations == 0,
        "connected_component_count": len(predicted_counts),
        "adjusted_rand_index": adjusted_rand_index(predicted_labels, exact_labels),
        "normalized_variation_of_information": normalized_variation_of_information(predicted_labels, exact_labels),
        "largest_predicted_class": max(predicted_counts),
        "largest_exact_class": max(exact_counts),
        "largest_class_ratio": max(predicted_counts) / max(exact_counts),
        "predicted_component_labels": predicted_labels,
    }


def rule_sensitive_metrics(
    score_sets: Sequence[Tensor],
    target_sets: Sequence[Tensor],
    threshold: float,
    rule_blind_predictions: dict[str, Sequence[Tensor]],
) -> dict[str, Any]:
    stacked_targets = torch.stack([target.to(dtype=torch.bool) for target in target_sets], dim=0)
    sensitive = stacked_targets.any(dim=0) & ~stacked_targets.all(dim=0)
    scores = torch.cat([item[sensitive] for item in score_sets])
    targets = torch.cat([item[sensitive] for item in target_sets])
    model_metrics = scored_metrics(scores, targets, threshold)
    baseline_metrics: dict[str, Any] = {}
    for name, prediction_sets in rule_blind_predictions.items():
        predictions = torch.cat([item[sensitive] for item in prediction_sets])
        baseline_metrics[name] = metrics_from_predictions(predictions, targets)
    best_name = max(baseline_metrics, key=lambda name: baseline_metrics[name]["mcc"])
    return {
        "state_pair_count": int(sensitive.sum().item()),
        "observation_count": int(targets.numel()),
        "state_pair_mask_sha256": sha256_json([bool(value) for value in sensitive.tolist()]),
        "model": model_metrics,
        "rule_blind_baselines": baseline_metrics,
        "best_rule_blind_baseline": best_name,
        "mcc_advantage_over_best_rule_blind": model_metrics["mcc"] - baseline_metrics[best_name]["mcc"],
    }


def remap_scores_for_state_symmetries(scores: Tensor) -> dict[str, float]:
    state_swap = torch.tensor(
        [pair_index(right, left) for left in range(STATE_COUNT) for right in range(STATE_COUNT)], dtype=torch.long
    )
    swap_difference = float((scores - scores[state_swap]).abs().max().item())
    rotation_difference = 0.0
    for offset in range(RING_SIZE):
        rotation_map = torch.tensor(
            [
                pair_index(rotate_state(left, offset), rotate_state(right, offset))
                for left in range(STATE_COUNT)
                for right in range(STATE_COUNT)
            ],
            dtype=torch.long,
        )
        rotation_difference = max(rotation_difference, float((scores - scores[rotation_map]).abs().max().item()))
    return {
        "state_swap_max_abs": swap_difference,
        "cyclic_rotation_max_abs": rotation_difference,
    }


def serialize_raw_evaluation(
    rule_pairs: Sequence[Sequence[int]],
    graphs: Sequence[Data],
    evaluation: dict[str, Any],
    partitions: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw = []
    for index, pair in enumerate(rule_pairs):
        raw.append(
            {
                "rules": list(pair),
                "target_same_object": [bool(value) for value in graphs[index].y.tolist()],
                "scores_per_seed": [
                    [float(value) for value in seed_scores[index].tolist()]
                    for seed_scores in evaluation["scores_per_seed"]
                ],
                "ensemble_scores": [float(value) for value in evaluation["ensemble_scores"][index].tolist()],
                "predicted_same_object": [
                    bool(value)
                    for value in (evaluation["ensemble_scores"][index] >= evaluation["threshold"]).tolist()
                ],
                "ensemble_metrics": evaluation["ensemble_metrics"]["per_fixture"][index],
                "per_seed_metrics": [
                    seed_metrics["per_fixture"][index]
                    for seed_metrics in evaluation["per_seed_metrics"]
                ],
                "partition_sha256": partitions[index]["partition_sha256"],
            }
        )
    return raw


def serialize_control_scores(
    rule_pairs: Sequence[Sequence[int]], score_sets: Sequence[Tensor], threshold: float
) -> list[dict[str, Any]]:
    return [
        {
            "rules": list(pair),
            "ensemble_scores": [float(value) for value in scores.tolist()],
            "predicted_same_object": [bool(value) for value in (scores >= threshold).tolist()],
        }
        for pair, scores in zip(rule_pairs, score_sets, strict=True)
    ]


def main() -> None:
    spec = load_json(SPEC_PATH)
    prereg = load_json(PREREG_PATH)
    object_card = load_json(OBJECT_CARD_PATH)
    spec_hash = sha256_bytes(SPEC_PATH.read_bytes())
    object_card_hash = sha256_bytes(OBJECT_CARD_PATH.read_bytes())
    preregistration_bound = all(
        (
            prereg.get("status") == "frozen_before_builder_source",
            prereg.get("builder_sources_present_when_frozen") is False,
            prereg.get("spec_sha256") == spec_hash,
            prereg.get("object_card_sha256") == object_card_hash,
            spec.get("sim_id") == SIM_ID,
            spec.get("classification") == CLASSIFICATION,
            spec.get("promotion_allowed") is False,
            spec.get("formal_admission_allowed") is False,
        )
    )
    split_receipt = validate_frozen_split(spec)
    if not preregistration_bound:
        raise RuntimeError("frozen preregistration binding failed")
    if not (
        split_receipt["expected_88_orbits"]
        and split_receipt["no_train_held_orbit_overlap"]
        and split_receipt["injected_symmetry_leakage_sentinel_detected"]
        and all(split_receipt["fixture_rules_in_frozen_orbit_blocks"].values())
        and all(split_receipt["fixture_rules_unique_within_each_split"].values())
    ):
        raise RuntimeError("frozen rule-family split or leakage sentinel failed")

    fixtures = spec["fixtures"]
    train_partitions = [exact_partition(*pair) for pair in fixtures["train"]]
    validation_partitions = [exact_partition(*pair) for pair in fixtures["validation"]]
    train_graphs = [graph_for_partition(item) for item in train_partitions]
    validation_graphs = [graph_for_partition(item) for item in validation_partitions]

    positive = fit_experiment("positive", train_graphs, validation_graphs, SEEDS)
    selected_threshold = positive["selected_threshold"]

    # Test labels are first materialized only after architecture, checkpoints,
    # stopping epochs, and the single validation threshold are frozen.
    test_pairs = fixtures["test_primary"]
    structural_pairs = fixtures["test_structural_holdout"]
    test_partitions = [exact_partition(*pair) for pair in test_pairs]
    structural_partitions = [exact_partition(*pair) for pair in structural_pairs]
    expected_structural_hashes = set(
        spec["behavioral_partition_hash"]["structural_holdout_hashes_excluded_from_train_and_validation"]
    )
    observed_structural_hashes = {item["partition_sha256"] for item in structural_partitions}
    train_validation_hashes = {
        item["partition_sha256"] for item in train_partitions + validation_partitions
    }
    structural_hash_binding = {
        "expected_hashes": sorted(expected_structural_hashes),
        "observed_hashes": sorted(observed_structural_hashes),
        "expected_hashes_match": observed_structural_hashes == expected_structural_hashes,
        "excluded_from_train_and_validation": not bool(
            expected_structural_hashes & train_validation_hashes
        ),
    }
    test_graphs = [graph_for_partition(item) for item in test_partitions]
    structural_graphs = [graph_for_partition(item) for item in structural_partitions]
    positive_test = evaluate_experiment(positive, test_graphs, selected_threshold)
    positive_structural = evaluate_experiment(positive, structural_graphs, selected_threshold)

    baselines = baseline_suite(train_partitions, validation_partitions, test_partitions)
    rule_sensitive = rule_sensitive_metrics(
        positive_test["ensemble_scores"],
        [graph.y for graph in test_graphs],
        selected_threshold,
        baselines.pop("rule_blind_predictions"),
    )
    partition_metrics = [
        relation_and_partition_metrics(scores, selected_threshold, partition["stable_labels"])
        for scores, partition in zip(positive_test["ensemble_scores"], test_partitions, strict=True)
    ]

    erased_train = [graph_for_partition(item, edge_mode="erased") for item in train_partitions]
    erased_validation = [graph_for_partition(item, edge_mode="erased") for item in validation_partitions]
    erased_test = [graph_for_partition(item, edge_mode="erased") for item in test_partitions]
    edge_erased = fit_experiment("retrained_edge_erasure", erased_train, erased_validation, CONTROL_SEEDS)
    edge_erased_test = evaluate_experiment(edge_erased, erased_test)

    shuffled = fit_experiment(
        "shuffled_training_labels", train_graphs, validation_graphs, CONTROL_SEEDS, label_mode="shuffled"
    )
    shuffled_test = evaluate_experiment(shuffled, test_graphs)
    optimizer_erased = fit_experiment(
        "optimizer_erased", train_graphs, validation_graphs, CONTROL_SEEDS, optimizer_enabled=False
    )
    optimizer_erased_test = evaluate_experiment(optimizer_erased, test_graphs)

    intact_checkpoints = positive["checkpoints"]
    _, same_weight_erased_scores = evaluate_checkpoints(intact_checkpoints, erased_test)
    probe_erased_test = [graph_for_partition(item, erase_probe=True) for item in test_partitions]
    _, same_weight_probe_erased_scores = evaluate_checkpoints(intact_checkpoints, probe_erased_test)
    self_transition_test = [graph_for_partition(item, edge_mode="self") for item in test_partitions]
    _, zero_transition_scores = evaluate_checkpoints(intact_checkpoints, self_transition_test)
    permuted_graphs = [
        graph_for_partition(test_partitions[(index + 1) % len(test_partitions)])
        for index in range(len(test_partitions))
    ]
    _, permuted_rule_scores = evaluate_checkpoints(intact_checkpoints, permuted_graphs)

    swapped_action_graphs = []
    for partition in test_partitions:
        swapped = dict(partition)
        swapped["transition_a"], swapped["transition_b"] = partition["transition_b"], partition["transition_a"]
        swapped_action_graphs.append(graph_for_partition(swapped))
    _, swapped_action_scores = evaluate_checkpoints(intact_checkpoints, swapped_action_graphs)
    action_swap_max_abs = max(
        float((left - right).abs().max().item())
        for left, right in zip(positive_test["ensemble_scores"], swapped_action_scores, strict=True)
    )
    symmetry_receipts = [remap_scores_for_state_symmetries(scores) for scores in positive_test["ensemble_scores"]]

    test_targets = [graph.y for graph in test_graphs]
    same_weight_erased_metrics = macro_metrics(same_weight_erased_scores, test_targets, selected_threshold)
    probe_erased_metrics = macro_metrics(same_weight_probe_erased_scores, test_targets, selected_threshold)
    zero_transition_metrics = macro_metrics(zero_transition_scores, test_targets, selected_threshold)
    permuted_rule_metrics = macro_metrics(permuted_rule_scores, test_targets, selected_threshold)

    mutated_rule = test_pairs[0][0] ^ 1
    mutated_partition = exact_partition(mutated_rule, test_pairs[0][1])
    original_hash = test_partitions[0]["partition_sha256"]
    mutation_hash = mutated_partition["partition_sha256"]
    one_bit_mutation = {
        "original_rules": list(test_pairs[0]),
        "mutated_rules": [mutated_rule, test_pairs[0][1]],
        "flipped_truth_table_output_bit": 0,
        "original_partition_sha256": original_hash,
        "mutated_partition_sha256": mutation_hash,
        "label_hash_changed": original_hash != mutation_hash,
        "behaviorally_silent": original_hash == mutation_hash,
    }

    primary_metrics = positive_test["ensemble_metrics"]
    seed_mccs = [item["macro_mcc"] for item in positive_test["per_seed_metrics"]]
    partition_macro_ari = sum(item["adjusted_rand_index"] for item in partition_metrics) / len(partition_metrics)
    partition_macro_nvi = sum(item["normalized_variation_of_information"] for item in partition_metrics) / len(partition_metrics)
    gates = {
        "test_primary_macro_mcc_at_least_0_55": primary_metrics["macro_mcc"] >= 0.55,
        "test_primary_macro_balanced_accuracy_at_least_0_78": primary_metrics["macro_balanced_accuracy"] >= 0.78,
        "test_primary_macro_positive_recall_at_least_0_65": primary_metrics["macro_positive_recall"] >= 0.65,
        "test_primary_macro_false_positive_rate_at_most_0_04": primary_metrics["macro_false_positive_rate"] <= 0.04,
        "rule_sensitive_mcc_at_least_0_50": rule_sensitive["model"]["mcc"] >= 0.50,
        "rule_sensitive_advantage_at_least_0_15": rule_sensitive["mcc_advantage_over_best_rule_blind"] >= 0.15,
        "every_seed_macro_mcc_at_least_0_35": min(seed_mccs) >= 0.35,
        "predicted_partition_macro_ari_at_least_0_75": partition_macro_ari >= 0.75,
        "predicted_partition_macro_nvi_at_most_0_20": partition_macro_nvi <= 0.20,
        "zero_relation_law_violations": all(item["relation_laws_pass"] for item in partition_metrics),
        "state_swap_invariance": max(item["state_swap_max_abs"] for item in symmetry_receipts) <= 1e-10,
        "action_swap_invariance": action_swap_max_abs <= 1e-10,
        "cyclic_rotation_invariance": max(item["cyclic_rotation_max_abs"] for item in symmetry_receipts) <= 1e-8,
        "zero_transition_information_mcc_drop_at_least_0_15": primary_metrics["macro_mcc"] - zero_transition_metrics["macro_mcc"] >= 0.15,
        "retrained_ring_edge_erasure_mcc_drop_at_least_0_10": primary_metrics["macro_mcc"] - edge_erased_test["ensemble_metrics"]["macro_mcc"] >= 0.10,
        "shuffled_training_label_test_mcc_at_most_0_05": shuffled_test["ensemble_metrics"]["macro_mcc"] <= 0.05,
        "structural_holdout_report_present": len(structural_pairs) == 2,
        "one_bit_transition_mutation_classified": one_bit_mutation["label_hash_changed"] or one_bit_mutation["behaviorally_silent"],
        "structural_holdout_hashes_bound": structural_hash_binding["expected_hashes_match"],
        "structural_holdout_hashes_excluded_from_train_validation": structural_hash_binding["excluded_from_train_and_validation"],
    }

    source_hash = sha256_bytes(SOURCE_PATH.read_bytes())
    result = {
        "schema": "codex_ratchet.pytorch_heldout_rule_proxy_result.v1",
        "schema_version": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_status": "diagnostic_only",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "all_pass": all(gates.values()),
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_hash,
        "result_path": str(RESULT_PATH),
        "spec_path": str(SPEC_PATH),
        "spec_sha256": spec_hash,
        "preregistration_receipt_sha256": sha256_bytes(PREREG_PATH.read_bytes()),
        "object_card_sha256": object_card_hash,
        "preregistration_bound_at_runtime": preregistration_bound,
        "reads_peer_result": False,
        "peer_result_paths_read": [],
        "numpy_used_on_claim_path": False,
        "engine_contract": {
            "mode": "all_three_full_sims",
            "role": "learned pair-graph refinement proxy on held-out action families",
            "semantic_authority": False,
            "exact_labels_computed_independently_from_frozen_spec": True,
        },
        "model_contract": {
            "node_count_per_fixture": PAIR_COUNT,
            "ordered_state_pairs": True,
            "directed_successor_edges_per_node": 2,
            "node_input": "probe-equality bit only",
            "rule_information_path": "successor graph topology only",
            "message_passing_steps": MESSAGE_PASSING_STEPS,
            "shared_refinement_parameters_across_steps": True,
            "symmetric_action_aggregation": "sum",
            "hidden_dim": HIDDEN_DIM,
            "forbidden_inputs_absent": [
                "class ID",
                "history fingerprint",
                "rule number embedding",
                "split ID",
                "Julia result",
                "JAX result",
            ],
        },
        "split_validation": split_receipt,
        "training": {
            "device": "cpu",
            "dtype": "torch.float64",
            "deterministic_algorithms": True,
            "seeds": list(SEEDS),
            "maximum_epochs": MAX_EPOCHS,
            "early_stopping_metric": "validation fixture-macro MCC",
            "early_stopping_patience": PATIENCE,
            "single_validation_selected_threshold": selected_threshold,
            "threshold_tie_break": "larger threshold",
            "optimizer": "torch.optim.Adam",
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "loss": "fixture-balanced torch.nn.functional.binary_cross_entropy_with_logits",
            "positive_training_receipts": positive["training_receipts"],
        },
        "exact_fixture_receipts": {
            "train": [
                {key: item[key] for key in ("rules", "stabilization_depth", "class_count", "partition_sha256")}
                for item in train_partitions
            ],
            "validation": [
                {key: item[key] for key in ("rules", "stabilization_depth", "class_count", "partition_sha256")}
                for item in validation_partitions
            ],
            "test_primary": [
                {key: item[key] for key in ("rules", "stabilization_depth", "class_count", "partition_sha256")}
                for item in test_partitions
            ],
            "test_structural_holdout": [
                {key: item[key] for key in ("rules", "stabilization_depth", "class_count", "partition_sha256")}
                for item in structural_partitions
            ],
        },
        "validation_selection": {
            "threshold": selected_threshold,
            "ensemble_macro_mcc": positive["validation_macro_mcc"],
            "raw_scores_sha256": sha256_json(
                [[float(value) for value in scores.tolist()] for scores in positive["validation_ensemble"]]
            ),
        },
        "test_primary": {
            "ensemble_metrics": primary_metrics,
            "per_seed_metrics": positive_test["per_seed_metrics"],
            "rule_sensitive": rule_sensitive,
            "partition_metrics": partition_metrics,
            "partition_macro_ari": partition_macro_ari,
            "partition_macro_normalized_vi": partition_macro_nvi,
            "raw_predictions": serialize_raw_evaluation(test_pairs, test_graphs, positive_test, test_partitions),
        },
        "test_structural_holdout": {
            "required_for_stronger_label": True,
            "frozen_hash_binding": structural_hash_binding,
            "ensemble_metrics": positive_structural["ensemble_metrics"],
            "per_seed_metrics": positive_structural["per_seed_metrics"],
            "raw_predictions": serialize_raw_evaluation(
                structural_pairs, structural_graphs, positive_structural, structural_partitions
            ),
        },
        "baselines": baselines,
        "controls": {
            "same_weight_edge_erasure": {
                "test_metrics": same_weight_erased_metrics,
                "raw_scores": serialize_control_scores(test_pairs, same_weight_erased_scores, selected_threshold),
            },
            "retrained_edge_erasure": {
                "training_receipts": edge_erased["training_receipts"],
                "test_metrics": edge_erased_test["ensemble_metrics"],
                "raw_scores": serialize_control_scores(
                    test_pairs, edge_erased_test["ensemble_scores"], edge_erased_test["threshold"]
                ),
            },
            "same_weight_probe_erasure": {
                "test_metrics": probe_erased_metrics,
                "raw_scores": serialize_control_scores(
                    test_pairs, same_weight_probe_erased_scores, selected_threshold
                ),
            },
            "same_weight_zero_transition_information": {
                "test_metrics": zero_transition_metrics,
                "raw_scores": serialize_control_scores(
                    test_pairs, zero_transition_scores, selected_threshold
                ),
            },
            "same_weight_rule_identity_permutation": {
                "test_metrics": permuted_rule_metrics,
                "raw_scores": serialize_control_scores(
                    test_pairs, permuted_rule_scores, selected_threshold
                ),
            },
            "shuffled_training_labels": {
                "training_receipts": shuffled["training_receipts"],
                "test_metrics": shuffled_test["ensemble_metrics"],
                "raw_scores": serialize_control_scores(
                    test_pairs, shuffled_test["ensemble_scores"], shuffled_test["threshold"]
                ),
            },
            "optimizer_erasure": {
                "training_receipts": optimizer_erased["training_receipts"],
                "test_metrics": optimizer_erased_test["ensemble_metrics"],
                "raw_scores": serialize_control_scores(
                    test_pairs, optimizer_erased_test["ensemble_scores"], optimizer_erased_test["threshold"]
                ),
            },
            "state_and_rotation_invariance": symmetry_receipts,
            "action_swap_max_abs": action_swap_max_abs,
            "one_bit_transition_mutation": one_bit_mutation,
            "claim_bearing_score_hashes": {
                "same_weight_edge_erasure": sha256_json(
                    [[float(value) for value in scores.tolist()] for scores in same_weight_erased_scores]
                ),
                "retrained_edge_erasure": sha256_json(
                    [[float(value) for value in scores.tolist()] for scores in edge_erased_test["ensemble_scores"]]
                ),
                "probe_erasure": sha256_json(
                    [[float(value) for value in scores.tolist()] for scores in same_weight_probe_erased_scores]
                ),
                "zero_transition": sha256_json(
                    [[float(value) for value in scores.tolist()] for scores in zero_transition_scores]
                ),
                "rule_permutation": sha256_json(
                    [[float(value) for value in scores.tolist()] for scores in permuted_rule_scores]
                ),
                "shuffled_labels": sha256_json(
                    [[float(value) for value in scores.tolist()] for scores in shuffled_test["ensemble_scores"]]
                ),
                "optimizer_erasure": sha256_json(
                    [[float(value) for value in scores.tolist()] for scores in optimizer_erased_test["ensemble_scores"]]
                ),
            },
        },
        "gates": gates,
        "packages_used": ["torch", "torch_geometric"],
        "actual_tools_used": ["torch", "torch_geometric"],
        "aligned_packages_load_bearing": ["torch", "torch_geometric"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.nn.MessagePassing.propagate",
                "input_object": "4096 ordered state-pair nodes and two rule-dependent successor edges per node",
                "output_object": "six-step shared behavioral-refinement embeddings and node logits",
                "positive_case": "held-out rule-family pair graphs",
                "negative/erased_control": "same-weight edge erasure plus matched retraining without edges",
                "boundary_case": "duplicate successors remain a two-element action multiset",
                "demotion_condition": "edge erasure macro-MCC drop below 0.10",
                "gates": ["all_pass", "retrained_ring_edge_erasure_mcc_drop_at_least_0_10"],
            },
            {
                "tool": "torch",
                "qualified_api/function": "torch.nn.functional.binary_cross_entropy_with_logits",
                "input_object": "per-fixture logits and exact same-object labels",
                "output_object": "equal-fixture, equal-positive-negative training loss",
                "positive_case": "intact frozen labels",
                "negative/erased_control": "within-fixture shuffled training labels",
                "boundary_case": "every fixture must contain both relation classes",
                "demotion_condition": "shuffled-label test MCC exceeds 0.05",
                "gates": ["all_pass", "shuffled_training_label_test_mcc_at_most_0_05"],
            },
            {
                "tool": "torch",
                "qualified_api/function": "torch.Tensor.backward",
                "input_object": "fixture-balanced BCE divided by training fixture count",
                "output_object": "accumulated gradients over every training rule fixture",
                "positive_case": "all frozen training fixtures contribute once per epoch",
                "negative/erased_control": "optimizer-erased models receive no backward pass",
                "boundary_case": "early stopping never reads test labels",
                "demotion_condition": "reported learning effect is no better than optimizer erasure",
                "gates": ["primary learning metrics", "optimizer erasure control"],
            },
            {
                "tool": "torch",
                "qualified_api/function": "torch.optim.Adam.step",
                "input_object": "accumulated balanced-loss gradients",
                "output_object": "validation-selected learned checkpoints",
                "positive_case": "three preregistered seeded optimizations",
                "negative/erased_control": "same initialized architecture with zero optimizer steps",
                "boundary_case": "maximum 300 epochs and patience 30",
                "demotion_condition": "optimizer-erased control matches the learned proxy",
                "gates": ["primary learning metrics", "optimizer erasure control"],
            },
        ],
        "claim_ceiling": {
            "allowed_if_green": spec["allowed_claim_label_if_all_learning_gates_pass"],
            "current_label": spec["allowed_claim_label_if_all_learning_gates_pass"] if all(gates.values()) else "HELD_OUT_RULE_PROXY_GATES_RED",
            "semantic_authority": False,
            "blocked_consumers": spec["blocked_consumers"],
            "T9_runtime_nonredundancy_earned": False,
        },
        "object_card_statement_sha256": object_card["primary_object_card"]["object_statement_sha256"],
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "engine": "pytorch", "out": str(RESULT_PATH)}))


if __name__ == "__main__":
    main()
