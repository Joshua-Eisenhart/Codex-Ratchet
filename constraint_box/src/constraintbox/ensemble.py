from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping


FrozenHistory = tuple[tuple[str, Any], ...]


def _freeze(history: Mapping[str, Any]) -> FrozenHistory:
    return tuple(sorted(history.items()))


def _thaw(history: FrozenHistory) -> dict[str, Any]:
    return dict(history)


@dataclass(frozen=True)
class FiniteHistoryEnsemble:
    """Finite set of compatible complete histories."""

    histories: tuple[FrozenHistory, ...]

    @classmethod
    def from_mappings(
        cls, histories: Iterable[Mapping[str, Any]]
    ) -> "FiniteHistoryEnsemble":
        frozen = tuple(_freeze(history) for history in histories)
        if len(set(frozen)) != len(frozen):
            raise ValueError("duplicate complete history")
        return cls(frozen)

    def compatible(
        self, constraints: Iterable[Callable[[dict[str, Any]], bool]]
    ) -> "FiniteHistoryEnsemble":
        kept = []
        for frozen in self.histories:
            history = _thaw(frozen)
            if all(constraint(history) for constraint in constraints):
                kept.append(history)
        return FiniteHistoryEnsemble.from_mappings(kept)

    def project(self, keys: tuple[str, ...]) -> tuple[tuple[Any, ...], ...]:
        if not keys:
            raise ValueError("projection needs at least one key")
        values = {
            tuple(_thaw(history)[key] for key in keys)
            for history in self.histories
        }
        return tuple(sorted(values, key=repr))

    def extension_fibre(
        self, keys: tuple[str, ...], projected_value: tuple[Any, ...]
    ) -> "FiniteHistoryEnsemble":
        if len(keys) != len(projected_value):
            raise ValueError("projection arity mismatch")
        selected = []
        for frozen in self.histories:
            history = _thaw(frozen)
            if tuple(history[key] for key in keys) == projected_value:
                selected.append(history)
        return FiniteHistoryEnsemble.from_mappings(selected)

    @property
    def count(self) -> int:
        return len(self.histories)

    @property
    def hartley_capacity_bits(self) -> float | None:
        if not self.histories:
            return None
        return math.log2(len(self.histories))

    def partition(self, probe_keys: tuple[str, ...]) -> tuple[int, ...]:
        labels: dict[tuple[Any, ...], int] = {}
        result = []
        for frozen in self.histories:
            history = _thaw(frozen)
            signature = tuple(history[key] for key in probe_keys)
            labels.setdefault(signature, len(labels))
            result.append(labels[signature])
        return tuple(result)

    def finite_sum(self, weights: Mapping[FrozenHistory, complex]) -> complex:
        missing = [history for history in self.histories if history not in weights]
        if missing:
            raise ValueError("weight missing for a compatible history")
        return sum((weights[history] for history in self.histories), 0j)


def history_pair_field(amplitudes: tuple[complex, ...]) -> tuple[tuple[complex, ...], ...]:
    """Outer product retaining diagonal and off-diagonal history relations."""

    return tuple(
        tuple(left * right.conjugate() for right in amplitudes)
        for left in amplitudes
    )


def diagonal_history_field(
    field: tuple[tuple[complex, ...], ...]
) -> tuple[tuple[complex, ...], ...]:
    return tuple(
        tuple(value if i == j else 0j for j, value in enumerate(row))
        for i, row in enumerate(field)
    )
