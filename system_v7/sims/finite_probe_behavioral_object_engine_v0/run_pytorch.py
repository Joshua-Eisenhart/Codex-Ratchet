#!/usr/bin/env python3
"""PyG learned-perception lane for the finite six-site ring fixture.

This file deliberately derives rotation-orbit targets from the 64 binary states.
It does not read Julia/JAX results and does not arbitrate exact object or basin
claims. Its only gate is learned reidentification of held-out cyclic views.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Any, Iterable

import torch
import torch.nn.functional as F
from torch import Tensor, nn
from torch.func import functional_call, jacrev
from torch_geometric.data import Batch, Data
from torch_geometric.nn import MessagePassing, global_add_pool


SIM_ID = "finite_probe_behavioral_object_engine_v0"
CLASSIFICATION = "scratch_diagnostic"
HERE = Path(__file__).resolve().parent
SOURCE_PATH = Path(__file__).resolve()
SPEC_PATH = HERE / "spec.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
RESULT_PATH = HERE / "results" / f"{SIM_ID}_pytorch_results.json"

RING_SIZE = 6
STATE_COUNT = 1 << RING_SIZE
MODEL_SEED = 730_241
SHUFFLE_SEED = 730_242
EPOCHS = 1_200
LEARNING_RATE = 3.0e-3
WEIGHT_DECAY = 1.0e-4
HIDDEN_DIM = 48
MESSAGE_PASSING_STEPS = RING_SIZE

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "deterministic differentiable classifier training, logits, losses, margins, and optimization",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "stateless model evaluation and held-out margin sensitivity audit",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing directed-ring MessagePassing, graph batching, and graph pooling",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "supportive",
    "torch_geometric": "load_bearing",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def state_bits(state: int) -> tuple[int, ...]:
    """Decode integer state with bit i at directed-ring site i."""
    return tuple((state >> site) & 1 for site in range(RING_SIZE))


def bits_state(bits: Iterable[int]) -> int:
    value = 0
    for site, bit in enumerate(bits):
        value |= int(bit) << site
    return value


def rotate_bits(bits: tuple[int, ...], offset: int) -> tuple[int, ...]:
    """Relabel site i as the old site i-offset, preserving ring orientation."""
    return tuple(bits[(site - offset) % RING_SIZE] for site in range(RING_SIZE))


def rotation_orbit(state: int) -> tuple[int, ...]:
    bits = state_bits(state)
    return tuple(sorted({bits_state(rotate_bits(bits, k)) for k in range(RING_SIZE)}))


def derive_rotation_targets() -> tuple[dict[int, int], list[int], dict[int, list[int]]]:
    """Construct target classes from cyclic action only, without fixture results."""
    representatives = sorted({min(rotation_orbit(state)) for state in range(STATE_COUNT)})
    representative_to_class = {representative: index for index, representative in enumerate(representatives)}
    targets: dict[int, int] = {}
    members: dict[int, list[int]] = {index: [] for index in range(len(representatives))}
    for state in range(STATE_COUNT):
        class_id = representative_to_class[min(rotation_orbit(state))]
        targets[state] = class_id
        members[class_id].append(state)
    return targets, representatives, members


def directed_ring_edges(erased: bool) -> Tensor:
    if erased:
        return torch.empty((2, 0), dtype=torch.long)
    sources = torch.arange(RING_SIZE, dtype=torch.long)
    targets = torch.remainder(sources + 1, RING_SIZE)
    return torch.stack((sources, targets), dim=0)


def graph_for_state(state: int, target: int, erased_edges: bool) -> Data:
    bits = torch.tensor(state_bits(state), dtype=torch.long)
    x = F.one_hot(bits, num_classes=2).to(dtype=torch.float64)
    return Data(
        x=x,
        edge_index=directed_ring_edges(erased_edges),
        y=torch.tensor([target], dtype=torch.long),
        state_id=torch.tensor([state], dtype=torch.long),
    )


class DirectedRingLayer(MessagePassing):
    """Learn an ordered local word from each node and its clockwise predecessor."""

    def __init__(self, width: int) -> None:
        super().__init__(aggr="sum", flow="source_to_target")
        self.update_mlp = nn.Sequential(
            nn.Linear(2 * width, width),
            nn.SiLU(),
            nn.Linear(width, width),
        )
        self.residual_norm = nn.LayerNorm(width)

    def forward(self, x: Tensor, edge_index: Tensor) -> Tensor:
        return self.propagate(edge_index=edge_index, x=x)

    def message(self, x_j: Tensor) -> Tensor:
        return x_j

    def update(self, aggregate: Tensor, x: Tensor) -> Tensor:
        update = self.update_mlp(torch.cat((x, aggregate), dim=-1))
        return self.residual_norm(x + update)


class RingObjectClassifier(nn.Module):
    def __init__(self, class_count: int) -> None:
        super().__init__()
        self.input_projection = nn.Sequential(nn.Linear(2, HIDDEN_DIM), nn.SiLU())
        self.layers = nn.ModuleList(
            DirectedRingLayer(HIDDEN_DIM) for _ in range(MESSAGE_PASSING_STEPS)
        )
        pooled_width = HIDDEN_DIM * (MESSAGE_PASSING_STEPS + 1)
        self.readout = nn.Sequential(
            nn.Linear(pooled_width, 2 * HIDDEN_DIM),
            nn.SiLU(),
            nn.Linear(2 * HIDDEN_DIM, class_count),
        )

    def forward(self, x: Tensor, edge_index: Tensor, batch: Tensor) -> Tensor:
        hidden = self.input_projection(x)
        pooled = [global_add_pool(hidden, batch)]
        for layer in self.layers:
            hidden = layer(hidden, edge_index)
            pooled.append(global_add_pool(hidden, batch))
        return self.readout(torch.cat(pooled, dim=-1))


def configure_determinism(seed: int) -> None:
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        # A reused interpreter may have already fixed this process-wide setting.
        pass


def model_state_sha256(model: nn.Module) -> str:
    buffer = io.BytesIO()
    torch.save(model.state_dict(), buffer)
    return sha256_bytes(buffer.getvalue())


def stateless_logits(model: nn.Module, batch: Batch) -> Tensor:
    params = dict(model.named_parameters())
    buffers = dict(model.named_buffers())
    return functional_call(
        model,
        (params, buffers),
        (batch.x, batch.edge_index, batch.batch),
    )


def margin_metrics(logits: Tensor, true_targets: Tensor) -> dict[str, Any]:
    true_logits = logits.gather(1, true_targets[:, None]).squeeze(1)
    mask = F.one_hot(true_targets, num_classes=logits.shape[1]).to(dtype=torch.bool)
    strongest_other = logits.masked_fill(mask, -torch.inf).max(dim=1).values
    margins = true_logits - strongest_other
    predictions = logits.argmax(dim=1)
    return {
        "accuracy": float((predictions == true_targets).to(torch.float64).mean().item()),
        "correct": int((predictions == true_targets).sum().item()),
        "count": int(true_targets.numel()),
        "margin_min": float(margins.min().item()),
        "margin_mean": float(margins.mean().item()),
        "margin_median": float(margins.median().item()),
        "margin_max": float(margins.max().item()),
        "positive_margin_fraction": float((margins > 0).to(torch.float64).mean().item()),
        "prediction_sha256": sha256_json(predictions.tolist()),
        "margin_sha256": sha256_json([float(value) for value in margins.tolist()]),
    }


def train_experiment(
    name: str,
    train_states: list[int],
    test_states: list[int],
    true_targets: dict[int, int],
    training_targets: dict[int, int],
    class_count: int,
    erased_edges: bool,
) -> tuple[RingObjectClassifier, dict[str, Any], Batch]:
    configure_determinism(MODEL_SEED)
    model = RingObjectClassifier(class_count).to(dtype=torch.float64)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )
    train_batch = Batch.from_data_list(
        [graph_for_state(state, training_targets[state], erased_edges) for state in train_states]
    )
    test_batch = Batch.from_data_list(
        [graph_for_state(state, true_targets[state], erased_edges) for state in test_states]
    )

    initial_loss: float | None = None
    model.train()
    for epoch in range(EPOCHS):
        optimizer.zero_grad(set_to_none=True)
        logits = model(train_batch.x, train_batch.edge_index, train_batch.batch)
        loss = F.cross_entropy(logits, train_batch.y)
        if epoch == 0:
            initial_loss = float(loss.item())
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        train_logits = stateless_logits(model, train_batch)
        held_logits = stateless_logits(model, test_batch)
        train_against_training = margin_metrics(train_logits, train_batch.y)
        held_against_true = margin_metrics(held_logits, test_batch.y)

    record = {
        "name": name,
        "seed": MODEL_SEED,
        "epochs_completed": EPOCHS,
        "bounded_epoch_limit": EPOCHS,
        "initial_loss": initial_loss,
        "final_loss": float(F.cross_entropy(train_logits, train_batch.y).item()),
        "erased_ring_edges": erased_edges,
        "directed_edge_count_per_graph": int(directed_ring_edges(erased_edges).shape[1]),
        "training_against_assigned_targets": train_against_training,
        "held_out_against_true_targets": held_against_true,
        "model_state_sha256": model_state_sha256(model),
    }
    return model, record, test_batch


def make_deranged_targets(targets: dict[int, int], class_count: int) -> tuple[dict[int, int], list[int]]:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(SHUFFLE_SEED)
    permutation = torch.randperm(class_count, generator=generator)
    for shift in range(class_count):
        candidate = torch.roll(permutation, shifts=shift)
        if bool(torch.all(candidate != torch.arange(class_count))):
            permutation = candidate
            break
    else:
        raise RuntimeError("failed to construct fixed-seed deranged target control")
    mapped = {state: int(permutation[class_id].item()) for state, class_id in targets.items()}
    return mapped, [int(value) for value in permutation.tolist()]


def torch_func_sensitivity_receipt(
    model: RingObjectClassifier, test_batch: Batch, sample_graph: int = 0
) -> dict[str, Any]:
    """Audit whether a held prediction locally depends on node features."""
    start = sample_graph * RING_SIZE
    stop = start + RING_SIZE
    x = test_batch.x[start:stop].detach().clone()
    edge_index = directed_ring_edges(erased=False)
    batch = torch.zeros(RING_SIZE, dtype=torch.long)
    true_target = int(test_batch.y[sample_graph].item())
    params = dict(model.named_parameters())
    buffers = dict(model.named_buffers())

    def selected_margin(node_features: Tensor) -> Tensor:
        logits = functional_call(model, (params, buffers), (node_features, edge_index, batch))[0]
        mask = torch.arange(logits.numel()) != true_target
        return logits[true_target] - logits[mask].max()

    jacobian = jacrev(selected_margin)(x)
    return {
        "qualified_api": "torch.func.jacrev(torch.func.functional_call)",
        "input_object": "held-out six-node directed-ring node features",
        "output_object": "Jacobian of true-class logit margin with respect to node features",
        "sample_state": int(test_batch.state_id[sample_graph].item()),
        "true_target": true_target,
        "jacobian_shape": list(jacobian.shape),
        "jacobian_l2_norm": float(torch.linalg.vector_norm(jacobian).item()),
        "finite": bool(torch.isfinite(jacobian).all().item()),
        "nonzero": bool(torch.linalg.vector_norm(jacobian).item() > 0.0),
        "role": "supportive learned-dependence audit; not an exact-object gate",
    }


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    spec_sha256 = sha256_bytes(SPEC_PATH.read_bytes())
    preregistration_bound = (
        prereg.get("registered_before_builder_source") is True
        and prereg.get("spec_sha256") == spec_sha256
        and prereg.get("sim_id") == SIM_ID
        and spec.get("sim_id") == SIM_ID
        and spec.get("classification") == CLASSIFICATION
        and spec.get("promotion_allowed") is False
        and spec.get("formal_admission_allowed") is False
    )
    targets, representatives, class_members = derive_rotation_targets()
    class_count = len(representatives)
    train_states = list(representatives)
    train_set = set(train_states)
    test_states = [state for state in range(STATE_COUNT) if state not in train_set]

    if set(train_states) & set(test_states):
        raise RuntimeError("train/test state overlap")
    if sorted(train_states + test_states) != list(range(STATE_COUNT)):
        raise RuntimeError("train/test split does not cover all 64 states")
    if any(targets[state] != targets[min(rotation_orbit(state))] for state in test_states):
        raise RuntimeError("held-out target is not its independently derived orbit target")

    positive_model, positive, positive_test_batch = train_experiment(
        "directed_ring_positive",
        train_states,
        test_states,
        targets,
        targets,
        class_count,
        erased_edges=False,
    )
    shuffled_targets, target_permutation = make_deranged_targets(targets, class_count)
    _, shuffled, _ = train_experiment(
        "deranged_training_targets_control",
        train_states,
        test_states,
        targets,
        shuffled_targets,
        class_count,
        erased_edges=False,
    )
    _, erased, _ = train_experiment(
        "erased_directed_ring_edges_control",
        train_states,
        test_states,
        targets,
        targets,
        class_count,
        erased_edges=True,
    )

    positive_accuracy = positive["held_out_against_true_targets"]["accuracy"]
    shuffled_accuracy = shuffled["held_out_against_true_targets"]["accuracy"]
    erased_accuracy = erased["held_out_against_true_targets"]["accuracy"]
    shuffled_gap = positive_accuracy - shuffled_accuracy
    erased_gap = positive_accuracy - erased_accuracy
    input_integrity_gates = {
        "preregistration_bound_at_runtime": preregistration_bound,
        "all_64_states_covered_once": sorted(train_states + test_states)
        == list(range(STATE_COUNT)),
        "fourteen_cyclic_target_classes_derived": class_count == 14,
        "train_and_held_state_ids_disjoint": not bool(set(train_states) & set(test_states)),
        "target_shuffle_is_deranged": not any(
            index == value for index, value in enumerate(target_permutation)
        ),
    }
    gates = {
        "held_out_rotation_accuracy_at_least_0_90": positive_accuracy >= 0.90,
        "shuffled_target_gap_at_least_0_25": shuffled_gap >= 0.25,
        "erased_ring_edge_gap_at_least_0_25": erased_gap >= 0.25,
    }

    source_hash = sha256_bytes(SOURCE_PATH.read_bytes())
    target_table = [targets[state] for state in range(STATE_COUNT)]
    split_manifest = {"train_states": train_states, "held_out_states": test_states}
    graph_fixture_manifest = {
        "ring_size": RING_SIZE,
        "positive_edge_index": directed_ring_edges(False).tolist(),
        "erased_edge_index": directed_ring_edges(True).tolist(),
        "state_bits": [list(state_bits(state)) for state in range(STATE_COUNT)],
    }
    control_manifest = {
        "shuffled_target_permutation": target_permutation,
        "erased_edge_index": directed_ring_edges(True).tolist(),
        "shared_model_seed": MODEL_SEED,
        "shared_epochs": EPOCHS,
    }
    sensitivity = torch_func_sensitivity_receipt(positive_model, positive_test_batch)

    result = {
        "schema": "codex_ratchet.pytorch_learned_perception_result.v1",
        "schema_version": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_status": "diagnostic_only",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "all_pass": all(input_integrity_gates.values()) and all(gates.values()),
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_hash,
        "result_path": str(RESULT_PATH),
        "spec_path": str(SPEC_PATH),
        "spec_sha256": spec_sha256,
        "preregistration_receipt_sha256": sha256_bytes(PREREG_PATH.read_bytes()),
        "reads_peer_result": False,
        "peer_result_paths_read": [],
        "engine_contract": {
            "mode": "pytorch_graph_network_packet",
            "role": "topology_dependent_orbit_fit_proxy",
            "semantic_owner": "julia",
            "local_gate": "topology-dependent fitting on isomorphic cyclic presentations only",
        },
        "sim_contract": {
            "tier": "finite learned-perception control lane",
            "purpose": "test learned cyclic-presentation reidentification on a bounded ring fixture",
            "scientific_question": "can a directed PyG classifier reidentify held-out rotations while target and topology controls fail?",
            "sim_execution_kind": "classical",
            "sim_class": "learned_perception_proxy",
            "carrier_layer": "finite 64-state binary six-ring",
            "geometry_layer": "directed cyclic graph presentation",
            "bridge_layer": "none",
            "cut_layer": "none",
            "branch_status_before_run": "preregistered scratch diagnostic",
            "law_or_candidate_tested": "learned cyclic-presentation reidentification only",
            "promotion_blockers": [
                "PyTorch is not semantic owner",
                "learned predictions do not certify exact quotient or basin structure",
                "classification and preregistration forbid promotion",
            ],
        },
        "inputs": {
            "carrier": "all 64 binary states on a periodic directed six-site ring",
            "state_encoding": "integer 0..63; bit i is site i",
            "node_features": "two-channel one-hot binary site value, torch.float64",
            "positive_edges": "six directed edges i -> (i+1) mod 6",
            "erased_control_edges": "empty edge_index with shape [2, 0]",
            "external_training_data": False,
            "peer_artifacts": False,
        },
        "target_derivation": {
            "method": "enumerate six cyclic relabelings per state, choose minimum integer representative, sort representatives, assign contiguous class ids",
            "independent_of_fixture_expected_values": True,
            "class_count_observed_for_label_construction": class_count,
            "representatives": representatives,
            "class_members": {str(key): value for key, value in class_members.items()},
            "target_table_state_0_through_63": target_table,
            "target_table_sha256": sha256_json(target_table),
            "claim_role": "training fixture label construction only; not a PyTorch exact-object receipt",
        },
        "input_integrity_gates": input_integrity_gates,
        "hashes": {
            "source_sha256": source_hash,
            "spec_sha256": spec_sha256,
            "preregistration_receipt_sha256": sha256_bytes(PREREG_PATH.read_bytes()),
            "target_table_sha256": sha256_json(target_table),
            "split_sha256": sha256_json(split_manifest),
            "graph_fixture_sha256": sha256_json(graph_fixture_manifest),
            "controls_sha256": sha256_json(control_manifest),
        },
        "split": {
            "policy": "one minimum cyclic representative per class for training; every other state is a held-out rotation",
            "training_count": len(train_states),
            "held_out_count": len(test_states),
            "state_overlap_count": 0,
            **split_manifest,
            "split_sha256": sha256_json(split_manifest),
        },
        "training": {
            "device": "cpu",
            "dtype": "torch.float64",
            "model_seed": MODEL_SEED,
            "shuffle_seed": SHUFFLE_SEED,
            "deterministic_algorithms": True,
            "epochs": EPOCHS,
            "optimizer": "torch.optim.Adam",
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "hidden_dim": HIDDEN_DIM,
            "message_passing_steps": MESSAGE_PASSING_STEPS,
            "message_update": "LayerNorm(x + MLP(concat(x, directed_predecessor_aggregate)))",
            "activation": "torch.nn.SiLU",
            "normalization": "torch.nn.LayerNorm after each residual message update",
            "early_stopping": False,
            "target_permutation_for_shuffled_control": target_permutation,
            "target_permutation_has_fixed_point": any(
                index == value for index, value in enumerate(target_permutation)
            ),
        },
        "experiments": {
            "positive": positive,
            "shuffled_target_control": shuffled,
            "erased_ring_edge_control": erased,
        },
        "test_accuracy": positive_accuracy,
        "test_margin": positive["held_out_against_true_targets"],
        "control_gaps": {
            "positive_minus_shuffled_target_accuracy": shuffled_gap,
            "positive_minus_erased_ring_edge_accuracy": erased_gap,
        },
        "preregistered_T8_gates": gates,
        "post_audit_interpretation": {
            "held_out_rotations_are_isomorphic_presentations": True,
            "global_pooling_builds_relabel_invariance_into_the_architecture": True,
            "shuffled_target_control_is_sanity_only": True,
            "edge_erasure_is_the_meaningful_topology_dependence_control": True,
            "unseen_object_generalization_earned": False,
        },
        "torch_func_sensitivity": sensitivity,
        "packages_used": ["torch", "torch.func", "torch_geometric"],
        "actual_tools_used": ["torch", "torch.func", "torch_geometric"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [
            "torch_geometric.data.Batch.from_data_list",
            "torch_geometric.nn.MessagePassing.propagate",
            "torch_geometric.nn.global_add_pool",
        ],
        "topology_surfaces_used": [],
        "negatives_run": [
            "fixed-seed deranged training targets evaluated against true targets",
            "same model family retrained after erasing every directed ring edge",
        ],
        "aligned_packages_load_bearing": ["torch", "torch_geometric"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.nn.MessagePassing.propagate",
                "input_object": "batched six-node directed cycle graphs with binary node features",
                "output_object": "six-step orientation-preserving graph embeddings and object logits",
                "positive_case": "intact directed-ring edges on held-out cyclic presentations",
                "negative/erased_control": "same model family retrained with edge_index shape [2,0]",
                "boundary_case": "constant all-zero and all-one rings remain valid finite graphs",
                "demotion_condition": "held accuracy below 0.90 or either preregistered control gap below 0.25",
                "gates": ["all_pass", "T8 learned perception accuracy and control gaps"],
            },
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.nn.global_add_pool",
                "input_object": "node embeddings at input and each directed message-passing depth",
                "output_object": "cyclic-presentation-invariant graph embedding",
                "positive_case": "held rotations share predictions with their training representative",
                "negative/erased_control": "edge erasure reduces pooled information to site-value multiplicities",
                "boundary_case": "one graph from each cyclic class in the training batch",
                "demotion_condition": "rotation-held-out accuracy gate fails",
                "gates": ["all_pass", "held_out_rotation_accuracy_at_least_0_90"],
            },
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.jacrev(torch.func.functional_call)",
                "input_object": "one held-out graph's node-feature tensor and frozen trained parameters",
                "output_object": "true-class margin Jacobian",
                "positive_case": "finite nonzero feature sensitivity",
                "negative/erased_control": "not claim-gating; erased topology is tested by PyG retraining control",
                "boundary_case": "single six-node graph under stateless evaluation",
                "demotion_condition": "none; supportive audit cannot promote or demote exact claims",
                "gates": [],
            },
        ],
        "outputs": {
            "result_json": str(RESULT_PATH),
            "result_json_content": "accuracies, margins, controls, hashes, APIs, gates, and claim ceilings",
            "model_artifact_emitted": False,
            "reason_model_not_emitted": "model hash is sufficient for this scratch diagnostic; no downstream model consumption is authorized",
        },
        "claim_ceiling": {
            "allowed": [
                "bounded topology-dependent fitting of cyclic orbit classes on this 64-state six-site fixture",
                "PyG held-out-rotation accuracy and preregistered control gaps from this run",
            ],
            "never_gates": [
                "exact behavioral-object identity",
                "exact cyclic-orbit equality",
                "quotient semiconjugacy",
                "exact attractor or basin structure",
                "Julia semantic arbitration",
                "JAX exhaustive-history claims",
            ],
            "blocked_consumers": [
                "QIT engine admission",
                "sixteen-stage or four-substage claims",
                "Axis0",
                "general AI perception",
                "MMMs or ontology admission",
                "cross-domain, physics, or consciousness claims",
            ],
            "removal_effect": "removing this lane demotes topology-dependent fit evidence only; packet-level engine-removal nonredundancy remains untested",
        },
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "engine": "pytorch", "out": str(RESULT_PATH)}))


if __name__ == "__main__":
    main()
