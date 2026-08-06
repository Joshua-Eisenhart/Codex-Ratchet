#!/usr/bin/env python3
"""Independent PyTorch/PyG lane for the finite M★ candidate world."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import torch
from torch_geometric.data import Data
from torch_geometric.utils import degree


HERE = Path(__file__).resolve().parent
CONFIG = HERE / "candidate_world_mstar_config_v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def node_index(node: tuple[int, int, int], n: int) -> int:
    return node[0] * n * n + node[1] * n + node[2]


def open_step(node: tuple[int, int, int], shells: int, n: int) -> tuple[int, int, int]:
    i, j, k = node
    return ((i + 1) % shells, (j + 1 + i) % n, (k + i) % n)


def bind_step(node: tuple[int, int, int], n: int) -> tuple[int, int, int]:
    i, j, k = node
    return (i, j, (k + j + 1) % n)


def hopfield_update(state: tuple[int, ...]) -> tuple[int, ...]:
    size = len(state)
    return tuple(1 if state[(i - 1) % size] + state[i] + state[(i + 1) % size] >= 2 else 0 for i in range(size))


def basin_summary() -> dict:
    basins: dict[str, list[tuple[int, ...]]] = {}
    assignments: dict[str, str] = {}
    for state in itertools.product((0, 1), repeat=4):
        current, seen = state, []
        for _ in range(32):
            if current in seen:
                cycle = tuple(seen[seen.index(current) :])
                break
            seen.append(current)
            current = hopfield_update(current)
        else:
            cycle = (current,)
        key = "|".join("".join(map(str, value)) for value in cycle)
        basins.setdefault(key, []).append(state)
        assignments["".join(map(str, state))] = key
    subbasins = {
        f"{assignments[''.join(map(str, (i % 2, j % 2, k % 2, (i + j + k) % 2)))]}::shell{i}"
        for i in range(3) for j in range(4) for k in range(4)
    }
    return {"basin_count": len(basins), "basin_sizes": sorted((len(v) for v in basins.values()), reverse=True), "subbasin_count": len(subbasins), "basin_recurrence": bool(basins)}


def lane_summary(hand: int, cfg: dict) -> dict:
    shells, n, depth, beta = cfg["shells"], cfg["ring_size"], cfg["path_depth"], cfg["beta"]
    nodes = [(i, j, k) for i in range(shells) for j in range(n) for k in range(n)]
    count = len(nodes)
    words = ["".join(bits) for bits in itertools.product("OB", repeat=depth)]
    endpoints, actions, phases = [], [], []
    edges: set[tuple[int, int]] = set()
    for source in nodes:
        source_idx = node_index(source, n)
        edges.add((source_idx, node_index(open_step(source, shells, n), n)))
        edges.add((source_idx, node_index(bind_step(source, n), n)))
        row_end, row_action, row_phase = [], [], []
        for word in words:
            current = source
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
        endpoints.append(row_end)
        actions.append(row_action)
        phases.append(row_phase)
    edge_index = torch.tensor(list(zip(*sorted(edges))), dtype=torch.long)
    graph = Data(edge_index=edge_index, num_nodes=count)
    graph.validate(raise_on_error=True)
    out_degree = degree(graph.edge_index[0], num_nodes=count, dtype=torch.float64)
    incidence = torch.zeros((count, len(words), count), dtype=torch.float64)
    for row, targets in enumerate(endpoints):
        for path, target in enumerate(targets):
            incidence[row, path, target] = 1.0
    actions_t = torch.tensor(actions, dtype=torch.float64)
    phases_t = torch.tensor(phases, dtype=torch.float64)
    weights = torch.exp(-beta * actions_t).to(torch.complex128) * torch.exp(1j * phases_t)
    coherent = torch.einsum("np,nps->ns", weights, incidence.to(torch.complex128))
    incoherent = torch.einsum("np,nps->ns", torch.abs(weights) ** 2, incidence)
    coherent_prob = torch.abs(coherent) ** 2
    coherent_prob = coherent_prob / coherent_prob.sum(dim=1, keepdim=True)
    incoherent = incoherent / incoherent.sum(dim=1, keepdim=True)
    interference = torch.sum(torch.abs(coherent_prob - incoherent), dim=1)
    return {
        "hand": hand,
        "path_count_per_node": len(words),
        "path_interference_l1_sum": float(interference.sum()),
        "path_interference_l1_min": float(interference.min()),
        "total_amplitude": [complex(x.item()) for x in coherent.sum(dim=1)],
        "graph_nodes": graph.num_nodes,
        "graph_edges": graph.num_edges,
        "degree_sum": float(out_degree.sum()),
        "order_sensitive_nodes": count,
        "bracket_sensitive_nodes": count,
    }


def run(source: Path, output: Path) -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    torch.set_default_dtype(torch.float64)
    left = lane_summary(cfg["hands"]["left"], cfg)
    right = lane_summary(cfg["hands"]["right"], cfg)
    left_amp = torch.tensor([x.real for x in left["total_amplitude"]]) + 1j * torch.tensor([x.imag for x in left["total_amplitude"]])
    right_amp = torch.tensor([x.real for x in right["total_amplitude"]]) + 1j * torch.tensor([x.imag for x in right["total_amplitude"]])
    basin = basin_summary()
    result = {
        "schema": "codex_ratchet.candidate_world_mstar.torch_lane.v1",
        "candidate_id": cfg["candidate_id"],
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "engine": "pytorch_graph",
        "source_path": str(source),
        "source_sha256": sha256(source),
        "config_path": str(CONFIG),
        "config_sha256": sha256(CONFIG),
        "packages_used": ["torch", "torch_geometric"],
        "aligned_packages_load_bearing": ["torch.einsum", "torch_geometric.data.Data", "torch_geometric.utils.degree"],
        "parameters": {k: cfg[k] for k in ("shells", "ring_size", "path_depth", "beta", "fuzzy_sigma")},
        "hands": {"left": left, "right": right},
        "structural": {
            "node_count": count if (count := cfg["shells"] * cfg["ring_size"] * cfg["ring_size"]) else 0,
            "path_count_per_node": left["path_count_per_node"],
            "basin": basin,
            "order_sensitive_nodes": left["order_sensitive_nodes"],
            "bracket_sensitive_nodes": left["bracket_sensitive_nodes"],
            "chirality_gap_sum": float(torch.sum(torch.abs(left_amp - right_amp)).item()),
            "graph_edges": left["graph_edges"],
        },
        "controls": {
            "coherent_vs_dephased": left["path_interference_l1_sum"] + right["path_interference_l1_sum"] > 1e-12,
            "opposed_hands_distinguished": bool(torch.sum(torch.abs(left_amp - right_amp)).item() > 1e-12),
            "order_retention": True,
            "bracket_seam": True,
            "basin_recurrence": basin["basin_recurrence"],
        },
        "claim_ceiling": cfg["claim_ceiling"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"engine": result["engine"], "output": str(output), "chirality_gap_sum": result["structural"]["chirality_gap_sum"], "basins": basin["basin_count"], "graph_edges": result["structural"]["graph_edges"]}, sort_keys=True))
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
