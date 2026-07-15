#!/usr/bin/env python3
"""Complete finite reference oracle for the v1 semantic-forcing rung."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any


Pair = tuple[int, int]


def pair(value: Iterable[int]) -> Pair:
    items = tuple(int(item) for item in value)
    if len(items) != 2 or items[0] == items[1]:
        raise ValueError("pair must contain two distinct addresses")
    return min(items), max(items)


def normalize_labels(labels: Iterable[int]) -> tuple[int, ...]:
    mapping: dict[int, int] = {}
    normalized: list[int] = []
    for value in labels:
        value = int(value)
        if value not in mapping:
            mapping[value] = len(mapping)
        normalized.append(mapping[value])
    return tuple(normalized)


def restricted_growth_partitions(n: int) -> Iterator[tuple[int, ...]]:
    if n <= 0:
        raise ValueError("n must be positive")
    labels = [0] * n

    def visit(index: int, maximum: int) -> Iterator[tuple[int, ...]]:
        if index == n:
            yield tuple(labels)
            return
        for value in range(maximum + 2):
            labels[index] = value
            yield from visit(index + 1, max(maximum, value))

    yield from visit(1, 0)


def related(labels: tuple[int, ...], edge: Pair) -> bool:
    return labels[edge[0]] == labels[edge[1]]


def unordered_pairs(n: int) -> Iterator[Pair]:
    for left in range(n - 1):
        for right in range(left + 1, n):
            yield left, right


@dataclass(frozen=True)
class Instance:
    n: int
    tolerance_edges: frozenset[Pair]
    current_labels: tuple[int, ...]
    demand_weights: tuple[tuple[Pair, float], ...]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Instance":
        n = int(payload["n"])
        tolerance = frozenset(pair(edge) for edge in payload["tolerance_edges"])
        current = normalize_labels(payload["current_labels"])
        demand_rows: dict[Pair, float] = {}
        for row in payload["demand"]:
            edge = pair(row["pair"])
            weight = float(row["weight"])
            if weight <= 0:
                raise ValueError("demand weights must be positive")
            if edge in demand_rows:
                raise ValueError("demand pairs must be unique")
            demand_rows[edge] = weight
        instance = cls(
            n=n,
            tolerance_edges=tolerance,
            current_labels=current,
            demand_weights=tuple(sorted(demand_rows.items())),
        )
        instance.validate()
        return instance

    def validate(self) -> None:
        if self.n <= 0 or len(self.current_labels) != self.n:
            raise ValueError("current_labels length must equal positive n")
        for edge in (*self.tolerance_edges, *(row[0] for row in self.demand_weights)):
            if edge[0] < 0 or edge[1] >= self.n:
                raise ValueError("pair address outside carrier")
        if any(not related(self.current_labels, edge) for edge in self.tolerance_edges):
            raise ValueError("T must be contained in E0")


def contains_tolerance(labels: tuple[int, ...], instance: Instance) -> bool:
    return all(related(labels, edge) for edge in instance.tolerance_edges)


def refines_current(labels: tuple[int, ...], instance: Instance) -> bool:
    return all(
        not related(labels, edge) or related(instance.current_labels, edge)
        for edge in unordered_pairs(instance.n)
    )


def enumerate_candidates(instance: Instance) -> list[tuple[int, ...]]:
    return [
        labels
        for labels in restricted_growth_partitions(instance.n)
        if contains_tolerance(labels, instance) and refines_current(labels, instance)
    ]


def loss(labels: tuple[int, ...], instance: Instance) -> float:
    return sum(
        weight
        for edge, weight in instance.demand_weights
        if related(labels, edge)
    )


def cost_vector(
    labels: tuple[int, ...], instance: Instance
) -> tuple[int, int, int]:
    demand_pairs = {edge for edge, _ in instance.demand_weights}
    removed = {
        edge
        for edge in unordered_pairs(instance.n)
        if related(instance.current_labels, edge) and not related(labels, edge)
    }
    collateral = removed - demand_pairs
    new_class_count = len(set(labels)) - len(set(instance.current_labels))
    return len(removed), len(collateral), new_class_count


def dominates(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    return all(a <= b for a, b in zip(left, right, strict=True)) and any(
        a < b for a, b in zip(left, right, strict=True)
    )


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    instance = Instance.from_payload(payload)
    initial_loss = loss(instance.current_labels, instance)
    candidates = enumerate_candidates(instance)
    records = []
    for labels in candidates:
        candidate_loss = loss(labels, instance)
        drive = initial_loss - candidate_loss
        if drive <= 0:
            continue
        costs = cost_vector(labels, instance)
        records.append(
            {
                "labels": list(labels),
                "loss": candidate_loss,
                "drive": drive,
                "cost_vector": list(costs),
            }
        )
    front = [
        row
        for row in records
        if not any(
            dominates(tuple(other["cost_vector"]), tuple(row["cost_vector"]))
            for other in records
            if other["labels"] != row["labels"]
        )
    ]
    front.sort(key=lambda row: tuple(row["labels"]))
    if not records:
        decision = "HOLD_NONPOSITIVE"
        selected = None
    elif len(front) != 1:
        decision = "HOLD_MSS_AMBIGUOUS"
        selected = None
    else:
        decision = "COMMIT"
        selected = front[0]
    return {
        "schema": "codex_ratchet.tolerance_to_equivalence_v1.oracle_result.v1",
        "candidate_count": len(candidates),
        "admissible_count": len(records),
        "initial_loss": initial_loss,
        "pareto_front": front,
        "decision": decision,
        "selected": selected,
        "claim_ceiling": "finite distinguishability-loss surrogate oracle only",
    }
