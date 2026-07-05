from __future__ import annotations

from typing import Any

import jax.numpy as jnp


def _checked_cells(q: list[list[int]]) -> list[list[int]]:
    used: set[int] = set()
    cells: list[list[int]] = []
    for raw in q:
        cell = [int(x) for x in raw]
        if len(cell) == 0:
            raise ValueError("empty cell")
        for x in cell:
            if x in used:
                raise ValueError("duplicate element")
            used.add(x)
        cells.append(cell)
    return cells


def _fact_array(fact: Any) -> jnp.ndarray:
    return jnp.asarray(fact["values"] if isinstance(fact, dict) else fact, dtype=float)


def _element_profile(x: int, facts: list[Any], n: int) -> jnp.ndarray:
    chunks = []
    for fact in facts:
        values = _fact_array(fact)
        if values.ndim == 1 and values.shape[0] == n:
            chunks.append(jnp.ravel(values[x]))
        elif values.ndim == 2 and values.shape == (n, n):
            chunks.append(jnp.ravel(values[x, :]))
            chunks.append(jnp.ravel(values[:, x]))
        else:
            raise ValueError("fact values must have shape (n,) or (n,n)")
    if not chunks:
        return jnp.asarray([], dtype=float)
    return jnp.concatenate(chunks)


def separation_witness(Q: list[list[int]], facts: list[Any], tolerance: float = 0.0) -> dict[str, Any]:
    cells = _checked_cells(Q)
    if len(cells) == 0:
        return {"conflates": False, "witness_pairs": []}
    n = max(max(cell) for cell in cells) + 1
    hits = []
    for cell_index, cell in enumerate(cells):
        profiles = [(x, _element_profile(x, facts, n)) for x in cell]
        for left_index in range(len(profiles)):
            x, px = profiles[left_index]
            for y, py in profiles[left_index + 1 :]:
                if px.size == 0:
                    delta = 0.0
                else:
                    delta = float(jnp.max(jnp.abs(px - py)))
                if delta > tolerance:
                    hits.append({"cell": cell_index, "pair": [x, y], "delta": delta})
    return {"conflates": len(hits) > 0, "witness_pairs": hits}
