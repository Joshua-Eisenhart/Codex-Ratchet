#!/usr/bin/env python3
"""Independent PyTorch lane for the bounded attractor-basin challenge.

This producer does not read Julia, JAX, SMT, or controller result files.  It
computes one finite Float64 grid under the declared map, runs PyTorch-native
Jacobian, graph, and training diagnostics, retains hostile controls, and emits
a scratch-diagnostic receipt.  The receipt is evidence for a later controller;
it is not a self-admission or a scientific basin proof.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as functional
from torch import nn
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing


DTYPE = torch.float64
DEVICE = torch.device("cpu")
H_POSITIVE = 0.2
H_WRONG = -0.2
STEPS = 80
X_TICKS = tuple(range(-15, 16))
Y_TICKS = tuple(range(-5, 6))
TRAINING_STEPS = 240
TRAINING_SEED = 271_828
PERMUTATION_SEED = 314_159
DIVERGENCE_BOUND = 1_000_000.0
EXPECTED_LABEL_COUNTS = {-1: 165, 0: 11, 1: 165, 99: 0}
OBJECT_STATEMENT_SHA256 = (
    "d4f5777a66ddc2e39656c867999c3a6f1e49fde19115a61ce880b6ff293f2128"
)
CLAIM_CEILING = (
    "scratch_diagnostic: one finite 341-point Float64 grid was iterated for "
    "80 steps and checked with PyTorch-native Jacobian, graph, and bounded "
    "training diagnostics; this is not a continuous-basin proof, Julia Canon "
    "admission, CR claim, whole-estate integration claim, release decision, "
    "or scientific promotion"
)
class BasinNeighborMean(MessagePassing):
    """One real PyG message-passing operation over the finite grid graph."""

    def __init__(self) -> None:
        super().__init__(aggr="mean")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        return self.propagate(
            edge_index,
            x=x,
            size=(x.shape[0], x.shape[0]),
        )

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j


class BasinDiagnosticClassifier(nn.Module):
    """Small bounded diagnostic; its prediction has no admission authority."""

    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(2, 8, dtype=DTYPE, device=DEVICE),
            nn.Tanh(),
            nn.Linear(8, 3, dtype=DTYPE, device=DEVICE),
        )

    def forward(self, states: torch.Tensor) -> torch.Tensor:
        return self.layers(states)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _tensor_sha256(tensor: torch.Tensor) -> str:
    """Hash tensor storage without NumPy, CSV, pickle, or peer bridges."""

    detached = tensor.detach().to(device="cpu").contiguous()
    raw_bytes = bytes(detached.view(torch.uint8).reshape(-1).tolist())
    return _sha256(raw_bytes)


def _tensor_receipt(tensor: torch.Tensor) -> dict[str, Any]:
    detached = tensor.detach()
    return {
        "type": "torch.Tensor",
        "dtype": str(detached.dtype),
        "device": str(detached.device),
        "shape": list(detached.shape),
        "sha256": _tensor_sha256(detached),
    }


def _map_state(state: torch.Tensor, h: torch.Tensor) -> torch.Tensor:
    x, y = state.unbind(dim=-1)
    return torch.stack((x - h * (x**3 - x), 0.5 * y))


def _initial_grid() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    x_values = torch.tensor(X_TICKS, dtype=DTYPE, device=DEVICE) / 10.0
    y_values = torch.tensor(Y_TICKS, dtype=DTYPE, device=DEVICE) / 10.0
    x_grid, y_grid = torch.meshgrid(x_values, y_values, indexing="ij")
    states = torch.stack((x_grid.reshape(-1), y_grid.reshape(-1)), dim=1)
    return states, x_values, y_values


def _iterate_map(states: torch.Tensor, h_value: float) -> torch.Tensor:
    h = torch.tensor(h_value, dtype=DTYPE, device=DEVICE)
    step = lambda state: _map_state(state, h)
    current = states.clone()
    for _ in range(STEPS):
        current = torch.func.vmap(step)(current)
    return current


def _fixed_point_jacobians(h_value: float) -> torch.Tensor:
    h = torch.tensor(h_value, dtype=DTYPE, device=DEVICE)
    fixed_points = torch.tensor(
        ((-1.0, 0.0), (0.0, 0.0), (1.0, 0.0)),
        dtype=DTYPE,
        device=DEVICE,
    )
    jacobian = torch.func.jacrev(lambda state: _map_state(state, h))
    return torch.func.vmap(jacobian)(fixed_points)


def _spectral_radii(jacobians: torch.Tensor) -> torch.Tensor:
    return torch.linalg.eigvals(jacobians).abs().amax(dim=1).real


def _classify_terminals(
    final_states: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    targets = torch.tensor(
        ((-1.0, 0.0), (0.0, 0.0), (1.0, 0.0)),
        dtype=DTYPE,
        device=DEVICE,
    )
    target_labels = torch.tensor((-1, 0, 1), dtype=torch.long, device=DEVICE)
    finite = torch.isfinite(final_states).all(dim=1)
    bounded = finite & (final_states.abs().amax(dim=1) <= DIVERGENCE_BOUND)
    labels = torch.full(
        (final_states.shape[0],),
        99,
        dtype=torch.long,
        device=DEVICE,
    )
    residuals = torch.full(
        (final_states.shape[0],),
        float("inf"),
        dtype=DTYPE,
        device=DEVICE,
    )
    if bool(bounded.any().item()):
        distances = torch.cdist(final_states[bounded], targets)
        nearest_distance, nearest_index = distances.min(dim=1)
        labels[bounded] = target_labels[nearest_index]
        residuals[bounded] = nearest_distance
    return labels, bounded, residuals


def _label_counts(labels: torch.Tensor) -> dict[str, int]:
    return {
        str(label): int((labels == label).sum().item())
        for label in (-1, 0, 1, 99)
    }


def _grid_edge_index(nx: int, ny: int) -> torch.Tensor:
    sources: list[int] = []
    targets: list[int] = []
    for x_index in range(nx):
        for y_index in range(ny):
            node = x_index * ny + y_index
            if x_index + 1 < nx:
                neighbor = (x_index + 1) * ny + y_index
                sources.extend((node, neighbor))
                targets.extend((neighbor, node))
            if y_index + 1 < ny:
                neighbor = x_index * ny + y_index + 1
                sources.extend((node, neighbor))
                targets.extend((neighbor, node))
    return torch.tensor(
        (sources, targets),
        dtype=torch.long,
        device=DEVICE,
    )


def _graph_diagnostic(labels: torch.Tensor) -> dict[str, Any]:
    class_ids = labels + 1
    node_features = functional.one_hot(class_ids, num_classes=3).to(dtype=DTYPE)
    edge_index = _grid_edge_index(len(X_TICKS), len(Y_TICKS))
    graph = Data(x=node_features, edge_index=edge_index)
    operator = BasinNeighborMean()
    intact_messages = operator(graph.x, graph.edge_index)
    intact_prediction = intact_messages.argmax(dim=1)
    intact_accuracy = (intact_prediction == class_ids).to(DTYPE).mean()

    severed_edge_index = torch.empty(
        (2, 0),
        dtype=torch.long,
        device=DEVICE,
    )
    severed_messages = operator(graph.x, severed_edge_index)
    severed_prediction = severed_messages.argmax(dim=1)
    severed_accuracy = (severed_prediction == class_ids).to(DTYPE).mean()
    accuracy_drop = intact_accuracy - severed_accuracy
    severance_detected = bool(
        (
            intact_accuracy >= 0.99
            and severed_accuracy <= 0.60
            and accuracy_drop >= 0.25
            and severed_messages.abs().sum() == 0
        ).item()
    )
    return {
        "graph_type": "torch_geometric.data.Data",
        "operation": (
            "torch_geometric.nn.MessagePassing.propagate(aggr='mean')"
        ),
        "node_count": int(graph.num_nodes),
        "directed_edge_count": int(graph.num_edges),
        "edge_index": _tensor_receipt(graph.edge_index),
        "node_features": _tensor_receipt(graph.x),
        "intact_messages": _tensor_receipt(intact_messages),
        "intact_label_accuracy": float(intact_accuracy.item()),
        "severed_edge_count": int(severed_edge_index.shape[1]),
        "severed_messages": _tensor_receipt(severed_messages),
        "severed_label_accuracy": float(severed_accuracy.item()),
        "accuracy_drop": float(accuracy_drop.item()),
        "severance_detected": severance_detected,
        "authority": "diagnostic graph-severance control only",
    }


def _train_diagnostic(
    states: torch.Tensor,
    truth_class_ids: torch.Tensor,
    training_class_ids: torch.Tensor,
    *,
    seed: int,
) -> dict[str, Any]:
    torch.manual_seed(seed)
    model = BasinDiagnosticClassifier()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.03)
    class_counts = torch.bincount(training_class_ids, minlength=3).to(DTYPE)
    class_weights = training_class_ids.numel() / (3.0 * class_counts)
    loss = torch.tensor(float("inf"), dtype=DTYPE, device=DEVICE)
    for _ in range(TRAINING_STEPS):
        optimizer.zero_grad(set_to_none=True)
        logits = model(states)
        loss = functional.cross_entropy(
            logits,
            training_class_ids,
            weight=class_weights,
        )
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        final_logits = model(states)
        predictions = final_logits.argmax(dim=1)
        truth_accuracy = (predictions == truth_class_ids).to(DTYPE).mean()
        training_accuracy = (
            (predictions == training_class_ids).to(DTYPE).mean()
        )
        parameters = torch.cat(
            [parameter.detach().reshape(-1) for parameter in model.parameters()]
        )
    return {
        "model": "Linear(2,8)-Tanh-Linear(8,3)",
        "optimizer": "torch.optim.Adam",
        "loss": "torch.nn.functional.cross_entropy",
        "seed": seed,
        "steps": TRAINING_STEPS,
        "parameter_count": int(parameters.numel()),
        "final_loss": float(loss.detach().item()),
        "truth_accuracy": float(truth_accuracy.item()),
        "training_label_accuracy": float(training_accuracy.item()),
        "predictions": _tensor_receipt(predictions),
        "parameters": _tensor_receipt(parameters),
        "authority": "bounded trainable diagnostic only",
    }


def _boundary_measurements(
    initial_states: torch.Tensor,
    final_states: torch.Tensor,
    labels: torch.Tensor,
    positive_radii: torch.Tensor,
) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for x_value, expected_label in ((-0.1, -1), (0.0, 0), (0.1, 1)):
        x_tensor = torch.tensor(x_value, dtype=DTYPE, device=DEVICE)
        selector = initial_states[:, 0] == x_tensor
        selected_labels = labels[selector]
        selected_final = final_states[selector]
        rows[str(x_value)] = {
            "initial_count": int(selector.sum().item()),
            "expected_label": expected_label,
            "observed_labels": sorted(
                {int(item) for item in selected_labels.tolist()}
            ),
            "max_abs_terminal_x": float(
                selected_final[:, 0].abs().max().item()
            ),
            "max_abs_terminal_y": float(
                selected_final[:, 1].abs().max().item()
            ),
        }
    passed = bool(
        rows["-0.1"]["observed_labels"] == [-1]
        and rows["0.0"]["observed_labels"] == [0]
        and rows["0.1"]["observed_labels"] == [1]
        and rows["0.0"]["max_abs_terminal_x"] == 0.0
        and float(positive_radii[1].item()) > 1.0
    )
    return {
        "rows": rows,
        "fixed_point_zero_spectral_radius": float(positive_radii[1].item()),
        "passed": passed,
    }


def _run_once() -> dict[str, Any]:
    initial_states, x_values, y_values = _initial_grid()
    positive_final = _iterate_map(initial_states, H_POSITIVE)
    positive_labels, positive_bounded, positive_residuals = (
        _classify_terminals(positive_final)
    )
    wrong_final = _iterate_map(initial_states, H_WRONG)
    wrong_labels, wrong_bounded, wrong_residuals = _classify_terminals(
        wrong_final
    )

    positive_jacobians = _fixed_point_jacobians(H_POSITIVE)
    wrong_jacobians = _fixed_point_jacobians(H_WRONG)
    positive_radii = _spectral_radii(positive_jacobians)
    wrong_radii = _spectral_radii(wrong_jacobians)
    positive_stable = positive_radii < 1.0
    wrong_stable = wrong_radii < 1.0

    positive_counts = _label_counts(positive_labels)
    wrong_counts = _label_counts(wrong_labels)
    max_positive_residual = float(
        positive_residuals[positive_bounded].max().item()
    )
    max_wrong_bounded_residual = float(
        wrong_residuals[wrong_bounded].max().item()
    )

    graph = _graph_diagnostic(positive_labels)
    truth_class_ids = positive_labels + 1
    training_positive = _train_diagnostic(
        initial_states,
        truth_class_ids,
        truth_class_ids,
        seed=TRAINING_SEED,
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(PERMUTATION_SEED)
    permutation = torch.randperm(
        truth_class_ids.numel(),
        generator=generator,
        device=DEVICE,
    )
    permuted_training_labels = truth_class_ids[permutation]
    training_permuted = _train_diagnostic(
        initial_states,
        truth_class_ids,
        permuted_training_labels,
        seed=TRAINING_SEED,
    )

    observed_labels = sorted(
        int(item) for item in torch.unique(positive_labels).tolist()
    )
    erased_catalog = (-1, 1)
    missing_after_erasure = sorted(
        set(observed_labels).difference(erased_catalog)
    )
    boundary = _boundary_measurements(
        initial_states,
        positive_final,
        positive_labels,
        positive_radii,
    )

    positive_passed = bool(
        positive_counts
        == {str(key): value for key, value in EXPECTED_LABEL_COUNTS.items()}
        and bool(positive_bounded.all().item())
        and max_positive_residual <= 1.0e-12
        and positive_stable.tolist() == [True, False, True]
    )
    wrong_passed = bool(
        wrong_counts
        == {"-1": 11, "0": 209, "1": 11, "99": 110}
        and wrong_stable.tolist() == [False, True, False]
        and wrong_counts != positive_counts
    )
    erased_passed = missing_after_erasure == [0]
    label_permutation_drop = (
        training_positive["truth_accuracy"]
        - training_permuted["truth_accuracy"]
    )
    label_permutation_passed = bool(
        training_positive["truth_accuracy"] >= 0.99
        and training_permuted["truth_accuracy"] <= 0.65
        and label_permutation_drop >= 0.30
    )

    controls = {
        "positive": {
            "passed": positive_passed,
            "expected_label_counts": {
                str(key): value for key, value in EXPECTED_LABEL_COUNTS.items()
            },
            "observed_label_counts": positive_counts,
            "max_terminal_distance_to_named_fixed_point": (
                max_positive_residual
            ),
            "stable_fixed_point_pattern_minus_one_zero_plus_one": (
                positive_stable.tolist()
            ),
        },
        "wrong_h_negative_0_2": {
            "passed": wrong_passed,
            "h": H_WRONG,
            "observed_label_counts": wrong_counts,
            "bounded_state_count": int(wrong_bounded.sum().item()),
            "diverged_or_out_of_bound_count": int(
                (~wrong_bounded).sum().item()
            ),
            "max_bounded_terminal_distance_to_named_fixed_point": (
                max_wrong_bounded_residual
            ),
            "stable_fixed_point_pattern_minus_one_zero_plus_one": (
                wrong_stable.tolist()
            ),
            "falsifier": "stability signature and basin partition must change",
        },
        "erased_attractor_label": {
            "passed": erased_passed,
            "erased_label": 0,
            "catalog_after_erasure": list(erased_catalog),
            "observed_labels": observed_labels,
            "missing_catalog_labels": missing_after_erasure,
            "partition_completeness_gate": "BLOCKED",
        },
        "boundary_x_zero": boundary,
        "graph_severance": {
            "passed": graph["severance_detected"],
            "intact_directed_edge_count": graph["directed_edge_count"],
            "severed_directed_edge_count": graph["severed_edge_count"],
            "intact_label_accuracy": graph["intact_label_accuracy"],
            "severed_label_accuracy": graph["severed_label_accuracy"],
            "accuracy_drop": graph["accuracy_drop"],
        },
        "label_permutation": {
            "passed": label_permutation_passed,
            "permutation_seed": PERMUTATION_SEED,
            "positive_truth_accuracy": training_positive["truth_accuracy"],
            "permuted_training_truth_accuracy": (
                training_permuted["truth_accuracy"]
            ),
            "truth_accuracy_drop": label_permutation_drop,
            "permutation": _tensor_receipt(permutation),
        },
    }

    measurements = {
        "initial_grid": {
            "x": {
                "start": -1.5,
                "stop": 1.5,
                "step": 0.1,
                "count": len(X_TICKS),
                "tensor": _tensor_receipt(x_values),
            },
            "y": {
                "start": -0.5,
                "stop": 0.5,
                "step": 0.1,
                "count": len(Y_TICKS),
                "tensor": _tensor_receipt(y_values),
            },
            "state_count": int(initial_states.shape[0]),
            "states": _tensor_receipt(initial_states),
        },
        "positive": {
            "h": H_POSITIVE,
            "steps": STEPS,
            "final_states": _tensor_receipt(positive_final),
            "labels": _tensor_receipt(positive_labels),
            "label_counts": positive_counts,
            "fixed_point_jacobians": _tensor_receipt(positive_jacobians),
            "fixed_point_jacobian_values": positive_jacobians.tolist(),
            "fixed_point_spectral_radii": positive_radii.tolist(),
            "max_terminal_distance_to_named_fixed_point": (
                max_positive_residual
            ),
        },
        "wrong": {
            "h": H_WRONG,
            "steps": STEPS,
            "final_states": _tensor_receipt(wrong_final),
            "labels": _tensor_receipt(wrong_labels),
            "label_counts": wrong_counts,
            "fixed_point_jacobians": _tensor_receipt(wrong_jacobians),
            "fixed_point_jacobian_values": wrong_jacobians.tolist(),
            "fixed_point_spectral_radii": wrong_radii.tolist(),
        },
        "graph_diagnostic": graph,
        "training_diagnostic": {
            "positive_internal_labels": training_positive,
            "permuted_internal_labels": training_permuted,
        },
    }

    signature = {
        "initial_states_sha256": measurements["initial_grid"]["states"][
            "sha256"
        ],
        "positive_final_sha256": measurements["positive"]["final_states"][
            "sha256"
        ],
        "positive_labels_sha256": measurements["positive"]["labels"][
            "sha256"
        ],
        "positive_jacobians_sha256": measurements["positive"][
            "fixed_point_jacobians"
        ]["sha256"],
        "wrong_final_sha256": measurements["wrong"]["final_states"][
            "sha256"
        ],
        "wrong_labels_sha256": measurements["wrong"]["labels"]["sha256"],
        "wrong_jacobians_sha256": measurements["wrong"][
            "fixed_point_jacobians"
        ]["sha256"],
        "graph_messages_sha256": graph["intact_messages"]["sha256"],
        "training_parameters_sha256": training_positive["parameters"][
            "sha256"
        ],
        "permuted_training_parameters_sha256": training_permuted[
            "parameters"
        ]["sha256"],
        "control_outcomes": {
            name: bool(control["passed"]) for name, control in controls.items()
        },
    }
    return {
        "measurements": measurements,
        "controls": controls,
        "signature": signature,
        "signature_sha256": _sha256(_canonical_json(signature)),
    }


def _runtime_receipt() -> dict[str, Any]:
    return {
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "executable_reported": sys.executable,
            "executable_resolved": str(Path(sys.executable).resolve()),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "byteorder": sys.byteorder,
        },
        "torch": {
            "version": torch.__version__,
            "distribution_version": importlib.metadata.version("torch"),
            "default_dtype": str(torch.get_default_dtype()),
            "device": str(DEVICE),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": torch.version.cuda,
            "deterministic_algorithms_enabled": (
                torch.are_deterministic_algorithms_enabled()
            ),
            "num_threads": torch.get_num_threads(),
        },
        "torch_geometric": {
            "version": importlib.metadata.version("torch-geometric"),
            "module_origin": str(Path(sys.modules["torch_geometric"].__file__).resolve()),
        },
    }


def _tool_calls() -> list[dict[str, Any]]:
    return [
        {
            "tool": "torch.func",
            "qualified_api/function": "torch.func.vmap",
            "input_object": "341x2 Float64 state tensor and one-step F_h",
            "output_object": "341x2 Float64 state tensor per each of 80 steps",
            "positive_case": "h=0.2 basin sweep",
            "negative/erased_control": "h=-0.2 wrong-sign sweep",
            "boundary_case": "exact x=0 and adjacent x=+-0.1 rows",
            "demotion_condition": "missing API, non-Float64 output, or replay drift",
            "gates": ["positive", "wrong_h_negative_0_2", "boundary_x_zero", "replay"],
            "integration_depth": "load_bearing",
        },
        {
            "tool": "torch.func",
            "qualified_api/function": "torch.func.jacrev composed with torch.func.vmap",
            "input_object": "three named fixed points for h=0.2 and h=-0.2",
            "output_object": "two 3x2x2 Float64 Jacobian tensors",
            "positive_case": "stable pattern [true,false,true]",
            "negative/erased_control": "wrong-sign stable pattern [false,true,false]",
            "boundary_case": "spectral radius 1.2 at (0,0) for h=0.2",
            "demotion_condition": "stability signature does not flip",
            "gates": ["positive", "wrong_h_negative_0_2", "boundary_x_zero"],
            "integration_depth": "load_bearing",
        },
        {
            "tool": "torch_geometric",
            "qualified_api/function": "torch_geometric.nn.MessagePassing.propagate",
            "input_object": "341-node directed four-neighbor grid with internal one-hot labels",
            "output_object": "341x3 mean-neighbor message tensor",
            "positive_case": "1280-edge intact graph",
            "negative/erased_control": "zero-edge severed graph",
            "boundary_case": "basin-boundary nodes remain in the intact graph",
            "demotion_condition": "severance does not erase messages and degrade the diagnostic",
            "gates": ["graph_severance"],
            "integration_depth": "control_load_bearing_not_network_engine_authority",
        },
        {
            "tool": "torch.optim",
            "qualified_api/function": "torch.optim.Adam.step",
            "input_object": "initial grid with labels produced internally by the positive map run",
            "output_object": "bounded 51-parameter diagnostic classifier",
            "positive_case": "240 steps on internal basin labels",
            "negative/erased_control": "240 steps on deterministically permuted labels",
            "boundary_case": "11 internally labeled x=0 samples",
            "demotion_condition": "positive accuracy below 0.99 or permutation drop below 0.30",
            "gates": ["label_permutation"],
            "integration_depth": "diagnostic_control_load_bearing",
        },
    ]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the independent bounded PyTorch basin lane and write its "
            "receipt into an explicitly selected directory."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="directory that will receive the JSON receipt and SHA-256 sidecar",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output_root = args.output_dir.expanduser().resolve()
    torch.set_default_dtype(DTYPE)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)

    first = _run_once()
    replay = _run_once()
    replay_passed = bool(
        first["signature_sha256"] == replay["signature_sha256"]
        and first["signature"] == replay["signature"]
    )
    controls = dict(first["controls"])
    controls["replay"] = {
        "passed": replay_passed,
        "first_signature_sha256": first["signature_sha256"],
        "replay_signature_sha256": replay["signature_sha256"],
        "same_process_independent_recomputation": True,
    }
    all_controls_passed = all(
        bool(control["passed"]) for control in controls.values()
    )

    source_path = Path(__file__).resolve()
    source_sha256 = _sha256(source_path.read_bytes())
    receipt_path = output_root / "torch_basin_receipt.json"
    sidecar_path = output_root / "torch_basin_receipt.sha256"
    receipt: dict[str, Any] = {
        "schema": "constraintbox.external-sim.pytorch-basin-receipt.v1",
        "receipt_id": "cb_attractor_basin_three_engine_20260801.pytorch.v1",
        "object_statement_sha256": OBJECT_STATEMENT_SHA256,
        "producer": {
            "engine": "pytorch",
            "engine_role": "external_sim_engine_evidence_producer",
            "ran": True,
            "reads_peer_result": False,
            "peer_result_paths_read": [],
            "source_path": str(source_path),
            "source_sha256": source_sha256,
            "packages_used": ["torch", "torch_geometric"],
            "aligned_packages_load_bearing": ["torch.func"],
            "aligned_packages_control_load_bearing": ["torch_geometric"],
        },
        "run_metadata": {
            "output_dir_requested": str(args.output_dir),
            "output_dir_resolved": str(output_root),
            "receipt_path": str(receipt_path),
            "sidecar_path": str(sidecar_path),
            "path_fields_are_semantic_claim_inputs": False,
        },
        "runtime": _runtime_receipt(),
        "type_contract": {
            "state_dtype": "torch.float64",
            "label_dtype": "torch.int64",
            "device": "cpu",
            "serialization": "canonical JSON receipt plus raw-tensor SHA-256",
            "forbidden_claim_path_bridges_used": [],
        },
        "mathematical_map": {
            "name": "F_h",
            "formula": "F_h(x,y)=(x-h*(x^3-x),0.5*y)",
            "positive_h": H_POSITIVE,
            "wrong_control_h": H_WRONG,
            "steps": STEPS,
            "fixed_points": [[-1.0, 0.0], [0.0, 0.0], [1.0, 0.0]],
            "attractor_labels_generated_internally": [-1, 0, 1],
        },
        "actual_api_calls": [
            "torch.func.vmap",
            "torch.func.jacrev",
            "torch.linalg.eigvals",
            "torch.cdist",
            "torch_geometric.data.Data",
            "torch_geometric.nn.MessagePassing.propagate",
            "torch.nn.functional.cross_entropy",
            "torch.optim.Adam.step",
        ],
        "tool_calls": _tool_calls(),
        "measurements": first["measurements"],
        "controls": controls,
        "all_required_controls_passed": all_controls_passed,
        "independent_replay": controls["replay"],
        "admission": {
            "producer_made_admission_decision": False,
            "promotion_allowed": False,
            "consumer_required": "typed ConstraintBox controller envelope",
            "reason": "external evidence producers cannot self-admit",
        },
        "claim_ceiling": CLAIM_CEILING,
        "blocked_downstream_claims": [
            "continuous attractor-basin proof",
            "Julia Canon admission",
            "formal CR admission",
            "whole sim estate integrated",
            "ConstraintBox release promotion",
            "automatic tuning",
        ],
    }
    receipt["hashes"] = {
        "source_sha256": source_sha256,
        "first_run_signature_sha256": first["signature_sha256"],
        "replay_run_signature_sha256": replay["signature_sha256"],
        "path_independent_semantic_replay_sha256": first[
            "signature_sha256"
        ],
        "receipt_body_sha256": _sha256(_canonical_json(receipt)),
    }

    output_root.mkdir(parents=True, exist_ok=True)
    receipt_payload = _canonical_json(receipt) + b"\n"
    receipt_path.write_bytes(receipt_payload)
    receipt_file_sha256 = _sha256(receipt_payload)
    sidecar_path.write_text(
        f"{receipt_file_sha256}  {receipt_path.name}\n",
        encoding="utf-8",
    )

    written_payload = receipt_path.read_bytes()
    written = json.loads(written_payload)
    if (
        _sha256(written_payload) != receipt_file_sha256
        or written["hashes"]["source_sha256"] != source_sha256
        or written["all_required_controls_passed"] is not True
        or written["admission"]["promotion_allowed"] is not False
    ):
        raise RuntimeError("written PyTorch receipt failed its local integrity check")
    print(
        _canonical_json(
            {
                "all_required_controls_passed": all_controls_passed,
                "claim_ceiling": CLAIM_CEILING,
                "receipt_file_sha256": receipt_file_sha256,
                "receipt_path": str(receipt_path),
                "sidecar_path": str(sidecar_path),
            }
        ).decode("utf-8")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
