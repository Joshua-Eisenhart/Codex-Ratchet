"""Small torch-native readout helpers for reservoir scout receipts.

These helpers replace sklearn classifier plumbing in formal scouts whose
nonclassical evidence should rest on torch feature extraction and torch readout
math. They intentionally stay simple: deterministic stratified split,
standardization from the train split, and a small torch-native multinomial
logistic readout with L2 regularization.
"""

from __future__ import annotations

from typing import Any

import torch


def as_float_tensor(value: Any) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().to(dtype=torch.float32)
    return torch.tensor(value, dtype=torch.float32)


def as_label_tensor(value: Any) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().to(dtype=torch.long)
    return torch.tensor(value, dtype=torch.long)


def stratified_split(labels: torch.Tensor, seed: int, test_size: float) -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator().manual_seed(seed)
    train_parts: list[torch.Tensor] = []
    test_parts: list[torch.Tensor] = []
    for label in sorted({int(v) for v in labels.tolist()}):
        idx = torch.nonzero(labels == label, as_tuple=True)[0]
        idx = idx[torch.randperm(idx.numel(), generator=generator)]
        n_test = max(1, int(round(float(idx.numel()) * test_size)))
        n_test = min(n_test, idx.numel() - 1) if idx.numel() > 1 else 1
        test_parts.append(idx[:n_test])
        train_parts.append(idx[n_test:])
    train_idx = torch.cat(train_parts)
    test_idx = torch.cat(test_parts)
    train_idx = train_idx[torch.randperm(train_idx.numel(), generator=generator)]
    test_idx = test_idx[torch.randperm(test_idx.numel(), generator=generator)]
    return train_idx, test_idx


def standardize(train_x: torch.Tensor, test_x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    mean = train_x.mean(dim=0, keepdim=True)
    scale = train_x.std(dim=0, keepdim=True)
    scale = torch.where(scale < 1e-6, torch.ones_like(scale), scale)
    return (train_x - mean) / scale, (test_x - mean) / scale


def classifier_accuracy(
    x: Any,
    y: Any,
    *,
    seed: int,
    shuffle_labels: bool = False,
    test_size: float = 0.35,
    ridge: float = 1e-3,
) -> float:
    x_t = as_float_tensor(x)
    y_t = as_label_tensor(y)
    if shuffle_labels:
        generator = torch.Generator().manual_seed(seed)
        y_t = y_t[torch.randperm(y_t.numel(), generator=generator)]
    train_idx, test_idx = stratified_split(y_t, seed=seed, test_size=test_size)
    train_x, test_x = standardize(x_t[train_idx], x_t[test_idx])
    train_y = y_t[train_idx]
    test_y = y_t[test_idx]
    classes = sorted({int(v) for v in train_y.tolist()})
    class_to_idx = {label: idx for idx, label in enumerate(classes)}
    train_target = torch.tensor([class_to_idx[int(v)] for v in train_y.tolist()], dtype=torch.long)
    weight = torch.zeros((train_x.shape[1], len(classes)), dtype=torch.float32, requires_grad=True)
    bias = torch.zeros(len(classes), dtype=torch.float32, requires_grad=True)
    optimizer = torch.optim.LBFGS([weight, bias], lr=0.8, max_iter=80, line_search_fn="strong_wolfe")

    def closure() -> torch.Tensor:
        optimizer.zero_grad()
        logits = train_x @ weight + bias
        loss = torch.nn.functional.cross_entropy(logits, train_target)
        loss = loss + float(ridge) * (weight.square().sum() + bias.square().sum())
        loss.backward()
        return loss

    optimizer.step(closure)
    with torch.no_grad():
        pred_idx = torch.argmax(test_x @ weight + bias, dim=1)
    pred = torch.tensor([classes[int(idx)] for idx in pred_idx.tolist()], dtype=torch.long)
    return float((pred == test_y).to(torch.float32).mean().item())
