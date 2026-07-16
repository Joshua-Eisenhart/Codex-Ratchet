#!/usr/bin/env python3
"""PyTorch learnable prototype leg for qit_projection_battery_v0."""

from __future__ import annotations

import json
from typing import Any

import torch
from torch.func import jacrev, vmap

from qit_projection_battery_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULTS,
    SIM_DIR,
    SIM_ID,
    VIEW_MASKS,
    now_z,
    object_ids,
    projection_records,
    rel,
    sha256_file,
    write_json,
)

SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULTS / f"{SIM_ID}_pytorch_results.json"
DTYPE = torch.float64


def tensor_records(control: str | None = None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, list[str]]:
    labels = object_ids()
    views = list(VIEW_MASKS)
    records = projection_records(control=control)
    x = torch.tensor([row["vector"] for row in records], dtype=DTYPE)
    y = torch.tensor([labels.index(row["object_id"]) for row in records], dtype=torch.long)
    view_id = torch.tensor([views.index(row["view"]) for row in records], dtype=torch.long)
    return x, y, view_id, views


def train_prototypes(train_x: torch.Tensor, train_y: torch.Tensor, object_count: int) -> torch.Tensor:
    torch.manual_seed(20260707)
    prototypes = torch.nn.Parameter(torch.zeros((object_count, train_x.shape[1]), dtype=DTYPE))
    with torch.no_grad():
        for idx in range(object_count):
            rows = train_x[train_y == idx]
            prototypes[idx].copy_(rows.mean(dim=0))
        prototypes.add_(0.001 * torch.randn_like(prototypes))
    opt = torch.optim.Adam([prototypes], lr=0.03)
    for _ in range(220):
        opt.zero_grad()
        logits = -torch.cdist(train_x, prototypes, p=2.0) ** 2
        loss = torch.nn.functional.cross_entropy(logits, train_y)
        loss.backward()
        opt.step()
    return prototypes.detach()


def learned_projection_readout(control: str | None = None) -> dict[str, Any]:
    labels = object_ids()
    x, y, view_id, views = tensor_records(control=control)
    per_view = []
    grad_norms_all: list[float] = []
    for heldout_idx, heldout_view in enumerate(views):
        train_mask = view_id != heldout_idx
        test_mask = view_id == heldout_idx
        train_x = x[train_mask]
        train_y = y[train_mask]
        test_x = x[test_mask]
        test_y = y[test_mask]
        prototypes = train_prototypes(train_x, train_y, len(labels))
        logits = -torch.cdist(test_x, prototypes, p=2.0) ** 2
        predictions = torch.argmax(logits, dim=1)
        accuracy = float((predictions == test_y).to(DTYPE).mean().item())

        def max_logit(row: torch.Tensor) -> torch.Tensor:
            return torch.max(-(torch.sum((prototypes - row) ** 2, dim=1)))

        grads = vmap(jacrev(max_logit))(test_x)
        grad_norms = torch.linalg.norm(grads, dim=1)
        grad_norms_all.extend(float(value) for value in grad_norms.tolist())
        per_view.append(
            {
                "heldout_view": heldout_view,
                "accuracy": round(accuracy, 12),
                "predictions": [int(value) for value in predictions.tolist()],
                "labels": [int(value) for value in test_y.tolist()],
                "lossless_train_shape": [int(train_x.shape[0]), int(train_x.shape[1])],
                "torch_func_jacrev_grad_norms": [float(value) for value in grad_norms.tolist()],
            }
        )
    mean_accuracy = sum(row["accuracy"] for row in per_view) / len(per_view)
    return {
        "control": control or "none",
        "object_count": len(labels),
        "view_count": len(views),
        "mean_heldout_accuracy": round(mean_accuracy, 12),
        "min_heldout_accuracy": round(min(row["accuracy"] for row in per_view), 12),
        "torch_func_jacrev_nonzero": bool(min(grad_norms_all) > 1.0e-9),
        "view_results": per_view,
    }


def build_result() -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    nominal = learned_projection_readout()
    bag = learned_projection_readout(control="bag_erased")
    erased = learned_projection_readout(control="view_erased")
    all_pass = (
        nominal["mean_heldout_accuracy"] >= 0.85
        and nominal["torch_func_jacrev_nonzero"]
        and bag["mean_heldout_accuracy"] <= 0.25
        and erased["mean_heldout_accuracy"] <= 0.25
        and nominal["mean_heldout_accuracy"] - bag["mean_heldout_accuracy"] >= 0.5
        and nominal["mean_heldout_accuracy"] - erased["mean_heldout_accuracy"] >= 0.5
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
        "object_count": nominal["object_count"],
        "view_count": nominal["view_count"],
        "learned_projection_readouts": {
            "nominal": nominal,
            "bag_erased_control": bag,
            "view_erased_control": erased,
        },
        "learned_layer_statement": (
            "A tiny PyTorch prototype readout learns the finite projection records and fails at chance "
            "when the carrier is bag-erased or view-erased."
        ),
        "ablation_load_bearing": {
            "nominal_minus_bag_accuracy": nominal["mean_heldout_accuracy"] - bag["mean_heldout_accuracy"],
            "nominal_minus_view_erased_accuracy": nominal["mean_heldout_accuracy"] - erased["mean_heldout_accuracy"],
            "torch_func_jacrev_used": nominal["torch_func_jacrev_nonzero"],
        },
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "package_observables": {
            "torch.func": "jacrev/vmap gradient norms of the learned finite projection readout; nonzero nominal sensitivity is required"
        },
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive tensor optimization of finite prototype readouts"},
            "torch.func": {
                "tried": True,
                "used": True,
                "reason": "load-bearing jacrev/vmap sensitivity check on the learned nominal projection readout",
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
                "nominal_mean": result["learned_projection_readouts"]["nominal"]["mean_heldout_accuracy"],
                "bag_mean": result["learned_projection_readouts"]["bag_erased_control"]["mean_heldout_accuracy"],
                "out": rel(RESULT_PATH),
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
