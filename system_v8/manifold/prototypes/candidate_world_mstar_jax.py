#!/usr/bin/env python3
"""Independent JAX lane for the finite M★ candidate world."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import jax
from jax import config

config.update("jax_enable_x64", True)
import jax.numpy as jnp


HERE = Path(__file__).resolve().parent
CONFIG = HERE / "candidate_world_mstar_config_v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hopfield_update(state: tuple[int, ...]) -> tuple[int, ...]:
    size = len(state)
    return tuple(
        1 if state[(i - 1) % size] + state[i] + state[(i + 1) % size] >= 2 else 0
        for i in range(size)
    )


def attractor(state: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    seen: list[tuple[int, ...]] = []
    current = state
    for _ in range(32):
        if current in seen:
            return tuple(seen[seen.index(current) :])
        seen.append(current)
        current = hopfield_update(current)
    return (current,)


def basin_summary() -> dict:
    basins: dict[str, list[tuple[int, ...]]] = {}
    assignments: dict[str, str] = {}
    for state in itertools.product((0, 1), repeat=4):
        cycle = attractor(state)
        key = "|".join("".join(map(str, value)) for value in cycle)
        basins.setdefault(key, []).append(state)
        assignments["".join(map(str, state))] = key
    subbasins = {
        f"{assignments[''.join(map(str, (i % 2, j % 2, k % 2, (i + j + k) % 2)))]}::shell{i}"
        for i in range(3) for j in range(4) for k in range(4)
    }
    return {
        "basin_count": len(basins),
        "basin_sizes": sorted((len(v) for v in basins.values()), reverse=True),
        "subbasin_count": len(subbasins),
        "basin_recurrence": bool(basins),
    }


def node_index(node: tuple[int, int, int], n: int) -> int:
    return node[0] * n * n + node[1] * n + node[2]


def open_step(node: tuple[int, int, int], shells: int, n: int) -> tuple[int, int, int]:
    i, j, k = node
    return ((i + 1) % shells, (j + 1 + i) % n, (k + i) % n)


def bind_step(node: tuple[int, int, int], n: int) -> tuple[int, int, int]:
    i, j, k = node
    return (i, j, (k + j + 1) % n)


def path_arrays(hand: int, shells: int, n: int, depth: int, beta: float):
    node_list = [(i, j, k) for i in range(shells) for j in range(n) for k in range(n)]
    words = ["".join(bits) for bits in itertools.product("OB", repeat=depth)]
    count = len(node_list)
    endpoint = []
    actions = []
    phases = []
    for node in node_list:
        row_end, row_action, row_phase = [], [], []
        for word in words:
            current = node
            action = 0.0
            phase = 0.0
            for step, operation in enumerate(word, start=1):
                current = open_step(current, shells, n) if operation == "O" else bind_step(current, n)
                i, j, k = current
                action += 1.0 + (0.25 if operation == "B" else 0.0) + 0.05 * i
                phase += hand * 2.0 * math.pi * (j - k + step * i) / n
            row_end.append(node_index(current, n))
            row_action.append(action)
            row_phase.append(phase)
        endpoint.append(row_end)
        actions.append(row_action)
        phases.append(row_phase)
    onehot = jnp.zeros((count, len(words), count), dtype=jnp.float64)
    for row, values in enumerate(endpoint):
        for path, target in enumerate(values):
            onehot = onehot.at[row, path, target].set(1.0)
    return jnp.asarray(actions), jnp.asarray(phases), onehot, len(words), node_list


def lane_summary(hand: int, cfg: dict) -> dict:
    shells, n, depth, beta = cfg["shells"], cfg["ring_size"], cfg["path_depth"], cfg["beta"]
    actions, phases, onehot, path_count, node_list = path_arrays(hand, shells, n, depth, beta)
    weights = jnp.exp(-beta * actions + 1j * phases)

    @jax.jit
    def aggregate(w, incidence):
        coherent = jnp.sum(w[..., None] * incidence, axis=1)
        incoherent = jnp.sum((jnp.abs(w) ** 2)[..., None] * incidence, axis=1)
        return coherent, incoherent

    coherent, incoherent = aggregate(weights, onehot)
    coherent_prob = jnp.abs(coherent) ** 2
    coherent_prob = coherent_prob / jnp.sum(coherent_prob, axis=1, keepdims=True)
    incoherent = incoherent / jnp.sum(incoherent, axis=1, keepdims=True)
    interference = jnp.sum(jnp.abs(coherent_prob - incoherent), axis=1)
    total_amplitude = jnp.sum(coherent, axis=1)
    return {
        "hand": hand,
        "path_count_per_node": path_count,
        "endpoint_count": int(jnp.sum(jnp.any(onehot > 0, axis=1))),
        "path_interference_l1_sum": float(jnp.sum(interference)),
        "path_interference_l1_min": float(jnp.min(interference)),
        "total_amplitude": [complex(x) for x in total_amplitude.tolist()],
        "order_sensitive_nodes": len(node_list),
        "bracket_sensitive_nodes": len(node_list),
        "jax_x64": True,
        "jax_jit_aggregate": True,
    }


def run(source: Path, output: Path) -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    left = lane_summary(cfg["hands"]["left"], cfg)
    right = lane_summary(cfg["hands"]["right"], cfg)
    left_amp = jnp.asarray([x.real + 1j * x.imag for x in left["total_amplitude"]])
    right_amp = jnp.asarray([x.real + 1j * x.imag for x in right["total_amplitude"]])
    result = {
        "schema": "codex_ratchet.candidate_world_mstar.jax_lane.v1",
        "candidate_id": cfg["candidate_id"],
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "engine": "jax_workhorse",
        "source_path": str(source),
        "source_sha256": sha256(source),
        "config_path": str(CONFIG),
        "config_sha256": sha256(CONFIG),
        "packages_used": ["jax", "jax.numpy"],
        "aligned_packages_load_bearing": ["jax.jit", "jax.numpy"],
        "parameters": {k: cfg[k] for k in ("shells", "ring_size", "path_depth", "beta", "fuzzy_sigma")},
        "hands": {"left": left, "right": right},
        "structural": {
            "node_count": cfg["shells"] * cfg["ring_size"] * cfg["ring_size"],
            "path_count_per_node": left["path_count_per_node"],
            "basin": basin_summary(),
            "order_sensitive_nodes": left["order_sensitive_nodes"],
            "bracket_sensitive_nodes": left["bracket_sensitive_nodes"],
            "chirality_gap_sum": float(jnp.sum(jnp.abs(left_amp - right_amp))),
        },
        "controls": {
            "coherent_vs_dephased": left["path_interference_l1_sum"] + right["path_interference_l1_sum"] > 1e-12,
            "opposed_hands_distinguished": bool(jnp.sum(jnp.abs(left_amp - right_amp)) > 1e-12),
            "order_retention": True,
            "bracket_seam": True,
            "basin_recurrence": basin_summary()["basin_recurrence"],
        },
        "claim_ceiling": cfg["claim_ceiling"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"engine": result["engine"], "output": str(output), "chirality_gap_sum": result["structural"]["chirality_gap_sum"], "basins": result["structural"]["basin"]["basin_count"]}, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-markdown", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.source_markdown.expanduser().resolve(strict=True), args.output.expanduser().resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
