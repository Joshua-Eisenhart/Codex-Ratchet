#!/usr/bin/env python3
"""PyTorch learnable readout leg for qit_full_type1_type2_64_live_v1."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from torch.func import jacrev, vmap

from qit_full_type1_type2_64_live_v1_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    SIM_DIR,
    SIM_ID,
    numeric_feature_matrix,
    now_z,
    rel,
    sha256_file,
    write_json,
)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_pytorch_results.json"
DTYPE = torch.float64


def augmented_dataset(mode: str) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    _, values = numeric_feature_matrix(mode)
    base = torch.tensor(values, dtype=DTYPE)
    labels = torch.arange(base.shape[0], dtype=torch.long)
    feature_dim = base.shape[1]
    phase = torch.arange(feature_dim, dtype=DTYPE)
    train_x = []
    train_y = []
    test_x = []
    test_y = []
    for view in range(4):
        jitter = 0.01 * torch.sin((view + 1) * (phase + 1.0))
        scaled = base * (1.0 + 0.02 * view) + jitter
        if view < 3:
            train_x.append(scaled)
            train_y.append(labels)
        else:
            test_x.append(scaled)
            test_y.append(labels)
    return torch.cat(train_x), torch.cat(train_y), torch.cat(test_x), torch.cat(test_y)


def fit_linear_readout(mode: str) -> dict:
    torch.manual_seed(20260707)
    train_x, train_y, test_x, test_y = augmented_dataset(mode)
    mean = train_x.mean(dim=0, keepdim=True)
    std = torch.clamp(train_x.std(dim=0, keepdim=True), min=1.0e-6)
    train_xn = (train_x - mean) / std
    test_xn = (test_x - mean) / std
    layer = torch.nn.Linear(train_x.shape[1], 4, bias=True, dtype=DTYPE)
    opt = torch.optim.Adam(layer.parameters(), lr=0.05)
    for _ in range(420):
        opt.zero_grad()
        loss = torch.nn.functional.cross_entropy(layer(train_xn), train_y)
        loss.backward()
        opt.step()
    with torch.no_grad():
        train_pred = torch.argmax(layer(train_xn), dim=1)
        test_logits = layer(test_xn)
        test_pred = torch.argmax(test_logits, dim=1)
        train_acc = float((train_pred == train_y).to(DTYPE).mean().item())
        test_acc = float((test_pred == test_y).to(DTYPE).mean().item())

    weight = layer.weight.detach()
    bias = layer.bias.detach()

    def max_logit(row: torch.Tensor) -> torch.Tensor:
        return torch.max(row @ weight.T + bias)

    grads = vmap(jacrev(max_logit))(test_xn)
    grad_norms = torch.linalg.norm(grads, dim=1)
    return {
        "mode": mode,
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "loss_final": float(loss.detach().item()),
        "test_predictions": [int(x) for x in test_pred.tolist()],
        "test_labels": [int(x) for x in test_y.tolist()],
        "torch_func_jacrev_grad_norms": [float(x) for x in grad_norms.tolist()],
        "torch_func_jacrev_nonzero": bool(torch.min(grad_norms).item() > 1.0e-9),
        "feature_dim": int(train_x.shape[1]),
    }


def build_result() -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    ordered = fit_linear_readout("ordered_full")
    bag = fit_linear_readout("bag_topology")
    collapsed = fit_linear_readout("collapsed_sheet_loop")
    all_pass = (
        ordered["test_accuracy"] == 1.0
        and ordered["torch_func_jacrev_nonzero"]
        and bag["test_accuracy"] <= 0.5
        and ordered["test_accuracy"] > bag["test_accuracy"]
        and ordered["test_accuracy"] >= collapsed["test_accuracy"]
    )
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "ran": True,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "readouts": {
            "ordered_full": ordered,
            "bag_topology_control": bag,
            "collapsed_sheet_loop_control": collapsed,
        },
        "learned_layer_statement": (
            "A small PyTorch linear readout learns the ordered atlas stream and loses accuracy "
            "when order/projection identity is erased."
        ),
        "ablation_load_bearing": {
            "ordered_minus_bag_accuracy": ordered["test_accuracy"] - bag["test_accuracy"],
            "ordered_minus_collapsed_accuracy": ordered["test_accuracy"] - collapsed["test_accuracy"],
            "torch_func_jacrev_used": ordered["torch_func_jacrev_nonzero"],
        },
        "object_count": 4,
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "package_observables": {
            "torch.func": "jacrev/vmap gradient norms of the learned ordered-stream readout; nonzero sensitivity is required"
        },
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive tensor training of the finite object readout"},
            "torch.func": {
                "tried": True,
                "used": True,
                "reason": "load-bearing jacrev/vmap sensitivity check on the learned ordered-stream readout",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch.func": "load_bearing"},
    }
    write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(
        json.dumps(
            {
                "engine": "pytorch",
                "all_pass": result["all_pass"],
                "ordered_test_accuracy": result["readouts"]["ordered_full"]["test_accuracy"],
                "bag_test_accuracy": result["readouts"]["bag_topology_control"]["test_accuracy"],
                "out": rel(RESULT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
