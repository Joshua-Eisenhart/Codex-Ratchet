from __future__ import annotations

from typing import Any

import numpy as np


def _cells(q: list[list[int]]) -> list[list[int]]:
    seen: set[int] = set()
    out: list[list[int]] = []
    for cell in q:
        clean = [int(x) for x in cell]
        if not clean:
            raise ValueError("empty cell")
        for x in clean:
            if x in seen:
                raise ValueError("duplicate element")
            seen.add(x)
        out.append(clean)
    return out


def _arity(values: np.ndarray, n: int) -> int:
    if values.ndim == 1 and values.shape[0] == n:
        return 1
    if values.ndim == 2 and values.shape == (n, n):
        return 2
    raise ValueError("fact values must have shape (n,) or (n,n)")


def _profile(x: int, facts: list[Any], n: int) -> np.ndarray:
    parts: list[np.ndarray] = []
    for fact in facts:
        values = np.asarray(fact["values"] if isinstance(fact, dict) else fact, dtype=float)
        if _arity(values, n) == 1:
            parts.append(np.ravel(values[x]))
        else:
            parts.append(np.ravel(values[x, :]))
            parts.append(np.ravel(values[:, x]))
    if not parts:
        return np.array([], dtype=float)
    return np.concatenate(parts)


def separation_witness(Q: list[list[int]], facts: list[Any], tolerance: float = 0.0) -> dict[str, Any]:
    q = _cells(Q)
    if not q:
        return {"conflates": False, "witness_pairs": []}
    n = max(max(cell) for cell in q) + 1
    pairs: list[dict[str, Any]] = []
    for cell_index, cell in enumerate(q):
        profiles = {x: _profile(x, facts, n) for x in cell}
        for i, x in enumerate(cell):
            for y in cell[i + 1 :]:
                delta = float(np.max(np.abs(profiles[x] - profiles[y]))) if profiles[x].size else 0.0
                if delta > tolerance:
                    pairs.append({"cell": cell_index, "pair": [x, y], "delta": delta})
    return {"conflates": bool(pairs), "witness_pairs": pairs}
